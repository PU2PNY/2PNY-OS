#!/usr/bin/env python3
"""NET-045: saved PU2PNY Wi-Fi profiles must retry autoconnect indefinitely.

NetworkManager stops auto-activating a profile after a few failed attempts
(connection.autoconnect-retries = -1 means "use the global default"). On a slow
Raspberry Pi Zero the Wi-Fi chip can come up after those attempts are spent, and
the hotspot then stays offline until someone intervenes. Profiles written by
the updated 2pny-wifi-apply already carry retries=0; this one-shot repairs
profiles saved by earlier versions. It only touches profiles named pu2pny-wifi-*, only
when the value differs (no needless SD writes), and never touches RF settings,
the setup access point or other connections.
"""
import json
import subprocess

PREFIX = "pu2pny-wifi-"


def nm(*args, timeout=20):
    return subprocess.run(["nmcli", "--wait", "10", *args], text=True, check=False,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def main():
    listing = nm("-t", "-f", "NAME,TYPE", "connection", "show")
    if listing.returncode != 0:
        print(json.dumps({"ok": False, "error": "nmcli_unavailable"}))
        return 0
    changed, failed = [], []
    for line in listing.stdout.splitlines():
        name, sep, kind = line.rpartition(":")
        if not sep or kind != "802-11-wireless" or not name.startswith(PREFIX):
            continue
        current = nm("-g", "connection.autoconnect-retries", "connection", "show", name).stdout.split()
        if current and current[0] == "0":
            continue
        result = nm("connection", "modify", name, "connection.autoconnect-retries", "0")
        (changed if result.returncode == 0 else failed).append(name)
    print(json.dumps({"ok": not failed, "changed": changed, "failed": failed}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
