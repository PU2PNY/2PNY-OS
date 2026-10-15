#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
required = [
    repo / "ci/patch-backend-4.00.002.py",
    repo / "ci/patch-image-4.00.002.sh",
    repo / "runtime/2pny-display-config.py",
    repo / "runtime/2pny-helix-mode.py",
    repo / "runtime/display-4.00.002.html",
    repo / "runtime/helix-4.00.002.html",
]
for p in required:
    if not p.is_file() or p.stat().st_size == 0:
        raise SystemExit(f"missing required file: {p}")

subprocess.run([sys.executable, "-m", "py_compile", str(repo / "runtime/2pny-display-config.py"), str(repo / "runtime/2pny-helix-mode.py"), str(repo / "ci/patch-backend-4.00.002.py")], check=True)
subprocess.run(["bash", "-n", str(repo / "ci/patch-image-4.00.002.sh")], check=True)

# Verify backend patch chain produces the expected local-only APIs/version.
with tempfile.TemporaryDirectory(prefix="pu2pny-400002-test-") as td:
    out = Path(td) / "main.go"
    subprocess.run([sys.executable, str(repo / "ci/patch-backend-4.00.002.py"), str(repo / "src/2pnyd-main-0.3.27.go"), str(out)], check=True)
    text = out.read_text()
    for marker in ('appVersion            = "4.00.002"', '"/api/display/config"', '"/api/helix"', '"/helix"', '/usr/local/sbin/2pny-display-config', '/usr/local/sbin/2pny-helix-mode'):
        if marker not in text:
            raise SystemExit(f"backend marker missing: {marker}")

# Import display helper without executing main and validate exact upstream layout
# mapping plus modem Transparent Data semantics.
spec = importlib.util.spec_from_file_location("display400002", repo / "runtime/2pny-display-config.py")
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
if mod.LAYOUTS != {"g4klx": 0, "on7lds_l2": 2, "on7lds_l3": 3, "on7lds_l3hs": 4}:
    raise SystemExit("unexpected Nextion layout mapping")
cfg = mod.normalize({"type": "nextion_driver_modem", "layout": "on7lds_l3", "brightness": 55, "idle_brightness": 12, "display_clock": True, "utc": False})
ini = mod.build_ini("[General]\nDisplay=None\n\n[Transparent Data]\nEnable=0\n", cfg)
for marker in ("Display=Nextion", "Port=modem", "ScreenLayout=3", "IdleBrightness=12", "Enable=1", "RemotePort=40094", "LocalPort=40095", "SendFrameType=1"):
    if marker not in ini:
        raise SystemExit(f"modem Nextion marker missing: {marker}")
oled = mod.normalize({"type": "oled3", "rotate": True, "invert": True, "scroll": True, "screensaver": True, "brightness": 10})
oled_ini = mod.build_ini("[General]\nDisplay=None\n", oled)
for marker in ("Display=OLED", "Type=3", "Rotate=1", "Invert=1", "Scroll=1", "LogoScreensaver=1"):
    if marker not in oled_ini:
        raise SystemExit(f"OLED marker missing: {marker}")

html = (repo / "runtime/display-4.00.002.html").read_text()
for marker in ("OLED Type 3", "OLED Type 6", "Nextion (enhanced w/driver)", "attached to modem", "HD44780", "TFT Serial", "LCDproc", "ON7LDS L2", "ON7LDS L3", "ON7LDS L3 HS", "rotate", "brightness"):
    if marker not in html:
        raise SystemExit(f"display UI marker missing: {marker}")

helix = (repo / "runtime/2pny-helix-mode.py").read_text()
for marker in ('VALID = {"off", "shadow", "process"}', '--self-test', 'legacy_protocol_transcoding_available', 'authorized_external_backend', 'production": False'):
    if marker not in helix:
        raise SystemExit(f"Helix guard marker missing: {marker}")

for doc, marker in (
    ("PU2PNY-OS_MASTER_SPEC.md", "DISPLAY-033"),
    ("PU2PNY-OS_CHANGELOG.md", "4.00.002"),
    ("PU2PNY-OS_RELEASE_STATUS.md", "4.00.002"),
    ("PU2PNY-OS_TEST_MATRIX.md", "SW-400002-DISPLAY"),
):
    if marker not in (repo / doc).read_text(errors="replace"):
        raise SystemExit(f"canonical marker missing: {doc}: {marker}")

print("SW_400002_SURGICAL_GATES_OK")
