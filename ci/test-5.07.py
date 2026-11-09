#!/usr/bin/env python3
"""SPEED-057 / BOOT-057 / EXPERT-057 / HOST-057 software tests and the 5.04 -> 5.07 overlay chain."""
import importlib.util, json, os, subprocess, sys, tempfile
from importlib.machinery import SourceFileLoader
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'ci/fixtures/5.03'

def load(path, name):
    loader = SourceFileLoader(name, str(path)); spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec); loader.exec_module(m); return m

# ---------- retry gate ----------
GATE = ROOT / 'runtime/5.07/retry-gate.sh'
def gate(td, load1='0.10', uptime='500.00', pgrep='false', cores='1', state_dir=None):
    td = Path(td); (td / 'loadavg').write_text(f'{load1} 0.5 0.5 1/100 1\n'); (td / 'uptime').write_text(f'{uptime} 1.0\n')
    env = dict(os.environ, PNY_RUN=str(td / 'run'), PNY_STATE=str(state_dir or td), PNY_LOADAVG=str(td / 'loadavg'),
               PNY_UPTIME=str(td / 'uptime'), PNY_CORES=cores, PNY_PGREP=pgrep)
    return subprocess.run(['sh', str(GATE)], env=env).returncode
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    assert gate(td) == 0, 'first attempt runs'
    assert gate(td, uptime='520.00') == 1, 'second attempt within 90 s backs off'
    assert gate(td, uptime='600.00') == 0, 'after 90 s the second attempt runs'
    assert gate(td, uptime='700.00') == 1, 'third attempt needs 180 s'
    assert gate(td, uptime='790.00') == 0
    assert gate(td, load1='2.50') == 1, 'busy single core is skipped'
    assert gate(td, load1='2.50', cores='4', uptime='5000.00') == 0, 'same load is fine on 4 cores'
    for i in range(12): gate(td, uptime=str(10000 + i * 5000) + '.00')
    count, last = (td / 'run/retry-gate.state').read_text().split()
    assert int(count) >= 5
    # back-off capped at 30 minutes
    assert gate(td, uptime=str(int(last) + 1700) + '.00') == 1 and gate(td, uptime=str(int(last) + 1801) + '.00') == 0
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    fake = td / 'pgrep.sh'; fake.write_text('#!/bin/sh\nexit 0\n'); fake.chmod(0o755)
    assert gate(td, pgrep=str(fake)) == 1, 'activation in progress: skip'
    assert not (td / 'run/retry-gate.state').exists(), 'a skipped run must not consume an attempt'
    assert gate(td) == 0
    assert gate(td, uptime='510.00') == 1
    (td / 'last-active-profile.json').write_text('{}')   # newer than the counter -> back-off resets
    assert gate(td, uptime='511.00') == 0

# ---------- fast resume now covers DMR and YSF ----------
fr = load(ROOT / 'runtime/5.07/fast-resume.py', 'fr7')
with tempfile.TemporaryDirectory() as td:
    state = Path(td); fr.STATE = state
    for d in ('dstar', 'dmr', 'ysf', 'mmdvm'): (state / d).mkdir()
    (state / 'provisioned').write_text('1'); (state / 'rf-configured').write_text('1')
    for f in ('dstar/DStarGateway.ini', 'dmr/DMRGateway.ini', 'ysf/YSFGateway.ini', 'mmdvm/MMDVM-Host.ini'): (state / f).write_text('x')
    (state / 'hardware-probe.json').write_text(json.dumps({'mmdvm': {'detected': True}}))
    class R: returncode = 0; stdout = 'default via 1.1.1.1 dev wlan0\n'
    _orig_run = fr.subprocess.run
    fr.subprocess.run = lambda *a, **k: R()
    for proto, rt_state in (('DSTAR', 'gateway_active'), ('DMR', 'configured'), ('YSF', 'gateway_active')):
        (state / 'last-active-profile.json').write_text(json.dumps({'protocol': proto, 'profile': {'protocol': proto}}))
        (state / 'network-radio.json').write_text(json.dumps({'protocol': proto, 'state': rt_state, 'server_name': 'S'}))
        (state / 'config.json').write_text(json.dumps({'protocol': proto, 'server_name': 'S'}))
        assert fr.eligible() == proto, proto
    (state / 'ysf/YSFGateway.ini').unlink()
    (state / 'last-active-profile.json').write_text(json.dumps({'protocol': 'YSF', 'profile': {'protocol': 'YSF'}}))
    (state / 'network-radio.json').write_text(json.dumps({'protocol': 'YSF', 'state': 'gateway_active', 'server_name': 'S'}))
    (state / 'config.json').write_text(json.dumps({'protocol': 'YSF', 'server_name': 'S'}))
    assert fr.eligible() is None, 'missing generated YSF config'
    (state / 'last-active-profile.json').write_text(json.dumps({'protocol': 'P25', 'profile': {'protocol': 'P25'}}))
    assert fr.eligible() is None, 'P25 keeps the original activation'
    fr.subprocess.run = _orig_run

