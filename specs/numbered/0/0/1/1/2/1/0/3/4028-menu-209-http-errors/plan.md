# Implementation Plan: Menu 209 HTTP Error Handling

**Branch**: `jmorrison-juniper-false-success-family-4028` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Spec Kit Feature**: `4028-menu-209-http-errors`

**Input**: Numeric feature specification from `specs/numbered/0/0/1/1/2/1/0/3/4028-menu-209-http-errors/spec.md`

## Summary

Change menu 209 response classification in
`src/operations/exporting/export/site_client_exporter.py`. Inspect the native
`getSiteBeacon` `status_code` before reading `response.data`. Use the same
local boolean gate shape as PR #4068. Treat 200-299 as success, treat an
absent or non-integer status as compatibility success, and treat every other
integer status as failure. Emit exactly
`! Error fetching site beacon detail: HTTP <status> from <url>`.

Keep the existing success normalization, no-data result, export filename,
primary-key strategy, menu wiring, and input flow. Keep exception-based HTTP
429 adaptive retries and first-error preservation unchanged. Extend the
focused unit tests in `tests/unit/export/test_site_client_exporter.py`. Add the
unique implementation fragment
`changelog.d/issue-4028-menu-209-http-errors.md`.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, Python standard library,
existing `SourceDependencyResolver`, `DataExporter`, and `pytest`

**Storage**: Existing CSV, SQLite, or ArangoDB and Redis export backends.
The change adds no storage schema.

**Testing**: Focused `pytest` unit regressions, existing menu 209 integration
tests, Python compilation, Ruff, Black, Mypy, and repository guardrails

**Target Platform**: Windows 11, macOS, and Linux

**Project Type**: Python command-line network operations tool

**Performance Goals**: Add a constant-time status check. Add no API
call, retry, or export overhead.

**Constraints**: Keep the change surgical. Validate `status_code` before
reading `response.data`. Accept only integer status values from 200 through
299. Treat every other integer status as failure. Continue for absent or
non-integer status values. Do not inspect or log the response body or
`data["detail"]`. Do not retry native HTTP 429 responses. Preserve
exception-based 429 retries. Do not edit `simple_endpoint_exporter.py`. Do
not change production code or tests during this planning phase.

**Scale/Scope**: One production method area, one existing unit test class, one
unique changelog fragment, and the managed planning artifacts

## Constitution Check

*GATE: Pass before Phase 0 research and after Phase 1 design.*

- **Five-Item Rule**: PASS WITH REMEDIATION. `SiteClientExporter` has a
  pre-existing method-count violation. The repair adds no method to that class.
  Focused fetch and output types hold five methods each. Each touched method has
  no more than 25 lines.
- **Class-Based Architecture**: PASS. Focused private types own response
  classification, retries, and output. The public menu facade remains stable.
- **Safety-First**: PASS. The existing `safe_input` flow remains unchanged.
  Failure text includes only the HTTP status and response URL. It does not
  include the response body, credentials, or request authorization data.
- **Full Deployment Pipeline**: DEFERRED TO IMPLEMENTATION. This command
  produces planning artifacts only. The implementation plan names the local
  validation commands and does not commit, push, or deploy.
- **Observability and Logging**: PASS. The existing caller logs the raised
  exception failures. The local HTTP gate emits the exact classifier line.
- **Inline Comments**: PASS FOR DESIGN. Each changed executable line must keep
  the repository inline-comment standard during implementation.
- **Action Logging**: PASS. The existing pre-call, success, exception, export,
  and retry logs remain. The design does not add an unlogged external action.
- **Managed specification route**: PASS. The record uses
  `specs/numbered/0/0/1/1/2/1/0/3/4028-menu-209-http-errors/`.
- **Process-folder exception**: PASS. The implementation adds only
  `changelog.d/issue-4028-menu-209-http-errors.md`. Existing direct-child debt
  remains outside this feature. The repository baseline work owns incremental
  remediation.
- **Product outputs**: PASS. Successful exports continue through
  `DataExporter`, which keeps product outputs under `data/`.
- **Mist Cloud SDK**: PASS. The design keeps
  `mistapi.api.v1.sites.beacons.getSiteBeacon`. It adds no direct HTTP
  transport.
- **Mist Cloud contract coverage**: PASS. The focused tests will prove HTTP
  404 and HTTP 500 failure, native HTTP 429 failure, successful dictionary
  export, successful empty handling, absent and non-integer compatibility,
  no body access, no exporter call on HTTP failure, and exception-based 429
  retry preservation.
- **Gate result before research**: PASS. No violation needs a complexity
  exception.

## Project Structure

### Documentation for this feature

```text
specs/numbered/0/0/1/1/2/1/0/3/4028-menu-209-http-errors/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── menu-209-response-classification.md
```

`tasks.md` is not part of this planning command and must not be created.

### Planned implementation paths

```text
src/operations/exporting/export/
└── site_client_exporter.py

tests/unit/export/
└── test_site_client_exporter.py

tests/integration/
└── test_menu_site_beacon_detail.py

src/foundation/support/refactors/
└── endpoint_primary_key_strategies.py

changelog.d/
└── issue-4028-menu-209-http-errors.md
```

