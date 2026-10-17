#!/usr/bin/env python3
"""Build 5.00.000 backend source from the protected 4.00.001 backend patch chain.

This intentionally changes only the application version in M0/M1. Runtime
managers are separate components; existing approved web behavior is preserved.
"""
from __future__ import annotations
import subprocess, sys, tempfile
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch-backend-5.00.000.py <base-go> <output-go>")
repo = Path(__file__).resolve().parents[1]
base = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
with tempfile.TemporaryDirectory(prefix="pu2pny-500000-backend-") as td:
    intermediate = Path(td) / "main-4.00.001.go"
    subprocess.run([sys.executable, str(repo / "ci/patch-backend-4.00.001.py"), str(base), str(intermediate)], check=True)
    text = intermediate.read_text()
old = 'appVersion            = "4.00.001"'
new = 'appVersion            = "5.00.000"'
if text.count(old) != 1:
    raise SystemExit(f"protected appVersion anchor count={text.count(old)}")
text = text.replace(old, new, 1)
out.write_text(text)
print("PATCH_BACKEND_500000_OK")
