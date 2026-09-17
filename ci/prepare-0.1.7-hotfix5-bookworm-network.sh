#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
root=Path('.')

# Version
for rel in ['builder/build-image.sh','rootfs-overlay/usr/local/sbin/2pny-firstboot','src/2pnyd/main.go']:
    p=root/rel
    s=p.read_text()
    s=s.replace('0.1.7-hotfix4','0.1.7-hotfix5').replace('Alpha 0.1.7 hotfix4','Alpha 0.1.7 hotfix5')
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.7-hotfix5\n')

# Pin the supported Raspberry Pi OS Legacy / Debian Bookworm image instead of
# the newly-released Trixie image. This deliberately removes a moving base from
# first-access networking while retaining current Raspberry Pi firmware/kernel.
b=root/'builder/build-image.sh'
s=b.read_text()
s=re.sub(r'https://downloads\.raspberrypi\.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-09-15/2026-09-15-raspios-trixie-arm64-lite\.img\.xz',
         'https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-09-15/2026-09-15-raspios-bookworm-arm64-lite.img.xz', s)
s=s.replace('cdf4f3bfac35ae947b46e4e767f935453810549779ac3290e05a6754aee627e5',
            'bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91')
s=s.replace('Raspberry Pi OS Lite 2026-09-15', 'Raspberry Pi OS Legacy Lite Bookworm 2026-09-15')
b.write_text(s)

# NetworkManager must not synthesize an in-memory "Wired connection 1" that
# can grab eth0 before the appliance profile.
conf=root/'rootfs-overlay/etc/NetworkManager/conf.d/20-2pny-appliance.conf'
conf.parent.mkdir(parents=True,exist_ok=True)
conf.write_text('''[main]\nno-auto-default=*\n\n[device]\nwifi.scan-rand-mac-address=no\n''')