# ---------- backend preparation: cached states and 32-bit host name ----------
for arch in ('arm64', 'arm32'):
    with tempfile.TemporaryDirectory() as td:
        cp = subprocess.run([sys.executable, str(ROOT / 'ci/prepare-5.07-backend.py'), td, arch], capture_output=True, text=True)
        assert cp.returncode == 0, cp.stderr[-500:]
        text = (Path(td) / 'main.go').read_text()
        start = text.index('func dashboardDataHandler('); end = text.index('\nfunc ', start + 10)
        body = text[start:end]
        assert body.count('serviceActiveCached(') >= 10 and 'serviceActive(' not in body.replace('serviceActiveCached(', ''), 'dashboard uses the cache only'
        assert 'appVersion            = "5.07.000"' in text
        if arch == 'arm32':
            assert 'pu2pny.local' not in text and text.count('pu2pny32.local') >= 6
        else:
            assert 'pu2pny32.local' not in text and 'http://pu2pny.local/wizard' in text

# ---------- overlay chain ----------
def make_root(td):
    root = Path(td) / 'root'
    files = (('2pny-display-core', 'usr/local/sbin/2pny-display-core'), ('protocols.html', 'usr/share/2pny/protocols.html'),
             ('expert.html', 'usr/share/2pny/expert.html'), ('system.html', 'usr/share/2pny/system.html'),
             ('2pny-timezone-apply', 'usr/local/sbin/2pny-timezone-apply'), ('en_GB.indx', 'usr/local/share/dstargateway.d/en_GB.indx'),
             ('TIME_en_GB.ambe', 'usr/local/share/dstargateway.d/TIME_en_GB.ambe'),
             ('2pny-protocol-profiles', 'usr/local/sbin/2pny-protocol-profiles'), ('wizard.html', 'usr/share/2pny/wizard.html'),
             ('internet.html', 'usr/share/2pny/internet.html'), ('dnsmasq-ap.template', 'usr/share/2pny/network/dnsmasq-ap.template'),
             ('2pny-captive.conf', 'etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf'),
             ('90-pu2pny-mdns', 'etc/NetworkManager/dispatcher.d/90-pu2pny-mdns'), ('2pny-network-core', 'usr/local/sbin/2pny-network-core'),
             ('2pny-mdns-guard', 'usr/local/sbin/2pny-mdns-guard'), ('2pny-mdns-alias', 'usr/local/sbin/2pny-mdns-alias'),
             ('hostname', 'etc/hostname'), ('hosts', 'etc/hosts'), ('avahi-daemon.conf', 'etc/avahi/avahi-daemon.conf'))
    for src, dst in files:
        (root / dst).parent.mkdir(parents=True, exist_ok=True); (root / dst).write_bytes((FIX / src).read_bytes())
    (root / 'usr/local/bin').mkdir(parents=True); (root / 'usr/local/bin/2pnyd').write_bytes(b'old')
    (root / 'etc/2pny').mkdir(parents=True); (root / 'etc/2pny/version').write_text('5.03.000\n')
    (root / 'etc/systemd/system/timers.target.wants').mkdir(parents=True)
    (root / 'usr/local/libexec/pu2pny').mkdir(parents=True)
    (root / 'usr/local/libexec/pu2pny/oled-502.py').write_bytes((ROOT / 'runtime/5.03/oled.py').read_bytes())
    return root

