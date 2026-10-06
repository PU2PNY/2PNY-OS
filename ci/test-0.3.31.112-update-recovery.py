#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src/2pny-update-manager-0.3.31.112.py"
spec = importlib.util.spec_from_file_location("pny_update_031112", MODULE)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_package(base: Path, *, version: str, from_version: str, files: dict[str, bytes], bad_payload_hash: bool = False,
                 target_override: str | None = None) -> tuple[Path, str]:
    package = base / f"{version}.tar.gz"
    entries = []
    for index, (path, data) in enumerate(files.items()):
        target = target_override if index == 0 and target_override else path
        value = digest(data)
        if bad_payload_hash and index == 0:
            value = "0" * 64
        entries.append({"path": target, "sha256": value, "size": len(data), "mode": "0644"})
    manifest = {
        "schema": 1,
        "version": version,
        "from_compatible": [from_version],
        "files": entries,
        "restart_units": ["2pnyd.service"],
        "health_units": ["2pnyd.service"],
    }
    with tarfile.open(package, "w:gz") as tf:
        raw = json.dumps(manifest, sort_keys=True).encode()
        ti = tarfile.TarInfo("manifest.json"); ti.size = len(raw); ti.mode = 0o644
        tf.addfile(ti, io.BytesIO(raw))
        for index, (path, data) in enumerate(files.items()):
            target = target_override if index == 0 and target_override else path
            name = "payload/" + target.lstrip("/")
            ti = tarfile.TarInfo(name); ti.size = len(data); ti.mode = 0o644
            tf.addfile(ti, io.BytesIO(data))
    return package, m.sha256_file(package)


def fake_paths(base: Path) -> object:
    root = base / "root"
    (root / "etc/2pny").mkdir(parents=True)
    (root / "etc/2pny/version").write_text("0.3.31.110\n")
    (root / "usr/share/2pny").mkdir(parents=True)
    return m.Paths(root=root.resolve(), state=(root / "var/lib/2pny/update-transactions").resolve(), version_file=root / "etc/2pny/version")


def assert_eq(left, right, message):
    if left != right:
        raise AssertionError(f"{message}: {left!r} != {right!r}")


def test_preflight_is_read_only(base: Path):
    paths = fake_paths(base / "preflight")
    target = paths.root / "usr/share/2pny/example.txt"
    target.write_text("old")
    package, package_sha = make_package(base, version="0.3.31.112", from_version="0.3.31.110",
                                        files={"/usr/share/2pny/example.txt": b"new"})
    plan = m.preflight(paths, package, package_sha, "0.3.31.112")
    assert_eq(plan.current_version, "0.3.31.110", "current version")
    assert_eq(target.read_text(), "old", "preflight modified active target")
    if paths.state.exists():
        raise AssertionError("preflight created transaction state")


def test_bad_outer_hash_fails_before_write(base: Path):
    paths = fake_paths(base / "bad-outer")
    target = paths.root / "usr/share/2pny/example.txt"; target.write_text("old")
    package, _ = make_package(base, version="0.3.31.112a", from_version="0.3.31.110",
                              files={"/usr/share/2pny/example.txt": b"new"})
    try:
        m.preflight(paths, package, "0" * 64, "0.3.31.112a")
        raise AssertionError("bad outer hash unexpectedly accepted")
    except m.UpdateError:
        pass
    assert_eq(target.read_text(), "old", "bad outer hash modified active target")


def test_bad_payload_hash_fails_before_write(base: Path):
    paths = fake_paths(base / "bad-payload")
    target = paths.root / "usr/share/2pny/example.txt"; target.write_text("old")
    package, package_sha = make_package(base, version="0.3.31.112b", from_version="0.3.31.110",
                                        files={"/usr/share/2pny/example.txt": b"new"}, bad_payload_hash=True)
    try:
        m.preflight(paths, package, package_sha, "0.3.31.112b")
        raise AssertionError("bad payload hash unexpectedly accepted")
    except m.UpdateError:
        pass
    assert_eq(target.read_text(), "old", "bad payload hash modified active target")


def test_path_traversal_rejected(base: Path):
    paths = fake_paths(base / "path")
    package, package_sha = make_package(base, version="0.3.31.112c", from_version="0.3.31.110",
                                        files={"/usr/share/2pny/example.txt": b"new"}, target_override="/etc/../root/pwn")
    try:
        m.preflight(paths, package, package_sha, "0.3.31.112c")
        raise AssertionError("path traversal unexpectedly accepted")
    except m.UpdateError:
        pass


