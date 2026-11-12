#!/usr/bin/env python3
"""Reconstrução do backend 5.09, HOST-511 e portal canônico."""
from pathlib import Path
import subprocess, sys
repo=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve()
arch=sys.argv[2] if len(sys.argv)>2 else 'arm64'
assert arch in ('arm32','arm64')
subprocess.run([sys.executable,str(repo/'ci/prepare-5.10-backend.py'),str(out),arch],check=True)
p=out/'main.go';s=p.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(old[:80],s.count(old))
    s=s.replace(old,new,1)
replace('appVersion            = "5.10.000"','appVersion            = "5.11.000"')
if arch=='arm64':
    assert s.count('pu2pny.local')==7,s.count('pu2pny.local')
    for line in list(dict.fromkeys(l for l in s.splitlines(True) if 'pu2pny.local' in l)):
        replace(line,line.replace('pu2pny.local','pu2pny64.local'))
host='pu2pny32.local' if arch=='arm32' else 'pu2pny64.local'
replace(f'"http://{host}/internet?captive=1"',f'"http://{host}/wizard?captive=1"')
start=s.index('func captivePortalHandler(');end=s.index('\nfunc ',start+10)
body=s[start:end];old='http.Redirect(w, r, "/wizard", http.StatusFound)'
assert body.count(old)==1
replace(body,body.replace(old,f'http.Redirect(w, r, "http://{host}/wizard?captive=1", http.StatusFound)'))
# Neutralizar somente texto conhecido, preservando URLs de dados.
for line in list(dict.fromkeys(l for l in s.splitlines(True) if 'Pi-Star' in l or 'WPSD' in l)):
    replace(line,line.replace('Pi-Star','MMDVMHost').replace('WPSD','ON7LDS'))
p.write_text(s)
(out/'web511.go').write_bytes((repo/'runtime/5.11/web.go').read_bytes())
print('PREPARE_511_OK',arch)
