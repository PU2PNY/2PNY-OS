#!/usr/bin/env python3
"""PU2PNY-OS 5.15 software regression checks.

5.15 is a strict superset of 5.14: it keeps every 5.14/5.13.003 change and adds
the OTA notifier fix, YSF auto-reconnect resilience (a systemd drop-in, not an RF
rewrite) and profile-apply timing instrumentation.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "ci/patch-image-5.15.py"
BUILD = ROOT / "ci/build-5.15.py"
BACKEND = ROOT / "ci/prepare-5.15-backend.py"


def main():
    patch_text = PATCH.read_text()
    build_text = BUILD.read_text()
    backend_text = BACKEND.read_text()
    for path, text in ((PATCH, patch_text), (BUILD, build_text), (BACKEND, backend_text)):
        compile(text, str(path), "exec")

    # Base and target versions.
    assert "5.12.002" in patch_text, "base must stay 5.12.002"
    assert "put('etc/2pny/version','5.15.000\\n',0o644)" in patch_text, "version must become 5.15.000"
    assert "BACKUP = '.pre-5.15'" in patch_text
    assert "5.15.000" in build_text and "IMAGE_515_VALIDATED" in build_text

    # YSF-515: auto-reconnect via systemd drop-in (not an RF-script rewrite).
    assert "2pny-ysfgateway.service.d/515-resilience.conf" in patch_text
    assert "Restart=always" in patch_text

    # 5.14 inheritance preserved (never-freeze wizard + responsive banner).
    for marker in ("pny514-css", "WIZ-514", "UI-514", "check_ap_health"):
        assert marker in patch_text, "lost 5.14/5.13.003 inheritance: " + marker

    # Backend: chains 5.14, bumps version, fixes OTA tag parse, times profile-apply.
    assert "ci/prepare-5.14-backend.py" in backend_text, "5.15 backend must chain 5.14"
    assert 'appVersion            = "5.15.000"' in backend_text
    assert 'TrimPrefix(rel.Tag,"pu2pny-")' in backend_text, "OTA tag normalisation missing"
    assert "PERF-515" in backend_text and "took_ms" in backend_text, "profile-apply timing missing"

    # The protected RF scripts and probe are not rewritten by the overlay.
    for protected in ("sbin/2pny-hardware-probe", "sbin/2pny-rf-apply", "sbin/2pny-protocol-network-apply"):
        assert protected not in patch_text, "5.15 overlay must not rewrite protected file: " + protected

    print("5.15_OTA_YSF_PERF_SW_PASS")


if __name__ == "__main__":
    main()
