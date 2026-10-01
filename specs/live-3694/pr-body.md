# Spec Conformance Checklist

**Linked Spec Issue**: #3694

Closes #3694.

## Summary

This repair resolves organization WLAN rows through the WLAN template scope before the site variable audit scans them.
It also skips tokens in `portal.*MessageFormat` fields because Mist fills those guest portal message placeholders.

## Live verification

Before repair, the issue showed these live cells:

```text
SiteVariableAudit.csv: 14 rows template_type=wlan site_id=00000000-...
variable_name=code x6, duration x6, field_path=$.portal.smsMessageFormat
560 rows template_type=gateway_template variable_name=branchvlan
```

After repair, menu 275 against the home organization produced these live cells:

```text
row_count_by_template_type=gateway_template:560
placeholder_site_rows=0
code_duration_rows=0
branchvlan_rows=560
branchvlan_missing_sites=140
summary_site_rows=144
summary_sites_with_missing=140
```

Console output:

```text
Site variable audit found 140 site(s) with missing variables. Wrote SiteVariableAudit.csv and SiteVariableSummary.csv.
```

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality

- [x] Tests added or updated for all changed functionality
- [ ] Coverage meets or exceeds 80% threshold
- [ ] New or changed guards state the measured count and prove one failing path
- [ ] No new Ruff lint violations (`ruff check .`)
- [ ] Code formatted with Black (`black --check --diff .`)
- [ ] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`)

## Security

- [x] No hardcoded secrets, tokens, or passwords
- [ ] Bandit passes with no new findings (`bandit -c pyproject.toml -r .`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [x] Sensitive data handled via `.env` / environment variables only

## Deployment

- [x] Dry-run verified locally (ran affected menu operations)
- [ ] `.env` changes documented in `deploy/.env.example` (if applicable)
- [ ] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)

- [ ] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [ ] Stable `data-testid` attributes added for new interactive elements
- [ ] AI agent verified selectors via VS Code Browser Agent Tools
- [ ] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation

- [ ] README.md updated (if user-facing changes)
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the PR number, the issue number, or the date
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)

## Local validation

```text
python -m py_compile src\reports\site_variable_audit\__init__.py src\reports\site_variable_audit\client.py src\reports\site_variable_audit\model.py src\reports\site_variable_audit\operation.py tests\unit\reports\site_variable_audit\__init__.py tests\unit\reports\site_variable_audit\site_variable_audit_client_test.py tests\unit\reports\site_variable_audit\site_variable_audit_contract_test.py tests\unit\reports\site_variable_audit\site_variable_audit_fixtures_test.py tests\unit\reports\site_variable_audit\site_variable_audit_model_test.py tests\unit\reports\site_variable_audit\site_variable_audit_operation_test.py tests\unit\reports\site_variable_audit\site_variable_audit_summary_test.py
python -m ruff check src\reports\site_variable_audit tests\unit\reports\site_variable_audit
python -m black --check src\reports\site_variable_audit tests\unit\reports\site_variable_audit
python -m mypy src\reports\site_variable_audit --config-file pyproject.toml
python -m pydocstyle src\reports\site_variable_audit
python -m pytest tests\unit\reports\site_variable_audit -q --timeout=120
python -m radon cc src\reports\site_variable_audit -j | complexity-gate --max 10
test-quality-analyzer --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main
python -m bandit -c pyproject.toml -r src\reports\site_variable_audit -q
python -m pytest tests\integration\test_mistapi_sdk_compatibility.py tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120
.\.venv\Scripts\python.exe MistHelper.py --skip-deps -M 275 -O 8a1ea872-241a-4c8e-a5ca-2d85674c7229 *> data\live-275.log
```
