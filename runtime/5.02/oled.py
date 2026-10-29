#!/usr/bin/env python3
"""Paged operational data for the existing OLED bus driver; never handles RF."""
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

def rows(live, cfg, network, now=None):
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
    ]
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
