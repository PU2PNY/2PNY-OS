# PU2PNY-OS 0.3.31.113 — Baseline Guard

## Purpose

Prevent accidental regression of a component that already has protected baseline evidence. The guard runs before expensive build work and does not alter runtime.

## Protected baseline

Reference SHA: `1c91b26fd561eb7a727df896f2179fd951b6681a` (`pu2pny-os-0.3.31.110`).

Protected areas are classified in `ci/baseline-guard-config.json`:

- RF / MMDVM
- DMR
- D-Star
- YSF / C4FM
- Network / wizard
- Displays / Nextion

The path patterns are intentionally case-insensitive and conservative. A false positive is preferable to a silent change in a protected runtime area; an authorized change is still possible through an explicit dossier.

## REL-027 — Protected Baseline CI Gate

When a protected component changes, CI must fail before build unless the same diff contains:

1. `ci/baseline-overrides/<component>.json`;
2. exact list of protected files being changed;
3. explicit reason;
4. valid project requirement IDs;
5. rollback plan;
6. TEST_MATRIX case IDs;
7. minimum validation level (DOC/SW/VPS/HW/PROD);
8. synchronization of `PU2PNY-OS_MASTER_SPEC.md`, `PU2PNY-OS_CHANGELOG.md`, `PU2PNY-OS_RELEASE_STATUS.md` and `PU2PNY-OS_TEST_MATRIX.md`.

Passing the guard means only that the protected change is explicit and reviewable. It **does not** mean the component was tested or approved.

## TEST-027 — Baseline Guard regression tests

The SW test suite must prove at minimum:

- unprotected/document-only change passes;
- protected change without dossier fails;
- incomplete/wrong dossier fails;
- protected change with complete dossier and canonical-document synchronization passes.

## Rollback

The guard is additive CI governance. Rollback is removal/revert of the guard commits; it does not modify runtime, image contents, radio configuration or user data.

## Validation status

- DOC: IMPLEMENTED on candidate branch.
- SW: PENDING execution by CI runner.
- VPS: NOT APPLICABLE to the gate logic itself.
- HW: NOT APPLICABLE.
- PROD: NOT APPROVED.
