# Implementation Plan: Export Log Disclosure

**Branch**: `jmorrison-juniper-csv-logging-disclosure-fix` | **Date**: 2026-11-15
**Spec**: [Specification](spec.md)

## Summary

Replace CSV row diagnostic output with aggregate counts. Preserve CSV contents
and failure context. The inventory source is held by issue #4762. Its device,
table, and address logging repair remains blocked.

## Technical Context

**Language/Version**: Python 3.15.
**Primary Dependencies**: Existing CSV writer and inventory exporter.
**Storage**: CSV files and existing selected export backends.
**Testing**: pytest with synthetic records and captured DEBUG logs.
**Target Platform**: Windows, macOS, Linux, and the Podman container.
**Project Type**: Network operations CLI.
**Performance Goals**: Avoid per-row diagnostic output.
**Constraints**: Preserve issue #4776 CSV carriage-return behavior.
**Scale/Scope**: Two existing exporters and their focused tests.

## Constitution Check

The change uses a routed numeric feature record and one release fragment.
The existing export package and process folders exceed the five-child limit.
This change adds no source modules and does not increase package debt.
Separate incremental remediation of existing folder debt remains necessary.
Existing large exporter classes and methods remain outside this bounded repair.
Future structural work must reduce that debt without a compatibility shim.
The output remains under the existing data destination rules.
The change adds no Mist Cloud requests or destructive operations.
The commit must use the Conventional Commits format.
The same checks apply after the design phase.

## Project Structure

- `src/operations/exporting/export/data_exporter.py`: CSV row emission.
- `src/operations/exporting/export/org_inventory_exporter.py`: held inventory logs.
- `tests/unit/export/test_data_exporter.py`: CSV marker regression.
- `tests/unit/test_org_inventory_exporter_helpers.py`: blocked inventory regression.
- `design/`: research, data model, contract, and validation guide.

## Complexity Tracking

The touched exporters are existing large classes. A broader decomposition is
outside this repair and must proceed as separate incremental work.
