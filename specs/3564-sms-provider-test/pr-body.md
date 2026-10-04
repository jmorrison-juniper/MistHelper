# Spec Conformance Checklist

**Linked Spec Issue**: #3564

Closes #3564

## Summary

This pull request adds the package for menu `284`, `Test the guest portal SMS provider`. It supports `Twilio`, `SMSGlobal`, and `Telstra`. It prompts for credentials with hidden input, asks for `y` confirmation before sending, and writes `SmsProviderTest.csv` without credentials.

## Files

- `src/mist/intelligence/troubleshooting/sms_provider_test/`
- `tests/unit/troubleshooting/sms_provider_test/`
- `specs/3564-sms-provider-test/`
- `changelog.d/issue-3564-sms-provider-test.md`

## Deferred wiring

Menu registration is deferred to the tier integration pull request. The exact instructions are in `specs/3564-sms-provider-test/wiring.md`. This branch does not edit `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `README.md`, generated menu references, or `web_portal/`.

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met in the owned package and tests.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold. `interrogate` reports 100% docstring coverage for the package.
- [x] New or changed guards state the measured count and prove one failing path. The confirmation guard test proves zero API calls after refusal.
- [x] No new Ruff lint violations. Targeted `ruff check` passed.
- [x] Code formatted with Black. Targeted `black --check` passed.
- [x] mypy passes. Targeted `mypy src\mist\intelligence\troubleshooting\sms_provider_test --config-file pyproject.toml` passed.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passes with no new findings. Targeted `bandit` passed for the package.
- [ ] pip-audit clean. Not run because no dependency changed.
- [x] Sensitive data handled through hidden prompts and never persisted.

## Deployment

- [ ] Dry-run verified locally. Not run against Mist because it would send an external SMS provider test.
- [x] `.env` changes documented in `deploy/.env.example` if applicable. No `.env` change applies.
- [x] Container builds successfully if Containerfile changed. No container file changed.

## UI / E2E Testing (if web UI changed)

- [x] Playwright E2E tests added or updated for changed UI flows in `tests/e2e/`. Not applicable, no web UI changed.
- [x] Stable `data-testid` attributes added for new interactive elements. Not applicable, no web UI changed.
- [x] AI agent verified selectors via VS Code Browser Agent Tools. Not applicable, no web UI changed.
- [x] Screenshots/traces captured for main UI flows. Not applicable, no web UI changed.

## Documentation

- [x] README.md updated if user-facing changes. Deferred through `wiring.md` by the fleet contract.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Validation

- `py_compile` passed for 5 package files.
- `ruff check src\mist\intelligence\troubleshooting\sms_provider_test tests\unit\troubleshooting\sms_provider_test` passed.
- `black --check src\mist\intelligence\troubleshooting\sms_provider_test tests\unit\troubleshooting\sms_provider_test` passed.
- `mypy src\mist\intelligence\troubleshooting\sms_provider_test --config-file pyproject.toml` passed.
- `pydocstyle src\mist\intelligence\troubleshooting\sms_provider_test` passed.
- `pytest tests\unit\troubleshooting\sms_provider_test -q --timeout=120` passed with 9 tests.
- `vulture src\mist\intelligence\troubleshooting\sms_provider_test --min-confidence 70` passed.
- `interrogate -v src\mist\intelligence\troubleshooting\sms_provider_test` passed with 100.0% coverage.
- `bandit -c pyproject.toml -r src\mist\intelligence\troubleshooting\sms_provider_test -q` passed.
- `radon cc src\mist\intelligence\troubleshooting\sms_provider_test -j | complexity-gate --max 10` passed.
- `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main` passed.
- `pytest tests\integration\test_mistapi_sdk_compatibility.py -q --timeout=120` passed.
- `pytest tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120` passed.
