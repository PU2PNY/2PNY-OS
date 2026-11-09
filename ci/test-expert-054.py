#!/usr/bin/env python3
"""EXPERT-054: allowlist, redaction and size limit of the Expert diagnostic commands (SW level)."""
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import sys as _sys
VERSION = _sys.argv[1] if len(_sys.argv) > 1 else '5.04'
spec = importlib.util.spec_from_file_location('expert_cmd', ROOT / f'runtime/{VERSION}/expert-cmd.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

# Only fixed read-only programs may ever run.
allowed = {'cat', 'uname', 'systemd-analyze', 'systemctl', 'journalctl', 'nmcli', 'sh', 'ls', 'timedatectl'}
for key, (label, items) in m.COMMANDS.items():
    for argv in items:
        assert argv[0] in allowed | {'sh'}, (key, argv)
        if argv[0] == 'sh':
            assert argv[1] == '-c' and not any(w in argv[2] for w in ('rm ', '>', 'reboot', 'dd ', 'chmod', 'mv ')), argv
assert m.run('rm -rf /') == {'ok': False, 'error': 'unknown_command'}
assert m.run('') == {'ok': False, 'error': 'unknown_command'}
assert m.run('version; id')['ok'] is False

# Secrets are masked in JSON and key=value forms.
sample = '{"server_password": "abc123", "psk": "wifipass", "name": "ok"}\nPassword=hunter2\nAuthKey: xyz\nIP=10.0.0.2'
red = m.redact(sample)
for secret in ('abc123', 'wifipass', 'hunter2', 'xyz'):
    assert secret not in red, red
assert '"name": "ok"' in red and 'IP=10.0.0.2' in red

# A very long line must not stall the redaction (regex backtracking).
import time as _t
t0=_t.time(); m.redact('k'*500000+' psk=abc\n'+'x'*500000); assert _t.time()-t0 < 3

# Output limit and unavailable programs.
real_run_one = m.run_one
calls = []
m.run_one = lambda argv: calls.append(argv) or (('x' * 100 + '\n') * 1000)
out = m.run('failed')
assert out['ok'] and len(out['output']) < m.LIMIT + 100 and '[cortado]' in out['output']
assert 'comando não disponível' in real_run_one(['definitely-not-installed-054'])
m.run_one = lambda argv: ('y' * 100 + '\n') * 1000
assert len(m.run('all')['output']) <= m.LIMIT + 100
print('TEST_EXPERT_054_OK')
