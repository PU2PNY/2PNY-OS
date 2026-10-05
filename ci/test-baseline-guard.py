#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
GUARD_SOURCE = SOURCE_ROOT / "ci/baseline_guard.py"
CONFIG_SOURCE = SOURCE_ROOT / "ci/baseline-guard-config.json"
CANONICAL = [
    "PU2PNY-OS_MASTER_SPEC.md",
    "PU2PNY-OS_CHANGELOG.md",
    "PU2PNY-OS_RELEASE_STATUS.md",
    "PU2PNY-OS_TEST_MATRIX.md",
]


def run(cwd: Path, *args: str, check=True):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check)


def write(path: Path, content: str = "x\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def commit(repo: Path, message: str):
    run(repo, "git", "add", ".")
    run(repo, "git", "commit", "-m", message)
    return run(repo, "git", "rev-parse", "HEAD").stdout.strip()


def make_repo() -> tuple[Path, str]:
    repo = Path(tempfile.mkdtemp(prefix="pny-baseline-guard-"))
    run(repo, "git", "init", "-q")
    run(repo, "git", "config", "user.name", "PU2PNY Test")
    run(repo, "git", "config", "user.email", "test@example.invalid")
    write(repo / "ci/baseline_guard.py", GUARD_SOURCE.read_text(encoding="utf-8"))
    cfg = json.loads(CONFIG_SOURCE.read_text(encoding="utf-8"))
    cfg["baseline_ref"] = "BASE_PLACEHOLDER"
    write(repo / "ci/baseline-guard-config.json", json.dumps(cfg, indent=2) + "\n")
    for doc in CANONICAL:
        write(repo / doc, "baseline\n")
    write(repo / "README.md", "baseline\n")
    write(repo / "src/2pny-display-detector.py", "baseline display\n")
    base = commit(repo, "baseline")
    cfg["baseline_ref"] = base
    write(repo / "ci/baseline-guard-config.json", json.dumps(cfg, indent=2) + "\n")
    base = commit(repo, "pin test baseline")
    cfg["baseline_ref"] = base
    write(repo / "ci/baseline-guard-config.json", json.dumps(cfg, indent=2) + "\n")
    base = commit(repo, "final test baseline")
    return repo, base


def guard(repo: Path, base: str):
    return run(repo, "python3", "ci/baseline_guard.py", "--base", base, "--head", "HEAD", check=False)


def reset_to(repo: Path, base: str):
    run(repo, "git", "reset", "--hard", base)
    run(repo, "git", "clean", "-fd")


def dossier(repo: Path, base: str, changed_files: list[str], *, complete=True):
    configured = json.loads((repo / "ci/baseline-guard-config.json").read_text(encoding="utf-8"))["baseline_ref"]
    data = {
        "component": "display",
        "baseline_ref": configured if complete else "wrong",
        "reason": "DISPLAY-031 isolated display candidate",
        "requirement_ids": ["DISPLAY-031", "TEST-031"],
        "changed_files": changed_files,
        "rollback": "Revert display-only commit and restore previous writer selection.",
        "test_matrix_ids": ["DISPLAY-031-SW", "DISPLAY-031-HW"],
        "minimum_validation": "HW",
    }
    write(repo / "ci/baseline-overrides/display.json", json.dumps(data, indent=2) + "\n")


def test_docs_only_pass():
    repo, base = make_repo()
    try:
        write(repo / "README.md", "docs change\n")
        commit(repo, "docs")
        result = guard(repo, base)
        assert result.returncode == 0, result.stderr + result.stdout
    finally:
        shutil.rmtree(repo)


def test_protected_without_dossier_fails():
    repo, base = make_repo()
    try:
        write(repo / "src/2pny-display-detector.py", "changed\n")
        commit(repo, "bad protected change")
        result = guard(repo, base)
        assert result.returncode == 2
        assert "without a changed dossier" in result.stderr
    finally:
        shutil.rmtree(repo)


def test_incomplete_dossier_fails():
    repo, base = make_repo()
    try:
        changed = "src/2pny-display-detector.py"
        write(repo / changed, "changed\n")
        for doc in CANONICAL:
            write(repo / doc, "updated\n")
        dossier(repo, base, [changed], complete=False)
        commit(repo, "incomplete override")
        result = guard(repo, base)
        assert result.returncode == 2
        assert "baseline_ref must match" in result.stderr
    finally:
        shutil.rmtree(repo)


def test_complete_override_passes():
    repo, base = make_repo()
    try:
        changed = "src/2pny-display-detector.py"
        write(repo / changed, "changed\n")
        for doc in CANONICAL:
            write(repo / doc, "updated\n")
        dossier(repo, base, [changed])
        commit(repo, "approved-scope protected change")
        result = guard(repo, base)
        assert result.returncode == 0, result.stderr + result.stdout
        assert "authorizes review only" in result.stdout
    finally:
        shutil.rmtree(repo)


def main():
    test_docs_only_pass()
    test_protected_without_dossier_fails()
    test_incomplete_dossier_fails()
    test_complete_override_passes()
    print("PASS: Baseline Guard positive/negative tests")


if __name__ == "__main__":
    main()
