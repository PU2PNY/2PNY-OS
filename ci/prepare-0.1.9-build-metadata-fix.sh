#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
p=Path('builder/build-image.sh')
s=p.read_text()
s=s.replace('2PNY OS ${VERSION}\nArchitecture:', 'PU2PNY OS ${VERSION}\nArchitecture:')
s=s.replace('Base: Raspberry Pi OS Lite 64-bit ${BASE_DATE} (Debian 13 Trixie)', 'Base: Raspberry Pi OS Lite 64-bit ${BASE_DATE} (Debian 12 Bookworm)')
s=s.replace('Temporary password: 2pnysetup', 'Setup AP security: open / no password')
p.write_text(s)
PY

grep -q 'PU2PNY OS ${VERSION}' builder/build-image.sh
grep -q 'Debian 12 Bookworm' builder/build-image.sh
grep -q 'Setup AP security: open / no password' builder/build-image.sh
! grep -q 'Debian 13 Trixie' builder/build-image.sh

echo 'PU2PNY 0.1.9 build metadata corrected'
