#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/validate-source.sh')
s=p.read_text()
remove_tokens=(
    '2pny-setup-watch',
    '2PNY-Ethernet-Setup',
    '2pny-ethernet-setup.nmconnection',
    '2pny-setup.nmconnection',
    'Validate Ethernet first-access hotfix',
    'Validate AP persistence',
    'Validate hotfix3 network state machine',
    'Validate simultaneous Ethernet + Wi-Fi setup',
    'Validate Bookworm deterministic networking',
)
lines=[]
for line in s.splitlines(True):
    if any(tok in line for tok in remove_tokens):
        continue
    lines.append(line)
s=''.join(lines)
# Keep the new explicit networking contract authoritative.
if '[2PNY] Validate 0.1.8 explicit AutoAP networking' not in s:
    s += r'''
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
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-networkd.service
grep -q '^DumpTAData=1$' rootfs-overlay/usr/local/sbin/2pny-rf-apply
'''
p.write_text(s)
PY
