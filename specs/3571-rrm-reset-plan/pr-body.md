# Spec Conformance Checklist

**Linked Spec Issue**: #3571

Closes #3571

## Summary

This pull request adds menu `291` implementation files for RRM optimize or reset plan capture. The operation is destructive and needs human review before merge.

## Files

- `src/mist/resources/site/rrm_reset/`
- `tests/unit/site/rrm_reset/`
- `specs/3571-rrm-reset-plan/`
- `changelog.d/issue-3571-rrm-reset-plan.md`

## Deferred wiring

Menu registration is deferred to the integration pull request. Use `specs/3571-rrm-reset-plan/wiring.md` for the exact `MistHelper.py`, `OperationRegistry`, category table, primary key strategy, and environment documentation changes.

## SpecKit analysis

Manual SpecKit analysis found no blocking inconsistency across `spec.md`, `plan.md`, and `tasks.md`. The tasks cover the destructive confirmation, dry-run behavior, before-write ordering, settle time, diff behavior, wiring manifest, and release note.

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality

- [x] Tests added or updated for all changed functionality
- [ ] Coverage meets or exceeds 80% threshold
- [ ] New or changed guards state the measured count and prove one failing path
- [ ] No new Ruff lint violations (`ruff check .`)
- [ ] Code formatted with Black (`black --check --diff .`)
- [x] mypy passes for `src/mist/resources/site/rrm_reset` (`mypy src/mist/resources/site/rrm_reset --config-file pyproject.toml`)

## Security

- [x] No hardcoded secrets, tokens, or passwords
- [ ] Bandit passes with no new findings (`bandit -c pyproject.toml -r .`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [x] Sensitive data handled via `.env` / environment variables only

## Deployment

- [x] Dry-run verified locally through unit tests
- [ ] `.env` changes documented in `deploy/.env.example` (if applicable)
- [ ] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)

- [ ] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [ ] Stable `data-testid` attributes added for new interactive elements
- [ ] AI agent verified selectors via VS Code Browser Agent Tools
- [ ] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation

- [ ] README.md updated (if user-facing changes)
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the PR number, the issue number, or the date
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)

## Validation

- `py_compile`: passed for `src/mist/resources/site/rrm_reset`.
- `ruff check`: passed for `src/mist/resources/site/rrm_reset` and `tests/unit/site/rrm_reset`.
- `black --check`: passed for `src/mist/resources/site/rrm_reset` and `tests/unit/site/rrm_reset`.
- `mypy`: passed for `src/mist/resources/site/rrm_reset`.
- `pydocstyle`: passed for `src/mist/resources/site/rrm_reset`.
- `pytest`: `11 passed` for `tests/unit/site/rrm_reset`.
- `complexity-gate`: passed for `src/mist/resources/site/rrm_reset` with max complexity `10`.
- `test-quality-analyzer`: passed for changes since `origin/main`.
- `vulture`: passed for `src/mist/resources/site/rrm_reset`.
- `interrogate`: `100.0%` for `src/mist/resources/site/rrm_reset`.
