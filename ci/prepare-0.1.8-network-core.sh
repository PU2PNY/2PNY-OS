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
    for old in ('0.1.7-hotfix5','0.1.7-hotfix4','0.1.7-hotfix3','0.1.7-alpha'):
        s=s.replace(old,'0.1.8-alpha')
    s=s.replace('Alpha 0.1.7 hotfix5','Alpha 0.1.8').replace('Alpha 0.1.7','Alpha 0.1.8')
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.8-alpha\n')

# hostapd + dnsmasq are explicit first-access engines, following the proven
# separation used by dedicated hotspot systems. Do not rely on NM shared mode.
b=root/'builder/build-image.sh'
s=b.read_text()
# Pin the final Bookworm ARM64 image by its official filename, URL and SHA-256.
# Earlier patches tried to replace one fully-expanded URL, while the builder
# stores the URL in shell variables, so the substitution never happened.
s=re.sub(r'^BASE_DATE=.*$', 'BASE_DATE="2026-09-15"', s, count=1, flags=re.M)
s=re.sub(r'^BASE_NAME=.*$', 'BASE_NAME="2026-09-15-raspios-bookworm-arm64-lite.img.xz"', s, count=1, flags=re.M)
s=re.sub(r'^BASE_URL=.*$', 'BASE_URL="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-09-15/${BASE_NAME}"', s, count=1, flags=re.M)
s=re.sub(r'^BASE_SHA256=.*$', 'BASE_SHA256="bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91"', s, count=1, flags=re.M)
s=s.replace('Debian 13 Trixie', 'Debian 12 Bookworm')
needle='wpasupplicant rfkill wireless-regdb'
if ' hostapd ' not in s and needle in s:
    s=s.replace(needle, needle+' hostapd dnsmasq iw', 1)
if 'hostapd' not in s or 'dnsmasq' not in s:
    raise SystemExit('could not add hostapd/dnsmasq to image package set')
b.write_text(s)

# Keep legacy NM setup profiles inert. They are fallback metadata only; the
# first-access network is owned by 2pny-network-core.
conn=root/'rootfs-overlay/etc/NetworkManager/system-connections'
conn.mkdir(parents=True,exist_ok=True)
(conn/'2pny-setup.nmconnection').write_text('''[connection]\nid=2PNY-SETUP-FALLBACK\nuuid=5d9da2d9-3b48-4936-8201-2a4f00000002\ntype=wifi\nautoconnect=false\n\n[wifi]\nmode=infrastructure\nssid=2PNY-SETUP\n\n[ipv4]\nmethod=disabled\n\n[ipv6]\nmethod=disabled\n''')
(conn/'2pny-ethernet-setup.nmconnection').write_text('''[connection]\nid=2PNY-Ethernet-Setup-Fallback\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000003\ntype=ethernet\nautoconnect=false\n\n[ethernet]\n\n[ipv4]\nmethod=disabled\n\n[ipv6]\nmethod=disabled\n''')

sbin=root/'rootfs-overlay/usr/local/sbin'; sbin.mkdir(parents=True,exist_ok=True)

