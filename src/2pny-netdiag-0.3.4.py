#!/usr/bin/env python3
"""PU2PNY-OS 0.3.4 lightweight network diagnostics.

All probes are cached and bounded.  This service only observes the active
route/DNS path; it never changes DNS, VPN, routes or RF configuration.
"""
import json, os, random, re, socket, struct, subprocess, time
from pathlib import Path

RUN=Path("/run/2pny"); STATE=Path("/var/lib/2pny"); OUT=RUN/"netdiag.json"
DNS_CANDIDATES=[
    ("Cloudflare","1.1.1.1"),
    ("Google","8.8.8.8"),
    ("OpenDNS","208.67.222.222"),
]

def readj(p):
    try:return json.loads(Path(p).read_text())
    except Exception:return {}

def atomic(o):
    RUN.mkdir(parents=True,exist_ok=True)
    t=OUT.with_suffix(".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,separators=(",",":")))
    os.chmod(t,0o644);os.replace(t,OUT)

def run(*args,timeout=4):
    try:return subprocess.run(args,text=True,capture_output=True,timeout=timeout)
    except Exception:return None

def target():
    n=readj(STATE/"network-radio.json")
    h=str(n.get("address") or "").strip()
    if re.fullmatch(r"[A-Za-z0-9.-]{1,253}",h):return h
    return "1.1.1.1"

def default_route():
    p=run("ip","-4","route","show","default")
    line=(p.stdout.splitlines()[0] if p and p.stdout.strip() else "")
    iface="";gateway=""
    m=re.search(r"\bdev\s+(\S+)",line)
    if m:iface=m.group(1)
    m=re.search(r"\bvia\s+((?:\d{1,3}\.){3}\d{1,3})",line)
    if m:gateway=m.group(1)
    return iface,gateway

def effective_dns(iface):
    out=[]
    p=run("resolvectl","dns",timeout=3)
    if p and p.returncode==0:
        for line in p.stdout.splitlines():
            if iface and line.startswith("Link ") and ("("+iface+")" not in line):continue
            for ip in re.findall(r"(?<![0-9A-Fa-f:])(?:\d{1,3}\.){3}\d{1,3}(?![0-9A-Fa-f:])",line):
                if ip not in out:out.append(ip)
    if not out and iface:
        p=run("nmcli","-g","IP4.DNS","device","show",iface,timeout=3)
        if p and p.returncode==0:
            for line in p.stdout.splitlines():
                ip=line.strip()
                if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}",ip) and ip not in out:out.append(ip)
    if not out:
        try:
            for line in Path("/etc/resolv.conf").read_text(errors="ignore").splitlines():
                m=re.match(r"\s*nameserver\s+((?:\d{1,3}\.){3}\d{1,3})",line)
                if m and m.group(1) not in out:out.append(m.group(1))
        except Exception:pass
    return out[:6]

def ping(host,count=4):
    try:
        p=subprocess.run(["ping","-n","-c",str(count),"-W","1",host],text=True,capture_output=True,timeout=count+3)
        vals=[float(x) for x in re.findall(r"time[=<]([0-9.]+)\s*ms",p.stdout)]
        loss=100*(1-len(vals)/count)
        jit=sum(abs(b-a) for a,b in zip(vals,vals[1:]))/(len(vals)-1) if len(vals)>1 else 0
        return {"reachable":p.returncode==0 and bool(vals),"latency_ms":round(sum(vals)/len(vals),1) if vals else None,
                "loss_pct":round(loss,1),"jitter_ms":round(jit,1)}
    except Exception:return {"reachable":False,"latency_ms":None,"loss_pct":100.0,"jitter_ms":None}

