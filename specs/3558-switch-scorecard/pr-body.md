# Spec Conformance Checklist

**Linked Spec Issue**: #3558

Closes #3558

## Summary

This draft pull request adds the organization switch scorecard package for menu `277`. The integration pull request applies the root menu wiring from `specs/3558-switch-scorecard/wiring.md`.

## Files

- `src/reports/switch_scorecard/`
- `tests/unit/reports/switch_scorecard/`
- `specs/3558-switch-scorecard/`
- `changelog.d/issue-3558-switch-scorecard.md`

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met or deferred in `wiring.md`.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold for the new package tests.
- [ ] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations for the changed package and tests.
- [x] Code formatted with Black for the changed package and tests.
- [x] mypy passes for the changed package.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [ ] Bandit passes with no new findings.
- [ ] pip-audit clean.
- [x] Sensitive data handled via environment variables only.

## Deployment

- [ ] Dry-run verified locally against live Mist data.
- [x] `.env` changes are not required.
- [x] Containerfile did not change.

## UI / E2E Testing

- [x] No web UI changed.

## Documentation

- [ ] README.md updated. Deferred to the integration pull request.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Local Gate Results

- `py_compile`: passed for `src/reports/switch_scorecard`.
- `ruff`: passed for `src/reports/switch_scorecard` and `tests/unit/reports/switch_scorecard`.
- `black --check`: passed for `src/reports/switch_scorecard` and `tests/unit/reports/switch_scorecard`.
- `mypy`: passed for `src/reports/switch_scorecard`.
- `pydocstyle`: passed for `src/reports/switch_scorecard`.
- `pytest`: `6 passed`.
- `vulture`: passed for `src/reports/switch_scorecard`.
- `interrogate`: passed at `100%` for `src/reports/switch_scorecard`.

## Deferred Wiring

The menu registration, operation registry entry, primary key strategies, generated menu references, and README update are deferred to the tier integration pull request. The required manifest is `specs/3558-switch-scorecard/wiring.md`.
