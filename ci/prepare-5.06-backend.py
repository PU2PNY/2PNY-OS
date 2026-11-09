#!/usr/bin/env python3
"""Reconstruct the 5.05 backend and add only the 5.06 browser clock route."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
subprocess.run([sys.executable, str(repo/'ci/prepare-5.05-backend.py'), str(out)], check=True)
main = out/'main.go'
text = main.read_text()
for old, new in (
    ('appVersion            = "5.05.000"', 'appVersion            = "5.06.000"'),
    ('http.HandleFunc("/api/oled/config", oled505Handler)',
     'http.HandleFunc("/api/oled/config", oled505Handler)\n\thttp.HandleFunc("/api/clock/browser", clock506Handler)'),
):
    if text.count(old) != 1:
        raise SystemExit('unexpected baseline anchor: '+old)
    text = text.replace(old, new, 1)
main.write_text(text)
(out/'web506.go').write_bytes((repo/'runtime/5.06/web.go').read_bytes())
print('PREPARE_506_BACKEND_OK')
