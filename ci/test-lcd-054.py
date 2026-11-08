#!/usr/bin/env python3
"""DISPLAY-054: LCD pages for 20x4 and 16x2, measured values only, never wider than the panel (SW level)."""
import importlib.util, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lcd504', ROOT / 'runtime/5.04/lcd.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cfg = {'callsign': 'PU2PNY', 'dmr_id': '7240000', 'protocol': 'DMR', 'rx_hz': 438800000, 'server_name': 'BM Brasil'}
net = {'default_ip': '192.168.15.20', 'uplink_type': 'wifi'}
live = {'internet': {'quality': 'good'}}
active = {'active': {'mode': 'dmr', 'protocol': 'DMR', 'source': 'PU2ABC', 'target': 'TG724', 'slot': 2, 'color_code': 1, 'ber': 0.3, 'rssi': -80,
                     'direction': 'RF', 'operator': {'name': 'Ana', 'city': 'Sao Paulo', 'country': 'Brasil', 'id': '7241111'}}}
for cols, rows in ((20, 4), (16, 2)):
    for lv in (live, active):
        ps = m.pages(lv, cfg, net, cols, rows, temp='47C', up='2h05m')
        assert ps and all(len(p) == rows for p in ps), (cols, rows, ps)
text = ' '.join(' '.join(p) for p in m.pages(live, cfg, net, 20, 4, temp='47C', up='2h05m'))
for needle in ('PU2PNY', '7240000', '192.168.15.20', 'pu2pny.local', 'CPU 47C', 'UP 2h05m', '438.8000'):
    assert needle in text, needle
assert 'PU2ABC' in ' '.join(m.pages(active, cfg, net, 20, 4)[0])
assert 'PU2ABC' in ' '.join(m.pages(active, cfg, net, 16, 2)[0])
# Unknown values stay '-', never invented.
bare = ' '.join(' '.join(p) for p in m.pages({}, {}, {}, 20, 4, temp='-', up='-'))
assert 'None' not in bare and 'null' not in bare.lower()
# render() cuts every line to the panel width and ASCII-folds.
class Fake:
    cols, rows = 16, 2
    def show(self, lines): self.lines = lines
f = Fake(); m.render(f, {}, dict(cfg, callsign='PU2Ç' + 'X' * 30), {})
assert len(f.lines) == 2 and all(len(l) <= 16 and l.isascii() for l in f.lines), f.lines
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / 't'; assert m.cpu_temperature(p) == '-' and m.uptime(p) == '-'
    p.write_text('47123\n'); assert m.cpu_temperature(p) == '47C'
    p.write_text('93784.2 1\n'); assert m.uptime(p) == '1d2h'
    p.write_text('3700.0 1\n'); assert m.uptime(p) == '1h01m'
print('TEST_DISPLAY_054_LCD_OK')
