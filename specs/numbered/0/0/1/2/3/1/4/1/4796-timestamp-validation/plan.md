# Implementation Plan: Timestamp validation

**Branch**: `jmorrison-juniper-issue-4796-timestamp-validation` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

Reject normalized timestamp labels and retain the existing route for valid UTC labels.

## Technical Context

**Language/Version**: PowerShell 7 and Python 3.15.
**Primary Dependencies**: .NET date parsing and pytest.
**Storage**: Feature paths under `specs/`.
**Testing**: PowerShell route contracts and an isolated container smoke test.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Repository process tooling.
**Performance Goals**: No new performance requirement.
**Constraints**: Do not create a destination for an invalid label. Do not call Mist.
**Scale/Scope**: One route helper and its existing contract tests.

## Constitution Check

- The new record uses the numeric base-5 route and has at most five children at each new level.
- Existing process folders have grandfathered excess children. Their separate incremental remediation remains outside this issue.
- The helper is an existing standalone function. This narrow repair does not restructure it.
- The change adds one unique release fragment and does not change `CHANGELOG.md`.
- The change writes no product output and uses no Mist transport.
- The PR title and commit will use Conventional Commits.

The same gates pass after the design. The existing function and process folder debt remain unchanged.

## Project Structure

- `.specify/scripts/powershell/spec-route.ps1`: timestamp validation.
- `tests/guardrails/test_spec_route_contract.py`: route contracts.
- `specs/numbered/0/0/1/2/3/1/4/1/4796-timestamp-validation/`: issue records.
- `changelog.d/issue-4796-timestamp-validation.md`: release fragment.

## Complexity Tracking

The existing route module uses standalone functions. Replacing its architecture would expand the issue.
