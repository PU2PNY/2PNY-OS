#!/usr/bin/env python3
"""PU2PNY-OS 5.14 software regression checks.

5.14 is a strict superset of 5.13.003: it keeps every 5.13.003 overlay change
and adds only the never-freeze wizard, the responsive banner and a bounded,
honest hardware fallback that never touches the protected probe.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "ci/patch-image-5.14.py"
BUILD = ROOT / "ci/build-5.14.py"
BACKEND = ROOT / "ci/prepare-5.14-backend.py"


def main():
    patch_text = PATCH.read_text()
    build_text = BUILD.read_text()
    backend_text = BACKEND.read_text()
    for path, text in ((PATCH, patch_text), (BUILD, build_text), (BACKEND, backend_text)):
        compile(text, str(path), "exec")

    # Base and target versions.
    assert "5.12.002" in patch_text, "base must stay 5.12.002"
    assert "put('etc/2pny/version','5.14.000\\n',0o644)" in patch_text, "version must become 5.14.000"
    assert "BACKUP = '.pre-5.14'" in patch_text
    assert "5.14.000" in build_text and "IMAGE_514_VALIDATED" in build_text

    # Wizard never-freeze + responsive banner (UI-514 / WIZ-514).
    for marker in ("pny514-css", "window.__pny514", "WIZ-514", "UI-514", "toBasic"):
        assert marker in patch_text, "missing wizard marker: " + marker

    # 5.13.003 inheritance must be preserved (AP health, dnsmasq leasefile, oled rotation).
    for marker in ("check_ap_health", "dhcp-leasefile=%s/dnsmasq-ap.leases", "enable_ap_forwarding(){",
                   "oledRotation", "ui-common-0.3.0.js"):
        assert marker in patch_text, "lost 5.13.003 inheritance: " + marker

    # Backend: chains 5.13.003, bumps version, shortens probe wait, never touches the probe binary.
    assert "ci/prepare-5.13.003-backend.py" in backend_text, "5.14 backend must chain 5.13.003"
    assert 'appVersion            = "5.14.000"' in backend_text
    assert "writeHardwareProbeFallback514" in backend_text
    assert '"-k", "2", "30", "/usr/local/sbin/2pny-hardware-probe"' in backend_text
    assert 'writeHardwareState("error", "hardware", msg)' in backend_text
    # The protected probe is only executed, never rewritten by the overlay.
    assert "sbin/2pny-hardware-probe" not in patch_text, \
        "5.14 overlay must not write the protected hardware probe"

    print("5.14_WIZARD_BANNER_SW_PASS")


if __name__ == "__main__":
    main()
