#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('src/2pnyd/main.go')
s=p.read_text()
lines=s.splitlines()
seen=False
out=[]
for line in lines:
    if 'http.HandleFunc("/api/hardware"' in line:
        if seen:
            continue
        seen=True
    out.append(line)
s='\n'.join(out)+'\n'
count=s.count('http.HandleFunc("/api/hardware"')
if count != 1:
    raise SystemExit(f'expected one /api/hardware route, found {count}')
p.write_text(s)
PY
gofmt -w src/2pnyd/main.go
test "$(grep -Fc 'http.HandleFunc("/api/hardware"' src/2pnyd/main.go)" -eq 1
echo '2PNY hardware API route deduplicated'
