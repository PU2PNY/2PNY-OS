#!/usr/bin/env python3
from pathlib import Path
import os, re, shutil, subprocess, sys, urllib.request, time

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.1-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# 0.3.1 is deliberately an overlay on top of the full 0.2.9 + 0.3.0 stack.
install("src/2pnyd-main-0.3.1.go","src/2pnyd/main.go",0o644)
install("src/wizard-0.3.1.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.3.1.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/protocols-0.3.1.html","rootfs-overlay/usr/share/2pny/protocols.html",0o644)

install("src/2pny-network-switch-0.3.1","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-mdns-guard-0.3.1","rootfs-overlay/usr/local/sbin/2pny-mdns-guard",0o755)
install("src/2pny-mdns-guard-0.3.1.service","rootfs-overlay/etc/systemd/system/2pny-mdns-guard.service",0o644)

install("src/2pny-live-core-0.3.1.py","rootfs-overlay/usr/local/lib/2pny-live-core.py",0o644)
install("src/2pny-hardware-probe-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-hardware-probe",0o755)
install("src/2pny-display-apply-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-display-apply",0o755)
install("src/2pny-nextion-autodetect-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-nextion-autodetect",0o755)

install("src/2pny-server-catalog-0.3.1.py","rootfs-overlay/usr/local/sbin/2pny-server-catalog",0o755)
install("src/2pny-hostfiles-update-0.3.1","rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",0o755)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Force the 0.3.1 mDNS service target in the enabled unit link.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
for service in ("2pny-mdns-guard.service","2pny-display-core.service","2pny-station.service","2pny-aprs.service","2pny-netdiag.service"):
    link=wants/service
    if link.exists() or link.is_symlink(): link.unlink()
    link.symlink_to("../"+service)

# Seed protocol catalogs into the image. Runtime updater keeps them fresh while
# preserving the last-good copies. Build fails if core catalogs cannot be seeded.
hostdir=root/"rootfs-overlay/var/lib/2pny/hostfiles"
hostdir.mkdir(parents=True,exist_ok=True)
sources={
 "DStar_Hosts.json":[
   "https://raw.githubusercontent.com/g4klx/DStarGateway/612f388727a9bb47aaeaae3a89f5abff3152ed93/Data/DStar_Hosts.json"],
 "DPlus_Hosts.txt":[
   "https://www.pistar.uk/downloads/DPlus_Hosts.txt",
   "https://raw.githubusercontent.com/airphel/WPSD-HostFiles/main/DPlus_Hosts.txt"],
 "DExtra_Hosts.txt":[
   "https://www.pistar.uk/downloads/DExtra_Hosts.txt",
   "https://raw.githubusercontent.com/airphel/WPSD-HostFiles/main/DExtra_Hosts.txt"],
 "DCS_Hosts.txt":[
   "https://www.pistar.uk/downloads/DCS_Hosts.txt",
   "https://raw.githubusercontent.com/airphel/WPSD-HostFiles/main/DCS_Hosts.txt"],
 "XLXHosts.txt":[
   "https://www.pistar.uk/downloads/XLXHosts.txt",
   "https://raw.githubusercontent.com/airphel/WPSD-HostFiles/main/XLXHosts.txt"],
 "YSFHosts.txt":[
   "https://www.pistar.uk/downloads/YSFHosts.txt",
   "https://raw.githubusercontent.com/airphel/WPSD-HostFiles/main/YSF_Hosts.txt",
   "https://raw.githubusercontent.com/dj0abr/OpenDVM/main/hosts/YSFHosts.txt"],
 "P25Hosts.txt":[
   "https://www.pistar.uk/downloads/P25Hosts.txt",
   "https://raw.githubusercontent.com/airphel/WPSD-HostFiles/main/P25_Hosts.txt"],
 "NXDNHosts.txt":[
   "https://www.pistar.uk/downloads/NXDNHosts.txt",
   "https://raw.githubusercontent.com/airphel/WPSD-HostFiles/main/NXDN_Hosts.txt"],
}
def fetch(urls):
    last=None
    for url in urls:
        for n in range(2):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"PU2PNY-OS/0.3.1-build"})
                with urllib.request.urlopen(req,timeout=20) as r:
                    data=r.read(4_000_000)
                if len(data)>40:return data
            except Exception as e:last=e;time.sleep(1+n)
    raise RuntimeError(f"catalog download failed: {urls}: {last}")
