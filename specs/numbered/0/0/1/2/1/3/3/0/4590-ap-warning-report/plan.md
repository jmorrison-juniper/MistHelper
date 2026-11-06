# Implementation Plan: AP warning report

**Branch**: `jmorrison-juniper-ap-warning-report` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

Build an isolated report package before menu integration.
Join AP inventory with site names and documented AP trouble statistics.
Read the LED dictionary once and retain unknown codes.
Register menu 307 and preserve the separate WAN documentation change in pull request #4208.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing mistapi SDK and standard library.

**Storage**: Existing DataExporter backends. No new storage system.

**Testing**: Pytest with mocked SDK responses and real CSV and SQLite writer integration.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Existing menu application.

**Performance Goals**: One paginated request sequence per source, with dictionary retrieval once per run.

**Constraints**: Read-only SDK requests, no new dependencies, and no credentials in output.

**Scale/Scope**: One selected organization, all its sites and AP inventory.

## Constitution Check

- The new package adds the fourth child to `src/operations/exporting`, which currently has three.
- Each new source package has at most five children.
- Methods use at most five parameters and remain small.
- Existing oversized report and export packages remain unchanged.
- Existing process-folder debt remains outside this feature.
  Separate remediation must migrate existing records without changing this feature.
- Product writes use DataExporter under `data/`.
- All cloud reads use supported SDK methods and the existing authenticated session.
- SDK pagination validates every page rather than accepting a partial `get_all` result.
- Tests cover endpoint arguments, malformed data, failed pages, unknown codes, and output failure.
- Commit messages use Conventional Commits.
- No custom transport or WebSocket exception is necessary.
- App-managed branch creation replaces the branch hook.
- No shared feature pointer changes.

**Post-design decision**: Pass for isolated implementation.
The coordination check found separate README sections and no active competing agent.
The user requests progress, so menu integration no longer depends on the WAN feature merge.

## Project Structure

### Documentation

The managed feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains research, data model, quickstart, contracts, and checklists.

### Source Code

```text
src/operations/exporting/ap_warning_report/
  __init__.py
  client.py
  codes.py
  rows.py
  operation.py
tests/unit/ap_warning_report/
  test_codes.py
  test_rows.py
  test_client.py
  test_operation.py
tests/integration/ap_warning_report/
  test_export.py
  test_sqlite.py
```

**Structure Decision**: Use a new compliant package rather than extending an oversized existing package.

## Complexity Tracking

No new structural exception is required for source files.
The existing test trees and unique changelog process records retain their established layout.
The primary-key registry receives one independent strategy entry.
This adds no module-level names and changes no existing strategy.
The follow-up integration must not rename modules or change existing menu behavior.
