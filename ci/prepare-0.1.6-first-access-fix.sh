#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
root=Path('.')

# Cloud-init cannot rewrite appliance networking.
cloud=root/'rootfs-overlay/etc/cloud'; cloud.mkdir(parents=True,exist_ok=True)
(cloud/'cloud-init.disabled').write_text('2PNY owns provisioning and networking.\n')

# Before provisioning, 10.42.0.1 is the only official setup address.
conn=root/'rootfs-overlay/etc/NetworkManager/system-connections'; conn.mkdir(parents=True,exist_ok=True)
(conn/'2pny-setup.nmconnection').write_text('''[connection]\nid=2PNY-SETUP\nuuid=5d9da2d9-3b48-4936-8201-2a4f00000002\ntype=wifi\nautoconnect=false\nmdns=2\n\n[wifi]\nmode=ap\nband=bg\nchannel=6\nssid=2PNY-SETUP\n\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=2pnysetup\n\n[ipv4]\nmethod=shared\naddress1=10.42.0.1/24\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')
(conn/'2pny-ethernet-setup.nmconnection').write_text('''[connection]\nid=2PNY-Ethernet-Setup\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000003\ntype=ethernet\nautoconnect=false\nmdns=2\n\n[ethernet]\n\n[ipv4]\nmethod=shared\naddress1=10.42.0.1/24\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')
(conn/'2pny-ethernet.nmconnection').write_text('''[connection]\nid=2PNY-Ethernet\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000001\ntype=ethernet\nautoconnect=false\nmdns=2\n\n[ethernet]\n\n[ipv4]\nmethod=auto\ndhcp-timeout=10\nmay-fail=true\n\n[ipv6]\nmethod=auto\naddr-gen-mode=default\n\n[proxy]\n''')

# RAM journal: low SD writes.
jd=root/'rootfs-overlay/etc/systemd/journald.conf.d'; jd.mkdir(parents=True,exist_ok=True)
(jd/'2pny.conf').write_text('[Journal]\nStorage=volatile\nRuntimeMaxUse=16M\nRuntimeMaxFileSize=4M\n')

# Core panel must start before provisioning and never wait for network-online.
svc=root/'rootfs-overlay/etc/systemd/system'; svc.mkdir(parents=True,exist_ok=True)
(svc/'2pnyd.service').write_text('''[Unit]\nDescription=2PNY Core and local panel\nAfter=local-fs.target NetworkManager.service\nWants=NetworkManager.service\nBefore=2pny-firstboot.service\nStartLimitIntervalSec=0\n\n[Service]\nType=simple\nExecStart=/usr/local/bin/2pnyd\nRestart=always\nRestartSec=1\nNoNewPrivileges=yes\nPrivateTmp=yes\nProtectHome=yes\nProtectSystem=strict\nReadWritePaths=/var/lib/2pny /run\nMemoryMax=64M\nTasksMax=64\n\n[Install]\nWantedBy=multi-user.target\n''')
(svc/'2pny-firstboot.service').write_text('''[Unit]\nDescription=2PNY deterministic first access\nAfter=NetworkManager.service 2pnyd.service\nWants=NetworkManager.service 2pnyd.service\nConditionPathExists=!/var/lib/2pny/provisioned\nStartLimitIntervalSec=0\n\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/2pny-firstboot\nRemainAfterExit=yes\nRestart=on-failure\nRestartSec=2\nTimeoutStartSec=45\n\n[Install]\nWantedBy=multi-user.target\n''')

def symlink(path,target):
    path.parent.mkdir(parents=True,exist_ok=True)
    try: path.unlink()
    except FileNotFoundError: pass
    path.symlink_to(target)
w=svc/'multi-user.target.wants'
symlink(w/'2pnyd.service','/etc/systemd/system/2pnyd.service')
symlink(w/'2pny-firstboot.service','/etc/systemd/system/2pny-firstboot.service')
symlink(w/'NetworkManager.service','/usr/lib/systemd/system/NetworkManager.service')
symlink(w/'avahi-daemon.service','/usr/lib/systemd/system/avahi-daemon.service')
symlink(svc/'NetworkManager-wait-online.service','/dev/null')

# Fast setup state machine. Cable gets 10.42.0.1 if present; otherwise Wi-Fi AP.
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny; LOG=/run/2pny-firstboot.log; STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"; exec >>"$LOG" 2>&1
status_write(){ { echo '2PNY OS 0.1.6-alpha'; echo "stage=$1"; echo "time=$(date -Is)"; echo '[active]'; nmcli -t -f NAME,TYPE,DEVICE connection show --active 2>/dev/null || true; echo '[ipv4]'; ip -4 -br address show 2>/dev/null || true; } >"${STATUS}.tmp" 2>/dev/null || true; mv -f "${STATUS}.tmp" "$STATUS" 2>/dev/null || true; }
hostnamectl set-hostname 2pny 2>/dev/null || true
systemctl start NetworkManager.service 2>/dev/null || true
systemctl start 2pnyd.service 2>/dev/null || true
systemctl start avahi-daemon.service 2>/dev/null || true
status_write starting
if [[ -f "$STATE/provisioned" ]]; then
  nmcli connection down 2PNY-SETUP >/dev/null 2>&1 || true
  nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true
  nmcli connection modify 2PNY-Ethernet connection.autoconnect yes >/dev/null 2>&1 || true
  nmcli --wait 8 connection up 2PNY-Ethernet >/dev/null 2>&1 || true
  status_write provisioned; exit 0
fi
raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
rfkill unblock wifi 2>/dev/null || true; nmcli radio wifi on 2>/dev/null || true
for _ in {1..16}; do nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break; sleep .25; done
ETH_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}')"
WIFI_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
nmcli connection down 2PNY-Ethernet >/dev/null 2>&1 || true
nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true
nmcli connection down 2PNY-SETUP >/dev/null 2>&1 || true
if [[ -n "${ETH_IF:-}" && "$(cat "/sys/class/net/${ETH_IF}/carrier" 2>/dev/null || echo 0)" == 1 ]]; then
  if nmcli --wait 6 connection up 2PNY-Ethernet-Setup ifname "$ETH_IF" >/dev/null 2>&1; then status_write ready-ethernet; echo '2PNY setup: http://10.42.0.1'; exit 0; fi
