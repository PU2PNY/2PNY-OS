#!/usr/bin/env python3
"""Offline 5.04 overlay on the published 5.03 image.

DISPLAY-054 (paged LCD), IDENTITY-054 (callsign/DMR ID), EXPERT-054 (one-click diagnostics).
Never runs target binaries and never touches RF configuration, MMDVMHost, gateways,
NextionDriver, MMDVM-Display or the profile autostart. Every text edit must match exactly once.
"""
import shutil
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
repo = Path(__file__).resolve().parents[1]
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.03.000'
assert binary.is_file() and binary.stat().st_size > 1000000


def backup(path):
    src, dst = root/path, root/(path + '.pre-5.04')
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)


def replace(path, old, new):
    p = root/path
    text = p.read_text()
    assert text.count(old) == 1, (path, old[:70], text.count(old))
    p.write_text(text.replace(old, new, 1))


def install(source, destination, mode):
    p = root/destination
    assert not p.exists()
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo/source, p)
    p.chmod(mode)


# Backend with the two new routes (cross-built by the pipeline).
backup('usr/local/bin/2pnyd')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)

install('runtime/5.04/identity-apply.py', 'usr/local/sbin/2pny-identity-apply', 0o755)
install('runtime/5.04/expert-cmd.py', 'usr/local/libexec/pu2pny/expert-cmd-504.py', 0o755)
install('runtime/5.04/lcd.py', 'usr/local/libexec/pu2pny/lcd-504.py', 0o644)

# DISPLAY-054: LCD pages need the same 4-second cadence the OLED already has.
core = 'usr/local/sbin/2pny-display-core'
backup(core)
replace(core, '(int(now//4) if kind=="oled" else int(now//60))', '(int(now//4) if kind in ("oled","lcd") else int(now//60))')
replace(core, '    OLED.render=_oled.render\n    main()',
        '    OLED.render=_oled.render\n'
        '    _lspec=importlib.util.spec_from_file_location("lcd504","/usr/local/libexec/pu2pny/lcd-504.py")\n'
        '    _lcd=importlib.util.module_from_spec(_lspec)\n'
        '    _lspec.loader.exec_module(_lcd)\n'
        '    LCD.render=_lcd.render\n'
        '    main()')

# IDENTITY-054: card on the Protocols page.
proto = 'usr/share/2pny/protocols.html'
backup(proto)
replace(proto, '</main>', (repo/'runtime/5.04/protocols-identity.html').read_text() + '</main>')
replace(proto, '</body>', '<script>' + (repo/'runtime/5.04/protocols-identity.js').read_text() + '</script></body>')

# EXPERT-054: one-click diagnostics card.
expert = 'usr/share/2pny/expert.html'
backup(expert)
replace(expert, '</main>', (repo/'runtime/5.04/expert-console.html').read_text() + '</main>')
replace(expert, '</body>', '<script>' + (repo/'runtime/5.04/expert-console.js').read_text() + '</script></body>')

for filename in ('usr/local/sbin/2pny-identity-apply', 'usr/local/libexec/pu2pny/expert-cmd-504.py',
                 'usr/local/libexec/pu2pny/lcd-504.py', core):
    compile((root/filename).read_bytes(), filename, 'exec')
(root/'etc/2pny/version').write_text('5.04.000\n')
print('PATCH_504_OFFLINE_OK', arch)
