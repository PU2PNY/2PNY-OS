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

# Gate the staged UI against the same renderer anchor used by the official 0.3.31 image patch.
hotspot = root / "rootfs-overlay/usr/share/2pny/hotspot.html"
if 'function renderFamilies(){updateRadioGuide();' not in hotspot.read_text():
    raise SystemExit('ARM32_0331_STAGE_RENDERER_GATE_FAILED')

repls = {
    'ARCH="arm64"': '''ARCH="armhf"
# ARM32 build-host compatibility only. Current GitHub hosts may not execute
# armhf userspace directly; register qemu-arm binfmt for chroot steps.
# Nothing from QEMU is copied into the final PU2PNY-OS image.
if [ "$(uname -m)" != "armv7l" ] && [ "$(uname -m)" != "armv6l" ]; then
  if [ ! -e /proc/sys/fs/binfmt_misc/qemu-arm ]; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends qemu-user-static binfmt-support
    update-binfmts --enable qemu-arm || true
  fi
  test -e /proc/sys/fs/binfmt_misc/qemu-arm
  grep -q '^enabled' /proc/sys/fs/binfmt_misc/qemu-arm
fi''',
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

# The upstream image builder contains a host-architecture guard written for its
# original native ARM64 workflow. For this branch only, replace that policy
# guard with the mandatory qemu-arm gate above. We locate the block by its
# unique error text and delete only the enclosing shell if/fi block.
msg = 'ERRO: este builder instala pacotes dentro do rootfs e deve rodar em Linux ARM64/aarch64.'
lines = s.splitlines(keepends=True)
try:
    mid = next(i for i, line in enumerate(lines) if msg in line)
except StopIteration:
    raise SystemExit('ARM32_HOST_GUARD_MESSAGE_MISSING')
start = next((i for i in range(mid, max(-1, mid - 10), -1)
              if lines[i].strip().startswith('if ') and lines[i].strip().endswith('then')), None)
end = next((i for i in range(mid, min(len(lines), mid + 10))
            if lines[i].strip() == 'fi'), None)
if start is None or end is None or end <= start:
    raise SystemExit('ARM32_HOST_GUARD_BLOCK_NOT_FOUND')
del lines[start:end + 1]
s = ''.join(lines)
if msg in s:
    raise SystemExit('ARM32_HOST_GUARD_STILL_PRESENT')

required = [
    'ARCH="armhf"',
    'GOARCH=arm GOARM=6',
    'raspios-bookworm-armhf-lite.img.xz',
    'raspios_oldstable_lite_armhf',
    'd82875ed98f905394094a41754a5621a6097655883a8f286e7c6c06477786c30',
    '/proc/sys/fs/binfmt_misc/qemu-arm',
]
for anchor in required:
    if anchor not in s:
        raise SystemExit(f"ARM32_REQUIRED_ANCHOR_MISSING: {anchor}")
if 'GOARCH=arm64' in s or 'raspios-bookworm-arm64-lite.img.xz' in s:
    raise SystemExit('ARM64_ANCHOR_REMAINS_IN_ARM32_BUILDER')

p.write_text(s)
print('ARM32_0_3_31_123_BUILDER_READY')
