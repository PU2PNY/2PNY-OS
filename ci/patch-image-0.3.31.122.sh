#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"

test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.121'
test -f "$ROOT/usr/local/sbin/2pny-display-apply"
test -f "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
test -f "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
test -x "$ROOT/usr/local/bin/NextionDriver-pu2pny"

cp -a "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/sbin/2pny-display-apply.0.3.31.121.bak"
cp -a "$ROOT/etc/systemd/system/2pny-nextiondriver.service" "$ROOT/etc/systemd/system/2pny-nextiondriver.service.0.3.31.121.bak"

ROOT="$ROOT" python3 - <<'PY'
import os,re
from pathlib import Path
root=Path(os.environ['ROOT'])

# DISPLAY-030A — Pi-Star/PD0DIB lifecycle semantics, scoped only to ON7LDS.
# Enabling this unit creates a .requires dependency from MMDVMHost to the
# NextionDriver. Disabling it removes that dependency, so native display modes
# remain exactly independent of NextionDriver.
p=root/'etc/systemd/system/2pny-nextiondriver.service'
s=p.read_text()
old='[Install]\nWantedBy=multi-user.target\n'
new='[Install]\nRequiredBy=2pny-mmdvmhost.service\n'
if s.count(old)!=1:
    raise SystemExit(f'NextionDriver install anchor count={s.count(old)}')
s=s.replace(old,new,1)
p.write_text(s)

# DISPLAY-030B — replace the imperative/racy handoff with the same dependency
# contract used by the PD0DIB Pi-Star installer. MMDVMHost is stopped before
# changing topology; NextionDriver must create its PTY first; MMDVMHost is then
# started with an installed Requires= relationship. Every failure restores the
# previous INI and removes the dependency before bringing the radio engine back.
p=root/'usr/local/sbin/2pny-display-apply'
s=p.read_text()
pattern=r'def stop_on7lds\(\):.*?\n(?=hw=load\(HW\))'
replacement=r'''def stop_on7lds():
    ctl("disable","--now",NEXTIONDRIVER)
    ctl("daemon-reload")

def patch_on7lds(layout):
    if layout not in (3,4):layout=3
    cp=host_config()
    cp.set("General","Display","Nextion")
    cp.set("Nextion","Port","/run/2pny-nextiondriver/ttyNextionDriver")
    cp.set("Nextion","Brightness",cp.get("Nextion","Brightness",fallback="50"))
    cp.set("Nextion","DisplayClock","1");cp.set("Nextion","UTC","0")
    cp.set("Nextion","IdleBrightness",cp.get("Nextion","IdleBrightness",fallback="20"))
    cp.set("Nextion","ScreenLayout",str(layout))
    if not cp.has_section("Transparent Data"):cp.add_section("Transparent Data")
    for k,v in (("Enable","1"),("RemoteAddress","127.0.0.1"),("RemotePort","40094"),("LocalPort","40095"),("SendFrameType","1")):
        cp.set("Transparent Data",k,v)
    if not cp.has_section("NextionDriver"):cp.add_section("NextionDriver")
    for k,v in (("Port","modem"),("LogLevel","2"),("DataFilesPath","/usr/share/2pny/nextiondriver"),("GroupsFile","groups.txt"),("DMRidFile","users.csv"),("WaitForLan","0"),("ShowModesStatus","1"),("RemoveDim","0"),("SleepWhenInactive","0")):
        cp.set("NextionDriver",k,v)
    backup=HOST.with_name("MMDVM-Host.ini.display-backup")
    host_service="2pny-mmdvmhost.service"
    if not ctl("stop",host_service):
        raise RuntimeError("MMDVMHost não parou para o handoff seguro da Nextion")
    stop_on7lds()
    write_host(cp,backup)
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    try:
        if not ctl("enable",NEXTIONDRIVER):
            raise RuntimeError("NextionDriver não pôde ser habilitado")
        if not ctl("daemon-reload"):
            raise RuntimeError("systemd não recarregou a dependência NextionDriver/MMDVMHost")
        if not ctl("start",NEXTIONDRIVER):
            raise RuntimeError("NextionDriver não iniciou")
        link=Path("/run/2pny-nextiondriver/ttyNextionDriver")
        end=time.monotonic()+12
        while time.monotonic()<end:
            if active(NEXTIONDRIVER) and link.exists():break
            time.sleep(.25)
        else:
            raise RuntimeError("NextionDriver não disponibilizou a porta virtual")
        if not ctl("start",host_service):
            raise RuntimeError("MMDVMHost não iniciou com a porta virtual do NextionDriver")
        end=time.monotonic()+12
        while time.monotonic()<end:
            if active(NEXTIONDRIVER) and active(host_service) and link.exists():
                return backup
            time.sleep(.25)
        raise RuntimeError("NextionDriver/MMDVMHost não estabilizaram no modo ON7LDS")
    except Exception:
        ctl("stop",host_service)
        stop_on7lds()
        shutil.copy2(backup,HOST)
        if not ctl("start",host_service):
            raise RuntimeError("Falha ON7LDS e o MMDVMHost não reiniciou após rollback")
        raise

'''
s2,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'ON7LDS function block replacement count={n}')
p.write_text(s2)
PY

printf '0.3.31.122\n' >"$ROOT/etc/2pny/version"

python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'RequiredBy=2pny-mmdvmhost.service' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'if not ctl("stop",host_service)' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'ctl("daemon-reload")' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'SendFrameType","1"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'Port","modem"' "$ROOT/usr/local/sbin/2pny-display-apply"
test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.122'
echo PATCH_IMAGE_0331122_OK
