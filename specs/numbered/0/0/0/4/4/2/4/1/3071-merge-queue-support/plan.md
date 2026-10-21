# Implementation Plan: Protected merge queue validation

**Branch**: `jmorrison-juniper-merge-queue-support` | **Date**: 2026-10-20 | **Spec**: [Specification](spec.md)

**Input**: The managed numeric #3071 specification in this directory.

## Summary

Add queue check requests to the two required-check workflows.
Keep all 15 required context names, strict protection, and merge-candidate checkout behavior.
Add negative contract proofs and document owner-controlled activation.

## Technical Context

**Language/Version**: GitHub Actions YAML and Python 3.13.

**Primary Dependencies**: Existing pytest and PyYAML. Existing pinned CodeQL reusable workflow.

**Storage**: No product data or schema changes.

**Testing**: Existing workflow guard, synthetic contract mutations, Ruff, Black, mypy, and the test-quality ratchet.

**Target Platform**: GitHub Actions and local Windows, macOS, or Linux development.

**Project Type**: Repository workflow configuration.

**Performance Goals**: Avoid cancellation between merge candidates without adding duplicate event runs.

**Constraints**: No settings changes. Preserve strict checks, required names, post-merge dispatch, and reserved workflow steps.

**Scale/Scope**: Two required-check workflows and 15 required contexts.

## Constitution Check

The design changes no Mist cloud behavior and uses no production credentials.
The app-managed branch remains unchanged by Spec Kit.
The feature selector remains command-scoped.
New feature records use the eight-level numeric route and five children or fewer.
The release fragment is the only new direct child of an established process folder.

The existing guard module exceeds five top-level names.
Add no new top-level name. Extend existing test classes and their module-scoped fixtures.
Use parameterized tests to keep new classes and methods within existing limits.
Track future separation of the existing trigger guard as independent structure remediation, not part of this workflow change.
The established changelog directory also exceeds five children.
Use its required unique-fragment exception and leave general directory remediation outside this change.

No product output changes location. Test evidence uses ignored paths or temporary test directories.
Use a Conventional Commit title and the required coauthor trailer.
The preparation pull request uses `Refs #3071` because operational acceptance remains incomplete.

Post-design result: the bounded configuration change needs no new runtime abstraction or dependency.

## Project Structure

### Documentation (this feature)

The feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains research, data model, quickstart, contracts, and checklists.

### Source Code (repository root)

- `.github/workflows/ci.yml`: add the queue trigger only.
- `.github/workflows/codeql.yml`: add the queue trigger and protect main and queue runs from cancellation.
- `tests/guardrails/test_ci_gate_triggers.py`: extend existing classes with workflow and mutation contracts.
- `documentation/quality-gates.md`: describe preparation, activation, evidence, and recovery.
- `changelog.d/issue-3071-merge-queue-support.md`: add the unique release note.

**Structure Decision**: Reuse the existing workflow parser and tests.
Make no new package or workflow.

## Research and Design

See [research](design/research.md), [data model](design/data-model.md), and [workflow contracts](design/contracts/workflows.md).
See [quickstart](design/quickstart.md) for runnable local checks.

The pinned reusable CodeQL workflow checks out the caller commit and analyzes Python without a pull-request-only condition.
The issue synchronization workflow excludes merge-group events before it changes issues.
The existing test-quality job scans all tests on non-pull-request events.
Default Actions checkout measures the queue commit. The explicit quality checkout falls back to `github.sha`.

## Validation and Delivery

Use the documented local workflow gates and record exact commands and results in the pull request.
The workflow change makes the committed test-quality ratchet scan every test root.
Do not change its baseline.
Run the focused workflow guard before and after the change.
Preserve the #4306 historical-fetch repair and every unrelated `ci.yml` byte.
The #4208 handover permits only the trigger edit.
Do not import or remove its browser evidence step.

After successful checks, obtain coordinator review before enabling auto-merge or merging.
The owner separately enables the queue and verifies two candidates.
The issue remains open until the owner records successful queue and merged-tree evidence.

## Complexity Tracking

| Existing debt | Narrow exception | Separate remediation |
| - | - | - |
| Guard module has more than five top-level names | Extend existing classes without a new top-level name | Divide the guard during a dedicated structure change |
| Changelog directory has more than five children | Add only the required unique fragment | Review grouped release-fragment intake separately |
