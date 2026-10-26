#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?mounted root required}"
[[ "$ROOT" == /* && -d "$ROOT" ]] || exit 2
[[ "$(cat "$ROOT/etc/2pny/version")" == "5.01.000" ]] || exit 2
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/usr/local/libexec/pu2pny/display/adapter.py"
test -s "$DEST"
# Preserve old working display adapter byte for byte; never touch NextionDriver binary or HMI.
cp -a "$DEST" "$DEST.pre-5.01"
install -m 0755 "$REPO/runtime/display/adapter.py" "$DEST"
APPLY="$ROOT/usr/local/sbin/2pny-display-apply"
test -s "$APPLY"
cp -a "$APPLY" "$APPLY.pre-v5.01"
install -m 0755 "$REPO/runtime/display/apply.py" "$APPLY"
install -m 0755 "$REPO/runtime/diagnostics/2pny-power-status.py" "$ROOT/usr/local/sbin/2pny-power-status"
python3 - "$DEST" "$APPLY" "$ROOT/usr/local/sbin/2pny-power-status" <<'PY'
from pathlib import Path
import sys
for filename in sys.argv[1:]:
    compile(Path(filename).read_bytes(), filename, 'exec')
PY
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
binary=root/'usr/local/bin/2pnyd'
raw=binary.read_bytes()
assert b'5.01.000' in raw
binary.write_bytes(raw.replace(b'5.01.000', b'5.01.001'))
(root/'etc/2pny/version').write_text('5.01.001\n')
PY
echo PU2PNY_V5011_DISPLAY_INFO_SAFE_OVERLAY_OK
