#!/usr/bin/env python3
"""DISPLAY-055: I2C OLED/LCD discovery, explicit type, extra rows and the 5.05 overlay chain (SW level).

Reproduces the original failure on the published 5.03 display-core (OLED never created when a MMDVM
is present) before testing the fix.
"""
import importlib.util, json, subprocess, sys, tempfile, textwrap
from importlib.machinery import SourceFileLoader
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'ci/fixtures/5.03'

def load(path, name):
    loader = SourceFileLoader(name, str(path)); spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec); loader.exec_module(m); return m

def make_root(td):
    root = Path(td) / 'root'
    for src, dst in (('2pny-display-core', 'usr/local/sbin/2pny-display-core'), ('protocols.html', 'usr/share/2pny/protocols.html'),
                     ('expert.html', 'usr/share/2pny/expert.html')):
        (root / dst).parent.mkdir(parents=True, exist_ok=True); (root / dst).write_bytes((FIX / src).read_bytes())
    (root / 'usr/local/bin').mkdir(parents=True); (root / 'usr/local/bin/2pnyd').write_bytes(b'old')
    (root / 'etc/2pny').mkdir(parents=True); (root / 'etc/2pny/version').write_text('5.03.000\n')
    (root / 'usr/local/libexec/pu2pny').mkdir(parents=True)
    (root / 'usr/local/libexec/pu2pny/oled-502.py').write_bytes((ROOT / 'runtime/5.03/oled.py').read_bytes())
    return root

def patch(version, root, binary):
    cp = subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(root), 'arm64', str(binary)], capture_output=True, text=True)
    assert cp.returncode == 0, cp.stderr
    return cp

def stub(mod):
    class Rec:
        def __init__(self, *a): self.args = a
    class Nex(Rec): pass
    class Oled(Rec): pass
    class Lcd(Rec): pass
    mod.Nextion, mod.OLED, mod.LCD = Nex, Oled, Lcd
    return Nex, Oled, Lcd

PROBE = {'display': {'detected': False, 'state': 'mmdvm_display_candidate', 'class': 'display_candidate', 'port': 'modem'},
         'mmdvm': {'detected': True}, 'i2c': []}

with tempfile.TemporaryDirectory() as td:
    binary = Path(td) / 'd'; binary.write_bytes(b'\0' * 1_200_000)
    root = make_root(td)
    # 1) Original failure on the published 5.03 file: an OLED on the bus is never used.
    old = load(root / 'usr/local/sbin/2pny-display-core', 'core503'); Nex, Oled, Lcd = stub(old)
    drv, kind = old.create_driver(PROBE)
    assert kind == 'nextion_mmdvm' and isinstance(drv, Nex), 'baseline reproduction'
    # 2) Chain the overlays exactly as the images receive them.
    patch('5.04', root, binary); patch('5.05', root, binary)
    assert (root / 'etc/2pny/version').read_text() == '5.05.000\n'
    core_path = root / 'usr/local/sbin/2pny-display-core'
    new = load(core_path, 'core505'); Nex, Oled, Lcd = stub(new)
    i2c = load(ROOT / 'runtime/5.05/i2c.py', 'i2c505')
    new._I2C505 = i2c
    new.SETTINGS = Path(td) / 'no-settings.json'
    def fresh(scan_result, config=None):
        i2c._cache.update(at=-1e9, found=None)
        i2c.read_config = lambda path=None: dict(config or {})
        i2c.scan = lambda *a, **k: scan_result
    fresh(0x3C)
    drv, kind = new.create_driver(PROBE)
    assert kind == 'oled' and isinstance(drv, Oled) and drv.args == (1, 0x3C, False, 64), (kind, getattr(drv, 'args', None))
    fresh(0x3C, {'type': 'sh1106'}); drv, kind = new.create_driver(PROBE)
    assert kind == 'oled' and drv.args == (1, 0x3C, True, 64), drv.args
    fresh(0x3D, {'type': 'ssd1306', 'height': 32}); drv, kind = new.create_driver(PROBE)
    assert kind == 'oled' and drv.args == (1, 0x3D, False, 32), drv.args
    fresh(0x27); drv, kind = new.create_driver(PROBE)
    assert kind == 'lcd' and drv.args == (1, 0x27, 20, 4), drv.args
    fresh(0x3F, {'type': 'lcd', 'lcd_cols': 16, 'lcd_rows': 2}); drv, kind = new.create_driver(PROBE)
    assert kind == 'lcd' and drv.args == (1, 0x3F, 16, 2), drv.args
    # Nextion users keep their behavior: nothing on the bus, or proven/persisted Nextion.
    fresh(None); drv, kind = new.create_driver(PROBE)
    assert kind == 'nextion_mmdvm' and isinstance(drv, Nex)
    fresh(0x3C)
    proven = json.loads(json.dumps(PROBE)); proven['display'].update({'class': 'nextion_mmdvm', 'state': 'manual_override'})
    drv, kind = new.create_driver(proven); assert kind == 'nextion_mmdvm' and isinstance(drv, Nex)
    fresh(0x3C, {'type': 'none'}); drv, kind = new.create_driver(PROBE); assert kind == 'nextion_mmdvm'
    # Probe-listed I2C address works without a scan, scan result is cached for a minute.
    fresh(None); hw = dict(PROBE, i2c=[{'bus': 1, 'address': '0x3c'}]); drv, kind = new.create_driver(hw); assert kind == 'oled'
    calls = []; fresh(None); i2c.scan = lambda *a, **k: calls.append(1)
    for _ in range(5): i2c.choose(PROBE['display'], PROBE, {}, config={}, scanner=lambda: calls.append(1))
    assert len(calls) == 1, calls
    # Scan is read-only and tolerates a missing bus.
    class Bus:
        reads = []
        def __init__(self, n): pass
        def read_byte(self, a):
            Bus.reads.append(a)
            if a != 0x27: raise OSError(121)
            return 0
        def write_byte(self, *a): raise AssertionError('scan must never write')
        def close(self): pass
    real_scan = load(ROOT / 'runtime/5.05/i2c.py', 'i2c505b').scan
    assert real_scan(1, Bus) == 0x27 and Bus.reads == [0x3C, 0x3D, 0x27]
    assert real_scan(1, lambda n: (_ for _ in ()).throw(OSError('no bus'))) is None
    html = (root / 'usr/share/2pny/expert.html').read_text()
    assert html.count('id="oledcard505"') == 1 and html.count('id="console504"') == 1 and html.count('</main>') == 1

