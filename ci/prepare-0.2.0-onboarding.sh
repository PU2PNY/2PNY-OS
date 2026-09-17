#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

VERSION="0.2.0-alpha"

install -m 0644 "$SELF_DIR/../src/2pnyd-main-0.2.0.go" src/2pnyd/main.go
install -m 0755 "$SELF_DIR/../src/2pny-network-core-0.2.0" rootfs-overlay/usr/local/sbin/2pny-network-core
install -m 0755 "$SELF_DIR/../src/2pny-network-switch-0.2.0" rootfs-overlay/usr/local/sbin/2pny-network-switch
install -m 0755 "$SELF_DIR/../src/2pny-hardware-prepare-0.2.0" rootfs-overlay/usr/local/sbin/2pny-hardware-prepare
install -m 0755 "$SELF_DIR/../src/2pny-mode-apply-0.2.0" rootfs-overlay/usr/local/sbin/2pny-mode-apply
install -D -m 0644 "$SELF_DIR/../src/wizard-0.2.0.html" rootfs-overlay/usr/share/2pny/wizard.html

python3 - <<'PY'
from pathlib import Path

version = "0.2.0-alpha"
root = Path(".")

for rel in [
    "builder/build-image.sh",
    "rootfs-overlay/usr/local/sbin/2pny-firstboot",
]:
    p = root / rel
    s = p.read_text()
    s = s.replace("0.1.9-hotfix1-alpha", version)
    s = s.replace("0.1.9-alpha", version)
    p.write_text(s)

(root / "rootfs-overlay/etc/2pny/version").write_text(version + "\n")

b = root / "builder/build-image.sh"
s = b.read_text()
if " iptables" not in s:
    s = s.replace("wireless-regdb", "wireless-regdb iptables", 1)
b.write_text(s)

share = root / "rootfs-overlay/usr/share/2pny/network"
share.mkdir(parents=True, exist_ok=True)

(share / "dnsmasq-ap.template").write_text("""interface=@IFACE@
bind-dynamic
listen-address=10.42.0.1
port=53
dhcp-authoritative
dhcp-range=10.42.0.20,10.42.0.200,255.255.255.0,12h
dhcp-option=3,10.42.0.1
dhcp-option=6,10.42.0.1
address=/pu2pny.local/10.42.0.1
address=/2pny.local/10.42.0.1
""")

(share / "dnsmasq-eth.template").write_text("""interface=@IFACE@
bind-dynamic
port=0
dhcp-authoritative
dhcp-range=10.43.0.20,10.43.0.200,255.255.255.0,12h
dhcp-option=3
dhcp-option=6
""")

svc = root / "rootfs-overlay/etc/systemd/system/2pny-network-core.service"
if svc.exists():
    text = svc.read_text().replace(
        "Description=2PNY deterministic first-access network core",
        "Description=PU2PNY dual-uplink first-access network core"
    )
    svc.write_text(text)

for rel in [
    "rootfs-overlay/var/lib/2pny/provisioned",
    "rootfs-overlay/var/lib/2pny/setup-state.json",
    "rootfs-overlay/var/lib/2pny/rf-apply-state.json",
    "rootfs-overlay/var/lib/2pny/uplink-ssid",
    "rootfs-overlay/var/lib/2pny/basic-radio.json",
]:
    p = root / rel
    try:
        p.unlink()
    except FileNotFoundError:
        pass
PY

chmod 0755 \
  rootfs-overlay/usr/local/sbin/2pny-network-core \
  rootfs-overlay/usr/local/sbin/2pny-network-switch \
  rootfs-overlay/usr/local/sbin/2pny-hardware-prepare \
  rootfs-overlay/usr/local/sbin/2pny-mode-apply

bash -n rootfs-overlay/usr/local/sbin/2pny-network-core
bash -n rootfs-overlay/usr/local/sbin/2pny-network-switch
bash -n rootfs-overlay/usr/local/sbin/2pny-hardware-prepare
bash -n rootfs-overlay/usr/local/sbin/2pny-mode-apply
python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__

gofmt -w src/2pnyd/main.go

grep -Eq 'appVersion[[:space:]]*=[[:space:]]*"0\.2\.0-alpha"' src/2pnyd/main.go
grep -Fq '/api/connectivity' src/2pnyd/main.go
grep -Fq '/api/network/connect' src/2pnyd/main.go
grep -Fq '/api/basic/apply' src/2pnyd/main.go
grep -Fq 'Primeiro acesso — Internet' rootfs-overlay/usr/share/2pny/wizard.html
grep -Fq 'Configuração básica' rootfs-overlay/usr/share/2pny/wizard.html
grep -Fq 'Hotspot' rootfs-overlay/usr/share/2pny/wizard.html
grep -Fq 'Repetidora' rootfs-overlay/usr/share/2pny/wizard.html
grep -Fq 'Crossmode' rootfs-overlay/usr/share/2pny/wizard.html
! grep -Fq 'RX Offset' rootfs-overlay/usr/share/2pny/wizard.html
! grep -Fq 'TX Offset' rootfs-overlay/usr/share/2pny/wizard.html
! grep -Fq 'Porta MMDVM detectada' rootfs-overlay/usr/share/2pny/wizard.html
grep -Eq '^dhcp-option=3$' rootfs-overlay/usr/share/2pny/network/dnsmasq-eth.template
grep -Eq '^dhcp-option=6$' rootfs-overlay/usr/share/2pny/network/dnsmasq-eth.template

echo 'PU2PNY OS 0.2.0 Internet-first onboarding applied'
