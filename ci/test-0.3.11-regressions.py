#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:(ROOT/p).read_text()

main=read("src/2pnyd-main-0.3.11.go")
rf=read("src/2pny-rf-apply-0.3.11")
probe=read("src/2pny-hardware-probe-0.3.11.py")
wiz=read("src/wizard-0.3.11.html")
lang=read("src/ui-language-0.3.11.js")

assert 'appVersion            = "0.3.11-alpha"' in main
assert 'MODEM_BAUD=' in rf and 'UARTSpeed=$MODEM_BAUD' in rf
assert 'flock -w 8 8' in rf
assert '2pny-mqtt-preflight --quiet' in rf
assert 'record_failure' in rf and 'last-rf-apply-error.json' in rf
assert 'MMDVMHost failed with detected baud' not in rf
assert 'MMDVMHost não iniciou; a configuração anterior foi restaurada' in rf
assert 'bridge = probe_nextion_mmdvm' not in probe
assert 'mmdvm_display_candidate' in probe
assert 'MMDVM confirmada. A Nextion pela porta do modem' in probe
assert 'scheduleHardwareAdvance' in wiz
assert 'automático em 5 s' in wiz
assert 'O assistente avançará automaticamente em 5 segundos.' in wiz
assert 'normalizeIncoming' in lang and 'incomingPT' in lang
assert 'MMDVMHost failed with detected baud' in lang
assert "if(language==='pt')return trimmed;" in lang
print("TEST_0311_REGRESSIONS_OK")
