#!/usr/bin/env python3
"""Fail-closed offline 5.03 overlay onto verified 5.02.1 image."""
import shutil
import sys
from pathlib import Path

root, arch = Path(sys.argv[1]).resolve(), sys.argv[2]
repo = Path(__file__).resolve().parents[1]
assert arch in ('arm32','arm64') and root != Path('/')
assert (root/'etc/2pny/version').read_text().strip() == '5.02.001'

def upgrade(target, source):
    installed = root/target
    backup = root/(target + '.pre-5.03')
    assert installed.is_file() and not backup.exists()
    previous = installed.read_text()
    if target.endswith('oled-502.py'):
        assert previous == (repo/'runtime/5.02/oled.py').read_text(), 'unexpected OLED baseline'
    else:
        assert 'for gateway in GATEWAYS:' in previous and '2pny-profile-autostart' in previous, 'unexpected autostart baseline'
    shutil.copy2(installed,backup)
    shutil.copyfile(repo/source,installed)
    installed.chmod(0o755)
    compile(installed.read_bytes(),target,'exec')

upgrade('usr/local/sbin/2pny-profile-autostart-safe','runtime/5.03/profile-autostart-safe.py')
unit=root/'etc/systemd/system/2pny-profile-autostart-retry.path'
assert not unit.exists() and not unit.is_symlink()
assert (root/'etc/systemd/system/2pny-profile-autostart-retry.service').is_file()
unit.write_bytes((repo/'runtime/5.03/2pny-profile-autostart-retry.path').read_bytes())
unit.chmod(0o644)
link=root/'etc/systemd/system/paths.target.wants/2pny-profile-autostart-retry.path'
assert not link.exists() and not link.is_symlink()
link.parent.mkdir(parents=True,exist_ok=True)
link.symlink_to('../2pny-profile-autostart-retry.path')
upgrade('usr/local/libexec/pu2pny/oled-502.py','runtime/5.03/oled.py')
(root/'etc/2pny/version').write_text('5.03.000\n')
print('PATCH_503_OFFLINE_OK',arch)
