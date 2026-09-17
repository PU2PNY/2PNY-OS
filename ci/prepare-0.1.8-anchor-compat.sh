#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('src/2pnyd/main.go')
s=p.read_text()
old='func connectConfiguredWiFi(ssid, password string) error {'
new='func connectConfiguredWiFi(ssid,password string) error {'
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('connectConfiguredWiFi signature not found')
p.write_text(s)
PY
echo '2PNY 0.1.8 handoff anchor normalized'
