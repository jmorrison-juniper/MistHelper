# Tasks: WAN Probe Response Status

**Input**: `spec.md`, `plan.md`, and the supporting files under `design/`.

## Phase 1: User Story 1 - Reject a refused device configuration (P1)

**Goal**: Reject an HTTP 403 device configuration response before the operation uses its parsed body.

**Independent Test**: A native SDK response with HTTP 403 and plausible port settings yields a failed result and no update request. A valid HTTP 200 response remains accepted.

- [x] T001 [US1] Add mocked native HTTP 403 and HTTP 200 configuration-response tests in `tests/unit/gateway/test_wan_probe_device_override_manager.py`. (delivered: `tests/unit/gateway/test_wan_probe_device_override_manager.py`)
- [x] T002 [US1] Reject non-200 configuration responses in `src/mist/resources/gateway/wan_probe_device_override_manager.py`. (delivered: `src/mist/resources/gateway/wan_probe_device_override_manager.py`)
- [x] T003 [US1] Set successful status on the mocked configuration response in `tests/unit/gateway/test_wan_probe_override_pipeline.py`. (delivered: `tests/unit/gateway/test_wan_probe_override_pipeline.py`)
- [x] T004 [US1] Run the focused WAN probe unit and refactor tests in `tests/unit/gateway/` and `tests/unit/refactors/`. (verified: 53 tests passed)
- [x] T005 [US1] Add the issue release note in `changelog.d/issue-4381-wan-probe-response-status.md`. (delivered: `changelog.d/issue-4381-wan-probe-response-status.md`)

## Dependencies and Execution Order

- T001 precedes T002 because the test must prove the defect before the status guard exists.
- T002 and T003 precede T004 because the full mocked test set requires the guard and explicit success statuses.
- T004 precedes T005 completion evidence and pull request creation.

## Implementation Strategy

Complete User Story 1 as one independently tested change. Do not call Mist Cloud or modify a production device.
