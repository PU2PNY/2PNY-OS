#!/usr/bin/env python3
"""EXPERT-054/055/056/057: fixed, read-only diagnostic commands for the Expert page.

Only identifiers from COMMANDS can run; the web request never supplies a
command line. Output is size-limited and secrets are redacted.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

LIMIT = 24000
UNITS = ('2pny-profile-autostart', '2pny-profile-autostart-retry', 'display-reconcile',
         'NetworkManager', '2pny-display-core', '2pny-mmdvmhost', '2pnyd')

def journal(*units, lines='200'):
    args = ['journalctl', '-b', '--no-pager', '-n', lines]
    for unit in units:
        args += ['-u', unit]
    return args

COMMANDS = {
    'version': ('Versão e placa', [['cat', '/etc/2pny/version'], ['cat', '/proc/device-tree/model'], ['uname', '-a'],
                                     ['cat', '/etc/os-release']]),
    'boot': ('Tempo de boot', [['systemd-analyze'], ['systemctl', 'list-jobs', '--no-pager'], ['systemd-analyze', 'blame'],
                               ['systemd-analyze', 'critical-chain'],
                               ['sh', '-c', 'cat /proc/uptime; for u in NetworkManager 2pny-network-core hostapd dnsmasq avahi-daemon 2pnyd 2pny-mmdvmhost 2pny-dmrgateway 2pny-display-core userconfig; do printf "%s " "$u"; systemctl show -p ActiveEnterTimestampMonotonic --value "$u.service"; done']]),
    'load': ('Carga e processos', [['sh', '-c', 'cat /proc/loadavg; nproc; ps -eo pid,pcpu,pmem,etime,args --sort=-pcpu | head -15'],
                                   ['systemctl', 'list-timers', '--no-pager']]),
    'apply': ('Última aplicação de rádio', [['sh', '-c', 'cat /var/lib/2pny/last-rf-apply-error.json /var/lib/2pny/rf-bootstrap.json /var/lib/2pny/network-radio.json'],
                                            journal('2pnyd', lines='80')]),
    'failed': ('Serviços com falha', [['systemctl', 'list-units', '--failed', '--no-pager']]),
    'services': ('Estado dos serviços', [['systemctl', 'is-active', *[u + '.service' for u in UNITS]]]),
    'profile': ('Perfil salvo e log de restauração', [['cat', '/var/lib/2pny/last-active-profile.json'],
                                                       journal('2pny-profile-autostart', '2pny-profile-autostart-retry', 'display-reconcile')]),
    'wifi': ('Wi-Fi e rede', [['nmcli', 'device', 'status'],
                              ['nmcli', '-f', 'NAME,TYPE,AUTOCONNECT,AUTOCONNECT-PRIORITY,ACTIVE,DEVICE', 'connection', 'show'],
                              ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,IN-USE', 'device', 'wifi', 'list', '--rescan', 'no'],
                              ['sh', '-c', 'for i in /sys/class/net/wlan*; do iw dev $(basename $i) link; done | head -20'],
                              ['nmcli', 'general', 'logging'],
                              journal('NetworkManager', lines='120'),
                              ['journalctl', '-b', '--no-pager', '-n', '80', '_COMM=NetworkManager']]),
    'display': ('Telas (OLED, LCD, Nextion)', [['cat', '/var/lib/2pny/hardware-probe.json'], ['sh', '-c', 'ls -l /dev/i2c-* /dev/serial* /dev/ttyAMA* /dev/ttyS*'],
                                               ['sh', '-c', 'grep -i -E "i2c|spi|uart" /boot/firmware/config.txt /boot/config.txt; lsmod | grep -i -E "i2c|spi"; ls /dev/i2c-*; cat /etc/modules-load.d/2pny-i2c.conf'],
                                               ['cat', '/var/lib/2pny/oled.json'], ['cat', '/var/lib/2pny/display-settings.json'], ['cat', '/run/2pny/display-status.json'],
                                               journal('2pny-display-core', lines='80')]),
    'clock': ('Relógio e fuso', [['timedatectl', 'status'], ['sh', '-c', 'ls -l /etc/localtime; cat /etc/timezone; cat /var/lib/2pny/settings/clock.json'],
                                 ['systemctl', 'is-active', '2pny-timezone-apply.path', '2pny-timezone-restore.service', 'systemd-timesyncd', 'fake-hwclock'],
                                 journal('2pny-timezone-apply', '2pny-timezone-restore', 'systemd-timedated', 'systemd-timesyncd', lines='60')]),
    'voice': ('Voz e hora cheia', [['sh', '-c', 'cat /var/lib/2pny/voice-settings.json; ls -l /var/lib/2pny/voice-hourly.enabled'],
                                   ['systemctl', 'list-timers', '2pny-hourly-voice.timer', '--no-pager'],
                                   ['journalctl', '-b', '--no-pager', '-n', '40', '-t', 'pu2pny-hourly-voice', '-t', 'pu2pny-fast-resume']]),
    'errors': ('Avisos e erros do sistema', [['journalctl', '-b', '--no-pager', '-n', '120', '-p', 'warning']]),
    'power': ('Temperatura e alimentação', [['sh', '-c', 'vcgencmd measure_temp; vcgencmd get_throttled; cat /proc/loadavg; free -m'] ]),
}

SECRET = re.compile(r'(?i)((?:password|passwd|secret|psk|token|authkey|api[_-]?key|key)"?[ \t]*[:=][ \t]*)("[^"]*"|[^\s,]+)')

def redact(text):
    """Line by line with a length cap, so a huge line can never stall the regex."""
    return '\n'.join(SECRET.sub(lambda m: m.group(1) + '***', line[:2000]) for line in text.split('\n'))

def run_one(argv):
    try:
        cp = subprocess.run(argv, check=False, text=True, errors='replace', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)
        return '$ ' + ' '.join(argv) + '\n' + cp.stdout.rstrip() + '\n'
    except FileNotFoundError:
        return '$ ' + ' '.join(argv) + '\n(comando não disponível)\n'
    except subprocess.TimeoutExpired:
        return '$ ' + ' '.join(argv) + '\n(tempo esgotado)\n'

def run(identifier):
    if identifier == 'all':
        chunks = [run(key)['output'] for key in COMMANDS]
        out = '\n'.join(chunks)
    elif identifier in COMMANDS:
        label, items = COMMANDS[identifier]
        out = '===== ' + label + ' =====\n' + '\n'.join(run_one(list(argv)) for argv in items)
    else:
        return {'ok': False, 'error': 'unknown_command'}
    out = redact(out)
    if len(out) > LIMIT:
        out = out[:LIMIT // 2] + '\n...[cortado]...\n' + out[-LIMIT // 2:]
    return {'ok': True, 'id': identifier, 'generated': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'output': out}

def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'list':
        items = [{'id': key, 'label': value[0]} for key, value in COMMANDS.items()]
        print(json.dumps({'ok': True, 'commands': items + [{'id': 'all', 'label': 'Relatório completo'}]}))
        return 0
    if len(sys.argv) != 2:
        print(json.dumps({'ok': False, 'error': 'usage'}))
        return 2
    result = run(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
