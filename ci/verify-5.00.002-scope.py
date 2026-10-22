#!/usr/bin/env python3
"""Fail closed if image content changes outside authorized display/version paths."""
import sys
from pathlib import Path

def load(path):
    return {line.split('  ', 1)[1]: line.split('  ', 1)[0] for line in Path(path).read_text().splitlines()}

before, after = map(load, sys.argv[1:])
allowed = {
 './usr/local/sbin/2pny-display-apply', './usr/local/sbin/2pny-display-apply.pre-5.00.002',
 './usr/local/bin/2pnyd', './etc/2pny/version', './usr/share/2pny/display.html',
 './etc/systemd/system/2pny-nextiondriver.service', './etc/systemd/system/2pny-display-adapter.service',
 './etc/systemd/system/2pny-display.service.d/official-renderer.conf',
}
for path in sorted(before.keys() | after.keys()):
    if before.get(path) == after.get(path):
        continue
    if path not in allowed and not path.startswith('./usr/local/libexec/pu2pny/display/') and not path.startswith('./usr/local/sbin/__pycache__/2pny-display-apply'):
        raise SystemExit('Unauthorized image modification: '+path)
    print('DISPLAY_SCOPE_CHANGE', path)
assert before['./usr/local/bin/MMDVM-Host'] == after['./usr/local/bin/MMDVM-Host']
print('DISPLAY_ONLY_FULL_MANIFEST_PASS')
