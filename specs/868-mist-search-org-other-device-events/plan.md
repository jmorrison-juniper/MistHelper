# Implementation Plan: Search Organization Other-Device Events

**Branch**: `feat/1376-search-org-other-device-events` | **Date**: 2026-09-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/868-mist-search-org-other-device-events/spec.md`

## Summary

Add menu 261 for the read-only `searchOrgOtherDeviceEvents` endpoint. The
exporter resolves one organization, prompts safely for the optional query
filters, calls the installed Mist SDK alias for the endpoint, pages all event
rows, flattens nested values, and writes through
`DataExporter.write_with_format_selection`.

The endpoint specification names
`mistapi.api.v1.orgs.otherdevices.events.search.searchOrgOtherDeviceEvents`,
but the installed SDK exposes the callable at
`mistapi.api.v1.orgs.otherdevices.searchOrgOtherDeviceEvents`. The new menu
uses the installed alias, which reaches the same REST path.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: `mistapi` 0.63.3, existing MistHelper utilities

**Storage**: CSV, SQLite, or ArangoDB through `DataExporter`

**Testing**: pytest unit tests, `py_compile`, Ruff, and Black

**Target Platform**: Windows host and Podman Linux container

**Project Type**: Menu-driven CLI

**Performance Goals**: One paged read operation per selected organization

**Constraints**: Use `safe_input()` for every prompt. Keep logs ASCII-only. Do
not log credentials. Keep output paths backend-safe.

**Scale/Scope**: One exporter method, one menu registration, one operation
registry update, focused tests, SpecKit documents, and user documentation
updates.

## Constitution Check

- **Five-Item Rule**: PASS. The feature extends the shared org-search class with
  a short method and a bounded prompt map.
- **Class-Based Architecture**: PASS. The feature lives in
  `OrgSearchExporter`. No wrapper function is added.
- **Safety-First Input**: PASS. Every optional filter prompt uses
  `InputUtils.safe_input()`.
- **Observability**: PASS. The shared helper logs the call, row count,
  persistence, and error context without secrets.
- **Inline Comments**: PASS. Every new executable line carries an inline
  comment.
- **Multi-Backend Output**: PASS. The shared `DataExporter` selects the backend.

## Project Structure

```text
src/export/org_search_exporter.py
tests/unit/export/test_org_search_exporter.py
MistHelper.py
src/utils/operation_registry.py
src/refactors/endpoint_primary_key_strategies.py
README.md
CHANGELOG.md
documentation/menu_reference.md
documentation/wiki/Menu-Reference.md
documentation/menu-highlights.md
specs/868-mist-search-org-other-device-events/plan.md
specs/868-mist-search-org-other-device-events/research.md
specs/868-mist-search-org-other-device-events/tasks.md
```

**Structure Decision**: Reuse `OrgSearchExporter` because the endpoint matches
the existing prompt, fetch, paginate, and persist flow for org-scoped searches.

## Implementation Notes

1. Add the optional filter prompt map for `searchOrgOtherDeviceEvents`.
2. Add `OrgSearchExporter.other_device_events()`.
3. Move the menu binding to menu 261 and register it as `safe`.
4. Keep the existing composite primary-key strategy of `id`, `mac`, and
   `timestamp`.
5. Regenerate the menu reference from the canonical menu and registry sources.

## Validation Plan

Run the focused exporter tests, then compile, lint, format, and run the menu
reference generator. Verify that menu 261 appears in the generated output and
that menu 252 no longer maps to this operation.
