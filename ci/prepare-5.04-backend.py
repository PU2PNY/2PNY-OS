#!/usr/bin/env python3
"""Reconstruct the 5.02 backend and add only the 5.04 routes (identity, expert diagnostics)."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
subprocess.run([sys.executable, str(repo/'ci/prepare-5.02-backend.py'), str(out)], check=True)
main = out/'main.go'
text = main.read_text()
for old, new in (
    ('appVersion            = "5.02.000"', 'appVersion            = "5.04.000"'),
    ('http.HandleFunc("/api/expert/reset", reset502Handler)',
     'http.HandleFunc("/api/expert/reset", reset502Handler)\n\thttp.HandleFunc("/api/identity/apply", identity504Handler)\n\thttp.HandleFunc("/api/expert/cmd", expert504Handler)'),
):
    if text.count(old) != 1:
        raise SystemExit('unexpected baseline anchor: '+old)
    text = text.replace(old, new, 1)
main.write_text(text)
(out/'web.go').write_bytes((repo/'runtime/5.04/web.go').read_bytes())
print('PREPARE_504_BACKEND_OK')
