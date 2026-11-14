#!/usr/bin/env python3
"""DISPLAY-5121: telemetry-only OLED pages, no ownership of MMDVM RF/Nextion."""
import shutil
import time
from pathlib import Path

NETWORK = Path('/run/2pny/network-status.txt')
TEMP = Path('/sys/class/thermal/thermal_zone0/temp')

def network_status(path=NETWORK):
    try:
        return dict(x.split('=', 1) for x in path.read_text().splitlines() if '=' in x)
    except (OSError, UnicodeError):
        return {}

def temperature(tel, path=TEMP):
    value = tel.get('temperature')
    if value is None:
        try: value = float(path.read_text().strip()) / 1000.0
        except (OSError, TypeError, ValueError): return '—'
    try:
        f = float(value)
        return f'{f:.0f}C' if -20 <= f <= 125 else '—'
    except (TypeError, ValueError, OverflowError):
        return '—'

def disk_free():
    try:
        return f'{shutil.disk_usage("/").free / 1073741824:.1f}G'
    except OSError:
        return '—'

def elapsed(a, now=None):
    try:
        ms = float(a.get('started_unix_ms'))
        if ms <= 0: return '—'
        seconds = max(0, int(((time.time() if now is None else now)*1000 - ms)/1000))
        return f'{seconds//60:02d}:{seconds%60:02d}'
    except (ValueError, TypeError):
        return '—'

def measured(value, suffix=''):
    if value is None or value == '': return '—'
    try:
        x = float(value)
        return f'{x:.1f}{suffix}' if abs(x) < 100 else f'{x:.0f}{suffix}'
    except (TypeError, ValueError):
        return '—'

def pages(live, cfg, tel, network=None, height=64, monotonic=None, now=None):
    """Return a frame of (text, y, font size); all unavailable metrics show —."""
    a = live.get('active') if isinstance(live, dict) else None
    a = a if isinstance(a, dict) else {}
    cfg = cfg if isinstance(cfg, dict) else {}
    tel = tel if isinstance(tel, dict) else {}
    net = network if network is not None else network_status()
    proto = str(a.get('protocol') or cfg.get('protocol') or '—').replace('DSTAR','D-Star')
    call = str(a.get('source') or cfg.get('callsign') or '—')
    ip = str(net.get('default_ip') or '—')
    temp = temperature(tel)
    disk = disk_free()
    mode = str(a.get('mode') or a.get('direction') or 'RX').upper()
    title = proto + (f" TS{a['slot']}" if a.get('slot') is not None else '')
    target = str(a.get('target') or cfg.get('server_name') or '—')
    if height < 48:
        phase = int((time.monotonic() if monotonic is None else monotonic)//4)
        if a:
            choices = [
                [f'{proto} {mode} {elapsed(a,now)}', call],
                [target, f"BER {measured(a.get('ber'),'%')}"],
                ['PU2PNY-OS', f'IP {ip}'],
            ]
        else:
            choices = [
                ['PU2PNY-OS', call],
                [proto + ' STANDBY', f'IP {ip}'],
                [f'CPU {temp}', f'DISCO {disk}'],
                [f'RF {cfg.get("rx_hz") or "—"}', target],
            ]
        first, second = choices[phase % len(choices)]
        return [(first,0,12),(second,15,12)]
    if a:
        return [
            ('PU2PNY-OS',0,12),
            (call,14,18),
            (f'{title} {mode} {elapsed(a,now)}',34,10),
            (target,44,10),
            (f"BER {measured(a.get('ber'),'%')} RSSI {measured(a.get('rssi_avg',a.get('rssi')))}",54,10),
        ]
    return [
        ('PU2PNY-OS',0,12),
        (call,14,18),
        (f'{proto} {target}',34,10),
        (f'IP {ip}',44,10),
        (f'CPU {temp} DISCO {disk}',54,10),
    ]

def render(self, live, cfg, tel):
    from PIL import ImageFont
    rows = pages(live, cfg, tel, height=self.h)
    signature = tuple(rows)
    if getattr(self,'_5121_signature',None) == signature:
        return 0,1
    image = self.Image.new('1',(128,self.h))
    draw = self.ImageDraw.Draw(image)
    fonts = getattr(self,'_5121_fonts',None)
    if fonts is None:
        path='/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
        fonts={n:ImageFont.truetype(path,n) for n in (10,12,18)}
        self._5121_fonts=fonts
    for value,y,size in rows:
        value=str(value)
        font=fonts[size]
        while value and font.getlength(value)>126:
            value=value[:-1]
        bbox=font.getbbox('Ag')
        draw.text((1,y-bbox[1]),value,font=font,fill=255)
    self.show_image(image)
    self._5121_signature=signature
    return 0,1
