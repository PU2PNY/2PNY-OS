#!/usr/bin/env python3
"""Change only the SSID in the existing hostapd template, never its credentials."""
from pathlib import Path
import re, sys
root=Path(sys.argv[1]).resolve()
arch=sys.argv[2]
if arch not in ("arm32","arm64"): raise SystemExit("invalid architecture")
path=root/"usr/share/2pny/network/hostapd.template"
raw=path.read_bytes()
ssid=f"pu2pny-{'32' if arch=='arm32' else '64'}".encode()
match=list(re.finditer(rb"(?m)^ssid=[^\r\n]*$",raw))
if len(match)!=1: raise SystemExit("hostapd template must contain exactly one SSID")
before=match[0].group()
assert before.startswith(b"ssid=")
new=raw[:match[0].start()]+b"ssid="+ssid+raw[match[0].end():]
assert new.replace(b"ssid="+ssid,b"SSID_REDACTED",1)==raw.replace(before,b"SSID_REDACTED",1)
path.write_bytes(new)
assert re.search(rb"(?m)^ssid="+ssid+rb"$",path.read_bytes())
print(f"AP_SSID_OK arch={arch} ssid={ssid.decode()}")
