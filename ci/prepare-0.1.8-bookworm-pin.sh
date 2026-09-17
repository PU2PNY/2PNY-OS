#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/build-image.sh')
s=p.read_text()
book_sha='bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91'
# The builder composes the URL from variables, so normalize each component.
s=s.replace('raspios_lite_arm64-2026-09-15','raspios_oldstable_lite_arm64-2026-09-15')
s=s.replace('/raspios_lite_arm64/', '/raspios_oldstable_lite_arm64/')
s=s.replace('raspios_lite_arm64/images', 'raspios_oldstable_lite_arm64/images')
s=s.replace('2026-09-15-raspios-trixie-arm64-lite.img.xz','2026-09-15-raspios-bookworm-arm64-lite.img.xz')
s=s.replace('cdf4f3bfac35ae947b46e4e767f935453810549779ac3290e05a6754aee627e5', book_sha)
# Protect against alternate variable values that still name the current family.
s=s.replace('raspios-trixie-arm64-lite.img.xz','raspios-bookworm-arm64-lite.img.xz')
if '2026-09-15-raspios-bookworm-arm64-lite.img.xz' not in s:
    raise SystemExit('Bookworm filename pin was not applied')
if 'raspios_oldstable_lite_arm64' not in s:
    raise SystemExit('Bookworm oldstable collection pin was not applied')
if book_sha not in s:
    raise SystemExit('Bookworm SHA256 pin was not applied')
if '2026-09-15-raspios-trixie-arm64-lite.img.xz' in s:
    raise SystemExit('Trixie filename remains after pin')
p.write_text(s)
PY
grep -Fq 'raspios_oldstable_lite_arm64' builder/build-image.sh
grep -Fq '2026-09-15-raspios-bookworm-arm64-lite.img.xz' builder/build-image.sh
grep -Fq 'bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91' builder/build-image.sh
! grep -Fq '2026-09-15-raspios-trixie-arm64-lite.img.xz' builder/build-image.sh
echo '2PNY 0.1.8 official Bookworm Lite collection/file/SHA pin applied'
