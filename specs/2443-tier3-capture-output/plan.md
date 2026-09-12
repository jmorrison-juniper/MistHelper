# Implementation Plan: Complete Tier 3 Capture Output

**Branch**: `fix/2443-tier3-capture-output` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/2443-tier3-capture-output/spec.md`

## Summary

The collector already stores Tier 3 data. The capture page and export layer discard it.
Add one shared section catalog for page tables and export kinds. Render bounded tables.
Add a safe `details_json` export field that retains all non-credential fields.
Extend the browser stand-in and assert each Tier 3 section in the page and downloads.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Flask, Jinja, pytest, pytest-playwright

**Storage**: Existing ArangoDB capture documents. No schema or key change.

**Testing**: pytest unit tests, contract tests, and Playwright E2E tests

**Target Platform**: Linux container and Windows developer workstation

**Project Type**: Server-rendered web application

**Performance Goals**: Render at most 500 rows in each table. Preserve complete downloads.

**Constraints**: No new dependency. No Mist write. No upgrade start. No credential output.

**Scale/Scope**: Nine result tables and ten export row kinds.

## Constitution Check

- PASS: The issue exists before implementation.
- PASS: The branch starts from `main` in a separate worktree.
- PASS: The change uses the existing capture document and natural key.
- PASS: The page keeps the existing row cap.
- PASS: The browser uses stable `data-testid` values.
- PASS: The change adds no destructive Mist operation.
- PASS: The code removes credential fields before display or export.

## Project Structure

### Documentation

```text
specs/2443-tier3-capture-output/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── capture-output.md
└── tasks.md
```

### Source Code

```text
src/upgrade_portal/
├── app/assets/templates/capture/capture.html
├── app/routes/capture.py
└── capture/
    ├── export.py
    └── tables.py

tests/
├── unit/upgrade_portal/test_capture_export.py
├── unit/upgrade_portal/test_capture_table_cap.py
└── e2e/upgrade_portal/
    ├── conftest.py
    └── test_capture.py
```

**Structure Decision**: Extend the existing capture page, table builders, and export writer. Do not change the collector or storage schema.

## Design

1. Define stable kinds for every client and Tier 3 group.
2. Build one export row for each stored section record.
3. Put the complete safe source record in `details_json`.
4. Build generic table descriptions from fixed section definitions.
5. Render every requested section with a fixed heading and dynamic safe columns.
6. Use the existing cap for every new table.
7. Add Tier 3 stand-in rows to the E2E application.
8. Verify the page and both export formats in a browser.

## Complexity Tracking

No constitution violation is required.
