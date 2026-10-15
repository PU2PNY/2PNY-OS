#!/usr/bin/env python3
"""Guarded PU2PNY Helix mode controller for physical-test candidates.

Helix remains optional. 'process' exposes the local PCM process bridge only; it
does not claim legacy AMBE/AMBE+2 transcoding unless an external licensed
backend is independently configured and detected.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

HELIX = Path("/usr/local/bin/helix-daemon")
STATE = Path("/var/lib/2pny/helix/mode.json")
SHADOW_SERVICE = "helix-voice.service"
PROCESS_SERVICE = "helix-voice-process.service"
LEGACY_BACKEND = Path("/var/lib/2pny/helix/legacy-backend.json")
VALID = {"off", "shadow", "process"}


def emit(obj: dict[str, Any], code: int = 0) -> None:
    print(json.dumps(obj, ensure_ascii=False))
    raise SystemExit(code)


def active(service: str) -> bool:
    try:
        return subprocess.run(["systemctl", "is-active", "--quiet", service], timeout=5).returncode == 0
    except Exception:
        return False


def ctl(*args: str, check: bool = True) -> None:
    subprocess.run(["systemctl", *args], check=check, timeout=20, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def legacy_backend_status() -> dict[str, Any]:
    try:
        obj = json.loads(LEGACY_BACKEND.read_text())
        if isinstance(obj, dict) and obj.get("enabled") is True and isinstance(obj.get("command"), str):
            cmd = obj["command"].strip()
            if cmd.startswith("/") and Path(cmd).is_file() and os.access(cmd, os.X_OK):
                return {"detected": True, "authorized_external_backend": True, "command": cmd}
    except Exception:
        pass
    return {"detected": False, "authorized_external_backend": False}


def current_mode() -> str:
    if active(PROCESS_SERVICE):
        return "process"
    if active(SHADOW_SERVICE):
        return "shadow"
    return "off"


def status() -> None:
    backend = legacy_backend_status()
    emit({
        "ok": True,
        "version": "4.00.002",
        "available": HELIX.is_file() and os.access(HELIX, os.X_OK),
        "mode": current_mode(),
        "modes": ["off", "shadow", "process"],
        "pcm_boundary": True,
        "process_socket": "/run/helix-voice/process.sock",
        "shadow_socket": "/run/helix-voice/observe.sock",
        "legacy_codec_backend": backend,
        "legacy_protocol_transcoding_available": bool(backend.get("detected")),
        "hvc_status": "experimental",
        "production": False,
        "note": "process = local PCM bridge; AMBE-family interoperability requires a separate authorized backend",
    })


def save(mode: str) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="mode.", dir=str(STATE.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"mode": mode, "version": "4.00.002"}, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(name, 0o600)
        os.replace(name, STATE)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def self_test() -> None:
    if not HELIX.is_file() or not os.access(HELIX, os.X_OK):
        emit({"ok": False, "error": "helix_unavailable"}, 1)
    try:
        run = subprocess.run([str(HELIX), "--self-test"], timeout=30, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except Exception as exc:
        emit({"ok": False, "error": "helix_self_test_failed", "detail": str(exc)}, 1)
    if run.returncode != 0:
        emit({"ok": False, "error": "helix_self_test_failed", "detail": run.stdout[-2000:]}, 1)


def apply() -> None:
    if os.geteuid() != 0:
        emit({"ok": False, "error": "root_required"}, 1)
    try:
        payload = json.load(sys.stdin)
    except Exception:
        emit({"ok": False, "error": "invalid_json"}, 1)
    if not isinstance(payload, dict):
        emit({"ok": False, "error": "invalid_json_object"}, 1)
    mode = str(payload.get("mode", "")).strip().lower()
    if mode not in VALID:
        emit({"ok": False, "error": "invalid_mode"}, 1)

    before = current_mode()
    try:
        if mode == "off":
            ctl("stop", PROCESS_SERVICE, check=False)
            ctl("stop", SHADOW_SERVICE, check=False)
        elif mode == "shadow":
            self_test()
            ctl("stop", PROCESS_SERVICE, check=False)
            ctl("restart", SHADOW_SERVICE)
            if not active(SHADOW_SERVICE):
                raise RuntimeError("shadow service did not become active")
        elif mode == "process":
            self_test()
            ctl("stop", SHADOW_SERVICE, check=False)
            ctl("restart", PROCESS_SERVICE)
            if not active(PROCESS_SERVICE):
                raise RuntimeError("process service did not become active")
        save(mode)
    except SystemExit:
        raise
    except Exception as exc:
        ctl("stop", PROCESS_SERVICE, check=False)
        ctl("stop", SHADOW_SERVICE, check=False)
        if before == "shadow":
            ctl("start", SHADOW_SERVICE, check=False)
        elif before == "process":
            ctl("start", PROCESS_SERVICE, check=False)
        emit({"ok": False, "error": "helix_apply_rolled_back", "detail": str(exc)}, 1)

    backend = legacy_backend_status()
    emit({
        "ok": True,
        "mode": current_mode(),
        "legacy_protocol_transcoding_available": bool(backend.get("detected")),
        "legacy_codec_backend": backend,
        "hardware_audio_validation": "PENDENTE",
        "production": False,
    })


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        status()
    elif action == "apply":
        apply()
    else:
        emit({"ok": False, "error": "unknown_action"}, 1)


if __name__ == "__main__":
    main()