# Open AP: no security setting at all. This is the canonical unencrypted
# NetworkManager profile and avoids treating key-mgmt=none as legacy WEP.
ap=root/'rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection'
ap.write_text('''[connection]\nid=2PNY-SETUP\nuuid=5d9da2d9-3b48-4936-8201-2a4f00000002\ntype=wifi\nautoconnect=false\nautoconnect-priority=100\nmdns=2\n\n[wifi]\nmode=ap\nband=bg\nssid=2PNY-SETUP\npowersave=2\n\n[ipv4]\nmethod=shared\naddress1=10.42.0.1/24\nnever-default=true\nmay-fail=false\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')

eth=root/'rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection'
eth.write_text('''[connection]\nid=2PNY-Ethernet-Setup\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000003\ntype=ethernet\nautoconnect=true\nautoconnect-priority=200\nmdns=2\n\n[ethernet]\n\n[ipv4]\nmethod=shared\naddress1=10.43.0.1/24\nnever-default=true\nmay-fail=false\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')

# Rebuild AP helper without security mutations that can make an open AP invalid.
apctl=root/'rootfs-overlay/usr/local/sbin/2pny-ap-control'
apctl.write_text(r'''#!/bin/bash
set -euo pipefail
ACTION="${1:-status}"
PROFILE=2PNY-SETUP
DISABLED_MARKER=/var/lib/2pny/ap-disabled
wifi_if(){
  local x
  x="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
  [[ -n "$x" ]] || x="$(for p in /sys/class/net/wlan*; do [[ -e "$p" ]] && { basename "$p"; break; }; done 2>/dev/null)"
  printf '%s' "$x"
}
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
has_ip(){ local i="$1"; [[ -n "$i" ]] && ip -4 -o addr show dev "$i" 2>/dev/null | grep -q ' 10\.42\.0\.1/24 '; }
normalize(){
  local w="$1"
  nmcli connection modify "$PROFILE" \
    connection.interface-name "$w" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    802-11-wireless.powersave 2 \
    ipv4.method shared \
    ipv4.addresses 10.42.0.1/24 \
    ipv4.never-default yes \
    ipv4.may-fail no \
    ipv6.method disabled \
    connection.autoconnect no \
    connection.mdns yes >/dev/null
  # An open network has no 802-11-wireless-security setting.
  nmcli connection modify "$PROFILE" remove 802-11-wireless-security 2>/dev/null || true
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
    ip link set "$WIFI" up >/dev/null 2>&1 || true
    normalize "$WIFI"
    nmcli --wait 20 connection up id "$PROFILE" ifname "$WIFI" >/dev/null
    for _ in {1..30}; do has_ip "$WIFI" && { echo 'AP 2PNY-SETUP ativo e aberto'; exit 0; }; sleep .25; done
    echo 'AP ativou sem 10.42.0.1' >&2; exit 3
    ;;
  off)
    mkdir -p /var/lib/2pny; touch "$DISABLED_MARKER"
    nmcli connection down id "$PROFILE" >/dev/null 2>&1 || true
    echo 'AP 2PNY-SETUP desativado'
    ;;
  *) echo 'uso: 2pny-ap-control status|on|off' >&2; exit 2;;
esac
''')

# Single boot supervisor. It removes any auto-generated Ethernet profile, then
# maintains Ethernet and AP independently. It never reports ready from files;
# readiness requires real interface addresses.
watch=root/'rootfs-overlay/usr/local/sbin/2pny-setup-watch'
watch.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
AP=2PNY-SETUP
ETHSET=2PNY-Ethernet-Setup
DISABLED="$STATE/ap-disabled"
mkdir -p "$STATE"
log(){ logger -t 2pny-setup-watch -- "$*" 2>/dev/null || true; }
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
eth_if(){ local x; x="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"&&$1!="lo"{print $1;exit}')"; [[ -n "$x" ]] || x="$(for p in /sys/class/net/eth* /sys/class/net/en*; do [[ -e "$p" ]] && { basename "$p"; break; }; done 2>/dev/null)"; printf '%s' "$x"; }
wifi_if(){ local x; x="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"; [[ -n "$x" ]] || x="$(for p in /sys/class/net/wlan*; do [[ -e "$p" ]] && { basename "$p"; break; }; done 2>/dev/null)"; printf '%s' "$x"; }
carrier(){ local i="$1"; [[ -n "$i" && -r "/sys/class/net/$i/carrier" ]] && [[ "$(cat "/sys/class/net/$i/carrier" 2>/dev/null || echo 0)" == 1 ]]; }
has_ip(){ local i="$1" a="$2"; [[ -n "$i" ]] && ip -4 -o addr show dev "$i" 2>/dev/null | grep -q " $a/24 "; }

prepare_nm(){
  rfkill unblock wifi >/dev/null 2>&1 || true
  nmcli radio wifi on >/dev/null 2>&1 || true
  # Remove auto-created Ethernet profiles; 2PNY owns direct setup explicitly.
  while IFS=: read -r name type; do
    [[ "$type" == ethernet && "$name" != "$ETHSET" && "$name" != "2PNY-Ethernet" ]] || continue
    nmcli connection down id "$name" >/dev/null 2>&1 || true
    nmcli connection delete id "$name" >/dev/null 2>&1 || true
  done < <(nmcli -t -f NAME,TYPE connection show 2>/dev/null || true)
}
prepare_nm

while [[ ! -f "$STATE/provisioned" ]]; do
  ETH="$(eth_if)"; WIFI="$(wifi_if)"

  if carrier "$ETH"; then
    if ! active "$ETHSET" || ! has_ip "$ETH" 10.43.0.1; then
      nmcli connection down id "$ETHSET" >/dev/null 2>&1 || true
      nmcli connection modify "$ETHSET" connection.interface-name "$ETH" ipv4.method shared ipv4.addresses 10.43.0.1/24 ipv4.never-default yes ipv4.may-fail no ipv6.method disabled connection.autoconnect yes connection.mdns yes >/dev/null 2>&1 || true
      if nmcli --wait 20 connection up id "$ETHSET" ifname "$ETH" >/dev/null 2>&1; then log "Ethernet ready on $ETH 10.43.0.1"; else log 'Ethernet activation failed'; fi
    fi
  fi

  if [[ -f "$DISABLED" ]]; then
    active "$AP" && nmcli connection down id "$AP" >/dev/null 2>&1 || true
  elif [[ -n "$WIFI" ]]; then
    if ! active "$AP" || ! has_ip "$WIFI" 10.42.0.1; then
      /usr/local/sbin/2pny-ap-control on >/dev/null 2>&1 && log "Wi-Fi AP ready on $WIFI 10.42.0.1" || log 'Wi-Fi AP activation failed'
    fi
  else
    log 'Wi-Fi device not detected yet'
  fi
  sleep 4
done
exit 0
''')

# Firstboot must not falsely succeed; it leaves the supervisor running and only
# records observed state.
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"
status_write(){ { echo '2PNY OS 0.1.7-hotfix5'; echo "stage=$1"; echo "time=$(date -Is)"; echo '[active]'; nmcli -t -f NAME,TYPE,DEVICE connection show --active 2>/dev/null || true; echo '[ipv4]'; ip -4 -br address show 2>/dev/null || true; echo '[rfkill]'; rfkill list 2>/dev/null || true; } >"${STATUS}.tmp" 2>/dev/null || true; mv -f "${STATUS}.tmp" "$STATUS" 2>/dev/null || true; }
hostnamectl set-hostname 2pny 2>/dev/null || true
systemctl start NetworkManager.service 2>/dev/null || true
systemctl start 2pnyd.service 2>/dev/null || true
systemctl start avahi-daemon.service 2>/dev/null || true
raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
rfkill unblock wifi 2>/dev/null || true
nmcli radio wifi on 2>/dev/null || true
systemctl restart NetworkManager.service 2>/dev/null || true
sleep 2
systemctl start 2pny-setup-watch.service 2>/dev/null || true
for _ in {1..120}; do
  W=0; E=0
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.42\.0\.1/24 ' && W=1
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.43\.0\.1/24 ' && E=1
  if (( W && E )); then status_write ready-wifi-and-ethernet; exit 0; fi
  if (( W )); then status_write ready-wifi; exit 0; fi
  if (( E )); then status_write ready-ethernet; exit 0; fi
  sleep .5
done
status_write network-not-ready
exit 1
''')

# Current panel captive DNS wildcard is unsafe for the Ethernet subnet. Keep
# the OS captive-probe HTTP endpoints, but do not force every DNS name to 10.42.
captive=root/'rootfs-overlay/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf'
captive.parent.mkdir(parents=True,exist_ok=True)
captive.write_text('''# 2PNY hotfix5: DHCP/DNS is provided by NetworkManager shared mode.\n# Captive detection uses HTTP probe endpoints in 2pnyd; no global wildcard DNS.\n''')

# Update source validator contract.
v=root/'builder/validate-source.sh'
vs=v.read_text().replace('0.1.7-hotfix4','0.1.7-hotfix5')
if '# 2PNY_HOTFIX5_BOOKWORM_NETWORK' not in vs:
    vs += r'''
# 2PNY_HOTFIX5_BOOKWORM_NETWORK
echo "[2PNY] Validate Bookworm deterministic networking"
grep -q 'raspios_oldstable_lite_arm64' builder/build-image.sh
grep -q 'bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91' builder/build-image.sh
grep -q '^no-auto-default=\*$' rootfs-overlay/etc/NetworkManager/conf.d/20-2pny-appliance.conf
! grep -q '\[wifi-security\]' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q 'address1=10.43.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection
grep -q 'never-default=true' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q 'never-default=true' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
grep -q 'DumpTAData=1' rootfs-overlay/usr/local/sbin/2pny-rf-apply
grep -q '0.1.7-hotfix5' src/2pnyd/main.go
'''
v.write_text(vs)
PY

chmod 0755 rootfs-overlay/usr/local/sbin/2pny-ap-control rootfs-overlay/usr/local/sbin/2pny-setup-watch rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot

echo '2PNY 0.1.7 hotfix5 Bookworm deterministic network applied'
