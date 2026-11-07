# Implementation Plan: WiFi Pagination Failure Handling

**Branch**: `jmorrison-juniper-potential-disco` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/1/1/1/4656-wifi-pagination/spec.md`.

## Summary

Retain successful WiFi pages after a later transport timeout and report the result as partial. Reject later HTTP error pages before exporting output. Keep complete pagination and first-page behavior unchanged.

The SDK `mistapi.get_all` cannot satisfy these rules. Its accumulator is local and is lost when `get_next` raises. It also appends later response data without checking the HTTP status. Follow pages with the SDK `mistapi.get_next`, check each response, and keep the rows already collected.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi` 0.64.x, already installed by the locked project environment.

**Storage**: Existing configured export backend and the existing no-data placeholder CSV.

**Testing**: `pytest` with mocked endpoint calls and controlled native SDK responses and sessions.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Python command-line application.

**Performance Goals**: Request pages in sequence and preserve the configured page limit of 1000.

**Constraints**: Use only `searchSiteWirelessClients`, `searchSiteWirelessClientSessions`, and SDK pagination. Make no live Mist calls in tests. Preserve first-page checks and valid-empty output.

**Scale/Scope**: One existing exporter, its existing unit and integration test modules, one release-note fragment, and this feature record.

## Constitution Check

*GATE: Passed before research. Re-check after design.*

- The managed issue route was resolved by `create-new-feature.ps1 -Json -DryRun -Number 4656`. The process-folder guard passed 11 tests.
- The new record adds no direct child outside a managed `specs/` root. Existing process-folder debt remains under the tracked baseline. This change does not restructure unrelated folders. Track any baseline reduction in a separate change.
- `.specify/feature.json` is owned by open PR #4654 and remains unchanged.
- The product export continues to use the configured exporter. It does not write outside `data/`.
- The existing endpoint methods preserve Mist SDK authentication and endpoint contracts. Controlled native responses test complete results, partial timeout results, failed later pages, first-page errors, and empty results. Tests make no live requests and do not log secrets.
- The work changes no production data and requires no destructive operation.
- The commit subject will use a Conventional Commit form accepted by the title guard.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/2/1/1/1/4656-wifi-pagination/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── checklists/requirements.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── contracts/wifi-pagination.md
```

### Source Code

```text
src/operations/exporting/export/wifi_clients_exporter.py
tests/unit/export/test_wifi_clients_response_failures.py
tests/integration/export/test_wifi_clients_native_response_failures.py
changelog.d/issue-4656-wifi-pagination.md
```

**Structure Decision**: Extend the existing WiFi exporter and its established unit and integration tests. Add no new production module or test directory.

## Phase 0: Research

See [research.md](design/research.md). It records the SDK behavior, the existing controlled-response fixtures, and the pagination decisions.

## Phase 1: Design

See [data-model.md](design/data-model.md), [contracts/wifi-pagination.md](design/contracts/wifi-pagination.md), and [quickstart.md](design/quickstart.md).

## Constitution Check After Design

- The feature remains inside the managed eight-level numeric route and adds no direct child to `specs/`.
- The source and test changes stay in existing files and packages.
- The implementation uses SDK page requests, retains successful rows only on later transport failure, and rejects later HTTP error responses.
- Test coverage will include complete results, timeout partial results, failed later HTTP responses, first-page failures, and valid empty results.
- No shared feature pointer, live cloud request, production export, or destructive operation is part of the change.

## Complexity Tracking

No constitution limit requires an exception. Keep each new helper within the existing function-size and complexity limits.
