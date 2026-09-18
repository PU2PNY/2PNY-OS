#!/usr/bin/env python3
from pathlib import Path
import os, re, shutil, subprocess, sys

root = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parents[1]
version = "0.2.2-alpha"

def install(src, dst, mode):
    target = root / dst
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / src, target)
    os.chmod(target, mode)

install("src/2pnyd-main-0.2.2.go", "src/2pnyd/main.go", 0o644)
install("src/2pny-network-core-0.2.2", "rootfs-overlay/usr/local/sbin/2pny-network-core", 0o755)
install("src/2pny-network-switch-0.2.2", "rootfs-overlay/usr/local/sbin/2pny-network-switch", 0o755)
install("src/2pny-rf-apply-0.2.2", "rootfs-overlay/usr/local/sbin/2pny-rf-apply", 0o755)
install("src/2pny-mode-apply-0.2.2", "rootfs-overlay/usr/local/sbin/2pny-mode-apply", 0o755)
install("src/2pny-hardware-probe-0.2.2.py", "rootfs-overlay/usr/local/sbin/2pny-hardware-probe", 0o755)
install("src/2pny-mmdvmhost-0.2.2.service", "rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service", 0o644)
install("src/wizard-0.2.2.html", "rootfs-overlay/usr/share/2pny/wizard.html", 0o644)

for rel in ("builder/build-image.sh", "rootfs-overlay/usr/local/sbin/2pny-firstboot"):
    p = root / rel
    text = p.read_text()
    for old in ("0.2.1-alpha", "0.2.0-alpha", "0.1.9-hotfix1-alpha", "0.1.9-alpha"):
        text = text.replace(old, version)
    text = text.replace("pu2pnu-os", "PU2PNY").replace("PU2PNY OS", "PU2PNY")
    p.write_text(text)

(root / "rootfs-overlay/etc/2pny/version").write_text(version + "\n")

share = root / "rootfs-overlay/usr/share/2pny/network"
(share / "dnsmasq-ap.template").write_text("""interface=@IFACE@
bind-dynamic
listen-address=10.43.0.1
port=53
dhcp-authoritative
dhcp-range=10.43.0.20,10.43.0.200,255.255.255.0,12h
dhcp-option=3,10.43.0.1
dhcp-option=6,10.43.0.1
dhcp-option-force=114,http://10.43.0.1/captive-api
address=/pu2pny.local/10.43.0.1
address=/connectivitycheck.gstatic.com/10.43.0.1
address=/clients3.google.com/10.43.0.1
address=/captive.apple.com/10.43.0.1
address=/www.msftconnecttest.com/10.43.0.1
address=/www.msftncsi.com/10.43.0.1
""")
(share / "dnsmasq-eth.template").write_text("""interface=@IFACE@
bind-dynamic
port=0
dhcp-authoritative
dhcp-range=10.43.0.20,10.43.0.200,255.255.255.0,12h
dhcp-option=3
dhcp-option=6
dhcp-option-force=114,http://10.43.0.1/captive-api
""")

hostapd = share / "hostapd.template"
hostapd.write_text(re.sub(r"(?m)^ssid=.*$", "ssid=pu2pny", hostapd.read_text()))

avahi = root / "rootfs-overlay/etc/avahi/services/2pny-http.service"
if avahi.exists():
    avahi.write_text(avahi.read_text().replace("PU2PNY OS on %h", "PU2PNY on %h"))

websvc = root / "rootfs-overlay/etc/systemd/system/2pnyd.service"
if websvc.exists():
    websvc.write_text(websvc.read_text().replace("Description=2PNY Core and local panel", "Description=PU2PNY Core and local panel"))

for rel in (
    "rootfs-overlay/var/lib/2pny/provisioned",
    "rootfs-overlay/var/lib/2pny/rf-configured",
    "rootfs-overlay/var/lib/2pny/rf-apply-state.json",
    "rootfs-overlay/var/lib/2pny/network-connect.json",
    "rootfs-overlay/var/lib/2pny/uplink-ssid",
    "rootfs-overlay/var/lib/2pny/basic-radio.json",
):
    try:
        (root / rel).unlink()
    except FileNotFoundError:
        pass

checks = [
    ["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-network-core")],
    ["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch")],
    ["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply")],
    ["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-mode-apply")],
    ["python3","-m","py_compile",str(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe")],
    ["gofmt","-w",str(root/"src/2pnyd/main.go")],
]
for cmd in checks:
    subprocess.run(cmd, check=True)

cache = root / "rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists():
    shutil.rmtree(cache)

main = (root / "src/2pnyd/main.go").read_text()
wizard = (root / "rootfs-overlay/usr/share/2pny/wizard.html").read_text()
rf = (root / "rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
probe = (root / "rootfs-overlay/usr/local/sbin/2pny-hardware-probe").read_text()
service = (root / "rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service").read_text()

assert '"0.2.2-alpha"' in main
assert re.search(r'Name:\s*"PU2PNY"', main)
assert "time.AfterFunc(2500*time.Millisecond" in main
assert "10.42.0.1" not in wizard
assert "http://10.43.0.1/" in wizard
assert "http://pu2pny.local/" in wizard
assert "CONFIG=/var/lib/2pny/mmdvm/MMDVM-Host.ini" in rf
assert "mktemp /run/2pny/.MMDVM-Host.ini.XXXXXX" in rf
assert "/var/lib/2pny/mmdvm/MMDVM-Host.ini" in service
assert "nextion_mmdvm" in probe
assert "def spi_devices" in probe
assert "921600" in probe
assert (share / "hostapd.template").read_text().find("ssid=pu2pny") >= 0
print("PU2PNY 0.2.2 patch applied")
