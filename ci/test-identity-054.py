#!/usr/bin/env python3
"""IDENTITY-054: identity change order, validation and rollback with stub apply tools (SW level)."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'runtime/5.04/identity-apply.py'

def setup(td, fail_rf=False, fail_net=False):
    td = Path(td); state = td / 'state'; sbin = td / 'sbin'; state.mkdir(); sbin.mkdir()
    (state / 'config.json').write_text(json.dumps({'callsign': 'PU2OLD', 'dmr_id': '7240001', 'protocol': 'DMR', 'rx_hz': 438000000,
                                                    'tx_hz': 438000000, 'use_mode': 'hotspot', 'network_state': 'up'}))
    (state / 'hardware-probe.json').write_text(json.dumps({'mmdvm': {'detected': True, 'port': '/dev/serial0'}}))
    log = td / 'calls.log'
    (sbin / '2pny-rf-apply').write_text('#!/bin/sh\necho "rf $*" >> %s\n%s' % (log, 'echo boom >&2; exit 5\n' if fail_rf else 'exit 0\n'))
    (sbin / '2pny-protocol-profiles').write_text('#!/bin/sh\necho "net $*" >> %s\n%s' % (log, 'echo netboom >&2; exit 6\n' if fail_net else 'exit 0\n'))
    for f in sbin.iterdir(): f.chmod(0o755)
    return state, sbin, log

def run(state, sbin, *args):
    env = dict(os.environ, PU2PNY_STATE=str(state), PU2PNY_SBIN=str(sbin))
    cp = subprocess.run([sys.executable, '-I', str(SCRIPT), *args], env=env, capture_output=True, text=True)
    return cp.returncode, json.loads(cp.stdout)

with tempfile.TemporaryDirectory() as td:  # success
    state, sbin, log = setup(td)
    rc, res = run(state, sbin, 'pu2new', '7249999')
    assert rc == 0 and res['changed'] and res['callsign'] == 'PU2NEW', res
    cfg = json.loads((state / 'config.json').read_text())
    assert cfg['callsign'] == 'PU2NEW' and cfg['dmr_id'] == '7249999' and cfg['network_state'] == 'up'
    calls = log.read_text().splitlines()
    assert calls == ['rf 438000000 438000000 0 0 0 /dev/serial0 PU2NEW 7249999', 'net activate DMR'], calls
    rc, res = run(state, sbin, 'PU2NEW', '7249999')   # unchanged: nothing restarted
    assert rc == 0 and res['changed'] is False and len(log.read_text().splitlines()) == 2

with tempfile.TemporaryDirectory() as td:  # invalid input never reaches the tools
    state, sbin, log = setup(td)
    for call, ident in (('AB', '7240001'), ('PU2 NEW', '7240001'), ('PU2NEW;id', '7240001'), ('PU2NEW', '12345'), ('PU2NEW', '1234567890'), ('PU2NEW', '72a0001')):
        rc, res = run(state, sbin, call, ident)
        assert rc == 1 and not res['ok'], (call, ident, res)
    assert not log.exists()

with tempfile.TemporaryDirectory() as td:  # RF failure leaves config untouched
    state, sbin, log = setup(td, fail_rf=True)
    rc, res = run(state, sbin, 'PU2NEW', '7249999')
    assert rc == 1 and 'boom' in res['error']
    assert json.loads((state / 'config.json').read_text())['callsign'] == 'PU2OLD'
    assert log.read_text().splitlines() == ['rf 438000000 438000000 0 0 0 /dev/serial0 PU2NEW 7249999']

with tempfile.TemporaryDirectory() as td:  # network failure restores the old identity
    state, sbin, log = setup(td, fail_net=True)
    rc, res = run(state, sbin, 'PU2NEW', '7249999')
    assert rc == 1 and res['rolled_back'] and 'netboom' in res['error']
    assert json.loads((state / 'config.json').read_text())['callsign'] == 'PU2OLD'
    assert log.read_text().splitlines()[-1] == 'rf 438000000 438000000 0 0 0 /dev/serial0 PU2OLD 7240001'

with tempfile.TemporaryDirectory() as td:  # no modem, no config
    state, sbin, log = setup(td)
    (state / 'hardware-probe.json').write_text('{}')
    assert run(state, sbin, 'PU2NEW', '7249999')[0] == 1 and not log.exists()
    (state / 'config.json').unlink()
    assert run(state, sbin, 'PU2NEW', '7249999')[0] == 1
print('TEST_IDENTITY_054_OK')
