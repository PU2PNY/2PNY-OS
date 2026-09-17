#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

root = Path('.')

# Version bump only after all previous 0.1.7 hotfix2 patches have been applied.
for rel in ['builder/build-image.sh', 'rootfs-overlay/usr/local/sbin/2pny-firstboot', 'src/2pnyd/main.go']:
    p = root / rel
    s = p.read_text()
    s = s.replace('0.1.7-hotfix2', '0.1.7-hotfix3').replace('Alpha 0.1.7 hotfix2', 'Alpha 0.1.7 hotfix3')
    p.write_text(s)
(root / 'rootfs-overlay/etc/2pny/version').write_text('0.1.7-hotfix3\n')

# Deterministic open AP profile. Explicit key-mgmt=none avoids ambiguity between
# an absent security section and an open AP on different NetworkManager versions.
conn = root / 'rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection'
conn.write_text('''[connection]
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

# There must be exactly one owner of pre-provisioning transport state. The old
# dispatcher restarted firstboot on connectivity-change, which could tear down
# the AP while a Windows/phone client was associating.
disp = root / 'rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity'
disp.write_text(r'''#!/bin/bash
# 2PNY hotfix3: pre-provisioning connectivity is owned exclusively by
# 2pny-setup-watch. Do not restart firstboot from NetworkManager events.
exit 0
''')

# AP helper: persistent user switch without masking systemd units. Masking from
# inside the hardened panel service can fail because /etc is read-only there.
apctl = root / 'rootfs-overlay/usr/local/sbin/2pny-ap-control'
apctl.write_text(r'''#!/bin/bash
set -euo pipefail
ACTION="${1:-status}"
PROFILE=2PNY-SETUP
DISABLED_MARKER=/var/lib/2pny/ap-disabled
wifi_if(){ nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}'; }
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
has_ip(){ local i="$1"; [[ -n "$i" ]] && ip -4 -o addr show dev "$i" 2>/dev/null | grep -q ' 10\.42\.0\.1/24 '; }
normalize(){
  local w="$1"
  if ! nmcli -t -f NAME connection show 2>/dev/null | grep -Fxq "$PROFILE"; then
    nmcli connection add type wifi ifname "$w" con-name "$PROFILE" ssid 2PNY-SETUP autoconnect no >/dev/null
  fi
  nmcli connection modify "$PROFILE" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    802-11-wireless.channel 6 \
    802-11-wireless.powersave 2 \
    802-11-wireless-security.key-mgmt none \
    802-11-wireless-security.auth-alg open \
    ipv4.method shared \
    ipv4.addresses 10.42.0.1/24 \
    ipv4.may-fail no \
    ipv6.method disabled \
    connection.autoconnect no \
    connection.mdns yes >/dev/null
}
case "$ACTION" in
  status)
    WIFI="$(wifi_if)"
    if active "$PROFILE" && has_ip "$WIFI"; then echo active; else echo inactive; fi
    ;;
  on)
    WIFI="$(wifi_if)"; [[ -n "$WIFI" ]] || { echo 'Wi-Fi não detectado' >&2; exit 2; }
    mkdir -p /var/lib/2pny; rm -f "$DISABLED_MARKER"
    rfkill unblock wifi >/dev/null 2>&1 || true
    nmcli radio wifi on >/dev/null 2>&1 || true
    nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true
    normalize "$WIFI"
    nmcli --wait 15 connection up "$PROFILE" ifname "$WIFI" >/dev/null
    for _ in {1..20}; do has_ip "$WIFI" && { echo 'AP 2PNY-SETUP ativo e aberto'; exit 0; }; sleep .25; done
    echo 'AP ativou sem o IP 10.42.0.1' >&2; exit 3
    ;;
  off)
    mkdir -p /var/lib/2pny; touch "$DISABLED_MARKER"
    nmcli connection down "$PROFILE" >/dev/null 2>&1 || true
    echo 'AP 2PNY-SETUP desativado'
    ;;
  *) echo 'uso: 2pny-ap-control status|on|off' >&2; exit 2;;
