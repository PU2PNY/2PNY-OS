#!/usr/bin/env python3
"""PU2PNY Direct rendezvous-only server 0.3.21.

The server never receives or derives peer session keys. It only stores short-lived
presence and forwards signed control messages or opaque encrypted relay packets.
"""
import argparse, json, logging, re, socket, time
from collections import defaultdict, deque

CALL_RE=re.compile(r"^[A-Z0-9]{3,8}(?:-[A-Z0-9]{1,2})?$")
MAX_PACKET=65535
TTL=90
RATE_WINDOW=10
RATE_MAX=160

class DirectServer:
    def __init__(self,host="0.0.0.0",port=43070):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind((host,port))
        self.nodes={}
        self.rate=defaultdict(deque)
        self.rx=0;self.relayed=0;self.lookup=0

    def allow(self,ip):
        now=time.monotonic();q=self.rate[ip]
        while q and now-q[0]>RATE_WINDOW:q.popleft()
        if len(q)>=RATE_MAX:return False
        q.append(now);return True

    def send(self,addr,obj):
        raw=json.dumps(obj,separators=(",",":"),ensure_ascii=True).encode()
        if len(raw)<=MAX_PACKET:self.sock.sendto(raw,addr)

    def prune(self):
        now=time.monotonic()
        for k,v in list(self.nodes.items()):
            if now-v["seen"]>TTL:self.nodes.pop(k,None)

    def endpoint(self,addr):return f"{addr[0]}:{addr[1]}"

    def handle(self,raw,addr):
        self.rx+=1
        if not self.allow(addr[0]) or len(raw)>MAX_PACKET:return
        try:m=json.loads(raw)
        except Exception:return
        if not isinstance(m,dict):return
        t=str(m.get("t") or "")
        fr=str(m.get("from") or "").upper().strip()
        to=str(m.get("to") or "").upper().strip()
        now=time.monotonic()
        if t=="reg":
            if not CALL_RE.fullmatch(fr):return
            ed=str(m.get("ed") or "");xp=str(m.get("x") or "")
            if not ed or not xp or len(ed)>256 or len(xp)>256:return
            old=self.nodes.get(fr)
            # A callsign key change is accepted only after the old presence expires.
            if old and (old["ed"]!=ed or old["x"]!=xp) and now-old["seen"]<=TTL:return
            self.nodes[fr]={"addr":addr,"ed":ed,"x":xp,"fp":str(m.get("fp") or "")[:64],"seen":now}
            self.send(addr,{"t":"reg-ok","from":"SERVER","to":fr,"endpoint":self.endpoint(addr),"ts":int(time.time())})
            return
        node=self.nodes.get(fr)
        if not node or node["addr"]!=addr or now-node["seen"]>TTL:return
        node["seen"]=now
        if t=="lookup":
            if not CALL_RE.fullmatch(to):return
            target=self.nodes.get(to);self.lookup+=1
            if not target or now-target["seen"]>TTL:
                self.send(addr,{"t":"lookup-result","from":to,"to":fr,"nonce":m.get("nonce",""),"error":"peer offline"})
                return
            # Ask the target to produce its own signed lookup-result. The server
            # provides the requester's observed endpoint but does not impersonate either peer.
            self.send(target["addr"],{"t":"lookup-query","from":fr,"to":to,"nonce":str(m.get("nonce") or "")[:128],"endpoint":self.endpoint(addr),"ed":node["ed"],"x":node["x"],"fp":node["fp"],"ts":int(time.time())})
            return
        if t=="lookup-result":
            if not CALL_RE.fullmatch(to):return
            dest=self.nodes.get(to)
            if not dest:return
            out=dict(m);out["endpoint"]=self.endpoint(addr)
            self.send(dest["addr"],out);return
        if t=="relay":
            # P2P-007: rendezvous/signaling is allowed; QSO/media relay is forbidden.
            return

    def serve(self):
        logging.info("PU2PNY Direct rendezvous-only UDP %s",self.sock.getsockname())
        last=time.monotonic()
        while True:
            raw,addr=self.sock.recvfrom(MAX_PACKET)
            self.handle(raw,addr)
            if time.monotonic()-last>15:self.prune();last=time.monotonic()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--host",default="0.0.0.0");ap.add_argument("--port",type=int,default=43070);a=ap.parse_args()
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    DirectServer(a.host,a.port).serve()
if __name__=="__main__":main()
