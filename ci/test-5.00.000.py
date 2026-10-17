#!/usr/bin/env python3
from __future__ import annotations
import ast, json, py_compile, subprocess, tempfile
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
runtime = repo / "runtime/5x"
required = [
    runtime / "2pny-eventd.py",
    runtime / "2pny-hardware-manager.py",
    runtime / "2pny-network-manager.py",
    runtime / "2pny-wifi-apply.py",
    runtime / "2pny-protocol-manager.py",
    repo / "ci/patch-image-5.00.000.sh",
    repo / "docs/PU2PNY-OS_UI_CONTRACT.md",
]
for p in required:
    if not p.is_file() or p.stat().st_size == 0: raise SystemExit(f"missing required file: {p}")
for p in runtime.glob("*.py"):
    py_compile.compile(str(p), doraise=True)
    ast.parse(p.read_text())
subprocess.run(["bash", "-n", str(repo / "ci/patch-image-5.00.000.sh")], check=True)

checks = {
    "2pny-eventd.py": ["SOCK = RUN / \"event.sock\"", "socket.SOCK_DGRAM", "atomic_json"],
    "2pny-hardware-manager.py": ["no_probe_write", "physical_validation_required", "serial_inventory"],
    "2pny-network-manager.py": ["ip\", \"monitor", "signal_dbm", "default_route"],
    "2pny-wifi-apply.py": ["association_or_ipv4_failed", "rolled_back", "NetworkManager"],
    "2pny-protocol-manager.py": ["canonical_mmdvmhost_unit_missing", "mmdvmhost_not_healthy", "gateway_start_failed"],
}
for name, markers in checks.items():
    text=(runtime/name).read_text()
    for marker in markers:
        if marker not in text: raise SystemExit(f"{name}: marker missing: {marker}")

patch=(repo/"ci/patch-image-5.00.000.sh").read_text()
for marker in ("expected immutable 4.00.001 base", "host-name=pu2pny", "mmdvmhost.service", "5.00.000", "systemctl --root"):
    if marker not in patch: raise SystemExit(f"patch marker missing: {marker}")
if "curl | bash" in patch or "eval " in patch: raise SystemExit("unsafe shell pattern")

contract=(repo/"docs/PU2PNY-OS_UI_CONTRACT.md").read_text()
for marker in ("Ao Vivo", "Internet", "Protocolos", "APRS/DPRS", "Direct/P2P", "Display", "Helix", "Backup/Recovery"):
    if marker not in contract: raise SystemExit(f"UI contract missing: {marker}")

print("SW_500000_SOURCE_GATES_OK")
