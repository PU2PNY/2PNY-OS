#!/usr/bin/env python3
"""Offline 5.05 overlay on the published 5.04 image.

DISPLAY-055: find and start the I2C OLED/LCD (bus scan + explicit type), add MMDVM modem and
Raspberry system rows to OLED and LCD. Never touches RF configuration, MMDVMHost, gateways,
NextionDriver, MMDVM-Display, the probe or the profile autostart. Edits must match exactly once.
"""
import shutil
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
repo = Path(__file__).resolve().parents[1]
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.04.000'
assert binary.is_file() and binary.stat().st_size > 1000000


def backup(path):
    src, dst = root/path, root/(path + '.pre-5.05')
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)


def replace(path, old, new):
    p = root/path
    text = p.read_text()
    assert text.count(old) == 1, (path, old[:70], text.count(old))
    p.write_text(text.replace(old, new, 1))


def upgrade(target, source, expected_source, mode):
    """Replace an installed module only if it is exactly the file the previous release shipped."""
    installed = root/target
    assert installed.read_text() == (repo/expected_source).read_text(), 'unexpected baseline: ' + target
    backup(target)
    shutil.copyfile(repo/source, installed)
    installed.chmod(mode)


backup('usr/local/bin/2pnyd')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)

i2c = root/'usr/local/libexec/pu2pny/i2c-505.py'
assert not i2c.exists()
shutil.copyfile(repo/'runtime/5.05/i2c.py', i2c)
i2c.chmod(0o644)
upgrade('usr/local/libexec/pu2pny/oled-502.py', 'runtime/5.05/oled.py', 'runtime/5.03/oled.py', 0o755)
upgrade('usr/local/libexec/pu2pny/lcd-504.py', 'runtime/5.05/lcd.py', 'runtime/5.04/lcd.py', 0o644)

core = 'usr/local/sbin/2pny-display-core'
backup(core)
replace(core, '    if settings.get("enabled") is False:return None,"disabled"\n',
        '    if settings.get("enabled") is False:return None,"disabled"\n'
        '    # DISPLAY-055: a plain I2C OLED/LCD never appears in the probe, and a present MMDVM turns the\n'
        '    # unproven display into "Nextion through the modem". Scan the bus; never override a proven Nextion.\n'
        '    _found=_I2C505.choose(d,hw,settings)\n'
        '    if _found:d=dict(d,**_found);cls=str(d.get("class") or "");state=str(d.get("state") or "")\n')
replace(core, 'resolution=str(settings.get("resolution") or d.get("resolution") or "128x64").lower()',
        'resolution=str((d.get("resolution") if state=="i2c_scan" else None) or settings.get("resolution") or d.get("resolution") or "128x64").lower()')
replace(core, 'cols=int(settings.get("lcd_cols") or 20);rows=int(settings.get("lcd_rows") or 4)',
        'cols=int((d.get("lcd_cols") if state=="i2c_scan" else None) or settings.get("lcd_cols") or 20);'
        'rows=int((d.get("lcd_rows") if state=="i2c_scan" else None) or settings.get("lcd_rows") or 4)')
replace(core, '    LCD.render=_lcd.render\n    main()',
        '    LCD.render=_lcd.render\n'
        '    _ispec=importlib.util.spec_from_file_location("i2c505","/usr/local/libexec/pu2pny/i2c-505.py")\n'
        '    _I2C505=importlib.util.module_from_spec(_ispec)\n'
        '    _ispec.loader.exec_module(_I2C505)\n'
        '    main()')

upgrade('usr/local/libexec/pu2pny/expert-cmd-504.py', 'runtime/5.05/expert-cmd.py', 'runtime/5.04/expert-cmd.py', 0o755)

expert = 'usr/share/2pny/expert.html'
backup(expert)
replace(expert, '</main>', (repo/'runtime/5.05/oled-card.html').read_text() + '</main>')
replace(expert, '</body>', '<script>' + (repo/'runtime/5.05/oled-card.js').read_text() + '</script></body>')

for filename in ('usr/local/libexec/pu2pny/i2c-505.py', 'usr/local/libexec/pu2pny/oled-502.py',
                 'usr/local/libexec/pu2pny/lcd-504.py', 'usr/local/libexec/pu2pny/expert-cmd-504.py', core):
    compile((root/filename).read_bytes(), filename, 'exec')
(root/'etc/2pny/version').write_text('5.05.000\n')
print('PATCH_505_OFFLINE_OK', arch)
