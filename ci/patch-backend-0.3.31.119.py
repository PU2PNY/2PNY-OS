#!/usr/bin/env python3
"""0.3.31.119 backend: remove the project-specific Nextion renderer.

Builds on the validated 0.3.31.117 display API policy, then narrows Nextion to
MMDVMHost native layout 0/2 or hardened ON7LDS NextionDriver layout 3/4.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

if len(sys.argv) != 3:
    raise SystemExit('usage: patch-backend-0.3.31.119.py <input.go> <output.go>')
repo=Path(__file__).resolve().parents[1]
src=Path(sys.argv[1])
out=Path(sys.argv[2])
with tempfile.NamedTemporaryFile(prefix='2pny-0331119-',suffix='.go',delete=False) as f:
    tmp=Path(f.name)
try:
    subprocess.run([sys.executable,str(repo/'ci/patch-backend-0.3.31.117.py'),str(src),str(tmp)],check=True)
    s=tmp.read_text()
finally:
    tmp.unlink(missing_ok=True)

def one(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: anchor count={n}')
    s=s.replace(old,new,1)

one('appVersion            = "0.3.31.117"','appVersion            = "0.3.31.119"','version')
one('''\t\tov := map[string]any{\n\t\t\t"enabled": false, "type": "nextion_mmdvm", "layout": 2,\n\t\t\t"renderer": "mmdvmhost-native", "model_profile": "auto", "resolution": "",\n\t\t}''',
    '''\t\tov := map[string]any{\n\t\t\t"enabled": false, "type": "nextion_mmdvm", "layout": 0,\n\t\t\t"renderer": "mmdvmhost-native", "model_profile": "auto", "resolution": "",\n\t\t}''','display GET default')
one('''\t\tif in.Renderer == "" {\n\t\t\tif in.Layout == 4 { in.Renderer = "on7lds-compatible" } else if in.Layout == 2 || in.Layout == 3 { in.Renderer = "mmdvmhost-native" } else { in.Renderer = "pu2pny-modern-v2" }\n\t\t}''',
    '''\t\tif in.Renderer == "" {\n\t\t\tif in.Layout == 3 || in.Layout == 4 { in.Renderer = "on7lds-compatible" } else { in.Renderer = "mmdvmhost-native" }\n\t\t}''','display renderer default')
one('if in.Renderer != "pu2pny-modern-v2" && in.Renderer != "mmdvmhost-native" && in.Renderer != "on7lds-compatible" {',
    'if in.Renderer != "mmdvmhost-native" && in.Renderer != "on7lds-compatible" {',
    'display renderer allowlist')
one('''\t\tif in.Enabled {\n\t\t\t// DISPLAY-025: preserve the proven native writer unless the operator\n\t\t\t// explicitly selected the hardened ON7LDS compatibility renderer.\n\t\t\tif in.Renderer == "on7lds-compatible" {\n\t\t\t\tif in.Layout != 3 && in.Layout != 4 { in.Layout = 3 }\n\t\t\t} else {\n\t\t\t\tin.Renderer = "mmdvmhost-native"\n\t\t\t\tif in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }\n\t\t\t}\n\t\t} else if in.Renderer == "pu2pny-modern-v2" {\n\t\t\tin.Layout = 9\n\t\t} else if in.Renderer == "on7lds-compatible" {\n\t\t\tif in.Layout != 3 && in.Layout != 4 { in.Layout = 3 }\n\t\t} else if in.Layout != 2 && in.Layout != 3 {\n\t\t\tin.Layout = 2\n\t\t}''',
    '''\t\tif in.Renderer == "on7lds-compatible" {\n\t\t\tif in.Layout != 3 && in.Layout != 4 { in.Layout = 3 }\n\t\t} else {\n\t\t\tin.Renderer = "mmdvmhost-native"\n\t\t\tif in.Layout != 0 && in.Layout != 2 { in.Layout = 0 }\n\t\t}''','display policy')

if 'pu2pny-modern-v2' in s:
    raise SystemExit('old project-specific Nextion renderer remains in backend')
out.write_text(s)
print('BACKEND_0331119_DISPLAY_POLICY_OK')
