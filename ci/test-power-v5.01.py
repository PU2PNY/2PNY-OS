#!/usr/bin/env python3
import importlib.util
spec=importlib.util.spec_from_file_location('power','runtime/diagnostics/2pny-power-status.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.decode("throttled=0x50005")["undervoltage_now"] is True
assert m.decode("throttled=0x50005")["undervoltage_since_boot"] is True
assert m.decode("throttled=0x50000")["undervoltage_now"] is False
assert m.decode("throttled=0x0")["throttled_now"] is False
assert m.decode("garbage")["state"] == "not_verified"
print("POWER_STATUS_CONTRACT_PASS")
