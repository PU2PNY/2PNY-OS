#!/usr/bin/env python3
"""Reconstruct the 5.09 backend and only change the version string to 5.10.000. Second argument `arm32` is passed through."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2] if len(sys.argv) > 2 else 'arm64'
assert arch in ('arm32', 'arm64')
subprocess.run([sys.executable, str(repo/'ci/prepare-5.09-backend.py'), str(out), arch], check=True)
main = out/'main.go'
text = main.read_text()
if text.count('appVersion            = "5.09.000"') != 1:
    raise SystemExit('unexpected baseline anchor: version')
main.write_text(text.replace('appVersion            = "5.09.000"', 'appVersion            = "5.10.000"', 1))
print('PREPARE_510_BACKEND_OK', arch)
