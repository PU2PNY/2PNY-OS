#!/usr/bin/env python3
from pathlib import Path
import json, os, shutil, subprocess, sys, urllib.request

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.2-alpha"
YSF_COMMIT="a71e33aaed25a93e8c2bb2d87fc5fb7491e72fe7"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.3.2.go","src/2pnyd/main.go",0o644)
install("src/wizard-0.3.2.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.3.2.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/2pny-network-switch-0.3.2","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-hostfiles-update-0.3.2","rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",0o755)
install("src/2pny-protocol-network-apply-all-0.3.2.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-station-worker-0.3.2.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# 0.3.1 accidentally seeded /var/lib/2pny/hostfiles while runtime reads /hosts.
wrong=root/"rootfs-overlay/var/lib/2pny/hostfiles"
hosts=root/"rootfs-overlay/var/lib/2pny/hosts"
hosts.mkdir(parents=True,exist_ok=True)
if wrong.exists():
    for p in wrong.iterdir():
        if p.is_file() and p.stat().st_size:
            shutil.copy2(p,hosts/p.name)
    shutil.rmtree(wrong)

# Build the runtime files expected by the pinned gateways before first boot.
ysf_txt=hosts/"YSFHosts.txt"
if ysf_txt.exists():
    refs=[]
    for raw in ysf_txt.read_text(errors="ignore").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"): continue
        parts=line.split(";")
        if len(parts)<5: continue
        ident,name,desc,address,port=map(str.strip,parts[:5])
        try: port=int(port)
        except ValueError: continue
        refs.append({"designator":ident.zfill(5)[-5:],"country":"YSF","name":name,
                     "use_xx_prefix":False,"user_count":"000","description":desc or name,
                     "port":port,"ipv4":address,"ipv6":None})
    (hosts/"YSFHosts.json").write_text(json.dumps({"reflectors":refs},ensure_ascii=False,separators=(",",":"))+"\n")

fcs=hosts/"FCSRooms.txt"
if not fcs.exists() or fcs.stat().st_size<40:
    url=f"https://raw.githubusercontent.com/g4klx/YSFClients/{YSF_COMMIT}/YSFGateway/FCSRooms.txt"
    req=urllib.request.Request(url,headers={"User-Agent":"PU2PNY-OS/0.3.2-build"})
    with urllib.request.urlopen(req,timeout=25) as resp:
        data=resp.read(2_000_000)
    if len(data)<40: raise RuntimeError("FCSRooms seed is unexpectedly small")
    fcs.write_bytes(data)

for name in ("P25Hosts.json","NXDNHosts.json"):
    p=hosts/name
    if not p.exists(): p.write_text('{"reflectors":[]}\n')

for p in hosts.iterdir():
    if p.is_file(): os.chmod(p,0o644)

# Compile/syntax gate on the final staged overlay.
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-hostfiles-update")],check=True)
for rel in (
  "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
  "rootfs-overlay/usr/local/sbin/2pny-station-worker",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
    cache=(root/rel).parent/"__pycache__"
    if cache.exists(): shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
apply=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
assert 'appVersion' in main and '"0.3.2-alpha"' in main
assert "resume_urls" in main and "startHostfilesUpdate" in main
assert "reconnectCandidates" in wiz and "serverCatalog=[]" in wiz
assert "activityBody" in dash and "signalBar" in dash and "radioId" in dash
assert 'atomic(HOST,host_text,0o640,"mmdvm")' in apply
for name in ("DStar_Hosts.json","DPlus_Hosts.txt","DExtra_Hosts.txt","DCS_Hosts.txt",
             "XLXHosts.txt","YSFHosts.txt","YSFHosts.json","FCSRooms.txt","P25Hosts.txt","NXDNHosts.txt"):
    p=hosts/name
    assert p.exists() and p.stat().st_size>0, name
assert not wrong.exists()
print("PU2PNY-OS 0.3.2 overlay applied: protocol ownership, Wi-Fi handoff, catalogs and live panel fixed")