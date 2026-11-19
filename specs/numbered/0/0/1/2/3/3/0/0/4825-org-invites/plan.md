# Implementation Plan: Organization Invites Export Reports Missing SDK Call

**Branch**: `4825-org-invites` (git branch `fix/4825-org-invites`) | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/spec.md`.

## Summary

Use a guarded lookup for the SDK call in `OrgExportUtils._invites`. When the call is absent, log one error and return. Keep the supported path unchanged. Add a regression test, correct one stale documentation note, and add a changelog fragment.

## Technical Context

- **Language/Version**: Python 3.15.2 in the locked environment. `pyproject.toml` requires Python 3.13 or newer.
- **Primary Dependencies**: mistapi 0.64.1, within the locked line `>=0.64.0,<0.65`.
- **Storage**: None. The absent path writes no file.
- **Testing**: pytest for `tests/unit/export/`, plus the guard tests.
- **Target Platform**: Windows 11, macOS, and Linux.
- **Project Type**: Single project CLI tool.
- **Constraints**: The supported path keeps its arguments and output. The change adds no dependency.
- **Scale/Scope**: One function, one test class, one documentation note, and one changelog fragment.

## Constitution Check

- **Commit title**: `fix(export): skip org invites export when SDK call is missing` uses the Conventional Commits form.
- **Process folder**: This record adds one route under `specs/numbered/`. It adds no direct child of `specs/`. It leaves `.specify/feature.json` unchanged.
- **Product outputs**: The change writes no output. The absent path writes no file.
- **Mist Cloud**: The change adds no REST request. The supported path passes an SDK function to the shared export.
- **Contract tests**: `test_invites` proves the supported path. `test_invites_without_sdk_list_call_logs_error_and_skips` proves the absent path. Output, failure handling, and safety are covered. The log message holds no secret.

## Design Decisions

1. **Guarded lookup.** A direct attribute read raises `AttributeError` when the SDK lacks the call. A lookup with a default returns `None` instead.
2. **No substitute endpoint.** `listSdkInvites` returns SDK onboarding invites, which is a different resource.
3. **No empty file.** An empty `OrgInvites.csv` reads as zero invites. The absent path therefore writes no file.
4. **Return value.** The function returns `None`, as the other functions in the module do. Callers ignore the return value.

## Project Structure

### Documentation (this feature)

- `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/spec.md`
- `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/plan.md`
- `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/tasks.md`

### Source Code (repository root)

- `src/operations/exporting/export/org_export_utils.py` (changed)
- `tests/unit/export/test_org_export_utils.py` (changed)
- `documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md` (changed)
- `changelog.d/issue-4825-org-invites.md` (new)

## Verification Plan

- Run the focused test file. The expected result is 96 passed.
- Run the absent-path test before the fix. The expected result is `AttributeError`.
- Run the lint, format, compile, type, pylint, and symbol gates on the changed Python files.
- Run the test-quality gate on the changed test file.
- Run the export test folder and the guard tests.
- Run `ste-linter` with `--min-score 80` on the new markdown files.

## Risks

- A future mistapi release may add or rename the call. The guard handles both cases. The supported path runs, and the absent path logs one error.

## Complexity Tracking

Not applicable. The plan has no constitution violation.
