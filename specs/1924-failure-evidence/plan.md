# Implementation Plan: Failure Evidence Erasure Audit

**Branch**: `chore/1924-failure-evidence` | **Date**: 2026-09-16 | **Spec**: `specs/1924-failure-evidence/spec.md`

**Input**: Feature specification from `/specs/1924-failure-evidence/spec.md`

## Summary

Issue #1924 needs a measured inventory for five evidence-erasure categories. The implementation records the inventory, bounds runtime dependency declarations, and extends the guard audit to reject unbounded dependency decisions.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: `packaging`, `pytest`, `ruff`, `black`, `mypy`, and the current project dependencies.

**Storage**: Markdown and JSON artifacts under `specs/1924-failure-evidence/`.

**Testing**: `pytest`, `tools.guard_proof_audit`, `ruff`, `black`, `mypy`, `radon`, and `symbol_diff`.

**Target Platform**: Windows development worktree and GitHub Actions Linux runners.

**Project Type**: Python CLI and web service repository.

**Performance Goals**: Complete the audit in less than one minute on a local checkout.

**Constraints**: Do not edit `MistHelper.py`. Do not edit generated API documentation. Keep the repair near 15 files or fewer.

**Scale/Scope**: The audit scans repository Python files and two dependency manifests.

## Constitution Check

- Five-Item Rule: The new guard methods stay small and class-based.
- Class-Based Architecture: `GuardProofAuditor` owns the new dependency guard behavior.
- Safety-First: The dependency guard fails visibly when it measures no input.
- Full Deployment Pipeline: Local gates run before the pull request.
- Observability: The guard logs before and after meaningful actions.

## Project Structure

### Documentation

```text
specs/1924-failure-evidence/
├── inventory.json
├── inventory.md
├── plan.md
├── spec.md
└── tasks.md
```

### Source Code

```text
tools/
└── guard_proof_audit.py

tests/
└── guardrails/
    └── test_guard_proof_audit.py

requirements.txt
pyproject.toml
changelog.d/issue-1924-failure-evidence.md
```

**Structure Decision**: Extend the existing guard audit because it already enforces the no-measurement rule from issue #2654.

## Complexity Tracking

No constitution violation is required. `tools/guard_proof_audit.py` is an existing guard module, so this narrow edit does not add a new root child.

## Changed Files

- `tools/guard_proof_audit.py`: Adds runtime dependency upper-bound auditing.
- `tests/guardrails/test_guard_proof_audit.py`: Adds negative tests for unbounded and zero dependency input.
- `requirements.txt`: Adds upper bounds to direct dependency declarations.
- `pyproject.toml`: Adds upper bounds to runtime package dependencies.
- `specs/1924-failure-evidence/spec.md`: Documents the audit contract.
- `specs/1924-failure-evidence/plan.md`: Documents the implementation plan.
- `specs/1924-failure-evidence/tasks.md`: Documents completed tasks.
- `specs/1924-failure-evidence/inventory.md`: Holds the measured inventory.
- `specs/1924-failure-evidence/inventory.json`: Holds the machine-readable inventory.
- `changelog.d/issue-1924-failure-evidence.md`: Adds the release-note fragment.

## Risk and Rollback

The dependency bounds can require an explicit review for a future major release. If a valid release appears, update the upper bound and run the compatibility tests.
