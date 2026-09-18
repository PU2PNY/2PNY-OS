#!/usr/bin/env python3
from pathlib import Path
import os, re, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.2.4-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.2.4.go","src/2pnyd/main.go",0o644)
install("src/2pny-network-core-0.2.4","rootfs-overlay/usr/local/sbin/2pny-network-core",0o755)
install("src/2pny-network-switch-0.2.4","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-rf-apply-0.2.4","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/2pny-hardware-probe-0.2.4.py","rootfs-overlay/usr/local/sbin/2pny-hardware-probe",0o755)
install("src/2pny-display-status-0.2.4.py","rootfs-overlay/usr/local/sbin/2pny-display-status",0o755)
install("src/2pny-auto-maintenance-0.2.4","rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",0o755)
install("src/2pny-auto-maintenance-0.2.4.service","rootfs-overlay/etc/systemd/system/2pny-auto-maintenance.service",0o644)
install("src/2pny-display-boot-0.2.4.service","rootfs-overlay/etc/systemd/system/2pny-display-boot.service",0o644)
install("src/wizard-0.2.4.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.2.4.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

for rel in ("builder/build-image.sh","rootfs-overlay/usr/local/sbin/2pny-firstboot"):
    p=root/rel
    if not p.exists(): continue
    s=p.read_text()
    for old in ("0.2.3-alpha","0.2.2-alpha","0.2.1-alpha"):
        s=s.replace(old,version)
    p.write_text(s)

enabled=root/"rootfs-overlay/var/lib/2pny/auto-maintenance.enabled"
enabled.parent.mkdir(parents=True,exist_ok=True)
enabled.write_text("enabled\n")
os.chmod(enabled,0o600)

wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
for service in ("2pny-auto-maintenance.service","2pny-display-boot.service"):
    link=wants/service
    if link.exists() or link.is_symlink(): link.unlink()
    link.symlink_to(Path("..")/service)

ap=root/"rootfs-overlay/usr/share/2pny/network/dnsmasq-ap.template"
s=ap.read_text()
extra=[
    "address=/detectportal.firefox.com/10.43.0.1",
    "address=/captive.gnome.org/10.43.0.1",
    "address=/nmcheck.gnome.org/10.43.0.1",
    "address=/connectivity-check.ubuntu.com/10.43.0.1",
    "address=/network-test.debian.org/10.43.0.1",
]
for line in extra:
    if line not in s: s += line+"\n"
ap.write_text(s)

for rel in (
    "rootfs-overlay/var/lib/2pny/provisioned",
    "rootfs-overlay/var/lib/2pny/wifi-scan.json",
    "rootfs-overlay/var/lib/2pny/network-connect.json",
    "rootfs-overlay/var/lib/2pny/rf-apply-state.json",
    "rootfs-overlay/var/lib/2pny/display-runtime.json",
    "rootfs-overlay/var/lib/2pny/display-status.json",
    "rootfs-overlay/var/lib/2pny/maintenance.json",
    "rootfs-overlay/var/lib/2pny/auto-maintenance.last",
):
    try:(root/rel).unlink()
    except FileNotFoundError:pass

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
for rel in (
    "rootfs-overlay/usr/local/sbin/2pny-network-core",
    "rootfs-overlay/usr/local/sbin/2pny-network-switch",
    "rootfs-overlay/usr/local/sbin/2pny-rf-apply",
    "rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",
):
    subprocess.run(["bash","-n",str(root/rel)],check=True)
for rel in (
    "rootfs-overlay/usr/local/sbin/2pny-hardware-probe",
    "rootfs-overlay/usr/local/sbin/2pny-display-status",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists(): shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
wizard=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
switch=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
probe=(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
maintenance=(root/"rootfs-overlay/usr/local/sbin/2pny-auto-maintenance").read_text()

assert re.search(r'appVersion\s*=\s*"0\.2\.4-alpha"',main)
assert 'http.HandleFunc("/api/maintenance"' in main
assert 'WiFiSSID' in main
assert 'case "${1:-}" in' in switch
assert 'case "\\${1:-}" in' not in switch
assert 'PU2PNY-WIFI-CANDIDATE' in switch
assert 'Não foi possível entrar na rede' in switch
assert 'probe_nextion_mmdvm' in probe
assert 'mmdvm_serial_confirmed' in probe
assert 'ScreenLayout=2' in rf and '2pny-display-status ready' in rf
assert 'autoMaintenance' in wizard and '/api/maintenance' in wizard
assert 'A última tentativa de Wi‑Fi falhou' in wizard
assert 'apt-get' in maintenance and 'upgrade' not in maintenance
assert enabled.exists()
print("PU2PNY 0.2.4 network/display/maintenance patch applied")
