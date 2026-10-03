---
description: "Bounded local tasks for the WiFi response repair."
---

# Tasks: WiFi response failures

**Input**: Design documents from `specs/3743-wifi-response-failures/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), and [design/research.md](design/research.md).

**Tests**: The user requires independent native runtime proof and direct guard controls.

## Phase 1: Setup

- [x] T001 Verify the ownership claim and exact reservations before source edits. (delivered: specs/3743-wifi-response-failures/spec.md)
- [x] T002 Read current templates and record the feature-only workflow. (delivered: specs/3743-wifi-response-failures/plan.md)

## Phase 2: Foundational

- [x] T003 Trace native status, parse, and pagination behavior. (delivered: specs/3743-wifi-response-failures/design/research.md)
- [x] T004 Preserve protected hashes and run the failing baseline. (delivered: tests/integration/export/test_wifi_clients_native_response_failures.py)

## Phase 3: User Story 1 - Report a failed response

**Goal**: Reject failed first and later pages before output.

**Independent Test**: Count final CSV, router, SQLite, SDK, and live HTTP callbacks for each failed response.

- [x] T005 [US1] Add direct guard controls. (delivered: tests/unit/export/test_wifi_clients_response_failures.py)
- [x] T006 [US1] Add native failure cases. (delivered: tests/integration/export/test_wifi_clients_native_response_failures.py)
- [x] T007 [US1] Repair per-page acceptance. (delivered: src/export/wifi_clients_exporter.py)

## Phase 4: User Story 2 - Preserve complete successful data

**Goal**: Preserve empty-data meaning and complete successful output.

**Independent Test**: Compare full CSV records, page order, site information, session joins, and writer selection.

- [x] T008 [US2] Add successful controls. (delivered: tests/integration/export/test_wifi_clients_native_response_failures.py)
- [x] T009 [US2] Verify unmodified methods and protected hashes against the private baseline. (delivered: src/export/wifi_clients_exporter.py)

## Phase 5: User Story 3 - Identify the failed request

**Goal**: Retain useful error context without body contents.

**Independent Test**: Check endpoint, site, page, status, and parse context in the existing exporter notice.

- [x] T010 [US3] Verify status, scope, and parse context in error notices. (delivered: tests/unit/export/test_wifi_clients_response_failures.py)

## Phase 6: Final Verification

- [x] T011 Add the release note. (delivered: changelog.d/issue-3743-wifi-response-failures.md)
- [x] T012 Run local gates and analyze conformance. (delivered: specs/3743-wifi-response-failures/plan.md)
- [x] T013 Prepare the offline document from the current pull request template. (delivered: .github/PULL_REQUEST_TEMPLATE.md)

## Dependencies & Execution Order

T001 and T002 precede T003.
T003 precedes T004.
T004 precedes T005 through T007.
T007 precedes the corrected controls in T008 through T010.
T011 and T012 precede T013.

## Parallel Opportunities

Independent read-only checks can run together.
Test execution and product edits remain sequential.
No additional agent or shared fixture is necessary.

## Implementation Strategy

First reproduce the failure.
Then repair page acceptance.
Verify successful behavior before the local commit.
Record public ownership and a safe local handoff only.
Keep push, pull request, Actions, merge, deployment, and release actions inactive.

## Verified Local Evidence

The private session artifacts hold the complete commands and results.
The affected run passed 280 cases with 100% exporter statement coverage.
The native run checked 77 cases, including 71 failures and six successful controls.
The direct guard scope checked 35 cases.
All sixteen status-mutation controls failed as expected.

The complete test-quality ratchet found zero new findings.
Explicit forced analysis checked both new modules without a skipped native module.
The normal dependency audit failed before auditing during the macOS `ensurepip` abort.
Separate strict hashed runtime audits passed for macOS, Linux, and Windows.
The Git-only development tool remains outside that runtime audit.
STE explicitly reports `dictionary_unavailable`, so vocabulary coverage remains partial.

The local commit and its committed changed-scope ratchet remain delivery steps.
They do not grant publication permission.
