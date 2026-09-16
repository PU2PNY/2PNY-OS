#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
root = Path('.')

p = root/'builder/build-image.sh'
s = p.read_text()
s = s.replace('VERSION="${VERSION:-0.1.2-alpha}"','VERSION="${VERSION:-0.1.3-alpha}"')
needle = 'chmod 0600 "${ROOT_MNT}/etc/NetworkManager/system-connections/"*.nmconnection\n'
insert = '''chmod 0600 "${ROOT_MNT}/etc/NetworkManager/system-connections/"*.nmconnection
# Raspberry Pi OS Trixie uses cloud-init on first boot. 2PNY owns networking itself.
CMDLINE="${ROOT_MNT}/boot/firmware/cmdline.txt"
grep -qw 'network-config=disabled' "$CMDLINE" || sed -i '1 s/$/ network-config=disabled/' "$CMDLINE"
grep -qw 'cfg80211.ieee80211_regdom=BR' "$CMDLINE" || sed -i '1 s/$/ cfg80211.ieee80211_regdom=BR/' "$CMDLINE"
mkdir -p "${ROOT_MNT}/var/lib/NetworkManager"
cat > "${ROOT_MNT}/var/lib/NetworkManager/NetworkManager.state" <<'NMSTATE'
[main]
NetworkingEnabled=true
WirelessEnabled=true
WWANEnabled=true
NMSTATE
rm -f "${ROOT_MNT}/var/lib/systemd/rfkill/"*:wlan 2>/dev/null || true
'''
if needle not in s:
    raise SystemExit('build-image patch anchor not found')
s = s.replace(needle, insert, 1)
p.write_text(s)

p = root/'src/2pnyd/main.go'
s = p.read_text().replace('appVersion      = "0.1.2-alpha"','appVersion      = "0.1.3-alpha"').replace('<b>Alpha 0.1.2:</b>','<b>Alpha 0.1.3:</b>')
p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.3-alpha\n')

cloud = root/'rootfs-overlay/etc/cloud/cloud.cfg.d'
cloud.mkdir(parents=True, exist_ok=True)
(cloud/'99-2pny-appliance.cfg').write_text('''# 2PNY owns first-boot networking and identity.
network:
  config: disabled
disable_network_activation: true
preserve_hostname: true
''')

nmstate = root/'rootfs-overlay/var/lib/NetworkManager'
nmstate.mkdir(parents=True, exist_ok=True)
(nmstate/'NetworkManager.state').write_text('''[main]
NetworkingEnabled=true
WirelessEnabled=true
WWANEnabled=true
''')

conn = root/'rootfs-overlay/etc/NetworkManager/system-connections'
(conn/'2pny-ethernet.nmconnection').write_text('''[connection]
id=2PNY-Ethernet
uuid=7ec42a49-a77d-49f7-a181-2a4f00000001
type=ethernet
autoconnect=true
autoconnect-priority=50
mdns=2

[ethernet]

[ipv4]
method=auto
link-local=4
dhcp-timeout=10

[ipv6]
method=auto
addr-gen-mode=default

[proxy]
''')

