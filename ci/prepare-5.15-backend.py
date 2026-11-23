#!/usr/bin/env python3
"""Rebuild the backend with the 5.15 changes on top of 5.14.

5.15 keeps every 5.14/5.13.003 change and adds:
  - OTA notifier fix: the release tag (pu2pny-v<ver>) is normalised before it is
    compared to the running version, so "atualização disponível" only shows when
    a genuinely newer release exists (before, it was always on).
It does not modify RF, the protected hardware probe, MMDVMHost or gateways.
Additional 5.15 blocks (profile-apply speed, YSF resilience) are appended here
as they are implemented.
"""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
subprocess.run([sys.executable, str(repo / 'ci/prepare-5.14-backend.py'), str(out), arch], check=True)
main = out / 'main.go'
source = main.read_text()


def replace(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old, new, 1)


# Version badge.
replace('appVersion            = "5.14.000"', 'appVersion            = "5.15.000"')

# OTA-514B: normalise the release tag before comparing with appVersion.
# Tags are "pu2pny-v5.15.000"; the old code only stripped a leading "v", so the
# parsed version never matched appVersion and the panel always said "available".
replace('version:=strings.TrimPrefix(rel.Tag,"v")',
        'version:=strings.TrimPrefix(strings.TrimPrefix(rel.Tag,"pu2pny-"),"v")')

# PERF-515: measure how long "ativar perfil" blocks on the protected
# protocol-network-apply script, so the real bottleneck on Pi Zero is visible
# (logged and returned as took_ms). Instrumentation only: no behaviour change.
replace('\tout, err := exec.Command("/usr/local/sbin/2pny-protocol-network-apply", args...).CombinedOutput()',
        '\tapplyStart515 := time.Now()\n'
        '\tout, err := exec.Command("/usr/local/sbin/2pny-protocol-network-apply", args...).CombinedOutput()\n'
        '\tapplyMS515 := time.Since(applyStart515).Milliseconds()\n'
        '\tlog.Printf("PERF-515 ativar-perfil %s levou %dms", in.Protocol, applyMS515)')
replace('\twriteJSON(w, 200, map[string]any{"ok": true, "changed": true})',
        '\twriteJSON(w, 200, map[string]any{"ok": true, "changed": true, "took_ms": applyMS515})')

main.write_text(source)
print("PREPARE_515_OK", arch)
