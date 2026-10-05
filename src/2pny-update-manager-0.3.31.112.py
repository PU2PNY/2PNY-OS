#!/usr/bin/env python3
"""PU2PNY-OS transactional update / backup / recovery candidate 0.3.31.112.

Design goals:
- preflight is read-only with respect to the active runtime tree;
- no activation is possible without a verified package, staged payload and
  verified backup/return point;
- every active-file replacement is atomic;
- any activation or health-check failure attempts automatic rollback;
- backup archives have their own manifest and SHA-256;
- arbitrary shell execution, curl|bash and unconstrained paths are forbidden.

This candidate is intentionally not wired into the runtime yet. The historical
0.3.20 updater remains untouched until this implementation passes SW/VPS and
its integration is explicitly approved.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA = 1
DEFAULT_ROOT = Path("/")
DEFAULT_STATE = Path("/var/lib/2pny/update-transactions")
DEFAULT_VERSION_FILE = Path("/etc/2pny/version")
ALLOWED_ROOTS = (
    "/usr/local/bin/",
    "/usr/local/sbin/",
    "/usr/local/lib/",
    "/usr/share/2pny/",
    "/etc/systemd/system/",
    "/etc/NetworkManager/dispatcher.d/",
    "/etc/2pny/",
)
DEFAULT_HEALTH_UNITS = (
    "2pny-station.service",
    "2pny-display-core.service",
    "2pny-netdiag.service",
    "2pnyd.service",
)
VERSION_RE = re.compile(r"^[A-Za-z0-9._-]{3,64}$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
UNIT_RE = re.compile(r"^[A-Za-z0-9_.@:-]+\.service$")


class UpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Paths:
    root: Path
    state: Path
    version_file: Path

    @classmethod
    def from_env(cls) -> "Paths":
        root = Path(os.environ.get("PU2PNY_ROOT", "/")).resolve()
        if root == DEFAULT_ROOT:
            state = DEFAULT_STATE
            version_file = DEFAULT_VERSION_FILE
        else:
            state = Path(os.environ.get("PU2PNY_STATE_ROOT", str(root / "var/lib/2pny/update-transactions"))).resolve()
            version_file = root / "etc/2pny/version"
        return cls(root=root, state=state, version_file=version_file)

    def host_path(self, absolute_target: str) -> Path:
        if not absolute_target.startswith("/"):
            raise UpdateError(f"target must be absolute: {absolute_target}")
        if self.root == DEFAULT_ROOT:
            return Path(absolute_target)
        return self.root / absolute_target.lstrip("/")


@dataclass
class PackageFile:
    path: str
    sha256: str
    mode: int | None
    size: int


@dataclass
class PackagePlan:
    package: Path
    package_sha256: str
    version: str
    manifest: dict[str, Any]
    files: list[PackageFile]
    current_version: str
    expanded_bytes: int
    backup_bytes: int


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, obj: Any, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(obj, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
        directory_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        tmp.unlink(missing_ok=True)


def validate_version(value: str) -> str:
    if not VERSION_RE.fullmatch(value or ""):
        raise UpdateError("invalid version")
    return value


def validate_sha(value: str) -> str:
    if not SHA_RE.fullmatch(value or ""):
        raise UpdateError("invalid SHA-256")
    return value.lower()


def allowed_target(path: str) -> bool:
    if not path.startswith("/") or ".." in Path(path).parts:
        return False
    return any(path.startswith(prefix) for prefix in ALLOWED_ROOTS)


def validate_unit(unit: str) -> str:
    if not UNIT_RE.fullmatch(unit):
        raise UpdateError(f"invalid service unit: {unit}")
    return unit


def safe_tar_member(name: str) -> bool:
    if not name or name.startswith("/"):
        return False
    parts = Path(name).parts
    return ".." not in parts and all(part not in ("", ".") for part in parts)


def ensure_no_symlink_parents(path: Path, stop: Path) -> None:
    """Reject activation through a symlinked parent inside the selected root."""
    stop = stop.resolve()
    current = path.parent
    while True:
        try:
            if current.is_symlink():
                raise UpdateError(f"symlinked target parent rejected: {current}")
        except OSError as exc:
            raise UpdateError(f"cannot inspect target parent {current}: {exc}") from exc
        if current == stop:
            return
        if stop not in current.parents:
            raise UpdateError(f"target escaped selected root: {path}")
        current = current.parent


def nearest_existing_parent(path: Path) -> Path:
    current = path
    while not current.exists():
        if current.parent == current:
            break
        current = current.parent
    return current


def read_current_version(paths: Paths) -> str:
    try:
        return paths.version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "unknown"


def compatible(manifest: dict[str, Any], current: str) -> bool:
    allowed = manifest.get("from_compatible")
    if allowed in (None, "", []):
        return False
    if isinstance(allowed, str):
        allowed = [allowed]
    if not isinstance(allowed, list):
        return False
    return current in [str(item) for item in allowed]


def read_manifest_from_tar(tf: tarfile.TarFile) -> dict[str, Any]:
    try:
        member = tf.getmember("manifest.json")
    except KeyError as exc:
        raise UpdateError("package has no manifest.json") from exc
    if not member.isfile() or member.size > 1024 * 1024:
        raise UpdateError("invalid manifest.json")
    handle = tf.extractfile(member)
    if handle is None:
        raise UpdateError("cannot read manifest.json")
    try:
        obj = json.loads(handle.read().decode("utf-8"))
    except Exception as exc:
        raise UpdateError(f"invalid manifest JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise UpdateError("manifest must be an object")
    return obj


def parse_manifest(manifest: dict[str, Any], expected_version: str) -> list[PackageFile]:
    if manifest.get("schema") != SCHEMA:
        raise UpdateError(f"unsupported manifest schema: {manifest.get('schema')!r}")
    version = validate_version(str(manifest.get("version") or ""))
    if version != expected_version:
        raise UpdateError(f"manifest version {version} does not match requested {expected_version}")
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise UpdateError("manifest files list is empty")
    out: list[PackageFile] = []
    seen: set[str] = set()
    for item in raw_files:
        if not isinstance(item, dict):
            raise UpdateError("manifest file entry is not an object")
        target = str(item.get("path") or "")
        digest = validate_sha(str(item.get("sha256") or ""))
        if not allowed_target(target):
            raise UpdateError(f"target outside allowlist: {target}")
        if target in seen:
            raise UpdateError(f"duplicate target: {target}")
        seen.add(target)
        mode_value = item.get("mode")
        mode: int | None = None
        if mode_value not in (None, ""):
            try:
                mode = int(str(mode_value), 8)
            except ValueError as exc:
                raise UpdateError(f"invalid mode for {target}") from exc
            if mode < 0o400 or mode > 0o777:
                raise UpdateError(f"unsafe mode for {target}")
        size = int(item.get("size") or 0)
        if size < 0:
            raise UpdateError(f"invalid size for {target}")
        out.append(PackageFile(path=target, sha256=digest, mode=mode, size=size))
    for unit in manifest.get("restart_units") or []:
        validate_unit(str(unit))
    for unit in manifest.get("health_units") or []:
        validate_unit(str(unit))
    return out


def payload_member_name(target: str) -> str:
    return "payload/" + target.lstrip("/")


def preflight(paths: Paths, package: Path, expected_sha: str, version: str) -> PackagePlan:
    """Read-only active-system validation. No active target or state file is written."""
    version = validate_version(version)
    expected_sha = validate_sha(expected_sha)
    package = package.resolve()
    if not package.is_file():
        raise UpdateError("package not found")
    actual = sha256_file(package)
    if actual != expected_sha:
        raise UpdateError("package SHA-256 mismatch")

    current = read_current_version(paths)
    expanded = 0
    backup_bytes = paths.version_file.stat().st_size if paths.version_file.is_file() else 0

    with tarfile.open(package, "r:gz") as tf:
        members = tf.getmembers()
        for member in members:
            if not safe_tar_member(member.name):
                raise UpdateError(f"unsafe archive member: {member.name}")
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise UpdateError(f"unsupported archive member type: {member.name}")
            if member.name != "manifest.json" and member.name != "payload" and not member.name.startswith("payload/"):
                raise UpdateError(f"archive member outside payload: {member.name}")
        manifest = read_manifest_from_tar(tf)
        files = parse_manifest(manifest, version)
        if not compatible(manifest, current):
            raise UpdateError(f"current version {current!r} is not listed in from_compatible")
        by_name = {m.name: m for m in members}
        for item in files:
            name = payload_member_name(item.path)
            member = by_name.get(name)
            if member is None or not member.isfile():
                raise UpdateError(f"payload missing: {item.path}")
            handle = tf.extractfile(member)
            if handle is None:
                raise UpdateError(f"cannot read payload: {item.path}")
            h = hashlib.sha256()
            total = 0
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
                total += len(chunk)
            if h.hexdigest() != item.sha256:
                raise UpdateError(f"payload SHA-256 mismatch: {item.path}")
            if item.size and item.size != total:
                raise UpdateError(f"payload size mismatch: {item.path}")
            expanded += total
            target = paths.host_path(item.path)
            ensure_no_symlink_parents(target, paths.root)
            if target.exists():
                if target.is_symlink():
                    raise UpdateError(f"symlink target rejected: {item.path}")
                if not target.is_file():
                    raise UpdateError(f"non-file target rejected: {item.path}")
                backup_bytes += target.stat().st_size
            parent = nearest_existing_parent(target.parent)
            if not os.access(parent, os.W_OK):
                raise UpdateError(f"target parent is not writable: {parent}")

    state_parent = nearest_existing_parent(paths.state)
    if not os.access(state_parent, os.W_OK):
        raise UpdateError(f"transaction state is not writable: {state_parent}")

    # Conservative capacity check: staged payload + backup + copy/metadata margin.
    required_state = max(16 * 1024 * 1024, expanded + backup_bytes + package.stat().st_size + 8 * 1024 * 1024)
    free_state = shutil.disk_usage(state_parent).free
    if free_state < required_state:
        raise UpdateError(f"insufficient free space for safe transaction: need {required_state}, have {free_state}")

    return PackagePlan(
        package=package,
        package_sha256=actual,
        version=version,
        manifest=manifest,
        files=files,
        current_version=current,
        expanded_bytes=expanded,
        backup_bytes=backup_bytes,
    )


def transaction_id(version: str, package_sha: str) -> str:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"{stamp}-{version}-{package_sha[:12]}"


def transaction_paths(paths: Paths, txid: str) -> dict[str, Path]:
    if not re.fullmatch(r"[A-Za-z0-9._-]{8,128}", txid):
        raise UpdateError("invalid transaction id")
    base = paths.state / txid
    return {
        "base": base,
        "stage": base / "stage",
        "backup": base / "backup.tar.gz",
        "backup_meta": base / "backup.json",
        "journal": base / "journal.json",
        "manifest": base / "manifest.json",
    }


def write_journal(t: dict[str, Path], phase: str, **extra: Any) -> None:
    current: dict[str, Any] = {}
    try:
        current = json.loads(t["journal"].read_text(encoding="utf-8"))
    except Exception:
        current = {}
    current.update(extra)
    current.update({"phase": phase, "updated": utc_now()})
    atomic_json(t["journal"], current)


def safe_extract_stage(plan: PackagePlan, stage: Path) -> None:
    stage.mkdir(parents=True, exist_ok=False)
    with tarfile.open(plan.package, "r:gz") as tf:
        by_name = {m.name: m for m in tf.getmembers()}
        for item in plan.files:
            member = by_name[payload_member_name(item.path)]
            handle = tf.extractfile(member)
            if handle is None:
                raise UpdateError(f"cannot extract staged payload: {item.path}")
            dst = stage / item.path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("wb") as out:
                shutil.copyfileobj(handle, out, 1024 * 1024)
                out.flush()
                os.fsync(out.fileno())
            if sha256_file(dst) != item.sha256:
                raise UpdateError(f"staged payload changed: {item.path}")
            os.chmod(dst, item.mode if item.mode is not None else 0o644)


def backup_arcname(target: str) -> str:
    return "root/" + target.lstrip("/")


def create_backup(paths: Paths, plan: PackagePlan, t: dict[str, Path]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    created: list[str] = []
    with tarfile.open(t["backup"], "w:gz") as tf:
        for item in plan.files:
            src = paths.host_path(item.path)
            if src.exists():
                if src.is_symlink() or not src.is_file():
                    raise UpdateError(f"backup target became unsafe: {item.path}")
                digest = sha256_file(src)
                tf.add(src, arcname=backup_arcname(item.path), recursive=False)
                entries.append({"path": item.path, "sha256": digest, "size": src.stat().st_size})
            else:
                created.append(item.path)
        version_target = "/etc/2pny/version"
        if paths.version_file.exists():
            digest = sha256_file(paths.version_file)
            tf.add(paths.version_file, arcname=backup_arcname(version_target), recursive=False)
            entries.append({"path": version_target, "sha256": digest, "size": paths.version_file.stat().st_size})
        else:
            created.append(version_target)
    os.chmod(t["backup"], 0o600)
    backup_hash = sha256_file(t["backup"])
    meta = {
        "schema": SCHEMA,
        "created_at": utc_now(),
        "from_version": plan.current_version,
        "to_version": plan.version,
        "archive": t["backup"].name,
        "archive_sha256": backup_hash,
        "entries": entries,
        "created_targets": sorted(set(created)),
    }
    atomic_json(t["backup_meta"], meta)
    return meta


def verify_backup(t: dict[str, Path]) -> dict[str, Any]:
    try:
        meta = json.loads(t["backup_meta"].read_text(encoding="utf-8"))
    except Exception as exc:
        raise UpdateError(f"invalid backup metadata: {exc}") from exc
    if meta.get("schema") != SCHEMA:
        raise UpdateError("unsupported backup metadata schema")
    digest = validate_sha(str(meta.get("archive_sha256") or ""))
    if not t["backup"].is_file() or sha256_file(t["backup"]) != digest:
        raise UpdateError("backup archive integrity check failed")
    entries = meta.get("entries")
    if not isinstance(entries, list):
        raise UpdateError("invalid backup entry list")
    for entry in entries:
        target = str(entry.get("path") or "")
        if target != "/etc/2pny/version" and not allowed_target(target):
            raise UpdateError(f"backup target outside allowlist: {target}")
        validate_sha(str(entry.get("sha256") or ""))
    return meta


def verify_staged(plan_manifest: dict[str, Any], stage: Path) -> list[PackageFile]:
    version = validate_version(str(plan_manifest.get("version") or ""))
    files = parse_manifest(plan_manifest, version)
    for item in files:
        src = stage / item.path.lstrip("/")
        if not src.is_file() or src.is_symlink():
            raise UpdateError(f"staged file missing/unsafe: {item.path}")
        if sha256_file(src) != item.sha256:
            raise UpdateError(f"staged file integrity failed: {item.path}")
    return files


def prepare(paths: Paths, package: Path, expected_sha: str, version: str) -> str:
    plan = preflight(paths, package, expected_sha, version)
    paths.state.mkdir(parents=True, exist_ok=True)
    os.chmod(paths.state, 0o700)
    txid = transaction_id(plan.version, plan.package_sha256)
    t = transaction_paths(paths, txid)
    if t["base"].exists():
        raise UpdateError("transaction already exists")
    t["base"].mkdir(mode=0o700)
    try:
        write_journal(
            t,
            "preflight_passed",
            transaction_id=txid,
            from_version=plan.current_version,
            to_version=plan.version,
            package_sha256=plan.package_sha256,
            activated=False,
            rolled_back=False,
        )
        safe_extract_stage(plan, t["stage"])
        atomic_json(t["manifest"], plan.manifest)
        write_journal(t, "staged")
        meta = create_backup(paths, plan, t)
        verify_backup(t)
        write_journal(t, "prepared", backup_sha256=meta["archive_sha256"])
        return txid
    except Exception:
        shutil.rmtree(t["base"], ignore_errors=True)
        raise


def run_systemctl(args: Iterable[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["systemctl", *list(args)], text=True, capture_output=True, timeout=timeout)


def real_runtime(paths: Paths) -> bool:
    return paths.root == DEFAULT_ROOT


def capture_health_baseline(paths: Paths, units: list[str]) -> dict[str, bool]:
    if not real_runtime(paths):
        return {unit: True for unit in units}
    result: dict[str, bool] = {}
    for unit in units:
        validate_unit(unit)
        result[unit] = run_systemctl(["is-active", "--quiet", unit], timeout=10).returncode == 0
    return result


def restart_and_health(paths: Paths, restart_units: list[str], health_units: list[str], baseline: dict[str, bool]) -> None:
    if not real_runtime(paths):
        if os.environ.get("PU2PNY_TEST_HEALTH_FAIL") == "1":
            raise UpdateError("injected test health failure")
        return
    if any(unit.endswith(".service") for unit in restart_units):
        run_systemctl(["daemon-reload"], timeout=20)
    for unit in restart_units:
        validate_unit(unit)
        result = run_systemctl(["try-restart", unit], timeout=30)
        if result.returncode not in (0,):
            raise UpdateError(f"service restart failed: {unit}: {result.stderr.strip()[:240]}")
    time.sleep(1.0)
    for unit in health_units:
        validate_unit(unit)
        if not baseline.get(unit, True):
            continue
        result = run_systemctl(["is-active", "--quiet", unit], timeout=10)
        if result.returncode != 0:
            raise UpdateError(f"health check failed: {unit}")


def atomic_install(src: Path, dst: Path, mode: int | None, root: Path) -> None:
    ensure_no_symlink_parents(dst, root)
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dst.name}.pny-update.", dir=str(dst.parent))
    tmp = Path(tmp_name)
    try:
        with src.open("rb") as inp, os.fdopen(fd, "wb") as out:
            shutil.copyfileobj(inp, out, 1024 * 1024)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp, mode if mode is not None else 0o644)
        os.replace(tmp, dst)
        directory_fd = os.open(dst.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        tmp.unlink(missing_ok=True)


def restore_backup(paths: Paths, t: dict[str, Path]) -> None:
    meta = verify_backup(t)
    entries = {str(entry["path"]): entry for entry in meta["entries"]}
    with tarfile.open(t["backup"], "r:gz") as tf:
        members = {m.name: m for m in tf.getmembers()}
        for target, entry in entries.items():
            member_name = backup_arcname(target)
            member = members.get(member_name)
            if member is None or not member.isfile() or not safe_tar_member(member.name):
                raise UpdateError(f"backup member missing/unsafe: {target}")
            handle = tf.extractfile(member)
            if handle is None:
                raise UpdateError(f"cannot read backup member: {target}")
            fd, tmp_name = tempfile.mkstemp(prefix="pny-restore-")
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "wb") as out:
                    shutil.copyfileobj(handle, out, 1024 * 1024)
                    out.flush()
                    os.fsync(out.fileno())
                if sha256_file(tmp) != str(entry["sha256"]).lower():
                    raise UpdateError(f"backup member digest mismatch: {target}")
                dst = paths.host_path(target)
                mode = stat.S_IMODE(member.mode)
                atomic_install(tmp, dst, mode, paths.root)
            finally:
                tmp.unlink(missing_ok=True)
    for target in meta.get("created_targets") or []:
        target = str(target)
        if target != "/etc/2pny/version" and not allowed_target(target):
            raise UpdateError(f"unsafe created target in backup metadata: {target}")
        dst = paths.host_path(target)
        if dst.exists() and not dst.is_symlink() and dst.is_file():
            dst.unlink()
    if real_runtime(paths):
        run_systemctl(["daemon-reload"], timeout=20)


def load_transaction(paths: Paths, txid: str) -> tuple[dict[str, Path], dict[str, Any], dict[str, Any]]:
    t = transaction_paths(paths, txid)
    if not t["base"].is_dir():
        raise UpdateError("transaction not found")
    try:
        journal = json.loads(t["journal"].read_text(encoding="utf-8"))
        manifest = json.loads(t["manifest"].read_text(encoding="utf-8"))
    except Exception as exc:
        raise UpdateError(f"transaction metadata invalid: {exc}") from exc
    return t, journal, manifest


def activate(paths: Paths, txid: str) -> None:
    t, journal, manifest = load_transaction(paths, txid)
    if journal.get("phase") != "prepared" or journal.get("activated") is True:
        raise UpdateError(f"transaction is not activatable: phase={journal.get('phase')}")
    verify_backup(t)
    files = verify_staged(manifest, t["stage"])
    restart_units = [validate_unit(str(x)) for x in (manifest.get("restart_units") or [])]
    health_units = [validate_unit(str(x)) for x in (manifest.get("health_units") or DEFAULT_HEALTH_UNITS)]
    baseline = capture_health_baseline(paths, health_units)
    write_journal(t, "activating", health_baseline=baseline)
    mutated = False
    try:
        for item in files:
            src = t["stage"] / item.path.lstrip("/")
            dst = paths.host_path(item.path)
            atomic_install(src, dst, item.mode, paths.root)
            mutated = True
        version_tmp = t["base"] / "new-version"
        version_tmp.write_text(str(manifest["version"]) + "\n", encoding="utf-8")
        atomic_install(version_tmp, paths.version_file, 0o644, paths.root)
        mutated = True
        restart_and_health(paths, restart_units, health_units, baseline)
        write_journal(t, "committed", activated=True, committed_at=utc_now())
    except BaseException as exc:
        if mutated:
            try:
                restore_backup(paths, t)
                write_journal(t, "rolled_back", activated=False, rolled_back=True, rollback_reason=str(exc)[:500])
            except Exception as rollback_exc:
                write_journal(
                    t,
                    "rollback_failed",
                    activated=False,
                    rolled_back=False,
                    rollback_reason=str(exc)[:500],
                    rollback_error=str(rollback_exc)[:500],
                )
                raise UpdateError(f"activation failed and rollback failed: {rollback_exc}") from exc
        raise


def rollback(paths: Paths, txid: str) -> None:
    t, journal, manifest = load_transaction(paths, txid)
    if journal.get("phase") not in ("committed", "rollback_failed"):
        raise UpdateError(f"transaction is not rollbackable: phase={journal.get('phase')}")
    restore_backup(paths, t)
    restart_units = [validate_unit(str(x)) for x in (manifest.get("restart_units") or [])]
    health_units = [validate_unit(str(x)) for x in (manifest.get("health_units") or DEFAULT_HEALTH_UNITS)]
    baseline = {unit: True for unit in health_units}
    restart_and_health(paths, restart_units, health_units, baseline)
    write_journal(t, "rolled_back", activated=False, rolled_back=True, manual_rollback_at=utc_now())


def list_status(paths: Paths) -> dict[str, Any]:
    out: list[dict[str, Any]] = []
    if paths.state.is_dir():
        for base in sorted(paths.state.iterdir(), reverse=True):
            if not base.is_dir():
                continue
            journal = base / "journal.json"
            try:
                data = json.loads(journal.read_text(encoding="utf-8"))
            except Exception:
                continue
            data["transaction_id"] = base.name
            out.append(data)
    return {"schema": SCHEMA, "current_version": read_current_version(paths), "transactions": out[:20]}


def acquire_global_lock(paths: Paths):
    paths.state.mkdir(parents=True, exist_ok=True)
    os.chmod(paths.state, 0o700)
    lock_path = paths.state / ".lock"
    handle = lock_path.open("a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise UpdateError("another update/recovery transaction is active") from exc
    return handle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PU2PNY-OS safe update/backup/recovery candidate")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("package", type=Path)
    p.add_argument("sha256")
    p.add_argument("version")
    p = sub.add_parser("prepare")
    p.add_argument("package", type=Path)
    p.add_argument("sha256")
    p.add_argument("version")
    p = sub.add_parser("activate")
    p.add_argument("transaction_id")
    p = sub.add_parser("rollback")
    p.add_argument("transaction_id")
    sub.add_parser("status")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = Paths.from_env()
    try:
        if args.command == "preflight":
            plan = preflight(paths, args.package, args.sha256, args.version)
            print(json.dumps({
                "ok": True,
                "phase": "preflight",
                "from_version": plan.current_version,
                "to_version": plan.version,
                "package_sha256": plan.package_sha256,
                "files": len(plan.files),
                "expanded_bytes": plan.expanded_bytes,
                "backup_bytes": plan.backup_bytes,
                "active_tree_written": False,
            }, ensure_ascii=False))
            return 0
        if args.command == "status":
            print(json.dumps(list_status(paths), ensure_ascii=False))
            return 0
        lock = acquire_global_lock(paths)
        try:
            if args.command == "prepare":
                txid = prepare(paths, args.package, args.sha256, args.version)
                print(json.dumps({"ok": True, "transaction_id": txid, "phase": "prepared"}, ensure_ascii=False))
            elif args.command == "activate":
                activate(paths, args.transaction_id)
                print(json.dumps({"ok": True, "transaction_id": args.transaction_id, "phase": "committed"}, ensure_ascii=False))
            elif args.command == "rollback":
                rollback(paths, args.transaction_id)
                print(json.dumps({"ok": True, "transaction_id": args.transaction_id, "phase": "rolled_back"}, ensure_ascii=False))
            return 0
        finally:
            lock.close()
    except UpdateError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
