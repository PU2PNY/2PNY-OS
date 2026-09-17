#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/validate-source.sh')
s=p.read_text().replace('0.1.7-hotfix4','0.1.7-hotfix5')
obsolete=(
    'key-mgmt=none',
    'auth-alg=open',
    'address=/#/10.42.0.1',
)
lines=[]
for line in s.splitlines(True):
    if any(tok in line for tok in obsolete):
        continue
    lines.append(line)
p.write_text(''.join(lines))
PY
echo '2PNY hotfix5 inherited validators aligned with Bookworm/open AP'
