#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 - "$SELF_DIR/prepare-0.1.3-live-status.sh" "$TMP" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
src=src.replace("s=pat.sub(new_handler+'\\n\\nfunc fileExists',s,count=1)", "s=pat.sub(lambda _m: new_handler+'\\n\\nfunc fileExists',s,count=1)")
Path(sys.argv[2]).write_text(src)
PY
chmod +x "$TMP"
bash "$TMP" "$ROOT"
