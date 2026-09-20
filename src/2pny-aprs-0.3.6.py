#!/usr/bin/env python3
"""PU2PNY APRS-IS client 0.3.6 — APRS messaging reliability.

Bidirectional APRS-IS client with verified login gating, persistent outbox,
bounded ACK retries, duplicate suppression and lightweight status.
"""
import json,os,re,socket,time
from pathlib import Path

STATE=Path("/var/lib/2pny")
RUN=Path("/run/2pny")
CFG=STATE/"aprs-settings.json"
STATUS=RUN/"aprs-status.json"
STORE=STATE/"aprs-messages.json"
OUTBOX=STATE/"aprs-outbox"
VERSION="0.3.6"
MAX_MESSAGES=120
MAX_RETRIES=3
RETRY_DELAYS=(30,90)
FINAL_ACK_WAIT=180

def readj(path,default=None):
    try:return json.loads(Path(path).read_text())
    except Exception:return {} if default is None else default

def atomic(path,obj,mode=0o600):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")))
    os.chmod(tmp,mode);os.replace(tmp,path)

def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())

def passcode(call):
    call=call.upper().split("-")[0];h=0x73e2
    for i in range(0,len(call),2):
        h^=ord(call[i])<<8
        if i+1<len(call):h^=ord(call[i+1])
    return h&0x7fff

def degmin(value,is_lat):
    v=float(value);hem=("N" if v>=0 else "S") if is_lat else ("E" if v>=0 else "W")
    v=abs(v);deg=int(v);minutes=(v-deg)*60
    return f"{deg:02d}{minutes:05.2f}{hem}" if is_lat else f"{deg:03d}{minutes:05.2f}{hem}"

def beacon(cfg,call):
    lat=degmin(cfg["latitude"],True);lon=degmin(cfg["longitude"],False)
    table=str(cfg.get("symbol_table") or "/")[:1];symbol=str(cfg.get("symbol") or "r")[:1]
    comment=str(cfg.get("comment") or "PU2PNY-OS hotspot").replace("\r"," ").replace("\n"," ")[:60]
    return f"{call}>APRS,TCPIP*:!{lat}{table}{lon}{symbol}{comment}"

def msg_packet(call,dest,text,msgid=None):
    dest=str(dest or "").upper().strip()[:9].ljust(9)
    text=str(text or "").replace("\r"," ").replace("\n"," ")[:60]
    suffix=("{" + str(msgid)) if msgid else ""
    return f"{call}>APRS,TCPIP*::{dest}:{text}{suffix}"

def login_line(call):
    # Port 14580 is bidirectional and already includes direct messages to the
    # logged-in callsign. Avoid a broad m/ filter to keep traffic/CPU low.
    return f"user {call} pass {passcode(call)} vers PU2PNY-OS {VERSION}"

def parse_logresp(line,call):
    m=re.match(r"^#\s*logresp\s+(\S+)\s+(verified|unverified)\b",str(line or "").strip(),re.I)
    if not m:return None
    if m.group(1).upper()!=call.upper():return None
    return m.group(2).lower()=="verified"

def parse_message(line,our):
    m=re.search(r":([^:]{9}):(.*)$",line)
    if not m:return None
    dest=m.group(1).strip().upper();body=m.group(2).strip()
    src=line.split(">",1)[0].strip().upper()
    if dest!=our.upper():return None
    if body.lower().startswith("ack") and len(body)>3:
        return {"type":"ack","source":src,"id":body[3:].strip()[:5]}
    if body.lower().startswith("rej") and len(body)>3:
        return {"type":"rej","source":src,"id":body[3:].strip()[:5]}
    mid=None
    if "{" in body:
        body,mid=body.rsplit("{",1);mid=mid.strip()[:5]
    return {"type":"message","source":src,"text":body.strip(),"id":mid}

def load_store():
    d=readj(STORE,{"messages":[],"unread":0})
    if not isinstance(d,dict):d={"messages":[],"unread":0}
    if not isinstance(d.get("messages"),list):d["messages"]=[]
    d["messages"]=d["messages"][-MAX_MESSAGES:]
    d["unread"]=max(0,int(d.get("unread") or 0))
    return d

def save_store(d):
    d["messages"]=d.get("messages",[])[-MAX_MESSAGES:]
    atomic(STORE,d)

def send(sock,line):
    sock.sendall((line+"\r\n").encode("ascii","replace"))

