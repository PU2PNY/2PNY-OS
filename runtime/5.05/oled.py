#!/usr/bin/env python3
"""Paged operational data for the existing OLED bus driver; never handles RF.

5.05: adds MMDVM modem and Raspberry Pi system rows after the existing ones.
Only measured values are shown; absent values are skipped to keep pages short.
"""
import json
import os
import math
import textwrap
import time
import unicodedata
from pathlib import Path

COLS = 20

def present(*values):
    for value in values:
        if value is not None and str(value).strip():
            return str(value)
    return '-'

def hz(value):
    try:
        value = float(value)
        return f'{value/1000000:.6f}' if value > 0 else '-'
    except (ValueError, TypeError):
        return '-'

def ascii_text(value):
    return unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().replace('\n', ' ')

def cpu_temperature(path=Path('/sys/class/thermal/thermal_zone0/temp')):
    """Return measured SoC temperature, never simulated data."""
    try:
        value = float(path.read_text().strip()) / 1000
        if -20 <= value <= 125:
            return f'{value:.1f} C'
    except (OSError, ValueError, TypeError, OverflowError):
        pass
    return '-'


def system_uptime(path=Path('/proc/uptime')):
    """Read monotonic kernel uptime, independent of clock or NTP."""
    try:
        seconds = int(float(path.read_text().split()[0]))
        if seconds >= 0:
            days, rest = divmod(seconds, 86400)
            hours, rest = divmod(rest, 3600)
            minutes = rest // 60
            return f'{days}d {hours}h' if days else f'{hours}h {minutes}m'
    except (OSError, ValueError, TypeError, IndexError, OverflowError):
        pass
    return '-'


def read_hw(path=Path('/var/lib/2pny/hardware-probe.json')):
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def text_file(path):
    try:
        return Path(path).read_text().replace('\0', '').strip()
    except OSError:
        return ''


