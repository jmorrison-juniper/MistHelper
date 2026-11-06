# Implementation Plan: Cohesive troubleshooting modules

**Branch**: `jmorrison-juniper-troubleshooting-core-relocation` | **Date**: 2026-11-06 | **Spec**: [Specification](spec.md)

## Summary

Relocate three modules without operation behavior changes.
Place menu test support under foundation support and Marvis troubleshooting under Marvis.
Update every active consumer and preserve historical evidence.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing mistapi and standard library dependencies only.

**Storage**: No change.

**Testing**: pytest behavior, import, resolver, declaration, package, and catalog checks.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Existing CLI and portals.

**Performance Goals**: No executable behavior change.

**Constraints**: No compatibility paths, no owned-file overlap, and no new package violation.

**Scale/Scope**: Three source modules and their active consumers.

## Constitution Check

- Both new packages have fewer than five children. Their parents increase from two children to three.
- Execution remains at five children. Troubleshooting decreases from five to four.
- New process records use the route returned by the existing PowerShell helper.
- Existing source function-size debt remains. Narrow annotation fixes satisfy strict typing at the new destinations.
- Incremental remediation: remove the unrelated `core` grouping without increasing package debt.
- Existing process-folder debt remains unchanged except for this issue's required unique changelog fragment.
- Further process-folder remediation remains tracked by the repository migration baseline.
- No request transport, safety confirmation, secret handling, or product output changes.
- Conventional commit and PR titles use `refactor`.

The design passes the constitution before and after the research phase.

## Project Structure

### Documentation

This feature keeps `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` beside `design/`.
Supporting research, model, verification, and checklist records stay under `design/`.
There is no new external interface contract.

### Source Code

- `src/foundation/support/menu_testing/interactive_test_runner.py`
- `src/mist/intelligence/marvis/troubleshooting/marvis_troubleshoot_utils.py`
- `src/mist/intelligence/marvis/troubleshooting/troubleshoot_utils.py`

### Files to change

1. Move the three modules and replace the old package marker with two subject-specific package markers.
2. Update `MistHelper.py`, `source_dependency_resolver.py`, the parity fixture, and existing affected unit tests.
3. Update the public symbol preservation map and active performance hook catalog.
4. Generate the menu references with the existing generators. Do not edit generated pages manually.
5. Add focused relocation tests, this managed record, and one issue-specific release fragment.

PR #4358 owns `.github/test-quality-baseline.json` and the older reliability quickstart. Do not edit these files.

## Verification

Run affected behavior tests and the entire guardrail suite.
Verify canonical imports, rejected obsolete imports, resolver identity, and logger identity.
Compare moved source changes and declarations against current `origin/main`.
Run applicable compile, Ruff, Black, mypy, docstring, dead-code, and code-quality gates.
Run both reference generators and confirm a second run produces identical output.
Commit the tests, run the documented test-quality preflight and ratchet, and check current-base ownership before the PR.
Run Bandit and dependency audit because the source move includes annotation fixes.

## Complexity Tracking

No new behavioral complexity or structural exception is introduced.
