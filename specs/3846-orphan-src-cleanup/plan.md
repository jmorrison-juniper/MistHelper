# Implementation Plan: Remove safe orphan source directories

**Spec**: [spec.md](spec.md)

**Source Issue**: #3846

## Approach

1. Keep the existing Git lookup that identifies tracked direct children under `src`.
2. Count each untracked direct directory before its content safety check.
3. Remove only candidates with no file outside a `__pycache__` directory.
4. Log each removed name and both measured counts.
5. Extend the focused unit test with canonical preservation, unsafe-content refusal, and count assertions.

## Files

- `scripts/bootstrap_worktree.py`
- `tests/unit/scripts/test_stale_source_sweep.py`
- `specs/3846-orphan-src-cleanup/spec.md`
- `specs/3846-orphan-src-cleanup/plan.md`
- `specs/3846-orphan-src-cleanup/tasks.md`
- `changelog.d/issue-3846-orphan-src-cleanup.md`

## Safety

The sweep stops when Git cannot provide tracked names.
The sweep keeps every candidate that contains a file outside `__pycache__`.
The sweep never removes a tracked directory.

## Validation

Run the focused test, Ruff, Black, mypy, Bandit, complexity, symbol preservation, STE, changelog policy, and test-quality checks.
