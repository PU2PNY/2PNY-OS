#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
root=Path('.')

for rel in ['builder/build-image.sh','src/2pnyd/main.go']:
    p=root/rel
    s=p.read_text()
    s=re.sub(r'0\.1\.7-hotfix5', '0.1.8-alpha', s)
    s=re.sub(r'Alpha 0\.1\.7 hotfix5', 'Alpha 0.1.8', s)
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.8-alpha\n')

b=root/'builder/build-image.sh'
s=b.read_text()
marker='# 2PNY_NETWORK_CORE_PACKAGES_V1'
if marker not in s:
    anchor='''# 2PNY_NETWORK_CORE_PACKAGES_V1
chroot "$MNT_ROOT" /bin/bash -lc 'export DEBIAN_FRONTEND=noninteractive; apt-get update; apt-get install -y --no-install-recommends hostapd dnsmasq-base iw rfkill avahi-daemon; systemctl disable hostapd.service 2>/dev/null || true; systemctl disable dnsmasq.service 2>/dev/null || true; rm -rf /var/lib/apt/lists/*'
'''
    for token in ['xz -T0', 'xz -T', 'echo "Build complete', 'echo "[OK]']:
        pos=s.find(token)
        if pos!=-1:
            s=s[:pos]+anchor+s[pos:]
            break
    else:
        s += '\n'+anchor
b.write_text(s)

for rel in [
    'rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection',
    'rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection',
]:
    p=root/rel
    if p.exists(): p.unlink()

nmconf=root/'rootfs-overlay/etc/NetworkManager/conf.d/20-2pny-appliance.conf'
nmconf.parent.mkdir(parents=True,exist_ok=True)
nmconf.write_text('''[main]\nno-auto-default=*\n\n[device]\nwifi.scan-rand-mac-address=no\n''')

hostapd=root/'rootfs-overlay/etc/2pny/hostapd-setup.conf'
hostapd.parent.mkdir(parents=True,exist_ok=True)
hostapd.write_text('''interface=wlan0\ndriver=nl80211\nssid=2PNY-SETUP\ncountry_code=BR\nhw_mode=g\nchannel=6\nbeacon_int=100\ndtim_period=2\nwmm_enabled=1\nieee80211n=1\nauth_algs=1\nignore_broadcast_ssid=0\nwpa=0\nctrl_interface=/run/hostapd\n''')

(root/'rootfs-overlay/etc/2pny/dnsmasq-wifi.conf').write_text('''interface=wlan0\nbind-interfaces\nexcept-interface=lo\nport=53\ndomain-needed\nbogus-priv\nno-resolv\nserver=8.8.8.8\nserver=1.1.1.1\ndhcp-range=10.42.0.20,10.42.0.150,255.255.255.0,1h\ndhcp-option=3,10.42.0.1\ndhcp-option=6,10.42.0.1\naddress=/#/10.42.0.1\ndhcp-authoritative\nlog-dhcp\n''')
(root/'rootfs-overlay/etc/2pny/dnsmasq-ethernet.conf').write_text('''interface=eth0\nbind-interfaces\nexcept-interface=lo\nport=0\ndhcp-range=10.43.0.20,10.43.0.150,255.255.255.0,1h\ndhcp-option=3,10.43.0.1\ndhcp-authoritative\nlog-dhcp\n''')

