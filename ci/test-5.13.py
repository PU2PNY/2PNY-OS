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
