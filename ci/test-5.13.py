#!/usr/bin/env python3
"""Regression checks for timezone persistence, manual precedence and AP DHCP."""
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('clock513',REPO/'runtime/5.13/tz-apply.py')
clock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clock)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    host_zones = clock.ZONEINFO
    clock.ZONEINFO = root/'zoneinfo'
    for zone in ('America/Sao_Paulo','America/New_York','Europe/London','zone.tab'):
        destination = clock.ZONEINFO/zone
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes((host_zones/zone).read_bytes())
    alias = clock.ZONEINFO/'US/Eastern'
    alias.parent.mkdir()
    alias.symlink_to('../America/New_York')
    clock.CLOCK = root/'settings'/'clock.json'
    clock.LOCALTIME = root/'localtime'
    clock.TIMEZONE = root/'timezone'
    clock.RUN = root
    ntp = []
    clock.set_ntp = ntp.append
    clock.set_timezone({'action':'initialize-zone','timezone':'America/Sao_Paulo'},'1')
    assert clock.effective_timezone() == 'America/Sao_Paulo'
    assert clock.clock_settings()['timezone_source'] == 'browser-iana' and ntp == [True]
    clock.set_timezone({'timezone':'US/Eastern'},'2')
    assert clock.effective_timezone() == 'US/Eastern'
    assert clock.clock_settings()['timezone'] == 'US/Eastern'
    clock.set_timezone({'action':'initialize-zone','timezone':'Europe/London'},'3')
    assert clock.effective_timezone() == 'US/Eastern' and ntp == [True]
    clock.set_timezone({'action':'dst-display','dst_manual':True},'4')
    assert clock.clock_settings()['dst_manual'] and clock.clock_settings()['timezone_source']=='manual'
    assert clock.TIMEZONE.read_text().strip() == 'US/Eastern'
    try:
        clock.set_timezone({'timezone':'zone.tab'},'5')
    except ValueError:
        pass
    else:
        raise AssertionError('accepted a non-TZif input')
    assert json.loads((root/'timezone-result-3.json').read_text())['unchanged']

overlay = (REPO/'ci/patch-image-5.13.py').read_text()
line = next(line for line in overlay.splitlines() if 'test -f "$STATE/provisioned" && test -n "$outif"' in line)
predicate = line.split("'")[1]
with tempfile.TemporaryDirectory() as temporary:
    def desired(uplink, ap='wlan0'):
        cmd = 'STATE="$1"; outif="$2"; AP_WIFI="$3"; now=0; ' + predicate + '; printf "%s" "$now"'
        return subprocess.check_output(['bash','-c',cmd,'bash',temporary,uplink,ap],text=True)
    assert desired('eth0') == '0'
    (Path(temporary)/'provisioned').touch()
    assert desired('eth0') == '1'
    assert desired('wlan0') == '0'
    assert desired('') == '0'

print('5.13 clock and DHCP regression checks passed')

with tempfile.TemporaryDirectory() as temporary:
    # Run the installed transaction with predictable NetworkManager effects.
    secondary = REPO/'runtime/5.13/wifi-secondary.sh'
    fixture = r'''
set -euo pipefail
PRIMARY=PU2PNY-WIFI
SECONDARY=PU2PNY-WIFI-SECONDARY
source "$1"
cd "$2"
touch "$SECONDARY"
wifi_if(){ echo wlan0; }
profile_ssid(){ echo principal; }
profile_uuid(){ echo candidate-uuid; }
active_name(){ echo "$PRIMARY"; }
exists(){ test -e "$1"; }
nm(){ return 1; }
timeout(){
  shift 4
  test "$1" = connection || return 1
  shift
  case "$1:$2" in
    add:type)
      [[ " $* " = *' connection.autoconnect no '* ]] || return 8
      touch PU2PNY-WIFI-SECONDARY-CANDIDATE ;;
    delete:uuid) rm -f PU2PNY-WIFI-SECONDARY-CANDIDATE ;;
    delete:*) rm -f "$2" ;;
    modify:uuid)
      if test "$4" = connection.id; then
        test "${FAIL_COMMIT:-0}" != 1 || return 19
        mv PU2PNY-WIFI-SECONDARY-CANDIDATE "$5"
      fi ;;
    modify:*) mv "$2" "$4" ;;
  esac
}
save_secondary reserva '' ''
'''
    root = Path(temporary)
    for fail in ('0','1'):
        result = subprocess.run(['bash','-c',fixture,'bash',secondary,root],capture_output=True,
                                env={**__import__('os').environ,'FAIL_COMMIT':fail})
        assert (result.returncode == 0) == (fail == '0'), result
        assert (root/'PU2PNY-WIFI-SECONDARY').exists(), result
        assert not (root/'PU2PNY-WIFI-SECONDARY-CANDIDATE').exists(), result
        assert not (root/'PU2PNY-WIFI-SECONDARY-BACKUP').exists(), result

print('5.13 secondary Wi-Fi save and rollback checks passed')

# Exercise the exact loader in the privileged request entrypoint, with the
# extensionless installed name. The stub records that request validation ran.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    patch_spec = importlib.util.spec_from_file_location('image513',REPO/'ci/patch-image-5.13.py')
    overlay_module = importlib.util.module_from_spec(patch_spec)
    patch_spec.loader.exec_module(overlay_module)
    import ast
    tree = ast.parse(Path(overlay_module.__file__).read_text())
    edit = next(node for node in ast.walk(tree) if isinstance(node,ast.Call)
                and node.args and isinstance(node.args[0],ast.Constant)
                and node.args[0].value == 'usr/local/libexec/pu2pny/2pny-rf-access-request')
    entry = (REPO/'runtime/5x/2pny-rf-access-request.py').read_text()
    for old,new in ast.literal_eval(edit.args[1]):
        assert entry.count(old)==1
        entry=entry.replace(old,new,1)
    module = {}
    exec(compile(entry,'rf-access-request','exec'),module)
    module['SRC'] = root/'2pny-rf-access'
    module['REQUEST'] = root/'request.json'
    module['RESULT'] = root/'result.json'
    module['SRC'].write_text('DEFAULT_INI=DEFAULT_STATE=DEFAULT_UNIT=None\ndef apply(a,b,c,r,d):\n    return {"ok": r["confirmation"] == "ABRIR RF PUBLICO"}\n')
    module['REQUEST'].write_text('{"mode":"public","confirmation":"ABRIR RF PUBLICO"}')
    assert module['main']()==0
    assert json.loads(module['RESULT'].read_text())['ok']

print('5.13 RF request resolves the extensionless installed helper')
