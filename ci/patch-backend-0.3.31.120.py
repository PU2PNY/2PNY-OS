#!/usr/bin/env python3
"""0.3.31.120 backend: preserve 0.3.31.119 display policy and bump version only."""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 3:
    raise SystemExit('usage: patch-backend-0.3.31.120.py <input.go> <output.go>')
repo = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1])
out = Path(sys.argv[2])
with tempfile.NamedTemporaryFile(prefix='2pny-0331120-', suffix='.go', delete=False) as f:
    tmp = Path(f.name)
try:
    subprocess.run([sys.executable, str(repo/'ci/patch-backend-0.3.31.119.py'), str(src), str(tmp)], check=True)
    s = tmp.read_text()
finally:
    tmp.unlink(missing_ok=True)
old = 'appVersion            = "0.3.31.119"'
if s.count(old) != 1:
    raise SystemExit(f'version anchor count={s.count(old)}')
s = s.replace(old, 'appVersion            = "0.3.31.120"', 1)
out.write_text(s)
print('BACKEND_0331120_VERSION_OK')
