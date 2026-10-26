#!/usr/bin/env python3
"""Offline tests for MMDVM-Info-compatible CPU JSON without hardware assumptions."""
from pathlib import Path
import importlib.util
import tempfile
spec=importlib.util.spec_from_file_location('adapter','runtime/display/adapter.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as tmp:
    t=Path(tmp)/'thermal'; f=Path(tmp)/'freq'; l=Path(tmp)/'load'
    t.write_text('45000\n')
    f.write_text('1500000\n')
    l.write_text('0.25 0.15 0.05 2/100 25\n')
    assert mod.cpu_metadata(t,f,l)=={'temperature':45.0,'frequency':1500.0,'load':0.25}
    t.write_text('invalid\n');f.unlink();l.write_text('invalid\n')
    assert mod.cpu_metadata(t,f,l)=={}
print('DISPLAY_INFO_CPU_CONTRACT_PASS')
