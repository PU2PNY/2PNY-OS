#!/usr/bin/env python3
"""CLOCK-056 / VOICE-056 / BOOT-056 / PROTO-056 software tests and the 5.04 -> 5.05 -> 5.06 overlay chain."""
import importlib.util, json, os, subprocess, sys, tempfile, time
from importlib.machinery import SourceFileLoader
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'ci/fixtures/5.03'

def load(path, name):
    loader = SourceFileLoader(name, str(path)); spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec); loader.exec_module(m); return m

# ---------- VOICE-056: word cutting from the real shipped TIME_en_GB data ----------
hv = load(ROOT / 'runtime/5.06/hourly-voice.py', 'hv')
index = hv.read_index(FIX / 'TIME_en_GB.indx'); ambe = (FIX / 'TIME_en_GB.ambe').read_bytes()
for hour in range(24):
    words = hv.sentence(hour)
    assert all(w in index for w in words), (hour, words)
assert hv.sentence(0) == ['It_is', 'midnight'] and hv.sentence(12) == ['It_is', 'midday']
assert hv.sentence(15) == ['It_is', 'three', 'O_Clock', 'PM'] and hv.sentence(9) == ['It_is', 'nine', 'O_Clock', 'AM']
with tempfile.TemporaryDirectory() as td:
    paths = hv.cut_words(ambe, index, hv.sentence(15), Path(td))
    assert len(paths) == 4
    for path, word in zip(paths, hv.sentence(15)):
        data = Path(path).read_bytes()
        assert data[:4] == b'AMBE' and (len(data) - 4) == index[word][1] * 9 and (len(data) - 4) % 9 == 0
    # index never points past the data
    for word, (offset, length) in index.items():
        assert (offset + length) * 9 + 4 <= len(ambe), word

# Gateway repeater name from the generated INI; transmits only when every gate is open.
with tempfile.TemporaryDirectory() as td:
    state = Path(td); (state / 'dstar').mkdir()
    (state / 'dstar/DStarGateway.ini').write_text('[Repeater 1]\nCallsign=PU2PNY\nBand=B\n')
    assert hv.gateway_repeater(state / 'dstar/DStarGateway.ini') == 'PU2PNY B'
    (state / 'dstar/DStarGateway.ini').write_text('[Repeater 1]\nCallsign=PU2PNY;rm\nBand=B\n')
    assert hv.gateway_repeater(state / 'dstar/DStarGateway.ini') == ''
    calls = []
    tool = state / 'tool.sh'; tool.write_text('#!/bin/sh\necho "$@" >> ' + str(state / 'calls') + '\n'); tool.chmod(0o755)
    (state / 'dstar/DStarGateway.ini').write_text('[Repeater 1]\nCallsign=PU2PNY\nBand=B\n')
    data = state / 'voice'; data.mkdir()
    (data / 'TIME_en_GB.indx').write_bytes((FIX / 'TIME_en_GB.indx').read_bytes()); (data / 'TIME_en_GB.ambe').write_bytes(ambe)
    hv.STATE, hv.DATA, hv.TOOL = state, data, str(tool)
    hv.log = lambda m: calls.append(m)
    hv.active = lambda unit: True
    # gates closed: no settings marker
    (state / 'config.json').write_text(json.dumps({'protocol': 'DSTAR'}))
    (state / 'voice-settings.json').write_text(json.dumps({'enabled': True, 'language': 'pt'}))
    hv.main(__import__('datetime').datetime(2026, 11, 9, 15, 0)); assert not (state / 'calls').exists(), 'no marker -> silent'
    (state / 'voice-hourly.enabled').write_text('1\n')
    hv.main(__import__('datetime').datetime(2026, 11, 9, 15, 0))
    line = (state / 'calls').read_text().split()
    assert line[0] == 'PU2PNY' and line[1] == 'B' and len(line) == 6, line  # 'PU2PNY B' argument splits in echo
    (state / 'calls').unlink()
    (state / 'config.json').write_text(json.dumps({'protocol': 'DMR'}))
    hv.main(__import__('datetime').datetime(2026, 11, 9, 15, 0)); assert not (state / 'calls').exists(), 'DMR -> silent'
    (state / 'config.json').write_text(json.dumps({'protocol': 'DSTAR'}))
    (state / 'voice-settings.json').write_text(json.dumps({'enabled': False}))
    hv.main(__import__('datetime').datetime(2026, 11, 9, 15, 0)); assert not (state / 'calls').exists(), 'voice off -> silent'
    (state / 'voice-settings.json').write_text(json.dumps({'enabled': True}))
    hv.active = lambda unit: unit != '2pny-dstargateway.service'
    hv.main(__import__('datetime').datetime(2026, 11, 9, 15, 0)); assert not (state / 'calls').exists(), 'gateway down -> silent'