(sbin/'2pny-network-core').write_text(r'''#!/bin/bash
set -u
RUN=/run/2pny
STATE=/var/lib/2pny
BOOT=/boot/firmware/2PNY-NETWORK.txt
mkdir -p "$RUN" "$STATE"

log(){ logger -t 2pny-network-core -- "$*" 2>/dev/null || true; echo "[$(date -Is)] $*" >>"$RUN/network.log"; }
find_eth(){ local p n; for p in /sys/class/net/eth* /sys/class/net/en*; do [[ -e "$p" ]] || continue; n="$(basename "$p")"; [[ "$n" != lo ]] && { echo "$n"; return; }; done; }
find_wifi(){ local p; for p in /sys/class/net/wlan* /sys/class/net/wl*; do [[ -e "$p" ]] || continue; basename "$p"; return; done; }
alive(){ [[ -n "${1:-}" ]] && kill -0 "$1" 2>/dev/null; }
readpid(){ [[ -r "$1" ]] && cat "$1" 2>/dev/null || true; }

if [[ "${1:-}" == "--self-test" ]]; then
  command -v hostapd >/dev/null
  command -v dnsmasq >/dev/null
  command -v iw >/dev/null
  command -v rfkill >/dev/null
  command -v nmcli >/dev/null
  grep -q '^ssid=2PNY-SETUP$' /usr/share/2pny/network/hostapd.template
  grep -q '10.42.0.20,10.42.0.200' /usr/share/2pny/network/dnsmasq-ap.template
  grep -q '10.43.0.20,10.43.0.200' /usr/share/2pny/network/dnsmasq-eth.template
  echo '2PNY network core self-test OK'
  exit 0
fi

ETH="$(find_eth)"
WIFI="$(find_wifi)"
HOSTAPD_PID=""; DNS_AP_PID=""; DNS_ETH_PID=""

write_status(){
  local stage="$1"
  {
    echo '2PNY OS 0.1.8-alpha'
    echo "stage=$stage"
    echo "time=$(date -Is)"
    echo "ethernet_if=${ETH:-none}"
    echo "wifi_if=${WIFI:-none}"
    echo 'wifi_setup_ip=10.42.0.1'
    echo 'ethernet_setup_ip=10.43.0.1'
    [[ -n "$WIFI" ]] && ip -4 -o addr show dev "$WIFI" 2>/dev/null || true
    [[ -n "$ETH" ]] && ip -4 -o addr show dev "$ETH" 2>/dev/null || true
    echo "hostapd=$(alive "$HOSTAPD_PID" && echo active || echo inactive)"
    echo "dnsmasq_ap=$(alive "$DNS_AP_PID" && echo active || echo inactive)"
    echo "dnsmasq_eth=$(alive "$DNS_ETH_PID" && echo active || echo inactive)"
  } >"$RUN/network-status.txt"
  cp -f "$RUN/network-status.txt" "$BOOT.tmp" 2>/dev/null && mv -f "$BOOT.tmp" "$BOOT" 2>/dev/null || true
}

stop_ap(){
  local p
  p="$(readpid "$RUN/hostapd.pid")"; [[ -n "$p" ]] && kill "$p" 2>/dev/null || true
  p="$(readpid "$RUN/dnsmasq-ap.pid")"; [[ -n "$p" ]] && kill "$p" 2>/dev/null || true
  rm -f "$RUN/hostapd.pid" "$RUN/dnsmasq-ap.pid"
  HOSTAPD_PID=""; DNS_AP_PID=""
}

start_ap(){
  [[ -n "$WIFI" ]] || return 1
  rfkill unblock wifi >/dev/null 2>&1 || true
  iw reg set BR >/dev/null 2>&1 || true
  nmcli device disconnect "$WIFI" >/dev/null 2>&1 || true
  nmcli device set "$WIFI" managed no >/dev/null 2>&1 || true
  ip link set "$WIFI" down >/dev/null 2>&1 || true
  ip addr flush dev "$WIFI" >/dev/null 2>&1 || true
  sleep .4
  ip link set "$WIFI" up >/dev/null 2>&1 || true
  ip addr add 10.42.0.1/24 dev "$WIFI" >/dev/null 2>&1 || ip addr replace 10.42.0.1/24 dev "$WIFI" >/dev/null 2>&1 || return 1
  sed "s/@IFACE@/$WIFI/g" /usr/share/2pny/network/hostapd.template >"$RUN/hostapd.conf"
  sed "s/@IFACE@/$WIFI/g" /usr/share/2pny/network/dnsmasq-ap.template >"$RUN/dnsmasq-ap.conf"
  hostapd -P "$RUN/hostapd.pid" "$RUN/hostapd.conf" >>"$RUN/hostapd.log" 2>&1 &
  HOSTAPD_PID=$!
  sleep 1
  alive "$HOSTAPD_PID" || { log 'hostapd failed'; return 1; }
  dnsmasq --keep-in-foreground --conf-file="$RUN/dnsmasq-ap.conf" --pid-file="$RUN/dnsmasq-ap.pid" >>"$RUN/dnsmasq-ap.log" 2>&1 &
  DNS_AP_PID=$!
  sleep .5
  alive "$DNS_AP_PID" || { log 'dnsmasq AP failed'; stop_ap; return 1; }
  log "Wi-Fi AP 2PNY-SETUP active on $WIFI / 10.42.0.1"
  return 0
}

start_eth(){
  [[ -n "$ETH" ]] || return 1
  nmcli device disconnect "$ETH" >/dev/null 2>&1 || true
  nmcli device set "$ETH" managed no >/dev/null 2>&1 || true
  ip link set "$ETH" up >/dev/null 2>&1 || true
  ip addr flush dev "$ETH" >/dev/null 2>&1 || true
  ip addr add 10.43.0.1/24 dev "$ETH" >/dev/null 2>&1 || ip addr replace 10.43.0.1/24 dev "$ETH" >/dev/null 2>&1 || return 1
  sed "s/@IFACE@/$ETH/g" /usr/share/2pny/network/dnsmasq-eth.template >"$RUN/dnsmasq-eth.conf"
  dnsmasq --keep-in-foreground --conf-file="$RUN/dnsmasq-eth.conf" --pid-file="$RUN/dnsmasq-eth.pid" >>"$RUN/dnsmasq-eth.log" 2>&1 &
  DNS_ETH_PID=$!
  sleep .5
  alive "$DNS_ETH_PID" || { log 'dnsmasq Ethernet failed'; return 1; }
  log "Direct Ethernet active on $ETH / 10.43.0.1"
  return 0
}

cleanup(){
  stop_ap
  local p
  p="$(readpid "$RUN/dnsmasq-eth.pid")"; [[ -n "$p" ]] && kill "$p" 2>/dev/null || true
  rm -f "$RUN/dnsmasq-eth.pid"
  [[ -n "$ETH" ]] && { ip addr del 10.43.0.1/24 dev "$ETH" 2>/dev/null || true; nmcli device set "$ETH" managed yes >/dev/null 2>&1 || true; }
  [[ -n "$WIFI" ]] && { ip addr del 10.42.0.1/24 dev "$WIFI" 2>/dev/null || true; nmcli device set "$WIFI" managed yes >/dev/null 2>&1 || true; }
  write_status stopped
}
trap cleanup EXIT TERM INT

[[ -f "$STATE/provisioned" ]] && { write_status provisioned; exit 0; }
systemctl start NetworkManager.service >/dev/null 2>&1 || true
systemctl start avahi-daemon.service >/dev/null 2>&1 || true

if [[ -n "$ETH" ]]; then start_eth || log 'Ethernet setup failed'; else log 'Ethernet interface not detected'; fi
if [[ ! -f "$STATE/ap-disabled" && -n "$WIFI" ]]; then start_ap || log 'Wi-Fi AP setup failed'; else log 'Wi-Fi AP disabled or interface absent'; fi
write_status ready

while [[ ! -f "$STATE/provisioned" ]]; do
  if [[ -n "$ETH" ]] && ! alive "$DNS_ETH_PID"; then start_eth || true; fi
  if [[ -f "$STATE/ap-disabled" ]]; then
    alive "$HOSTAPD_PID" && stop_ap
  elif [[ -n "$WIFI" ]]; then
    if ! alive "$HOSTAPD_PID" || ! alive "$DNS_AP_PID"; then stop_ap; start_ap || true; fi
  fi
  write_status ready
  sleep 3
done
log 'Provisioning complete; releasing interfaces to NetworkManager'
exit 0
''')

