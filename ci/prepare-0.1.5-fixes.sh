#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Use a canonical standalone Python source instead of nested generated escape sequences.
install -m 0755 "$SELF_DIR/../src/2pny-hardware-probe.py" rootfs-overlay/usr/local/sbin/2pny-hardware-probe

python3 - <<'PY'
from pathlib import Path

# Force modem UART settings into a global config section so they apply regardless
# of the final section shipped by the Raspberry Pi base image.
p = Path('builder/build-image.sh')
s = p.read_text()
old = '''grep -qxF 'enable_uart=1' "$BOOTCFG" || printf '\\nenable_uart=1\\n' >> "$BOOTCFG"
grep -qxF 'dtoverlay=disable-bt' "$BOOTCFG" || printf 'dtoverlay=disable-bt\\n' >> "$BOOTCFG"
grep -qxF 'dtparam=i2c_arm=on' "$BOOTCFG" || printf 'dtparam=i2c_arm=on\\n' >> "$BOOTCFG"'''
new = '''if ! grep -q '^# 2PNY MMDVM UART$' "$BOOTCFG"; then
  printf '\\n[all]\\n# 2PNY MMDVM UART\\nenable_uart=1\\ndtoverlay=disable-bt\\ndtparam=i2c_arm=on\\n' >> "$BOOTCFG"
fi'''
if old not in s:
    raise SystemExit('global UART config anchor not found')
s = s.replace(old, new, 1)
p.write_text(s)
PY

python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__

grep -q 'bytes((0xE0, 0x03, 0x00))' rootfs-overlay/usr/local/sbin/2pny-hardware-probe
grep -q 'connect\\xff\\xff\\xff' rootfs-overlay/usr/local/sbin/2pny-hardware-probe
grep -q '^# 2PNY MMDVM UART' builder/build-image.sh

echo '2PNY 0.1.5 UART/probe hardening applied'
