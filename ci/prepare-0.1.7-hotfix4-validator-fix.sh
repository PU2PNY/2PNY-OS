#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/validate-source.sh')
s=p.read_text().replace('0.1.7-hotfix3','0.1.7-hotfix4')
s=s.replace("grep -q address1=10.42.0.1/24 rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection",
            "grep -q address1=10.43.0.1/24 rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection")
p.write_text(s)
PY
echo '2PNY hotfix4 inherited validators aligned'
