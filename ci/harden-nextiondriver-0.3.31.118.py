#!/usr/bin/env python3
"""0.3.31.118: preserve 0.3.31.117 hardening and relocate ON7LDS PTY link.

The upstream NextionDriver hard-codes /dev/ttyNextionDriver. PU2PNY runs the
compatibility driver unprivileged (User=mmdvm), so the link must live in the
systemd RuntimeDirectory owned by that user. This keeps the service non-root
and matches the path already consumed by 2pny-display-apply.
"""
from pathlib import Path
import re
import subprocess
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: harden-nextiondriver-0.3.31.118.py <NextionDriver checkout>")

repo = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1]).resolve()
base = repo / "ci/harden-nextiondriver-0.3.31.117.py"
subprocess.run([sys.executable, str(base), str(root)], check=True)

header = root / "NextionDriver.h"
if not header.is_file():
    raise SystemExit("missing upstream NextionDriver.h")
text = header.read_text()
pattern = r'(?m)^#define\s+NEXTIONDRIVERLINK\s+"/dev/ttyNextionDriver"\s*$'
replacement = '#define NEXTIONDRIVERLINK\t\t"/run/2pny-nextiondriver/ttyNextionDriver"'
text, count = re.subn(pattern, replacement, text, count=1)
if count != 1:
    raise SystemExit("upstream NEXTIONDRIVERLINK anchor missing/ambiguous")
header.write_text(text)

runtime_link = "/run/2pny-nextiondriver/ttyNextionDriver"
old_link = "/dev/ttyNextionDriver"
source = "\n".join(p.read_text(errors="ignore") for p in sorted(root.glob("*.[ch]")))
if runtime_link not in source:
    raise SystemExit("runtime PTY link not present after patch")
if old_link in source:
    raise SystemExit("legacy /dev NextionDriver link still present in source")

print("NEXTIONDRIVER_0331118_RUNTIME_LINK_OK")
