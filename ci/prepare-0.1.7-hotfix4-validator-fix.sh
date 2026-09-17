#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/validate-source.sh')
lines=p.read_text().replace('0.1.7-hotfix3','0.1.7-hotfix4').splitlines()
out=[]
for line in lines:
    if '2pny-ethernet-setup.nmconnection' in line and '10.42.0.1/24' in line:
        line=line.replace('10.42.0.1/24','10.43.0.1/24')
    out.append(line)
p.write_text('\n'.join(out)+'\n')
PY
echo '2PNY hotfix4 inherited validators aligned robustly'
