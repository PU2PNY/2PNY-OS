#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?mounted image root required}"
[[ "$ROOT" == /* && -d "$ROOT" ]] || exit 2
[[ "$(cat "$ROOT/etc/2pny/version")" == "5.00.003" ]] || exit 2
REPO="$(cd "$(dirname "$0")/.." && pwd)"
test -s "$REPO/runtime/diagnostics/2pny-audit-v5.sh"
install -m 0755 "$REPO/runtime/diagnostics/2pny-audit-v5.sh" "$ROOT/usr/local/sbin/2pny-audit"
bash -n "$ROOT/usr/local/sbin/2pny-audit"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
exe=root/'usr/local/bin/2pnyd'
raw=exe.read_bytes()
assert b'5.00.003' in raw, 'prior image identity mismatch'
exe.write_bytes(raw.replace(b'5.00.003',b'5.00.004'))
(root/'etc/2pny/version').write_text('5.00.004\n')
PY
echo 'PU2PNY_500004_READONLY_AUDIT_OVERLAY_OK'
