#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

VERSION="0.2.1-alpha"

install -m 0644 "$SELF_DIR/../src/2pnyd-main-0.2.1.go" src/2pnyd/main.go
install -m 0755 "$SELF_DIR/../src/2pny-network-core-0.2.1" rootfs-overlay/usr/local/sbin/2pny-network-core
install -m 0755 "$SELF_DIR/../src/2pny-network-switch-0.2.1" rootfs-overlay/usr/local/sbin/2pny-network-switch
install -D -m 0644 "$SELF_DIR/../src/wizard-0.2.1.html" rootfs-overlay/usr/share/2pny/wizard.html

python3 - <<'PY'
from pathlib import Path

version = "0.2.1-alpha"
root = Path(".")

for rel in [
    "builder/build-image.sh",
    "rootfs-overlay/usr/local/sbin/2pny-firstboot",
]:
    p = root / rel
    s = p.read_text()
    for old in ("0.2.0-alpha", "0.1.9-hotfix1-alpha", "0.1.9-alpha"):
        s = s.replace(old, version)
    s = s.replace("PU2PNY OS", "pu2pnu-os")
    p.write_text(s)

(root / "rootfs-overlay/etc/2pny/version").write_text(version + "\n")

hostapd = root / "rootfs-overlay/usr/share/2pny/network/hostapd.template"
h = hostapd.read_text()
lines = []
for line in h.splitlines():
    if line.startswith("ssid="):
        lines.append("ssid=pu2pny")
    else:
        lines.append(line)
hostapd.write_text("\n".join(lines) + "\n")

share = root / "rootfs-overlay/usr/share/2pny/network"

ap = share / "dnsmasq-ap.template"
a = ap.read_text()
if "dhcp-option-force=114," not in a:
    a += "dhcp-option-force=114,http://10.42.0.1/captive-api\n"
ap.write_text(a)

eth = share / "dnsmasq-eth.template"
e = eth.read_text()
if "dhcp-option-force=114," not in e:
    e += "dhcp-option-force=114,http://10.43.0.1/captive-api\n"
eth.write_text(e)

av = root / "rootfs-overlay/etc/avahi/services/2pny-http.service"
if av.exists():
    t = av.read_text().replace("PU2PNY OS on %h", "pu2pnu-os on %h")
    av.write_text(t)

svc = root / "rootfs-overlay/etc/systemd/system/2pny-network-core.service"
if svc.exists():
    t = svc.read_text()
    t = t.replace("PU2PNY dual-uplink first-access network core", "pu2pnu-os resilient first-access network core")
    svc.write_text(t)

for rel in [
    "rootfs-overlay/var/lib/2pny/provisioned",
    "rootfs-overlay/var/lib/2pny/setup-state.json",
    "rootfs-overlay/var/lib/2pny/rf-apply-state.json",
    "rootfs-overlay/var/lib/2pny/network-connect.json",
    "rootfs-overlay/var/lib/2pny/uplink-ssid",
    "rootfs-overlay/var/lib/2pny/basic-radio.json",
]:
    p = root / rel
    try:
        p.unlink()
    except FileNotFoundError:
        pass
PY

chmod 0755   rootfs-overlay/usr/local/sbin/2pny-network-core   rootfs-overlay/usr/local/sbin/2pny-network-switch

bash -n rootfs-overlay/usr/local/sbin/2pny-network-core
bash -n rootfs-overlay/usr/local/sbin/2pny-network-switch
gofmt -w src/2pnyd/main.go

grep -Eq 'appVersion[[:space:]]*=[[:space:]]*"0\.2\.1-alpha"' src/2pnyd/main.go
grep -Fq '/api/network/connect/status' src/2pnyd/main.go
grep -Fq '/captive-api' src/2pnyd/main.go
grep -Fq 'scan-json' src/2pnyd/main.go
grep -Fq 'wifiScan' rootfs-overlay/usr/share/2pny/wizard.html
grep -Fq 'showPass' rootfs-overlay/usr/share/2pny/wizard.html
grep -Fq 'ssidSelect' rootfs-overlay/usr/share/2pny/wizard.html
grep -Fq 'pu2pnu-os' rootfs-overlay/usr/share/2pny/wizard.html
grep -q '^ssid=pu2pny$' rootfs-overlay/usr/share/2pny/network/hostapd.template
! grep -q '^ssid=2PNY-SETUP$' rootfs-overlay/usr/share/2pny/network/hostapd.template
grep -q '^dhcp-option-force=114,http://10.42.0.1/captive-api$' rootfs-overlay/usr/share/2pny/network/dnsmasq-ap.template
grep -q '^dhcp-option-force=114,http://10.43.0.1/captive-api$' rootfs-overlay/usr/share/2pny/network/dnsmasq-eth.template
grep -Fq '10.43.0.11/24' rootfs-overlay/usr/local/sbin/2pny-network-core
grep -Fq 'PU2PNY-ETH-AUTO' rootfs-overlay/usr/local/sbin/2pny-network-core
grep -Fq 'LAST_CARRIER' rootfs-overlay/usr/local/sbin/2pny-network-core

echo 'pu2pnu-os 0.2.1 network and onboarding fixes applied'
