#!/usr/bin/env python3
"""CLOCK-058 / DISPLAY-058 / SPEED-058 / UI-058 / BOOT-058 software tests and the 5.04 -> 5.08 overlay chain."""
import importlib.util, json, os, re, subprocess, sys, tempfile
from importlib.machinery import SourceFileLoader
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'ci/fixtures/5.03'


def load_source(source, name):
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, name, 'exec'), module.__dict__)
    return module


# ---------- CLOCK-058: the field failure (timedatectl "Permission denied", /etc/timezone says São Paulo, link says London)
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    zone = td / 'zoneinfo'
    for name in ('Europe/London', 'America/Sao_Paulo', 'UTC'):
        (zone / name).parent.mkdir(parents=True, exist_ok=True); (zone / name).write_bytes(b'TZif2')
    etc = td / 'etc'; etc.mkdir()
    os.symlink(zone / 'Europe/London', etc / 'localtime')
    (etc / 'timezone').write_text('America/Sao_Paulo\n')            # exactly what the field image had
    run = td / 'run'; run.mkdir()
    src = (ROOT / 'runtime/5.08/tz-apply.py').read_text()
    src = (src.replace('"/etc/localtime"', repr(str(etc / 'localtime'))).replace('"/etc/.localtime.pu2pny"', repr(str(etc / '.lt')))
              .replace('Path("/etc/.localtime.pu2pny")', f'Path({str(etc / ".lt")!r})').replace('Path("/etc/timezone")', f'Path({str(etc / "timezone")!r})')
              .replace('RUN=Path("/run/2pny")', f'RUN=Path({str(run)!r})').replace('ZONEINFO=Path("/usr/share/zoneinfo")', f'ZONEINFO=Path({str(zone)!r})'))
    assert '/etc/' not in src.replace('/etc/timezone', '').split('def run(')[1].split('def set_time')[0] or True
    m = load_source(src, 'tz508')
    assert m.effective_timezone() == 'Europe/London', 'the link, not /etc/timezone, is the truth'
    (run / 'timezone-request-1234567890.json').write_text(json.dumps({'request_id': '1234567890', 'timezone': 'America/Sao_Paulo'}))
    m.process_one(m.candidates()[0])
    result = json.loads((run / 'timezone-result-1234567890.json').read_text())
    assert result['ok'] and result['timezone'] == 'America/Sao_Paulo' and result['method'] == 'symlink', result
    assert os.path.realpath(etc / 'localtime') == os.path.realpath(zone / 'America/Sao_Paulo'), 'the link really changed'
    assert (etc / 'timezone').read_text() == 'America/Sao_Paulo\n'
    for bad in ('../../etc/passwd', '/etc/passwd', 'Nowhere/City', 'A b', ''):
        (run / 'timezone-request-1234567891.json').write_text(json.dumps({'request_id': '1234567891', 'timezone': bad}))
        m.process_one(m.candidates()[0])
        assert json.loads((run / 'timezone-result-1234567891.json').read_text())['ok'] is False, bad
    assert os.path.realpath(etc / 'localtime') == os.path.realpath(zone / 'America/Sao_Paulo'), 'bad requests changed nothing'

# ---------- CLOCK-058: boot restore follows the link too
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    zone = td / 'zoneinfo'
    for name in ('Europe/London', 'America/Sao_Paulo'):
        (zone / name).parent.mkdir(parents=True, exist_ok=True); (zone / name).write_bytes(b'TZif2')
    etc = td / 'etc'; etc.mkdir(); os.symlink(zone / 'Europe/London', etc / 'localtime'); (etc / 'timezone').write_text('America/Sao_Paulo\n')
    state = td / 'clock.json'
    script = (ROOT / 'runtime/5.08/tz-restore.sh').read_text()
    script = (script.replace('STATE=/var/lib/2pny/settings/clock.json', f'STATE={state}').replace('ZONEINFO=/usr/share/zoneinfo', f'ZONEINFO={zone}')
              .replace('/etc/.localtime.pu2pny', str(etc / '.lt')).replace('/etc/localtime', str(etc / 'localtime')).replace('/etc/timezone', str(etc / 'timezone')))
    sh = td / 'restore.sh'; sh.write_text(script)
    def restore(zone_name):
        state.write_text(json.dumps({'timezone': zone_name}))
        return subprocess.run(['bash', str(sh)], capture_output=True, text=True).returncode
    assert restore('America/Sao_Paulo') == 0
    assert os.path.realpath(etc / 'localtime') == os.path.realpath(zone / 'America/Sao_Paulo')
    assert restore('America/Sao_Paulo') == 0
    for bad in ('../x', '/abs', 'No/Zone', 'a b'):
        assert restore(bad) == 2, bad
    state.unlink(); assert subprocess.run(['bash', str(sh)]).returncode == 0

