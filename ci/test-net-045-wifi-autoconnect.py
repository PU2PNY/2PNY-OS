#!/usr/bin/env python3
"""NET-045 regression: saved Wi-Fi profiles retry autoconnect forever.

Uses a stub nmcli/ip, so it runs anywhere. SW-level only: it proves which
nmcli calls are made, not that a real Pi Zero reconnects (HW).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / 'runtime/5x/2pny-wifi-apply.py'
RECONCILE = ROOT / 'runtime/5x/2pny-wifi-retry-reconcile.py'

STUB_NMCLI = r'''#!/usr/bin/env python3
import json, os, sys
state_path = os.environ["NM_STATE"]
state = json.load(open(state_path))
args = sys.argv[1:]
if args[:2] == ["--wait", args[1]]:
    args = args[2:]
state["calls"].append(args)
out = ""
rc = 0
if args[:4] == ["-t", "-f", "DEVICE,TYPE", "device"]:
    out = "wlan0:wifi\n"
elif args[:4] == ["-t", "-f", "NAME,TYPE", "connection"] and "--active" in args:
    out = ""
elif args[:4] == ["-t", "-f", "NAME,TYPE", "connection"]:
    out = "".join(f"{n}:{c['type']}\n" for n, c in state["profiles"].items())
elif args[:3] == ["-t", "-f", "NAME"]:
    out = "".join(f"{n}\n" for n in state["profiles"])
elif args[:2] == ["-g", "connection.autoconnect-retries"]:
    out = str(state["profiles"][args[-1]].get("retries", -1)) + "\n"
elif args[:2] == ["connection", "modify"]:
    prof = state["profiles"].setdefault(args[2], {"type": "802-11-wireless"})
    for key, value in zip(args[3::2], args[4::2]):
        if key == "connection.autoconnect-retries":
            prof["retries"] = int(value)
elif args[:2] == ["connection", "add"]:
    name = args[args.index("con-name") + 1]
    state["profiles"][name] = {"type": "802-11-wireless", "retries": -1}
json.dump(state, open(state_path, "w"))
sys.stdout.write(out)
sys.exit(rc)
'''
STUB_IP = '#!/bin/sh\necho "2: wlan0    inet 192.0.2.10/24 scope global wlan0"\n'


def sandbox(profiles):
    td = tempfile.TemporaryDirectory(prefix='pu2pny-net045-')
    base = Path(td.name)
    bindir = base / 'bin'
    bindir.mkdir()
    (bindir / 'nmcli').write_text(STUB_NMCLI)
    (bindir / 'ip').write_text(STUB_IP)
    for item in bindir.iterdir():
        item.chmod(0o755)
    state = base / 'state.json'
    state.write_text(json.dumps({'calls': [], 'profiles': profiles}))
    env = os.environ.copy()
    env['PATH'] = str(bindir) + os.pathsep + env['PATH']
    env['NM_STATE'] = str(state)
    return td, state, env


def run(script, env, *args):
    cp = subprocess.run([sys.executable, '-I', str(script), *args], env=env, text=True,
                        capture_output=True)
    assert cp.returncode == 0, cp.stderr
    return cp.stdout


def modifies(state):
    return [c for c in json.loads(state.read_text())['calls'] if c[:2] == ['connection', 'modify']]


# 1. New and updated profiles are written with retries=0 and the rest unchanged.
for existing in ({}, {'pu2pny-wifi-Casa': {'type': '802-11-wireless', 'retries': -1}}):
    td, state, env = sandbox(existing)
    with td:
        out = json.loads(run(APPLY, env, '--ssid', 'Casa', '--password', 'senha-forte-123'))
        assert out['ok'] is True, out
        mods = modifies(state)
        assert mods, 'profile was not written'
        for call in mods:
            assert 'connection.autoconnect-retries' in call and call[call.index('connection.autoconnect-retries') + 1] == '0', call
            assert 'connection.autoconnect' in call and call[call.index('connection.autoconnect') + 1] == 'yes'
            assert 'connection.autoconnect-priority' in call

# 2. Reconcile repairs only old PU2PNY Wi-Fi profiles, only when needed.
profiles = {
    'pu2pny-wifi-Casa': {'type': '802-11-wireless', 'retries': -1},
    'pu2pny-wifi-Sitio': {'type': '802-11-wireless', 'retries': 0},
    'PU2PNY-OS': {'type': '802-11-wireless', 'retries': -1},       # setup AP: never touched
    'Wired connection 1': {'type': '802-3-ethernet', 'retries': -1},
    'outro-wifi': {'type': '802-11-wireless', 'retries': -1},      # not ours: never touched
}
td, state, env = sandbox(profiles)
with td:
    first = json.loads(run(RECONCILE, env))
    assert first == {'ok': True, 'changed': ['pu2pny-wifi-Casa'], 'failed': []}, first
    assert [m[2] for m in modifies(state)] == ['pu2pny-wifi-Casa']
    final = json.loads(state.read_text())['profiles']
    assert final['pu2pny-wifi-Casa']['retries'] == 0
    for untouched in ('PU2PNY-OS', 'Wired connection 1', 'outro-wifi'):
        assert final[untouched]['retries'] == -1, untouched
    # 3. Idempotent: a second boot performs zero writes.
    before = len(modifies(state))
    second = json.loads(run(RECONCILE, env))
    assert second == {'ok': True, 'changed': [], 'failed': []}, second
    assert len(modifies(state)) == before

print('TEST_NET_045_WIFI_AUTOCONNECT_OK')
