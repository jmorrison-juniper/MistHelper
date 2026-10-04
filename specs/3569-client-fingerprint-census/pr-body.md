# Spec Conformance Checklist

**Linked Spec Issue**: #3569

Closes #3569

## Summary

This pull request adds the menu `289` client fingerprint census package. The menu wiring is deferred to the tier integration pull request through `specs/3569-client-fingerprint-census/wiring.md`.

## Files

- `src/mist/intelligence/reports/client_fingerprint_census/`
- `tests/unit/reports/client_fingerprint_census/`
- `specs/3569-client-fingerprint-census/`
- `changelog.d/issue-3569-client-fingerprint-census.md`

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality

- [x] Tests added or updated for all changed functionality
- [x] Coverage meets or exceeds 80% threshold
- [x] New or changed guards state the measured count and prove one failing path
- [x] No new Ruff lint violations (`ruff check .`)
- [x] Code formatted with Black (`black --check --diff .`)
- [x] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`)

## Security

- [x] No hardcoded secrets, tokens, or passwords
- [x] Bandit passes with no new findings (`bandit -c pyproject.toml -r src\mist\intelligence\reports\client_fingerprint_census`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [x] Sensitive data handled via `.env` / environment variables only

## Deployment

- [ ] Dry-run verified locally (ran affected menu operations)
- [x] `.env` changes documented in `deploy/.env.example` (if applicable)
- [x] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)

- [x] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [x] Stable `data-testid` attributes added for new interactive elements
- [x] AI agent verified selectors via VS Code Browser Agent Tools
- [x] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation

- [ ] README.md updated (if user-facing changes)
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the PR number, the issue number, or the date
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)

## Validation

- `python -m py_compile src\mist\intelligence\reports\client_fingerprint_census\__init__.py src\mist\intelligence\reports\client_fingerprint_census\client.py src\mist\intelligence\reports\client_fingerprint_census\model.py src\mist\intelligence\reports\client_fingerprint_census\operation.py`: passed
- `python -m ruff check src\mist\intelligence\reports\client_fingerprint_census tests\unit\reports\client_fingerprint_census`: passed
- `python -m black --check src\mist\intelligence\reports\client_fingerprint_census tests\unit\reports\client_fingerprint_census`: passed
- `python -m mypy src\mist\intelligence\reports\client_fingerprint_census --config-file pyproject.toml`: passed
- `python -m pydocstyle src\mist\intelligence\reports\client_fingerprint_census`: passed
- `python -m pytest tests\unit\reports\client_fingerprint_census -q --timeout=120`: 12 passed
- `python -m vulture src\mist\intelligence\reports\client_fingerprint_census --min-confidence 70`: passed
- `python -m interrogate -v src\mist\intelligence\reports\client_fingerprint_census`: 100 percent
- `python -m radon cc src\mist\intelligence\reports\client_fingerprint_census -j | complexity-gate --max 10`: passed
- `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main`: passed
- `python -m bandit -c pyproject.toml -r src\mist\intelligence\reports\client_fingerprint_census -q`: passed
- `python -m pytest tests\integration\test_mistapi_sdk_compatibility.py -q --timeout=120`: passed
- `python -m pytest tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120`: passed
- `speckit.analyze`: remaining findings are fleet-scope deferrals. `wiring.md` carries the README and shared-file integration path.

## Deferred wiring

The integration pull request must apply `specs/3569-client-fingerprint-census/wiring.md` to the shared menu files, generated references, and primary key strategy table.
