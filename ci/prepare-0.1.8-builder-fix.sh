#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/build-image.sh')
s=p.read_text()
# Remove the earlier unsafe builder hook; the final image validator will verify modes.
lines=s.splitlines(True)
out=[]
skip_comment=False
for line in lines:
    if '2PNY 0.1.8: NetworkManager keyfiles must be root-only' in line:
        skip_comment=True
        continue
    if skip_comment and 'MNT_ROOT/etc/NetworkManager/system-connections' in line:
        skip_comment=False
        continue
    if 'MNT_ROOT/etc/NetworkManager/system-connections' in line:
        continue
    out.append(line)
p.write_text(''.join(out))

# Harden source overlay permissions so rsync/cp preserves them into the image.
conn=Path('rootfs-overlay/etc/NetworkManager/system-connections')
if conn.exists():
    for f in conn.glob('*.nmconnection'):
        f.chmod(0o600)
PY
! grep -q 'MNT_ROOT/etc/NetworkManager/system-connections' builder/build-image.sh
if [ -d rootfs-overlay/etc/NetworkManager/system-connections ]; then
  find rootfs-overlay/etc/NetworkManager/system-connections -type f -name '*.nmconnection' -exec chmod 600 {} +
fi
echo '2PNY 0.1.8 builder keyfile-permission fix applied'
