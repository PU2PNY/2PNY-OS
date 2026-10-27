#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?image root required}"
[[ "$ROOT" == /* && -d "$ROOT" ]] || exit 2
[[ "$(cat "$ROOT/etc/2pny/version")" == "5.01.001" ]] || exit 2
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/usr/local/sbin/2pny-hardware-probe"
test -s "$DEST"
cp -a "$DEST" "$DEST.pre-v5.01.2"
install -m 0755 "$REPO/src/2pny-hardware-probe-0.3.26.py" "$DEST"
python3 - "$DEST" <<'PY'
from pathlib import Path
import sys
compile(Path(sys.argv[1]).read_bytes(), sys.argv[1], 'exec')
PY
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
exe=root/'usr/local/bin/2pnyd'
raw=exe.read_bytes()
assert b'5.01.001' in raw
exe.write_bytes(raw.replace(b'5.01.001',b'5.01.002'))
(root/'etc/2pny/version').write_text('5.01.002\n')
PY
echo V5012_MMDVM_PROBE_ONLY_OK
