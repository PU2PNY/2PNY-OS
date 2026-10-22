#!/usr/bin/env python3
"""Display-only transaction for MQTT MMDVM-Host. RF configuration is read-only."""
import configparser
import fcntl
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

STATE = Path('/var/lib/2pny')
DISPLAY = STATE/'display'
HOST = STATE/'mmdvm/MMDVM-Host.ini'
OVERRIDE = STATE/'display-override.json'
HW = STATE/'hardware-probe.json'
SETTINGS = STATE/'display-settings.json'
STATUS = STATE/'display-runtime.json'
SERVICE = '2pny-display.service'
ADAPTER = '2pny-display-adapter.service'
DRIVER = '2pny-nextiondriver.service'
CORE = '2pny-display-core.service'
CONFIG = DISPLAY/'MMDVM-Display.ini'
DRIVER_CONFIG = DISPLAY/'NextionDriver.ini'
PTY = Path('/run/2pny-nextiondriver/ttyNextionDriver')


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def atomic(path, data, mode=0o640):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.'+path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        # Installed configs must be readable by the unprivileged display service.
        import grp
        os.chown(tmp, 0, grp.getgrnam('mmdvm').gr_gid)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def json_write(path, data, mode=0o640):
    atomic(path, (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode(), mode)


def ctl(*args, check=True):
    return subprocess.run(['systemctl', *args], check=check, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=20).returncode == 0


def active(unit):
    return ctl('is-active', '--quiet', unit, check=False)


def ini_bytes(cp):
    import io
    out = io.StringIO()
    cp.write(out, space_around_delimiters=False)
    return out.getvalue().encode()


def make_config(host, ov, device, kind):
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    layout = int(ov.get('layout', 0))
    if layout not in (0, 2, 3, 4):
        raise ValueError('Selecione G4KLX, ON7LDS L2, L3 ou L3 HS')
    on7 = layout in (3, 4)
    port = 'modem' if kind == 'nextion_mmdvm' else str(device.get('port') or '')
    if port != 'modem':
        if not re.fullmatch(r'/dev/(?:tty(?:AMA|USB|ACM)\d+|serial\d+|serial/by-id/[A-Za-z0-9_.:+@-]+)', port):
            raise ValueError('Porta física de display inválida')
        if os.path.realpath(port) == os.path.realpath(host.get('Modem', 'Port', fallback='')):
            raise ValueError('A porta física da MMDVM é reservada ao rádio')
        if not Path(port).exists():
            raise ValueError('Porta de display ausente')
    cp['General'] = {'Display': 'Nextion', 'Daemon': '0'}
    cp['Log'] = {'MQTTLevel': '0', 'DisplayLevel': '1'}
    cp['MQTT'] = {k: host.get('MQTT', k, fallback=v) for k, v in
                  {'Host': '127.0.0.1', 'Port': '1883', 'Auth': '0', 'Username': '', 'Password': ''}.items()}
    cp['MQTT'].update({'Name': 'pu2pny-display', 'HostMQTTName': host.get('MQTT', 'Name', fallback='host'),
                       'InfoMQTTName': 'pu2pny-display-info', 'HostConfName': 'MMDVM-Host', 'Keepalive': '60'})
    cp['Nextion'] = {'Port': str(PTY) if on7 else port, 'Speed': '115200' if on7 else str(device.get('baud') or 9600),
                     'Brightness': '50', 'IdleBrightness': '20', 'DisplayClock': '1', 'UTC': '0',
                     # Upstream renderer accepts 0/2/3. L3 HS is a driver transport setting.
                     'ScreenLayout': '3' if on7 else str(layout)}
    driver = configparser.ConfigParser(interpolation=None)
    driver.optionxform = str
    driver['General'] = {k: host.get('General', k) for k in ('Callsign', 'Id') if host.has_option('General', k)}
    driver['Nextion'] = {'ScreenLayout': str(layout)}
    driver['NextionDriver'] = {'Port': port, 'LogLevel': '1', 'DataFilesPath': '/usr/share/2pny/nextiondriver',
                               'GroupsFile': 'groups.txt', 'DMRidFile': 'users.csv', 'WaitForLan': '0',
                               'ShowModesStatus': '1', 'RemoveDim': '0', 'SleepWhenInactive': '0'}
    # A private display bridge replaces the old attempt to render inside RF host.
    driver['Transparent Data'] = {'Enable': '1', 'SendFrameType': '1', 'RemoteAddress': '127.0.0.1',
                                   'RemotePort': '40194', 'LocalPort': '40195'}
    return cp, driver, on7, layout, port


def apply():
    ov = read(OVERRIDE)
    hw = read(HW)
    d = hw.get('display') or {}
    kind = d.get('class', '')
    if kind not in ('nextion', 'nextion_mmdvm'):
        if kind not in ('oled', 'lcd', 'lcd_i2c_candidate') and ov.get('enabled') and (hw.get('mmdvm') or {}).get('detected'):
            kind = 'nextion_mmdvm'
        else:
            # Preserve the existing direct OLED/LCD bus path; do not fabricate support
            # for compile-time drivers absent from the shipped upstream binary.
            ctl('disable', '--now', ADAPTER, check=False)
            subprocess.run(['/usr/local/sbin/2pny-display-apply.pre-5.00.002'], check=True, timeout=50)
            return
    units = (SERVICE, ADAPTER, DRIVER, CORE)
    old_active = {u: active(u) for u in units}
    old_enabled = {u: ctl('is-enabled', '--quiet', u, check=False) for u in units}
    paths = (CONFIG, DRIVER_CONFIG, SETTINGS, STATUS)
    backups = {p: p.read_bytes() if p.exists() else None for p in paths}
    if ov.get('enabled') is False:
        for u in units:
            ctl('disable', '--now', u, check=False)
        json_write(STATUS, {'state': 'disabled', 'active': False, 'writer': 'none', 'type': kind,
                            'message': 'Display desativado pelo usuário.'}, 0o644)
        return
    host = configparser.ConfigParser(interpolation=None, strict=False)
    host.optionxform = str
    if not host.read(HOST):
        raise ValueError('Configuração RF ausente; nenhuma alteração aplicada')
    cp, driver, on7, layout, port = make_config(host, ov, d, kind)
    try:
        for u in units:
            ctl('stop', u)
        ctl('disable', CORE, check=False)
        ctl('disable', DRIVER, check=False)  # Removes legacy RF Requires dependency.
        ctl('daemon-reload')
        atomic(CONFIG, ini_bytes(cp))
        atomic(DRIVER_CONFIG, ini_bytes(driver))
        settings = {'enabled': True, 'type': kind, 'renderer': 'on7lds-compatible' if on7 else 'mmdvmhost-native',
                    'writer': 'MMDVM-Display+NextionDriver' if on7 else 'MMDVM-Display',
                    'driver': 'MMDVM-Display', 'requested_layout': layout, 'effective_layout': layout,
                    'physical_confirmed': d.get('physical_confirmed') is True}
        json_write(SETTINGS, settings)
        ctl('enable', ADAPTER, SERVICE)
        ctl('start', ADAPTER)
        if on7:
            ctl('enable', DRIVER)
            ctl('start', DRIVER)
            end = time.monotonic()+8
            while not PTY.exists() or not active(DRIVER):
                if time.monotonic() > end:
                    raise RuntimeError('NextionDriver não disponibilizou sua porta virtual')
                time.sleep(.2)
        ctl('start', SERVICE)
        # Active for one instant is insufficient: catch startup/unsupported-layout exits.
        for _ in range(4):
            time.sleep(.5)
            if not active(SERVICE) or not active(ADAPTER) or (on7 and not active(DRIVER)):
                raise RuntimeError('Driver oficial de display não estabilizou')
        json_write(STATUS, {**settings, 'state': 'tx_only_unconfirmed', 'active': False,
                            'software_active': True, 'integration': 'mqtt-mmdvm' if port == 'modem' else 'uart',
                            'layout': layout, 'port': port, 'model_profile': ov.get('model_profile', 'auto'),
                            'resolution': ov.get('resolution', ''),
                            'message': 'Driver oficial MMDVM-Display iniciado; confirme standby/RX/TX na tela física. HMI/TFT preservado.',
                            'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, 0o644)
    except Exception:
        for u in units:
            ctl('stop', u, check=False)
        for path, raw in backups.items():
            if raw is None:
                path.unlink(missing_ok=True)
            else:
                atomic(path, raw, 0o644 if path == STATUS else 0o640)
        for u in units:
            ctl('enable' if old_enabled[u] else 'disable', u, check=False)
        for u in (ADAPTER, DRIVER, CORE, SERVICE):
            if old_active[u]:
                ctl('start', u, check=False)
        raise


if __name__ == '__main__':
    with open('/run/lock/2pny-display.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        apply()
    print('DISPLAY_APPLY_OK')
