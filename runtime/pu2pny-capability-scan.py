#!/usr/bin/env python3
"""PU2PNY-OS 4.00.000 conservative capability inventory.

No RF/audio capability is promoted to operational merely from package presence.
The scanner consolidates existing local evidence into a sanitized JSON snapshot.
It performs no radio writes and no network calls.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = 1
OS_VERSION = "4.00.000"
BASE = Path(os.environ.get("PU2PNY_ROOT", "/"))
OUT_OVERRIDE = os.environ.get("PU2PNY_CAPABILITIES_OUT", "")
TEST_ARCH = os.environ.get("PU2PNY_TEST_ARCH", "")


def rp(path: str) -> Path:
    p = Path(path)
    if BASE == Path("/"):
        return p
    return BASE / str(p).lstrip("/")


def read_text(path: str, limit: int = 1_000_000) -> str:
    try:
        return rp(path).read_text(errors="replace")[:limit].strip("\x00\n\r ")
    except (OSError, UnicodeError):
        return ""


def read_json(path: str) -> dict[str, Any]:
    raw = read_text(path)
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return obj if isinstance(obj, dict) else {}


def has_executable(name: str) -> bool:
    if BASE == Path("/"):
        return shutil.which(name) is not None
    for directory in ("/usr/local/bin", "/usr/local/sbin", "/usr/bin", "/usr/sbin", "/bin", "/sbin"):
        p = rp(f"{directory}/{name}")
        if p.is_file() and os.access(p, os.X_OK):
            return True
    return False


def systemd_state(unit: str) -> dict[str, str]:
    if BASE != Path("/") or shutil.which("systemctl") is None:
        return {"active": "unknown", "enabled": "unknown"}

    def run(*args: str) -> str:
        try:
            cp = subprocess.run(
                ["systemctl", *args, unit],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1.5,
            )
            lines = cp.stdout.strip().splitlines()
            return lines[0] if lines else "unknown"
        except (OSError, subprocess.TimeoutExpired):
            return "unknown"

    return {"active": run("is-active"), "enabled": run("is-enabled")}


def normalize_cap(value: Any) -> str:
    return "".join(ch for ch in str(value).upper() if ch.isalnum())


def state_for_modem_cap(mmdvm: dict[str, Any], aliases: tuple[str, ...]) -> dict[str, Any]:
    detected = mmdvm.get("detected") is True
    raw_caps = mmdvm.get("capabilities")
    caps = {normalize_cap(v) for v in raw_caps} if isinstance(raw_caps, list) else set()
    present = any(normalize_cap(alias) in caps for alias in aliases)
    if not detected:
        status = "unavailable"
        reason = "modem_not_detected"
    elif not isinstance(raw_caps, list):
        status = "unknown"
        reason = "firmware_capabilities_not_reported"
    elif present:
        status = "available"
        reason = "firmware_reports_capability"
    else:
        status = "unavailable"
        reason = "firmware_does_not_report_capability"
    return {"status": status, "reason": reason, "evidence": "DOC", "rf_validated": False}


def display_inventory() -> dict[str, Any]:
    detected = read_json("/var/lib/2pny/display-detection.json")
    runtime = read_json("/run/2pny/display-detect-status.json")
    displays = detected.get("displays") if isinstance(detected.get("displays"), list) else []
    clean = []
    for item in displays[:16]:
        if not isinstance(item, dict):
            continue
        clean.append({
            "family": item.get("family") or item.get("type") or "unknown",
            "model": item.get("model") or "—",
            "resolution": item.get("resolution") or "—",
            "transport": item.get("transport") or "—",
            "port": item.get("port") or "—",
            "physical_confirmed": bool(item.get("physical_confirmed", False)),
            "state": item.get("state") or "detected",
        })
    return {
        "state": detected.get("state") or runtime.get("state") or ("detected" if clean else "unknown"),
        "items": clean,
        "supported_families": ["nextion", "oled", "hd44780", "lcdproc"],
        "physical_validation_required": True,
    }


def helix_inventory() -> dict[str, Any]:
    binary = has_executable("helix-daemon")
    service = systemd_state("helix-voice.service")
    if not binary:
        state = "unavailable"
    elif service["active"] == "active":
        state = "ready"
    elif service["active"] in {"failed", "deactivating"}:
        state = "error"
    else:
        state = "disabled"
    return {
        "state": state,
        "binary_present": binary,
        "service": service,
        "mode_default": "off",
        "modes": ["off", "shadow", "process"],
        "ipc": "local-hxp1",
        "fallback_required": True,
        "hvc": {"state": "blocked", "reason": "research_quality_and_fto_gates", "production": False},
        "ambe_backend": {"state": "external_required", "native_helix": False, "production": False},
    }


def remote_inventory() -> dict[str, Any]:
    return {
        "cloudflare": {"installed": has_executable("cloudflared"), "default": "disabled"},
        "tailscale": {"installed": has_executable("tailscale"), "default": "disabled"},
        "zerotier": {"installed": has_executable("zerotier-cli"), "default": "disabled"},
    }


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def main() -> int:
    hw = read_json("/var/lib/2pny/hardware.json")
    mmdvm = hw.get("mmdvm") if isinstance(hw.get("mmdvm"), dict) else {}
    model = hw.get("raspberry_model") or read_text("/proc/device-tree/model") or "—"
    arch = TEST_ARCH or platform.machine() or "unknown"
    duplex_raw = mmdvm.get("duplex", "unknown")
    duplex = ("yes" if duplex_raw else "no") if isinstance(duplex_raw, bool) else str(duplex_raw or "unknown")

    protocols = {
        "dmr": state_for_modem_cap(mmdvm, ("DMR",)),
        "dstar": state_for_modem_cap(mmdvm, ("D-Star", "DSTAR")),
        "ysf": state_for_modem_cap(mmdvm, ("YSF", "C4FM")),
        "p25": state_for_modem_cap(mmdvm, ("P25",)),
        "nxdn": state_for_modem_cap(mmdvm, ("NXDN",)),
        "pocsag": state_for_modem_cap(mmdvm, ("POCSAG",)),
        "m17": {"status": "unknown", "reason": "requires_explicit_compatible_firmware_or_backend", "evidence": "DOC", "rf_validated": False},
        "fm": {"status": "unknown", "reason": "requires_explicit_analog_capable_modem_or_radio", "evidence": "DOC", "rf_validated": False},
    }

    services = {}
    for name, unit in (
        ("mmdvmhost", "2pny-mmdvmhost.service"),
        ("dmrgateway", "dmrgateway.service"),
        ("nextiondriver", "2pny-nextiondriver.service"),
    ):
        services[name] = systemd_state(unit)

    payload = {
        "schema": SCHEMA,
        "os_version": OS_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "policy": {"capability_is_not_hw_validation": True, "unknown_is_not_promoted": True, "no_network_probe": True, "no_rf_write": True},
        "platform": {"architecture": arch, "model": model},
        "modem": {
            "detected": mmdvm.get("detected") is True,
            "profile": mmdvm.get("profile") or "—",
            "description": mmdvm.get("description") or "—",
            "port": mmdvm.get("port") or "—",
            "realpath": mmdvm.get("realpath") or "—",
            "baud": mmdvm.get("baud") if isinstance(mmdvm.get("baud"), int) else None,
            "duplex": duplex,
            "reported_capabilities": mmdvm.get("capabilities") if isinstance(mmdvm.get("capabilities"), list) else [],
        },
        "protocols": protocols,
        "display": display_inventory(),
        "services": services,
        "transcoder": {"helix": helix_inventory()},
        "remote_access": remote_inventory(),
        "validation": {"software": "pending", "vps": "pending", "hardware": "pending"},
    }

    out = Path(OUT_OVERRIDE) if OUT_OVERRIDE else rp("/run/2pny/capabilities.json")
    atomic_write(out, payload)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
