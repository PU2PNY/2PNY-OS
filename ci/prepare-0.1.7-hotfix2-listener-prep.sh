#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import re
p=Path('src/2pnyd/main.go')
s=p.read_text()
patterns=[
    r'(listenAddr\s*:=\s*)"[^"]*"',
    r'(listenAddr\s*=\s*)"[^"]*"',
]
changed=0
for pat in patterns:
    s,n=re.subn(pat, r'\1"0.0.0.0:80"', s, count=1)
    if n:
        changed=1
        break
if not changed:
    raise SystemExit('listenAddr assignment not found')
if 'http.ListenAndServe(listenAddr, nil)' not in s and 'http.ListenAndServe(listenAddr,nil)' not in s:
    raise SystemExit('listenAddr is not used by ListenAndServe')
p.write_text(s)
PY
gofmt -w src/2pnyd/main.go
grep -q 'listenAddr.*0.0.0.0:80' src/2pnyd/main.go
echo '2PNY listener forced to 0.0.0.0:80'
