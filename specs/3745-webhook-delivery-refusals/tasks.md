---
description: "Tasks for the local webhook delivery refusal repair"
---

# Tasks: Webhook delivery refusals

**Input**: Design documents from `specs/3745-webhook-delivery-refusals/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), and [the response contract](design/response-contract.md).

**Tests**: Unit and native integration evidence are required.

**Organization**: Each user story has its own observable acceptance contract.

## Format: `[ID] [P?] [Story] Description`

A checked task names its delivered file. Private evidence remains outside the repository.

## Phase 1: Setup

- [x] T001 Verify the exact public reservation for `src/export/org_webhook_deliveries_exporter.py`. (delivered: spec.md)
- [x] T002 Preserve original tests and protected inputs before editing `src/export/org_webhook_deliveries_exporter.py`. (delivered: plan.md)
- [x] T003 Trace the installed native SDK contract and repeat delivery and discovery controls. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T004 Define status, body, pagination, logging, and output decisions. (delivered: design/response-contract.md)
- [x] T005 Build scoped native transport and resource measurement. (delivered: tests/integration/export/test_org_webhook_native_refusals.py)

## Phase 3: User Story 1 - Distinguish a refused search (Priority: P1)

**Goal**: Prevent normal empty-result or persistence paths after a failed response.

**Independent Test**: Assert the exporter error and zero persistence for failed first and later pages.

### Tests for User Story 1

- [x] T006 [US1] Add status, body, and unreadable-response tests. (delivered: tests/unit/export/test_org_webhook_response_refusals.py)
- [x] T007 [US1] Prove native `401`, `403`, `404`, and `503` first and later refusals. (delivered: tests/integration/export/test_org_webhook_native_refusals.py)
- [x] T008 [US1] Prove native refusal failures against unchanged source and actual guard mutations. (delivered: tests/integration/export/test_org_webhook_native_refusals.py)

### Implementation for User Story 1

- [x] T009 [US1] Validate every native page. (delivered: src/export/org_webhook_deliveries_exporter.py)
- [x] T010 [US1] Report safe exporter-owned refusal context. (delivered: src/export/org_webhook_deliveries_exporter.py)

## Phase 4: User Story 2 - Retain successful output (Priority: P2)

**Goal**: Preserve records, values, metadata, filenames, pagination, and genuine empty results.

**Independent Test**: Inspect exact real CSV output from successful native controls.

### Tests for User Story 2

- [x] T011 [US2] Verify successful native list and `results` pagination. (delivered: tests/integration/export/test_org_webhook_native_refusals.py)
- [x] T012 [US2] Verify genuine empty results and standalone database warnings. (delivered: tests/integration/export/test_org_webhook_native_refusals.py)

### Implementation for User Story 2

- [x] T013 [US2] Preserve the actual persistence and output contract. (delivered: src/export/org_webhook_deliveries_exporter.py)

## Phase 5: User Story 3 - Distinguish failed discovery (Priority: P3)

**Goal**: Refuse failed discovery before the normal empty notice or selection prompt.

**Independent Test**: Exercise actual native discovery and its successful selection control.

### Tests for User Story 3

- [x] T014 [US3] Add native first and later discovery refusal cases. (delivered: tests/integration/export/test_org_webhook_native_refusals.py)
- [x] T015 [US3] Preserve successful discovery selection and the thirteen original cases. (delivered: tests/unit/export/test_org_webhook_response_refusals.py)

### Implementation for User Story 3

- [x] T016 [US3] Apply validated page collection to discovery. (delivered: src/export/org_webhook_deliveries_exporter.py)

## Phase 6: Cross-Cutting Verification

- [x] T017 Verify affected tests, precise coverage, current source gates, and original assertions. (delivered: tests/integration/export/test_org_webhook_native_refusals.py)
- [x] T018 Verify full and explicit native analyzer evidence with unchanged settings and baseline. (delivered: plan.md)
- [x] T019 Add the unique release fragment. (delivered: changelog.d/issue-3745-webhook-delivery-refusals.md)
- [x] T020 Verify the specification, plan, and task contracts. (delivered: checklists/requirements.md)

## Dependencies & Execution Order

Setup precedes foundational work. Native red proof precedes the source repair.
US1 and US3 share the validated page collector. US2 verifies the unchanged output boundary.
Final verification depends on all three user stories.
The clean local commit depends on passing current local evidence.
The committed-scope ratchet follows that commit.
The offline PR draft and coordinator receipt remain private until the safe public handoff.
Publication and deployment are not tasks in this local grant.

## Parallel Opportunities

The new unit and native test files can receive independent edits after the contract is fixed.
Independent read-only code gates can run together after the affected tests pass.
No agent receives a peer environment or an outside file reservation.

## Implementation Strategy

Implement the refusal decision first. Verify the successful controls before extending page and discovery coverage.
If an original successful fixture fails under strict validation, preserve both cases and request a narrow coordinator grant.
Do not weaken the guard or remove a test.
