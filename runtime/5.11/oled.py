"""DISPLAY-511: tela fixa, fonte nativa e nenhuma escrita I2C sem mudança."""
import time
from pathlib import Path


def network_status():
    try:
        return dict(line.split('=', 1) for line in Path('/run/2pny/network-status.txt').read_text().splitlines() if '=' in line)
    except OSError:
        return {}


def render(self, live, cfg, tel):
    from PIL import ImageFont
    a = live.get('active') or {}
    op = a.get('operator') or {}
    proto = str(a.get('protocol') or cfg.get('protocol') or '—')
    call = str((a.get('source') or '—') if a else cfg.get('callsign') or '—')
    if a:
        mode = str(a.get('mode') or '—').upper()
        slot = ' TS' + str(a['slot']) if a.get('slot') is not None else ''
        title = proto + slot + ' ' + mode
    else:
        title = ' '.join(str(v) for v in (proto, cfg.get('server_name'), cfg.get('xlx_module')) if v)
    lines = [title, call]
    if self.h >= 48:
        if a:
            try:
                elapsed = max(0, int(time.time() - float(a['started_unix_ms']) / 1000))
                duration = f'{elapsed//60}:{elapsed%60:02d}'
            except (KeyError, TypeError, ValueError):
                duration = '—'
            lines += [str(op.get('name') or a.get('target') or '—'),
                      str(a.get('target') or '—') if op.get('name') else '',
                      duration + (f" BER {a['ber']}%" if a.get('ber') is not None else '')]
        else:
            lines += [network_status().get('default_ip') or '—', 'Listening']
    signature = tuple(lines)
    if getattr(self, '_511_signature', None) == signature:
        return 0, 1
    image = self.Image.new('1', (128, self.h))
    draw = self.ImageDraw.Draw(image)
    fonts = getattr(self, '_511_fonts', None)
    if fonts is None:
        fontfile = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
        fonts = {size: ImageFont.truetype(fontfile, size) for size in (10, 12, 18)}
        self._511_fonts = fonts
    positions = [(0, 10), (12, 18)] if self.h < 48 else [(0, 12), (14, 18), (34, 10), (44, 10), (54, 10)]
    for text, (y, size) in zip(lines, positions):
        font = fonts[size]
        while text and font.getlength(text) > 126:
            text = text[:-1]
        top = font.getbbox('Ag')[1]
        draw.text((1, y-top), text, font=font, fill=255)
    self.show_image(image)
    self._511_signature = signature
    return 0, 1
