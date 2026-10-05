#!/usr/bin/env python3
"""Fail-before-build guard for protected PU2PNY-OS baselines.

This guard does not decide whether a change is technically correct. It prevents
protected runtime areas from changing silently. A protected change must carry
an explicit, reviewable dossier plus synchronized canonical project records.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "ci/baseline-guard-config.json"
REQ_ID = re.compile(r"^(?:ARCH|BOOT|NET|WIZ|HW|RF|PROTO|LIVE|UI|DISPLAY|APRS|QRZ|P2P|DATA|UPDATE|BACKUP|SEC|PERF|TEST|REL)-\d+$")


class GuardError(RuntimeError):
    pass


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GuardError(f"cannot read JSON {path}: {exc}") from exc


def git_lines(*args: str) -> list[str]:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if p.returncode:
        raise GuardError(p.stderr.strip() or f"git {' '.join(args)} failed")
    return [line.strip() for line in p.stdout.splitlines() if line.strip()]


def changed_files(base: str, head: str) -> list[str]:
    return git_lines("diff", "--name-only", f"{base}...{head}")


def matches(path: str, patterns: list[str]) -> bool:
    value = path.lower()
    return any(fnmatch.fnmatchcase(value, str(pattern).lower()) for pattern in patterns)


def classify(changed: list[str], config: dict) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, spec in config.get("components", {}).items():
        if not spec.get("protected"):
            continue
        hits = sorted({p for p in changed if matches(p, spec.get("patterns", []))})
        if hits:
            result[name] = hits
    return result


def nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_dossier(component: str, protected_files: list[str], changed: set[str], config: dict) -> list[str]:
    errors: list[str] = []
    rel = f"ci/baseline-overrides/{component}.json"
    path = ROOT / rel
    if rel not in changed:
        return [f"{component}: protected files changed without a changed dossier: {rel}"]
    if not path.is_file():
        return [f"{component}: dossier missing from working tree: {rel}"]
    try:
        data = load_json(path)
    except GuardError as exc:
        return [f"{component}: {exc}"]

    if data.get("component") != component:
        errors.append(f"{component}: dossier component must be exactly {component!r}")
    if data.get("baseline_ref") != config.get("baseline_ref"):
        errors.append(f"{component}: dossier baseline_ref must match protected baseline {config.get('baseline_ref')}")
    for field in ("reason", "rollback"):
        if not nonempty_string(data.get(field)):
            errors.append(f"{component}: dossier field {field!r} must be a non-empty string")

    reqs = data.get("requirement_ids")
    if not isinstance(reqs, list) or not reqs or any(not isinstance(x, str) or not REQ_ID.fullmatch(x) for x in reqs):
        errors.append(f"{component}: requirement_ids must contain valid project requirement IDs")

    tests = data.get("test_matrix_ids")
    if not isinstance(tests, list) or not tests or any(not isinstance(x, str) or not x.strip() for x in tests):
        errors.append(f"{component}: test_matrix_ids must be a non-empty string list")

    level = data.get("minimum_validation")
    if level not in config.get("validation_levels", []):
        errors.append(f"{component}: minimum_validation must be one of {config.get('validation_levels', [])}")

    declared = data.get("changed_files")
    if not isinstance(declared, list) or any(not isinstance(x, str) for x in declared):
        errors.append(f"{component}: changed_files must be a string list")
    else:
        missing = sorted(set(protected_files) - set(declared))
        extras = sorted(set(declared) - set(changed))
        if missing:
            errors.append(f"{component}: dossier does not declare protected changes: {', '.join(missing)}")
        if extras:
            errors.append(f"{component}: dossier declares files not changed in this diff: {', '.join(extras)}")

    return errors


def run_guard(base: str, head: str, config_path: Path) -> int:
    config = load_json(config_path)
    changed_list = changed_files(base, head)
    changed = set(changed_list)
    protected = classify(changed_list, config)

    print(f"Baseline Guard: base={base} head={head}")
    print(f"Changed files: {len(changed_list)}")
    if not protected:
        print("PASS: no protected baseline component changed")
        return 0

    print("Protected components touched:")
    for component, paths in protected.items():
        print(f"  - {component}: {len(paths)} file(s)")
        for path in paths:
            print(f"      {path}")

    errors: list[str] = []
    canonical = set(config.get("canonical_documents", []))
    missing_docs = sorted(canonical - changed)
    if missing_docs:
        errors.append("protected change requires synchronized canonical documents in the same diff: " + ", ".join(missing_docs))

    for component, paths in protected.items():
        errors.extend(validate_dossier(component, paths, changed, config))

    if errors:
        print("FAIL: protected baseline change is not fully justified", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 2

    print("PASS: protected changes have explicit scope, rollback, requirements and test evidence plan")
    print("NOTE: this gate authorizes review only; it does not mark SW/VPS/HW/PROD validation as approved.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Git base ref/SHA; defaults to config baseline_ref")
    parser.add_argument("--head", default="HEAD", help="Git head ref/SHA")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    try:
        config = load_json(config_path)
        base = args.base or config.get("baseline_ref")
        if not nonempty_string(base):
            raise GuardError("baseline_ref is missing")
        return run_guard(str(base), args.head, config_path)
    except GuardError as exc:
        print(f"Baseline Guard configuration/error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
