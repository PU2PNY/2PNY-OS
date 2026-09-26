#!/usr/bin/env python3
"""PU2PNY APRS-IS client 0.3.6 — APRS messaging reliability.

Bidirectional APRS-IS client with verified login gating, persistent outbox,
bounded ACK retries, duplicate suppression and lightweight status.
"""
import datetime,json,os,re,socket,time
from pathlib import Path

STATE=Path("/var/lib/2pny")
RUN=Path("/run/2pny")
CFG=STATE/"aprs-settings.json"
STATUS=RUN/"aprs-status.json"
STORE=STATE/"aprs-messages.json"
OUTBOX=STATE/"aprs-outbox"
ACKDIAG=RUN/"aprs-ack.json"
VERSION="0.3.27"
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

# APRS-013: this distribution is message-only. Position/beacon packet
# generation is intentionally absent; messaging does not require coordinates.
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

def command_response(command,body,source):
    command=str(command or "").upper().strip()
    if command=="PING":return "PONG PU2PNY-OS APRS"
    if command=="HELP":return "CMD PING STATUS LAST MYLAST ONLINE MODULE INFO HELP"
    network=readj(STATE/"network-radio.json")
    runtime=readj(RUN/"network-runtime.json")
    net=dict(network);net.update(runtime)
    if command=="STATUS":
        proto=str(net.get("protocol") or "—").upper()
        state=str(net.get("link_state") or net.get("state") or "não verificado").upper()
        return f"PU2PNY-OS {proto} {state}"[:67]
    if command=="MODULE":
        mod=str(net.get("module") or "")
        proto=str(net.get("protocol") or "").upper()
        return (f"MODULE {proto} {mod}" if mod else f"MODULE {proto} INDISPONIVEL")[:67]
    if command=="INFO":return "PU2PNY-OS APRS RADIO DIGITAL"
    live=readj(RUN/"live.json")
    hist=live.get("history") if isinstance(live,dict) else []
    if not isinstance(hist,list):hist=[]
    def call(v):return str(v or "").upper().strip().split("-",1)[0]
    def last_for(target):
        target=call(target)
        for row in reversed(hist[-160:]):
            if call(row.get("source"))==target:return row
        return None
    if command in ("LAST","MYLAST"):
        parts=str(body or "").strip().upper().split(maxsplit=1)
        target=source if command=="MYLAST" or len(parts)<2 else parts[1]
        row=last_for(target)
        if not row:return f"SEM ATIVIDADE LOCAL: {call(target)}"[:67]
        proto=str(row.get("protocol") or "—").upper();mode=str(row.get("mode") or "").upper()
        ts=str(row.get("ended_at") or row.get("started_at") or "")
        hh=ts[11:19] if len(ts)>=19 else "—"
        prefix="MYLAST" if command=="MYLAST" else "LAST "+call(target)
        return f"{prefix} {proto} {mode} {hh}Z"[:67]
    if command=="ONLINE":
        cutoff=time.time()-900;seen=set()
        for row in hist[-240:]:
            raw=str(row.get("ended_at") or row.get("started_at") or "")
            try:epoch=datetime.datetime.fromisoformat(raw.replace("Z","+00:00")).timestamp()
            except Exception:continue
            if epoch>=cutoff:
                c=call(row.get("source"))
                if c:seen.add(c)
        return f"ONLINE 15M: {len(seen)} ESTACOES"
    return ""

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

def server_candidates(configured):
    configured=str(configured or "soam.aprs2.net").strip() or "soam.aprs2.net"
    out=[]
    for host in (configured,"rotate.aprs2.net"):
        if host and host not in out:out.append(host)
    return out

def connect_aprs(call,configured,port):
    """Bounded regional -> worldwide APRS-IS connection fallback."""
    errors=[]
    for host in server_candidates(configured):
        try:
            sock=socket.create_connection((host,port),timeout=6)
            sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
            sock.settimeout(.25)
            send(sock,login_line(call))
            return sock,host,""
        except Exception as exc:
            errors.append(host+":"+type(exc).__name__)
    return None,"",";".join(errors)[-220:]

def write_status(cfg,call,server,port,store,state,tcp_connected=False,verified=False,
                 last_beacon=0,last_message_tx=0,last_rx=0,last_error="",login_started=0,
                 configured_server=""):
    now=time.time()
    atomic(STATUS,{
        "enabled":bool(cfg.get("enabled")),"state":state,
        "connected":bool(verified),"tcp_connected":bool(tcp_connected),
        "verified":bool(verified),"callsign":call,"server":server,"configured_server":configured_server or server,"port":port,
        "fallback_active":bool(configured_server and server and server!=configured_server),
        "last_tx":None,
        "last_message_tx":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(last_message_tx)) if last_message_tx else None,
        "last_rx":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(last_rx)) if last_rx else None,
        "next_tx_seconds":0,
        "login_wait_seconds":max(0,int(12-(now-login_started))) if tcp_connected and not verified and login_started else 0,
        "outbox_pending":pending_count(),"last_error":last_error or None,
        "ack_diagnostics":readj(ACKDIAG,{}),
        "unread":store.get("unread",0),"messages":store.get("messages",[])[-40:]
    },0o644)

