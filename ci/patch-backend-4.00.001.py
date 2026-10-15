#!/usr/bin/env python3
"""PU2PNY-OS 4.00.001 surgical backend overlay.

Builds on the immutable 4.00.000 backend patch chain.  The only runtime-source
change is PERF-051: lower idle filesystem polling frequency for the live-state
watcher.  No RF/protocol/gateway semantics are changed here.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 3:
    raise SystemExit("usage: patch-backend-4.00.001.py <input-go> <output-go>")

repo = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
base = repo / "ci/patch-backend-4.00.000.py"

with tempfile.TemporaryDirectory(prefix="pu2pny-400001-") as td:
    staged = Path(td) / "main.go"
    subprocess.run([sys.executable, str(base), str(src), str(staged)], check=True)
    text = staged.read_text()

if text.count('appVersion            = "4.00.000"') != 1:
    raise SystemExit("4.00.000 appVersion anchor missing/ambiguous")
text = text.replace('appVersion            = "4.00.000"', 'appVersion            = "4.00.001"', 1)

# PERF-051: the live snapshot file is already de-duplicated before publish.
# Halving stat polling from 12.5/s to 6.25/s lowers idle syscall/wakeup pressure
# on ARMv6 while adding at most ~80 ms to file-change observation.  This is a
# bounded scheduler change only; SSE/API semantics remain untouched.
old = "\t\ttime.Sleep(80 * time.Millisecond)"
new = "\t\ttime.Sleep(160 * time.Millisecond)"
if text.count(old) != 1:
    raise SystemExit("live watcher polling anchor missing/ambiguous")
text = text.replace(old, new, 1)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text)
print("PATCH_BACKEND_400001_OK")
