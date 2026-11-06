# Validation Guide: Runtime Dependency Refresh

Use this guide to validate the completed dependency refresh. The parent reported that the checks below passed. This agent did not run dependency tests.

## Prerequisites

- Use the project Python environment.
- Confirm that the checked-out branch contains the parent-owned dependency changes.
- Keep the feature selector command-scoped. Do not edit `.specify/feature.json`.

## Dependency and SDK checks

Run the existing export, lock, declaration parity, and SDK checks:

```powershell
python -m pytest tests/guardrails/test_dependency_export.py tests/guardrails/test_dependency_lock_file.py tests/guardrails/test_dependency_declaration_parity.py tests/integration/test_mistapi_sdk_compatibility.py
```

Expected result: all selected tests pass.

## Additional checks

Confirm these parent-reported results before publication:

- Dependency audit reports no findings.
- Package consistency and import checks pass.
- The Linux resolver succeeds.
- All 11 platform markers remain unchanged.
- The selected dependency checks report 28 passed tests.
- Database, dashboard, and release-note checks report 316 passed tests and one skipped test.

The parent reports 344 passed tests and one skipped test across the final test run. The skipped test requires pull request context.

## Scope check

Confirm that the feature changes only `uv.lock`, both dependency exports, the unique issue release note, and the managed specification files.