def main():
    sock=None;tcp_connected=False;verified=False;login_started=0
    last_beacon=0;last_message_tx=0;last_rx=0;last_cfg=None;effective_server=""
    store=load_store();buf=b"";last_status=0;last_outbox_check=0;last_retry_check=0;last_error=""
    while True:
        cfg=readj(CFG);enabled=bool(cfg.get("enabled"));base=str(cfg.get("callsign") or "").upper().strip()
        ssid_raw=cfg.get("ssid");ssid=10 if ssid_raw is None else int(ssid_raw)
        call=base if "-" in base or ssid==0 else f"{base}-{ssid}"
        valid=bool(re.fullmatch(r"[A-Z0-9]{3,6}(?:-[0-9]{1,2})?",call))
        server=str(cfg.get("server") or "soam.aprs2.net").strip() or "soam.aprs2.net";port=int(cfg.get("port") or 14580)
        if not enabled or not valid:
            if sock:
                try:sock.close()
                except Exception:pass
            sock=None;tcp_connected=False;verified=False;effective_server=""
            write_status(cfg,call,server,port,store,"disabled" if not enabled else "needs_configuration",
                         last_beacon=last_beacon,last_message_tx=last_message_tx,last_rx=last_rx,
                         last_error="" if not enabled else "callsign_invalid",configured_server=server)
            time.sleep(3);continue

        sig=(call,server,port)
        if sig!=last_cfg:
            if sock:
                try:sock.close()
                except Exception:pass
            sock=None;tcp_connected=False;verified=False;last_cfg=sig;buf=b"";last_error="";effective_server=""

        if not sock:
            sock,effective_server,last_error=connect_aprs(call,server,port)
            if sock:
                tcp_connected=True;verified=False;login_started=time.time();buf=b"";last_error=""
            else:
                tcp_connected=False;verified=False
                write_status(cfg,call,server,port,store,"offline",False,False,last_beacon,last_message_tx,last_rx,last_error,configured_server=server)
                time.sleep(8);continue

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
                    matched=apply_ack(store,m["source"],m["id"],"ack")
                    atomic(ACKDIAG,{"type":"ack","source":m["source"],"id":m["id"],"matched":matched,"received_at":utc()},0o644)
                    continue
                if m["type"]=="rej":
                    matched=apply_ack(store,m["source"],m["id"],"rejected")
                    atomic(ACKDIAG,{"type":"rej","source":m["source"],"id":m["id"],"matched":matched,"received_at":utc()},0o644)
                    continue
                is_new=record_incoming(store,m["source"],m["text"],m["id"])
                if m.get("id"):
                    send(sock,msg_packet(call,m["source"],"ack"+m["id"]))
                if is_new:
                    body=str(m.get("text") or "").strip()
                    command=body.split(None,1)[0].upper() if body else ""
                    if command in ("PING","STATUS","LAST","MYLAST","ONLINE","MODULE","INFO","HELP"):
                        reply=command_response(command,body,m["source"])
                        if reply:
                            send(sock,msg_packet(call,m["source"],reply))
                            last_message_tx=now
        except socket.timeout:
            pass
        except Exception as exc:
            last_error=type(exc).__name__
            try:sock.close()
            except Exception:pass
            sock=None;tcp_connected=False;verified=False;effective_server=""

        if auth_rejected:
            try:sock.close()
            except Exception:pass
            sock=None;tcp_connected=False
            write_status(cfg,call,effective_server or server,port,store,"login_rejected",False,False,last_beacon,last_message_tx,last_rx,last_error,configured_server=server)
            effective_server=""
            time.sleep(15);continue

        if sock and not verified and now-login_started>12:
            last_error="login_timeout"
            try:sock.close()
            except Exception:pass
            sock=None;tcp_connected=False
            write_status(cfg,call,effective_server or server,port,store,"login_timeout",False,False,last_beacon,last_message_tx,last_rx,last_error,configured_server=server)
            effective_server=""
            time.sleep(8);continue

        if sock and verified:
            # APRS-013: message-only. Verified sessions process only message
            # outbox/retries and incoming messages/ACKs; no position beacon.
            if now-last_outbox_check>=1:
                try:
                    sent_count=consume_outbox(sock,call,store,now)
                    if sent_count:last_message_tx=now
                    last_outbox_check=now
                except Exception as exc:
                    last_error=type(exc).__name__
                    try:sock.close()
                    except Exception:pass
                    sock=None;tcp_connected=False;verified=False;effective_server="";continue

            if now-last_retry_check>=2:
                try:
                    retried=retry_unacked(sock,call,store,now)
                    if retried:last_message_tx=now
                    last_retry_check=now
                except Exception as exc:
                    last_error=type(exc).__name__
                    try:sock.close()
                    except Exception:pass
                    sock=None;tcp_connected=False;verified=False;effective_server="";continue

        if now-last_status>=2:
            state="connected" if verified else ("authenticating" if tcp_connected else "offline")
            write_status(cfg,call,effective_server or server,port,store,state,tcp_connected,verified,
                         last_beacon,last_message_tx,last_rx,last_error,login_started,configured_server=server)
            last_status=now
        time.sleep(.25)

if __name__=="__main__":
    main()