**Structure Decision**: Keep the response classification in the existing
`SiteClientExporter` class. Extend the existing focused unit test class. Use
the integration test and primary-key file as unchanged regression evidence.

## Phase 0: Research

Research decisions are in [research.md](research.md).

The research resolves these design questions:

1. Which native response field is authoritative?
2. When can the implementation read `response.data`?
3. Which response fields can the failure gate read and log?
4. How must native HTTP 429 differ from an exception that contains `429`?
5. Which successful and compatibility paths must remain unchanged?

All research questions have a selected design.

## Phase 1: Design and Contracts

### Response classification

1. Call `mistapi.api.v1.sites.beacons.getSiteBeacon` through the existing SDK
   path.
2. Read `response.status_code` before any read of `response.data`.
3. If the status is absent or is not an integer, return `False` from the local
   gate and continue through the current payload path.
4. If the status is an integer from 200 through 299, return `False` and
   continue through the current payload path.
5. For every other integer status, read only `response.url`, with the
   canonical fallback when the URL is absent.
6. Log the failure without the response body.
7. Emit exactly
   `! Error fetching site beacon detail: HTTP <status> from <url>`.
8. Return `True` from the local gate and stop before payload access,
   normalization, filename creation, and `DataExporter`.

The detailed behavior contract is in
[contracts/menu-209-response-classification.md](contracts/menu-209-response-classification.md).

### Retry preservation

Keep the `except RuntimeError` logic unchanged. A `RuntimeError` from the SDK
that contains `429` continues through the adaptive delay and bounded retry
path. The local boolean gate does not raise. A native response with status
429 fails without entering the exception retry path.

The first-error rule remains unchanged. If a later non-429 exception follows a
429 retry exception, the helper raises the first exception.

### Failure message boundary

Read only `status_code` and `url` during classification. Do not access,
normalize, format, or log `response.data` or `data["detail"]`. The 404 body
shape is irrelevant.

### Focused regression design

Extend `TestGetSiteBeacon` in
`tests/unit/export/test_site_client_exporter.py` with these cases:

1. Native HTTP 404 emits the exact classifier line, performs no retry, and
   calls no exporter.
2. Native HTTP 500 with any body performs no normalization and calls no
   exporter.
3. Native HTTP 429 performs no adaptive retry and calls no exporter.
4. HTTP 200 with a beacon dictionary keeps one existing exporter call,
   filename, and API function name.
5. HTTP 200 with empty data keeps the successful no-data path.
6. A response with an absent status keeps current payload handling.
7. A response with a non-integer status keeps current payload handling.
8. A body object that fails on access proves the failure gate does not read
   the body.
9. The existing exception-based 429 retry test remains unchanged and passes.
10. The existing first-error preservation test remains unchanged and passes.

Use response doubles with only `status_code` and `data`. Do not use a live
credential or network call.

### Release note design

During implementation, add
`changelog.d/issue-4028-menu-209-http-errors.md`. Use one `###` heading and
one `Fixed` bullet. State that menu 209 now rejects Mist HTTP errors before
export. End the bullet with `Issue #4028.`

Do not edit `CHANGELOG.md`.

### Post-design Constitution Check

- **Five-Item Rule**: PASS WITH REMEDIATION. The focused fetch and output
  types prevent new methods in the pre-existing oversized facade. The repair
  also shortens each touched workflow method to 25 lines or fewer.
- **Class-Based Architecture**: PASS. Private subject types own the new
  behavior, and `SiteClientExporter` keeps the stable menu entry point.
- **Safety-First**: PASS. Status validation is early. Classification does not
  inspect the response body. Export stops on failure.
- **Full Deployment Pipeline**: PASS FOR PLAN. The quickstart lists focused
  and applicable repository gates for implementation.
- **Observability and Logging**: PASS. The failure enters the existing error
  logs with a clear, bounded message.
- **Inline Comments and action logs**: PASS FOR PLAN. The implementation must
  keep both standards in the touched block.
- **Mist Cloud transport**: PASS. The SDK path remains the sole transport.
- **Output, failure, safety, and redaction tests**: PASS BY DESIGN. The
  contract and focused regression list cover each required category.
- **Post-design gate result**: PASS. No complexity tracking entry is needed.

## Complexity Tracking

| Existing violation | Repair action |
| - | - |
| `SiteClientExporter` has more than five methods. | Add no method to the facade. Put the new gate and retry flow in `_SiteBeaconFetcher`. |
| The old beacon retry and menu workflow exceeded 25 lines. | Divide the flow between `_SiteBeaconFetcher` and `_SiteBeaconExportWorkflow`. |

## Implementation Boundary

The later implementation may change only these feature-owned paths unless a
failing applicable gate proves that another path is required:

- `src/operations/exporting/export/site_client_exporter.py`
- `tests/unit/export/test_site_client_exporter.py`
- `changelog.d/issue-4028-menu-209-http-errors.md`

The implementation must not change menu registration, portal controls,
primary-key strategy, successful filenames, input prompts, or unrelated
exporters. It MUST NOT change
`src/operations/exporting/export/simple_endpoint_exporter.py` while PR #4068
is open.

## Validation Plan

Run the commands in [quickstart.md](quickstart.md) in the listed order.
Record the actual result of each command during implementation.
