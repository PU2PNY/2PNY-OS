#!/usr/bin/env python3
from pathlib import Path
import os, re, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.2.3-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.2.3.go","src/2pnyd/main.go",0o644)
install("src/2pny-network-switch-0.2.3","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-rf-apply-0.2.3","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/wizard-0.2.3.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.2.3.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

for rel in ("builder/build-image.sh","rootfs-overlay/usr/local/sbin/2pny-firstboot"):
    p=root/rel
    if not p.exists(): continue
    s=p.read_text().replace("0.2.2-alpha",version)
    p.write_text(s)

# Ensure no stale scan state or provisioning data ships in the image.
for rel in (
    "rootfs-overlay/var/lib/2pny/provisioned",
    "rootfs-overlay/var/lib/2pny/wifi-scan.json",
    "rootfs-overlay/var/lib/2pny/network-connect.json",
    "rootfs-overlay/var/lib/2pny/rf-apply-state.json",
    "rootfs-overlay/var/lib/2pny/display-runtime.json",
):
    try:(root/rel).unlink()
    except FileNotFoundError:pass

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply")],check=True)

main=(root/"src/2pnyd/main.go").read_text()
wizard=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
switch=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()

assert re.search(r'appVersion\s*=\s*"0\.2\.3-alpha"',main)
assert 'dashboardFile' in main and '/api/dashboard' in main
assert 'wifiScanStateFile' in main and 'startWiFiScan' in main
assert 'http.Redirect(w, r, "/dashboard"' in main
assert 'in.UseMode == "repeater"' in main
assert "systemctl stop 2pny-network-core.service" in switch
assert "scan_json()" in switch
assert "ScreenLayout=2" in rf
assert "display-runtime.json" in rf
assert "Abrir painel principal" in wizard
assert "Alterar rede" in wizard
assert "txWrap" in wizard and "syncUseMode" in wizard
assert "/api/wifi/scan" in wizard
assert "Painel principal" in dash and "/api/dashboard" in dash
print("PU2PNY 0.2.3 dashboard/network patch applied")
