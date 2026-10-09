---
description: "Implementation tasks for HTTP error handling in endpoint exporters."
---

# Tasks: Empty Export Endpoint Response Handling

**Prerequisites**: `spec.md`, `plan.md`

## Phase 1: Shared response decision

- [X] T001 Add the strict 2xx response helper with the required error wording.
- [X] T002 Add direct tests for missing, mocked, successful, and failed status values.

## Phase 2: Issue #4038

- [X] T003 Wire the helper into `EndpointFamilyExporter._run`.
- [X] T004 Add a red proof that an HTTP error body does not reach `mistapi.get_all`.

## Phase 3: Release and follow-up record

- [X] T005 Add the issue #4038 changelog fragment.
- [X] T006 Record that issue #4043 remains open for `SimpleEndpointExporter._run`.
- [ ] T007 Wire the helper into `SimpleEndpointExporter._run` in the follow-up branch.
