#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
root=Path('.')

# Version bump after hotfix3.
for rel in ['builder/build-image.sh','rootfs-overlay/usr/local/sbin/2pny-firstboot','src/2pnyd/main.go']:
    p=root/rel
    s=p.read_text()
    s=s.replace('0.1.7-hotfix3','0.1.7-hotfix4').replace('Alpha 0.1.7 hotfix3','Alpha 0.1.7 hotfix4')
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.7-hotfix4\n')

# Direct Ethernet gets its own subnet so Ethernet and Wi-Fi AP can coexist.
conn=root/'rootfs-overlay/etc/NetworkManager/system-connections'
conn.mkdir(parents=True,exist_ok=True)
(conn/'2pny-ethernet-setup.nmconnection').write_text('''[connection]
id=2PNY-Ethernet-Setup
uuid=7ec42a49-a77d-49f7-a181-2a4f00000003
type=ethernet
autoconnect=true
autoconnect-priority=90
mdns=2

[ethernet]

[ipv4]
method=shared
address1=10.43.0.1/24
may-fail=false

[ipv6]
method=disabled

[proxy]
''')

# AP remains open and independent from Ethernet.
ap=root/'rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection'
ap.write_text('''[connection]
id=2PNY-SETUP
uuid=5d9da2d9-3b48-4936-8201-2a4f00000002
type=wifi
autoconnect=false
autoconnect-priority=100
mdns=2

[wifi]
mode=ap
band=bg
channel=6
ssid=2PNY-SETUP
powersave=2

[wifi-security]
key-mgmt=none
auth-alg=open

[ipv4]
method=shared
address1=10.42.0.1/24
may-fail=false

[ipv6]
method=disabled

[proxy]
''')

# AP button must never touch Ethernet.
apctl=root/'rootfs-overlay/usr/local/sbin/2pny-ap-control'
s=apctl.read_text()
s=s.replace('    nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true\n','')
apctl.write_text(s)

# Dual-transport self-healing watcher. Ethernet and AP are maintained independently.
watch=root/'rootfs-overlay/usr/local/sbin/2pny-setup-watch'
watch.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
AP=2PNY-SETUP
ETHSET=2PNY-Ethernet-Setup
DISABLED="$STATE/ap-disabled"
SLEEP=3
mkdir -p "$STATE"
log(){ logger -t 2pny-setup-watch -- "$*" 2>/dev/null || true; }
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
eth_if(){
  local x
  x="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"&&$1!="lo"{print $1;exit}')"
  [[ -n "$x" ]] || x="$(for p in /sys/class/net/eth* /sys/class/net/en*; do [[ -e "$p" ]] && { basename "$p"; break; }; done 2>/dev/null)"
  printf '%s' "$x"
}
wifi_if(){
  local x
  x="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
  [[ -n "$x" ]] || x="$(for p in /sys/class/net/wlan*; do [[ -e "$p" ]] && { basename "$p"; break; }; done 2>/dev/null)"
  printf '%s' "$x"
}
carrier(){ local i="$1"; [[ -n "$i" && -r "/sys/class/net/$i/carrier" ]] && [[ "$(cat "/sys/class/net/$i/carrier" 2>/dev/null || echo 0)" == 1 ]]; }
has_ip(){ local i="$1" ip="$2"; [[ -n "$i" ]] && ip -4 -o addr show dev "$i" 2>/dev/null | grep -q " $ip/24 "; }

normalize_ap(){
  local w="$1"
  nmcli connection modify "$AP" \
    connection.interface-name "$w" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    802-11-wireless.channel 6 \
    802-11-wireless.powersave 2 \
    802-11-wireless-security.key-mgmt none \
    802-11-wireless-security.auth-alg open \
    ipv4.method shared ipv4.addresses 10.42.0.1/24 ipv4.may-fail no \
    ipv6.method disabled connection.autoconnect no connection.mdns yes >/dev/null 2>&1
}
normalize_eth(){
  local e="$1"
  nmcli connection modify "$ETHSET" \
    connection.interface-name "$e" \
    ipv4.method shared ipv4.addresses 10.43.0.1/24 ipv4.may-fail no \
    ipv6.method disabled connection.autoconnect yes connection.mdns yes >/dev/null 2>&1
}
start_ap(){
  local w="$1"
  rfkill unblock wifi >/dev/null 2>&1 || true
  nmcli radio wifi on >/dev/null 2>&1 || true
  ip link set "$w" up >/dev/null 2>&1 || true
  normalize_ap "$w" || return 1
  nmcli --wait 15 connection up "$AP" ifname "$w" >/dev/null 2>&1 || return 1
  for _ in {1..20}; do has_ip "$w" 10.42.0.1 && return 0; sleep .25; done
  return 1
}
start_eth(){
  local e="$1"
  normalize_eth "$e" || return 1
  nmcli --wait 15 connection up "$ETHSET" ifname "$e" >/dev/null 2>&1 || return 1
  for _ in {1..20}; do has_ip "$e" 10.43.0.1 && return 0; sleep .25; done
  return 1
}

