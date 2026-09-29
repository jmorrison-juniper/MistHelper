# Wiring Notes: Site Variable Audit

## Status

This file is a planning placeholder. The final wiring manifest is deferred to
the implementation or integration pull request.

## Required sections for the final manifest

The final manifest must include these sections:

1. Source package files.
2. Test files.
3. Menu registration.
4. Operation registry entry.
5. Generated menu reference files.
6. Release note fragment.
7. Validation commands.

## Deferred source package files

The implementation pull request must add:

- `src/reports/site_variable_audit/__init__.py`
- `src/reports/site_variable_audit/client.py`
- `src/reports/site_variable_audit/model.py`
- `src/reports/site_variable_audit/operation.py`

## Deferred test files

The implementation pull request must add tests under:

- `tests/unit/reports/site_variable_audit/`

The tests must target model logic and client fixtures. Tests must not use the
network.

## Deferred integration files

The integration pull request must update:

- `MistHelper.py`
- `src/utils/operation_registry.py`
- `README.md`
- `documentation/menu_reference.md`
- generated menu API map files, if the generator changes them

This planning step must not edit those files.

The implementation step must add:

- `changelog.d/issue-3556-site-variable-audit.md`

## Required run handler

Menu 275 must call `SiteVariableAudit.run()`.

`SiteVariableAudit.run()` must take no positional argument. It must read the API
session and organization data through `SourceDependencyResolver`.
