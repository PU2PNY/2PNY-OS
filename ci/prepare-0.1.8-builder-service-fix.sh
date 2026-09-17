#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/build-image.sh')
s=p.read_text()
lines=[]
changed=False
for line in s.splitlines(True):
    if 'systemctl' in line and 'enable' in line and '2pny-firstboot.service' in line:
        line=line.replace('2pny-firstboot.service','2pny-network-core.service')
        changed=True
    if 'systemctl' in line and 'enable' in line and '2pny-setup-watch.service' in line:
        line=line.replace('2pny-setup-watch.service','2pny-network-core.service')
        changed=True
    lines.append(line)
s=''.join(lines)
if not changed:
    raise SystemExit('legacy first-access enable command not found in builder')
# De-duplicate adjacent service names if a legacy line enabled both old services.
s=s.replace('2pny-network-core.service 2pny-network-core.service','2pny-network-core.service')
# The build must never try to enable services intentionally masked by 0.1.8.
for line in s.splitlines():
    if 'systemctl' in line and 'enable' in line and any(x in line for x in ('2pny-firstboot.service','2pny-setup-watch.service','hostapd.service','dnsmasq.service')):
        raise SystemExit('masked service still enabled by builder: '+line)
if '2pny-network-core.service' not in s:
    raise SystemExit('network core enable missing')
p.write_text(s)
PY
bash -n builder/build-image.sh
echo '2PNY 0.1.8 builder enables network core, not legacy first-access services'
