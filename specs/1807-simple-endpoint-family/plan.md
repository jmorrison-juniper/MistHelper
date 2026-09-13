# Implementation Plan: Simple endpoint family stage one

**Branch**: `feat/1807-simple-endpoint-family` | **Date**: 2026-09-12 |
**Spec**: [spec.md](./spec.md)

## Summary

This feature adds `SimpleEndpointExporter`. The exporter holds four operation
tables for no-identifier, organization, site, and MSP endpoints. The operator
selects one operation from a prompt. The exporter resolves the SDK function,
collects all pages, normalizes the response, and writes through the shared data
exporter.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: `mistapi`, pytest, ruff, black, and mypy.

**Storage**: CSV, SQLite, or ArangoDB through the existing `DataExporter` path.

**Testing**: Unit tests under `tests/unit/export/` and strategy tests under
`tests/unit/`.

**Target Platform**: Windows 11 locally and Linux in continuous integration.

**Project Type**: A CLI menu export feature.

**Constraints**: The feature makes only read-only Mist API calls. It writes no
secrets and no cloud state.

## Constitution Check

| Principle | How this plan meets it |
| - | - |
| Five-Item Rule | One exporter class owns the behavior, and each table is grouped by scope. |
| Class-Based Architecture | `SimpleEndpointExporter` owns all execution logic. |
| Safety-First | The exporter uses `safe_input()` and returns safely on bad choices. |
| Full Deployment Pipeline | The implementation runs compile, lint, format, type, and unit checks. |
| Observability | The exporter logs before and after each meaningful action. |
| Inline Comments | New executable lines carry inline comments. |
| Action Logging | SDK calls, prompts, transforms, and writes are logged. |

## Project Structure

```text
src/export/simple_endpoint_exporter.py
src/refactors/endpoint_primary_key_strategies.py
src/utils/operation_registry.py
MistHelper.py
tests/unit/export/test_simple_endpoint_exporter.py
tests/unit/test_pk_strategies.py
```

## Design Decisions

### Decision 1: Resolve from the installed SDK

The discovery pass scans the installed `mistapi` package for exact function
names. It does not derive a module from a URL.

### Decision 2: Use one prompt per scope

Four menu entries keep the main menu small. The prompt shows all related
operations for the selected scope.

### Decision 3: Normalize non-list responses

Some endpoints return one JSON object. The exporter wraps that object in a list
so the shared writer receives rows.