ctl=root/'rootfs-overlay/usr/local/sbin/2pny-network-core'
ctl.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
RUN=/run/2pny
mkdir -p "$STATE" "$RUN" /run/hostapd
log(){ logger -t 2pny-network-core -- "$*" 2>/dev/null || true; }
proc_alive(){ [[ -r "$1" ]] && kill -0 "$(cat "$1" 2>/dev/null)" 2>/dev/null; }
find_wifi(){ [[ -d /sys/class/net/wlan0 ]] && { echo wlan0; return; }; for p in /sys/class/net/wlan*; do [[ -e "$p" ]] && { basename "$p"; return; }; done; }
find_eth(){ [[ -d /sys/class/net/eth0 ]] && { echo eth0; return; }; for p in /sys/class/net/en*; do [[ -e "$p" ]] && { basename "$p"; return; }; done; }
has_addr(){ ip -4 -o addr show dev "$1" 2>/dev/null | grep -q " $2/24 "; }
stop_pid(){ local p="$1"; if proc_alive "$p"; then kill "$(cat "$p")" 2>/dev/null || true; sleep .2; fi; rm -f "$p"; }
stop_setup(){
  stop_pid "$RUN/hostapd.pid"; stop_pid "$RUN/dnsmasq-wifi.pid"; stop_pid "$RUN/dnsmasq-ethernet.pid"
  local w e; w="$(find_wifi)"; e="$(find_eth)"
  [[ -n "$w" ]] && { ip addr flush dev "$w" 2>/dev/null || true; nmcli device set "$w" managed yes 2>/dev/null || true; }
  [[ -n "$e" ]] && { ip addr flush dev "$e" 2>/dev/null || true; nmcli device set "$e" managed yes 2>/dev/null || true; }
  nmcli connection reload 2>/dev/null || true
}
trap stop_setup EXIT
while true; do
  if [[ -f "$STATE/provisioned" ]]; then log 'provisioned: returning interfaces to NetworkManager'; stop_setup; exit 0; fi
  WIFI="$(find_wifi)"; ETH="$(find_eth)"
  if [[ -n "$ETH" ]]; then
    nmcli device disconnect "$ETH" >/dev/null 2>&1 || true
    nmcli device set "$ETH" managed no >/dev/null 2>&1 || true
    ip link set "$ETH" up >/dev/null 2>&1 || true
    has_addr "$ETH" 10.43.0.1 || { ip addr flush dev "$ETH" 2>/dev/null || true; ip addr add 10.43.0.1/24 dev "$ETH" 2>/dev/null || true; }
    if ! proc_alive "$RUN/dnsmasq-ethernet.pid"; then
      rm -f "$RUN/dnsmasq-ethernet.pid"
      /usr/sbin/dnsmasq --conf-file=/etc/2pny/dnsmasq-ethernet.conf --pid-file="$RUN/dnsmasq-ethernet.pid" --dhcp-leasefile="$STATE/dnsmasq-ethernet.leases" >/dev/null 2>&1 || log 'ethernet dnsmasq start failed'
    fi
  fi
  if [[ -n "$WIFI" && ! -f "$STATE/ap-disabled" ]]; then
    rfkill unblock wifi >/dev/null 2>&1 || true
    nmcli radio wifi on >/dev/null 2>&1 || true
    nmcli device disconnect "$WIFI" >/dev/null 2>&1 || true
    nmcli device set "$WIFI" managed no >/dev/null 2>&1 || true
    ip link set "$WIFI" down >/dev/null 2>&1 || true
    ip addr flush dev "$WIFI" 2>/dev/null || true
    ip link set "$WIFI" up >/dev/null 2>&1 || true
    has_addr "$WIFI" 10.42.0.1 || ip addr add 10.42.0.1/24 dev "$WIFI" 2>/dev/null || true
    if ! proc_alive "$RUN/hostapd.pid"; then
      rm -f "$RUN/hostapd.pid"
      /usr/sbin/hostapd -B -P "$RUN/hostapd.pid" /etc/2pny/hostapd-setup.conf >/dev/null 2>&1 || log 'hostapd start failed'
    fi
    if ! proc_alive "$RUN/dnsmasq-wifi.pid"; then
      rm -f "$RUN/dnsmasq-wifi.pid"
      /usr/sbin/dnsmasq --conf-file=/etc/2pny/dnsmasq-wifi.conf --pid-file="$RUN/dnsmasq-wifi.pid" --dhcp-leasefile="$STATE/dnsmasq-wifi.leases" >/dev/null 2>&1 || log 'wifi dnsmasq start failed'
    fi
  else
    stop_pid "$RUN/hostapd.pid"; stop_pid "$RUN/dnsmasq-wifi.pid"
  fi
  sleep 3
done
''')
ctl.chmod(0o755)

apctl=root/'rootfs-overlay/usr/local/sbin/2pny-ap-control'
apctl.write_text(r'''#!/bin/bash
set -euo pipefail
STATE=/var/lib/2pny
mkdir -p "$STATE"
case "${1:-status}" in
  on) rm -f "$STATE/ap-disabled"; systemctl restart 2pny-network-core.service >/dev/null 2>&1 || true; echo active ;;
  off) touch "$STATE/ap-disabled"; systemctl restart 2pny-network-core.service >/dev/null 2>&1 || true; echo inactive ;;
  status) [[ -f "$STATE/ap-disabled" ]] && echo inactive || echo active ;;
  *) echo 'uso: 2pny-ap-control status|on|off' >&2; exit 2 ;;
