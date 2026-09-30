# Spec Conformance Checklist

Closes #3553

**Linked Spec Issue**: #3553

## Summary

This pull request adds the certificate expiry report package for menu 272.
It adds model, client, operation, and unit-test coverage under the feature-owned paths.
The integration pull request wires menu 272 and applies `specs/3553-certificate-expiry-report/wiring.md`.

## Files

- `src/reports/certificate_expiry/**`
- `tests/unit/reports/certificate_expiry/**`
- `specs/3553-certificate-expiry-report/**`
- `changelog.d/issue-3553-certificate-expiry-report.md`
- `requirements.txt`

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met for the feature-owned package.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds the 80 percent threshold.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations.
- [x] Code formatted with Black.
- [x] mypy passes for `src/reports/certificate_expiry`.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passes with no new findings for `src/reports/certificate_expiry`.
- [x] pip-audit is clean for `requirements.txt`.
- [x] Sensitive certificate bodies and private-key markers stay out of logs and output rows.

## Deployment

- [x] Dry-run verified locally with unit tests and handler fixtures.
- [x] `.env` changes are not applicable.
- [x] Container build is not applicable.

## UI / E2E Testing

- [x] Web UI changes are not applicable.
- [x] Playwright changes are not applicable.

## Documentation

- [x] README.md is deferred to the integration pull request.
- [x] Release note added as `changelog.d/issue-3553-certificate-expiry-report.md`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Validation

- `python -m py_compile MistHelper.py` and all new Python files passed.
- `python -m ruff check src\reports\certificate_expiry tests\unit\reports\certificate_expiry` passed.
- `python -m black --check src\reports\certificate_expiry tests\unit\reports\certificate_expiry` passed.
- `python -m mypy src\reports\certificate_expiry --config-file pyproject.toml` passed.
- `python -m pydocstyle src\reports\certificate_expiry` passed.
- `python -m pytest tests\unit\reports\certificate_expiry -q --timeout=120` passed, 26 tests.
- `python -m vulture src\reports\certificate_expiry --min-confidence 70` passed.
- `python -m interrogate -v src\reports\certificate_expiry` passed.
- `python -m radon cc src\reports\certificate_expiry -j | complexity-gate --max 10` passed.
- `test-quality-analyzer --gate --changed-from origin/main` passed.
- `python -m pytest tests\integration\test_mistapi_sdk_compatibility.py -q --timeout=120` passed, 8 tests.
- `python -m pytest tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120` passed, 27 tests.
- `python -m bandit -c pyproject.toml -r src\reports\certificate_expiry -q` passed.
- `python -m pip_audit -r requirements.txt` passed with no known vulnerabilities.
- `speckit.analyze` passed with no actionable findings.

## Deferred Integration

The integration pull request must register menu 272, add the primary key strategy, update menu documentation, and regenerate menu references.
This branch adds a runtime guard that blocks export until `certificate_expiry_report` exists in the primary key strategy table.
