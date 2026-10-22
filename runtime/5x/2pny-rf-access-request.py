#!/usr/bin/env python3
"""Privileged one-shot access-policy executor; triggered by a systemd Path unit."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

SRC = Path("/usr/local/libexec/pu2pny/2pny-rf-access")
REQUEST = Path("/run/2pny/access-request.json")
RESULT = Path("/run/2pny/access-result.json")

def atomic_result(value: dict) -> None:
    RESULT.parent.mkdir(exist_ok=True, parents=True)
    fd, tmp = tempfile.mkstemp(prefix=".access-result.", dir=str(RESULT.parent))
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(tmp, 0o640)
        os.replace(tmp, RESULT)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def main() -> int:
    if not REQUEST.is_file() or REQUEST.stat().st_size > 32768:
        atomic_result({"ok": False, "error": "invalid_request"})
        return 1
    try:
        spec = importlib.util.spec_from_file_location("rfaccess", SRC)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        request = json.loads(REQUEST.read_text())
        if not isinstance(request, dict):
            raise ValueError("invalid_request")
        # Explicitly leave status unknown until successfully applied.
        result = module.apply(module.DEFAULT_INI, module.DEFAULT_STATE,
                              module.DEFAULT_UNIT, request, False)
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
    finally:
        try:
            REQUEST.unlink()
        except OSError:
            pass
    atomic_result(result)
    return 0 if result.get("ok") else 1

if __name__ == "__main__":
    sys.exit(main())
