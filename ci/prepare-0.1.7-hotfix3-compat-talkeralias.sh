#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path

v=Path('builder/validate-source.sh')
s=v.read_text()
obsolete=[
    "grep -q \"active '2PNY-Ethernet-Setup'\" rootfs-overlay/usr/local/sbin/2pny-setup-watch\n",
    "grep -q 'nmcli --wait 10 connection up 2PNY-Ethernet-Setup' rootfs-overlay/usr/local/sbin/2pny-setup-watch\n",
    "grep -q 'for _ in {1..20}' rootfs-overlay/usr/local/sbin/2pny-firstboot\n",
    "! grep -q '\\\\[wifi-security\\\\]' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection\n",
    "grep -q 'mask --now 2pny-setup-watch.service' rootfs-overlay/usr/local/sbin/2pny-ap-control\n",
]
for line in obsolete:
    s=s.replace(line,'')

marker='# 2PNY_HOTFIX3_COMPAT_TALKERALIAS'
if marker not in s:
    s += r'''
# 2PNY_HOTFIX3_COMPAT_TALKERALIAS
echo "[2PNY] Validate hotfix3 network state machine and DMR Talker Alias"
grep -q '^ETHSET=2PNY-Ethernet-Setup$' rootfs-overlay/usr/local/sbin/2pny-setup-watch
grep -q 'connection up "$ETHSET"' rootfs-overlay/usr/local/sbin/2pny-setup-watch
grep -q '^key-mgmt=none$' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q '^auth-alg=open$' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
! grep -q '^psk=' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q '^DumpTAData=1$' rootfs-overlay/usr/local/sbin/2pny-rf-apply
! grep -q 'mask --now 2pny-setup-watch.service' rootfs-overlay/usr/local/sbin/2pny-ap-control
'''
v.write_text(s)

rf=Path('rootfs-overlay/usr/local/sbin/2pny-rf-apply')
r=rf.read_text()
if 'DumpTAData=1' not in r:
    r=r.replace('ColorCode=1\n','ColorCode=1\nDumpTAData=1\n',1)
rf.write_text(r)
PY

bash -n rootfs-overlay/usr/local/sbin/2pny-rf-apply
chmod 0755 rootfs-overlay/usr/local/sbin/2pny-rf-apply

echo '2PNY hotfix3 compatibility checks and DMR Talker Alias applied'
