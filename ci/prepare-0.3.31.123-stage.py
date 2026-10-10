#!/usr/bin/env python3
"""Run the existing 0.3.31 preparer against the current cumulative 0.3.30 baseline.

The published-image patch for 0.3.31 uses `function renderFamilies(){` in hotspot.html.
The older builder preparer still expects `function render(){`. This wrapper changes only
that stale staging anchor/injection in a temporary copy; all functional 0.3.31 logic,
DMR byte protection, RF/network/display changes and validation remain in the canonical
preparer.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
canonical = repo / "ci/prepare-0.3.31-alpha.py"
text = canonical.read_text()

old_marker = "marker='function render(){'"
new_marker = "marker='function renderFamilies(){'"
old_inject = "function render(){updateRadioGuide();"
new_inject = "function renderFamilies(){updateRadioGuide();"

if text.count(old_marker) != 1:
    raise SystemExit('ARM32_STAGE_MARKER_ANCHOR_MISSING_OR_AMBIGUOUS')
if text.count(old_inject) != 1:
    raise SystemExit('ARM32_STAGE_INJECT_ANCHOR_MISSING_OR_AMBIGUOUS')

text = text.replace(old_marker, new_marker, 1).replace(old_inject, new_inject, 1)

with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as tf:
    tf.write(text)
    tmp = Path(tf.name)
try:
    subprocess.run([sys.executable, str(tmp), *sys.argv[1:]], check=True)
finally:
    tmp.unlink(missing_ok=True)

print('ARM32_0_3_31_STAGE_COMPAT_OK')
