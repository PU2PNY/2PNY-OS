#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scope',ROOT/'ci/classify-change-scope.py');assert spec and spec.loader
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def check(paths,docs,arm):
    r=m.classify(paths);assert r['docs_only'] is docs,r;assert r['arm64_required'] is arm,r

check(['docs/RECOVERY.md'],True,False)
check(['PU2PNY-OS_CHANGELOG.md','docs/NOTE.md'],True,False)
check(['README.md'],True,False)
check(['src/display-0.3.30.html'],False,True)
check(['docs/NOTE.md','src/display-0.3.30.html'],False,True)
check(['.github/workflows/build.yml'],False,True)
check(['ci/test.py'],False,True)
check([],False,True)
assert m.classify(['src/display-0.3.30.html'])['i18n_required'] is True
assert m.classify(['src/ui-language-0.3.27.js'])['i18n_required'] is True
assert m.classify(['docs/NOTE.md'])['i18n_required'] is False
print('PASS: docs-only classifier is conservative')