(sbin/'2pny-network-switch').write_text(r'''#!/bin/bash
set -euo pipefail
SSID="${1:-}"
PASS="${2:-}"
[[ -n "$SSID" ]] || { echo 'SSID vazio' >&2; exit 2; }
find_wifi(){ local p; for p in /sys/class/net/wlan* /sys/class/net/wl*; do [[ -e "$p" ]] || continue; basename "$p"; return; done; }
WIFI="$(find_wifi)"
[[ -n "$WIFI" ]] || { echo 'interface Wi-Fi não encontrada' >&2; exit 3; }
systemctl stop 2pny-network-core.service >/dev/null 2>&1 || true
sleep 1
rfkill unblock wifi >/dev/null 2>&1 || true
nmcli radio wifi on >/dev/null 2>&1 || true
nmcli device set "$WIFI" managed yes >/dev/null 2>&1 || true
nmcli connection delete 2PNY-WIFI >/dev/null 2>&1 || true
nmcli device wifi rescan ifname "$WIFI" >/dev/null 2>&1 || true
if [[ -n "$PASS" ]]; then
  OUT="$(nmcli --wait 35 device wifi connect "$SSID" password "$PASS" ifname "$WIFI" name 2PNY-WIFI 2>&1)" || { echo "$OUT" >&2; systemctl start 2pny-network-core.service >/dev/null 2>&1 || true; exit 4; }
else
  OUT="$(nmcli --wait 35 device wifi connect "$SSID" ifname "$WIFI" name 2PNY-WIFI 2>&1)" || { echo "$OUT" >&2; systemctl start 2pny-network-core.service >/dev/null 2>&1 || true; exit 4; }
fi
nmcli connection modify 2PNY-WIFI connection.autoconnect yes connection.autoconnect-priority 60 connection.mdns yes >/dev/null 2>&1 || true
echo 'Wi-Fi conectado'
''')

(sbin/'2pny-ap-control').write_text(r'''#!/bin/bash
set -euo pipefail
STATE=/var/lib/2pny
mkdir -p "$STATE"
case "${1:-status}" in
  on) rm -f "$STATE/ap-disabled"; systemctl restart 2pny-network-core.service >/dev/null 2>&1 || true; echo 'AP habilitado';;
  off) touch "$STATE/ap-disabled"; echo 'AP desabilitado';;
  status) [[ -f "$STATE/ap-disabled" ]] && echo inactive || echo active;;
  *) echo 'uso: 2pny-ap-control on|off|status' >&2; exit 2;;
esac
''')

