# Implementation Plan: Typed operation outcomes

**Branch**: `jmorrison-juniper-typed-operation-outcomes`
**Date**: 2026-10-19
**Spec**: [spec.md](spec.md)
**Initial base**: `origin/main` at `cdc965f5f59a99c1ae25fcca55871b6c14f4a19b`

## Summary

Add an immutable `OperationOutcome` model and migrate eligible producers in
serial batches. Keep the portal classifier unchanged until producer migration
finishes. Keep #3168 open.

The preserved specification in
[PR #4019](https://github.com/jmorrison-juniper/MistHelper/pull/4019)
defines the serial migration. This batch replaces its stale inventory and
implements the contract prerequisite only.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: Standard-library dataclasses and typing.
**Storage**: None.
**Testing**: pytest, Ruff, Black, mypy, Bandit, and focused coverage.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Shared internal model for future handler returns.
**Performance Goals**: No network, filesystem, or database action during construction.
**Constraints**: No portal wiring, handler migration, fallback, or Mist write.
**Scale/Scope**: One production module and one focused test module.

## Constitution Check

- Use one class with three fields and two validation methods at most.
- Add the model under `src/foundation/models/`, which has three tracked
  children before this change. Do not add to its overfull `dataclasses/` child.
- Keep the feature root at five children or fewer. Keep supporting records
  under `design/`.
- Existing process-folder debt remains in `changelog.d/`. Add only the unique
  required fragment. The release coordinator removes it during aggregation.
- Existing source and test folder debt remains unchanged. A later folder
  remediation must move existing model tests into bounded packages.
- Add no output outside the ignored test evidence locations.
- Use a Conventional Commit subject and PR title.
- Run all tests without a Mist session. This model uses no Mist transport.

The pre-design and post-design checks pass. No existing executable block changes.

## Project Structure

```text
src/foundation/models/operation_outcome.py
tests/unit/dataclasses/test_operation_outcome.py
changelog.d/issue-3168-typed-operation-outcomes.md
specs/numbered/0/0/1/0/0/1/3/3/3168-typed-operation-outcomes/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/handler.md
    checklists/requirements.md
```

## Delivery Order

1. Deliver this model, its tests, and the contract documentation.
2. Migrate existing value-return handlers first, preserving each caller's
   return meaning. Menus 274, 280, and 276 now return `OperationOutcome`.
3. Refresh the current named-handler inventory. No un-migrated value-return
   operation handler remains. Keep menu 92 as a site-selection input helper.
4. Migrate the remaining named handlers in serial operation-family batches.
5. Use a separate issue and exclusive `MistHelper.py` batch for lambda conversion.
6. Replace portal classification only after all supported producers return
   the type. Delete all marker tuples, prose readers, and dependent tests.

Menus 274, 280, and 276 now return `OperationOutcome`. The research record
contains their state mappings and caller contracts. The current inventory
found no un-migrated value-return operation handler.

Menu 92 remains a site-selection input helper. Do not change its string result.
The next producer batch must select a named operation family whose handlers
currently return `None`. Keep `MistHelper.py` lambda registrations, portal
classification, and final marker removal unchanged until their separate
batches. No producer batch adds a compatibility fallback.

## Validation

Use the exact commands in [quickstart.md](design/quickstart.md).
Run the committed-test quality procedure before push.
Record command results in the PR body.

## Workflow Constraints

PowerShell is absent on this host. The managed route was checked with the
same eight-digit base-5 algorithm and parent-capacity rules in `spec-route.ps1`.
The check examined ten parents and found no violation.

The app already created and renamed this isolated branch. Do not run the
branch-creation hook or modify `.specify/feature.json`.
Use the command-scoped feature path for later workflow steps.

The optional commit hooks do not run between artifact edits.
The companion hooks are disabled in `.specify/extensions.yml`.

## Complexity Tracking

No new structural exception is required for production code.
The existing portal executor remains large but untouched.
