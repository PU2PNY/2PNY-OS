#!/usr/bin/env python3
"""PU2PNY-OS display configurator with Pi-Star/WPSD-compatible MMDVMHost semantics.

This helper edits only display-related INI sections. It never flashes HMI/TFT
files and never guesses a display model. Physical display validation remains HW.
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

INI = Path("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
STATE = Path("/var/lib/2pny/display/config.json")
BACKUP = Path("/var/lib/2pny/display/MMDVM-Host.ini.pre-4.00.002")
MMDVM_SERVICE = "2pny-mmdvmhost.service"
DRIVER_SERVICE = "2pny-nextiondriver.service"

DISPLAY_TYPES = {
    "none": "None",
    "oled3": "OLED",
    "oled6": "OLED",
    "nextion": "Nextion",
    "nextion_driver": "Nextion",
    "nextion_driver_modem": "Nextion",
    "hd44780": "HD44780",
    "tft_serial": "TFT Serial",
    "lcdproc": "LCDproc",
}
LAYOUTS = {"g4klx": 0, "on7lds_l2": 2, "on7lds_l3": 3, "on7lds_l3hs": 4}
SERIAL_RE = re.compile(r"^/dev/(serial[0-9]+|ttyAMA[0-9]+|ttyUSB[0-9]+|ttyACM[0-9]+|serial/by-id/[A-Za-z0-9_.:+@-]+)$")


def fail(code: str, detail: str = "") -> None:
    print(json.dumps({"ok": False, "error": code, "detail": detail}, ensure_ascii=False))
    raise SystemExit(1)


def clamp_int(value: Any, name: str, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        fail("invalid_" + name)
    if n < lo or n > hi:
        fail("invalid_" + name, f"expected {lo}..{hi}")
    return n


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if value in (0, 1, "0", "1"):
        return str(value) == "1"
    fail("invalid_boolean")
    return False


def valid_port(value: Any, allow_modem: bool = True, require_present: bool = True) -> str:
    port = str(value or "").strip()
    if allow_modem and port == "modem":
        return port
    if not SERIAL_RE.fullmatch(port):
        fail("invalid_display_port", port)
    if require_present and not Path(port).exists():
        fail("display_port_not_present", port)
    return port


def available_ports() -> list[str]:
    found = {"modem"}
    for pattern in ("/dev/serial[0-9]*", "/dev/ttyAMA*", "/dev/ttyUSB*", "/dev/ttyACM*", "/dev/serial/by-id/*"):
        for item in glob.glob(pattern):
            if SERIAL_RE.fullmatch(item):
                found.add(item)
    return sorted(found, key=lambda x: (x != "modem", x))


def service_active(name: str) -> bool:
    try:
        return subprocess.run(["systemctl", "is-active", "--quiet", name], timeout=5).returncode == 0
    except Exception:
        return False


def service_enabled(name: str) -> bool:
    try:
        return subprocess.run(["systemctl", "is-enabled", "--quiet", name], timeout=5).returncode == 0
    except Exception:
        return False


def systemctl(*args: str, check: bool = True) -> None:
    subprocess.run(["systemctl", *args], check=check, timeout=20, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def section_patch(text: str, section: str, values: dict[str, Any]) -> str:
    lines = text.splitlines(keepends=True)
    header = f"[{section}]"
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i
            break
    if start is None:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        if lines and lines[-1].strip():
            lines.append("\n")
        lines.append(header + "\n")
        for key, value in values.items():
            lines.append(f"{key}={value}\n")
        return "".join(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].lstrip().startswith("[") and lines[i].rstrip().endswith("]"):
            end = i
            break
    pending = {str(k): str(v) for k, v in values.items()}
    for i in range(start + 1, end):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", ";")) or "=" not in raw:
            continue
        key = raw.split("=", 1)[0].strip()
        if key in pending:
            lines[i] = f"{key}={pending.pop(key)}\n"
    if pending:
        lines[end:end] = [f"{key}={value}\n" for key, value in pending.items()]
    return "".join(lines)


def atomic_write(path: Path, text: str, mode: int = 0o640) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmpname = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmpname, mode)
        os.replace(tmpname, path)
    finally:
        try:
            os.unlink(tmpname)
        except FileNotFoundError:
            pass


def load_state() -> dict[str, Any]:
    try:
        data = json.loads(STATE.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(cfg: dict[str, Any]) -> None:
    atomic_write(STATE, json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", 0o600)


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    dtype = str(payload.get("type", "none")).strip().lower()
    if dtype not in DISPLAY_TYPES:
        fail("invalid_display_type", dtype)
    cfg: dict[str, Any] = {"type": dtype}
    if dtype.startswith("nextion"):
        layout = str(payload.get("layout", "g4klx")).strip().lower()
        if layout not in LAYOUTS:
            fail("invalid_nextion_layout", layout)
        if dtype == "nextion_driver_modem":
            port = "modem"
        else:
            port = valid_port(payload.get("port", "modem"), allow_modem=(dtype == "nextion"))
        cfg.update({"port": port, "layout": layout,
                    "brightness": clamp_int(payload.get("brightness", 50), "brightness", 0, 100),
                    "idle_brightness": clamp_int(payload.get("idle_brightness", 20), "idle_brightness", 0, 100),
                    "display_clock": as_bool(payload.get("display_clock"), True),
                    "utc": as_bool(payload.get("utc"), False)})
    elif dtype in ("oled3", "oled6"):
        cfg.update({"brightness": clamp_int(payload.get("brightness", 0), "brightness", 0, 255),
                    "screensaver": as_bool(payload.get("screensaver"), True),
                    "scroll": as_bool(payload.get("scroll"), dtype == "oled3") if dtype == "oled3" else False,
                    "rotate": as_bool(payload.get("rotate"), False),
                    "invert": as_bool(payload.get("invert"), False)})
    elif dtype == "tft_serial":
        cfg.update({"port": valid_port(payload.get("port", "modem"), allow_modem=True),
                    "brightness": clamp_int(payload.get("brightness", 50), "brightness", 0, 100)})
    elif dtype == "lcdproc":
        cfg.update({"display_clock": as_bool(payload.get("display_clock"), True),
                    "utc": as_bool(payload.get("utc"), False),
                    "dim_on_idle": as_bool(payload.get("dim_on_idle"), False)})
    return cfg


def build_ini(original: str, cfg: dict[str, Any]) -> str:
    dtype = cfg["type"]
    text = section_patch(original, "General", {"Display": DISPLAY_TYPES[dtype]})
    if dtype.startswith("nextion"):
        mmdvm_port = "/dev/ttyNextionDriver" if dtype == "nextion_driver" else cfg["port"]
        text = section_patch(text, "Nextion", {"Port": mmdvm_port,
            "Brightness": cfg["brightness"], "DisplayClock": int(cfg["display_clock"]),
            "UTC": int(cfg["utc"]), "ScreenLayout": LAYOUTS[cfg["layout"]],
            "IdleBrightness": cfg["idle_brightness"]})
        if dtype in ("nextion_driver", "nextion_driver_modem"):
            text = section_patch(text, "NextionDriver", {"Port": cfg["port"], "LogLevel": 2,
                "RemoveDim": 0, "SleepWhenInactive": 600, "ShowModesStatus": 0})
        if dtype == "nextion_driver_modem":
            text = section_patch(text, "Transparent Data", {"Enable": 1, "RemoteAddress": "127.0.0.1",
                "RemotePort": 40094, "LocalPort": 40095, "SendFrameType": 1})
    elif dtype in ("oled3", "oled6"):
        text = section_patch(text, "OLED", {"Type": 3 if dtype == "oled3" else 6,
            "Brightness": cfg["brightness"], "Invert": int(cfg["invert"]), "Scroll": int(cfg["scroll"]),
            "Rotate": int(cfg["rotate"]), "LogoScreensaver": int(cfg["screensaver"])})
    elif dtype == "tft_serial":
        text = section_patch(text, "TFT Serial", {"Port": cfg["port"], "Brightness": cfg["brightness"]})
    elif dtype == "lcdproc":
        text = section_patch(text, "LCDproc", {"Address": "localhost", "Port": 13666,
            "DimOnIdle": int(cfg["dim_on_idle"]), "DisplayClock": int(cfg["display_clock"]), "UTC": int(cfg["utc"])})
    return text


def status() -> None:
    cfg = load_state()
    print(json.dumps({"ok": True, "version": "4.00.002", "config": cfg,
        "available_ports": available_ports(),
        "nextion_layouts": ["g4klx", "on7lds_l2", "on7lds_l3", "on7lds_l3hs"],
        "mmdvmhost_active": service_active(MMDVM_SERVICE),
        "nextiondriver_active": service_active(DRIVER_SERVICE),
        "nextiondriver_enabled": service_enabled(DRIVER_SERVICE),
        "hmi_autoflash": False, "source": "Pi-Star/WPSD-compatible MMDVMHost semantics"}, ensure_ascii=False))


def apply() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        fail("invalid_json")
    if not isinstance(payload, dict):
        fail("invalid_json_object")
    cfg = normalize(payload)
    if not INI.is_file():
        fail("mmdvm_ini_missing", str(INI))
    original = INI.read_text(errors="replace")
    candidate = build_ini(original, cfg)
    if candidate == original and cfg == load_state():
        status()
        return

    mmdvm_was_active = service_active(MMDVM_SERVICE)
    driver_was_active = service_active(DRIVER_SERVICE)
    driver_was_enabled = service_enabled(DRIVER_SERVICE)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INI, BACKUP)
    driver_needed = cfg["type"] in ("nextion_driver", "nextion_driver_modem")
    try:
        if mmdvm_was_active:
            systemctl("stop", MMDVM_SERVICE)
        systemctl("stop", DRIVER_SERVICE, check=False)
        atomic_write(INI, candidate, INI.stat().st_mode & 0o777)
        if driver_needed:
            systemctl("enable", DRIVER_SERVICE)
            systemctl("start", DRIVER_SERVICE)
            if not service_active(DRIVER_SERVICE):
                raise RuntimeError("NextionDriver did not become active")
        else:
            systemctl("disable", DRIVER_SERVICE, check=False)
        if mmdvm_was_active:
            systemctl("start", MMDVM_SERVICE)
            if not service_active(MMDVM_SERVICE):
                raise RuntimeError("MMDVMHost did not become active")
        save_state(cfg)
    except Exception as exc:
        try:
            shutil.copy2(BACKUP, INI)
            systemctl("stop", DRIVER_SERVICE, check=False)
            if driver_was_enabled:
                systemctl("enable", DRIVER_SERVICE, check=False)
            else:
                systemctl("disable", DRIVER_SERVICE, check=False)
            if driver_was_active:
                systemctl("start", DRIVER_SERVICE, check=False)
            if mmdvm_was_active:
                systemctl("start", MMDVM_SERVICE, check=False)
        finally:
            fail("display_apply_rolled_back", str(exc))
    print(json.dumps({"ok": True, "applied": cfg, "hardware_validation": "PENDENTE"}, ensure_ascii=False))


def main() -> None:
    if os.geteuid() != 0 and len(sys.argv) > 1 and sys.argv[1] == "apply":
        fail("root_required")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        status()
    elif action == "apply":
        apply()
    else:
        fail("unknown_action", action)


if __name__ == "__main__":
    main()
