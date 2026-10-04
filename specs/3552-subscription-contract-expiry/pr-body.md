# Spec Conformance Checklist

**Linked Spec Issue**: #3552

Closes #3552

## Summary
- Added `src/mist/intelligence/reports/subscription_expiry/` for menu 271.
- Added network-free unit tests under `tests/unit/reports/subscription_expiry/`.
- Added `changelog.d/issue-3552-subscription-contract-expiry.md`.
- Deferred menu and registry wiring to `specs/3552-subscription-contract-expiry/wiring.md`.

## Changed files
- `src/mist/intelligence/reports/subscription_expiry/__init__.py`
- `src/mist/intelligence/reports/subscription_expiry/client.py`
- `src/mist/intelligence/reports/subscription_expiry/model.py`
- `src/mist/intelligence/reports/subscription_expiry/operation.py`
- `tests/unit/reports/subscription_expiry/__init__.py`
- `tests/unit/reports/subscription_expiry/test_client.py`
- `tests/unit/reports/subscription_expiry/test_model.py`
- `tests/unit/reports/subscription_expiry/test_operation.py`
- `specs/3552-subscription-contract-expiry/**`
- `changelog.d/issue-3552-subscription-contract-expiry.md`

## Menu wiring
- Menu 271 is deferred to the integration pull request.
- The exact integration instructions are in `specs/3552-subscription-contract-expiry/wiring.md`.
- The deferred files are `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `README.md`, and generated menu references.

## Local validation
- `python -m py_compile ...`: passed for 8 new Python files.
- `python -m ruff check src\mist\intelligence\reports\subscription_expiry tests\unit\reports\subscription_expiry`: passed.
- `python -m black --check src\mist\intelligence\reports\subscription_expiry tests\unit\reports\subscription_expiry`: passed.
- `python -m mypy src\mist\intelligence\reports\subscription_expiry --config-file pyproject.toml`: passed.
- `python -m pydocstyle src\mist\intelligence\reports\subscription_expiry`: passed.
- `python -m vulture src\mist\intelligence\reports\subscription_expiry --min-confidence 70`: passed.
- `python -m interrogate -v src\mist\intelligence\reports\subscription_expiry`: passed at 100 percent.
- `python -m radon cc src\mist\intelligence\reports\subscription_expiry -j | complexity-gate --max 10`: passed.
- `test-quality-analyzer --gate --changed-from origin/main`: passed with 3 files checked and 0 new findings.
- `python -m pytest tests\unit\reports\subscription_expiry -q --timeout=120`: 11 passed.

## Acceptance Criteria
- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality
- [x] Tests added or updated for all changed functionality
- [x] Coverage meets or exceeds 80% threshold
- [x] New or changed guards state the measured count and prove one failing path
- [x] No new Ruff lint violations for changed files
- [x] Code formatted with Black for changed files
- [x] mypy passes for the new package

## Security
- [x] No hardcoded secrets, tokens, or passwords
- [ ] Bandit passes with no new findings
- [ ] pip-audit clean
- [x] Sensitive data handled via `.env` or environment variables only

## Deployment
- [ ] Dry-run verified locally against a live Mist organization
- [x] `.env` changes documented in `deploy/.env.example` if applicable
- [x] Container build not applicable

## UI / E2E Testing
- [x] Playwright E2E tests not applicable
- [x] Stable `data-testid` attributes not applicable
- [x] Browser Agent Tool verification not applicable
- [x] Screenshots and traces not applicable

## Documentation
- [ ] README.md updated
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the issue number
- [x] `CHANGELOG.md` is unchanged by this branch
