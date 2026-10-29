#!/usr/bin/env python3
"""Explicit software reset of the MMDVM process; never erases configuration."""
import json
import os
import subprocess
from pathlib import Path

BASE = Path('/run/2pny')
REQUEST = BASE/'reset-mmdvm-request.json'
RESULT = BASE/'reset-mmdvm-result.json'

def main():
    try:
        request = json.loads(REQUEST.read_text())
        REQUEST.unlink()
        if request != {'action': 'reset-mmdvm'}:
            raise ValueError('invalid_action')
        live = json.loads((BASE/'live-state.json').read_text())
        if live.get('active') or live.get('standby') is not True:
            raise ValueError('radio_busy_wait_for_standby')
        subprocess.run(['systemctl', 'try-restart', '2pny-mmdvmhost.service'], check=True, timeout=12)
        subprocess.run(['systemctl', 'is-active', '--quiet', '2pny-mmdvmhost.service'], check=True, timeout=3)
        result = {'ok': True, 'state': 'software_restarted', 'hw': 'not_verified', 'configuration': 'preserved'}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {'ok': False, 'error': str(exc)[:180]}
    tmp = RESULT.with_suffix('.tmp')
    tmp.write_text(json.dumps(result)+'\n')
    os.chmod(tmp, 0o644)
    tmp.replace(RESULT)

if __name__ == '__main__':
    main()