# ---------- BOOT-056: quick resume only when everything proves the last profile ----------
fr = load(ROOT / 'runtime/5.06/fast-resume.py', 'fr')
with tempfile.TemporaryDirectory() as td:
    state = Path(td); fr.STATE = state
    for d in ('dstar', 'mmdvm'): (state / d).mkdir()
    (state / 'provisioned').write_text('1'); (state / 'rf-configured').write_text('1')
    (state / 'dstar/DStarGateway.ini').write_text('x'); (state / 'mmdvm/MMDVM-Host.ini').write_text('x')
    (state / 'last-active-profile.json').write_text(json.dumps({'protocol': 'DSTAR', 'profile': {'protocol': 'DSTAR'}}))
    (state / 'network-radio.json').write_text(json.dumps({'protocol': 'DSTAR', 'state': 'gateway_active', 'server_name': 'XLX026'}))
    (state / 'config.json').write_text(json.dumps({'protocol': 'DSTAR', 'server_name': 'XLX026'}))
    (state / 'hardware-probe.json').write_text(json.dumps({'mmdvm': {'detected': True}}))
    real_run = subprocess.run
    class R:  # uplink present
        returncode = 0; stdout = 'default via 192.168.1.1 dev wlan0\n'
    fr.subprocess.run = lambda *a, **k: R()
    assert fr.eligible() == 'DSTAR'
    (state / 'network-radio.json').write_text(json.dumps({'protocol': 'DSTAR', 'state': 'connecting', 'server_name': 'XLX026'}))
    assert fr.eligible() is None, 'runtime not proven'
    (state / 'network-radio.json').write_text(json.dumps({'protocol': 'DSTAR', 'state': 'gateway_active', 'server_name': 'XLX999'}))
    assert fr.eligible() is None, 'saved server differs from the running one'
    (state / 'network-radio.json').write_text(json.dumps({'protocol': 'DSTAR', 'state': 'gateway_active', 'server_name': 'XLX026'}))
    (state / 'dstar/DStarGateway.ini').unlink(); assert fr.eligible() is None, 'generated config missing'
    (state / 'dstar/DStarGateway.ini').write_text('x')
    class NoRoute: returncode = 0; stdout = ''
    fr.subprocess.run = lambda *a, **k: NoRoute(); assert fr.eligible() is None, 'no uplink'
    fr.subprocess.run = lambda *a, **k: R()
    (state / 'last-active-profile.json').write_text(json.dumps({'protocol': 'DMR', 'profile': {}}))
    assert fr.eligible() is None, 'DMR keeps the unchanged full activation'
    # start sequence: never restarts, starts host then gateway
    (state / 'last-active-profile.json').write_text(json.dumps({'protocol': 'DSTAR', 'profile': {'protocol': 'DSTAR'}}))
    seen = []
    fr.active = lambda unit: False
    def sc(*args, timeout=25): seen.append(args); return 0
    fr.systemctl = sc; fr.log = lambda m: None; fr.time.sleep = lambda s: None
    fr.main()
    assert seen == [('start', '2pny-mmdvmhost.service'), ('start', '2pny-dstargateway.service')], seen
    fr.subprocess.run = real_run

# ---------- CLOCK-056: helper falls back to the symlink when timedatectl does not stick ----------
tz = load(ROOT / 'runtime/5.06/tz-apply.py', 'tz')
with tempfile.TemporaryDirectory() as td:
    run_dir = Path(td) / 'run'; run_dir.mkdir(); tz.RUN = run_dir
    tz.ZONEINFO = Path(td) / 'zi'; (tz.ZONEINFO / 'America').mkdir(parents=True)
    (tz.ZONEINFO / 'America/Sao_Paulo').write_text('tz'); (tz.ZONEINFO / 'Europe').mkdir(); (tz.ZONEINFO / 'Europe/London').write_text('tz')
    state = {'zone': 'Europe/London'}
    class P:
        def __init__(self, out='', rc=0): self.stdout, self.stderr, self.returncode = out, '', rc
    def fake_run(args, timeout=10):
        if args[:3] == ['timedatectl', 'show', '-p']: return P(state['zone'] + '\n')
        if args[:2] == ['timedatectl', 'set-timezone']: return P('', 0)       # "succeeds" but does not change anything
        raise AssertionError(args)
    tz.run = fake_run
    links = []
    tz.link_fallback = lambda name: (links.append(name), state.update(zone=name))
    tz.Path = Path
    written = {}
    orig = Path.write_text
    Path.write_text = lambda self, data, *a, **k: written.__setitem__(str(self), data) if str(self) == '/etc/timezone' else orig(self, data, *a, **k)
    try:
        rid = '1' * 12
        tz.set_timezone({'timezone': 'America/Sao_Paulo'}, rid)
    finally:
        Path.write_text = orig
    result = json.loads((run_dir / f'timezone-result-{rid}.json').read_text())
    assert result == {'ok': True, 'timezone': 'America/Sao_Paulo', 'method': 'symlink', 'request_id': rid}, result
    assert links == ['America/Sao_Paulo'] and written['/etc/timezone'] == 'America/Sao_Paulo\n'
    for bad in ('../etc/passwd', '/etc/passwd', 'America/../x', 'Nope/Zone', ''):
        try: tz.set_timezone({'timezone': bad}, rid); raise SystemExit('accepted ' + bad)
        except (ValueError,): pass

