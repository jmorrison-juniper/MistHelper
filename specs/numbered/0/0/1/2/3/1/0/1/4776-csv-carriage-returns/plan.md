# Implementation Plan: Preserve CSV Carriage Returns

**Branch**: `jmorrison-juniper-csv-carriage-return-preservation` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

Preserve carriage returns in normalized records. Convert them to literal `\r` at CSV output.
Keep existing line-feed and list handling, including shared processing before backend selection.

## Technical Context

**Language/Version**: Python 3.15.
**Primary Dependencies**: Standard library and existing export helpers.
**Storage**: CSV, SQLite, and the existing polyglot store.
**Testing**: pytest with synthetic records.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Python operations tool.
**Performance Goals**: No new performance target.
**Constraints**: Do not access production systems or held hardware changes.
**Scale/Scope**: Shared record processing and CSV output.

## Constitution Check

- The managed numeric route holds the feature records.
- The change adds one unique release fragment to the existing process folder.
- The process folder has existing child-count debt. A separate migration must reduce that debt.
- Existing shared classes exceed structural limits. This change adds no class or module.
- A separate refactor must reduce the existing class and module debt.
- The change uses no new Mist transport or configuration.
- Product outputs remain under `data/`. Tests use temporary paths.
- Use a Conventional Commit subject and pull request title.

The design retains these decisions after Phase 1. No new structural violation is needed.

## Project Structure

- `src/foundation/models/data/data_processing_utils.py`: preserve carriage returns in shared processing.
- `src/operations/exporting/export/data_exporter.py`: escape carriage returns at CSV output.
- `tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py`: shared helper regression.
- `tests/unit/export/test_data_exporter.py`: CSV and backend regression.
- `tests/unit/export/test_endpoint_family_exporter.py`: update pre-dispatch expectations.
- `tests/unit/db/sle_window_summary/test_backend_preservation.py`: SQLite carriage-return regression.
- `changelog.d/`: issue-specific release fragment.

## Complexity Tracking

Existing hierarchy debt is recorded above. The change does not add a hierarchy level.
