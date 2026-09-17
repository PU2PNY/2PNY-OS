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
    s=re.sub(r'0\.1\.7-hotfix5|0\.1\.7-hotfix4|0\.1\.7-hotfix3|0\.1\.7-hotfix2|0\.1\.7-hotfix1|0\.1\.7-alpha','0.1.8-alpha',s)
    s=s.replace('Alpha 0.1.7 hotfix5','Alpha 0.1.8').replace('Alpha 0.1.7','Alpha 0.1.8')
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.8-alpha\n')

# Ensure deterministic network packages are present in the final image.
b=root/'builder/build-image.sh'
s=b.read_text()
# Extend any package-install line that already includes network-manager/avahi with hostapd/dnsmasq.
if 'hostapd' not in s or 'dnsmasq' not in s:
    s=s.replace('network-manager avahi-daemon', 'network-manager avahi-daemon hostapd dnsmasq rfkill iw', 1)
    s=s.replace('network-manager dnsmasq-base avahi-daemon', 'network-manager dnsmasq-base dnsmasq hostapd avahi-daemon rfkill iw', 1)
# Harden keyfile permissions after overlay copy, regardless of how the builder copies files.
perm='''\n# 2PNY 0.1.8: NetworkManager keyfiles must be root-only or they are ignored.\nfind "$MNT_ROOT/etc/NetworkManager/system-connections" -type f -name '*.nmconnection' -exec chmod 600 {} + 2>/dev/null || true\n'''
if '2PNY 0.1.8: NetworkManager keyfiles must be root-only' not in s:
    marker='sync\n'
    idx=s.rfind(marker)
    s=s[:idx+len(marker)] + perm + s[idx+len(marker):] if idx!=-1 else s+perm
b.write_text(s)

# NetworkManager remains responsible for the user's normal connections only.
conf=root/'rootfs-overlay/etc/NetworkManager/conf.d/20-2pny-appliance.conf'
conf.parent.mkdir(parents=True,exist_ok=True)
conf.write_text('''[main]\nno-auto-default=*\n\n[device]\nwifi.scan-rand-mac-address=no\n''')

# hostapd: open first-access AP, 2.4 GHz for maximum compatibility.
h=root/'rootfs-overlay/etc/hostapd/hostapd-2pny.conf'
h.parent.mkdir(parents=True,exist_ok=True)
h.write_text('''interface=wlan0\ndriver=nl80211\nssid=2PNY-SETUP\nhw_mode=g\nchannel=6\nwmm_enabled=1\nauth_algs=1\nignore_broadcast_ssid=0\ncountry_code=BR\nieee80211d=1\n''')

# dnsmasq: explicit DHCP on both setup transports. bind-dynamic tolerates interfaces appearing later.
d=root/'rootfs-overlay/etc/dnsmasq.d/2pny-setup.conf'
d.parent.mkdir(parents=True,exist_ok=True)
d.write_text('''bind-dynamic\nexcept-interface=lo\ninterface=wlan0\ninterface=eth0\nno-dhcp-interface=lo\ndhcp-authoritative\ndhcp-range=interface:wlan0,10.42.0.20,10.42.0.80,255.255.255.0,12h\ndhcp-option=interface:wlan0,3,10.42.0.1\ndhcp-option=interface:wlan0,6,10.42.0.1\ndhcp-range=interface:eth0,10.43.0.20,10.43.0.80,255.255.255.0,12h\ndhcp-option=interface:eth0,3,10.43.0.1\ndhcp-option=interface:eth0,6,10.43.0.1\naddress=/2pny.local/10.42.0.1\n''')

# Dedicated first-access controller, inspired by Pi-Star's explicit hostapd+dnsmasq AutoAP,
# but keeping Ethernet and AP alive simultaneously. NetworkManager is told not to manage
# setup interfaces until provisioning finishes.
net=root/'rootfs-overlay/usr/local/sbin/2pny-networkd'
net.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
mkdir -p "$STATE"
log(){ logger -t 2pny-networkd -- "$*" 2>/dev/null || true; }
first_wifi(){ for p in /sys/class/net/wlan*; do [[ -e "$p" ]] && { basename "$p"; return; }; done; }
first_eth(){ for p in /sys/class/net/eth* /sys/class/net/en*; do [[ -e "$p" ]] && { basename "$p"; return; }; done; }
has4(){ ip -4 -o addr show dev "$1" 2>/dev/null | grep -q " $2/24 "; }
setup_addr(){ local i="$1" a="$2"; [[ -n "$i" ]] || return 1; ip link set "$i" up >/dev/null 2>&1 || true; has4 "$i" "$a" || ip addr replace "$a/24" dev "$i"; }

# Wait for kernel devices/firmware.
for _ in {1..60}; do
  WIFI="$(first_wifi 2>/dev/null || true)"; ETH="$(first_eth 2>/dev/null || true)"
  [[ -n "$WIFI" || -n "$ETH" ]] && break
  sleep .5