# ---------- overlay chain ----------
sys.path.insert(0, str(ROOT / 'ci'))
def make_root(td):
    root = Path(td) / 'root'
    for src, dst in (('2pny-display-core', 'usr/local/sbin/2pny-display-core'), ('protocols.html', 'usr/share/2pny/protocols.html'),
                     ('expert.html', 'usr/share/2pny/expert.html'), ('system.html', 'usr/share/2pny/system.html'),
                     ('2pny-timezone-apply', 'usr/local/sbin/2pny-timezone-apply'), ('en_GB.indx', 'usr/local/share/dstargateway.d/en_GB.indx'),
                     ('TIME_en_GB.ambe', 'usr/local/share/dstargateway.d/TIME_en_GB.ambe')):
        (root / dst).parent.mkdir(parents=True, exist_ok=True); (root / dst).write_bytes((FIX / src).read_bytes())
    (root / 'usr/local/bin').mkdir(parents=True); (root / 'usr/local/bin/2pnyd').write_bytes(b'old')
    (root / 'etc/2pny').mkdir(parents=True); (root / 'etc/2pny/version').write_text('5.03.000\n')
    (root / 'etc/systemd/system/timers.target.wants').mkdir(parents=True)
    (root / 'usr/local/libexec/pu2pny').mkdir(parents=True)
    (root / 'usr/local/libexec/pu2pny/oled-502.py').write_bytes((ROOT / 'runtime/5.03/oled.py').read_bytes())
    return root
with tempfile.TemporaryDirectory() as td:
    binary = Path(td) / 'd'; binary.write_bytes(b'\0' * 1_200_000)
    root = make_root(td)
    for version in ('5.04', '5.05', '5.06'):
        cp = subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(root), 'arm64', str(binary)], capture_output=True, text=True)
        assert cp.returncode == 0, (version, cp.stderr[-600:])
    assert (root / 'etc/2pny/version').read_text() == '5.06.000\n'
    assert 'auto506' in (root / 'usr/share/2pny/system.html').read_text() and 'crossmodeCard' in (root / 'usr/share/2pny/expert.html').read_text()
    assert (root / 'usr/local/share/dstargateway.d/en_GB.indx').read_text().endswith('linkedto\t2124\t19\n')
    assert os.readlink(root / 'etc/systemd/system/timers.target.wants/2pny-hourly-voice.timer') == '../2pny-hourly-voice.timer'
    for backup in ('usr/local/sbin/2pny-timezone-apply', 'usr/share/2pny/system.html', 'usr/local/share/dstargateway.d/en_GB.indx'):
        assert (root / (backup + '.pre-5.06')).read_bytes() == (FIX / Path(backup).name).read_bytes()
    # second application must refuse (idempotence guard)
    cp = subprocess.run([sys.executable, '-I', str(ROOT / 'ci/patch-image-5.06.py'), str(root), 'arm64', str(binary)], capture_output=True, text=True)
    assert cp.returncode != 0
    # modified baseline must refuse
    root2 = make_root(td + '/b'); (root2 / 'usr/local/sbin/2pny-timezone-apply').write_text('# modified\n')
    for version in ('5.04', '5.05'):
        subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(root2), 'arm64', str(binary)], capture_output=True, text=True, check=True)
    cp = subprocess.run([sys.executable, '-I', str(ROOT / 'ci/patch-image-5.06.py'), str(root2), 'arm64', str(binary)], capture_output=True, text=True)
    assert cp.returncode != 0 and 'unexpected baseline' in cp.stderr
print('TEST_506_OK')
