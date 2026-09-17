#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('rootfs-overlay/etc/default')
p.mkdir(parents=True, exist_ok=True)
(Path('rootfs-overlay/etc/default/hostapd')).write_text('DAEMON_CONF="/etc/hostapd/hostapd-2pny.conf"\n')
PY
