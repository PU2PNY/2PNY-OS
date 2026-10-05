#!/usr/bin/env python3
"""Hardened integration entrypoint for PU2PNY-OS update candidate 0.3.31.112.

The transactional engine lives in 2pny-update-manager-0.3.31.112.py. This
entrypoint intentionally narrows service control to the same PU2PNY units used
by the known updater baseline. Runtime integration must invoke this entrypoint,
not the engine module directly.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ENGINE = Path(__file__).with_name("2pny-update-manager-0.3.31.112.py")
spec = importlib.util.spec_from_file_location("pny_update_engine_031112", ENGINE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load PU2PNY update engine")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

# Preserve the exact service surface used by the previous updater. Expanding
# this allowlist is a security-sensitive change and requires its own review,
# baseline analysis and regression tests.
ALLOWED_SERVICE_UNITS = frozenset({
    "2pny-station.service",
    "2pny-display-core.service",
    "2pny-netdiag.service",
    "2pnyd.service",
})

_original_validate_unit = engine.validate_unit


def validate_approved_unit(unit: str) -> str:
    value = _original_validate_unit(unit)
    if value not in ALLOWED_SERVICE_UNITS:
        raise engine.UpdateError(f"service unit outside PU2PNY update allowlist: {value}")
    return value


# Engine functions resolve validate_unit dynamically from their own module,
# therefore this policy applies consistently to manifest parsing, baseline
# capture, restart, health-check and rollback paths.
engine.validate_unit = validate_approved_unit


def main() -> int:
    return engine.main()


if __name__ == "__main__":
    raise SystemExit(main())
