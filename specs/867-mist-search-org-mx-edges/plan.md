# Implementation Plan: searchOrgMxEdges

## Scope

Add the read-only `searchOrgMxEdges` organization search to MistHelper without
changing the existing export backends or SDK pagination behavior.

## Design

1. Extend `OrgSearchExporter` with a menu entry that resolves the organization,
   collects optional query filters through `InputUtils.safe_input`, calls the
   installed SDK callable, and persists rows through `_persist`.
2. Preserve the existing `searchOrgMxEdges` composite primary-key strategy and
   register the operation in menu slot 248.
3. Add unit coverage for typed filter forwarding, default omission, pagination,
   and DataExporter binding.
4. Regenerate the menu references and update README and CHANGELOG.

## Validation

- Run the focused organization search exporter tests.
- Run `python -m py_compile MistHelper.py`.
- Run `python -m ruff check` and `python -m black --check` when available.
- Run the menu reference generator and confirm no generated drift.
