## Summary

Closes #3572.

This draft pull request adds the owned package for menu 292 CSV imports. It supports organization PSKs, organization user MACs, organization assets, site PSKs, and site assets.

## Destructive operation notice

Menu 292 is destructive. It creates or updates Mist cloud records. A human must review the menu wiring before merge.

## Spec and wiring

- Spec: `specs/3572-csv-imports/spec.md`
- Plan: `specs/3572-csv-imports/plan.md`
- Research: `specs/3572-csv-imports/research.md`
- Wiring manifest: `specs/3572-csv-imports/wiring.md`

## Files changed

- `src/inventory/csv_imports/**`
- `tests/unit/inventory/csv_imports/**`
- `specs/3572-csv-imports/**`
- `changelog.d/issue-3572-csv-imports.md`

## Deferred integration work

Menu wiring is deferred to the tier integration pull request. The integration pull request must apply `specs/3572-csv-imports/wiring.md`, update generated menu references, and keep menu 292 in the destructive category.

## Validation

- `py_compile`: passed for `src/inventory/csv_imports`.
- `ruff`: passed for `src/inventory/csv_imports` and `tests/unit/inventory/csv_imports`.
- `black --check`: passed for `src/inventory/csv_imports` and `tests/unit/inventory/csv_imports`.
- `mypy`: passed for `src/inventory/csv_imports`.
- `pydocstyle`: passed for `src/inventory/csv_imports`.
- `pytest`: passed, 15 tests.
- `vulture`: passed for `src/inventory/csv_imports`.
- `interrogate`: passed with 100 percent docstring coverage.

## Checklist

- [x] Linked the issue with `Closes #3572`.
- [x] Added a release note fragment.
- [x] Added tests for the owned package.
- [x] Kept `MistHelper.py`, `operation_registry.py`, and generated menu references unchanged.
- [x] Stated that the operation is destructive and needs human review.
