# Implementation Plan: searchOrgDevices

**Branch**: `863-mist-search-org-devices` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)

## Summary

Add menu 249 for the read-only `searchOrgDevices` endpoint. Reuse
`OrgSearchExporter` so the endpoint receives the standard organization lookup,
SDK pagination, flattening, and multi-backend export flow.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: `mistapi`, `pytest`, Ruff, Black

**Storage**: CSV, SQLite, or ArangoDB through `DataExporter`

**Testing**: Pytest unit tests for `OrgSearchExporter`

**Target Platform**: Windows host and Podman container

**Project Type**: Python command-line tool

**Performance Goals**: Use the SDK pagination helper and preserve existing retry and rate-limit behavior.

**Constraints**: Keep the endpoint read-only, use ASCII logs, and preserve the five-item code rules.

**Scale/Scope**: One exporter method, one menu entry, one registry entry, tests, and documentation.

## Constitution Check

- **Five-item rule**: Pass. The feature reuses existing helpers and adds one short method.
- **Class-based design**: Pass. The method belongs to `OrgSearchExporter`.
- **Safety**: Pass. The endpoint uses `GET` and does not change Mist Cloud state.
- **Observability**: Pass. The shared exporter logs before and after the API call and export.
- **Inline comments**: Pass. New executable lines include intent comments.
- **Action logging**: Pass. The shared exporter provides lifecycle logging.

## Project Structure

```text
src/export/org_search_exporter.py
src/utils/operation_registry.py
MistHelper.py
tests/unit/export/test_org_search_exporter.py
README.md
CHANGELOG.md
documentation/menu_reference.md
specs/863-mist-search-org-devices/
```

## Design

`OrgSearchExporter.devices` calls
`mistapi.api.v1.orgs.devices.searchOrgDevices` with the active API session and
organization ID. The shared helper calls `mistapi.get_all`, flattens rows,
escapes multiline values, and writes `OrgDevices.csv`.

The existing endpoint catalog defines the composite `["id", "mac"]` key for
device search rows. This feature uses that strategy without a schema change.
