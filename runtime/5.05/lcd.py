#!/usr/bin/env python3
"""DISPLAY-054/055: paged HD44780 (16x2 / 20x4) rendering; never handles RF.

Pure page builder plus a render() that is attached to the installed LCD class.
Standby cycles identity, network, URL and system pages; during traffic the
call page comes first. Only measured values are shown.
"""
import json
import time
import unicodedata
from pathlib import Path

PAGE_SECONDS = 4

def ascii_text(value):
    return unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().replace('\n', ' ').strip()

def present(*values):
    for value in values:
        if value is not None and str(value).strip():
            return str(value)
    return '-'

def cpu_temperature(path=Path('/sys/class/thermal/thermal_zone0/temp')):
    try:
        value = float(path.read_text().strip()) / 1000
        if -20 <= value <= 125:
            return f'{value:.0f}C'
    except (OSError, ValueError, OverflowError):
        pass
    return '-'

def uptime(path=Path('/proc/uptime')):
    try:
        seconds = int(float(path.read_text().split()[0]))
        days, rest = divmod(seconds, 86400)
        hours, rest = divmod(rest, 3600)
        return f'{days}d{hours}h' if days else f'{hours}h{rest // 60:02d}m'
    except (OSError, ValueError, IndexError, OverflowError):
        return '-'

def network_status(path=Path('/run/2pny/network-status.txt')):
    try:
        return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)
    except OSError:
        return {}

def mhz(hz):
    try:
        value = float(hz)
        return f'{value / 1e6:.4f}' if value > 0 else '-'
    except (TypeError, ValueError):
        return '-'

def hw_state(path=Path('/var/lib/2pny/hardware-probe.json')):
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load_average(path=Path('/proc/loadavg')):
    try:
        return path.read_text().split()[0]
    except (OSError, IndexError):
        return '-'


def pages(live, cfg, net, cols, rows, temp=None, up=None, hw=None, load=None):
    """Return a list of pages; each page is a list of exactly `rows` strings (not yet cut to `cols`)."""
    a = live.get('active') or {}
    op = a.get('operator') or {}
    proto = present(a.get('protocol'), cfg.get('protocol')).replace('DSTAR', 'D-STAR')
    mode = str(a.get('mode') or 'standby').upper()
    uplink = present(net.get('uplink_type'), 'NET').upper()
    ip = present(net.get('default_ip'))
    temp = cpu_temperature() if temp is None else temp
    up = uptime() if up is None else up
    mm = ((hw if hw is not None else hw_state()).get('mmdvm') or {})
    load = load_average() if load is None else load
    modes = ','.join(str(x) for x in (mm.get('capabilities') or [])) or '-'
    port = Path(str(mm.get('port') or '-')).name
    if rows >= 4:
        modem_page = [present(mm.get('profile')), f'{port}@{present(mm.get("baud"))}', f'FW {present(mm.get("description"))}', modes]
    else:
        modem_page = [present(mm.get('profile')), f'{port}@{present(mm.get("baud"))}']
    if not mm.get('detected'):
        modem_page = None
    if rows >= 4:
        traffic = [f'{mode} {proto}', present(a.get('source')) + ' ' + present(op.get('name'), '').replace('-', ''),
                   ' / '.join(x for x in (str(op.get('city') or ''), str(op.get('country') or '')) if x) or present(a.get('target')),
                   f'BER {present(a.get("ber"))} RSSI {present(a.get("rssi_avg"), a.get("rssi"))}']
        standby = [
            [f'{present(cfg.get("callsign"), "PU2PNY")}', f'ID {present(cfg.get("dmr_id"))}', f'{proto} READY', f'RF {mhz(cfg.get("rx_hz"))}'],
            [f'{uplink} {ip}', 'pu2pny.local', f'Net {present((live.get("internet") or {}).get("quality"))}', f'{present(cfg.get("server_name"))}'],
            ['PU2PNY-OS', f'CPU {temp}', f'UP {up}', f'LOAD {load}'],
            modem_page,
        ]
    else:
        traffic = [f'{mode} {proto}', present(a.get('source'))]
        standby = [
            [f'{present(cfg.get("callsign"), "PU2PNY")}', f'ID {present(cfg.get("dmr_id"))}'],
            [f'{uplink} {ip}', 'pu2pny.local'],
            [f'{proto} {present(cfg.get("server_name"))}', f'RF {mhz(cfg.get("rx_hz"))}'],
            [f'CPU {temp} UP {up}', f'LOAD {load}'],
            modem_page,
        ]
    if a:
        extra = [['ID ' + present(op.get('id'), a.get('id')), f'TG {present(a.get("target"))}'] if rows < 4 else
                 [f'{present(a.get("direction"))} TS{present(a.get("slot"))}', f'TG {present(a.get("target"))}', f'CC {present(a.get("color_code"))}', f'{uplink} {ip}']]
        return [traffic] + extra
    return [p for p in standby if p]

def render(self, live, cfg, tel):
    items = pages(live, cfg, network_status(), self.cols, self.rows)
    page = int(time.monotonic() // PAGE_SECONDS) % len(items)
    self.show([ascii_text(line)[:self.cols] for line in items[page]])
    return page, len(items)
