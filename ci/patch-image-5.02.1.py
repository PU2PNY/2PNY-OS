#!/usr/bin/env python3
"""Offline 5.02.1 overlay on the published 5.02 image (DISPLAY-045, NET-045).

Never runs target binaries and never touches RF configuration, MMDVMHost,
gateways, NextionDriver, MMDVM-Display, HMI/TFT or the 2pnyd daemon. Both edits
are surgical text replacements that must match exactly once, so an unexpected
base file aborts the build instead of being silently overwritten.
"""
import shutil
import sys
from pathlib import Path

root, arch = Path(sys.argv[1]).resolve(), sys.argv[2]
repo = Path(__file__).resolve().parents[1]
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.02.000'


def replace(path, old, new, count=1):
    p = root/path
    text = p.read_text()
    assert text.count(old) == count, (str(path), old[:80], text.count(old))
    p.write_text(text.replace(old, new))


def backup(path):
    src = root/path
    dst = root/(path + '.pre-5.02.1')
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)


# DISPLAY-045: the boot probe's "mmdvm_display_candidate" must not hide the saved Nextion profile.
display_apply = 'usr/local/sbin/2pny-display-apply'
backup(display_apply)
replace(display_apply,
        "    # Never displace an actual OLED/LCD/TFT classification.\n"
        "    if detected not in ('', 'unknown', 'none'):\n"
        "        return d",
        "    # DISPLAY-045: after boot the probe records class=display_candidate with\n"
        "    # state=mmdvm_display_candidate when nothing was proven yet. That is not an\n"
        "    # OLED/LCD classification and must not discard the saved user profile.\n"
        "    unproven_modem_port = (detected == 'display_candidate'\n"
        "                           and d.get('state') == 'mmdvm_display_candidate')\n"
        "    # Never displace an actual OLED/LCD/TFT classification.\n"
        "    if detected not in ('', 'unknown', 'none') and not unproven_modem_port:\n"
        "        return d")

# NET-045: NetworkManager must never give up auto-reconnecting a saved Wi-Fi profile.
wifi_apply = 'usr/local/sbin/2pny-wifi-apply'
backup(wifi_apply)
replace(wifi_apply,
        '"connection.autoconnect-priority", str(ns.priority)])',
        '"connection.autoconnect-priority", str(ns.priority), "connection.autoconnect-retries", "0"])',
        count=2)

# NET-045: repair profiles saved by earlier versions, once per boot.
reconcile = root/'usr/local/sbin/2pny-wifi-retry-reconcile'
assert not reconcile.exists()
shutil.copyfile(repo/'runtime/5x/2pny-wifi-retry-reconcile.py', reconcile)
reconcile.chmod(0o755)
unit = root/'etc/systemd/system/2pny-wifi-retry-reconcile.service'
assert not unit.exists()
shutil.copyfile(repo/'runtime/5x/2pny-wifi-retry-reconcile.service', unit)
unit.chmod(0o644)
link = root/'etc/systemd/system/multi-user.target.wants/2pny-wifi-retry-reconcile.service'
assert not link.exists() and not link.is_symlink()
link.symlink_to('../2pny-wifi-retry-reconcile.service')

for filename in (display_apply, wifi_apply, 'usr/local/sbin/2pny-wifi-retry-reconcile'):
    compile((root/filename).read_bytes(), filename, 'exec')

(root/'etc/2pny/version').write_text('5.02.001\n')
print('PATCH_50201_OFFLINE_OK', arch)
