#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?mounted root required}"
ARCH="${2:?arm32 or arm64}"
[[ "$ROOT" == /* && -d "$ROOT" && ( "$ARCH" == arm32 || "$ARCH" == arm64 ) ]] || exit 2
[[ "$(cat "$ROOT/etc/2pny/version")" == 5.00.004 ]] || exit 2
REPO="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$REPO/ci/patch-ap-v5.01.py" "$ROOT" "$ARCH"
# Strictly preserve the RF/display/runtime from the proven source image.
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
exe=root/'usr/local/bin/2pnyd'
raw=exe.read_bytes()
old=b'5.00.004'
assert old in raw
exe.write_bytes(raw.replace(old,b'5.01.000'))
(root/'etc/2pny/version').write_text('5.01.000\n')
PY
echo V501_AP_ARCH_SCOPE_OK
