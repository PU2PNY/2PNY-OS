#!/usr/bin/env python3
"""ARMv6-5122: defer expensive background jobs while Pi Zero is booting or busy.

Used by systemd ExecCondition on automatic maintenance and hostfile updates.
Return 1 means *skipped*, not failed. RF, network, panel and user-requested
operations are not changed. A later systemd timer may retry during idle.
"""
import os
from pathlib import Path

def measured(path, fallback=None):
    try:
        value = Path(path).read_text(errors='replace').strip()
        return value or fallback
    except OSError:
        return fallback

def is_pi_zero(model, cpu_count, machine):
    return cpu_count == 1 and (
        "Raspberry Pi Zero" in (model or "") or machine in ("armv6l", "armv6")
    )

def should_run(model, cpu_count, machine, uptime, load1, min_uptime=1800, max_load=1.0):
    if not is_pi_zero(model, cpu_count, machine):
        return True
    return uptime >= min_uptime and load1 <= max_load

def main():
    import platform
    model=measured("/proc/device-tree/model", "").replace("\x00", "")
    try:
        with open("/proc/uptime", encoding="ascii") as file:
            uptime=float(file.read().split()[0])
        load1=os.getloadavg()[0]
    except (OSError, ValueError, IndexError):
        return 1
    allow=should_run(model, os.cpu_count() or 1, platform.machine(), uptime, load1)
    return 0 if allow else 1

if __name__=="__main__":
    raise SystemExit(main())
