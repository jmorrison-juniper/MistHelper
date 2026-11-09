# Implementation Plan: Other-device event failure boundaries

**Branch**: `jmorrison-juniper-other-device-event-audit` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: The specification in this managed numeric feature directory.

## Summary

Keep the broad handler only around the endpoint and pagination calls.
The SDK has no common exception type for malformed remote pages.
Use fixed error messages without exception text.
Move row counting and persistence outside the handler.

## Technical Context

**Language/Version**: Python 3.13 or newer. Local interpreter: Python 3.14.7.

**Primary Dependencies**: Installed mistapi 0.64.1, requests, pytest.

**Storage**: Mocked export writer only.

**Testing**: Focused pytest cases with DNS and sockets blocked.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Existing menu operation.

**Performance Goals**: No new requests or retries.

**Constraints**: Local work only. No credentials, real databases, or cloud requests.

**Scale/Scope**: One exporter, its existing test file, one unique release note, and this feature directory.

## Constitution Check

- Preserve the existing SDK REST endpoint and pagination helper.
- Prove successful output, failures, and privacy with offline tests.
- Keep each new feature directory at five children or fewer.
- Preserve the existing shared feature pointer and app-managed branch.
- Use a unique release note. Existing process-folder debt remains outside this slice.
- Track process-folder migration separately through the existing managed-route guard.
- Existing exporter methods exceed 25 physical lines because comments and logging occupy separate lines.
  Do not expand their responsibilities. Separate structural remediation remains outside this bounded audit.
- Tests use a mocked writer, so no product output reaches a real backend.
- Use `Refs #1794` in any local commit, never a closing reference.

The design check passes with the existing method-length debt recorded.
PowerShell is absent. Read the scripts and templates without running selector-writing setup commands.
The feature route uses the inspected eight-digit base-5 calculation.
The mandatory branch hook cannot replace the app-managed branch.
Optional commit hooks are deferred until validation completes.

## Project Structure

- `src/operations/exporting/export/site_other_device_events_exporter.py`
- `tests/unit/export/test_site_other_device_events_exporter.py`
- `changelog.d/issue-1794-other-device-events-boundaries.md`
- This feature root: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
- Supporting design records: research, data model, quickstart, contracts, and checklists.

## Complexity Tracking

| Existing debt | Reason to retain | Separate action |
|---|---|---|
| Long exporter methods | A narrow handler audit must preserve the operation structure. | Consider a dedicated method-structure slice. |
| Large process directories | Required unique records must not overwrite shared records. | Continue the managed-route migration. |