fi
if [[ -n "${WIFI_IF:-}" ]]; then
  ip link set "$WIFI_IF" up 2>/dev/null || true
  if nmcli --wait 6 connection up 2PNY-SETUP ifname "$WIFI_IF" >/dev/null 2>&1; then status_write ready-wifi; echo '2PNY-SETUP: http://10.42.0.1'; exit 0; fi
  nmcli connection delete 2PNY-SETUP >/dev/null 2>&1 || true
  if nmcli --wait 8 device wifi hotspot ifname "$WIFI_IF" con-name 2PNY-SETUP ssid 2PNY-SETUP band bg channel 6 password 2pnysetup >/dev/null 2>&1; then
    nmcli connection modify 2PNY-SETUP ipv4.method shared ipv4.addresses 10.42.0.1/24 ipv6.method disabled connection.autoconnect no connection.mdns yes >/dev/null 2>&1 || true
    status_write ready-wifi-recovered; echo '2PNY-SETUP recovered: http://10.42.0.1'; exit 0
  fi
fi
status_write error-no-setup; exit 1
''')

# No polling daemon. NetworkManager event restores setup only while unprovisioned.
disp=root/'rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity'
disp.write_text(r'''#!/bin/bash
[[ -f /var/lib/2pny/provisioned ]] && exit 0
case "${2:-unknown}" in down|connectivity-change) systemctl restart 2pny-firstboot.service >/dev/null 2>&1 || true;; esac
exit 0
''')

# No absolute mDNS redirect: keep current host and use relative /wizard.
p=root/'src/2pnyd/main.go'; s=p.read_text()
s=s.replace('127.0.0.1:80',':80').replace('localhost:80',':80')
for old in ['http://2pny.local/wizard','http://2pny.local/','http://2pny.local']:
    s=s.replace(old,'/wizard')
s=s.replace('/wizard/wizard','/wizard')
s=s.replace("let u=['/api/setup-status','/wizardapi/setup-status'];","let u=['/api/setup-status'];")
s=s.replace('Abrindo o painel automaticamente...','Rede configurada. Reconecte à rede normal e abra o IP atribuído ao 2PNY.')
s=s.replace('Abrindo o painel...','Rede configurada. Use o IP atribuído pela sua rede.')
s=s.replace("await waitms(1500);window.location.href='/wizard';return","return")
s=s.replace("setTimeout(()=>window.location.href='/wizard',1200)","")
s=s.replace('href="http://2pny.local/wizard"','href="/wizard"')
p.write_text(s)

# Update inherited validators to the strict 0.1.6 contract.
v=root/'builder/validate-source.sh'; vs=v.read_text()
vs=vs.replace("grep -q '0.1.5-alpha' src/2pnyd/main.go","grep -q '0.1.6-alpha' src/2pnyd/main.go")
vs=vs.replace("grep -q '169.254.2.1/16' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet.nmconnection","grep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection")
if '# 2PNY_FIRST_ACCESS_STRICT_0_1_6' not in vs:
    vs += r'''\n# 2PNY_FIRST_ACCESS_STRICT_0_1_6\necho "[2PNY] Validate strict first access"\ngrep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\ngrep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection\ngrep -q 'autoconnect=false' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet.nmconnection\n! grep -q 'http://2pny.local/wizard' src/2pnyd/main.go\ngrep -q 'href="/wizard"' src/2pnyd/main.go\ngrep -q 'Storage=volatile' rootfs-overlay/etc/systemd/journald.conf.d/2pny.conf\ntest -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pnyd.service\ntest -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-firstboot.service\n'''
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod 0755 rootfs-overlay/usr/local/sbin/2pny-firstboot rootfs-overlay/etc/NetworkManager/dispatcher.d/90-2pny-connectivity
chmod 0600 rootfs-overlay/etc/NetworkManager/system-connections/*.nmconnection

echo '2PNY 0.1.6 deterministic first-access fix applied'
