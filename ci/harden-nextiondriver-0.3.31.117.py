#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: harden-nextiondriver-0.3.31.117.py <NextionDriver checkout>")
root = Path(sys.argv[1]).resolve()
main = root / "NextionDriver.c"
helpers = root / "helpers.c"
for p in (main, helpers):
    if not p.is_file():
        raise SystemExit(f"missing upstream source: {p}")

s = main.read_text()
start_marker = '                if ((RXbuffer[1]<0xF2)&&(received>2)&&(received<200)) {'
end_marker = '                        response=RXbuffer[1];\n                    }\n'
if s.count(start_marker) != 1:
    raise SystemExit("unsafe HMI command block anchor missing/ambiguous")
start = s.index(start_marker)
end = s.index(end_marker, start) + len(end_marker)
safe = '''                if ((RXbuffer[1]<0xF2)&&(received>2)&&(received<200)) {
                    /* PU2PNY-OS SECURITY: HMI payloads are data, never host shell. */
                    writelog(LOG_WARNING,"PU2PNY-OS blocked HMI host-command request");
                    snprintf(TXbuffer, sizeof(TXbuffer), "msg.txt=\\\"Host command blocked\\\"");
                    sendCommand(TXbuffer);
                    response=RXbuffer[1];
                }
'''
s = s[:start] + safe + s[end:]

# A display must never be able to initiate a TFT/HMI flash by itself. Upstream
# has two HMI command paths that call updateDisplay(); both are neutralized.
flash_calls = s.count('updateDisplay();')
if flash_calls != 2:
    raise SystemExit(f"expected exactly two HMI updateDisplay call sites, found {flash_calls}")
s = s.replace('updateDisplay();', 'writelog(LOG_WARNING,"PU2PNY-OS blocked HMI/TFT update request");')
main.write_text(s)

h = helpers.read_text()
needle = 'ok=system(cmd);'
count = h.count(needle)
if count != 2:
    raise SystemExit(f"expected exactly two upstream wget/system calls, found {count}")
h = h.replace(needle, 'ok=-1; writelog(LOG_WARNING,"PU2PNY-OS: external DB download disabled; use OS-managed pinned data");')
helpers.write_text(h)

# Security gate: the hardened source set must contain no shell execution primitive.
unsafe = []
for p in sorted(root.glob('*.c')):
    text = p.read_text(errors='ignore')
    for pat in (r'\bsystem\s*\(', r'\bpopen\s*\('):
        if re.search(pat, text):
            unsafe.append(f"{p.name}:{pat}")
if unsafe:
    raise SystemExit("unsafe shell execution remains: " + ", ".join(unsafe))

if 'updateDisplay();' in main.read_text():
    raise SystemExit("automatic updateDisplay call site still present")

print("NEXTIONDRIVER_0331117_HARDENED_OK")
