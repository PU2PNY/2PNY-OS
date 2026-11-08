#!/usr/bin/env python3
"""IDENTITY-054: change callsign and DMR ID through the existing proven apply chain.

Order: 2pny-rf-apply (rewrites MMDVM-Host.ini and restarts MMDVMHost, has its own
rollback) -> 2pny-protocol-profiles activate (regenerates gateway files from the
new MMDVMHost callsign/ID using the saved server secrets) -> config.json.
Any failure restores the previous identity.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

STATE = Path(os.environ.get('PU2PNY_STATE', '/var/lib/2pny'))
SBIN = Path(os.environ.get('PU2PNY_SBIN', '/usr/local/sbin'))
NETWORK = {'DMR', 'DSTAR', 'YSF', 'P25', 'NXDN', 'POCSAG'}

def out(ok, **fields):
    print(json.dumps(dict(ok=ok, **fields), ensure_ascii=False))
    return 0 if ok else 1

def write_json(path, data):
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=str(path.parent))
    with os.fdopen(fd, 'w') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)

def rf_apply(cfg, port, callsign, dmr_id):
    rx = str(int(cfg.get('rx_hz') or 0))
    tx = str(int(cfg.get('tx_hz') or cfg.get('rx_hz') or 0))
    repeater = str(cfg.get('use_mode')) == 'repeater'
    if not repeater:
        tx = rx
    args = [rx, tx, str(int(cfg.get('rx_offset_hz') or 0)), str(int(cfg.get('tx_offset_hz') or 0)),
            '1' if repeater else '0', port, callsign, dmr_id]
    return subprocess.run([str(SBIN / '2pny-rf-apply'), *args], text=True, capture_output=True, timeout=60)

def main():
    if len(sys.argv) != 3:
        return out(False, error='uso: 2pny-identity-apply INDICATIVO DMR_ID')
    callsign, dmr_id = sys.argv[1].strip().upper(), sys.argv[2].strip()
    if not re.fullmatch(r'[A-Z0-9/-]{3,16}', callsign):
        return out(False, error='indicativo inválido')
    if not re.fullmatch(r'[0-9]{6,9}', dmr_id):
        return out(False, error='DMR ID inválido')
    cfg_path = STATE / 'config.json'
    try:
        cfg = json.loads(cfg_path.read_text())
    except (OSError, ValueError):
        return out(False, error='configuração atual ausente; conclua o assistente primeiro')
    old_call, old_id = str(cfg.get('callsign') or ''), str(cfg.get('dmr_id') or '')
    if (old_call, old_id) == (callsign, dmr_id):
        return out(True, changed=False, message='Nada mudou; nenhum serviço foi reiniciado.')
    try:
        hardware = json.loads((STATE / 'hardware-probe.json').read_text())
        port = str((hardware.get('mmdvm') or {}).get('port') or '')
    except (OSError, ValueError):
        port = ''
    if not port.startswith('/dev/'):
        return out(False, error='MMDVM não detectada; identidade não alterada')
    backup = STATE / 'backups' / 'identity'
    backup.mkdir(parents=True, exist_ok=True)
    write_json(backup / 'config.json.last', cfg)
    result = rf_apply(cfg, port, callsign, dmr_id)
    if result.returncode:
        return out(False, error=(result.stderr or result.stdout or 'falha ao aplicar RF').strip())
    proto = str(cfg.get('protocol') or '').upper()
    if proto in NETWORK:
        net = subprocess.run([str(SBIN / '2pny-protocol-profiles'), 'activate', proto], text=True, capture_output=True, timeout=90)
        if net.returncode:
            rf_apply(cfg, port, old_call, old_id)  # restore previous identity in MMDVM-Host.ini
            return out(False, rolled_back=True, error=(net.stderr or net.stdout or 'falha ao aplicar a rede').strip())
        try:  # activate rewrote config.json (network_state); re-read before changing identity
            cfg = json.loads(cfg_path.read_text())
        except (OSError, ValueError):
            pass
    cfg['callsign'], cfg['dmr_id'] = callsign, dmr_id
    write_json(cfg_path, cfg)
    return out(True, changed=True, callsign=callsign, dmr_id=dmr_id)

if __name__ == '__main__':
    raise SystemExit(main())
