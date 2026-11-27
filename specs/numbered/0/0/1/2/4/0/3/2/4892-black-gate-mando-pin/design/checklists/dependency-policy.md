# Dependency Policy Checklist: Black Gate Failure From the Mando Pin

**Purpose**: Check the dependency rules that this change follows.
**Created**: 2026-11-26
**Feature**: `spec.md`

## Pins and Lock

- [x] CHK001 Mando stays at 0.7.1 in `uv.lock` (R-16).
- [x] CHK002 `requirements-dev.txt` stays a uv export output, so no hand edit is made (R-05).
- [x] CHK003 `requirements.txt` holds no mando pin (R-19).
- [x] CHK004 Radon 6.0.1 stays the dev pin (R-03, R-18).

## Dependabot

- [x] CHK005 The ignore rule uses the package manager pattern (R-45).
- [x] CHK006 The ignore rule covers each rejected sample release (`design\contracts\dependabot-mando-ignore.md`).
- [x] CHK007 The change adds one ignore rule. It does not disable an update stream (R-24).
- [x] CHK008 Pull request #4888 stays open. The owner decides its next step (D-4, U-2).

## Radon Constraint

- [x] CHK009 PyPI metadata states the range `<0.8,>=0.6` (R-46).
- [x] CHK010 The PyPI project page lists radon 6.0.1 as the latest release (R-47). Explained: the check covers this page, not every release file.
