# Implementation Plan: Reboot Site Lock Safety

**Branch**: `fix/2644-reboot-site-lock` | **Date**: 2026-09-16 | **Spec**: `specs\2644-reboot-site-lock\spec.md`

**Input**: Feature specification from `specs\2644-reboot-site-lock\spec.md`

## Summary

Issue #2644 shows that a scheduled reboot can wait for one year while the site lock can renew for twelve hours. The repair caps accepted schedules below the lock life, stops cloud polling until the reboot window starts, and fails closed when the lock is lost.

## Mechanism Decision

I chose a combined repair.

1. Cap the accepted schedule below the site lock life. This proves that a new schedule cannot ask one run to wait longer than its lock can protect. The cap keeps one heartbeat interval and one phase deadline inside the twelve hour lock life.
2. Stop polling before the scheduled reboot window. This removes cloud calls that cannot show a device return before the device can reboot.
3. Fail closed on lock loss before each later site action. This proves that a run never acts on a site after its heartbeat reports loss.

I rejected an unbounded renewing lock, because a renewing lock can starve a site when the driver misbehaves. I rejected release-and-reacquire, because the run can reach its reboot window and then fail to take the site back. That creates a scheduled firmware event with no owner. I rejected polling reduction alone, because it lowers call volume but does not solve lock expiry.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Standard library, Flask, mistapi 0.64.0, pytest

**Storage**: Existing Redis site lock and existing run record store

**Testing**: pytest, ruff, black, mypy, radon

**Target Platform**: Windows development and containerized portal runtime

**Project Type**: Python web portal and firmware workflow

**Performance Goals**: A scheduled wait makes zero Mist cloud calls before its reboot window.

**Constraints**: No permanent locks. No live Mist API call in tests. No edits under `documentation\api\`.

**Scale/Scope**: One upgrade run, and the multi-site workflow after pull request #2720 merges.

## Constitution Check

- The change touches existing modules because the upgrade package already exceeds the Five-Item Rule.
- No new direct child is added under the noncompliant `src\upgrade_portal\upgrade` package.
- New behavior stays in named classes and existing classes.
- Each new executable line has an inline comment.
- Each meaningful action has logging before and after.
- No secret, lock token, or work email address reaches a log message.

## Project Structure

### Documentation

```text
specs\2644-reboot-site-lock\
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src\upgrade_portal\runtime\lock.py
src\upgrade_portal\upgrade\options.py
src\upgrade_portal\upgrade\phase_gate.py
src\upgrade_portal\upgrade\driver.py
tests\unit\upgrade_portal\test_phase_gate.py
tests\unit\upgrade_portal\test_upgrade_driver.py
tests\unit\upgrade_portal\test_upgrade_ssr_options.py
changelog.d\issue-2644-reboot-site-lock.md
```

**Structure Decision**: The change stays in the existing upgrade portal modules that own locks, options, phase polling, and the run driver.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing package has more than five modules | The defect sits in the existing upgrade portal path | A new module would add another child to the noncompliant package |
