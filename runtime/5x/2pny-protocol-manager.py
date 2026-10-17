#!/usr/bin/env python3
"""Single-owner protocol service coordinator for PU2PNY-OS 5.x.

It never rewrites RF parameters. It proves MMDVMHost healthy before switching a
network gateway, starts the requested gateway first, and only then stops others.
"""
from __future__ import annotations
import argparse, json, os, subprocess, tempfile
from pathlib import Path

STATE = Path("/var/lib/2pny/protocol/active.json")
MMDVM = "2pny-mmdvmhost.service"
MAP = {
    "dmr": ("dmrgateway.service", "2pny-dmrgateway.service"),
    "dstar": ("dstargateway.service", "2pny-dstargateway.service"),
    "ysf": ("ysfgateway.service", "2pny-ysfgateway.service"),
    "p25": ("p25gateway.service", "2pny-p25gateway.service"),
    "nxdn": ("nxdngateway.service", "2pny-nxdngateway.service"),
    "pocsag": ("dapnetgateway.service", "2pny-dapnetgateway.service"),
}

def sys(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["systemctl", *args], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)

def exists(unit: str) -> bool: return sys("cat", unit).returncode == 0

def active(unit: str) -> bool: return bool(unit) and sys("is-active", "--quiet", unit).returncode == 0

def resolve(mode: str) -> str:
    for unit in MAP[mode]:
        if exists(unit): return unit
    return ""

def atomic_state(obj: dict[str, str]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{STATE.name}.", dir=str(STATE.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, separators=(",", ":")); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp, 0o600); os.replace(tmp, STATE)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def status() -> dict:
    gateways = {}
    for mode in MAP:
        unit = resolve(mode)
        gateways[mode] = {"unit": unit or "—", "active": active(unit)}
    return {"mmdvmhost": {"unit": MMDVM, "exists": exists(MMDVM), "active": active(MMDVM)}, "gateways": gateways}

def apply(mode: str) -> int:
    if not exists(MMDVM):
        print(json.dumps({"ok": False, "error": "canonical_mmdvmhost_unit_missing"})); return 3
    if not active(MMDVM):
        cp = sys("start", MMDVM)
        if cp.returncode != 0 or not active(MMDVM):
            print(json.dumps({"ok": False, "error": "mmdvmhost_not_healthy"})); return 4
    target = resolve(mode)
    if not target:
        print(json.dumps({"ok": False, "error": "gateway_unit_missing", "mode": mode})); return 5
    before = {m: resolve(m) for m in MAP if resolve(m) and active(resolve(m))}
    cp = sys("start", target)
    if cp.returncode != 0 or not active(target):
        print(json.dumps({"ok": False, "error": "gateway_start_failed", "mode": mode, "unit": target})); return 6
    for old_mode, unit in before.items():
        if old_mode != mode and unit != target: sys("stop", unit)
    atomic_state({"mode": mode, "unit": target})
    print(json.dumps({"ok": True, "mode": mode, "unit": target})); return 0

def main() -> int:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="command", required=True); sub.add_parser("status")
    a = sub.add_parser("apply"); a.add_argument("mode", choices=sorted(MAP)); ns = p.parse_args()
    if ns.command == "status": print(json.dumps(status(), ensure_ascii=False)); return 0
    return apply(ns.mode)

if __name__ == "__main__": raise SystemExit(main())
