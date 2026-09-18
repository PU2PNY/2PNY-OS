#!/usr/bin/env python3
from pathlib import Path
import os, re, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.2.5-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.2.5.go","src/2pnyd/main.go",0o644)
install("src/2pny-network-core-0.2.5","rootfs-overlay/usr/local/sbin/2pny-network-core",0o755)
install("src/2pny-network-switch-0.2.5","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-hostfiles-update-0.2.5","rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",0o755)
install("src/2pny-server-catalog-0.2.5.py","rootfs-overlay/usr/local/sbin/2pny-server-catalog",0o755)
install("src/2pny-protocol-network-apply-0.2.5","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-live-status-0.2.5.py","rootfs-overlay/usr/local/sbin/2pny-live-status",0o755)
install("src/2pny-auto-maintenance-0.2.5","rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",0o755)
install("src/wizard-0.2.5.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.2.5.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

for rel in ("builder/build-image.sh","rootfs-overlay/usr/local/sbin/2pny-firstboot"):
    p=root/rel
    if not p.exists(): continue
    s=p.read_text()
    for old in ("0.2.4-alpha","0.2.3-alpha","0.2.2-alpha","0.2.1-alpha"):
        s=s.replace(old,version)
    p.write_text(s)

# Offline-safe starter cache. Runtime maintenance refreshes the full public lists.
hosts=root/"rootfs-overlay/var/lib/2pny/hosts"
hosts.mkdir(parents=True,exist_ok=True)
(hosts/"DMR_Hosts.txt").write_text(
    "XLX_026 0000 82.152.175.30 passw0rd 62030\n"
    "BM_7242_Brazil 7242 7242.master.brandmeister.network passw0rd 62031\n"
    "TGIF_Network 0000 tgif.network passw0rd 62031\n"
)
(hosts/"YSFHosts.txt").write_text(
    "72426;BR-XLX026 Brazil;C4FM/YSF;82.152.175.30;42000;000;\n"
)

# Never ship mutable state from a previous build/test.
for rel in (
    "rootfs-overlay/var/lib/2pny/provisioned",
    "rootfs-overlay/var/lib/2pny/wifi-scan.json",
    "rootfs-overlay/var/lib/2pny/network-connect.json",
    "rootfs-overlay/var/lib/2pny/rf-apply-state.json",
    "rootfs-overlay/var/lib/2pny/network-radio.json",
    "rootfs-overlay/var/lib/2pny/hostfiles-status.json",
    "rootfs-overlay/var/lib/2pny/maintenance.json",
    "rootfs-overlay/var/lib/2pny/auto-maintenance.last",
    "rootfs-overlay/var/lib/2pny/hosts/.updated",
):
    try:(root/rel).unlink()
    except FileNotFoundError:pass

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
for rel in (
    "rootfs-overlay/usr/local/sbin/2pny-network-core",
    "rootfs-overlay/usr/local/sbin/2pny-network-switch",
    "rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",
    "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
    "rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",
):
    subprocess.run(["bash","-n",str(root/rel)],check=True)
for rel in (
    "rootfs-overlay/usr/local/sbin/2pny-server-catalog",
    "rootfs-overlay/usr/local/sbin/2pny-live-status",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists(): shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
wizard=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
switch=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
network=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
core=(root/"rootfs-overlay/usr/local/sbin/2pny-network-core").read_text()

assert re.search(r'appVersion\s*=\s*"0\.2\.5-alpha"',main)
assert 'http.HandleFunc("/api/servers"' in main
assert 'http.HandleFunc("/api/live"' in main
assert 'selecione um servidor/master DMR válido' in main
assert '2pny-protocol-network-apply' in main
assert 'systemctl stop 2pny-network-core.service' not in switch
assert 'ap-scan-hold' in switch and 'ap-scan-hold' in core
assert 'PU2PNY-WIFI-CANDIDATE' in switch
assert '[DMR Network]' in network and '"Enable":"1"' in network
assert 'Servidor DMR' in wizard and '/api/servers' in wizard
assert 'singleWifiNote' in wizard
assert 'Ao vivo' in dash and '/api/live' in dash
assert (hosts/"DMR_Hosts.txt").exists()
print("PU2PNY 0.2.5 protocol/network/live patch applied")
