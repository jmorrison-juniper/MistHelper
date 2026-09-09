# Implementation Plan: `searchOrgVars`

## Scope

Implement the read-only organization variable search endpoint without changing
the existing bulk collector or unrelated menu operations.

## Files

1. Extend `src/export/org_search_exporter.py` with `OrgSearchExporter.org_vars`.
2. Register menu 248 in `MistHelper.py`.
3. Register menu 248 as a safe operation in `src/utils/operation_registry.py`.
4. Correct the `searchOrgVars` composite key in `src/refactors/endpoint_primary_key_strategies.py`.
5. Add unit and menu registration tests.
6. Update the README, menu reference, and changelog.

## Validation

Run the focused exporter tests, menu registry tests, Python compilation, Ruff,
Black, and the endpoint strategy tests before commit.
