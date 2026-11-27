# CI Gate Checklist: Ops platform dateutil pin (issue #4908)

**Purpose**: Confirm that the failure evidence and the gate scope are complete.
**Created**: 2026-11-26
**Feature**: `spec.md` and `design\research.md`

## Failure Evidence

- [x] CHK001 Run ID 45064318582 and job ID 137336951691 are named (research R1).
- [x] CHK002 The failing step `Install dependencies` is named with its command (RC-02).
- [x] CHK003 The conflict lines from the run log are quoted (research R1).
- [x] CHK004 The merge commit and the PR head are both named, and the difference is explained (research R2).

## Main Branch Health

- [x] CHK005 The same job passes on `main` in run 45774119357 (S-8).
- [x] CHK006 The ops pin on `main` is `2.9.0.post0` (RC-16).

## Upstream State

- [x] CHK007 The newest celery release pins the older version (RC-50, RC-53).
- [x] CHK008 The newest python-dateutil 2.x release is `2.9.0.post0` (RC-54).

## Gate Scope

- [x] CHK009 The ops job installs its own requirements file, and pip-audit scans root requirements only (RC-02, RC-09).
- [x] CHK010 Types, dead code, docstrings, and code quality exclude `tests/` (RC-10 to RC-14).
