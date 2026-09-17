#!/usr/bin/env bash
set -euo pipefail
# Build trigger after workflow registration; no runtime behavior change.
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('rootfs-overlay/usr/local/sbin/2pny-setup-watch')
s=p.read_text().replace('${2PNY_WATCH_ONCE:-0}', '${PNY2_WATCH_ONCE:-0}')
p.write_text(s)

v=Path('builder/validate-source.sh')
s=v.read_text()
if '# 2PNY_0_1_8_NETWORK_FOLLOWUP' not in s:
    s += '''\n# 2PNY_0_1_8_NETWORK_FOLLOWUP\ngrep -q 'PNY2_WATCH_ONCE' rootfs-overlay/usr/local/sbin/2pny-setup-watch\n! grep -q '2PNY_WATCH_ONCE' rootfs-overlay/usr/local/sbin/2pny-setup-watch\n'''
v.write_text(s)
PY
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
echo '2PNY 0.1.8 network follow-up applied'