while [[ ! -f "$STATE/provisioned" ]]; do
  ETH="$(eth_if)"; WIFI="$(wifi_if)"

  # Ethernet direct access is independent. Cable insertion must never stop AP.
  if carrier "$ETH"; then
    if ! active "$ETHSET" || ! has_ip "$ETH" 10.43.0.1; then
      log "starting direct Ethernet setup on $ETH"
      nmcli connection down 2PNY-Ethernet >/dev/null 2>&1 || true
      start_eth "$ETH" || log 'Ethernet setup activation failed; retrying later'
    fi
  else
    active "$ETHSET" && nmcli connection down "$ETHSET" >/dev/null 2>&1 || true
  fi

  # Wi-Fi AP is also independent and remains visible while Ethernet is active.
  if [[ -f "$DISABLED" ]]; then
    active "$AP" && nmcli connection down "$AP" >/dev/null 2>&1 || true
  elif [[ -n "$WIFI" ]]; then
    if ! active "$AP" || ! has_ip "$WIFI" 10.42.0.1; then
      log "starting open setup AP on $WIFI"
      active "$AP" && nmcli connection down "$AP" >/dev/null 2>&1 || true
      start_ap "$WIFI" || log 'AP activation failed; retrying later'
    fi
  else
    log 'Wi-Fi device not found yet'
  fi

  sleep "$SLEEP"
done
log 'provisioned; setup watcher exiting'
exit 0
''')

# Firstboot starts the watcher and accepts either path while leaving both alive.
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
LOG=/run/2pny-firstboot.log
STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"; exec >>"$LOG" 2>&1
status_write(){ { echo '2PNY OS 0.1.7-hotfix4'; echo "stage=$1"; echo "time=$(date -Is)"; echo '[active]'; nmcli -t -f NAME,TYPE,DEVICE connection show --active 2>/dev/null || true; echo '[ipv4]'; ip -4 -br address show 2>/dev/null || true; } >"${STATUS}.tmp" 2>/dev/null || true; mv -f "${STATUS}.tmp" "$STATUS" 2>/dev/null || true; }
hostnamectl set-hostname 2pny 2>/dev/null || true
systemctl start NetworkManager.service 2>/dev/null || true
systemctl start 2pnyd.service 2>/dev/null || true
systemctl start avahi-daemon.service 2>/dev/null || true
status_write starting
if [[ -f "$STATE/provisioned" ]]; then status_write provisioned; exit 0; fi
raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
rfkill unblock wifi 2>/dev/null || true
nmcli radio wifi on 2>/dev/null || true
systemctl start 2pny-setup-watch.service 2>/dev/null || true
for _ in {1..90}; do
  WIFI_OK=0; ETH_OK=0
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.42\.0\.1/24 ' && WIFI_OK=1
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.43\.0\.1/24 ' && ETH_OK=1
  if (( WIFI_OK && ETH_OK )); then status_write ready-wifi-and-ethernet; exit 0; fi
  if (( WIFI_OK )); then status_write ready-wifi; exit 0; fi
  if (( ETH_OK )); then status_write ready-ethernet; exit 0; fi
  sleep .5
done
status_write waiting-network
exit 1
''')

# Remove obsolete single-owner assertions and add dual-network contract.
v=root/'builder/validate-source.sh'
lines=v.read_text().splitlines()
reject=(
  'single-owner setup networking',
  'owned exclusively by',
  "active \"$AP\" && has_ip \"$WIFI\"",
  'AP activation failed; recreating profile once',
)
lines=[ln for ln in lines if not any(x in ln for x in reject)]
vs='\n'.join(lines)+'\n'
marker='# 2PNY_HOTFIX4_DUAL_NETWORK'
if marker not in vs:
    vs += r'''
# 2PNY_HOTFIX4_DUAL_NETWORK
echo "[2PNY] Validate simultaneous Ethernet + Wi-Fi setup"
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
grep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q 'address1=10.43.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection
grep -q 'Ethernet direct access is independent' rootfs-overlay/usr/local/sbin/2pny-setup-watch
grep -q 'Wi-Fi AP is also independent' rootfs-overlay/usr/local/sbin/2pny-setup-watch
! grep -q 'nmcli connection down 2PNY-Ethernet-Setup' rootfs-overlay/usr/local/sbin/2pny-ap-control
grep -q '^DumpTAData=1$' rootfs-overlay/usr/local/sbin/2pny-rf-apply
grep -q '0.1.7-hotfix4' src/2pnyd/main.go
'''
v.write_text(vs)
PY

chmod 0755 rootfs-overlay/usr/local/sbin/2pny-firstboot rootfs-overlay/usr/local/sbin/2pny-setup-watch rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control

echo '2PNY 0.1.7 hotfix4 simultaneous Ethernet and Wi-Fi setup applied'
