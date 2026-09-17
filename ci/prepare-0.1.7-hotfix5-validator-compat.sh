#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/validate-source.sh')
s=p.read_text().replace('0.1.7-hotfix4','0.1.7-hotfix5')

# Hotfix5 fully replaces the network implementation introduced by hotfix3/4.
# Remove only inherited assertions that test those superseded implementation
# details. Hotfix5 appends its own behavioral contract afterwards.
obsolete=(
    'key-mgmt=none',
    'auth-alg=open',
    'address=/#/10.42.0.1',
    'connection up "$ETHSET"',
    'Ethernet direct access is independent',
    'Wi-Fi AP is also independent',
    'nmcli connection down 2PNY-Ethernet-Setup',
)
lines=[]
for line in s.splitlines(True):
    if any(tok in line for tok in obsolete):
        continue
    lines.append(line)
p.write_text(''.join(lines))
PY
echo '2PNY hotfix5 inherited network validators removed; Bookworm contract is authoritative'
