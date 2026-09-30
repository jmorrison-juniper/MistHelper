# Spec Conformance Checklist

**Linked Spec Issue**: #3555

Closes #3555

## Summary
- Added `src/reports/psk_hygiene/` with the PSK hygiene client, model, and operation.
- Added unit tests under `tests/unit/reports/psk_hygiene/`.
- Added `changelog.d/issue-3555-psk-hygiene-report.md`.
- Deferred menu wiring to `specs/3555-psk-hygiene-report/wiring.md`.

## Deferred integration work
- `MistHelper.py` menu 274 registration is deferred.
- `src/utils/operation_registry.py` is deferred.
- `src/refactors/endpoint_primary_key_strategies.py` is deferred.
- `README.md` and generated menu references are deferred.
- The integration pull request must run `python MistHelper.py --test --menu 274`.

## Acceptance Criteria
- [x] All current-branch acceptance criteria from the linked Spec Issue are met.
- [x] Each current-branch criterion has a corresponding test or verification.

## Quality
- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations for the feature scope.
- [x] Code formatted with Black for the feature scope.
- [x] mypy passes for `src/reports/psk_hygiene`.

## Security
- [x] No hardcoded secrets, tokens, or passwords.
- [ ] Bandit passes with no new findings. Not run for this feature-only draft.
- [ ] pip-audit clean. Not run because dependency manifests did not change.
- [x] Sensitive data handled via `.env` / environment variables only.

## Deployment
- [ ] Dry-run verified locally. Menu wiring is deferred to integration.
- [x] `.env` changes documented in `deploy/.env.example` (not applicable).
- [x] Container builds successfully (not applicable).

## UI / E2E Testing
- [x] Not applicable. No web UI changed.

## Documentation
- [ ] README.md updated. Deferred to integration.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Local validation
- `python -m py_compile` passed for all new PSK hygiene source and test files.
- `python -m ruff check src\reports\psk_hygiene tests\unit\reports\psk_hygiene` passed.
- `python -m black --check src\reports\psk_hygiene tests\unit\reports\psk_hygiene` passed.
- `python -m mypy src\reports\psk_hygiene --config-file pyproject.toml` passed.
- `python -m pydocstyle src\reports\psk_hygiene` passed.
- `python -m pytest tests\unit\reports\psk_hygiene -q --timeout=120` passed with 26 tests.
- `python -m vulture src\reports\psk_hygiene --min-confidence 70` passed.
- `python -m interrogate -v src\reports\psk_hygiene` passed at 100 percent.

## Known draft blocker
- Final SpecKit analysis still reports a class-based model helper concern. The current implementation exposes `PskHygieneScorer`, but private module helpers remain.
