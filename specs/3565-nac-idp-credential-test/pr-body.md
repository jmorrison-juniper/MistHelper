# Spec Conformance Checklist

**Linked Spec Issue**: #3565

Closes #3565

## Summary

- Added the owned package for menu 285 at `src/troubleshooting/nac_idp_credential_test`.
- Added model, client, prompt, and operation tests under `tests/unit/troubleshooting/nac_idp_credential_test`.
- Deferred integration wiring to `specs/3565-nac-idp-credential-test/wiring.md`.

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality

- [x] Tests added or updated for all changed functionality
- [x] Coverage meets or exceeds 80% threshold
- [x] New or changed guards state the measured count and prove one failing path
- [x] No new Ruff lint violations (`ruff check` on owned package and tests)
- [x] Code formatted with Black (`black --check` on owned package and tests)
- [x] mypy passes (`mypy src\troubleshooting\nac_idp_credential_test --config-file pyproject.toml`)

## Security

- [x] No hardcoded secrets, tokens, or passwords
- [x] Bandit passes with no new findings (`bandit -c pyproject.toml -r src\troubleshooting\nac_idp_credential_test -q`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [x] Sensitive data handled through hidden input only

## Deployment

- [x] Dry-run verified locally with unit tests and mocked prompts
- [x] `.env` changes documented in `deploy/.env.example` (not applicable)
- [x] Container builds successfully (not applicable)

## UI / E2E Testing (if web UI changed)

- [x] Playwright E2E tests added or updated for changed UI flows (not applicable)
- [x] Stable `data-testid` attributes added for new interactive elements (not applicable)
- [x] AI agent verified selectors through VS Code Browser Agent Tools (not applicable)
- [x] Screenshots or traces captured for main UI flows (not applicable)

## Documentation

- [x] README.md updated (deferred to the integration pull request)
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the issue number
- [x] `CHANGELOG.md` is unchanged by this branch

## Validation

- `py_compile`: passed for all owned Python files.
- `ruff check`: passed for `src\troubleshooting\nac_idp_credential_test` and `tests\unit\troubleshooting\nac_idp_credential_test`.
- `black --check`: passed for `src\troubleshooting\nac_idp_credential_test` and `tests\unit\troubleshooting\nac_idp_credential_test`.
- `mypy`: passed for `src\troubleshooting\nac_idp_credential_test`.
- `pydocstyle`: passed for `src\troubleshooting\nac_idp_credential_test`.
- `pytest`: 13 passed for `tests\unit\troubleshooting\nac_idp_credential_test`.
- `vulture`: passed for `src\troubleshooting\nac_idp_credential_test`.
- `interrogate`: passed with 100.0 percent for `src\troubleshooting\nac_idp_credential_test`.
- `bandit`: passed for `src\troubleshooting\nac_idp_credential_test`.
- `complexity-gate`: passed with maximum complexity 10.
- `test-quality-analyzer`: passed with 3 files checked and 0 new findings.
- `test_mistapi_sdk_compatibility`: passed with 486 call signatures checked.
- `test_output_scan_runtime_files`: passed with 27 tests.

## Files

- `src/troubleshooting/nac_idp_credential_test/**`
- `tests/unit/troubleshooting/nac_idp_credential_test/**`
- `specs/3565-nac-idp-credential-test/**`
- `changelog.d/issue-3565-nac-idp-credential-test.md`
