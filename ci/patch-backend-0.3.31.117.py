#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch-backend-0.3.31.117.py <input.go> <output.go>')
src=Path(sys.argv[1])
out=Path(sys.argv[2])
s=src.read_text()

def one(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: anchor count={n}')
    s=s.replace(old,new,1)

one('appVersion            = "0.3.27-alpha"','appVersion            = "0.3.31.117"','version')
one('''\t\tov := map[string]any{\n\t\t\t"enabled": false, "type": "nextion_mmdvm", "layout": 9,\n\t\t\t"renderer": "pu2pny-modern-v2", "model_profile": "auto", "resolution": "",\n\t\t}''',
    '''\t\tov := map[string]any{\n\t\t\t"enabled": false, "type": "nextion_mmdvm", "layout": 2,\n\t\t\t"renderer": "mmdvmhost-native", "model_profile": "auto", "resolution": "",\n\t\t}''','display GET default')
one('''\t\tif in.Renderer == "" {\n\t\t\tif in.Layout == 2 || in.Layout == 3 { in.Renderer = "mmdvmhost-native" } else { in.Renderer = "pu2pny-modern-v2" }\n\t\t}''',
    '''\t\tif in.Renderer == "" {\n\t\t\tif in.Layout == 4 { in.Renderer = "on7lds-compatible" } else if in.Layout == 2 || in.Layout == 3 { in.Renderer = "mmdvmhost-native" } else { in.Renderer = "pu2pny-modern-v2" }\n\t\t}''','display renderer default')
one('if in.Renderer != "pu2pny-modern-v2" && in.Renderer != "mmdvmhost-native" {',
    'if in.Renderer != "pu2pny-modern-v2" && in.Renderer != "mmdvmhost-native" && in.Renderer != "on7lds-compatible" {',
    'display renderer allowlist')
one('''\t\tif in.Enabled {\n\t\t\t// DISPLAY-018: this endpoint controls Nextion through the modem.\n\t\t\t// Hardware validation regressed with the MQTT/vector bridge, so the\n\t\t\t// proven MMDVMHost-native writer is authoritative here.\n\t\t\tin.Renderer = "mmdvmhost-native"\n\t\t\tif in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }\n\t\t} else if in.Renderer == "pu2pny-modern-v2" {\n\t\t\tin.Layout = 9\n\t\t} else if in.Layout != 2 && in.Layout != 3 {\n\t\t\tin.Layout = 2\n\t\t}''',
    '''\t\tif in.Enabled {\n\t\t\t// DISPLAY-025: preserve the proven native writer unless the operator\n\t\t\t// explicitly selected the hardened ON7LDS compatibility renderer.\n\t\t\tif in.Renderer == "on7lds-compatible" {\n\t\t\t\tif in.Layout != 3 && in.Layout != 4 { in.Layout = 3 }\n\t\t\t} else {\n\t\t\t\tin.Renderer = "mmdvmhost-native"\n\t\t\t\tif in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }\n\t\t\t}\n\t\t} else if in.Renderer == "pu2pny-modern-v2" {\n\t\t\tin.Layout = 9\n\t\t} else if in.Renderer == "on7lds-compatible" {\n\t\t\tif in.Layout != 3 && in.Layout != 4 { in.Layout = 3 }\n\t\t} else if in.Layout != 2 && in.Layout != 3 {\n\t\t\tin.Layout = 2\n\t\t}''','display enabled policy')
one('"enabled": true, "type": "nextion_mmdvm", "speed": 9600,',
    '"enabled": true, "type": "nextion_mmdvm", "speed": func() int { if in.Layout == 4 { return 115200 }; return 9600 }(),',
    'display speed metadata')

out.write_text(s)
print('BACKEND_0331117_PATCH_OK')