done
WIFI="$(first_wifi 2>/dev/null || true)"; ETH="$(first_eth 2>/dev/null || true)"

# If provisioned, leave normal station networking to NetworkManager, but keep direct Ethernet rescue.
if [[ -f "$STATE/provisioned" ]]; then
  if [[ -n "$ETH" ]]; then
    nmcli device set "$ETH" managed no >/dev/null 2>&1 || true
    setup_addr "$ETH" 10.43.0.1 || true
    systemctl restart dnsmasq.service >/dev/null 2>&1 || true
  fi
  exit 0
fi

rfkill unblock wifi >/dev/null 2>&1 || true
[[ -n "$WIFI" ]] && nmcli device set "$WIFI" managed no >/dev/null 2>&1 || true
[[ -n "$ETH" ]] && nmcli device set "$ETH" managed no >/dev/null 2>&1 || true

if [[ -n "$ETH" ]]; then setup_addr "$ETH" 10.43.0.1 && log "Ethernet setup ready: $ETH 10.43.0.1"; fi
if [[ -n "$WIFI" && ! -f "$STATE/ap-disabled" ]]; then
  setup_addr "$WIFI" 10.42.0.1 || true
  # hostapd config normally says wlan0; support nonstandard interface names too.
  sed -i "s/^interface=.*/interface=$WIFI/" /etc/hostapd/hostapd-2pny.conf
  systemctl restart hostapd.service >/dev/null 2>&1 || log 'hostapd failed'
fi
systemctl restart dnsmasq.service >/dev/null 2>&1 || log 'dnsmasq failed'

# Self-heal while first setup is incomplete.
while [[ ! -f "$STATE/provisioned" ]]; do
  WIFI="$(first_wifi 2>/dev/null || true)"; ETH="$(first_eth 2>/dev/null || true)"
  [[ -n "$ETH" ]] && setup_addr "$ETH" 10.43.0.1 || true
  if [[ -n "$WIFI" && ! -f "$STATE/ap-disabled" ]]; then
    setup_addr "$WIFI" 10.42.0.1 || true
    pgrep -x hostapd >/dev/null 2>&1 || systemctl restart hostapd.service >/dev/null 2>&1 || true
  else
    systemctl stop hostapd.service >/dev/null 2>&1 || true
  fi
  pgrep -x dnsmasq >/dev/null 2>&1 || systemctl restart dnsmasq.service >/dev/null 2>&1 || true
  sleep 3
done

# Provisioned: return Wi-Fi to NetworkManager for station mode; Ethernet rescue remains static.
systemctl stop hostapd.service >/dev/null 2>&1 || true
if [[ -n "$WIFI" ]]; then
  ip addr flush dev "$WIFI" >/dev/null 2>&1 || true
  nmcli device set "$WIFI" managed yes >/dev/null 2>&1 || true
  nmcli radio wifi on >/dev/null 2>&1 || true
fi
log 'provisioned; station Wi-Fi returned to NetworkManager'
exit 0
''')

svc=root/'rootfs-overlay/etc/systemd/system/2pny-networkd.service'
svc.write_text('''[Unit]\nDescription=2PNY deterministic first-access network\nAfter=NetworkManager.service systemd-udev-settle.service\nWants=NetworkManager.service\n\n[Service]\nType=simple\nExecStart=/usr/local/sbin/2pny-networkd\nRestart=on-failure\nRestartSec=2\nNoNewPrivileges=yes\nPrivateTmp=yes\nProtectHome=yes\nMemoryMax=32M\nTasksMax=32\n\n[Install]\nWantedBy=multi-user.target\n''')

# hostapd service override uses our config and is controlled by networkd, not auto-started independently.
ov=root/'rootfs-overlay/etc/systemd/system/hostapd.service.d/2pny.conf'
ov.parent.mkdir(parents=True,exist_ok=True)
ov.write_text('''[Service]\nExecStart=\nExecStart=/usr/sbin/hostapd -P /run/hostapd.pid /etc/hostapd/hostapd-2pny.conf\n''')

# AP control now only toggles marker and hostapd; Ethernet is never touched.
apctl=root/'rootfs-overlay/usr/local/sbin/2pny-ap-control'
apctl.write_text(r'''#!/bin/bash
set -euo pipefail
STATE=/var/lib/2pny
MARK=$STATE/ap-disabled
mkdir -p "$STATE"
case "${1:-status}" in
 status) if pgrep -x hostapd >/dev/null 2>&1; then echo active; else echo inactive; fi ;;
 on) rm -f "$MARK"; systemctl restart 2pny-networkd.service >/dev/null 2>&1 || true; systemctl restart hostapd.service >/dev/null 2>&1 || true; echo 'AP 2PNY-SETUP ativo' ;;
 off) touch "$MARK"; systemctl stop hostapd.service >/dev/null 2>&1 || true; echo 'AP 2PNY-SETUP desativado' ;;
 *) echo 'uso: 2pny-ap-control status|on|off' >&2; exit 2;;