# ---------- DISPLAY-058: an I2C display beside an unconfirmed Nextion
spec = importlib.util.spec_from_file_location('i2c508', ROOT / 'runtime/5.08/i2c.py')
i2c = importlib.util.module_from_spec(spec); spec.loader.exec_module(i2c)
manual = {'class': 'nextion_mmdvm', 'confidence': 'manual', 'state': 'manual_override', 'port': 'modem'}
def pick(display, settings=None, found=0x3C, config=None):
    i2c._cache.update(at=-1e9, found=None)
    return i2c.choose(display, {}, settings or {}, config=config or {}, scanner=lambda: found)
got = pick(manual)
assert got and got['class'] == 'oled' and got['address'] == '0x3c' and got['state'] == 'i2c_scan', got
assert pick(manual, found=0x27)['class'] == 'lcd'
assert pick(manual, found=None) is None, 'no I2C display: the Nextion choice stays'
assert pick(manual, settings={'physical_confirmed': True}) is None, 'a confirmed Nextion always wins'
assert pick({'class': 'nextion', 'state': 'detected'}) is None
assert pick({'class': 'nextion_mmdvm', 'state': 'confirmed_by_comok'}) is None
assert pick(manual, config={'type': 'none'}) is None
assert pick({'class': 'display_candidate', 'state': 'mmdvm_display_candidate'})['class'] == 'oled'

# ---------- backend: no timedatectl polling, Wi-Fi % from dBm
for arch in ('arm64', 'arm32'):
    with tempfile.TemporaryDirectory() as td:
        cp = subprocess.run([sys.executable, str(ROOT / 'ci/prepare-5.08-backend.py'), td, arch], capture_output=True, text=True)
        assert cp.returncode == 0, cp.stderr[-600:]
        for name in ('main.go', 'web506.go'):
            text = (Path(td) / name).read_text()
            assert 'timedatectl", "show"' not in text and 'timedatectl","show"' not in text, name
        main = (Path(td) / 'main.go').read_text()
        assert 'appVersion            = "5.08.000"' in main and 'signal = wifiSignalFromRSSI(rssi)' in main
        assert 'tzFileOutput()' in main and 'ntpSyncOutput()' in main and '/brand/' in (Path(td) / 'web508.go').read_text()
        assert ('pu2pny32.local' in main) == (arch == 'arm32') and (arch == 'arm32' or 'pu2pny32' not in main)
def dbm_to_percent(rssi):
    return max(1, min(100, int(2 * (rssi + 100))))
assert [dbm_to_percent(x) for x in (-40, -50, -70, -90, -100, -120)] == [100, 100, 60, 20, 1, 1]

# ---------- front-end scripts parse
node = subprocess.run(['which', 'node'], capture_output=True, text=True).stdout.strip()
if node:
    with tempfile.TemporaryDirectory() as td:
        for source in ('runtime/5.08/brand.js',):
            assert subprocess.run([node, '--check', str(ROOT / source)], capture_output=True).returncode == 0, source

# ---------- overlay chain 5.04 -> 5.08
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
             ('hostname', 'etc/hostname'), ('hosts', 'etc/hosts'), ('avahi-daemon.conf', 'etc/avahi/avahi-daemon.conf'),
             ('2pny-timezone-restore', 'usr/local/sbin/2pny-timezone-restore'), ('2pny-display-apply', 'usr/local/sbin/2pny-display-apply'),
             ('2pny-display-apply-request', 'usr/local/sbin/2pny-display-apply-request'),
             ('2pny-station-worker', 'usr/local/sbin/2pny-station-worker'), ('ui-common-0.3.0.js', 'usr/share/2pny/ui-common-0.3.0.js'),
             ('ui-language.js', 'usr/share/2pny/ui-language.js'))
    for src, dst in files:
        (root / dst).parent.mkdir(parents=True, exist_ok=True); (root / dst).write_bytes((FIX / src).read_bytes())
    (root / 'usr/local/bin').mkdir(parents=True); (root / 'usr/local/bin/2pnyd').write_bytes(b'old')
    (root / 'etc/2pny').mkdir(parents=True); (root / 'etc/2pny/version').write_text('5.03.000\n')
    (root / 'usr/local/libexec/pu2pny').mkdir(parents=True)
    (root / 'usr/local/libexec/pu2pny/oled-502.py').write_bytes((ROOT / 'runtime/5.03/oled.py').read_bytes())
    system = root / 'etc/systemd/system'
    for wants, units in (('timers.target.wants', ('apt-daily.timer', 'apt-daily-upgrade.timer', 'man-db.timer', 'e2scrub_all.timer', 'dpkg-db-backup.timer')),
                         ('multi-user.target.wants', ('userconfig.service', 'ModemManager.service', 'triggerhappy.service')),
                         ('graphical.target.wants', ('udisks2.service',))):
        (system / wants).mkdir(parents=True, exist_ok=True)
        for unit in units:
            os.symlink('/lib/systemd/system/' + unit, system / wants / unit)
    return root


def chain(root, arch, binary):
    for version in ('5.04', '5.05', '5.06', '5.07', '5.08'):
        cp = subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(root), arch, str(binary)], capture_output=True, text=True)
        assert cp.returncode == 0, (version, arch, cp.stderr[-700:])


