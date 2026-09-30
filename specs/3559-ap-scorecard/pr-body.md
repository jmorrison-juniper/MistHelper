# Spec Conformance Checklist

**Linked Spec Issue**: #3559

Closes #3559

## Summary

- Adds `src/reports/ap_scorecard/` with the `ApScorecard.run` handler for menu `278`.
- Uses `listOrgDevicesStats` with `type=ap` through the existing `mistapi.get_all` pagination seam.
- Writes `ApScorecard.csv` and `ApScorecardBySite.csv` through `DataExporter`.
- Defers menu registration and shared-file wiring to `specs/3559-ap-scorecard/wiring.md`.

## Files

- `specs/3559-ap-scorecard/`
- `src/reports/ap_scorecard/`
- `tests/unit/reports/ap_scorecard/`
- `changelog.d/issue-3559-ap-scorecard.md`

## Acceptance Criteria

- [x] All feature-owned acceptance criteria from the linked Spec Issue are met.
- [x] Each feature-owned criterion has a corresponding test or verification.
- [x] The final `MistHelper.py --test` proof is deferred until the integration pull request registers menu `278`.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations: `ruff check src\reports\ap_scorecard tests\unit\reports\ap_scorecard`.
- [x] Code formatted with Black: `black --check src\reports\ap_scorecard tests\unit\reports\ap_scorecard`.
- [x] mypy passes: `mypy src\reports\ap_scorecard --config-file pyproject.toml`.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit is not required for the feature-owned subset because no security-sensitive code changed.
- [x] pip-audit is not required because no dependency manifest changed.
- [x] Sensitive data stays in the existing environment flow.

## Deployment

- [x] Dry-run verified locally through unit tests for the operation handler.
- [x] `.env` changes are not applicable.
- [x] Container build is not applicable because no container file changed.

## UI / E2E Testing

- [x] Not applicable because no web UI changed.

## Documentation

- [x] README.md update is deferred to the integration pull request.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Validation

```text
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m py_compile src\reports\ap_scorecard\__init__.py src\reports\ap_scorecard\client.py src\reports\ap_scorecard\model.py src\reports\ap_scorecard\operation.py tests\unit\reports\ap_scorecard\__init__.py tests\unit\reports\ap_scorecard\conftest.py tests\unit\reports\ap_scorecard\test_ap_scorecard_client.py tests\unit\reports\ap_scorecard\test_ap_scorecard_model.py tests\unit\reports\ap_scorecard\test_ap_scorecard_operation.py tests\unit\reports\ap_scorecard\test_ap_scorecard_support_files.py
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m ruff check src\reports\ap_scorecard tests\unit\reports\ap_scorecard
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m black --check src\reports\ap_scorecard tests\unit\reports\ap_scorecard
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m mypy src\reports\ap_scorecard --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m pydocstyle src\reports\ap_scorecard
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m vulture src\reports\ap_scorecard --min-confidence 70
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m interrogate -v src\reports\ap_scorecard
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m radon cc src\reports\ap_scorecard -j | C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\complexity-gate.exe --max 10
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\test-quality-analyzer.exe --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main
C:\Users\jmorrison\mh-fleet\3559-ap-scorecard\.venv\Scripts\python.exe -m pytest tests\unit\reports\ap_scorecard -q --timeout=120
Result: 26 passed. Interrogate reported 100.0% package docstring coverage. Complexity gate and test quality ratchet passed.
```

## SpecKit analyze

The final analyze run reported no open findings.
