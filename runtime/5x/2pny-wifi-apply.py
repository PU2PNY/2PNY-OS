#!/usr/bin/env python3
"""Transactional Wi-Fi profile switch for PU2PNY-OS 5.x using NetworkManager."""
from __future__ import annotations
import argparse, json, re, subprocess, time

PREFIX = "pu2pny-wifi-"
AP_CANDIDATES = ("PU2PNY-OS", "pu2pny-os", "pu2pny")

def run(args: list[str], timeout: int = 25) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["nmcli", "--wait", "20", *args], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)

def safe_name(ssid: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "-", ssid).strip("-")[:40] or "wifi"
    return PREFIX + token

def current_active() -> str:
    cp = run(["-t", "-f", "NAME,TYPE", "connection", "show", "--active"])
    for line in cp.stdout.splitlines():
        name, sep, typ = line.rpartition(":")
        if sep and typ == "802-11-wireless" and name not in AP_CANDIDATES: return name
    return ""

def has_ipv4(iface: str) -> bool:
    cp = subprocess.run(["ip", "-4", "-o", "addr", "show", "dev", iface], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return " inet " in cp.stdout

def find_wifi_iface() -> str:
    cp = run(["-t", "-f", "DEVICE,TYPE", "device", "status"])
    for line in cp.stdout.splitlines():
        dev, sep, typ = line.rpartition(":")
        if sep and typ == "wifi": return dev
    return ""

def recover_ap() -> None:
    for name in AP_CANDIDATES:
        if run(["connection", "up", name]).returncode == 0: return

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--ssid", required=True); ap.add_argument("--password", required=True); ap.add_argument("--priority", type=int, default=100)
    ns = ap.parse_args()
    if not (1 <= len(ns.ssid.encode()) <= 32) or len(ns.password) < 8:
        print(json.dumps({"ok": False, "error": "invalid_wifi_credentials"})); return 2
    iface = find_wifi_iface()
    if not iface:
        print(json.dumps({"ok": False, "error": "wifi_interface_not_found"})); return 3
    previous = current_active(); name = safe_name(ns.ssid)
    known = run(["-t", "-f", "NAME", "connection", "show"]).stdout.splitlines()
    if name in known:
        cp = run(["connection", "modify", name, "802-11-wireless.ssid", ns.ssid, "802-11-wireless-security.key-mgmt", "wpa-psk", "802-11-wireless-security.psk", ns.password, "connection.autoconnect", "yes", "connection.autoconnect-priority", str(ns.priority)])
    else:
        cp = run(["connection", "add", "type", "wifi", "ifname", iface, "con-name", name, "ssid", ns.ssid])
        if cp.returncode == 0:
            cp = run(["connection", "modify", name, "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", ns.password, "connection.autoconnect", "yes", "connection.autoconnect-priority", str(ns.priority)])
    if cp.returncode != 0:
        print(json.dumps({"ok": False, "error": "profile_stage_failed", "detail": cp.stderr.strip()})); return 4
    cp = run(["connection", "up", name, "ifname", iface]); deadline = time.time() + 25
    while cp.returncode == 0 and time.time() < deadline:
        if has_ipv4(iface):
            print(json.dumps({"ok": True, "profile": name, "interface": iface, "ipv4": True})); return 0
        time.sleep(1)
    run(["connection", "down", name])
    if previous: run(["connection", "up", previous, "ifname", iface])
    else: recover_ap()
    print(json.dumps({"ok": False, "error": "association_or_ipv4_failed", "rolled_back": True})); return 5

if __name__ == "__main__": raise SystemExit(main())