# Extra OLED rows: old order kept, modem and Raspberry values appended, absent values skipped.
old = load(ROOT / 'runtime/5.03/oled.py', 'o503'); newo = load(ROOT / 'runtime/5.05/oled.py', 'o505')
cfg = {'callsign': 'PU2PNY', 'dmr_id': '7240000', 'protocol': 'DMR'}; net = {'default_ip': '192.0.2.10', 'uplink_type': 'wifi'}
hw = {'mmdvm': {'detected': True, 'profile': 'MMDVM_HS compatível', 'description': 'MMDVM_HS_Hat-v1.5.2', 'port': '/dev/ttyAMA0', 'baud': 115200,
                'capabilities': ['D-Star', 'DMR'], 'protocol_version': 2, 'cpu': 'ST-Micro ARM', 'udid': 'AABBCCDDEEFF00112233445566778899'}}
sysinfo = [('Board', 'Pi Zero W Rev 1.1'), ('Load', '0.10'), ('RAM free', '300 MB'), ('SD free', '70%'), ('CPU MHz', '1000')]
for live in ({}, {'active': {'source': 'PU2ABC', 'target': 'TG724', 'protocol': 'DMR'}}):
    a = old.rows(live, cfg, net, now=1700000000); b = newo.rows(live, cfg, net, now=1700000000, hw=hw, system=sysinfo)
    assert b[:len(a)] == a and len(b) > len(a)
    text = ' '.join(b)
    for needle in ('Modem: MMDVM_HS', 'FW: MMDVM_HS_Hat-v1.5.2', 'ttyAMA0@115200', 'D-Star,DMR', 'UDID: 66778899', 'Board: Pi Zero W', 'Load: 0.10', 'SD free: 70%'):
        assert needle in text, needle
none = newo.rows({}, cfg, net, now=1700000000, hw={}, system=[])
assert none == old.rows({}, cfg, net, now=1700000000), 'no modem and no system data must equal the old rows'
with tempfile.TemporaryDirectory() as td:
    r = Path(td); (r / 'proc/device-tree').mkdir(parents=True); (r / 'proc/device-tree/model').write_bytes(b'Raspberry Pi Zero W Rev 1.1\0')
    (r / 'proc/loadavg').write_text('0.52 0.40 0.30 1/100 123\n'); (r / 'proc/meminfo').write_text('MemTotal: 500000 kB\nMemAvailable: 307200 kB\n')
    got = dict(newo.system_info(root=r)); assert got['Board'] == 'Pi Zero W Rev 1.1' and got['Load'] == '0.52' and got['RAM free'] == '300 MB', got
    assert 'SD free' in got
    assert newo.system_info(root=r / 'missing') == [] or all(isinstance(v, str) for _, v in newo.system_info(root=r / 'missing'))
print('TEST_DISPLAY_055_OK')
