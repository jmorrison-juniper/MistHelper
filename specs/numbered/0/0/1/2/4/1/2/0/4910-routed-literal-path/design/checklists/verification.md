# Verification Checklist: Restore -LiteralPath in the setup scripts

**Purpose**: Record the evidence that the implementer produces before the pull request opens.

**Created**: 2026-11-26

**Feature**: [spec.md](../spec.md)

## Red and Green Evidence

- [ ] The red run of T003 is recorded, with each failing test name and the guard message.
- [ ] The green run of T008 is recorded, with the counts of passed and failed tests.
- [ ] The guard message reports 26 examined lines in four scripts, and 0 bare lines after the fix.

## Local Gates (T-LOCAL-GATES)

- [ ] `python -m ruff check .` prints `All checks passed`.
- [ ] `python -m black --check .` reports that no file needs a change.
- [ ] `python -m pytest tests/guardrails` counts match the untouched `main` run, with no new failure.
- [ ] `symbol-diff` exits with code 0 for each changed Python test module.
- [ ] `bandit -c pyproject.toml -r .` reports no finding.
- [ ] `radon cc` and `complexity-gate --max 10` report no block above 10.
- [ ] The test quality preflight passes, and the changed-file and full-suite gates print `gate: 0 new findings vs baseline`.
- [ ] `ste-linter` scores 80 or above for each record file and for the changelog fragment.

## Scope and Style

- [ ] `git status --short` lists only the paths of the change map.
- [ ] Each changed line in a touched block has an inline comment (FR-012).
- [ ] Each touched action has an info line before it and a debug line after it (FR-012).
- [ ] No semicolon, contraction, or Latin abbreviation appears in a record file.
- [ ] The changelog fragment names issue #4910 in its bullet.

## Remote Evidence (T-PR and T-REMOTE-CI)

- [ ] The pull request body holds `Closes #4910`.
- [ ] Each required check reports success: Quality Gates, Conventional Commits PR title, STE compliance, and CodeQL.
- [ ] No open pull request overlaps the change map. Repeat the check on the day of T-PR.
