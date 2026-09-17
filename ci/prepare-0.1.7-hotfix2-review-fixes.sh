#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

root = Path('.')

# 1) AP toggle must be authoritative and survive the setup watcher/reboot.
apctl = root / 'rootfs-overlay/usr/local/sbin/2pny-ap-control'
s = apctl.read_text()
if 'DISABLED_MARKER=/var/lib/2pny/ap-disabled' not in s:
    s = s.replace('PROFILE=2PNY-SETUP\n', 'PROFILE=2PNY-SETUP\nDISABLED_MARKER=/var/lib/2pny/ap-disabled\n', 1)
    s = s.replace('    ensure_profile\n', '''    ensure_profile
    mkdir -p /var/lib/2pny
    rm -f "$DISABLED_MARKER"
    systemctl unmask 2pny-setup-watch.service 2>/dev/null || true
    systemctl unmask 2pny-setup-watch.timer 2>/dev/null || true
''', 1)
    s = s.replace('  off)\n    nmcli connection down "$PROFILE" >/dev/null 2>&1 || true\n', '''  off)
    mkdir -p /var/lib/2pny
    touch "$DISABLED_MARKER"
    nmcli connection modify "$PROFILE" connection.autoconnect no >/dev/null 2>&1 || true
    systemctl mask --now 2pny-setup-watch.timer 2>/dev/null || true
    systemctl mask --now 2pny-setup-watch.service 2>/dev/null || true
    nmcli connection down "$PROFILE" >/dev/null 2>&1 || true
''', 1)
apctl.write_text(s)

# 2) Never claim a display from a shared I2C address alone. Keep such addresses
# as candidates, then prefer confirmable HAT/framebuffer evidence.
hp = root / 'rootfs-overlay/usr/local/sbin/2pny-hardware-probe'
hs = hp.read_text()
new_probe = r'''def probe_configured_display(i2c, hat):
    addresses = {str(item.get("address", "")).lower() for item in i2c}
    candidate = None
    if "0x3c" in addresses or "0x3d" in addresses:
        addr = "0x3c" if "0x3c" in addresses else "0x3d"
        candidate = {"detected": False, "state": "i2c_candidate", "class": "display_candidate", "model": "Possível display I2C", "address": addr, "confidence": "candidate"}
    elif "0x27" in addresses or "0x3f" in addresses:
        addr = "0x27" if "0x27" in addresses else "0x3f"
        candidate = {"detected": False, "state": "i2c_candidate", "class": "display_candidate", "model": "Possível LCD/expansor I2C", "address": addr, "confidence": "candidate"}
    h = " ".join(str(hat.get(k, "")) for k in ("product", "vendor")).lower()
    if any(word in h for word in ("display", "screen", "lcd", "oled", "tft")):
        return {"detected": True, "state": "hat_metadata", "class": "hat_display", "model": hat.get("product") or "Display HAT", "confidence": "hat_metadata"}
    for fb in sorted(glob.glob("/sys/class/graphics/fb*")):
        name = read_text(Path(fb) / "name")
        low = name.lower()
        if name and any(word in low for word in ("tft", "lcd", "ili", "st77", "fb_", "waveshare")):
            return {"detected": True, "state": "framebuffer", "class": "framebuffer", "model": name, "device": fb, "confidence": "kernel"}
    return candidate
'''
hs2, n = re.subn(r'def probe_configured_display\(i2c, hat\):\n.*?\n    return None\n', new_probe, hs, count=1, flags=re.S)
if n != 1:
    raise SystemExit('probe_configured_display replacement failed')
hp.write_text(hs2)

# Build-time contracts for the two review fixes.
v = root / 'builder/validate-source.sh'
vs = v.read_text()
if '# 2PNY_HOTFIX2_REVIEW_FIXES' not in vs:
    vs += '''\n# 2PNY_HOTFIX2_REVIEW_FIXES\necho "[2PNY] Validate AP persistence and conservative display detection"\ngrep -q 'DISABLED_MARKER=/var/lib/2pny/ap-disabled' rootfs-overlay/usr/local/sbin/2pny-ap-control\ngrep -q 'mask --now 2pny-setup-watch.service' rootfs-overlay/usr/local/sbin/2pny-ap-control\ngrep -q '"detected": False, "state": "i2c_candidate"' rootfs-overlay/usr/local/sbin/2pny-hardware-probe\n! grep -q '"detected": True, "state": "i2c_configured"' rootfs-overlay/usr/local/sbin/2pny-hardware-probe\n'''
v.write_text(vs)
PY

chmod 0755 rootfs-overlay/usr/local/sbin/2pny-ap-control rootfs-overlay/usr/local/sbin/2pny-hardware-probe
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__

echo '2PNY hotfix2 review fixes applied'
