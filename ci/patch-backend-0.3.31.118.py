#!/usr/bin/env python3
"""0.3.31.118 backend: reuse DISPLAY-025 policy byte-for-byte, change version only."""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 3:
    raise SystemExit('usage: patch-backend-0.3.31.118.py <input.go> <output.go>')
repo=Path(__file__).resolve().parents[1]
with tempfile.NamedTemporaryFile(prefix='2pnyd-031117-',suffix='.go',delete=False) as f:
    tmp=Path(f.name)
try:
    subprocess.run([sys.executable,str(repo/'ci/patch-backend-0.3.31.117.py'),sys.argv[1],str(tmp)],check=True)
    s=tmp.read_text()
    old='appVersion            = "0.3.31.117"'
    new='appVersion            = "0.3.31.118"'
    if s.count(old)!=1:
        raise SystemExit('0.3.31.117 version anchor missing/ambiguous')
    s=s.replace(old,new,1)
    Path(sys.argv[2]).write_text(s)
finally:
    tmp.unlink(missing_ok=True)
print('BACKEND_0331118_VERSION_ONLY_OK')