def valid_dest(dest):
    return bool(re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?",str(dest or "").upper().strip()))

def consume_outbox(sock,call,store,now=None):
    """Transmit queued commands only on a verified session.

    Validation errors are quarantined. Network errors preserve the .json queue
    file and are raised so the caller can reconnect without losing the message.
    """
    now=time.time() if now is None else float(now)
    OUTBOX.mkdir(parents=True,exist_ok=True)
    changed=False;sent_count=0
    for p in sorted(OUTBOX.glob("*.json"))[:10]:
        try:
            cmd=json.loads(p.read_text())
        except Exception:
            p.rename(p.with_suffix(".bad"));continue
        dest=str(cmd.get("to") or "").upper().strip();text=str(cmd.get("text") or "").strip()
        if not valid_dest(dest) or not text or len(text)>60:
            p.rename(p.with_suffix(".bad"));continue
        mid=str(cmd.get("id") or int(now*10)%100000).zfill(3)[-5:]
        packet=msg_packet(call,dest,text,mid)
        try:
            send(sock,packet)
        except Exception:
            raise
        store["messages"].append({
            "direction":"out","station":dest,"text":text[:60],"id":mid,
            "status":"waiting_ack","timestamp":utc(),"attempts":1,
            "last_attempt_epoch":now
        })
        p.unlink(missing_ok=True);changed=True;sent_count+=1
    if changed:save_store(store)
    return sent_count

def apply_ack(store,source,mid,status):
    changed=False
    for item in reversed(store["messages"]):
        if item.get("direction")=="out" and item.get("station")==source and str(item.get("id"))==str(mid):
            item["status"]=status;item["ack_at"]=utc();changed=True;break
    if changed:save_store(store)
    return changed

def record_incoming(store,source,text,mid):
    if mid:
        for item in reversed(store["messages"][-80:]):
            if item.get("direction")=="in" and item.get("station")==source and str(item.get("id") or "")==str(mid):
                return False
    store["messages"].append({
        "direction":"in","station":source,"text":text,"id":mid,
        "status":"received","timestamp":utc()
    })
    store["unread"]=int(store.get("unread") or 0)+1
    save_store(store)
    return True

def retry_unacked(sock,call,store,now=None):
    now=time.time() if now is None else float(now)
    changed=False;retried=0
    for item in store.get("messages",[]):
        if item.get("direction")!="out" or item.get("status") not in ("waiting_ack","sent"):
            continue
        mid=str(item.get("id") or "")
        if not mid:continue
        attempts=max(1,int(item.get("attempts") or 1))
        last=float(item.get("last_attempt_epoch") or 0)
        if attempts>=MAX_RETRIES:
            if last and now-last>=FINAL_ACK_WAIT:
                item["status"]="no_ack";item["completed_at"]=utc();changed=True
            continue
        delay=RETRY_DELAYS[min(attempts-1,len(RETRY_DELAYS)-1)]
        if last and now-last<delay:continue
        send(sock,msg_packet(call,item.get("station"),item.get("text"),mid))
        item["attempts"]=attempts+1;item["last_attempt_epoch"]=now
        item["status"]="waiting_ack";changed=True;retried+=1
    if changed:save_store(store)
    return retried

def pending_count():
    try:return len(list(OUTBOX.glob("*.json")))
    except Exception:return 0

def write_status(cfg,call,server,port,store,state,tcp_connected=False,verified=False,
                 last_beacon=0,last_message_tx=0,last_rx=0,last_error="",login_started=0):
    now=time.time()
    interval=max(300,min(86400,int(cfg.get("interval_seconds") or 1800)))
    atomic(STATUS,{
        "enabled":bool(cfg.get("enabled")),"state":state,
        "connected":bool(verified),"tcp_connected":bool(tcp_connected),
        "verified":bool(verified),"callsign":call,"server":server,"port":port,
        "last_tx":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(last_beacon)) if last_beacon else None,
        "last_message_tx":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(last_message_tx)) if last_message_tx else None,
        "last_rx":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(last_rx)) if last_rx else None,
        "next_tx_seconds":max(0,int(interval-(now-last_beacon))) if last_beacon else 0,
        "login_wait_seconds":max(0,int(12-(now-login_started))) if tcp_connected and not verified and login_started else 0,
        "outbox_pending":pending_count(),"last_error":last_error or None,
        "unread":store.get("unread",0),"messages":store.get("messages",[])[-40:]
    },0o644)

