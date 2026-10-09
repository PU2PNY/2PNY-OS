#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"

test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.120'
test -f "$ROOT/usr/local/sbin/2pny-display-apply"
test -x "$ROOT/usr/local/bin/NextionDriver-pu2pny"
test -f "$ROOT/etc/systemd/system/2pny-nextiondriver.service"

cp -a "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/sbin/2pny-display-apply.0.3.31.120.bak"
cp -a "$ROOT/etc/systemd/system/2pny-nextiondriver.service" "$ROOT/etc/systemd/system/2pny-nextiondriver.service.0.3.31.120.bak"

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path
root=Path(os.environ['ROOT'])

# DISPLAY-029A: ON7LDS upstream explicitly supports -i to avoid false duplicate
# process rejection. The PU2PNY binary name contains NextionDriver, so use the
# supported flag and clean the runtime PTY before each service start.
p=root/'etc/systemd/system/2pny-nextiondriver.service'
s=p.read_text()
old='ExecStart=/usr/local/bin/NextionDriver-pu2pny -d -c /var/lib/2pny/mmdvm/MMDVM-Host.ini'
new='ExecStartPre=/usr/bin/rm -f /run/2pny-nextiondriver/ttyNextionDriver\nExecStart=/usr/local/bin/NextionDriver-pu2pny -d -i -vv -c /var/lib/2pny/mmdvm/MMDVM-Host.ini'
if s.count(old)!=1: raise SystemExit(f'nextiondriver ExecStart anchor count={s.count(old)}')
s=s.replace(old,new,1)
if 'TimeoutStartSec=' not in s:
    s=s.replace('RestartSec=2\n','RestartSec=2\nTimeoutStartSec=15\n',1)
p.write_text(s)

# DISPLAY-029B: do a clean stop/start instead of restart while changing the
# MMDVMHost<->NextionDriver PTY topology. This guarantees RuntimeDirectory and
# the PTY link are recreated from the just-written INI before MMDVMHost opens it.
p=root/'usr/local/sbin/2pny-display-apply'
s=p.read_text()
old='if (not ctl("enable",NEXTIONDRIVER)) or (not ctl("restart",NEXTIONDRIVER)):'
new='if not ctl("stop",NEXTIONDRIVER):\n        pass\n    if (not ctl("enable",NEXTIONDRIVER)) or (not ctl("start",NEXTIONDRIVER)):'
if s.count(old)!=1: raise SystemExit(f'clean handoff anchor count={s.count(old)}')
s=s.replace(old,new,1)
old2='''    try:restart_host_or_rollback(backup)\n    except Exception:\n        ctl("disable","--now",NEXTIONDRIVER);raise\n    return backup'''
new2='''    try:\n        restart_host_or_rollback(backup)\n        end=time.monotonic()+8\n        while time.monotonic()<end:\n            if active(NEXTIONDRIVER) and active(HOST_SERVICE) and link.exists():break\n            time.sleep(.25)\n        else:\n            raise RuntimeError("NextionDriver/MMDVMHost não estabilizaram após o handoff")\n    except Exception:\n        ctl("disable","--now",NEXTIONDRIVER)\n        shutil.copy2(backup,HOST)\n        restart_host_or_rollback(backup)\n        raise\n    return backup'''
if s.count(old2)!=1: raise SystemExit(f'post-handoff validation anchor count={s.count(old2)}')
s=s.replace(old2,new2,1)
p.write_text(s)
PY

printf '0.3.31.121\n' >"$ROOT/etc/2pny/version"

python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'ExecStartPre=/usr/bin/rm -f /run/2pny-nextiondriver/ttyNextionDriver' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'NextionDriver-pu2pny -d -i -vv -c /var/lib/2pny/mmdvm/MMDVM-Host.ini' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'ctl("start",NEXTIONDRIVER)' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'NextionDriver/MMDVMHost não estabilizaram após o handoff' "$ROOT/usr/local/sbin/2pny-display-apply"
test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.121'
echo PATCH_IMAGE_0331121_OK
