#!/usr/bin/env python3
"""Conservative PU2PNY-OS 5.x hardware inventory: no RF writes, no guessing."""
from __future__ import annotations
import json, os, platform, socket, tempfile
from pathlib import Path
from typing import Any

OUT = Path(os.environ.get("PU2PNY_HARDWARE_OUT", "/run/pu2pny/hardware.json"))
LEGACY = Path("/var/lib/2pny/hardware.json")

def read_text(p: Path) -> str:
    try: return p.read_text(errors="replace").strip("\x00\r\n ")
    except OSError: return ""

def load_json(p: Path) -> dict[str, Any]:
    try:
        value = json.loads(p.read_text())
        return value if isinstance(value, dict) else {}
    except Exception: return {}

def atomic(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, sort_keys=True, separators=(",", ":")); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp, 0o644); os.replace(tmp, path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def serial_inventory() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for name in ("serial0", "serial1"):
        p = Path("/dev") / name
        if p.exists() or p.is_symlink():
            try: real = str(p.resolve(strict=True))
            except OSError: real = "—"
            out.append({"path": str(p), "realpath": real, "present": real != "—"})
    for pat in ("ttyAMA*", "ttyUSB*", "ttyACM*"):
        for p in sorted(Path("/dev").glob(pat)):
            if not any(x["path"] == str(p) for x in out): out.append({"path": str(p), "realpath": str(p), "present": True})
    return out

def main() -> int:
    legacy = load_json(LEGACY)
    m = legacy.get("mmdvm") if isinstance(legacy.get("mmdvm"), dict) else {}
    model = read_text(Path("/proc/device-tree/model")) or "—"
    i2c = [str(p) for p in sorted(Path("/dev").glob("i2c-*"))]
    net = [p.name for p in sorted(Path("/sys/class/net").glob("*")) if p.name != "lo"]
    payload = {
        "schema": 1, "version": "5.00.000",
        "platform": {"model": model, "architecture": platform.machine() or "unknown", "hostname": socket.gethostname()},
        "serial": serial_inventory(), "i2c": {"buses": i2c, "present": bool(i2c)}, "network_interfaces": net,
        "mmdvm": {
            "detected": m.get("detected") is True, "port": m.get("port") or "—", "realpath": m.get("realpath") or "—",
            "baud": m.get("baud") if isinstance(m.get("baud"), int) else None, "description": m.get("description") or "—",
            "profile": m.get("profile") or "—", "duplex": m.get("duplex", "unknown"),
            "capabilities": m.get("capabilities") if isinstance(m.get("capabilities"), list) else []},
        "policy": {"no_probe_write": True, "legacy_evidence_preserved": True, "physical_validation_required": True}}
    atomic(OUT, payload); return 0

if __name__ == "__main__": raise SystemExit(main())
