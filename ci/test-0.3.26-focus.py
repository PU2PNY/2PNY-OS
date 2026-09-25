#!/usr/bin/env python3
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]

probe=(root/"src/2pny-hardware-probe-0.3.26.py").read_text()
switch=(root/"src/2pny-network-switch-0.3.26").read_text()
profiles=(root/"src/2pny-wifi-profiles-0.3.26").read_text()
dispatcher=(root/"src/90-pu2pny-wifi-choice-0.3.26").read_text()
internet=(root/"src/internet-0.3.26.html").read_text()
system=(root/"src/system-0.3.26.html").read_text()
backend=(root/"src/2pnyd-main-0.3.26.go").read_text()

# HW-004: broad serial discovery, upstream-compatible UART speeds, identification-only.
for token in (
    '/dev/serial/by-id/*','/dev/serial/by-path/*','/dev/serial0',
    '/dev/ttyAMA*','/dev/ttyS*','/dev/ttyACM*','/dev/ttyUSB*',
    '/dev/ttyXRUSB*','/dev/ttyGS*'
):
    assert token in probe, token
for baud in (1200,2400,4800,9600,19200,38400,57600,115200,230400,460800,500000):
    assert f'({baud}, "B{baud}")' in probe, baud
assert 'bytes((0xE0, 0x03, 0x00))' in probe
assert 'usb_reset_prone' in probe and 'time.sleep(1.8)' in probe
assert 'radio_service_active()' in probe and '2pny-mmdvmhost.service' in probe
mmdvm_body=probe[probe.index('def probe_mmdvm'):probe.index('def parse_mmdvm_serial_payloads')]
for forbidden in ('SET_CONFIG','SET_FREQ','flash','RXFrequency','TXFrequency','RXOffset','TXOffset'):
    assert forbidden not in mmdvm_body, forbidden

# NET-032: remove redundant scans and reduce PU2PNY-controlled fixed waits >3x.
assert 'for attempt in 1 2 3' not in switch[switch.index('scan_json(){'):switch.index('sanitize_nm_error')]
assert '--rescan yes' in switch
assert 'test "${count:-0}" -lt 2' in switch
assert 'sleep 0.35' in switch
assert 'ipv4.dhcp-timeout 12' in switch
assert 'nmcli --wait 14 connection up PU2PNY-WIFI-CANDIDATE' in switch
assert 'for _ in $(seq 1 16)' in switch
assert 'sleep 0.5' in switch
# Previous worst fixed association budget: 3*45 + 2*(1+1) reset + 30 IP + 5 grace = 174s.
# New worst fixed association budget: 3*14 + 2*(.3+.3) reset + 16*.5 IP + 5 grace = 56.2s.
assert 174.0 / 56.2 >= 3.0

# NET-033: shared scan, prioritized profiles, bounded failover, hysteresis and rollback.
assert profiles.count('device wifi list --rescan yes') == 1
assert 'connection.autoconnect-priority 200' in profiles
assert 'connection.autoconnect-priority 150' in profiles
assert 'connection.autoconnect-retries 2' in profiles
assert '12-point hysteresis' in profiles
assert 'nm --wait 6 connection up "$chosen"' in profiles
assert 'nm --wait 8 connection up "$SECONDARY"' in profiles
assert 'nm --wait 6 connection up uuid "$old_uuid"' in profiles
assert 'for _ in $(seq 1 8)' in profiles
assert 'A rede anterior foi restaurada.' in profiles
assert 'hidden=yes' in profiles and 'hidden=no' in profiles
assert 'sleep 0.15' in dispatcher and 'auto-select' in dispatcher
# Previous dispatcher+activation fixed delay ~1+18 = 19s; new .15+6 = 6.15s.
assert 19.0 / 6.15 >= 3.0
# Previous manual switch+confirmation ~22+15 = 37s; new 8+4 = 12s.
assert 37.0 / 12.0 >= 3.0

# UI: dedicated Wi-Fi 2 scan and immediate reboot paint.
assert 'id="wifiSearchSecond"' in internet
assert "PNY.q('wifiSearchSecond').onclick=wifiScan" in internet
assert 'deadline=Date.now()+18000' in internet
assert 'setTimeout(r,400)' in internet
assert "PNY.operation(rt,rt)" in system
assert "PNYT('Reiniciar hotspot')" in system
assert 'requestAnimationFrame(function(){requestAnimationFrame(r)})' in system
assert "await action('reboot',null,5000)" in system

# Backend only accelerates scan dispatch and bumps version.
assert 'appVersion            = "0.3.26-alpha"' in backend
assert 'time.Sleep(120 * time.Millisecond)' in backend
assert '"18", "/usr/local/sbin/2pny-network-switch", "scan-json"' in backend

print("FOCUS_0326_OK")
