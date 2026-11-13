#!/usr/bin/env python3
"""BOOT-512: simulação do boot opcional e do preflight; nenhum comando de sistema."""
import importlib.util
import os
import tempfile
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("boot512", REPO/"ci/patch-image-5.12.py")
boot=importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)

def fixture(tmp):
    root=Path(tmp)
    version=root/"etc/2pny/version"
    version.parent.mkdir(parents=True)
    version.write_text("5.11.000\n")
    units=root/"etc/systemd/system"
    wants=units/"multi-user.target.wants"
    timers=units/"timers.target.wants"
    wants.mkdir(parents=True)
    timers.mkdir(parents=True)
    for name in ("2pny-auto-maintenance","2pny-hostfiles-update"):
        (units/f"{name}.service").write_text(
            "[Unit]\nDescription=fixture\n[Service]\nType=oneshot\nExecStart=/bin/true\n")
        dropin=units/f"{name}.service.d/60-delay.conf"
        dropin.parent.mkdir()
        dropin.write_text("[Service]\nExecStartPre=/bin/sleep 300\n")
        (wants/f"{name}.service").symlink_to(f"../{name}.service")
    (units/"2pny-hostfiles-update.timer").write_text(
        "[Timer]\nOnBootSec=5min\nUnit=2pny-hostfiles-update.service\n")
    (timers/"2pny-hostfiles-update.timer").symlink_to("../2pny-hostfiles-update.timer")
    return root

with tempfile.TemporaryDirectory() as td:
    root=fixture(td)
    before=(root/"etc/systemd/system/2pny-auto-maintenance.service").read_bytes()
    boot.apply(root)
    assert (root/"etc/2pny/version").read_text().strip()=="5.12.000"
    assert (root/"etc/2pny/version.pre-5.12").read_text().strip()=="5.11.000"
    for name in ("2pny-auto-maintenance","2pny-hostfiles-update"):
        assert not (root/f"etc/systemd/system/{name}.service.d/60-delay.conf").exists()
        backup=root/f"etc/systemd/system/{name}.service.d/60-delay.conf.pre-5.12"
        assert "sleep 300" in backup.read_text()
        assert not (root/f"etc/systemd/system/multi-user.target.wants/{name}.service").exists()
    assert (root/"etc/systemd/system/2pny-auto-maintenance.service").read_bytes()==before
    assert "OnBootSec=8min" in (root/"etc/systemd/system/2pny-auto-maintenance.timer").read_text()
    assert (root/"etc/systemd/system/timers.target.wants/2pny-auto-maintenance.timer").is_symlink()
    assert (root/"etc/systemd/system/timers.target.wants/2pny-hostfiles-update.timer").is_symlink()
    try:boot.apply(root)
    except AssertionError:pass
    else:raise AssertionError("aplicação duplicada não foi rejeitada")

with tempfile.TemporaryDirectory() as td:
    root=fixture(td)
    (root/"etc/systemd/system/timers.target.wants/2pny-hostfiles-update.timer").unlink()
    try:boot.apply(root)
    except AssertionError as exc:
        assert "timer de hostfiles" in str(exc)
    else:raise AssertionError("falha de pré-validação não rejeitada")
    assert (root/"etc/2pny/version").read_text().strip()=="5.11.000"
    assert not (root/"etc/2pny/version.pre-5.12").exists()
    assert (root/"etc/systemd/system/multi-user.target.wants/2pny-auto-maintenance.service").is_symlink()
print("TEST_BOOT_512_DEFERRED_MAINTENANCE_OK")
