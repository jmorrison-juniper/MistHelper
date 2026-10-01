# Spec Conformance Checklist

**Linked Spec Issue**: #3690

Closes #3690

## Live verification

- Before: `Found 0 unacknowledged alarm(s). No unacknowledged alarms were found.`
- After: `Found 60 unacknowledged alarm(s).`
- The live dry run normalized 60 alarm rows in the current 24-hour window.
- Menu 281 ran with `--dry-run`, and no acknowledgement request was sent.
- The menu operation requested `GET /const/alarm_defs` and `GET /orgs/8a1ea872-241a-4c8e-a5ca-2d85674c7229/alarms/search?duration=24h&limit=1000`.

## Acceptance Criteria
- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality
- [x] Tests added or updated for all changed functionality
- [x] No new Ruff lint violations (`ruff check .`)
- [x] Code formatted with Black (`black --check --diff .`)
- [x] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`)

## Security
- [x] No hardcoded secrets, tokens, or passwords
- [x] Sensitive data handled via `.env` / environment variables only

## Deployment
- [x] Dry-run verified locally (ran affected menu operations)

## Documentation
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the PR number, the issue number, or the date
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)

## Gate evidence

- `python -m py_compile src\reports\alert_digest\model.py tests\unit\reports\alert_digest\test_alert_digest_model.py`
- `python -m ruff check src\reports\alert_digest tests\unit\reports\alert_digest`
- `python -m black --check src\reports\alert_digest tests\unit\reports\alert_digest`
- `python -m mypy src\reports\alert_digest --config-file pyproject.toml`
- `python -m pydocstyle src\reports\alert_digest`
- `python -m pytest tests\unit\reports\alert_digest -q --timeout=120`
- `python -m radon cc src\reports\alert_digest -j | complexity-gate --max 10`
- `test-quality-analyzer --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main`
- `python -m bandit -c pyproject.toml -r src\reports\alert_digest -q`
- `python -m pytest tests\integration\test_mistapi_sdk_compatibility.py tests\unit\web_portal\test_output_scan_runtime_files.py -q --timeout=120`