def route(host):
    try:p=subprocess.run(["traceroute","-n","-q","1","-w","1","-m","12",host],text=True,capture_output=True,timeout=18)
    except Exception:return []
    hops=[]
    for line in p.stdout.splitlines()[1:]:
        m=re.match(r"\s*(\d+)\s+(.+)",line)
        if not m:continue
        rest=m.group(2);ipm=re.search(r"((?:\d{1,3}\.){3}\d{1,3})",rest);ms=re.search(r"([0-9.]+)\s*ms",rest)
        hops.append({"hop":int(m.group(1)),"address":ipm.group(1) if ipm else None,
                     "latency_ms":float(ms.group(1)) if ms else None,"icmp_reply":bool(ipm)})
    return hops

def dns_packet(name):
    qid=random.randint(0,65535)
    labels=b"".join(bytes([len(x)])+x.encode("ascii") for x in name.split("."))+b"\0"
    return qid,struct.pack("!HHHHHH",qid,0x0100,1,0,0,0)+labels+struct.pack("!HH",1,1)

def dns_probe(server,name="example.com"):
    qid,packet=dns_packet(name);started=time.monotonic()
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(1.2)
    try:
        s.sendto(packet,(server,53));data,_=s.recvfrom(2048)
        ms=round((time.monotonic()-started)*1000,1)
        if len(data)<12 or struct.unpack("!H",data[:2])[0]!=qid:raise OSError("resposta DNS inválida")
        flags=struct.unpack("!H",data[2:4])[0];rcode=flags&0xF
        return {"server":server,"reachable":rcode in (0,3),"latency_ms":ms,"rcode":rcode}
    except Exception:
        return {"server":server,"reachable":False,"latency_ms":None,"rcode":None}
    finally:s.close()

def dns_snapshot(servers):
    tests=[];seen=set()
    for label,server in [("Atual",s) for s in servers]+DNS_CANDIDATES:
        if server in seen:continue
        seen.add(server);r=dns_probe(server);r["provider"]=label;tests.append(r)
    good=[x for x in tests if x["reachable"] and x["latency_ms"] is not None]
    recommendation=None
    current=[x for x in good if x["server"] in servers]
    alternatives=[x for x in good if x["server"] not in servers]
    if current and alternatives:
        cur=min(current,key=lambda x:x["latency_ms"]);alt=min(alternatives,key=lambda x:x["latency_ms"])
        # Suggest only for a material, repeatable-looking gap. Never auto-apply.
        if cur["latency_ms"]>=40 and alt["latency_ms"]+20<cur["latency_ms"]:
            recommendation={"candidate":alt["provider"],"server":alt["server"],
                            "observed_ms":alt["latency_ms"],"current_ms":cur["latency_ms"],
                            "message":f"{alt['provider']} respondeu mais rápido neste teste. Compare novamente antes de alterar o DNS."}
    return tests,recommendation

def main():
    last_route=0;cached_hops=[];last_target=""
    last_dns=0;cached_dns=[];cached_rec=None;last_dns_key=None
    while True:
        h=target();iface,gateway=default_route();servers=effective_dns(iface);now=time.time()
        metrics=ping(h,4)
        if h!=last_target or now-last_route>600:
            cached_hops=route(h);last_route=now;last_target=h
        dns_key=(iface,tuple(servers))
        if dns_key!=last_dns_key or now-last_dns>600:
            cached_dns,cached_rec=dns_snapshot(servers);last_dns=now;last_dns_key=dns_key
        health="offline" if not metrics["reachable"] else "poor" if metrics["loss_pct"]>5 or (metrics["latency_ms"] or 0)>250 or (metrics["jitter_ms"] or 0)>60 else "warning" if metrics["loss_pct"]>1 or (metrics["latency_ms"] or 0)>160 else "ok"
        atomic({"target":h,"health":health,"metrics":metrics,"interface":iface,"gateway":gateway,
                "dns_servers":servers,"dns_tests":cached_dns,"dns_recommendation":cached_rec,
                "hops":cached_hops,"hop_count":len(cached_hops),
                "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
                "note":"Hops sem resposta ICMP não significam necessariamente falha. DNS sugerido nunca é aplicado automaticamente."})
        time.sleep(30)

if __name__=="__main__":main()
