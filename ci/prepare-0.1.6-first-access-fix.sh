#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re
root = Path('.')

# Keep browser on the host/IP that is already reachable. Never require mDNS
# for the transition from setup to the local wizard.
p = root/'src/2pnyd/main.go'
s = p.read_text()
for old in [
    'http://2pny.local/wizard',
    'http://2pny.local/',
]:
    s = s.replace(old, '/wizard')
s = s.replace('"next":"http://2pny.local"', '"next":"/wizard"')
s = s.replace('"next": "http://2pny.local"', '"next": "/wizard"')
# Browser transitions must use the server-selected relative next route.
s = s.replace("window.location.href='http://2pny.local/wizard'", "window.location.href='/wizard'")
s = s.replace("window.location.href='http://2pny.local/'", "window.location.href='/wizard'")
s = s.replace("window.location.href='http://2pny.local'", "window.location.href='/wizard'")
p.write_text(s)

# Make first AP startup deterministic and fast. The pre-created NetworkManager
# profile is the primary path; dynamic hotspot creation is only the fallback.
p = root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
s = p.read_text()
s = re.sub(r'for _ in \{1\.\.60\}; do nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break; sleep 1; done',
           'for _ in {1..15}; do nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break; sleep 1; done', s)
s = re.sub(r'for attempt in \{1\.\.6\}; do', 'for attempt in {1..3}; do', s)
s = s.replace('nmcli --wait 15 connection up 2PNY-SETUP', 'nmcli --wait 6 connection up 2PNY-SETUP')
s = s.replace('nmcli --wait 15 device wifi hotspot', 'nmcli --wait 8 device wifi hotspot')
s = s.replace('sleep 5\n  done', 'sleep 2\n  done')
p.write_text(s)

# Validation catches any future absolute first-access redirect regression.
v = root/'builder/validate-source.sh'
vs = v.read_text()
marker = '# 2PNY_FIRST_ACCESS_0_1_6_CHECK'
if marker not in vs:
    vs += '''\n# 2PNY_FIRST_ACCESS_0_1_6_CHECK\ngrep -q "'/wizard'" src/2pnyd/main.go\n! grep -q "window.location.href='http://2pny.local" src/2pnyd/main.go\ngrep -q 'for _ in {1..15}' rootfs-overlay/usr/local/sbin/2pny-firstboot\n'''
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod +x rootfs-overlay/usr/local/sbin/2pny-firstboot builder/validate-source.sh

echo '2PNY 0.1.6 first-access redirect and Wi-Fi startup fix applied'
