#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
root=Path('.')
conn=root/'rootfs-overlay/etc/NetworkManager/system-connections'; conn.mkdir(parents=True,exist_ok=True)
(conn/'2pny-setup.nmconnection').write_text('''[connection]\nid=2PNY-SETUP\nuuid=5d9da2d9-3b48-4936-8201-2a4f00000002\ntype=wifi\nautoconnect=false\nautoconnect-priority=100\nmdns=2\n\n[wifi]\nmode=ap\nband=bg\nchannel=6\nssid=2PNY-SETUP\n\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=2pnysetup\n\n[ipv4]\nmethod=shared\naddress1=10.42.0.1/24\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')
(conn/'2pny-setup-ethernet.nmconnection').write_text('''[connection]\nid=2PNY-SETUP-ETH\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000003\ntype=ethernet\nautoconnect=false\nautoconnect-priority=110\nmdns=2\n\n[ethernet]\n\n[ipv4]\nmethod=shared\naddress1=10.42.0.1/24\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')
(conn/'2pny-ethernet.nmconnection').write_text('''[connection]\nid=2PNY-Ethernet\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000001\ntype=ethernet\nautoconnect=false\nautoconnect-priority=50\nmdns=2\n\n[ethernet]\n\n[ipv4]\nmethod=auto\ndhcp-timeout=10\n\n[ipv6]\nmethod=auto\naddr-gen-mode=default\n\n[proxy]\n''')
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny; LOG=/var/log/2pny-firstboot.log; STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"; exec >>"$LOG" 2>&1
stamp(){ printf '%s\n' "$1" >"$STATUS" 2>/dev/null || true; echo "[$(date -Is)] $1"; }
stamp '2PNY: starting first access'
hostnamectl set-hostname 2pny || true
systemctl start NetworkManager.service || true
systemctl start 2pnyd.service || true
systemctl start avahi-daemon.service || true
if [[ -f "$STATE/provisioned" ]]; then nmcli connection modify 2PNY-Ethernet connection.autoconnect yes 2>/dev/null || true; stamp '2PNY: provisioned'; exit 0; fi
raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
rfkill unblock wifi 2>/dev/null || true; nmcli radio wifi on 2>/dev/null || true
for _ in {1..12}; do nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break; sleep .25; done
ETH_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}')"
WIFI_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
ETH_CARRIER=0; if [[ -n "${ETH_IF:-}" && -r "/sys/class/net/$ETH_IF/carrier" ]]; then read -r ETH_CARRIER <"/sys/class/net/$ETH_IF/carrier" || ETH_CARRIER=0; fi
nmcli connection down 2PNY-Ethernet >/dev/null 2>&1 || true; nmcli connection down 2PNY-SETUP-ETH >/dev/null 2>&1 || true; nmcli connection down 2PNY-SETUP >/dev/null 2>&1 || true
if [[ "$ETH_CARRIER" == 1 ]] && nmcli --wait 8 connection up 2PNY-SETUP-ETH ifname "$ETH_IF" >/dev/null 2>&1; then stamp '2PNY: setup ready on Ethernet http://10.42.0.1'; exit 0; fi
if [[ -n "${WIFI_IF:-}" ]]; then
 ip link set "$WIFI_IF" up 2>/dev/null || true
 if nmcli --wait 8 connection up 2PNY-SETUP ifname "$WIFI_IF" >/dev/null 2>&1; then stamp '2PNY: setup ready on Wi-Fi http://10.42.0.1'; exit 0; fi
 nmcli connection delete 2PNY-SETUP >/dev/null 2>&1 || true
 if nmcli --wait 8 device wifi hotspot ifname "$WIFI_IF" con-name 2PNY-SETUP ssid 2PNY-SETUP band bg channel 6 password 2pnysetup >/dev/null 2>&1; then nmcli connection modify 2PNY-SETUP ipv4.method shared ipv4.addresses 10.42.0.1/24 connection.autoconnect no connection.mdns yes >/dev/null 2>&1 || true; stamp '2PNY: setup recovered on Wi-Fi http://10.42.0.1'; exit 0; fi
fi
stamp '2PNY ERROR: setup transport unavailable'; exit 1
''')
disp=root/'rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity'
disp.write_text(r'''#!/bin/bash
IFACE="${1:-unknown}"; ACTION="${2:-unknown}"; STATE=/var/lib/2pny
logger -t 2pny-net "interface=${IFACE} action=${ACTION}"
[[ -f "$STATE/provisioned" ]] && exit 0
case "$ACTION" in down|connectivity-change) systemctl restart 2pny-firstboot.service >/dev/null 2>&1 || true;; esac
exit 0
''')
svc=root/'rootfs-overlay/etc/systemd/system/2pnyd.service'
if svc.exists():
 s=svc.read_text().replace('After=NetworkManager.service network-online.target','After=NetworkManager.service').replace('Wants=NetworkManager.service network-online.target','Wants=NetworkManager.service'); svc.write_text(s)
p=root/'src/2pnyd/main.go'; s=p.read_text()
s=s.replace('http://2pny.local/wizard','/wizard').replace('href="http://2pny.local/wizard"','href="/wizard"')
s=s.replace('Abrindo o painel automaticamente...', 'Configuração salva. Reconecte à rede normal e abra o IP atribuído ao 2PNY.')
s=s.replace('Abrindo o painel...', 'Configuração salva. Use o IP atribuído pela sua rede.')
s=s.replace("await waitms(1500);window.location.href='/wizard';return", "return")
s=s.replace("setTimeout(()=>window.location.href='/wizard',1200)", "")
p.write_text(s)
v=root/'builder/validate-source.sh'; vs=v.read_text().replace("grep -q '0.1.5-alpha' src/2pnyd/main.go", "grep -q '0.1.6-alpha' src/2pnyd/main.go")
if '# 2PNY_FIRST_ACCESS_0_1_6' not in vs:
 vs += r'''\n# 2PNY_FIRST_ACCESS_0_1_6\necho "[2PNY] Validate deterministic first access"\ngrep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup-ethernet.nmconnection\ngrep -q 'autoconnect=false' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet.nmconnection\ngrep -q 'setup ready on Wi-Fi http://10.42.0.1' rootfs-overlay/usr/local/sbin/2pny-firstboot\ngrep -q 'setup ready on Ethernet http://10.42.0.1' rootfs-overlay/usr/local/sbin/2pny-firstboot\n! grep -q 'http://2pny.local/wizard' src/2pnyd/main.go\ngrep -q 'href="/wizard"' src/2pnyd/main.go\n'''
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod 0755 rootfs-overlay/usr/local/sbin/2pny-firstboot rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity
chmod 0600 rootfs-overlay/etc/NetworkManager/system-connections/*.nmconnection

echo '2PNY 0.1.6 first-access hardening applied'