def chain(root, arch, binary):
    for version in ('5.04', '5.05', '5.06', '5.07'):
        cp = subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(root), arch, str(binary)], capture_output=True, text=True)
        assert cp.returncode == 0, (version, arch, cp.stderr[-600:])

with tempfile.TemporaryDirectory() as td:
    binary = Path(td) / 'd'; binary.write_bytes(b'\0' * 1_200_000)
    root64 = make_root(td + '/a64'); chain(root64, 'arm64', binary)
    root32 = make_root(td + '/a32'); chain(root32, 'arm32', binary)
    for root in (root64, root32):
        assert (root / 'etc/2pny/version').read_text() == '5.07.000\n'
        text = (root / 'usr/local/sbin/2pny-protocol-profiles').read_text()
        assert 'timeout=150)' in text and 'timeout=45)' not in text and 'timeout=55)' not in text
        assert 'Date.now()+240000' in (root / 'usr/share/2pny/wizard.html').read_text()
        assert (root / 'usr/local/sbin/2pny-retry-gate').stat().st_mode & 0o111
        assert 'ExecCondition=/usr/local/sbin/2pny-retry-gate' in (root / 'etc/systemd/system/2pny-profile-autostart-retry.service.d/57-gate.conf').read_text()
        for unit in ('2pny-netdiag', '2pny-aprs', '2pny-station', '2pny-display-core'):
            assert 'CPUWeight=' in (root / f'etc/systemd/system/{unit}.service.d/57-cpu.conf').read_text()
        assert (root / 'usr/local/sbin/2pny-protocol-profiles.pre-5.07').read_bytes() == (FIX / '2pny-protocol-profiles').read_bytes()
    # 64-bit: the host name stays pu2pny
    assert (root64 / 'etc/hostname').read_text() == 'pu2pny\n'
    assert 'pu2pny32' not in (root64 / 'usr/share/2pny/wizard.html').read_text()
    assert not (root64 / 'usr/local/sbin/2pny-mdns-alias.pre-5.07').exists()
    # 32-bit: every name moves together
    assert (root32 / 'etc/hostname').read_text() == 'pu2pny32\n'
    assert '127.0.1.1\tpu2pny32\n' in (root32 / 'etc/hosts').read_text()
    assert 'host-name=pu2pny32\n' in (root32 / 'etc/avahi/avahi-daemon.conf').read_text()
    guard = (root32 / 'usr/local/sbin/2pny-mdns-guard').read_text()
    assert 'set-hostname pu2pny32 ' in guard and "printf 'pu2pny32\\n'" in guard and '("host-name","pu2pny32")' in guard
    assert '2pny32.local' in (root32 / 'usr/local/sbin/2pny-mdns-alias').read_text()
    for path in ('usr/share/2pny/wizard.html', 'usr/share/2pny/internet.html', 'usr/share/2pny/network/dnsmasq-ap.template',
                 'etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf', 'etc/NetworkManager/dispatcher.d/90-pu2pny-mdns',
                 'usr/local/sbin/2pny-network-core', 'usr/local/libexec/pu2pny/oled-502.py', 'usr/local/libexec/pu2pny/lcd-504.py'):
        text = (root32 / path).read_text()
        assert 'pu2pny.local' not in text and 'pu2pny32.local' in text, path
    # a modified baseline is refused
    bad = make_root(td + '/bad'); (bad / 'usr/local/sbin/2pny-protocol-profiles').write_text('# modified\n')
    for version in ('5.04', '5.05', '5.06'):
        subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(bad), 'arm64', str(binary)], capture_output=True, text=True, check=True)
    cp = subprocess.run([sys.executable, '-I', str(ROOT / 'ci/patch-image-5.07.py'), str(bad), 'arm64', str(binary)], capture_output=True, text=True)
    assert cp.returncode != 0 and 'unexpected baseline' in cp.stderr
print('TEST_507_OK')
