# Spec Conformance Checklist

**Linked Spec Issue**: #3563

Closes #3563

## Summary

This pull request adds the feature-owned package for menu `283`, which triggers one Mist synthetic test on demand. It supports site scope, one-device scope, and switch RADIUS scope. The integration pull request must apply menu wiring from `specs/3563-synthetic-test-trigger/wiring.md`.

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met in the feature package.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold for the changed package.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations for the package and tests.
- [x] Code formatted with Black for the package and tests.
- [x] mypy passes for the package.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passes with no new findings for the feature package.
- [ ] pip-audit clean. Not run because no dependency changed.
- [x] Sensitive data stays out of logs and export rows.

## Deployment

- [ ] Dry-run verified locally. Not run because menu wiring is deferred to the integration pull request.
- [x] `.env` changes documented in `deploy/.env.example` are not applicable.
- [x] Container build is not applicable because no container file changed.

## UI / E2E Testing

- [x] Playwright E2E tests are not applicable because no web UI changed.
- [x] Stable `data-testid` attributes are not applicable.
- [x] Browser Agent verification is not applicable.
- [x] Screenshots and traces are not applicable.

## Documentation

- [ ] README.md updated. Deferred to the integration pull request by contract.
- [x] Release note added as `changelog.d/issue-3563-synthetic-test-trigger.md`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Files

- `src/mist/intelligence/troubleshooting/synthetic_test_trigger/__init__.py`
- `src/mist/intelligence/troubleshooting/synthetic_test_trigger/client.py`
- `src/mist/intelligence/troubleshooting/synthetic_test_trigger/models.py`
- `src/mist/intelligence/troubleshooting/synthetic_test_trigger/operation.py`
- `tests/unit/troubleshooting/synthetic_test_trigger/__init__.py`
- `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py`
- `specs/3563-synthetic-test-trigger/*`
- `changelog.d/issue-3563-synthetic-test-trigger.md`

## Local gate results

- `py_compile`: passed for four new package files.
- `ruff check`: passed for the package and tests.
- `black --check`: passed for the package and tests.
- `mypy`: passed for the package.
- `pydocstyle`: passed for the package.
- `pytest`: `7 passed`.
- `vulture`: no findings at `--min-confidence 70`.
- `interrogate`: `100.0%` package docstring coverage.
- `radon` plus `complexity-gate`: all functions within threshold 10.
- `test-quality-analyzer`: scanned one changed test file with 0 new findings.
- `mistapi` SDK compatibility: `8 passed` with 366 unverifiable call signatures.
- `output scan`: `27 passed`.
- `bandit`: no findings for the feature package.

## Deferred integration wiring

Menu registration, `MistHelper.py` import, `OperationRegistry`, primary key strategy, README, and menu reference updates are deferred. The integration pull request must copy `specs/3563-synthetic-test-trigger/wiring.md`.