def main():
    sock=None;tcp_connected=False;verified=False;login_started=0
    last_beacon=0;last_message_tx=0;last_rx=0;last_cfg=None
    store=load_store();buf=b"";last_status=0;last_outbox_check=0;last_retry_check=0;last_error=""
    while True:
        cfg=readj(CFG);enabled=bool(cfg.get("enabled"));base=str(cfg.get("callsign") or "").upper().strip()
        ssid_raw=cfg.get("ssid");ssid=10 if ssid_raw is None else int(ssid_raw)
        call=base if "-" in base or ssid==0 else f"{base}-{ssid}"
        valid=bool(re.fullmatch(r"[A-Z0-9]{3,6}(?:-[0-9]{1,2})?",call))
        interval=max(300,min(86400,int(cfg.get("interval_seconds") or 1800)))
        server=str(cfg.get("server") or "soam.aprs2.net");port=int(cfg.get("port") or 14580)
        if not enabled or not valid:
            if sock:
                try:sock.close()
                except Exception:pass
            sock=None;tcp_connected=False;verified=False
            write_status(cfg,call,server,port,store,"disabled" if not enabled else "needs_configuration",
                         last_beacon=last_beacon,last_message_tx=last_message_tx,last_rx=last_rx,
                         last_error="" if not enabled else "callsign_invalid")
            time.sleep(3);continue

        sig=(call,server,port)
        if sig!=last_cfg:
            if sock:
                try:sock.close()
                except Exception:pass
            sock=None;tcp_connected=False;verified=False;last_cfg=sig;buf=b"";last_error=""

        if not sock:
            try:
                sock=socket.create_connection((server,port),timeout=8)
                sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                sock.settimeout(.25)
                send(sock,login_line(call))
                tcp_connected=True;verified=False;login_started=time.time();buf=b"";last_error=""
            except Exception as exc:
                sock=None;tcp_connected=False;verified=False;last_error=type(exc).__name__
                write_status(cfg,call,server,port,store,"offline",False,False,last_beacon,last_message_tx,last_rx,last_error)
                time.sleep(10);continue

        now=time.time()
        auth_rejected=False
        try:
            data=sock.recv(4096)
            if data==b"":raise ConnectionError("closed")
            buf+=data
            while b"\n" in buf:
                raw,buf=buf.split(b"\n",1);line=raw.decode("ascii","replace").strip()
                if not line:continue
                if line.startswith("#"):
                    auth=parse_logresp(line,call)
                    if auth is True:
                        verified=True;last_error=""
                    elif auth is False:
                        verified=False;last_error="login_unverified";auth_rejected=True
                    continue
                if not verified:continue
                last_rx=now
                m=parse_message(line,call)
                if not m:continue
                if m["type"]=="ack":
                    apply_ack(store,m["source"],m["id"],"ack");continue
                if m["type"]=="rej":
                    apply_ack(store,m["source"],m["id"],"rejected");continue
                is_new=record_incoming(store,m["source"],m["text"],m["id"])
                if m.get("id"):
                    send(sock,msg_packet(call,m["source"],"ack"+m["id"]))
                if not is_new:
                    # Duplicate retransmissions are ACKed above but do not inflate inbox/unread.
                    pass
        except socket.timeout:
            pass
        except Exception as exc:
            last_error=type(exc).__name__
            try:sock.close()
            except Exception:pass
            sock=None;tcp_connected=False;verified=False

        if auth_rejected:
            try:sock.close()
            except Exception:pass
            sock=None;tcp_connected=False
            write_status(cfg,call,server,port,store,"login_rejected",False,False,last_beacon,last_message_tx,last_rx,last_error)
            time.sleep(15);continue

        if sock and not verified and now-login_started>12:
            last_error="login_timeout"
            try:sock.close()
            except Exception:pass
            sock=None;tcp_connected=False
            write_status(cfg,call,server,port,store,"login_timeout",False,False,last_beacon,last_message_tx,last_rx,last_error)
            time.sleep(10);continue

        if sock and verified:
            if cfg.get("latitude") not in (None,"") and cfg.get("longitude") not in (None,"") and now-last_beacon>=interval:
                try:send(sock,beacon(cfg,call));last_beacon=now
                except Exception as exc:
                    last_error=type(exc).__name__
                    try:sock.close()
                    except Exception:pass
                    sock=None;tcp_connected=False;verified=False;continue

            if now-last_outbox_check>=1:
                try:
                    sent_count=consume_outbox(sock,call,store,now)
                    if sent_count:last_message_tx=now
                    last_outbox_check=now
                except Exception as exc:
                    last_error=type(exc).__name__
                    try:sock.close()
                    except Exception:pass
                    sock=None;tcp_connected=False;verified=False;continue

            if now-last_retry_check>=2:
                try:
                    retried=retry_unacked(sock,call,store,now)
                    if retried:last_message_tx=now
                    last_retry_check=now
                except Exception as exc:
                    last_error=type(exc).__name__
                    try:sock.close()
                    except Exception:pass
                    sock=None;tcp_connected=False;verified=False;continue

        if now-last_status>=2:
            state="connected" if verified else ("authenticating" if tcp_connected else "offline")
            write_status(cfg,call,server,port,store,state,tcp_connected,verified,
                         last_beacon,last_message_tx,last_rx,last_error,login_started)
            last_status=now
        time.sleep(.25)

if __name__=="__main__":
    main()
