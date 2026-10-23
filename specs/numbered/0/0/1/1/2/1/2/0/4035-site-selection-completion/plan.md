# Implementation Plan: Site selection completion

**Branch**: `jmorrison-juniper-fix-4035-site-selection-completion`

**Date**: 2026-10-23

**Spec**: [Site selection completion](spec.md)

## Summary

Interpret the existing menu-92 identifier result at the portal boundary. Use the existing explicit outcome path for successful selection.
Do not change the shared selector or infer success from its log text.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Existing `OperationOutcome`, `OperationExecutor`, Flask, and pytest.

**Storage**: Existing in-memory run records. No schema change.

**Testing**: pytest unit tests, an actual-selector integration case, and a browser terminal-message regression.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: CLI with a web portal.

**Performance Goals**: Add one bounded result check per completed handler.

**Constraints**: No production credentials, cloud operations, selector return-type changes, or new dependencies.

**Scale/Scope**: Menu 92 only. Preserve other menus.

## Constitution Check

The design passes the safety and transport requirements. This repair introduces no API transport.
The managed numeric route has eight base-5 segments. The feature root has four planned children.
Supporting records use `design/`, which has five children.
Only this issue owns the new changelog fragment.
No output path changes. Tests use temporary directories.
Existing `OperationExecutor` exceeds the class-member limit. The repair adds no member and keeps the changed method below 25 lines.
Existing test modules and process folders exceed structural limits. This change edits established tests instead of adding another direct test module.
Separate incremental remediation: divide the executor and group the established process records in a future structural change.
This repair does not expand that unrelated work.
The post-design review reached the same result.

## Project Structure

### Documentation

The managed feature root contains `spec.md`, `plan.md`, `tasks.md`, and `design/`.
The design records contain research, the data model, the validation guide, contracts, and the requirements checklist.

### Source Code

- `web_portal/services/operation.py`: Interpret menu 92's nonblank identifier before the existing typed outcome mapping.
- `tests/unit/web_portal/test_portal_silent_completion.py`: Cover selection, invalid results, other menus, empty exports, and failures.
- `tests/e2e/web_portal/test_operation_terminal_reconciliation.py`: Cover the visible completed selection with no results panel.
- `changelog.d/issue-4035-site-selection-completion.md`: Record the operator-visible repair.

## Complexity Tracking

Use the existing handler-outcome method. Do not add a wrapper or change the shared helper.
Existing structural debt remains unchanged.
