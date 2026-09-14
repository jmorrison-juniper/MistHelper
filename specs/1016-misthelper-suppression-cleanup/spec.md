# Feature Specification: MistHelper.py Suppression Cleanup

**Feature Branch**: `chore/1004-suppression-cleanup`

**Created**: 2026-07-13

**Updated**: 2026-09-13

**Status**: Implemented

**Issue**: #1004

## Current Truth

Issue #1004 now covers the final suppression cleanup in `MistHelper.py`. The stale eight-pull-request plan is complete enough to replace with one focused pull request. The file held six confirmed suppressions before this work.

## Suppression Inventory

The search command was `rg "#\s*(type: ignore|noqa|nosec|pylint: disable)" MistHelper.py`. It found these real suppressions before implementation.

1. Line 47: `# nosec B404` on the direct `subprocess` import.
2. Line 929: `# nosec B310` on the PyPI `urlopen` call.
3. Line 1110: `# type: ignore[import-untyped]` on the optional `paramiko` import.
4. Line 1111: `# type: ignore[import-untyped]` on the optional `RejectPolicy` import.
5. Line 2236: `# type: ignore[attr-defined]` on the dynamic `mistapi` module attribute write.
6. Line 5079: `# nosec B104` on the container bind-all address.

`rtk python -m ruff check MistHelper.py --select ALL --statistics` reported the full lint surface. The relevant security and typing signals were one `S104`, one `S310`, and the type ignores named above. The command also reported many advisory rules that the normal project gate does not enable.

## User Scenario

A maintainer can run the project gates with no suppression comments in `MistHelper.py`. The dependency bootstrap, optional SSH imports, dynamic Mist SDK binding, and web portal bind selection keep the same behavior.

## Requirements

- **FR-001**: Remove all `# nosec`, `# type: ignore`, `# noqa`, and `# pylint: disable` comments from `MistHelper.py`.
- **FR-002**: Fix the root cause for each removed suppression.
- **FR-003**: Keep the public module-level symbol set unchanged.
- **FR-004**: Add one release note fragment for issue #1004.
- **FR-005**: Record final evidence in `analysis.md`.

## Acceptance Criteria

- **AC-001**: The suppression search returns zero matches in `MistHelper.py`.
- **AC-002**: `ruff check MistHelper.py` passes.
- **AC-003**: `mypy MistHelper.py --config-file pyproject.toml` passes.
- **AC-004**: `tools.symbol_diff --base main MistHelper.py` reports no module-level name change.
- **AC-005**: The full local gate set passes before the commit.
