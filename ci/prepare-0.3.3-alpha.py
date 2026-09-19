#!/usr/bin/env python3
from pathlib import Path
import json, os, shutil, subprocess, sys, urllib.request

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.3-alpha"
YSF_COMMIT="a71e33aaed25a93e8c2bb2d87fc5fb7491e72fe7"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# 0.3.3 is a complete final overlay: do not rely on stale 0.3.0 web/runtime
# files merely remaining from an earlier prepare step.
install("src/2pnyd-main-0.3.3.go","src/2pnyd/main.go",0o644)
install("src/wizard-0.3.3.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.3.3.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/internet-0.3.0.html","rootfs-overlay/usr/share/2pny/internet.html",0o644)
install("src/hotspot-0.3.3.html","rootfs-overlay/usr/share/2pny/hotspot.html",0o644)
install("src/protocols-0.3.1.html","rootfs-overlay/usr/share/2pny/protocols.html",0o644)
install("src/history-0.3.0.html","rootfs-overlay/usr/share/2pny/history.html",0o644)
install("src/aprs-0.3.0.html","rootfs-overlay/usr/share/2pny/aprs.html",0o644)
install("src/display-0.3.3.html","rootfs-overlay/usr/share/2pny/display.html",0o644)
install("src/system-0.3.0.html","rootfs-overlay/usr/share/2pny/system.html",0o644)
install("src/expert-0.3.0.html","rootfs-overlay/usr/share/2pny/expert.html",0o644)
install("src/ui-0.3.0.css","rootfs-overlay/usr/share/2pny/ui-0.3.0.css",0o644)
install("src/ui-common-0.3.3.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js",0o644)
install("src/ui-language-0.3.3.js","rootfs-overlay/usr/share/2pny/ui-language.js",0o644)

install("src/2pny-network-switch-0.3.3","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-network-core-0.3.3","rootfs-overlay/usr/local/sbin/2pny-network-core",0o755)
install("src/2pny-mode-apply-0.3.0","rootfs-overlay/usr/local/sbin/2pny-mode-apply",0o755)
install("src/2pny-mdns-guard-0.3.3","rootfs-overlay/usr/local/sbin/2pny-mdns-guard",0o755)
install("src/2pny-mdns-guard-0.3.3.service","rootfs-overlay/etc/systemd/system/2pny-mdns-guard.service",0o644)
install("src/90-pu2pny-mdns-0.3.3","rootfs-overlay/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns",0o755)

install("src/2pny-live-core-0.3.1.py","rootfs-overlay/usr/local/lib/2pny-live-core.py",0o644)
install("src/2pny-station-worker-0.3.2.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755)
install("src/2pny-station-0.2.8.service","rootfs-overlay/etc/systemd/system/2pny-station.service",0o644)
install("src/2pny-hardware-probe-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-hardware-probe",0o755)
install("src/2pny-display-core-0.2.9.py","rootfs-overlay/usr/local/sbin/2pny-display-core",0o755)
install("src/2pny-display-core-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-display-core.service",0o644)
install("src/2pny-display-apply-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-display-apply",0o755)
install("src/2pny-display-status-0.2.8.py","rootfs-overlay/usr/local/sbin/2pny-display-status",0o755)
install("src/2pny-nextion-autodetect-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-nextion-autodetect",0o755)
install("src/2pny-server-catalog-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-server-catalog",0o755)
install("src/2pny-hostfiles-update-0.3.2","rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",0o755)
install("src/2pny-protocol-network-apply-0.3.0.py","rootfs-overlay/usr/local/libexec/2pny-dmr-apply",0o755)
install("src/2pny-protocol-network-apply-all-0.3.2.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-aprs-0.3.0.py","rootfs-overlay/usr/local/sbin/2pny-aprs",0o755)
install("src/2pny-aprs-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-aprs.service",0o644)
install("src/2pny-netdiag-0.3.0.py","rootfs-overlay/usr/local/sbin/2pny-netdiag",0o755)
install("src/2pny-netdiag-0.3.0.service","rootfs-overlay/etc/systemd/system/2pny-netdiag.service",0o644)
for src,dst in (
 ("src/2pny-dstargateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-dstargateway.service"),
 ("src/2pny-ysfgateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-ysfgateway.service"),
 ("src/2pny-p25gateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-p25gateway.service"),
 ("src/2pny-nxdngateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-nxdngateway.service"),
 ("src/2pny-dapnetgateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-dapnetgateway.service"),
):
    install(src,dst,0o644)
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
    req=urllib.request.Request(url,headers={"User-Agent":"PU2PNY-OS/0.3.3-build"})
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
assert 'appVersion' in main and '"0.3.3-alpha"' in main
assert "resume_urls" in main and "startHostfilesUpdate" in main and '"stage"' in main and '"systemctl", "reboot"' in main
assert "reconnectCandidates" in wiz and "serverCatalog=[]" in wiz and 'id="versionBadge"' in wiz and "0.3.0-alpha" not in wiz
assert "activityGroups" in dash and "signalBar" in dash and "radioId" in dash and 'class="btn plus"' in dash
assert 'atomic(HOST,host_text,0o640,"mmdvm")' in apply
for name in ("DStar_Hosts.json","DPlus_Hosts.txt","DExtra_Hosts.txt","DCS_Hosts.txt",
             "XLXHosts.txt","YSFHosts.txt","YSFHosts.json","FCSRooms.txt","P25Hosts.txt","NXDNHosts.txt"):
    p=hosts/name
    assert p.exists() and p.stat().st_size>0, name
assert not wrong.exists()
nav=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
netcore=(root/"rootfs-overlay/usr/local/sbin/2pny-network-core").read_text()
for label in ("Ao Vivo","Internet","Hotspot","Protocolos","APRS / D-PRS","Histórico","Display","Sistema"): assert label in nav
assert "PU2PNY 0.3.0-alpha" not in netcore
assert "write_connect_state connected" in netcore and "recovery_ap" in netcore
assert (root/"rootfs-overlay/usr/share/2pny/hotspot.html").stat().st_size>1000
assert (root/"rootfs-overlay/usr/share/2pny/display.html").stat().st_size>1000
assert (root/"rootfs-overlay/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns").stat().st_mode & 0o111
print("PU2PNY-OS 0.3.3 final overlay applied: complete UI, reboot Wi-Fi handoff, mDNS and protocol fixes preserved")