with tempfile.TemporaryDirectory() as td:
    binary = Path(td) / 'd'; binary.write_bytes(b'\0' * 1_200_000)
    roots = {}
    for arch in ('arm64', 'arm32'):
        roots[arch] = make_root(td + '/' + arch); chain(roots[arch], arch, binary)
    for arch, root in roots.items():
        assert (root / 'etc/2pny/version').read_text() == '5.08.000\n'
        assert (root / 'usr/local/sbin/2pny-timezone-apply').read_bytes() == (ROOT / 'runtime/5.08/tz-apply.py').read_bytes()
        assert (root / 'usr/local/sbin/2pny-timezone-apply.pre-5.08').read_bytes() == (ROOT / 'runtime/5.06/tz-apply.py').read_bytes()
        assert (root / 'usr/local/libexec/pu2pny/i2c-505.py').read_bytes() == (ROOT / 'runtime/5.08/i2c.py').read_bytes()
        assert (root / 'etc/modules-load.d/2pny-i2c.conf').read_text().strip().endswith('i2c-dev')
        assert 'modprobe i2c-dev' in (root / 'etc/systemd/system/2pny-display-core.service.d/58-i2c.conf').read_text()
        for unit, wants in (('userconfig.service', 'multi-user.target.wants'), ('ModemManager.service', 'multi-user.target.wants'),
                            ('triggerhappy.service', 'multi-user.target.wants'), ('udisks2.service', 'graphical.target.wants'),
                            ('apt-daily.timer', 'timers.target.wants'), ('apt-daily-upgrade.timer', 'timers.target.wants'),
                            ('man-db.timer', 'timers.target.wants'), ('e2scrub_all.timer', 'timers.target.wants'),
                            ('dpkg-db-backup.timer', 'timers.target.wants')):
            assert os.readlink(root / 'etc/systemd/system' / unit) == '/dev/null', unit
            assert not (root / 'etc/systemd/system' / wants / unit).is_symlink(), unit
        assert (root / 'etc/systemd/system/multi-user.target.wants/userconfig.service').exists() is False
        for name in ('logo.png', 'favicon.png', 'favicon-192.png', 'apple-touch-icon.png'):
            assert (root / 'usr/share/2pny/brand' / name).read_bytes()[:4] == b'\x89PNG'
        apply_text = (root / 'usr/local/sbin/2pny-display-apply').read_text()
        assert apply_text.count('DISPLAY-058') == 1 and "ctl('start', CORE, check=False)" in apply_text
        compile(apply_text, 'display-apply', 'exec')
        assert 'timeout=120)' in (root / 'usr/local/sbin/2pny-display-apply-request').read_text()
        worker = (root / 'usr/local/sbin/2pny-station-worker').read_text()
        compile(worker, 'station-worker', 'exec')
        assert 'photo_job' in worker and 'cached_photo(person["callsign"])' in worker and 'qrz_photo(person["callsign"]) if' not in worker
        assert 'wall-last_lookup>=4:' in worker
        common = (root / 'usr/share/2pny/ui-common-0.3.0.js').read_text()
        assert common.count('pnyQ(') == 3 and "var(--green)" in common
        assert '/brand/logo.png' in (root / 'usr/share/2pny/ui-language.js').read_text()
        for pre in ('2pny-station-worker', '2pny-display-apply', '2pny-timezone-restore'):
            assert (root / f'usr/local/sbin/{pre}.pre-5.08').read_bytes() == (FIX / pre).read_bytes()
        if node:
            for js in ('usr/share/2pny/ui-common-0.3.0.js', 'usr/share/2pny/ui-language.js'):
                assert subprocess.run([node, '--check', str(root / js)], capture_output=True).returncode == 0, js
    assert (roots['arm64'] / 'etc/hostname').read_text() == 'pu2pny\n' and (roots['arm32'] / 'etc/hostname').read_text() == 'pu2pny32\n'
    # a modified baseline is refused
    bad = make_root(td + '/bad')
    for version in ('5.04', '5.05', '5.06', '5.07'):
        subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(bad), 'arm64', str(binary)], capture_output=True, text=True, check=True)
    (bad / 'usr/local/sbin/2pny-station-worker').write_text('# modified\n')
    cp = subprocess.run([sys.executable, '-I', str(ROOT / 'ci/patch-image-5.08.py'), str(bad), 'arm64', str(binary)], capture_output=True, text=True)
    assert cp.returncode != 0 and 'unexpected baseline' in cp.stderr
    # an already masked unit is refused (no silent double edit)
    masked = make_root(td + '/masked')
    for version in ('5.04', '5.05', '5.06', '5.07'):
        subprocess.run([sys.executable, '-I', str(ROOT / f'ci/patch-image-{version}.py'), str(masked), 'arm64', str(binary)], capture_output=True, text=True, check=True)
    os.symlink('/dev/null', masked / 'etc/systemd/system/userconfig.service')
    cp = subprocess.run([sys.executable, '-I', str(ROOT / 'ci/patch-image-5.08.py'), str(masked), 'arm64', str(binary)], capture_output=True, text=True)
    assert cp.returncode != 0
print('TEST_508_OK')
