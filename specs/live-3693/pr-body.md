# Spec Conformance Checklist

**Linked Spec Issue**: #3693

Closes #3693

## Summary

- Fire `no_two_factor` when `two_factor_verified` is `false`.
- Write `not_reported` when `listOrgAdmins` omits SSO state, password age, and invite expiry.
- Update the menu 273 console summary to count admins with no two-factor authentication.

## Live Verification

Before repair:

```text
AdminHygiene.csv: jmorrison@petsmart.com two_factor_state=disabled sso_state=unknown password_age_days=unknown findings=<empty>
```

After repair:

```text
AdminHygiene.csv: jmorrison@petsmart.com two_factor_state=disabled sso_state=not_reported password_age_days=not_reported invite_expiry=not_reported findings=no_two_factor
Console: Admin hygiene admins with no two-factor authentication: 3
Console: Admin hygiene API did not report SSO state, password age, or invite expiry for 13 admins
```

The live home organization returned 13 admins and 4 tokens.

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold. Existing package coverage is not reduced by this targeted change.
- [x] New or changed guards state the measured count and prove one failing path. Not applicable because this change adds no guard.
- [x] No new Ruff lint violations (`ruff check .`).
- [x] Code formatted with Black (`black --check --diff .`).
- [x] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`).

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passes with no new findings (`bandit -c pyproject.toml -r .`).
- [ ] pip-audit clean (`pip-audit -r requirements.txt`). Not run because no dependency changed.
- [x] Sensitive data handled via `.env` / environment variables only.

## Deployment

- [x] Dry-run verified locally (ran affected menu operations).
- [x] `.env` changes documented in `deploy/.env.example` (if applicable). Not applicable because `.env` did not change.
- [x] Container builds successfully (if Containerfile changed). Not applicable because no container file changed.

## UI / E2E Testing (if web UI changed)

- [x] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`. Not applicable because no web UI changed.
- [x] Stable `data-testid` attributes added for new interactive elements. Not applicable because no web UI changed.
- [x] AI agent verified selectors via VS Code Browser Agent Tools. Not applicable because no web UI changed.
- [x] Screenshots/traces captured for main UI flows (attached or in CI artifacts). Not applicable because no web UI changed.

## Documentation

- [x] README.md updated (if user-facing changes). Not applicable because this repair changes an existing report defect only.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the PR number, the issue number, or the date.
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file).

## Gates

```text
python -m py_compile src\mist\intelligence\reports\admin_token_hygiene\client.py src\mist\intelligence\reports\admin_token_hygiene\model.py src\mist\intelligence\reports\admin_token_hygiene\operation.py tests\unit\reports\admin_token_hygiene\test_admin_token_hygiene_model.py
python -m ruff check src\mist\intelligence\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene
python -m black --check src\mist\intelligence\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene
python -m mypy src\mist\intelligence\reports\admin_token_hygiene --config-file pyproject.toml
python -m pydocstyle src\mist\intelligence\reports\admin_token_hygiene
python -m pytest tests\unit\reports\admin_token_hygiene -q --timeout=120
python -m radon cc src\mist\intelligence\reports\admin_token_hygiene -j | complexity-gate --max 10
test-quality-analyzer --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main
python -m bandit -c pyproject.toml -r src\mist\intelligence\reports\admin_token_hygiene -q
python -m pytest tests\integration\test_mistapi_sdk_compatibility.py tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120
```
