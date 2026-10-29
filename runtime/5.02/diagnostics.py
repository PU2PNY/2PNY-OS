#!/usr/bin/env python3
"""Bounded, read-only diagnostic export. Never opens modem UART or secret files."""
import configparser
import json
import re
import subprocess
from pathlib import Path

LIMIT = 262144
SECRET = re.compile(r'(?i)(password|passwd|passphrase|psk|token|secret|authkey|api.?key|authorization|cookie|private.?key)')
ASSIGNMENT = re.compile(r'(?im)([\w.-]*(?:password|passwd|passphrase|psk|token|secret|authkey|api.?key|authorization|cookie)[\w.-]*\s*[=:]\s*)([^\r\n]*)')

def scrub(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if SECRET.search(str(k)) else scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, str):
        return '\n'.join('[REDACTED_LINE]' if SECRET.search(line) else line for line in value.split('\n'))
    return value

def read(path, kind='text'):
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(LIMIT + 1)
        if len(raw) > LIMIT:
            return {'state': 'unavailable', 'reason': 'size_limit'}
        text = raw.decode('utf-8', errors='replace').replace('\x00', '')
        if kind == 'json':
            text = json.loads(text)
        elif kind == 'ini':
            cp = configparser.ConfigParser(interpolation=None, strict=False)
            cp.optionxform = str
            cp.read_string(text)
            text = {section: dict(cp[section]) for section in cp.sections()}
        return {'state': 'available', 'data': scrub(text)}
    except (OSError, ValueError, configparser.Error) as exc:
        return {'state': 'unavailable', 'reason': type(exc).__name__}

def command(args, seconds=3):
    # Temporary files bound process memory even if the journal is unexpectedly large.
    import tempfile
    with tempfile.TemporaryFile() as out:
        try:
            cp = subprocess.run(args, stdout=out, stderr=subprocess.DEVNULL, timeout=seconds, check=False)
            out.seek(0)
            raw = out.read(LIMIT + 1)
            return {'state': 'available' if cp.returncode == 0 else 'unavailable',
                    'exit_code': cp.returncode, 'truncated': len(raw) > LIMIT,
                    'data': scrub(raw[:LIMIT].decode(errors='replace'))}
        except (OSError, subprocess.SubprocessError) as exc:
            return {'state': 'unavailable', 'reason': type(exc).__name__}

def snapshot():
    import datetime
    report = {'schema': 1, 'version': '5.02', 'generated': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'validation': 'snapshot_only_not_RF_or_HW_test', 'limits': {'file_bytes': LIMIT, 'journal_lines_per_unit': 200}}
    report['raspberry'] = {p: read(p) for p in (
        '/proc/device-tree/model', '/proc/cpuinfo', '/proc/meminfo', '/proc/loadavg', '/proc/uptime',
        '/proc/version', '/etc/os-release', '/sys/class/thermal/thermal_zone0/temp',
        '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq',
        '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')}
    # CPU serial is an identifier, never a credential. No Wi-Fi connection files or secret directory.
    report['runtime'] = {name: read('/var/lib/2pny/'+name+'.json', 'json') for name in (
        'config', 'hardware', 'hardware-probe', 'rf-apply-state', 'display-settings', 'display-runtime')}
    report['mmdvm'] = read('/var/lib/2pny/mmdvm/MMDVM-Host.ini', 'ini')
    report['network'] = command(['ip', '-j', 'address'])
    report['filesystem'] = command(['df', '-h'])
    report['power'] = command(['vcgencmd', 'get_throttled'])
    report['services'] = {}
    report['logs'] = {}
    units = ('2pny-mmdvmhost', '2pny-dmrgateway', '2pny-dstargateway', '2pny-ysfgateway',
             '2pny-p25gateway', '2pny-nxdngateway', '2pny-dapnetgateway', '2pny-display',
             '2pny-nextiondriver', '2pny-display-adapter', '2pnyd')
    # One systemctl/journal process each, rather than one child per protocol.
    report['services'] = command(['systemctl', 'show', *[u+'.service' for u in units],
        '--property=Id,LoadState,ActiveState,SubState,Result,NRestarts,ExecMainStatus,MemoryCurrent,CPUUsageNSec'])
    args = ['journalctl', '--no-pager', '-b', '-n', '1000', '-o', 'short-iso']
    for unit in units:
        args += ['-u', unit+'.service']
    report['logs'] = command(args, 5)
    report['kernel_warnings'] = command(['journalctl', '--no-pager', '-k', '-b', '-p', 'warning', '-n', '160'], 4)
    return scrub(report)

if __name__ == '__main__':
    print(json.dumps(snapshot(), ensure_ascii=False, separators=(',', ':')))
