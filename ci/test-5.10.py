#!/usr/bin/env python3
"""CLOCK-060 / DIRECT-060 / BOOT-060 / UI-060 / EXPERT-060 software tests and the 5.04 -> 5.10 overlay chain."""
import os, re, struct, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
prefix = (ROOT/'ci/test-5.09.py').read_text().split("# the chain helper")[0]
ns = {'__file__': str(ROOT/'ci/test-5.09.py')}
exec(prefix, ns)
make_root, chain509 = ns['make_root'], ns['chain509']
node = subprocess.run(['which', 'node'], capture_output=True, text=True).stdout.strip()


def fake_elf(cls, machine):
    head = bytearray(64); head[:4] = b'\x7fELF'; head[4] = cls; head[5] = 1
    struct.pack_into('<H', head, 18, machine)
    return bytes(head) + b'\0' * 2048


def build_root(td, name, arch, core=fake_elf(2, 183)):
    root = make_root(td + '/' + name)
    (root/'usr/local/bin/2pny-direct-core').write_bytes(core)
    binary = Path(td)/'d'; binary.write_bytes(b'\0'*1_200_000)
    chain509(root, arch, binary)
    return root, binary


def patch510(root, arch, binary, *extra):
    return subprocess.run([sys.executable, '-I', str(ROOT/'ci/patch-image-5.10.py'), str(root), arch, str(binary), *map(str, extra)], capture_output=True, text=True)


with tempfile.TemporaryDirectory() as td:
    core32 = Path(td)/'core32'; core32.write_bytes(fake_elf(1, 40))
    wrong = Path(td)/'wrong'; wrong.write_bytes(fake_elf(2, 183))
    for arch in ('arm64', 'arm32'):
        root, binary = build_root(td, arch, arch)
        before_proto = (root/'usr/share/2pny/protocols.html').read_text()
        cp = patch510(root, arch, binary, *([core32] if arch == 'arm32' else []))
        assert cp.returncode == 0, (arch, cp.stderr[-800:])
        assert (root/'etc/2pny/version').read_text() == '5.10.000\n'
        d = root/'etc/systemd/system'
        assert 'ReadWritePaths=/etc' in (d/'2pny-timezone-apply.service.d/60-etc.conf').read_text()
        direct = (d/'2pny-direct.service.d/60-restart.conf').read_text()
        assert 'StartLimitBurst=4' in direct and 'StartLimitIntervalSec=900' in direct and 'RestartSec=30' in direct
        for unit in ('2pny-auto-maintenance', '2pny-hostfiles-update'):
            text = (d/f'{unit}.service.d/60-delay.conf').read_text()
            assert 'ExecStartPre=/bin/sleep 300' in text and 'TimeoutStartSec=' in text
        head = (root/'usr/local/bin/2pny-direct-core').read_bytes()[:20]
        assert (head[4], struct.unpack('<H', head[18:20])[0]) == ((1, 40) if arch == 'arm32' else (2, 183))
        assert ((root/'usr/local/bin/2pny-direct-core.pre-5.10').exists()) == (arch == 'arm32')
        ui = (root/'usr/share/2pny/ui-language.js').read_text()
        assert "/brand/logo-mark.png" in ui and "/brand/logo.png'" not in ui and "),30],[" in ui
        assert (root/'usr/share/2pny/brand/logo-mark.png').read_bytes()[:4] == b'\x89PNG'
        proto = (root/'usr/share/2pny/protocols.html').read_text()
        assert proto.count('href="#identity504"') == 1 and 'id="identity504"' in proto
        assert proto.count('<div') - proto.count('</div>') == before_proto.count('<div') - before_proto.count('</div>')
        assert 'ls\', \'-ln\', \'/etc/NetworkManager/system-connections' in (root/'usr/local/libexec/pu2pny/expert-cmd-504.py').read_text()
        if node:
            f = Path(td)/'ui.js'; f.write_text(ui)
            assert subprocess.run([node, '--check', str(f)], capture_output=True).returncode == 0
        for pre in ('usr/share/2pny/protocols.html', 'usr/share/2pny/ui-language.js', 'usr/local/libexec/pu2pny/expert-cmd-504.py'):
            assert (root/(pre + '.pre-5.10')).exists(), pre
    # refusals
    root, binary = build_root(td, 'r1', 'arm32')
    assert patch510(root, 'arm32', binary).returncode != 0, 'arm32 without the ARMv6 core is refused'
    root, binary = build_root(td, 'r2', 'arm32')
    cp = patch510(root, 'arm32', binary, wrong)
    assert cp.returncode != 0 and 'AssertionError' in cp.stderr, 'a 64-bit replacement is refused'
    root, binary = build_root(td, 'r3', 'arm32', core=fake_elf(1, 40))
    assert patch510(root, 'arm32', binary, core32).returncode != 0, 'only the AArch64 baseline may be replaced'
    root, binary = build_root(td, 'r4', 'arm64')
    (root/'usr/share/2pny/protocols.html').write_text((root/'usr/share/2pny/protocols.html').read_text().replace('currentProto', 'x'))
    assert patch510(root, 'arm64', binary).returncode != 0, 'anchor mismatch is refused'

# the real Direct source builds for ARMv6 and passes its self-test natively
src = ROOT/'src/direct-core'
files = [str(src/n) for n in ('direct_types.go', 'direct_session.go', 'direct_transport.go', 'direct_radio.go', 'direct_main.go')]
env = dict(os.environ, GO111MODULE='off', CGO_ENABLED='0', GOOS='linux')
with tempfile.TemporaryDirectory() as td:
    arm = Path(td)/'core-arm'
    cp = subprocess.run(['go', 'build', '-trimpath', '-o', str(arm), *files], env=dict(env, GOARCH='arm', GOARM='6'), capture_output=True, text=True)
    assert cp.returncode == 0, cp.stderr[-500:]
    head = arm.read_bytes()[:20]
    assert (head[4], struct.unpack('<H', head[18:20])[0]) == (1, 40)
    host = Path(td)/'core-host'
    cp = subprocess.run(['go', 'build', '-o', str(host), *files], env=dict(env, GOARCH=subprocess.check_output(['go', 'env', 'GOARCH'], text=True).strip()), capture_output=True, text=True)
    assert cp.returncode == 0, cp.stderr[-500:]
    assert 'DIRECT_SELFTEST_OK' in subprocess.run([str(host), '--selftest'], capture_output=True, text=True).stdout

for arch in ('arm64', 'arm32'):
    with tempfile.TemporaryDirectory() as td:
        cp = subprocess.run([sys.executable, str(ROOT/'ci/prepare-5.10-backend.py'), td, arch], capture_output=True, text=True)
        assert cp.returncode == 0, cp.stderr[-500:]
        assert 'appVersion            = "5.10.000"' in (Path(td)/'main.go').read_text()
print('TEST_510_OK')
