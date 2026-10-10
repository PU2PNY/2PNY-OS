#!/usr/bin/env python3
"""Adapt the fully staged PU2PNY builder to Raspberry Pi Zero/Zero W ARMv6.

This is intentionally branch-local and must never alter the ARM64 release path.
Run only after the complete overlay chain through 0.3.31-alpha has been staged.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
p = root / "builder/build-image.sh"
s = p.read_text()

repls = {
    'ARCH="arm64"': 'ARCH="armhf"',
    'BASE_NAME="2026-09-15-raspios-bookworm-arm64-lite.img.xz"': 'BASE_NAME="2026-09-15-raspios-bookworm-armhf-lite.img.xz"',
    'BASE_URL="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-09-15/${BASE_NAME}"': 'BASE_URL="https://downloads.raspberrypi.com/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2026-09-15/${BASE_NAME}"',
    'BASE_SHA256="bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91"': 'BASE_SHA256="d82875ed98f905394094a41754a5621a6097655883a8f286e7c6c06477786c30"',
    'GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build': 'GOOS=linux GOARCH=arm GOARM=6 CGO_ENABLED=0 go build',
    'Compilando 2pnyd ARM64': 'Compilando 2pnyd ARM32/armhf (GOARM=6)',
    'Base: Raspberry Pi OS Lite 64-bit ${BASE_DATE} (Debian 12 Bookworm)': 'Base: Raspberry Pi OS Legacy Lite 32-bit ${BASE_DATE} (Debian 12 Bookworm)',
}

for old, new in repls.items():
    if old not in s:
        raise SystemExit(f"ARM32_PORT_ANCHOR_MISSING: {old}")
    s = s.replace(old, new)

required = [
    'ARCH="armhf"',
    'GOARCH=arm GOARM=6',
    'raspios-bookworm-armhf-lite.img.xz',
    'raspios_oldstable_lite_armhf',
    'd82875ed98f905394094a41754a5621a6097655883a8f286e7c6c06477786c30',
]
for anchor in required:
    if anchor not in s:
        raise SystemExit(f"ARM32_REQUIRED_ANCHOR_MISSING: {anchor}")
if 'GOARCH=arm64' in s or 'raspios-bookworm-arm64-lite.img.xz' in s:
    raise SystemExit('ARM64_ANCHOR_REMAINS_IN_ARM32_BUILDER')

p.write_text(s)
print('ARM32_0_3_31_123_BUILDER_READY')
