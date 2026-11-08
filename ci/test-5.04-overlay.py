#!/usr/bin/env python3
"""Offline test of ci/patch-image-5.04.py against a fake 5.03 root built from the published 5.03 files (SW level)."""
import hashlib, re, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'ci/fixtures/5.03'
PATCH = ROOT / 'ci/patch-image-5.04.py'
for line in (FIX / 'SHA256SUMS').read_text().splitlines():
    digest, name = line.split()
    assert hashlib.sha256((FIX / name).read_bytes()).hexdigest() == digest, name

def make_root(td, version='5.03.000'):
    root = Path(td) / 'root'
    for src, dst in (('2pny-display-core', 'usr/local/sbin/2pny-display-core'), ('protocols.html', 'usr/share/2pny/protocols.html'),
                     ('expert.html', 'usr/share/2pny/expert.html')):
        (root / dst).parent.mkdir(parents=True, exist_ok=True); (root / dst).write_bytes((FIX / src).read_bytes())
    (root / 'usr/local/bin').mkdir(parents=True); (root / 'usr/local/bin/2pnyd').write_bytes(b'old-daemon')
    (root / 'etc/2pny').mkdir(parents=True); (root / 'etc/2pny/version').write_text(version + '\n')
    return root

def run(root, binary, arch='arm64'):
    return subprocess.run([sys.executable, '-I', str(PATCH), str(root), arch, str(binary)], capture_output=True, text=True)

with tempfile.TemporaryDirectory() as td:
    binary = Path(td) / 'daemon'; binary.write_bytes(b'\0' * 1_200_000)
    for arch in ('arm32', 'arm64'):
        with tempfile.TemporaryDirectory() as rd:
            root = make_root(rd)
            before = {p: (root / p).read_bytes() for p in ('usr/local/sbin/2pny-display-core', 'usr/share/2pny/protocols.html', 'usr/share/2pny/expert.html')}
            cp = run(root, binary, arch)
            assert cp.returncode == 0, cp.stderr
            assert f'PATCH_504_OFFLINE_OK {arch}' in cp.stdout
            assert (root / 'etc/2pny/version').read_text() == '5.04.000\n'
            assert (root / 'usr/local/bin/2pnyd.pre-5.04').read_bytes() == b'old-daemon'
            for path, original in before.items():
                assert (root / (path + '.pre-5.04')).read_bytes() == original
            core = (root / 'usr/local/sbin/2pny-display-core').read_text()
            assert 'kind in ("oled","lcd")' in core and 'LCD.render=_lcd.render' in core and 'OLED.render=_oled.render' in core
            compile(core, 'core', 'exec')
            for page, marker, js in (('protocols.html', 'id="identity504"', 'idSave'), ('expert.html', 'id="console504"', 'consoleAll')):
                html = (root / 'usr/share/2pny' / page).read_text()
                assert html.count(marker) == 1 and html.count('</main>') == 1 and html.count('</body>') == 1 and js in html
            assert (root / 'usr/local/sbin/2pny-identity-apply').stat().st_mode & 0o111
            assert (root / 'usr/local/libexec/pu2pny/expert-cmd-504.py').stat().st_mode & 0o111
            assert run(root, binary, arch).returncode != 0, 'overlay must not be re-applicable'
            # JavaScript syntax of both injected scripts.
            if subprocess.run(['which', 'node'], capture_output=True).returncode == 0:
                for page in ('protocols.html', 'expert.html'):
                    html = (root / 'usr/share/2pny' / page).read_text()
                    for i, s in enumerate(re.findall(r'<script>(.*?)</script>', html, re.S)):
                        f = Path(rd) / f'{page}.{i}.js'; f.write_text(s)
                        r = subprocess.run(['node', '--check', str(f)], capture_output=True, text=True)
                        assert r.returncode == 0, (page, i, r.stderr)
with tempfile.TemporaryDirectory() as td:
    binary = Path(td) / 'd'; binary.write_bytes(b'\0' * 1_200_000)
    assert run(make_root(td + '/a', '5.02.001'), binary).returncode != 0
    root = make_root(td + '/b'); p = root / 'usr/share/2pny/expert.html'; p.write_text(p.read_text().replace('</main>', '</main></main>'))
    assert run(root, binary).returncode != 0
    small = Path(td) / 's'; small.write_bytes(b'x')
    assert run(make_root(td + '/c'), small).returncode != 0
print('TEST_504_OVERLAY_OK')