share=root/'rootfs-overlay/usr/share/2pny/network'; share.mkdir(parents=True,exist_ok=True)
(share/'hostapd.template').write_text('''country_code=BR\ninterface=@IFACE@\ndriver=nl80211\nssid=2PNY-SETUP\nhw_mode=g\nchannel=6\nauth_algs=1\nwpa=0\nignore_broadcast_ssid=0\nlogger_syslog=-1\nlogger_syslog_level=2\n''')
(share/'dnsmasq-ap.template').write_text('''interface=@IFACE@\nbind-dynamic\nlisten-address=10.42.0.1\nport=53\ndhcp-authoritative\ndhcp-range=10.42.0.20,10.42.0.200,255.255.255.0,12h\ndhcp-option=3,10.42.0.1\ndhcp-option=6,10.42.0.1\naddress=/#/10.42.0.1\nno-resolv\nno-hosts\n''')
(share/'dnsmasq-eth.template').write_text('''interface=@IFACE@\nbind-dynamic\nlisten-address=10.43.0.1\nport=53\ndhcp-authoritative\ndhcp-range=10.43.0.20,10.43.0.200,255.255.255.0,12h\ndhcp-option=3,10.43.0.1\ndhcp-option=6,10.43.0.1\naddress=/#/10.43.0.1\nno-resolv\nno-hosts\n''')

svc=root/'rootfs-overlay/etc/systemd/system'; svc.mkdir(parents=True,exist_ok=True)
(svc/'2pny-network-core.service').write_text('''[Unit]\nDescription=2PNY deterministic first-access network core\nAfter=NetworkManager.service systemd-rfkill.service\nWants=NetworkManager.service\nBefore=2pnyd.service\n\n[Service]\nType=simple\nExecStart=/usr/local/sbin/2pny-network-core\nRestart=on-failure\nRestartSec=2\nTimeoutStopSec=8\nMemoryMax=64M\nTasksMax=64\n\n[Install]\nWantedBy=multi-user.target\n''')

# Disable distro daemons and inherited setup supervisors. The binaries are used
# only by 2pny-network-core so there is a single network owner.
for name in ('hostapd.service','dnsmasq.service','2pny-firstboot.service','2pny-setup-watch.service'):
    p=svc/name
    try: p.unlink()
    except FileNotFoundError: pass
    p.symlink_to('/dev/null')
w=svc/'multi-user.target.wants'; w.mkdir(parents=True,exist_ok=True)
for name in ('2pny-firstboot.service','2pny-setup-watch.service'):
    p=w/name
    try: p.unlink()
    except FileNotFoundError: pass
p=w/'2pny-network-core.service'
try: p.unlink()
except FileNotFoundError: pass
p.symlink_to('/etc/systemd/system/2pny-network-core.service')

# Route Wi-Fi handoff through the new network core instead of asking
# NetworkManager to fight a running AP.
go=root/'src/2pnyd/main.go'
gs=go.read_text()
marker='2PNY_NETWORK_CORE_HANDOFF_V1'
if marker not in gs:
    signature=re.compile(r'func connectConfiguredWiFi\(ssid\s*,\s*password string\) error \{\n')
    match=signature.search(gs)
    if not match: raise SystemExit('connectConfiguredWiFi signature not found')
    inject=match.group(0)+'\t// 2PNY_NETWORK_CORE_HANDOFF_V1\n\tif fileExists("/usr/local/sbin/2pny-network-switch") {\n\t\tb,err:=exec.Command("/usr/local/sbin/2pny-network-switch",ssid,password).CombinedOutput()\n\t\tif err!=nil { msg:=strings.TrimSpace(string(b)); if msg=="" { msg=err.Error() }; return fmt.Errorf("Wi-Fi não conectou: %s",msg) }\n\t\treturn nil\n\t}\n'
    gs=gs[:match.start()]+inject+gs[match.end():]
go.write_text(gs)
PY

chmod 0755 rootfs-overlay/usr/local/sbin/2pny-network-core \
  rootfs-overlay/usr/local/sbin/2pny-network-switch \
  rootfs-overlay/usr/local/sbin/2pny-ap-control
chmod 0600 rootfs-overlay/etc/NetworkManager/system-connections/*.nmconnection
bash -n rootfs-overlay/usr/local/sbin/2pny-network-core
bash -n rootfs-overlay/usr/local/sbin/2pny-network-switch
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
gofmt -w src/2pnyd/main.go

echo '2PNY 0.1.8 deterministic hostapd/dnsmasq network core applied'
