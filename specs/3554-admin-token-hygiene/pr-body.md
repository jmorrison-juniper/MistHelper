# Spec Conformance Checklist

Closes #3554

**Linked Spec Issue**: #3554

## Summary

This pull request adds the menu 273 admin and API token hygiene report package.
The integration pull request will wire the menu entry from `specs/3554-admin-token-hygiene/wiring.md`.

## Files

- `src/mist/intelligence/reports/admin_token_hygiene/**`
- `tests/unit/reports/admin_token_hygiene/**`
- `specs/3554-admin-token-hygiene/**`
- `changelog.d/issue-3554-admin-token-hygiene.md`

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds the 80 percent threshold.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations.
- [x] Code formatted with Black.
- [x] mypy passes.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passes with no new findings.
- [ ] pip-audit clean. This branch changed no dependency file.
- [x] Sensitive data is handled through `.env` or environment variables only.

## Deployment

- [x] Dry-run verified locally through unit tests with fake Mist data.
- [x] `.env` changes documented in `deploy/.env.example`, if applicable. No new `.env` key was added.
- [x] Container builds successfully, if the Containerfile changed. This branch changed no container file.

## UI / E2E Testing

- [x] Not applicable. This branch changes no web UI files.

## Documentation

- [ ] README.md updated, if user-facing changes. This is deferred to the integration pull request.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Local Gate Results

- `py_compile`: pass.
- `ruff check src\mist\intelligence\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene`: pass.
- `black --check src\mist\intelligence\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene`: pass.
- `mypy src\mist\intelligence\reports\admin_token_hygiene --config-file pyproject.toml`: pass.
- `pydocstyle src\mist\intelligence\reports\admin_token_hygiene`: pass.
- `pytest tests\unit\reports\admin_token_hygiene -q --timeout=120`: 19 passed.
- `bandit -c pyproject.toml -r src\mist\intelligence\reports\admin_token_hygiene -q`: pass.
- `radon cc src\mist\intelligence\reports\admin_token_hygiene -j | complexity-gate --max 10`: pass.
- `vulture src\mist\intelligence\reports\admin_token_hygiene --min-confidence 70`: pass.
- `interrogate -q src\mist\intelligence\reports\admin_token_hygiene`: pass.
- `test-quality-analyzer --gate --changed-from origin/main`: pass.
- `pytest tests\integration\test_mistapi_sdk_compatibility.py -q --timeout=120`: pass.
- `pytest tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120`: pass.

## Deferred Integration

The integration pull request must apply the shared menu registration, operation registry row, primary key strategies, README update, generated menu references, and menu API map from `specs/3554-admin-token-hygiene/wiring.md`.
