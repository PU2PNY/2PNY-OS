#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/build-image.sh')
s=p.read_text()
old='''echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev'''
new='''echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get update\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev'''
if old not in s:
    if 'apt-get update\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev' not in s:
        raise SystemExit('MMDVMHost dependency install anchor not found')
else:
    s=s.replace(old,new,1)
p.write_text(s)
PY
bash -n builder/build-image.sh
echo '2PNY 0.1.6 MMDVMHost apt-index build fix applied'
