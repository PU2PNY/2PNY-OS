#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/build-image.sh')
s=p.read_text()
install_old='chroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev'
install_new='chroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev nlohmann-json3-dev'
if install_new not in s:
    if install_old not in s:
        raise SystemExit('MMDVMHost dependency install anchor not found')
    s=s.replace(install_old,install_new,1)
apt_update='echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get update\n'
if apt_update not in s:
    anchor='echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."\n'
    if anchor not in s:
        raise SystemExit('MMDVMHost build stage anchor not found')
    s=s.replace(anchor,apt_update,1)
purge_old='apt-get purge -y g++ make git libmosquitto-dev'
purge_new='apt-get purge -y g++ make git libmosquitto-dev nlohmann-json3-dev'
if purge_new not in s:
    if purge_old not in s:
        raise SystemExit('MMDVMHost build dependency purge anchor not found')
    s=s.replace(purge_old,purge_new,1)
p.write_text(s)
PY
bash -n builder/build-image.sh
grep -q 'nlohmann-json3-dev' builder/build-image.sh
echo '2PNY 0.1.6 MMDVMHost build dependencies fixed and kept out of final image'
