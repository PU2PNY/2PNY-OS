#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
p=Path('builder/build-image.sh')
s=p.read_text()
# The builder composes the Raspberry Pi URL from family/date/file variables.
# Replace every Trixie-family component rather than relying on one full literal URL.
s=s.replace('raspios_lite_arm64', 'raspios_oldstable_lite_arm64')
s=s.replace('2026-09-15-raspios-trixie-arm64-lite.img.xz', '2026-09-15-raspios-bookworm-arm64-lite.img.xz')
s=s.replace('cdf4f3bfac35ae947b46e4e767f935453810549779ac3290e05a6754aee627e5', 'bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91')
s=s.replace('Raspberry Pi OS Lite 2026-09-15', 'Raspberry Pi OS Legacy Lite Bookworm 2026-09-15')
if 'raspios_oldstable_lite_arm64' not in s or 'raspios-bookworm-arm64-lite.img.xz' not in s:
    raise SystemExit('Bookworm base pin did not apply')
if 'raspios-trixie-arm64-lite.img.xz' in s:
    raise SystemExit('Trixie image reference remains')
p.write_text(s)
PY
echo '2PNY hotfix5 builder base pinned to Bookworm Legacy Lite'
