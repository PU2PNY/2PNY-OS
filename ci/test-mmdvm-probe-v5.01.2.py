#!/usr/bin/env python3
"""Source contract regression: avoid real serial hardware in CI."""
from pathlib import Path
import ast
source=Path('src/2pny-hardware-probe-0.3.26.py').read_text()
tree=ast.parse(source)
assert '0.60 if baud == 115200 else 0.18' in source
assert '0.65 if baud == 115200 else 0.22' in source
assert 'previous.get("mmdvm", {}).get("detected") is True' in source
assert 'pending_modem_confirmation' in source
assert 'if radio_service_active() and OUT.exists()' in source
assert 'fcntl.flock(_serial_lock.fileno(), fcntl.LOCK_EX)' in source
assert any(isinstance(node,ast.FunctionDef) and node.name=='probe_mmdvm' for node in tree.body)
print('MMDVM_PROBE_115200_SCOPE_AND_SERIAL_OWNERSHIP_PASS')
