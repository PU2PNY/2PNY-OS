#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
root=Path('.')

# Patch release: deterministic direct-Ethernet first access.
for rel in ['builder/build-image.sh', 'rootfs-overlay/usr/local/sbin/2pny-firstboot', 'src/2pnyd/main.go']:
    p=root/rel
    s=p.read_text()
    s=s.replace('0.1.7-alpha','0.1.7-hotfix1').replace('Alpha 0.1.7','Alpha 0.1.7 hotfix1')
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.7-hotfix1\n')

# A persistent pre-provisioning watcher removes the boot-time carrier race.
# Ethernet has priority; Wi-Fi setup is restored automatically if the cable
# is removed. Only one setup transport owns 10.42.0.1 at a time.
watch=root/'rootfs-overlay/usr/local/sbin/2pny-setup-watch'
watch.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
SLEEP=2
log(){ logger -t 2pny-setup-watch -- "$*" 2>/dev/null || true; }
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
eth_if(){ nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}'; }
wifi_if(){ nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}'; }
carrier(){ local i="$1"; [[ -n "$i" && -r "/sys/class/net/$i/carrier" ]] && [[ "$(cat "/sys/class/net/$i/carrier" 2>/dev/null || echo 0)" == 1 ]]; }

while [[ ! -f "$STATE/provisioned" ]]; do
  ETH="$(eth_if)"; WIFI="$(wifi_if)"
  if carrier "$ETH"; then
    if ! active '2PNY-Ethernet-Setup'; then
      log "ethernet carrier detected on $ETH; selecting direct setup"
      nmcli connection down 2PNY-SETUP >/dev/null 2>&1 || true
      nmcli connection down 2PNY-Ethernet >/dev/null 2>&1 || true
      nmcli --wait 10 connection up 2PNY-Ethernet-Setup ifname "$ETH" >/dev/null 2>&1 || true
    fi
  else
    if active '2PNY-Ethernet-Setup'; then
      nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true
    fi
    if [[ -n "$WIFI" ]] && ! active '2PNY-SETUP'; then
      log "no ethernet carrier; selecting Wi-Fi setup"
      rfkill unblock wifi >/dev/null 2>&1 || true
      nmcli radio wifi on >/dev/null 2>&1 || true
      nmcli --wait 10 connection up 2PNY-SETUP ifname "$WIFI" >/dev/null 2>&1 || true
    fi
  fi
  sleep "$SLEEP"
done
log 'provisioned; setup watcher exiting'
exit 0
''')

svc=root/'rootfs-overlay/etc/systemd/system/2pny-setup-watch.service'
svc.write_text('''[Unit]\nDescription=2PNY first-access transport watcher\nAfter=NetworkManager.service\nWants=NetworkManager.service\nConditionPathExists=!/var/lib/2pny/provisioned\n\n[Service]\nType=simple\nExecStart=/usr/local/sbin/2pny-setup-watch\nRestart=on-failure\nRestartSec=2\nNoNewPrivileges=yes\nPrivateTmp=yes\nProtectHome=yes\nProtectSystem=strict\nReadOnlyPaths=/sys\nMemoryMax=24M\nTasksMax=24\n\n[Install]\nWantedBy=multi-user.target\n''')

w=root/'rootfs-overlay/etc/systemd/system/multi-user.target.wants'
w.mkdir(parents=True,exist_ok=True)
link=w/'2pny-setup-watch.service'
try: link.unlink()
except FileNotFoundError: pass
link.symlink_to('/etc/systemd/system/2pny-setup-watch.service')

# The one-shot still handles the initial fast path; give Ethernet carrier a
# short settling window before falling back to Wi-Fi.
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
s=fb.read_text()
old='''if [[ -n "${ETH_IF:-}" && "$(cat "/sys/class/net/${ETH_IF}/carrier" 2>/dev/null || echo 0)" == 1 ]]; then\n  if nmcli --wait 6 connection up 2PNY-Ethernet-Setup ifname "$ETH_IF" >/dev/null 2>&1; then status_write ready-ethernet; echo '2PNY setup: http://10.42.0.1'; exit 0; fi\nfi'''
new='''if [[ -n "${ETH_IF:-}" ]]; then\n  for _ in {1..20}; do\n    [[ "$(cat "/sys/class/net/${ETH_IF}/carrier" 2>/dev/null || echo 0)" == 1 ]] && break\n    sleep .25\n  done\n  if [[ "$(cat "/sys/class/net/${ETH_IF}/carrier" 2>/dev/null || echo 0)" == 1 ]]; then\n    if nmcli --wait 10 connection up 2PNY-Ethernet-Setup ifname "$ETH_IF" >/dev/null 2>&1; then status_write ready-ethernet; echo '2PNY setup: http://10.42.0.1'; exit 0; fi\n  fi\nfi'''
if old not in s:
    raise SystemExit('firstboot Ethernet anchor not found')
s=s.replace(old,new,1)
fb.write_text(s)

v=root/'builder/validate-source.sh'
vs=v.read_text().replace("grep -q '0.1.7-alpha' src/2pnyd/main.go", "grep -q '0.1.7-hotfix1' src/2pnyd/main.go")
if '# 2PNY_0_1_7_HOTFIX1_ETHERNET' not in vs:
    vs += '''\n# 2PNY_0_1_7_HOTFIX1_ETHERNET\necho "[2PNY] Validate Ethernet first-access hotfix"\nbash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch\nbash -n rootfs-overlay/usr/local/sbin/2pny-firstboot\ntest -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-setup-watch.service\ngrep -q 'MemoryMax=24M' rootfs-overlay/etc/systemd/system/2pny-setup-watch.service\ngrep -q "active '2PNY-Ethernet-Setup'" rootfs-overlay/usr/local/sbin/2pny-setup-watch\ngrep -q "nmcli --wait 10 connection up 2PNY-Ethernet-Setup" rootfs-overlay/usr/local/sbin/2pny-setup-watch\ngrep -q 'for _ in {1..20}' rootfs-overlay/usr/local/sbin/2pny-firstboot\ngrep -q '0.1.7-hotfix1' src/2pnyd/main.go\n'''
v.write_text(vs)
PY

chmod 0755 rootfs-overlay/usr/local/sbin/2pny-setup-watch rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot

echo '2PNY 0.1.7 hotfix1 direct-Ethernet watcher applied'
