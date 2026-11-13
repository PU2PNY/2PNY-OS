#!/usr/bin/env python3
"""NET-512: teste do transplante do painel nas imagens Armbian, sem root/RF."""
import importlib.util
import os
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("board512", REPO / "ci/build-board-5.12.py")
board = importlib.util.module_from_spec(spec)
spec.loader.exec_module(board)


def setup(tmp, panel=True, wants=True):
    root = Path(tmp) / "target"
    source = Path(tmp) / "source"
    units = source / "etc/systemd/system"
    units.mkdir(parents=True)
    (units / "2pny-network-core.service").write_text("[Unit]\nDescription=rede\n")
    if panel:
        (units / "2pnyd.service").write_text(
            "[Unit]\nDescription=PU2PNY local panel\n"
            "[Service]\nExecStart=/usr/local/bin/2pnyd\n"
            "[Install]\nWantedBy=multi-user.target\n"
        )
    if wants:
        wanted = units / "multi-user.target.wants"
        wanted.mkdir()
        (wanted / "2pnyd.service").symlink_to("../2pnyd.service")
        (wanted / "2pny-network-core.service").symlink_to("../2pny-network-core.service")
    timer = units / "2pny-hostfiles-update.timer"
    timer.write_text("[Timer]\nOnBootSec=5min\n")
    wanted_timer = units / "timers.target.wants"
    wanted_timer.mkdir()
    (wanted_timer / timer.name).symlink_to("../2pny-hostfiles-update.timer")
    (units / "pu2pny-capabilities.service").write_text("[Service]\nType=oneshot\n")
    return root, source


with tempfile.TemporaryDirectory() as td:
    root, source = setup(td)
    assert "2pnyd.service" not in [p.name for p in
            (source / "etc/systemd/system").glob("2pny-*")], "reprodução da falha 5.11"
    board.stage_pu2pny_units(root, source)
    target = root / "etc/systemd/system"
    assert (target / "2pnyd.service").is_file()
    assert (target / "2pnyd.service").read_bytes() == (
        source / "etc/systemd/system/2pnyd.service").read_bytes()
    link = target / "multi-user.target.wants/2pnyd.service"
    assert link.is_symlink() and os.path.basename(os.readlink(link)) == "2pnyd.service"
    assert (target / "multi-user.target.wants/2pny-network-core.service").is_symlink()
    assert (target / "timers.target.wants/2pny-hostfiles-update.timer").is_symlink()
    assert (target / "pu2pny-capabilities.service").is_file()

with tempfile.TemporaryDirectory() as td:
    root, source = setup(td, wants=False)
    try:
        board.stage_pu2pny_units(root, source)
    except AssertionError as exc:
        assert "não habilitado" in str(exc)
    else:
        raise AssertionError("a imagem sem habilitação do painel deveria falhar")

with tempfile.TemporaryDirectory() as td:
    root, source = setup(td, panel=False)
    try:
        board.stage_pu2pny_units(root, source)
    except AssertionError as exc:
        assert "unit 2pnyd ausente" in str(exc)
    else:
        raise AssertionError("a imagem sem unit 2pnyd deveria falhar")

print("TEST_NET_512_BOARD_HTTP_UNIT_OK")
