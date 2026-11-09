#!/usr/bin/env python3
"""Reconstruct the 5.06 backend; add the cached dashboard unit states (SPEED-057).
Optional second argument `arm32` renames every pu2pny.local to pu2pny32.local (HOST-057)."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2] if len(sys.argv) > 2 else 'arm64'
assert arch in ('arm32', 'arm64')
subprocess.run([sys.executable, str(repo/'ci/prepare-5.06-backend.py'), str(out)], check=True)
main = out/'main.go'
text = main.read_text()
if text.count('appVersion            = "5.06.000"') != 1:
    raise SystemExit('unexpected baseline anchor: version')
text = text.replace('appVersion            = "5.06.000"', 'appVersion            = "5.07.000"', 1)
start = text.index('func dashboardDataHandler(')
end = text.index('\nfunc ', start + 10)
body = text[start:end]
if body.count('serviceActive(') < 10:
    raise SystemExit('unexpected dashboard handler')
text = text[:start] + body.replace('serviceActive(', 'serviceActiveCached(') + text[end:]
if arch == 'arm32':
    if text.count('pu2pny.local') < 6:
        raise SystemExit('unexpected host name count')
    text = text.replace('pu2pny.local', 'pu2pny32.local')
main.write_text(text)
(out/'web507.go').write_bytes((repo/'runtime/5.07/web.go').read_bytes())
print('PREPARE_507_BACKEND_OK', arch)
