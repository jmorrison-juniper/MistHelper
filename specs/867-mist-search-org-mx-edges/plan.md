# Implementation Plan: searchOrgMxEdges

## Scope

Record the completed `searchOrgMxEdges` implementation that now ships on
`origin/main` as menu 253, and finish the missing SpecKit files for issue
#1375.

## Design

1. Confirm the authoritative HTTP contract from the local OpenAPI snapshot and
   endpoint index.
2. Confirm the installed `mistapi` SDK signature from the fresh worktree
   virtual environment.
3. Confirm the current MistHelper implementation on `origin/main`, which uses
   `OrgSearchExporter.mx_edges`, `InputUtils.safe_input`,
   `mistapi.get_all`, `DataExporter.write_with_format_selection`, and the
   existing `searchOrgMxEdges` composite primary-key strategy.
4. Restore the missing workflow records under
   `specs/867-mist-search-org-mx-edges/`.
5. Correct the related documentation that still says this endpoint is missing
   or unused by MistHelper.

## Validation

- Run `python -m py_compile` on the touched Python entry points that exercise
  the menu wiring.
- Run `python -m ruff check .`.
- Run `python -m black --check .`.
- Run the focused exporter and primary-key tests that cover
  `searchOrgMxEdges`.
