#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import re
p=Path('builder/build-image.sh')
s=p.read_text()
book_url='https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-09-15/2026-09-15-raspios-bookworm-arm64-lite.img.xz'
book_sha='bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91'
# Replace any current Raspberry Pi ARM64 Lite image URL, regardless of earlier hotfix shape.
s=re.sub(r'https://downloads\.raspberrypi\.(?:com|org)/[^"\'\s]+(?:trixie|bookworm)-arm64-lite\.img\.xz', book_url, s)
# Replace the known current Trixie checksum and any prior intended Bookworm checksum remains stable.
s=s.replace('cdf4f3bfac35ae947b46e4e767f935453810549779ac3290e05a6754aee627e5', book_sha)
# If an explicit URL assignment still references a trixie cache/name, normalize known filename tokens.
s=s.replace('2026-09-15-raspios-trixie-arm64-lite.img.xz','2026-09-15-raspios-bookworm-arm64-lite.img.xz')
# Make sure the authoritative values are actually present; fail instead of silently building wrong base.
if book_url not in s:
    raise SystemExit('Bookworm URL pin was not applied')
if book_sha not in s:
    raise SystemExit('Bookworm SHA256 pin was not applied')
p.write_text(s)
PY
grep -Fq '2026-09-15-raspios-bookworm-arm64-lite.img.xz' builder/build-image.sh
grep -Fq 'bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91' builder/build-image.sh
! grep -Fq '2026-09-15-raspios-trixie-arm64-lite.img.xz' builder/build-image.sh
echo '2PNY 0.1.8 official Bookworm Lite URL/SHA pin applied'
