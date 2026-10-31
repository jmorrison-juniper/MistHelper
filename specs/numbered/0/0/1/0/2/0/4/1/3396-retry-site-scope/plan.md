# Implementation Plan: Retry site scope

**Branch**: `jmorrison-juniper-retry-site-scope` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

Filter the saved site rows only for retry saves, after the aggregate target validation.
Read that durable retry scope for confirmation and submission.
Preserve the operator selection and the exact comparison of effective site order.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: Flask and the existing aggregate firmware service.
**Storage**: Existing durable run store and token-based site locks. No schema change.
**Testing**: Pytest contract routes with fake storage, captures, inventory, and cloud services.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Existing web portal.
**Performance Goals**: No additional external request. Site filtering uses sets and ordered lists.
**Constraints**: No live firmware action, credential, or external connection in tests.
**Scale/Scope**: One route module, one existing contract test module, one release note, and this specification directory.

## Constitution Check

- The app supplies an isolated branch from commit `0b04cda81c8ef75096f3bedae0885038c775d665`.
- The branch hook uses the app-managed branch. The app rename replaces raw branch creation.
- `Resolve-SpecFeaturePath` and `Assert-SpecFeatureDestination` validated the numeric route before writing.
- Keep the feature selector command-scoped. Do not change `.specify/feature.json`.
- No transport changes occur. Existing Mist SDK routes remain intact.
- Existing route functions and modules exceed structural limits. Edit only necessary blocks and add bounded scope behavior.
- Separate incremental remediation: divide the existing large route module in a later owner-approved issue, outside this file set.
- The changelog directory has existing process-folder debt. Add only the required unique fragment.
- Separate incremental remediation: retain the existing managed-record migration process, without changing its baseline.
- Authentication, confirmation, audit, token locks, claims, and transactions retain their existing code paths.
- Human review replaces the general deployment procedure for this task. Leave the draft pull request unmerged.

The design review found no new structural exception beyond the required unique process records.

## Project Structure

The permitted executable files are:

- `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`
- `tests/contract/upgrade_portal/test_org_child_controls_routes.py`

The release note is `changelog.d/issue-3396-retry-site-scope.md`.
The feature root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The `design/` directory holds research, the data model, the validation guide, contracts, and checklists.

## Design

1. Retain the full selected-site validation during save.
2. Filter approved rows by validated aggregate target site IDs only when a retry exists.
3. Use an owned durable retry record to intersect the active selection with its saved site IDs.
4. Preserve selected order so the existing exact-context comparison refuses missing or reordered planned sites.
5. Apply this effective scope before confirmation reads and before submission lock checks.

Do not rebuild a retry from changing cloud inventory during confirmation or submission.
The durable operation defines the confirmed scope.

## Validation

Extend the existing contract file with blocked network access and scope assertions.
Cover cleared families, departed devices, plain saves, complete retries, and changed effective context.
Run focused contract and unit tests, local static gates, and the test-quality preflight.
After committing, run the committed-difference test-quality gate against verified `origin/main`.
Record exact results in the draft pull request.

## Extension Hooks

The YAML parses successfully.
`before_specify` requires `speckit.git.feature`, satisfied by the app-managed branch hook.
Every enabled commit hook for specify, plan, tasks, implement, and analyze is optional.
Optional command: `/speckit-git-commit`. Prompt: commit the current phase changes.
Defer these optional commits to the requested tested implementation commit.
Companion hooks are disabled and do not run.