esac
''')

# Single state machine for Ethernet/AP selection. It never cycles a healthy AP.
watch = root / 'rootfs-overlay/usr/local/sbin/2pny-setup-watch'
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
eth_if(){ nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}'; }
wifi_if(){ nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}'; }
carrier(){ local i="$1"; [[ -n "$i" && -r "/sys/class/net/$i/carrier" ]] && [[ "$(cat "/sys/class/net/$i/carrier" 2>/dev/null || echo 0)" == 1 ]]; }
has_ip(){ local i="$1"; [[ -n "$i" ]] && ip -4 -o addr show dev "$i" 2>/dev/null | grep -q ' 10\.42\.0\.1/24 '; }
normalize_ap(){
  local w="$1"
  if ! nmcli -t -f NAME connection show 2>/dev/null | grep -Fxq "$AP"; then
    nmcli connection add type wifi ifname "$w" con-name "$AP" ssid 2PNY-SETUP autoconnect no >/dev/null 2>&1 || return 1
  fi
  nmcli connection modify "$AP" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    802-11-wireless.channel 6 \
    802-11-wireless.powersave 2 \
    802-11-wireless-security.key-mgmt none \
    802-11-wireless-security.auth-alg open \
    ipv4.method shared \
    ipv4.addresses 10.42.0.1/24 \
    ipv4.may-fail no \
    ipv6.method disabled \
    connection.autoconnect no \
    connection.mdns yes >/dev/null 2>&1
}
start_ap(){
  local w="$1"
  rfkill unblock wifi >/dev/null 2>&1 || true
  nmcli radio wifi on >/dev/null 2>&1 || true
  normalize_ap "$w" || return 1
  nmcli connection down "$ETHSET" >/dev/null 2>&1 || true
  if ! nmcli --wait 15 connection up "$AP" ifname "$w" >/dev/null 2>&1; then
    log 'AP activation failed; recreating profile once'
    nmcli connection delete "$AP" >/dev/null 2>&1 || true
    normalize_ap "$w" || return 1
    nmcli --wait 15 connection up "$AP" ifname "$w" >/dev/null 2>&1 || return 1
  fi
  for _ in {1..20}; do has_ip "$w" && return 0; sleep .25; done
  return 1
}

while [[ ! -f "$STATE/provisioned" ]]; do
  ETH="$(eth_if)"; WIFI="$(wifi_if)"

  if carrier "$ETH"; then
    # Ethernet setup owns 10.42.0.1 while carrier is present.
    if active "$AP"; then nmcli connection down "$AP" >/dev/null 2>&1 || true; fi
    if ! active "$ETHSET" || ! has_ip "$ETH"; then
      log "selecting direct Ethernet setup on $ETH"
      nmcli connection down "$ETHSET" >/dev/null 2>&1 || true
      nmcli --wait 15 connection up "$ETHSET" ifname "$ETH" >/dev/null 2>&1 || true
    fi
    sleep "$SLEEP"; continue
  fi

  if active "$ETHSET"; then nmcli connection down "$ETHSET" >/dev/null 2>&1 || true; fi

  # Explicit panel switch wins: do not resurrect the AP when disabled.
  if [[ -f "$DISABLED" ]]; then
    active "$AP" && nmcli connection down "$AP" >/dev/null 2>&1 || true
    sleep "$SLEEP"; continue
  fi

  if [[ -z "$WIFI" ]]; then log 'Wi-Fi device not found'; sleep "$SLEEP"; continue; fi

  # Healthy means both connection active and gateway address present. Leave it
  # untouched so clients can associate without a restart race.
  if active "$AP" && has_ip "$WIFI"; then sleep "$SLEEP"; continue; fi

  if active "$AP"; then nmcli connection down "$AP" >/dev/null 2>&1 || true; fi
  log "starting open setup AP on $WIFI"
  if ! start_ap "$WIFI"; then
    log 'AP unhealthy after activation; will retry with backoff'
    nmcli connection down "$AP" >/dev/null 2>&1 || true
    sleep 8; continue
  fi
  log 'AP ready at 10.42.0.1'
  sleep "$SLEEP"
done
log 'provisioned; setup watcher exiting'
exit 0
''')