(conn/'2pny-setup.nmconnection').write_text('''[connection]
id=2PNY-SETUP
uuid=5d9da2d9-3b48-4936-8201-2a4f00000002
type=wifi
autoconnect=true
autoconnect-priority=100
mdns=2

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

p = root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
p.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
LOG=/var/log/2pny-firstboot.log
mkdir -p "$STATE"
exec >>"$LOG" 2>&1

echo "[$(date -Is)] 2PNY first boot 0.1.3-alpha"
hostnamectl set-hostname 2pny || true
systemctl start NetworkManager.service || true
systemctl start avahi-daemon.service || true

if [[ -f "$STATE/provisioned" ]]; then
  echo "already provisioned"
  exit 0
fi

raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
for f in /var/lib/systemd/rfkill/*:wlan; do
  [[ -e "$f" ]] && echo 0 > "$f" 2>/dev/null || true
done
rfkill unblock wifi 2>/dev/null || true
nmcli radio wifi on 2>/dev/null || true

for _ in {1..60}; do
  nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break
  sleep 1
done

ETH_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}')"
if [[ -n "${ETH_IF:-}" ]]; then
  nmcli connection modify 2PNY-Ethernet connection.autoconnect yes connection.autoconnect-priority 50 2>/dev/null || true
  nmcli --wait 12 connection up 2PNY-Ethernet ifname "$ETH_IF" >/dev/null 2>&1 || true
  echo "Ethernet prepared on ${ETH_IF}; DHCP + link-local fallback"
fi

WIFI_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
AP_OK=0
if [[ -n "${WIFI_IF:-}" ]]; then
  echo "Wi-Fi detected: ${WIFI_IF}"
  ip link set "$WIFI_IF" up 2>/dev/null || true
  rfkill unblock wifi 2>/dev/null || true
  nmcli radio wifi on 2>/dev/null || true

  for attempt in {1..6}; do
    echo "AP attempt ${attempt}/6"
    if nmcli --wait 15 connection up 2PNY-SETUP ifname "$WIFI_IF" >/dev/null 2>&1; then
      AP_OK=1
      break
    fi

    if [[ "$attempt" -eq 2 ]]; then
      nmcli connection delete 2PNY-SETUP >/dev/null 2>&1 || true
      if nmcli --wait 15 device wifi hotspot ifname "$WIFI_IF" con-name 2PNY-SETUP \
           ssid 2PNY-SETUP band bg channel 6 password 2pnysetup >/dev/null 2>&1; then
        nmcli connection modify 2PNY-SETUP ipv4.method shared ipv4.addresses 10.42.0.1/24 \
          connection.autoconnect yes connection.autoconnect-priority 100 connection.mdns yes >/dev/null 2>&1 || true
        AP_OK=1
        break
      fi
    fi

    raspi-config nonint do_wifi_country BR 2>/dev/null || true
    rfkill unblock wifi 2>/dev/null || true
    nmcli radio wifi on 2>/dev/null || true
    sleep 5
  done

  if [[ "$AP_OK" -eq 1 ]]; then
    echo "Setup AP active: SSID=2PNY-SETUP IP=10.42.0.1"
  else
    echo "ERROR: Wi-Fi exists but 2PNY-SETUP could not be activated"
  fi
else
  echo "No Wi-Fi interface detected; Ethernet remains supported"
  AP_OK=1
fi

systemctl restart avahi-daemon.service || true
systemctl restart 2pnyd.service || true
sleep 2
ip -4 address show || true
nmcli radio all || true
nmcli device status || true
nmcli connection show --active || true

if [[ "$AP_OK" -ne 1 ]]; then
  echo "[$(date -Is)] first boot incomplete; systemd will retry"
  exit 1
fi

echo "[$(date -Is)] first boot ready"
exit 0
''')

p = root/'rootfs-overlay/etc/systemd/system/2pny-firstboot.service'
p.write_text('''[Unit]
Description=2PNY first boot provisioning
After=NetworkManager.service avahi-daemon.service
Wants=NetworkManager.service avahi-daemon.service
ConditionPathExists=!/var/lib/2pny/provisioned
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/2pny-firstboot
RemainAfterExit=yes
Restart=on-failure
RestartSec=10
TimeoutStartSec=180

[Install]
WantedBy=multi-user.target
''')

p = root/'rootfs-overlay/etc/systemd/system/2pnyd.service'
s = p.read_text()
s = s.replace('After=NetworkManager.service network-online.target\nWants=NetworkManager.service network-online.target',
              'After=NetworkManager.service\nWants=NetworkManager.service')
p.write_text(s)

p = root/'builder/validate-source.sh'
s = p.read_text()
anchor = 'rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection; do'
replacement = '''rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection \\
  rootfs-overlay/etc/cloud/cloud.cfg.d/99-2pny-appliance.cfg \\
  rootfs-overlay/var/lib/NetworkManager/NetworkManager.state; do'''
if anchor not in s:
    raise SystemExit('validate-source patch anchor not found')
s = s.replace(anchor, replacement, 1)
p.write_text(s)
PY

chmod +x builder/build-image.sh builder/validate-source.sh rootfs-overlay/usr/local/sbin/2pny-firstboot

echo "2PNY 0.1.3 Trixie/cloud-init/rfkill recovery patch applied"
