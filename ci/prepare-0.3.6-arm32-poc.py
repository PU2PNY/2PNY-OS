#!/usr/bin/env python3
"""Prepare the fully-staged PU2PNY builder for an isolated ARM32/armhf proof-of-concept.

This never edits the ARM64 production branch. Run only after the normal 0.3.6 overlay
chain has finished, so we port the exact builder that would otherwise create ARM64.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
p=root/"builder/build-image.sh"
s=p.read_text()

repls={
'ARCH="arm64"':'ARCH="armhf"',
'BASE_NAME="2026-09-15-raspios-bookworm-arm64-lite.img.xz"':'BASE_NAME="2026-09-15-raspios-bookworm-armhf-lite.img.xz"',
'BASE_URL="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-09-15/${BASE_NAME}"':'BASE_URL="https://downloads.raspberrypi.com/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2026-09-15/${BASE_NAME}"',
'BASE_SHA256="bcaefdf9c40dbed31dcaeb3b8494e498b4f1e3078c2604b0d9f5f595f8f6fd91"':'BASE_SHA256="d82875ed98f905394094a41754a5621a6097655883a8f286e7c6c06477786c30"',
'GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build':'GOOS=linux GOARCH=arm GOARM=6 CGO_ENABLED=0 go build',
'Compilando 2pnyd ARM64':'Compilando 2pnyd ARM32/armhf (GOARM=6)',
'Base: Raspberry Pi OS Lite 64-bit ${BASE_DATE} (Debian 12 Bookworm)':'Base: Raspberry Pi OS Legacy Lite 32-bit ${BASE_DATE} (Debian 12 Bookworm)',
}
for old,new in repls.items():
    if old not in s:
        raise SystemExit(f"ARM32_PORT_ANCHOR_MISSING: {old}")
    s=s.replace(old,new)

# Host stays aarch64 intentionally: GitHub's ARM64 runner was proven to execute
# the official armhf rootfs natively. This avoids QEMU overhead/variance.
assert 'ARCH="armhf"' in s
assert 'GOARCH=arm GOARM=6' in s
assert 'raspios-bookworm-armhf-lite.img.xz' in s
assert 'raspios_oldstable_lite_armhf' in s
assert 'GOARCH=arm64' not in s
assert 'raspios-bookworm-arm64-lite.img.xz' not in s
p.write_text(s)
print("ARM32_BUILDER_READY")
