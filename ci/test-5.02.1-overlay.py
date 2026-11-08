#!/usr/bin/env python3
"""Offline test of ci/patch-image-5.02.1.py against a fake 5.02 root.

The fake root is built from the files as they were in the published 5.02 source
(git commit eec7a9f), so the overlay is exercised against the real "before" text.
SW-level: proves the overlay result, not hardware behavior.
"""
import importlib.util
import subprocess
from importlib.machinery import SourceFileLoader
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'eec7a9f7f5e81b90e18e30021c754673ad97a50f'
PATCH = ROOT / 'ci/patch-image-5.02.1.py'


def base_file(rel):
    cp = subprocess.run(['git', 'show', f'{BASE_COMMIT}:{rel}'], cwd=ROOT, capture_output=True)
    assert cp.returncode == 0, f'{rel} missing in {BASE_COMMIT}: {cp.stderr.decode()}'
    return cp.stdout


def make_root(td, version='5.02.000'):
    root = Path(td) / 'root'
    for rel, source in (('usr/local/sbin/2pny-display-apply', 'runtime/display/apply.py'),
                        ('usr/local/sbin/2pny-wifi-apply', 'runtime/5x/2pny-wifi-apply.py')):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(base_file(source))
    (root / 'etc/2pny').mkdir(parents=True)
    (root / 'etc/2pny/version').write_text(version + '\n')
    (root / 'etc/systemd/system/multi-user.target.wants').mkdir(parents=True)
    return root


def run_patch(root, arch):
    return subprocess.run([sys.executable, '-I', str(PATCH), str(root), arch], capture_output=True, text=True)


def load(path):
    # The installed file has no .py suffix, so name the loader explicitly.
    loader = SourceFileLoader('patched_display_apply', str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


for arch in ('arm32', 'arm64'):
    with tempfile.TemporaryDirectory(prefix='pu2pny-50201-') as td:
        root = make_root(td)
        before_display = (root / 'usr/local/sbin/2pny-display-apply').read_bytes()
        before_wifi = (root / 'usr/local/sbin/2pny-wifi-apply').read_bytes()
        cp = run_patch(root, arch)
        assert cp.returncode == 0, cp.stderr
        assert f'PATCH_50201_OFFLINE_OK {arch}' in cp.stdout
        assert (root / 'etc/2pny/version').read_text() == '5.02.001\n'
        # Forensic rollback copies preserve the exact previous files.
        assert (root / 'usr/local/sbin/2pny-display-apply.pre-5.02.1').read_bytes() == before_display
        assert (root / 'usr/local/sbin/2pny-wifi-apply.pre-5.02.1').read_bytes() == before_wifi
        # DISPLAY-045 behavior in the patched file.
        mod = load(root / 'usr/local/sbin/2pny-display-apply')
        saved = {'enabled': True, 'type': 'nextion_mmdvm', 'requested_layout': 3}
        candidate = {'class': 'display_candidate', 'state': 'mmdvm_display_candidate', 'port': 'modem'}
        assert mod.select_persisted_modem_display(candidate, saved, {})['class'] == 'nextion_mmdvm'
        i2c = {'class': 'display_candidate', 'state': 'i2c_candidate', 'address': '0x3c'}
        assert mod.select_persisted_modem_display(i2c, saved, {}) == i2c
        assert mod.select_persisted_modem_display({'class': 'oled'}, saved, {}) == {'class': 'oled'}
        assert mod.select_persisted_modem_display(candidate, saved, {'enabled': False}) == candidate
        # NET-045 in the patched file and the reconcile installation.
        wifi = (root / 'usr/local/sbin/2pny-wifi-apply').read_text()
        assert wifi.count('"connection.autoconnect-retries", "0"') == 2
        assert (root / 'usr/local/sbin/2pny-wifi-retry-reconcile').stat().st_mode & 0o111
        unit = root / 'etc/systemd/system/2pny-wifi-retry-reconcile.service'
        assert 'ExecStart=/usr/bin/python3 /usr/local/sbin/2pny-wifi-retry-reconcile' in unit.read_text()
        link = root / 'etc/systemd/system/multi-user.target.wants/2pny-wifi-retry-reconcile.service'
        assert link.is_symlink() and link.readlink().as_posix() == '../2pny-wifi-retry-reconcile.service'
        # Running the overlay twice must abort rather than stack changes.
        again = run_patch(root, arch)
        assert again.returncode != 0, 'overlay must not be re-applicable'

# Refuse an unexpected base version and an unexpected base file shape.
with tempfile.TemporaryDirectory(prefix='pu2pny-50201-') as td:
    assert run_patch(make_root(td, '5.01.002'), 'arm64').returncode != 0
with tempfile.TemporaryDirectory(prefix='pu2pny-50201-') as td:
    root = make_root(td)
    (root / 'usr/local/sbin/2pny-display-apply').write_text('# unexpected base file\n')
    assert run_patch(root, 'arm32').returncode != 0

print('TEST_50201_OVERLAY_OK')