esac
''')

# Firstboot becomes orchestration/status only.
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"
hostnamectl set-hostname 2pny 2>/dev/null || true
raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
rfkill unblock wifi 2>/dev/null || true
systemctl start NetworkManager.service 2>/dev/null || true
systemctl start avahi-daemon.service 2>/dev/null || true
systemctl start 2pnyd.service 2>/dev/null || true
systemctl restart 2pny-networkd.service 2>/dev/null || true
for _ in {1..120}; do
  W=0; E=0; H=0; D=0
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.42\.0\.1/24 ' && W=1
  ip -4 -o addr show 2>/dev/null | grep -q ' 10\.43\.0\.1/24 ' && E=1
  pgrep -x hostapd >/dev/null 2>&1 && H=1
  pgrep -x dnsmasq >/dev/null 2>&1 && D=1
  if (( (W && H && D) || (E && D) )); then
    { echo '2PNY OS 0.1.8-alpha'; echo "wifi_ap=$W"; echo "ethernet=$E"; echo "hostapd=$H"; echo "dnsmasq=$D"; ip -4 -br addr 2>/dev/null || true; } >"$STATUS" 2>/dev/null || true
    exit 0
  fi
  sleep .5
done
exit 1
''')

# Disable old watcher to prevent races; enable the new networkd.
old=root/'rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-setup-watch.service'
try: old.unlink()
except FileNotFoundError: pass
w=root/'rootfs-overlay/etc/systemd/system/multi-user.target.wants'
w.mkdir(parents=True,exist_ok=True)
ln=w/'2pny-networkd.service'
try: ln.unlink()
except FileNotFoundError: pass
ln.symlink_to('/etc/systemd/system/2pny-networkd.service')

# Do not autostart hostapd until networkd has prepared the interface.
for p in [root/'rootfs-overlay/etc/systemd/system/multi-user.target.wants/hostapd.service',root/'rootfs-overlay/etc/systemd/system/multi-user.target.wants/dnsmasq.service']:
    try: p.unlink()
    except FileNotFoundError: pass

# Keep dnsmasq available; networkd starts it. Ensure default distro hostapd config does not conflict.
(root/'rootfs-overlay/etc/default/hostapd').write_text('DAEMON_CONF="/etc/hostapd/hostapd-2pny.conf"\n')

# Replace inherited network assertions with 0.1.8 contracts.
v=root/'builder/validate-source.sh'
vs=v.read_text()
lines=[]
for line in vs.splitlines(True):
    if any(x in line for x in ['2PNY_HOTFIX3','2PNY_HOTFIX4','2PNY_HOTFIX5','Validate hotfix3','Validate simultaneous Ethernet','Validate Bookworm deterministic']):
        continue
    # remove inherited exact checks on old NetworkManager setup profiles / watcher
    if ('2pny-setup-watch' in line or '2pny-setup.nmconnection' in line or '2pny-ethernet-setup.nmconnection' in line) and ('grep ' in line):
        continue
    lines.append(line)
vs=''.join(lines)
vs=vs.replace('0.1.7-hotfix5','0.1.8-alpha').replace('0.1.7-hotfix4','0.1.8-alpha')
vs += r'''
echo "[2PNY] Validate 0.1.8 explicit AutoAP networking"
bash -n rootfs-overlay/usr/local/sbin/2pny-networkd
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
test -s rootfs-overlay/etc/hostapd/hostapd-2pny.conf
test -s rootfs-overlay/etc/dnsmasq.d/2pny-setup.conf
grep -q '^ssid=2PNY-SETUP$' rootfs-overlay/etc/hostapd/hostapd-2pny.conf
! grep -Eq 'wpa=|wpa_passphrase|wpa_key_mgmt' rootfs-overlay/etc/hostapd/hostapd-2pny.conf
grep -q '10.42.0.20,10.42.0.80' rootfs-overlay/etc/dnsmasq.d/2pny-setup.conf
grep -q '10.43.0.20,10.43.0.80' rootfs-overlay/etc/dnsmasq.d/2pny-setup.conf
grep -q '10.42.0.1' rootfs-overlay/usr/local/sbin/2pny-networkd
grep -q '10.43.0.1' rootfs-overlay/usr/local/sbin/2pny-networkd
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-networkd.service
grep -q '^DumpTAData=1$' rootfs-overlay/usr/local/sbin/2pny-rf-apply
grep -q '0.1.8-alpha' src/2pnyd/main.go
'''
v.write_text(vs)
PY

chmod 0755 rootfs-overlay/usr/local/sbin/2pny-networkd rootfs-overlay/usr/local/sbin/2pny-ap-control rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-networkd
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot

echo '2PNY 0.1.8 explicit AutoAP network architecture applied'
