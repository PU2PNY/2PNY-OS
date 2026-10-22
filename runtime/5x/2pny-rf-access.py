#!/usr/bin/env python3
"""Transactional, fail-closed RF access policy for the *existing* MMDVMHost.

No settings are applied at boot. The explicit 'apply' operation edits ONLY
SelfOnly/WhiteList in the supported radio sections. No frequency, slot,
gateway, modem UART, callsign or security token is touched.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

DEFAULT_INI = Path("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
DEFAULT_STATE = Path("/var/lib/2pny/access/policy.json")
DEFAULT_UNIT = "2pny-mmdvmhost.service"
CONTROL = ("D-Star", "DMR", "System Fusion", "P25", "NXDN")
CALL = re.compile(r"^[A-Z0-9]{3,8}$")
RADIO_ID = re.compile(r"^[0-9]{6,8}$")


class AccessError(Exception):
    pass


def sections(text: str) -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            found.setdefault(section, {})
        elif section and line and not line.startswith(("#", ";")) and "=" in line:
            k, v = line.split("=", 1)
            found[section][k.strip().lower()] = v.strip().split("#", 1)[0].strip()
    return found


def patch_key(src: str, section: str, values: dict[str, str]) -> str:
    """Patch only an existing, unambiguous INI section, preserving other bytes."""
    lines = src.splitlines(keepends=True)
    positions = [i for i, s in enumerate(lines) if s.strip().lower() == "[" + section.lower() + "]"]
    if len(positions) != 1:
        raise AccessError(f"missing_or_ambiguous_section:{section}")
    start = positions[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].strip().startswith("[") and lines[i].strip().endswith("]")), len(lines))
    for key, val in values.items():
        pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=", re.I)
        matches = [i for i in range(start, end) if pattern.match(lines[i])]
        if len(matches) > 1:
            raise AccessError(f"ambiguous_key:{section}.{key}")
        if matches:
            lines[matches[0]] = f"{key}={val}\n"
        else:
            lines.insert(end, f"{key}={val}\n")
            end += 1
    return "".join(lines)


def normalize_id(value: str) -> str:
    value = str(value).strip()
    if not RADIO_ID.fullmatch(value) or int(value) == 0:
        raise AccessError("invalid_radio_id")
    return value


def normalize_call(value: str) -> str:
    value = str(value).strip().upper()
    if not CALL.fullmatch(value):
        raise AccessError("invalid_callsign")
    return value


def enabled(data: dict[str, dict[str, str]], section: str) -> bool:
    return data.get(section, {}).get("enable", "0") == "1"


def render_policy(src: str, request: dict) -> tuple[str, dict]:
    mode = request.get("mode")
    if mode not in ("private", "semi_public", "public"):
        raise AccessError("invalid_access_mode")
    if mode == "public" and request.get("confirmation") != "ABRIR RF PUBLICO":
        raise AccessError("public_requires_explicit_confirmation")
    data = sections(src)
    active = [name for name in CONTROL if enabled(data, name)]
    if not active:
        raise AccessError("no_active_supported_rf_protocol")
    allowed = request.get("allowed", [])
    if not isinstance(allowed, list) or len(allowed) > 200:
        raise AccessError("invalid_allowed_list")
    ids: set[str] = set()
    calls: set[str] = set()
    for entry in allowed:
        if not isinstance(entry, dict):
            raise AccessError("invalid_allowed_entry")
        if entry.get("dmr_id"):
            ids.add(normalize_id(entry["dmr_id"]))
        if entry.get("callsign"):
            calls.add(normalize_call(entry["callsign"]))
        if not entry.get("dmr_id") and not entry.get("callsign"):
            raise AccessError("empty_allowed_entry")
    if mode == "semi_public":
        if not allowed:
            raise AccessError("empty_acl_fail_closed")
        # These host controls have SelfOnly but no equivalent source-ID ACL
        # in the pinned host implementation. Never claim 'semi' there.
        unsupported = [x for x in ("System Fusion", "P25", "NXDN") if x in active]
        if unsupported:
            raise AccessError("semi_public_not_supported_for_active:" + ",".join(unsupported))
        if "DMR" in active and not ids:
            raise AccessError("semi_public_dmr_requires_ids")
        if "D-Star" in active and not calls:
            raise AccessError("semi_public_dstar_requires_callsigns")
    if "DMR" in active:
        owner_id = normalize_id(data.get("General", {}).get("id", ""))
        # ESSID extends the hotspot identity but RF self-only uses bare ID.
        if len(owner_id) == 8 and int(owner_id) > 9999999:
            owner_id = owner_id[:-1]
        ids.add(owner_id)
    if "D-Star" in active:
        calls.add(normalize_call(data.get("General", {}).get("callsign", "")))
    # Require all expected sections to exist before writing anything.
    for section in active:
        if section not in data:
            raise AccessError(f"missing_section:{section}")
    result = src
    for section in active:
        modifications = {"SelfOnly": "1" if mode == "private" else "0"}
        if section == "DMR":
            modifications["WhiteList"] = ",".join(sorted(ids)) if mode == "semi_public" else ""
        if section == "D-Star":
            modifications["WhiteList"] = ",".join(sorted(calls)) if mode == "semi_public" else ""
        result = patch_key(result, section, modifications)
    return result, {"mode": mode, "supported_active": active,
                    "authorized_callsigns": sorted(calls) if mode == "semi_public" else [],
                    "authorized_dmr_ids": sorted(ids) if mode == "semi_public" else []}


def atomic_write(target: Path, data: bytes, mode: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(dir=target.parent, prefix="." + target.name + ".")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(path, mode)
        os.replace(path, target)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def service(op: str, unit: str) -> bool:
    return subprocess.run(["systemctl", op, unit], check=False,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=25).returncode == 0


def apply(ini: Path, state: Path, unit: str, request: dict, dry_run: bool) -> dict:
    if not ini.is_file():
        raise AccessError("mmdvmhost_config_missing")
    with open(ini, "rb") as inp:
        fcntl.flock(inp.fileno(), fcntl.LOCK_EX)
        original = inp.read()
        if len(original) > 512 * 1024:
            raise AccessError("unexpected_config_size")
        try:
            current = original.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AccessError("config_not_utf8") from exc
        updated, state_doc = render_policy(current, request)
        if dry_run:
            return {"ok": True, "dry_run": True, **state_doc}
        if not service("is-active", unit):
            raise AccessError("mmdvmhost_not_active_refusing_change")
        stat = ini.stat()
        snapshot = state.with_suffix(".rollback.ini")
        # Keep rollback in root-only directory, never web-accessible.
        state.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(state.parent, 0o700)
        atomic_write(snapshot, original, 0o600)
        try:
            atomic_write(ini, updated.encode("utf-8"), stat.st_mode & 0o777)
            if not service("restart", unit) or not service("is-active", unit):
                raise AccessError("mmdvmhost_failed_after_policy_change")
            atomic_write(state, (json.dumps(state_doc, sort_keys=True) + "\n").encode(), 0o600)
        except Exception as exc:
            atomic_write(ini, original, stat.st_mode & 0o777)
            service("restart", unit)
            raise AccessError("policy_rolled_back:" + str(exc)) from exc
        return {"ok": True, "applied": True, **state_doc}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("status", "check", "apply"))
    parser.add_argument("--ini", type=Path, default=DEFAULT_INI)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--unit", default=DEFAULT_UNIT)
    parser.add_argument("--request", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "status":
            if args.state.is_file():
                doc = json.loads(args.state.read_text())
                print(json.dumps({"ok": True, "policy": doc}, ensure_ascii=False))
            else:
                print(json.dumps({"ok": True, "policy": {"mode": "legacy_unchanged", "verified": False}}))
            return 0
        if args.request is None or not args.request.is_file() or args.request.stat().st_size > 32768:
            raise AccessError("request_required")
        request = json.loads(args.request.read_text())
        if not isinstance(request, dict):
            raise AccessError("invalid_request")
        result = apply(args.ini, args.state, args.unit, request, args.action == "check")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (AccessError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
