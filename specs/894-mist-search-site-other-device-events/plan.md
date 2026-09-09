# Implementation Plan: Search Site Other Device Events

**Branch**: `feat/1402-search-site-other-device-events` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/894-mist-search-site-other-device-events/spec.md`

## Summary

Add menu 249 for the read-only `searchSiteOtherDeviceEvents` endpoint. The
exporter resolves one site with the shared site helper, calls the verified
Mist SDK function, pages all event rows, flattens nested values, and writes
through `DataExporter.write_with_format_selection`.

The installed SDK exposes the operation at
`mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents`. The endpoint
uses the existing composite key strategy of `mac` and `timestamp`.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: `mistapi` 0.63.3, existing MistHelper utilities

**Storage**: CSV, SQLite, or ArangoDB through `DataExporter`

**Testing**: pytest unit tests, `py_compile`, Ruff, and Black

**Target Platform**: Windows host and Podman Linux container

**Project Type**: Menu-driven CLI

**Performance Goals**: One paged read operation per selected site

**Constraints**: Use `safe_input()` through the shared site resolver. Keep logs
ASCII-only. Do not log credentials. Keep output paths backend-safe.

**Scale/Scope**: One exporter module, one menu registration, endpoint strategy
verification, focused tests, and documentation updates.

## Constitution Check

- **Five-Item Rule**: PASS. The exporter uses short static methods with limited
  parameters and bounded control flow.
- **Class-Based Architecture**: PASS. The feature lives in
  `SiteOtherDeviceEventsExporter`. No wrapper function is added.
- **Safety-First Input**: PASS. Site selection uses the existing EOF-safe
  `InputUtils.safe_input()` flow.
- **Observability**: PASS. Logs record the call, row count, persistence, and
  error context without secrets.
- **Inline Comments**: PASS. New executable lines include intent comments.
- **Multi-Backend Output**: PASS. The shared DataExporter selects the backend.

## Project Structure

```text
src/export/site_other_device_events_exporter.py
tests/unit/export/test_site_other_device_events_exporter.py
MistHelper.py
src/refactors/endpoint_primary_key_strategies.py
README.md
CHANGELOG.md
documentation/menu_reference.md
specs/894-mist-search-site-other-device-events/plan.md
specs/894-mist-search-site-other-device-events/tasks.md
```

**Structure Decision**: Add a focused exporter module and wire it into the
existing menu registry. Keep the existing primary-key catalog authoritative.

## Implementation Notes

1. Resolve a site through `SiteDeviceExporter._resolve_site_for_stats()`.
2. Call `mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents()`.
3. Use `mistapi.get_all()` for pagination.
4. Flatten nested fields and escape multiline values.
5. Persist with operationId `searchSiteOtherDeviceEvents`.
6. Report an empty response without creating an export.

## Validation Plan

Run the focused exporter tests, then compile, lint, format, and run the menu
registry checks. Run the non-live menu smoke path with mocked collaborators.
