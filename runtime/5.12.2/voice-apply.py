#!/usr/bin/env python3
"""VOICE-511: aplicar voz aos INIs existentes, com rollback e segredo preservado."""
import argparse
import configparser
import fcntl
import json
import os
import grp
import stat
import subprocess
import tempfile
from pathlib import Path

FILES = {'dmr': 'dmr/DMRGateway.ini', 'dstar': 'dstar/DStarGateway.ini',
         'p25': 'p25/P25Gateway.ini', 'nxdn': 'nxdn/NXDNGateway.ini'}
UNITS = {p: '2pny-' + ('dmrgateway' if p == 'dmr' else p + 'gateway') + '.service' for p in FILES}


def atomic(path, data, mode=0o600, gateway_ini=False):
    """VOICE-5122: private state remains 0600, gateway INIs must be readable by mmdvm."""
    if path.is_symlink():
        raise ValueError('recusando INI por symlink')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            if gateway_ini:
                os.fchown(out.fileno(), 0, grp.getgrnam('mmdvm').gr_gid)
                os.fchmod(out.fileno(), 0o640)
            else:
                os.fchmod(out.fileno(), mode)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def ensure_gateway_access(path):
    """Repair a 5.11 INI left root:root 0600 even when its content is unchanged."""
    if path.is_symlink():
        raise ValueError('recusando INI por symlink')
    st = path.stat()
    if not stat.S_ISREG(st.st_mode):
        raise ValueError('configuração não é arquivo regular')
    gid = grp.getgrnam('mmdvm').gr_gid
    # The generator owns these INIs as root:mmdvm. Never make secrets world-readable.
    if st.st_uid != 0 or st.st_gid != gid:
        os.chown(path, 0, gid)
    if stat.S_IMODE(st.st_mode) != 0o640:
        os.chmod(path, 0o640)
    # Only repair traversal, never broaden directory permission to world-accessible.
    for parent in (path.parent.parent, path.parent):
        if parent.is_symlink():
            raise ValueError('diretório de configuração inesperado')
        ps = parent.stat()
        if ps.st_gid != gid and not (ps.st_mode & stat.S_IXOTH):
            os.chown(parent, 0, gid)
        if not (ps.st_mode & stat.S_IXGRP) and not (ps.st_mode & stat.S_IXOTH):
            os.chmod(parent, stat.S_IMODE(ps.st_mode) | stat.S_IXGRP)


def edited(raw, proto, settings):
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    cp.read_string(raw.decode())
    if proto in settings:
        enabled = settings[proto] is not False
    elif proto == 'dmr':
        enabled = settings.get('enabled', cp.get('Voice','Enabled',fallback='1') == '1') is not False
    elif proto == 'dstar':
        enabled = cp.get('Paths','Data',fallback='') != '/usr/share/2pny/audio/dstar-off/'
    else:
        enabled = cp.get('Voice','Enabled',fallback='0') == '1'
    section = 'Paths' if proto == 'dstar' else 'Voice'
    if not cp.has_section(section):
        raise ValueError('seção de voz ausente: ' + proto)
    # Alterar apenas a chave, conservando todos os demais bytes/comentários do INI.
    import re
    values = {'Data': '/usr/local/share/dstargateway.d/' if enabled else '/usr/share/2pny/audio/dstar-off/'} if proto == 'dstar' else {'Enabled': str(int(enabled))}
    if proto == 'dmr':
        values['Language'] = {'pt': 'Portugues', 'en': 'English_UK', 'es': 'Espanol'}[settings.get('language', 'pt')]
    text = raw.decode()
    match = re.search(r'(?ms)^\[' + section + r'\][^\n]*\n(?P<body>.*?)(?=^\[|\Z)', text)
    if not match:
        raise ValueError('seção ambígua')
    body = match['body']
    for key, value in values.items():
        pattern = r'(?mi)^(' + key + r'\s*=)[^\r\n]*'
        if len(re.findall(pattern, body)) != 1:
            raise ValueError('chave ausente/duplicada: ' + proto + '/' + key)
        body = re.sub(pattern, lambda m: m[1] + value, body)
    return (text[:match.start('body')] + body + text[match.end('body'):]).encode()


