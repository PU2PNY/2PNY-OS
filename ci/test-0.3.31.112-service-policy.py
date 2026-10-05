#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "src/2pny-update-entrypoint-0.3.31.112.py"
spec = importlib.util.spec_from_file_location("pny_update_entry_031112", ENTRY)
assert spec and spec.loader
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
engine = entry.engine

BASE = {
    "schema": 1,
    "version": "0.3.31.112",
    "from_compatible": ["0.3.31.110"],
    "files": [{
        "path": "/usr/share/2pny/example.txt",
        "sha256": "0" * 64,
        "size": 1,
        "mode": "0644",
    }],
}


def expect_rejected(unit: str) -> None:
    manifest = dict(BASE)
    manifest["restart_units"] = [unit]
    manifest["health_units"] = [unit]
    try:
        engine.parse_manifest(manifest, "0.3.31.112")
    except engine.UpdateError:
        return
    raise AssertionError(f"unsafe service unexpectedly accepted: {unit}")


def expect_accepted(unit: str) -> None:
    manifest = dict(BASE)
    manifest["restart_units"] = [unit]
    manifest["health_units"] = [unit]
    engine.parse_manifest(manifest, "0.3.31.112")


def main() -> None:
    expect_rejected("ssh.service")
    expect_rejected("cron.service")
    expect_rejected("MMDVMHost.service")
    for unit in sorted(entry.ALLOWED_SERVICE_UNITS):
        expect_accepted(unit)
    print("PASS: recovery service allowlist blocks non-PU2PNY units")


if __name__ == "__main__":
    main()