for name,urls in sources.items():
    data=fetch(urls)
    (hostdir/name).write_bytes(data)
    os.chmod(hostdir/name,0o644)

# Release image must not contain runtime/user state.
for rel in (
 "rootfs-overlay/var/lib/2pny/provisioned","rootfs-overlay/var/lib/2pny/rf-configured",
 "rootfs-overlay/var/lib/2pny/rf-apply-state.json","rootfs-overlay/var/lib/2pny/network-radio.json",
 "rootfs-overlay/var/lib/2pny/network-connect.json","rootfs-overlay/var/lib/2pny/wifi-scan.json",
 "rootfs-overlay/var/lib/2pny/wifi-country","rootfs-overlay/var/lib/2pny/display-runtime.json",
 "rootfs-overlay/var/lib/2pny/display-override.json","rootfs-overlay/var/lib/2pny/station/operators.sqlite",
 "rootfs-overlay/var/lib/2pny/station/operators.sqlite-wal","rootfs-overlay/var/lib/2pny/station/operators.sqlite-shm",
 "rootfs-overlay/run/2pny/live-state.json","rootfs-overlay/run/2pny/contacts.json","rootfs-overlay/run/2pny/netdiag.json",
):
    try:(root/rel).unlink()
    except FileNotFoundError:pass

# Syntax / compatibility gate on final staged overlay.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
for rel in (
 "rootfs-overlay/usr/local/sbin/2pny-network-switch",
 "rootfs-overlay/usr/local/sbin/2pny-network-core",
 "rootfs-overlay/usr/local/sbin/2pny-mdns-guard",
 "rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",
 "rootfs-overlay/usr/local/sbin/2pny-mode-apply",
):
    subprocess.run(["bash","-n",str(root/rel)],check=True)
for rel in (
 "rootfs-overlay/usr/local/lib/2pny-live-core.py",
 "rootfs-overlay/usr/local/sbin/2pny-station-worker",
 "rootfs-overlay/usr/local/sbin/2pny-hardware-probe",
 "rootfs-overlay/usr/local/sbin/2pny-display-core",
 "rootfs-overlay/usr/local/sbin/2pny-display-apply",
 "rootfs-overlay/usr/local/sbin/2pny-nextion-autodetect",
 "rootfs-overlay/usr/local/sbin/2pny-server-catalog",
 "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
 "rootfs-overlay/usr/local/libexec/2pny-dmr-apply",
 "rootfs-overlay/usr/local/sbin/2pny-aprs",
 "rootfs-overlay/usr/local/sbin/2pny-netdiag",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
for base in (root/"rootfs-overlay/usr/local/lib",root/"rootfs-overlay/usr/local/sbin",root/"rootfs-overlay/usr/local/libexec"):
    cache=base/"__pycache__"
    if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
proto=(root/"rootfs-overlay/usr/share/2pny/protocols.html").read_text()
sw=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
probe=(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe").read_text()
assert re.search(r'appVersion\s*=\s*"0\.3\.1-alpha"',main)
assert "create_candidate" in sw and "try_profile" in sw and "restore_on_error" in sw
assert 'b"connect\\xff\\xff\\xff"' in probe
assert 'id="search"' not in proto and "Buscar servidor" not in proto
for x in ("REF / DPlus","XRF / DExtra","DCS","XLX"): assert x in proto
assert "Aguardando transmissão" in dash and "currentActive" in dash
assert "Failed to fetch" not in wiz
assert (hostdir/"DStar_Hosts.json").stat().st_size>1000
assert (hostdir/"YSFHosts.txt").stat().st_size>100
print("PU2PNY-OS 0.3.1 overlay applied with 0.2.9 parity preserved")