# firstboot only initializes prerequisites and waits for the authoritative watcher.
fb = root / 'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
LOG=/run/2pny-firstboot.log
STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"; exec >>"$LOG" 2>&1
status_write(){ { echo '2PNY OS 0.1.7-hotfix3'; echo "stage=$1"; echo "time=$(date -Is)"; echo '[active]'; nmcli -t -f NAME,TYPE,DEVICE connection show --active 2>/dev/null || true; echo '[ipv4]'; ip -4 -br address show 2>/dev/null || true; } >"${STATUS}.tmp" 2>/dev/null || true; mv -f "${STATUS}.tmp" "$STATUS" 2>/dev/null || true; }
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
for _ in {1..60}; do
  if ip -4 -o addr show 2>/dev/null | grep -q ' 10\.42\.0\.1/24 '; then
    if nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq '2PNY-Ethernet-Setup'; then status_write ready-ethernet; exit 0; fi
    if nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq '2PNY-SETUP'; then status_write ready-wifi; exit 0; fi
  fi
  sleep .5
done
status_write waiting-network
# The watcher remains active and self-healing; a retry of this oneshot is safe.
exit 1
''')

# Keep the watcher writable only where needed and give NetworkManager time to settle.
svc = root / 'rootfs-overlay/etc/systemd/system/2pny-setup-watch.service'
svc.write_text('''[Unit]
Description=2PNY first-access transport state machine
After=NetworkManager.service
Wants=NetworkManager.service
ConditionPathExists=!/var/lib/2pny/provisioned
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/usr/local/sbin/2pny-setup-watch
Restart=always
RestartSec=3
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadOnlyPaths=/sys
MemoryMax=24M
TasksMax=24

[Install]
WantedBy=multi-user.target
''')

# Build contract for the physical-network hotfix.
v = root / 'builder/validate-source.sh'
vs = v.read_text().replace("grep -q '0.1.7-hotfix2' src/2pnyd/main.go", "grep -q '0.1.7-hotfix3' src/2pnyd/main.go")
if '# 2PNY_HOTFIX3_NETWORK_STABILITY' not in vs:
    vs += '''\n# 2PNY_HOTFIX3_NETWORK_STABILITY\necho "[2PNY] Validate single-owner setup networking"\nbash -n rootfs-overlay/usr/local/sbin/2pny-firstboot\nbash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch\nbash -n rootfs-overlay/usr/local/sbin/2pny-ap-control\ngrep -q 'key-mgmt=none' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'auth-alg=open' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'powersave=2' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'method=shared' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'owned exclusively by' rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity\n! grep -q 'restart 2pny-firstboot' rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity\ngrep -q 'active "$AP" && has_ip "$WIFI"' rootfs-overlay/usr/local/sbin/2pny-setup-watch\ngrep -q 'AP activation failed; recreating profile once' rootfs-overlay/usr/local/sbin/2pny-setup-watch\ngrep -q 'DISABLED_MARKER=/var/lib/2pny/ap-disabled' rootfs-overlay/usr/local/sbin/2pny-ap-control\n! grep -q 'systemctl mask' rootfs-overlay/usr/local/sbin/2pny-ap-control\ngrep -q '0.1.7-hotfix3' src/2pnyd/main.go\n'''
v.write_text(vs)
PY

chmod 0755 \
  rootfs-overlay/usr/local/sbin/2pny-firstboot \
  rootfs-overlay/usr/local/sbin/2pny-setup-watch \
  rootfs-overlay/usr/local/sbin/2pny-ap-control \
  rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity
chmod 0600 rootfs-overlay/etc/NetworkManager/system-connections/*.nmconnection
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control

echo '2PNY 0.1.7 hotfix3 single-owner/self-healing setup network applied'
