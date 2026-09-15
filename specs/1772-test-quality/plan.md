# Implementation Plan: Issue 1772 test-quality triage

**Branch**: `chore/1772-test-quality` | **Date**: 2026-09-15 | **Spec**: `specs\1772-test-quality\spec.md`

**Input**: Feature specification from `specs\1772-test-quality\spec.md`

## Summary

Re-measure issue #1772 after issue #1768 made analyzer coverage explicit. Repair the high-severity false positive in `UntestedDetector` CLI orchestration. Defer each medium-severity group to a separate issue.

## Technical Context

**Language/Version**: Python 3.13.3 in the worktree virtual environment.

**Primary Dependencies**: Standard library, pytest, and the existing `tools.test_quality_analyzer` package.

**Storage**: Markdown artifacts under `specs\1772-test-quality\`. No schema change.

**Testing**: pytest, ruff, black, mypy, `tools.test_quality_analyzer`, and `tools.guard_proof_audit`.

**Target Platform**: Windows development worktree and GitHub pull request checks.

**Project Type**: Python CLI and test tooling.

**Performance Goals**: Keep the analyzer runtime comparable with the baseline run.

**Constraints**: Do not edit frozen vendor documentation. Do not edit `CHANGELOG.md`. Keep the repair small enough to review.

**Scale/Scope**: 669 analyzed files, 28 skipped files, and 2,693 pre-repair findings.

## Constitution Check

- Five-Item Rule: The change edits existing test tooling only and adds no new top-level package.
- Class-Based Architecture: The repair stays in the existing `TestQualityCLI` class.
- Safety-First: The change adds no user input or destructive operation.
- Full Deployment Pipeline: Local gates and pull request checks validate the change.
- Observability: New analyzer branches log before and after source-path resolution.

## Project Structure

### Documentation (this feature)

```text
specs\1772-test-quality\
├── spec.md
├── plan.md
├── tasks.md
└── triage.md
```

### Source Code (repository root)

```text
tools\test_quality_analyzer\__main__.py
tests\tools\test_quality_analyzer\test_cli.py
changelog.d\issue-1772-test-quality.md
```

**Structure Decision**: Use the existing analyzer package and test suite. Put triage records under the feature spec directory.

## Complexity Tracking

No constitution violation is required.

## Repair Plan

1. Run the analyzer before code changes and record counts.
2. Classify the 124 high findings individually.
3. Repair `TestQualityCLI` so real pytest roots are not source-under-test roots for `UntestedDetector`.
4. Preserve analyzer fixture-root behavior for detector meta-tests.
5. Add a regression test that would have failed before the repair.
6. File one follow-up issue for each medium-severity rule group.
7. Run local gates and publish the pull request.

## Deferred Work

The medium-severity groups remain real test-quality debt. They are deferred to issues #2696 through #2711, one issue for each rule group.