esac
''')
apctl.chmod(0o755)

svc=root/'rootfs-overlay/etc/systemd/system/2pny-network-core.service'
svc.write_text('''[Unit]\nDescription=2PNY deterministic first-access network core\nAfter=NetworkManager.service systemd-udev-settle.service\nWants=NetworkManager.service\nConditionPathExists=!/var/lib/2pny/provisioned\n\n[Service]\nType=simple\nExecStart=/usr/local/sbin/2pny-network-core\nRestart=always\nRestartSec=2\nNoNewPrivileges=yes\nPrivateTmp=yes\nProtectHome=yes\nProtectSystem=strict\nReadWritePaths=/var/lib/2pny /run/2pny /run/hostapd\nCapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW CAP_KILL CAP_SETUID CAP_SETGID\nAmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW CAP_KILL\nMemoryMax=48M\nTasksMax=64\n\n[Install]\nWantedBy=multi-user.target\n''')

w=root/'rootfs-overlay/etc/systemd/system/multi-user.target.wants'
w.mkdir(parents=True,exist_ok=True)
old=w/'2pny-setup-watch.service'
if old.exists() or old.is_symlink(): old.unlink()
link=w/'2pny-network-core.service'
try: link.unlink()
except FileNotFoundError: pass
link.symlink_to('/etc/systemd/system/2pny-network-core.service')

fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"
hostnamectl set-hostname 2pny 2>/dev/null || true
raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
rfkill unblock wifi 2>/dev/null || true
systemctl start 2pnyd.service 2>/dev/null || true
systemctl start avahi-daemon.service 2>/dev/null || true
systemctl start 2pny-network-core.service 2>/dev/null || true
for _ in {1..120}; do
  W=0; E=0; P=0
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.42\.0\.1/24 ' && W=1
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.43\.0\.1/24 ' && E=1
  ss -ltn 2>/dev/null | grep -q ':80 ' && P=1
  if (( P && (W || E) )); then
    { echo '2PNY OS 0.1.8-alpha'; echo 'stage=ready'; echo "wifi_ap=$W"; echo "ethernet_setup=$E"; echo "panel=$P"; echo "time=$(date -Is)"; } >"$STATUS" 2>/dev/null || true
    exit 0
  fi
  sleep .5
done
{ echo '2PNY OS 0.1.8-alpha'; echo 'stage=network-not-ready'; ip -4 -br a; systemctl --no-pager --full status 2pny-network-core.service 2>/dev/null || true; } >"$STATUS" 2>/dev/null || true
exit 1
''')
fb.chmod(0o755)

dispatch=root/'rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity'
dispatch.write_text('#!/bin/sh\nexit 0\n')
dispatch.chmod(0o755)

v=root/'builder/validate-source.sh'
vs=v.read_text()
filtered=[]
for line in vs.splitlines(True):
    if any(tok in line for tok in ['2PNY-Ethernet-Setup','2pny-setup.nmconnection','2pny-ethernet-setup.nmconnection','2pny-setup-watch','hotfix3 network state machine','simultaneous Ethernet + Wi-Fi setup','Bookworm deterministic networking','method=shared','key-mgmt=none','auth-alg=open','restart 2pny-firstboot','systemctl mask','powersave=2']):
        continue
    filtered.append(line)
vs=''.join(filtered)
if '# 2PNY_NETWORK_CORE_0_1_8' not in vs:
    vs += r'''
# 2PNY_NETWORK_CORE_0_1_8
echo "[2PNY] Validate deterministic 0.1.8 network core"
grep -q '0.1.8-alpha' src/2pnyd/main.go
grep -q 'raspios_oldstable_lite_arm64' builder/build-image.sh
grep -q 'hostapd dnsmasq-base iw rfkill avahi-daemon' builder/build-image.sh
test -x rootfs-overlay/usr/local/sbin/2pny-network-core
test -x rootfs-overlay/usr/local/sbin/2pny-ap-control
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-network-core.service
! test -e rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-setup-watch.service
grep -q '^ssid=2PNY-SETUP$' rootfs-overlay/etc/2pny/hostapd-setup.conf
grep -q '^wpa=0$' rootfs-overlay/etc/2pny/hostapd-setup.conf
grep -q 'dhcp-range=10.42.0.20,10.42.0.150' rootfs-overlay/etc/2pny/dnsmasq-wifi.conf
grep -q 'dhcp-range=10.43.0.20,10.43.0.150' rootfs-overlay/etc/2pny/dnsmasq-ethernet.conf
grep -q 'ip addr add 10.42.0.1/24' rootfs-overlay/usr/local/sbin/2pny-network-core
grep -q 'ip addr add 10.43.0.1/24' rootfs-overlay/usr/local/sbin/2pny-network-core
! grep -q 'ipv4.method shared' rootfs-overlay/usr/local/sbin/2pny-network-core
bash -n rootfs-overlay/usr/local/sbin/2pny-network-core
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
grep -q '^DumpTAData=1$' rootfs-overlay/usr/local/sbin/2pny-rf-apply
'''
v.write_text(vs)
PY

echo '2PNY 0.1.8 deterministic network core applied'
