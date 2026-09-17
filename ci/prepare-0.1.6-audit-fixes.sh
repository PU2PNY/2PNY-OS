#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

root = Path('.')

# MMDVMHost on Debian 13/Trixie needs the nlohmann JSON headers in addition
# to libmosquitto-dev. Keep all build-only packages out of the final image.
p = root/'builder/build-image.sh'
s = p.read_text()
s = s.replace(
    'apt-get install -y --no-install-recommends g++ make git libmosquitto-dev',
    'apt-get install -y --no-install-recommends g++ make git libmosquitto-dev nlohmann-json3-dev'
)
s = s.replace(
    'apt-get purge -y g++ make git libmosquitto-dev',
    'apt-get purge -y g++ make git libmosquitto-dev nlohmann-json3-dev'
)
# Never rely on an earlier apt index: the base build cleans /var/lib/apt/lists.
needle='echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."\n'
if needle in s and needle + 'chroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get update\n' not in s:
    s=s.replace(needle, needle + 'chroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get update\n', 1)
p.write_text(s)

# Source-level invariants from the first-access audit.
p = root/'builder/validate-source.sh'
vs = p.read_text()
checks = r'''
# 2PNY_0_1_6_DEEP_AUDIT_CHECKS
# Setup must be reachable by numeric address and must not depend on mDNS.
grep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection
grep -q 'autoconnect=false' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q 'cloud-init.disabled' <(find rootfs-overlay/etc/cloud -maxdepth 1 -type f -printf '%f\n')
# Absolute redirects to 2pny.local caused the white-page failure on 0.1.5.
! grep -q 'http://2pny.local' src/2pnyd/main.go
# Core web service must not wait for network-online/DHCP.
! grep -q 'network-online.target' rootfs-overlay/etc/systemd/system/2pnyd.service
grep -q 'Before=2pny-firstboot.service' rootfs-overlay/etc/systemd/system/2pnyd.service
grep -q 'MemoryMax=64M' rootfs-overlay/etc/systemd/system/2pnyd.service
# Runtime logging stays in RAM to protect the SD card.
grep -q 'Storage=volatile' rootfs-overlay/etc/systemd/journald.conf.d/2pny.conf
# The transition page must remain stable after the AP disappears.
grep -q 'Reconecte este dispositivo à sua rede normal' src/2pnyd/main.go
'''
if '# 2PNY_0_1_6_DEEP_AUDIT_CHECKS' not in vs:
    vs += checks
p.write_text(vs)
PY

bash -n builder/build-image.sh
bash -n builder/validate-source.sh

echo '2PNY 0.1.6 deep-audit fixes applied'
