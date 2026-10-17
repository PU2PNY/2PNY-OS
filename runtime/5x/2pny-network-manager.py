#!/usr/bin/env python3
"""Event-driven PU2PNY-OS 5.x network state publisher."""
from __future__ import annotations
import json, os, re, socket, subprocess, tempfile, time
from pathlib import Path
from typing import Any

OUT = Path(os.environ.get("PU2PNY_NETWORK_OUT", "/run/pu2pny/network.json"))
EVENT = Path(os.environ.get("PU2PNY_EVENT_SOCK", "/run/pu2pny/event.sock"))

def cmd(argv: list[str], timeout: float = 3.0) -> str:
    try:
        cp = subprocess.run(argv, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout)
        return cp.stdout.strip()
    except (OSError, subprocess.TimeoutExpired): return ""

def ipv4(iface: str) -> str:
    m = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)/", cmd(["ip", "-4", "-o", "addr", "show", "dev", iface]))
    return m.group(1) if m else "—"

def oper(iface: str) -> str:
    try: return Path(f"/sys/class/net/{iface}/operstate").read_text().strip()
    except OSError: return "unknown"

def wifi(iface: str) -> dict[str, Any]:
    text = cmd(["iw", "dev", iface, "link"]); ssid = "—"; dbm = None
    m = re.search(r"^\s*SSID:\s*(.+)$", text, re.M)
    if m: ssid = m.group(1).strip()
    m = re.search(r"signal:\s*(-?\d+(?:\.\d+)?)\s*dBm", text)
    if m: dbm = float(m.group(1))
    pct = max(0, min(100, round(2 * (dbm + 100)))) if dbm is not None else None
    return {"connected": "Not connected" not in text and ssid != "—", "ssid": ssid, "signal_dbm": dbm, "signal_pct": pct, "ipv4": ipv4(iface), "operstate": oper(iface)}

def ethernet(iface: str) -> dict[str, Any]:
    carrier = None
    try: carrier = Path(f"/sys/class/net/{iface}/carrier").read_text().strip() == "1"
    except OSError: pass
    ip = ipv4(iface)
    return {"connected": carrier is True and ip != "—", "carrier": carrier, "ipv4": ip, "operstate": oper(iface)}

def snapshot() -> dict[str, Any]:
    ifaces = [p.name for p in Path("/sys/class/net").glob("*") if p.name != "lo"]
    wlan = next((x for x in ifaces if x.startswith(("wl", "wlan"))), None)
    eths = [x for x in ifaces if x.startswith(("eth", "en"))]
    routes = cmd(["ip", "-4", "route", "show", "default"]).splitlines()
    return {"schema": 1, "version": "5.00.000", "updated": time.time(),
            "wifi": wifi(wlan) if wlan else {"connected": False, "ssid": "—", "signal_dbm": None, "signal_pct": None, "ipv4": "—", "operstate": "absent"},
            "ethernet": {x: ethernet(x) for x in eths}, "default_route": routes[0] if routes else "—"}

def atomic(obj: dict[str, Any]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{OUT.name}.", dir=str(OUT.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, sort_keys=True, separators=(",", ":")); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp, 0o644); os.replace(tmp, OUT)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def publish(obj: dict[str, Any]) -> None:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        s.sendto(json.dumps({"topic": "network", "data": obj}, separators=(",", ":")).encode(), str(EVENT)); s.close()
    except OSError: pass

def update() -> None:
    obj = snapshot(); atomic(obj); publish(obj)

def main() -> int:
    update()
    while True:
        try:
            p = subprocess.Popen(["ip", "monitor", "link", "address", "route"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if p.stdout is None: raise OSError("ip monitor stdout unavailable")
            for _line in p.stdout:
                time.sleep(0.15); update()
            p.wait()
        except KeyboardInterrupt: return 0
        except OSError: time.sleep(2)

if __name__ == "__main__": raise SystemExit(main())
