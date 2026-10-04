# Spec Conformance Checklist

**Linked Spec Issue**: #3570

Closes #3570

## Summary
- Added the RF diagnostics package for deferred menu 290 wiring.
- Added spectrum analysis start and bounded poll support.
- Added client RF diagnostic recording, stop, download, and audit support.
- Deferred menu, registry, endpoint catalog, README, generated reference, and category table changes to `specs/3570-spectrum-rfdiag/wiring.md`.

## Files
- `src/mist/intelligence/troubleshooting/rf_diagnostics/**`
- `tests/unit/troubleshooting/rf_diagnostics/**`
- `specs/3570-spectrum-rfdiag/**`
- `changelog.d/issue-3570-spectrum-rfdiag.md`

## Acceptance Criteria
- [x] All acceptance criteria from the linked Spec Issue are met for the package boundary.
- [x] Each criterion has a corresponding test or verification.

## Quality
- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations (`ruff check src/mist/intelligence/troubleshooting/rf_diagnostics tests/unit/troubleshooting/rf_diagnostics`).
- [x] Code formatted with Black (`black --check src/mist/intelligence/troubleshooting/rf_diagnostics tests/unit/troubleshooting/rf_diagnostics`).
- [x] mypy passes (`mypy src/mist/intelligence/troubleshooting/rf_diagnostics --config-file pyproject.toml`).

## Security
- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passes with no new findings (`bandit -c pyproject.toml -r src/mist/intelligence/troubleshooting/rf_diagnostics -q`).
- [x] pip-audit is not applicable because this change adds no dependency.
- [x] Sensitive data handled via existing environment/session handling only.

## Deployment
- [x] Dry-run verified locally with unit tests and fake Mist clients.
- [x] `.env` changes documented in `deploy/.env.example` if applicable. Not applicable.
- [x] Container builds successfully if Containerfile changed. Not applicable.

## UI / E2E Testing
- [x] Playwright E2E tests added or updated if web UI changed. Not applicable.
- [x] Stable `data-testid` attributes added for new interactive elements. Not applicable.
- [x] AI agent verified selectors through Browser Agent Tools. Not applicable.
- [x] Screenshots or traces captured for main UI flows. Not applicable.

## Documentation
- [x] README.md updated if user-facing changes. Deferred in wiring manifest.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Validation
- `pytest tests/unit/troubleshooting/rf_diagnostics -q --timeout=120`: 18 passed.
- `pytest tests/integration/test_mistapi_sdk_compatibility.py -q --timeout=120`: 8 passed, 482 call signatures checked.
- `pytest tests/unit/web_portal/test_output_scan_runtime_files.py -q --timeout=120`: 27 passed.
- `test-quality-analyzer --gate`: 8 files checked, 0 findings.
- `complexity-gate --max 10`: all functions within threshold.
- `interrogate -v src/mist/intelligence/troubleshooting/rf_diagnostics`: 100 percent.
- `bandit -c pyproject.toml -r src/mist/intelligence/troubleshooting/rf_diagnostics -q`: passed.
