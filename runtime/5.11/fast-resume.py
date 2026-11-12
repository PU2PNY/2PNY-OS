#!/usr/bin/env python3
"""BOOT-057: quick resume of the last proven profile (runs before 2pny-profile-autostart and its retry; D-Star, DMR and YSF).

The original autostart regenerates every configuration, restarts MMDVMHost and the gateway and waits for
the bridge on every boot, which delayed the D-Star reflector link by tens of seconds. When the saved profile
is the one that was last running (network-radio.json state gateway_active, same protocol) and its generated
files exist, only start MMDVMHost and the gateway. Anything uncertain exits quietly and the unchanged
autostart does the full activation. It never rewrites configuration and never restarts a running unit.
"""
import json, os, subprocess, sys, time
from pathlib import Path

STATE = Path(os.environ.get('PNY_STATE', '/var/lib/2pny'))
GATEWAYS = {'DMR': '2pny-dmrgateway.service', 'DSTAR': '2pny-dstargateway.service', 'YSF': '2pny-ysfgateway.service',
            'P25': '2pny-p25gateway.service', 'NXDN': '2pny-nxdngateway.service', 'POCSAG': '2pny-dapnetgateway.service'}
FILES = {'DSTAR': 'dstar/DStarGateway.ini', 'DMR': 'dmr/DMRGateway.ini', 'YSF': 'ysf/YSFGateway.ini'}  # generated gateway file per protocol

def readj(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}

def norm(value):
    proto = str(value or '').upper().replace('-', '')
    return 'YSF' if proto == 'C4FM' else proto

def systemctl(*args, timeout=25):
    return subprocess.run(['systemctl', *args], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout).returncode

def active(unit):
    return systemctl('is-active', '--quiet', unit, timeout=10) == 0

def log(message):
    subprocess.run(['logger', '-t', 'pu2pny-fast-resume', '--', message], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def eligible():
    if not (STATE / 'provisioned').exists() or not (STATE / 'rf-configured').exists():
        return None
    proof = readj(STATE / 'last-active-profile.json')
    proto = norm(proof.get('protocol'))
    if proto not in FILES or not isinstance(proof.get('profile'), dict):
        return None
    runtime = readj(STATE / 'network-radio.json')
    if norm(runtime.get('protocol')) != proto or str(runtime.get('state') or '') not in ('gateway_active', 'active', 'ready', 'configured'):
        return None
    saved = readj(STATE / 'config.json')
    if norm(saved.get('protocol')) != proto:
        return None
    for key, field in (('server_name', 'server_name'), ('port', 'server_port')):
        runtime_value, saved_value = runtime.get(key), saved.get(field)
        if runtime_value not in (None, '', 0) and saved_value not in (None, '', 0) and str(runtime_value) != str(saved_value):
            return None
    if not (readj(STATE / 'hardware-probe.json').get('mmdvm') or {}).get('detected'):
        return None
    if not (STATE / FILES[proto]).is_file() or not (STATE / 'mmdvm' / 'MMDVM-Host.ini').is_file():
        return None
    route = subprocess.run(['ip', '-4', 'route', 'show', 'default'], check=False, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
    if route.returncode or not route.stdout.strip():
        return None
    return proto

def main():
    proto = eligible()
    if not proto:
        return 0
    gateway = GATEWAYS[proto]
    if active('2pny-mmdvmhost.service') and active(gateway):
        return 0
    started = time.monotonic()
    deadline = time.monotonic() + 45
    while not active('2pny-mmdvmhost.service'):
        if time.monotonic() >= deadline:
            log('retomada rápida cancelada após 45s: MMDVMHost não iniciou')
            return 0
        systemctl('reset-failed', '2pny-mmdvmhost.service', timeout=3)
        systemctl('start', '--no-block', '2pny-mmdvmhost.service', timeout=3)
        time.sleep(min(3, max(0, deadline-time.monotonic())))
        if not active('2pny-mmdvmhost.service'):
            result = subprocess.run(['systemctl','show','2pny-mmdvmhost.service',
                                     '-p','Result','-p','ExecMainStatus','-p','SubState'],
                                    check=False, capture_output=True, text=True, timeout=3)
            log('MMDVMHost: ' + result.stdout.strip().replace('\n', '; ')[:250])
    if not active(gateway) and systemctl('start', gateway) != 0:
        log('retomada rápida cancelada: gateway não iniciou')
        return 0
    time.sleep(2)
    ok = active('2pny-mmdvmhost.service') and active(gateway)
    log(f'retomada rápida {proto}: {"ok" if ok else "falhou"} em {time.monotonic() - started:.1f}s')
    return 0

if __name__ == '__main__':
    sys.exit(main())
