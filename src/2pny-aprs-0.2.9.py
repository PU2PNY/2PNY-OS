#!/usr/bin/env python3
"""PU2PNY APRS-IS client 0.2.9. APRS only; no DPRS path."""
import json, os, socket, time
from pathlib import Path

STATE=Path("/var/lib/2pny")
RUN=Path("/run/2pny")
CFG=STATE/"aprs-settings.json"
STATUS=RUN/"aprs-status.json"

def read():
    try:return json.loads(CFG.read_text())
    except Exception:return {}
def atomic(obj):
    RUN.mkdir(parents=True,exist_ok=True)
    tmp=STATUS.with_suffix(".tmp");tmp.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")));os.chmod(tmp,0o644);os.replace(tmp,STATUS)
def passcode(call):
    call=call.upper().split("-")[0]
    h=0x73e2
    for i in range(0,len(call),2):
        h^=ord(call[i])<<8
        if i+1<len(call):h^=ord(call[i+1])
    return h&0x7fff
def degmin(value,is_lat):
    v=float(value);hem=("N" if v>=0 else "S") if is_lat else ("E" if v>=0 else "W")
    v=abs(v);deg=int(v);minutes=(v-deg)*60
    return (f"{deg:02d}{minutes:05.2f}{hem}" if is_lat else f"{deg:03d}{minutes:05.2f}{hem}")
def packet(cfg):
    call=str(cfg.get("callsign") or "").upper().strip()
    lat=degmin(cfg["latitude"],True);lon=degmin(cfg["longitude"],False)
    table=str(cfg.get("symbol_table") or "/")[:1];symbol=str(cfg.get("symbol") or "r")[:1]
    comment=str(cfg.get("comment") or "PU2PNY-OS hotspot").replace("\r"," ").replace("\n"," ")[:60]
    return f"{call}>APRS,TCPIP*:!{lat}{table}{lon}{symbol}{comment}"
def main():
    history=[];sock=None;connected=False;last_tx=0;last_cfg=None
    while True:
        cfg=read()
        enabled=bool(cfg.get("enabled"))
        call=str(cfg.get("callsign") or "").upper().strip()
        valid=3<=len(call)<=16 and all(c.isalnum() or c=="-" for c in call)
        try:
            interval=max(300,int(cfg.get("interval_seconds") or 1800))
        except Exception:interval=1800
        if not enabled or not valid or cfg.get("latitude") in (None,"") or cfg.get("longitude") in (None,""):
            if sock:
                try:sock.close()
                except Exception:pass
                sock=None
            connected=False
            atomic({"enabled":enabled,"state":"disabled" if not enabled else "needs_configuration","connected":False,"history":history[-20:]})
            time.sleep(5);continue
        server=str(cfg.get("server") or "rotate.aprs2.net");port=int(cfg.get("port") or 14580)
        signature=(call,server,port)
        if signature!=last_cfg:
            if sock:
                try:sock.close()
                except Exception:pass
            sock=None;connected=False;last_cfg=signature
        if not sock:
            try:
                sock=socket.create_connection((server,port),timeout=8);sock.settimeout(8)
                login=f"user {call} pass {passcode(call)} vers PU2PNY-OS 0.2.9 filter m/100\r\n"
                sock.sendall(login.encode("ascii"))
                connected=True
            except Exception as e:
                sock=None;connected=False
                atomic({"enabled":True,"state":"offline","connected":False,"server":server,"error":type(e).__name__,"history":history[-20:]})
                time.sleep(15);continue
        now=time.time()
        if now-last_tx>=interval:
            try:
                p=packet(cfg);sock.sendall((p+"\r\n").encode("ascii","replace"))
                last_tx=now;history.append({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"packet":p})
                history=history[-20:]
            except Exception as e:
                try:sock.close()
                except Exception:pass
                sock=None;connected=False
                atomic({"enabled":True,"state":"offline","connected":False,"server":server,"error":type(e).__name__,"history":history[-20:]})
                continue
        atomic({"enabled":True,"state":"connected" if connected else "offline","connected":connected,"server":server,"port":port,
                "last_tx":history[-1]["timestamp"] if history else None,"next_tx_seconds":max(0,int(interval-(now-last_tx))),"history":history[-20:]})
        # Keep connection alive and notice a remote close without busy polling.
        try:
            sock.settimeout(0.2);data=sock.recv(256)
            if data==b"":raise ConnectionError("closed")
        except socket.timeout:pass
        except Exception:
            try:sock.close()
            except Exception:pass
            sock=None;connected=False
        time.sleep(2)
if __name__=="__main__":main()