def test_prepare_does_not_mutate_active_tree(base: Path):
    paths = fake_paths(base / "prepare")
    target = paths.root / "usr/share/2pny/example.txt"; target.write_text("old")
    package, package_sha = make_package(base, version="0.3.31.112d", from_version="0.3.31.110",
                                        files={"/usr/share/2pny/example.txt": b"new"})
    txid = m.prepare(paths, package, package_sha, "0.3.31.112d")
    t = m.transaction_paths(paths, txid)
    assert_eq(target.read_text(), "old", "prepare modified active target")
    meta = m.verify_backup(t)
    if not meta.get("archive_sha256"):
        raise AssertionError("backup has no archive digest")
    journal = json.loads(t["journal"].read_text())
    assert_eq(journal["phase"], "prepared", "transaction phase")


def test_activate_and_manual_rollback(base: Path):
    paths = fake_paths(base / "activate")
    target = paths.root / "usr/share/2pny/example.txt"; target.write_text("old")
    package, package_sha = make_package(base, version="0.3.31.112e", from_version="0.3.31.110",
                                        files={"/usr/share/2pny/example.txt": b"new"})
    txid = m.prepare(paths, package, package_sha, "0.3.31.112e")
    m.activate(paths, txid)
    assert_eq(target.read_text(), "new", "activation did not install staged file")
    assert_eq(paths.version_file.read_text().strip(), "0.3.31.112e", "version not activated")
    m.rollback(paths, txid)
    assert_eq(target.read_text(), "old", "manual rollback did not restore file")
    assert_eq(paths.version_file.read_text().strip(), "0.3.31.110", "manual rollback did not restore version")


def test_health_failure_auto_rolls_back(base: Path):
    paths = fake_paths(base / "health")
    target = paths.root / "usr/share/2pny/example.txt"; target.write_text("old")
    package, package_sha = make_package(base, version="0.3.31.112f", from_version="0.3.31.110",
                                        files={"/usr/share/2pny/example.txt": b"new"})
    txid = m.prepare(paths, package, package_sha, "0.3.31.112f")
    os.environ["PU2PNY_TEST_HEALTH_FAIL"] = "1"
    try:
        try:
            m.activate(paths, txid)
            raise AssertionError("injected health failure unexpectedly committed")
        except m.UpdateError:
            pass
    finally:
        os.environ.pop("PU2PNY_TEST_HEALTH_FAIL", None)
    assert_eq(target.read_text(), "old", "automatic rollback did not restore file")
    assert_eq(paths.version_file.read_text().strip(), "0.3.31.110", "automatic rollback did not restore version")
    journal = json.loads(m.transaction_paths(paths, txid)["journal"].read_text())
    assert_eq(journal["phase"], "rolled_back", "auto rollback phase")


def test_tampered_backup_blocks_activation(base: Path):
    paths = fake_paths(base / "tamper")
    target = paths.root / "usr/share/2pny/example.txt"; target.write_text("old")
    package, package_sha = make_package(base, version="0.3.31.112g", from_version="0.3.31.110",
                                        files={"/usr/share/2pny/example.txt": b"new"})
    txid = m.prepare(paths, package, package_sha, "0.3.31.112g")
    t = m.transaction_paths(paths, txid)
    with t["backup"].open("ab") as handle:
        handle.write(b"tamper")
    try:
        m.activate(paths, txid)
        raise AssertionError("tampered backup unexpectedly accepted")
    except m.UpdateError:
        pass
    assert_eq(target.read_text(), "old", "tampered backup allowed active mutation")


def main():
    tests = [
        test_preflight_is_read_only,
        test_bad_outer_hash_fails_before_write,
        test_bad_payload_hash_fails_before_write,
        test_path_traversal_rejected,
        test_prepare_does_not_mutate_active_tree,
        test_activate_and_manual_rollback,
        test_health_failure_auto_rolls_back,
        test_tampered_backup_blocks_activation,
    ]
    with tempfile.TemporaryDirectory(prefix="pny-update-test-") as tmp:
        base = Path(tmp)
        for index, test in enumerate(tests):
            case = base / f"case-{index}"; case.mkdir()
            test(case)
            print(f"PASS {test.__name__}")
    print(f"PASS: {len(tests)} update/backup/recovery tests")


if __name__ == "__main__":
    main()
