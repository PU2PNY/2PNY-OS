#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
root=Path('.')

p=root/'builder/build-image.sh'
s=p.read_text()
s=s.replace('VERSION="${VERSION:-0.1.1-alpha}"','VERSION="${VERSION:-0.1.2-alpha}"')
s=s.replace(
    'network-manager avahi-daemon dnsmasq-base ca-certificates curl iproute2 iw i2c-tools usbutils python3',
    'network-manager avahi-daemon dnsmasq-base ca-certificates curl iproute2 iw i2c-tools usbutils python3 \\\n  wpasupplicant rfkill wireless-regdb'
)
s=s.replace(
    'chmod 0755 "${ROOT_MNT}/etc/NetworkManager/dispatcher.d/90-2pny-connectivity"\n',
    'chmod 0755 "${ROOT_MNT}/etc/NetworkManager/dispatcher.d/90-2pny-connectivity"\nchmod 0600 "${ROOT_MNT}/etc/NetworkManager/system-connections/"*.nmconnection\n'
)
p.write_text(s)

p=root/'src/2pnyd/main.go'
s=p.read_text().replace('appVersion      = "0.1.1-alpha"','appVersion      = "0.1.2-alpha"').replace('<b>Alpha 0.1.1:</b>','<b>Alpha 0.1.2:</b>')
p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.2-alpha\n')

p=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
p.write_text('''#!/bin/bash
set -euo pipefail
STATE=/var/lib/2pny
LOG=/var/log/2pny-firstboot.log
mkdir -p "$STATE"
exec >>"$LOG" 2>&1

echo "[$(date -Is)] 2PNY first boot 0.1.2-alpha"
hostnamectl set-hostname 2pny || true
systemctl enable --now NetworkManager.service || true
systemctl enable --now avahi-daemon.service || true
rfkill unblock wifi 2>/dev/null || true
nmcli radio wifi on 2>/dev/null || true

if [[ -f "$STATE/provisioned" ]]; then
  exit 0
fi

for _ in {1..30}; do
  nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break
  sleep 1
done

ETH_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}')"
if [[ -n "${ETH_IF:-}" ]]; then
  nmcli connection modify "2PNY-Ethernet" connection.autoconnect yes connection.autoconnect-priority 50 2>/dev/null || true
  nmcli connection up "2PNY-Ethernet" >/dev/null 2>&1 || true
  echo "Ethernet prepared on ${ETH_IF}"
fi

WIFI_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
if [[ -n "${WIFI_IF:-}" ]]; then
  ip link set "$WIFI_IF" up 2>/dev/null || true
  nmcli radio wifi on 2>/dev/null || true
  nmcli connection up "2PNY-SETUP" >/dev/null 2>&1 || true
  echo "Setup hotspot requested on ${WIFI_IF}: SSID=2PNY-SETUP IP=10.42.0.1"
else
  echo "No Wi-Fi interface detected. Ethernet DHCP/mDNS remains available."
fi

systemctl restart avahi-daemon.service || true
systemctl restart 2pnyd.service || true
ip -4 address show || true
nmcli device status || true
echo "[$(date -Is)] first boot ready"
''')

conn=root/'rootfs-overlay/etc/NetworkManager/system-connections'
conn.mkdir(parents=True,exist_ok=True)
(conn/'2pny-ethernet.nmconnection').write_text('''[connection]
id=2PNY-Ethernet
uuid=7ec42a49-a77d-49f7-a181-2a4f00000001
type=ethernet
autoconnect=true
autoconnect-priority=50

[ethernet]

[ipv4]
method=auto

[ipv6]
method=auto
addr-gen-mode=default

[proxy]
''')
(conn/'2pny-setup.nmconnection').write_text('''[connection]
id=2PNY-SETUP
uuid=5d9da2d9-3b48-4936-8201-2a4f00000002
type=wifi
interface-name=wlan0
autoconnect=true
autoconnect-priority=100

[wifi]
mode=ap
band=bg
channel=6
ssid=2PNY-SETUP

[wifi-security]
key-mgmt=wpa-psk
psk=2pnysetup

[ipv4]
method=shared
address1=10.42.0.1/24

[ipv6]
method=disabled

[proxy]
''')

p=root/'rootfs-overlay/etc/systemd/system/2pnyd.service'
s=p.read_text().replace('After=network.target\nWants=network.target','After=NetworkManager.service network-online.target\nWants=NetworkManager.service network-online.target')
p.write_text(s)

p=root/'builder/validate-source.sh'
s=p.read_text().replace(
    'rootfs-overlay/etc/systemd/system/2pny-firstboot.service; do',
    'rootfs-overlay/etc/systemd/system/2pny-firstboot.service \\\n  rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet.nmconnection \\\n  rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection; do'
)
p.write_text(s)
PY

chmod +x builder/build-image.sh builder/validate-source.sh rootfs-overlay/usr/local/sbin/2pny-firstboot

echo "2PNY 0.1.2 network/first-boot patch applied"
