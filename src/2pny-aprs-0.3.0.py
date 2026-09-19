#!/usr/bin/env python3
"""PU2PNY APRS-IS client 0.3.0 — APRS only, no DPRS.

Supports fixed-position beacon, APRS-IS send/receive messages, ACK tracking,
bounded persistent inbox/outbox history and a lightweight status snapshot.
"""
import json,os,re,socket,time,uuid
from pathlib import Path
STATE=Path("/var/lib/2pny");RUN=Path("/run/2pny")
CFG=STATE/"aprs-settings.json";STATUS=RUN/"aprs-status.json";STORE=STATE/"aprs-messages.json";OUTBOX=STATE/"aprs-outbox"

def readj(path,default=None):
    try:return json.loads(Path(path).read_text())
    except Exception:return {} if default is None else default
def atomic(path,obj,mode=0o600):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")));os.chmod(tmp,mode);os.replace(tmp,path)
def passcode(call):
    call=call.upper().split("-")[0];h=0x73e2
    for i in range(0,len(call),2):
        h^=ord(call[i])<<8
        if i+1<len(call):h^=ord(call[i+1])
    return h&0x7fff
def degmin(value,is_lat):
    v=float(value);hem=("N" if v>=0 else "S") if is_lat else ("E" if v>=0 else "W");v=abs(v);deg=int(v);minutes=(v-deg)*60
    return (f"{deg:02d}{minutes:05.2f}{hem}" if is_lat else f"{deg:03d}{minutes:05.2f}{hem}")
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
def parse_message(line,our):
    # APRS message payload is :ADDRESSEE:TEXT
    m=re.search(r":([^:]{9}):(.*)$",line)
    if not m:return None
    dest=m.group(1).strip().upper();body=m.group(2).strip()
    src=line.split(">",1)[0].strip().upper()
    if dest!=our.upper():return None
    if body.lower().startswith("ack") and len(body)>3:return {"type":"ack","source":src,"id":body[3:].strip()}
    if body.lower().startswith("rej") and len(body)>3:return {"type":"rej","source":src,"id":body[3:].strip()}
    mid=None
    if "{" in body:
        body,mid=body.rsplit("{",1);mid=mid.strip()[:5]
    return {"type":"message","source":src,"text":body.strip(),"id":mid}
def load_store():
    d=readj(STORE,{"messages":[],"unread":0})
    if not isinstance(d.get("messages"),list):d["messages"]=[]
    d["messages"]=d["messages"][-120:];d["unread"]=int(d.get("unread") or 0)
    return d
def save_store(d):d["messages"]=d.get("messages",[])[-120:];atomic(STORE,d)
def send(sock,line):
    sock.sendall((line+"\r\n").encode("ascii","replace"))
def consume_outbox(sock,call,store):
    OUTBOX.mkdir(parents=True,exist_ok=True)
    changed=False
    for p in sorted(OUTBOX.glob("*.json"))[:10]:
        try:
            cmd=json.loads(p.read_text());dest=str(cmd.get("to") or "").upper().strip();text=str(cmd.get("text") or "").strip()
            if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?",dest) or not text:raise ValueError("invalid")
            mid=str(cmd.get("id") or int(time.time()*10)%1000).zfill(3)[-3:]
            send(sock,msg_packet(call,dest,text,mid))
            store["messages"].append({"direction":"out","station":dest,"text":text[:60],"id":mid,"status":"sent","timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})
            changed=True;p.unlink(missing_ok=True)
        except Exception:
            p.rename(p.with_suffix(".bad"))
    if changed:save_store(store)
    return changed
def apply_ack(store,source,mid,status):
    changed=False
    for item in reversed(store["messages"]):
        if item.get("direction")=="out" and item.get("station")==source and str(item.get("id"))==str(mid):
            item["status"]=status;item["ack_at"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime());changed=True;break
    if changed:save_store(store)
def main():
    sock=None;connected=False;last_tx=0;last_cfg=None;store=load_store();buf=b"";last_status=0
    while True:
        cfg=readj(CFG);enabled=bool(cfg.get("enabled"));base=str(cfg.get("callsign") or "").upper().strip()
        ssid=int(cfg.get("ssid") or 10);call=base if "-" in base or ssid==0 else f"{base}-{ssid}"
        valid=bool(re.fullmatch(r"[A-Z0-9]{3,6}(?:-[0-9]{1,2})?",call))
        interval=max(300,min(86400,int(cfg.get("interval_seconds") or 1800)))
        if not enabled or not valid:
            if sock:
                try:sock.close()
                except Exception:pass
            sock=None;connected=False
            atomic(STATUS,{"enabled":enabled,"state":"disabled" if not enabled else "needs_configuration","connected":False,"callsign":call,"unread":store["unread"],"messages":store["messages"][-40:]},0o644)
            time.sleep(3);continue
        server=str(cfg.get("server") or "brazil.aprs2.net");port=int(cfg.get("port") or 14580);sig=(call,server,port)
        if sig!=last_cfg:
            if sock:
                try:sock.close()
                except Exception:pass
            sock=None;connected=False;last_cfg=sig
        if not sock:
            try:
                sock=socket.create_connection((server,port),timeout=8);sock.settimeout(.25)
                send(sock,f"user {call} pass {passcode(call)} vers PU2PNY-OS 0.3.0 filter m/500")
                connected=True;buf=b""
            except Exception as exc:
                sock=None;connected=False;atomic(STATUS,{"enabled":True,"state":"offline","connected":False,"callsign":call,"server":server,"error":type(exc).__name__,"unread":store["unread"],"messages":store["messages"][-40:]},0o644);time.sleep(10);continue
        now=time.time()
        if cfg.get("latitude") not in (None,"") and cfg.get("longitude") not in (None,"") and now-last_tx>=interval:
            try:send(sock,beacon(cfg,call));last_tx=now
            except Exception:
                try:sock.close()
                except Exception:pass
                sock=None;connected=False;continue
        try:consume_outbox(sock,call,store)
        except Exception:
            try:sock.close()
            except Exception:pass
            sock=None;connected=False;continue
        try:
            data=sock.recv(4096)
            if data==b"":raise ConnectionError("closed")
            buf+=data
            while b"\n" in buf:
                raw,buf=buf.split(b"\n",1);line=raw.decode("ascii","replace").strip()
                if not line or line.startswith("#"):continue
                m=parse_message(line,call)
                if not m:continue
                if m["type"]=="ack":apply_ack(store,m["source"],m["id"],"ack");continue
                if m["type"]=="rej":apply_ack(store,m["source"],m["id"],"rejected");continue
                store["messages"].append({"direction":"in","station":m["source"],"text":m["text"],"id":m["id"],"status":"received","timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})
                store["unread"]=int(store.get("unread") or 0)+1;save_store(store)
                if m.get("id"):
                    send(sock,msg_packet(call,m["source"],"ack"+m["id"]))
        except socket.timeout:pass
        except Exception:
            try:sock.close()
            except Exception:pass
            sock=None;connected=False
        if now-last_status>=2:
            atomic(STATUS,{"enabled":True,"state":"connected" if connected else "offline","connected":connected,"callsign":call,"server":server,"port":port,
                "last_tx":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(last_tx)) if last_tx else None,
                "next_tx_seconds":max(0,int(interval-(now-last_tx))) if last_tx else 0,"unread":store["unread"],"messages":store["messages"][-40:]},0o644);last_status=now
        time.sleep(.25)
if __name__=="__main__":main()