def apply(state, settings, only=None, restart=True, ctl=None):
    ctl = ctl or (lambda *args: subprocess.run(['systemctl', *args], check=False,
                                               capture_output=True, timeout=30).returncode == 0)
    changed = []
    try:
        for proto in ([only] if only else FILES):
            path = state / FILES[proto]
            if not path.exists():
                continue  # perfil ainda não gerado
            old = path.read_bytes()
            new = edited(old, proto, settings)
            if new == old:
                ensure_gateway_access(path)
                continue
            backup = path.with_name(path.name + '.pre-5.11')
            if not backup.exists():
                atomic(backup, old)
            changed.append((path, old, proto))
            atomic(path, new, gateway_ini=True)
            ensure_gateway_access(path)
        if restart:
            for _, _, proto in changed:
                if ctl('is-active', '--quiet', UNITS[proto]) and not ctl('restart', UNITS[proto]):
                    raise RuntimeError('gateway não reiniciou: ' + proto)
    except Exception:
        for path, old, proto in reversed(changed):
            atomic(path, old, gateway_ini=True)
            if restart and ctl('is-active', '--quiet', UNITS[proto]):
                ctl('restart', UNITS[proto])
        raise
    return [proto for _, _, proto in changed]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', choices=FILES)
    parser.add_argument('--no-restart', action='store_true')
    parser.add_argument('--request', action='store_true')
    args = parser.parse_args()
    state = Path(os.environ.get('PNY_STATE', '/var/lib/2pny'))
    run = Path(os.environ.get('PNY_RUN', '/run/2pny'))
    run.mkdir(parents=True, exist_ok=True)
    with (run / 'voice-apply.lock').open('w') as lock:
        if not args.no_restart:fcntl.flock(lock, fcntl.LOCK_EX)
        path = run / 'voice-request.json' if args.request else state / 'voice-settings.json'
        settings = {}
        try:
            settings = json.loads(path.read_text()) if path.exists() else {}
            if args.request:path.unlink(missing_ok=True)
            if settings.get('language', 'pt') not in ('pt', 'en', 'es'):
                raise ValueError('idioma inválido')
            for key in ('dmr', 'dstar', 'p25', 'nxdn', 'hourly'):
                if key in settings and type(settings[key]) is not bool:
                    raise ValueError('opção inválida: ' + key)
            saved = state / 'voice-settings.json'
            prior = saved.read_bytes() if saved.exists() else None
            originals = {state/path:(state/path).read_bytes() for path in FILES.values() if (state/path).is_file()}
            active = []
            if args.request:
                for proto,unit in UNITS.items():
                    if subprocess.run(['systemctl','is-active','--quiet',unit],check=False,capture_output=True,timeout=10).returncode==0:active.append(unit)
                atomic(saved, json.dumps(settings).encode())
            try:
                changed = apply(state, settings, args.only, False if args.request else not args.no_restart)
                if args.request:
                    for unit in active:
                        if subprocess.run(['systemctl','restart',unit],check=False,capture_output=True,timeout=45).returncode:raise RuntimeError('gateway não reiniciou')
            except Exception:
                if args.request:
                    if prior is None:saved.unlink(missing_ok=True)
                    else:atomic(saved,prior)
                    for path,raw in originals.items():atomic(path,raw,gateway_ini=True)
                    for unit in active:subprocess.run(['systemctl','restart',unit],check=False,capture_output=True,timeout=45)
                raise
            if args.request:
                marker = state / 'voice-hourly.enabled'
                if settings.get('hourly') and settings.get('dstar', True):
                    atomic(marker, b'1\n')
                else:
                    marker.unlink(missing_ok=True)
            result = {'ok': True, 'changed': changed}
        except Exception as exc:
            result = {'ok': False, 'error': str(exc)}
        if args.request:
            atomic(run / 'voice-result.json', json.dumps(result).encode())
        if not result['ok']:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
