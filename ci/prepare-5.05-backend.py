#!/usr/bin/env python3
"""Reconstruct the 5.04 backend and add only the 5.05 OLED/LCD type route."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
subprocess.run([sys.executable, str(repo/'ci/prepare-5.04-backend.py'), str(out)], check=True)
main = out/'main.go'
text = main.read_text()
for old, new in (
    ('appVersion            = "5.04.000"', 'appVersion            = "5.05.000"'),
    ('http.HandleFunc("/api/expert/cmd", expert504Handler)',
     'http.HandleFunc("/api/expert/cmd", expert504Handler)\n\thttp.HandleFunc("/api/oled/config", oled505Handler)'),
):
    if text.count(old) != 1:
        raise SystemExit('unexpected baseline anchor: '+old)
    text = text.replace(old, new, 1)
main.write_text(text)
(out/'web505.go').write_bytes((repo/'runtime/5.05/web.go').read_bytes())
print('PREPARE_505_BACKEND_OK')