def system_info(statvfs=os.statvfs, root=Path('/')):
    """Cheap measured Raspberry values; every item is optional."""
    info = []
    model = text_file(root / 'proc/device-tree/model').replace('Raspberry Pi ', 'Pi ')
    if model:
        info.append(('Board', model))
    try:
        load = text_file(root / 'proc/loadavg').split()[0]
        info.append(('Load', load))
    except IndexError:
        pass
    try:
        for line in text_file(root / 'proc/meminfo').splitlines():
            if line.startswith('MemAvailable:'):
                info.append(('RAM free', f'{int(line.split()[1]) // 1024} MB'))
    except (ValueError, IndexError):
        pass
    try:
        st = statvfs(str(root))
        total, free = st.f_blocks * st.f_frsize, st.f_bavail * st.f_frsize
        if total > 0:
            info.append(('SD free', f'{free * 100 // total}%'))
    except OSError:
        pass
    try:
        khz = int(text_file(root / 'sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'))
        info.append(('CPU MHz', str(khz // 1000)))
    except ValueError:
        pass
    host = text_file(root / 'etc/hostname')
    if host:
        info.append(('Host', host))
    return info


def modem_info(hw):
    """MMDVM identification from the boot probe (what the modem answered)."""
    m = (hw or {}).get('mmdvm') or {}
    if not m.get('detected'):
        return []
    info = [('Modem', m.get('profile')), ('FW', m.get('description'))]
    port = str(m.get('port') or '')
    if port:
        info.append(('Port', os.path.basename(port) + ('@' + str(m.get('baud')) if m.get('baud') else '')))
    if m.get('capabilities'):
        info.append(('Modes', ','.join(str(x) for x in m['capabilities'])))
    if m.get('protocol_version') is not None:
        info.append(('Proto', m.get('protocol_version')))
    if m.get('cpu') and m.get('cpu') != 'Não informado':
        info.append(('MCU', m.get('cpu')))
    if m.get('udid'):
        info.append(('UDID', str(m['udid'])[-8:]))
    return info


def rows(live, cfg, network, now=None, hw=None, system=None):
    a = live.get('active') or {}
    op = a.get('operator') or {}
    internet = live.get('internet') or {}
    now = time.time() if now is None else now
    duration = '-'
    try:
        started = float(a.get('started_unix_ms')) / 1000
        if 0 < started <= now:
            seconds = int(now-started)
            duration = f'{seconds//60}:{seconds%60:02d}'
    except (TypeError, ValueError, OverflowError):
        pass
    fields = [
        ('Call', a.get('source')), ('Dest', a.get('target')),
        ('BER %', a.get('ber')), ('RSSI dBm', present(a.get('rssi_avg'), a.get('rssi'))),
        ('ID', present(op.get('id'), a.get('id'))), ('Name', op.get('name')),
        ('City', op.get('city')), ('Country', op.get('country')),
        ('Protocol', a.get('protocol')), ('Direction', a.get('direction')),
        ('Slot', a.get('slot')), ('CC', a.get('color_code')), ('Module', a.get('module')),
        ('Duration', duration), ('Local', cfg.get('callsign')), ('Local ID', cfg.get('dmr_id')),
        ('RX MHz', hz(cfg.get('rx_hz'))), ('TX MHz', hz(cfg.get('tx_hz'))),
        ('ModeCfg', cfg.get('use_mode')), ('ServerCfg', cfg.get('server_name')),
        ('ModCfg', cfg.get('xlx_module')), ('CCCfg', cfg.get('color_code')),
        ('SlotCfg', cfg.get('dmr_slot')), ('Uplink', network.get('uplink_type')),
        ('IP', network.get('default_ip')), ('Network', internet.get('quality')),
        ('URL', 'pu2pny.local'), ('CPU', cpu_temperature()), ('Uptime', system_uptime()),
    ]
    present_extra = [(k, v) for k, v in (modem_info(hw if hw is not None else read_hw()) + (system if system is not None else system_info()))
                     if v is not None and str(v).strip() and str(v) != '-']
    fields = fields + present_extra
    # Idle first page identifies the local station instead of showing empty caller fields.
    if not a:
        fields = fields[14:18]+fields[:14]+fields[18:]
    result = []
    for key, value in fields:
        line = ascii_text(key+': '+present(value))
        result += textwrap.wrap(line, width=COLS, break_long_words=True, break_on_hyphens=False) or ['-']
    return result

def network_status():
    try:
        return dict(line.split('=', 1) for line in Path('/run/2pny/network-status.txt').read_text().splitlines() if '=' in line)
    except OSError:
        return {}

def fit_rows(content, font, width=124):
    result = []
    for text in content:
        chunk = ''
        for char in text:
            box = font.getbbox(chunk+char)
            if chunk and box[2]-box[0] > width:
                result.append(chunk)
                chunk = ''
            chunk += char
        result.append(chunk)
    return result

def render(self, live, cfg, tel):
    a = live.get('active') or {}
    key = (a.get('source'), a.get('target'), a.get('protocol'), a.get('started_unix_ms'), cfg.get('callsign'))
    clock = time.monotonic()
    if getattr(self, '_502_key', None) != key:
        self._502_key, self._502_epoch = key, clock
    content = fit_rows(rows(live, cfg, network_status()), self.font)
    capacity = max(1, (self.h-12)//10)
    total = max(1, math.ceil(len(content)/capacity))
    page = int((clock-self._502_epoch)//4) % total
    mode = str(a.get('mode') or ('STBY' if live.get('standby') is True else '?')).upper()
    proto = present(a.get('protocol')) if a else present(cfg.get('protocol'))
    header = ascii_text(f'{proto} {mode} {page+1}/{total}')[:COLS]
    image = self.Image.new('1', (128, self.h))

    def line(text, y):
        bbox = self.font.getbbox(text)
        height = max(1, bbox[3]-bbox[1])
        tile = self.Image.new('1', (max(124, bbox[2]-bbox[0]), height))
        self.ImageDraw.Draw(tile).text((-bbox[0], -bbox[1]), text, font=self.font, fill=255)
        # Fit the whole glyph vertically; never crop descenders on a 32-pixel panel.
        if height != 9 or tile.width != 124:
            tile = tile.resize((124, 9), resample=0)
        image.paste(tile, (2, y))

    line(header, 1)
    for index, text in enumerate(content[page*capacity:(page+1)*capacity]):
        line(text, 12+index*10)
    self.show_image(image)
    return page, total
