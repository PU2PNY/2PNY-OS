#!/usr/bin/env python3
"""Read-only Raspberry power health. Never changes supply, CPU or RF settings."""
import json
import re
import subprocess

def decode(text):
    m = re.fullmatch(r"throttled=0x([0-9a-fA-F]+)", text.strip())
    if not m:
        return {"state": "not_verified", "reason": "invalid_firmware_response"}
    value = int(m.group(1), 16)
    return {
        "state": "reported_by_firmware",
        "raw_hex": f"0x{value:x}",
        "undervoltage_now": bool(value & (1 << 0)),
        "frequency_capped_now": bool(value & (1 << 1)),
        "throttled_now": bool(value & (1 << 2)),
        "temperature_limit_now": bool(value & (1 << 3)),
        "undervoltage_since_boot": bool(value & (1 << 16)),
        "frequency_capped_since_boot": bool(value & (1 << 17)),
        "throttled_since_boot": bool(value & (1 << 18)),
        "temperature_limit_since_boot": bool(value & (1 << 19)),
    }

def snapshot():
    try:
        cp = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True,
                            text=True, timeout=3, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return {"state": "not_verified", "reason": "firmware_telemetry_unavailable"}
    return decode(cp.stdout) if cp.returncode == 0 else {
        "state": "not_verified", "reason": "firmware_command_failed"}

if __name__ == "__main__":
    print(json.dumps(snapshot(), separators=(',', ':'), sort_keys=True))
