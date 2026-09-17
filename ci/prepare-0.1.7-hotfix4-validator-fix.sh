#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/validate-source.sh')
s=p.read_text().replace('0.1.7-hotfix3','0.1.7-hotfix4')
p.write_text(s)
PY
echo '2PNY hotfix4 inherited validator version aligned'
