#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import ast
repo = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("display_patch", repo / "ci/patch-display-5.00.001.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

go = (repo / "src/2pnyd-main-0.3.27.go").read_text()
apply = (repo / "src/2pny-display-apply-0.3.30.py").read_text()
after_go = module.patch_go(go)
after_apply = module.patch_apply(apply)
ast.parse(after_apply)
assert 'if in.Layout != 0 && in.Layout != 2 && in.Layout != 3' in after_go
assert 'requested=int(ov.get("layout",9))' in after_apply
assert 'ctl("disable","--now",DRIVER)' in after_apply
assert 'd.get("physical_confirmed") is True and active(MMDVM)' in after_apply
assert "Port=modem" not in after_go  # Never hardcode hardware UART in Go
assert 'rfApplyHandler' in after_go  # Existing RF backend preserved
assert '[General]' not in after_apply # It edits a parsed INI, not a factory template
for banned in ("curl | bash", "eval(", "system("):
    assert banned not in after_apply
print("DISPLAY_500001_SOURCE_PATCH_TEST_OK")
