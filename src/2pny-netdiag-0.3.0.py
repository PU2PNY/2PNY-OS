#!/usr/bin/env python3
import json,os,re,subprocess,time
from pathlib import Path
RUN=Path("/run/2pny");STATE=Path("/var/lib/2pny");OUT=RUN/"netdiag.json"
def readj(p):
    try:return json.loads(Path(p).read_text())
    except Exception:return {}
def atomic(o):
    RUN.mkdir(parents=True,exist_ok=True);t=OUT.with_suffix(".tmp");t.write_text(json.dumps(o,ensure_ascii=False,separators=(",",":")));os.chmod(t,0o644);os.replace(t,OUT)
def target():
    n=readj(STATE/"network-radio.json")
    h=str(n.get("address") or "").strip()
    if re.fullmatch(r"[A-Za-z0-9.-]{1,253}",h):return h
    return "1.1.1.1"
def ping(host,count=5):
    try:
        p=subprocess.run(["ping","-n","-c",str(count),"-W","1",host],text=True,capture_output=True,timeout=count+3)
        vals=[float(x) for x in re.findall(r"time[=<]([0-9.]+)\s*ms",p.stdout)]
        loss=100*(1-len(vals)/count)
        jit=sum(abs(b-a) for a,b in zip(vals,vals[1:]))/(len(vals)-1) if len(vals)>1 else 0
        return {"reachable":p.returncode==0 and bool(vals),"latency_ms":round(vals[-1],1) if vals else None,"loss_pct":round(loss,1),"jitter_ms":round(jit,1)}
    except Exception:return {"reachable":False,"latency_ms":None,"loss_pct":100.0,"jitter_ms":None}
def route(host):
    cmd=["traceroute","-n","-q","1","-w","1","-m","12",host]
    try:p=subprocess.run(cmd,text=True,capture_output=True,timeout=18)
    except Exception:return []
    hops=[]
    for line in p.stdout.splitlines()[1:]:
        m=re.match(r"\s*(\d+)\s+(.+)",line)
        if not m:continue
        rest=m.group(2);ipm=re.search(r"((?:\d{1,3}\.){3}\d{1,3})",rest);ms=re.search(r"([0-9.]+)\s*ms",rest)
        hops.append({"hop":int(m.group(1)),"address":ipm.group(1) if ipm else None,"latency_ms":float(ms.group(1)) if ms else None,"icmp_reply":bool(ipm)})
    return hops
def main():
    last_route=0;cached=[];last_target=""
    while True:
        h=target();m=ping(h,4);now=time.time()
        if h!=last_target or now-last_route>600:
            cached=route(h);last_route=now;last_target=h
        health="offline" if not m["reachable"] else "poor" if m["loss_pct"]>5 or (m["latency_ms"] or 0)>250 or (m["jitter_ms"] or 0)>60 else "warning" if m["loss_pct"]>1 or (m["latency_ms"] or 0)>160 else "ok"
        atomic({"target":h,"health":health,"metrics":m,"hops":cached,"updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"note":"Hops sem resposta ICMP não significam necessariamente falha; a saúde final usa alcance/perda/latência do destino."})
        time.sleep(5 if health!="ok" else 10)
if __name__=="__main__":main()
