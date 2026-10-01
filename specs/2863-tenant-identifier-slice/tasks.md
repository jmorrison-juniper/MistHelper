# Tasks: Tenant identifier validation

**Input**: [spec.md](spec.md), [plan.md](plan.md), and [research.md](research.md).

## Phase 1: Setup

- [x] T001 Reserve the exact slice in issue #2863 before source edits.
  (delivered: research.md)
- [x] T002 Define the scope and contracts with current SpecKit templates.
  (delivered: spec.md, plan.md, research.md)
- [x] T003 Restore the isolated environment from the current manifests.
  (delivered: quickstart.md)

## Phase 2: Required-Input Refusal

**Goal**: Invalid scope inputs produce a named refusal before the SDK.

**Independent Test**: Assert exact error text, one refusal, and zero SDK calls.

- [x] T004 [US1] Add real public SDK-boundary regression tests in
  tests/unit/api/test_tenant_identifier_validation.py. Run them before the fix.
  Covers FR-001, FR-002, FR-004, FR-005, FR-006, and SC-001.
  (delivered: tests/unit/api/test_tenant_identifier_validation.py)
- [x] T005 [US1] Add the shared semantic validator and complete its call-site
  migration in src/api/tenant_fetch.py.
  Covers FR-001, FR-002, FR-004, FR-005, and FR-006.
  (delivered: src/api/tenant_fetch.py)
- [x] T006 [US1] Prove private metadata stays out of refusals and logs in
  tests/unit/api/test_tenant_identifier_validation.py.
  Covers FR-006 and SC-002.
  (delivered: tests/unit/api/test_tenant_identifier_validation.py)
- [x] T007 [US1] Prove service-ping discovery propagates the refusal before
  empty-source storage in tests/unit/api/test_tenant_identifier_validation.py.
  Covers FR-011.
  (delivered: tests/unit/api/test_tenant_identifier_validation.py)

## Phase 3: Existing-Behavior Preservation

**Goal**: Valid and optional-scope calls retain their current behavior.

**Independent Test**: Assert exact SDK calls and exact tenant results.

- [x] T008 [US2] Prove organization-only `None`, combined scope, opaque
  identifiers, valid empty responses, sorting, and unknown records in
  tests/unit/api/test_tenant_identifier_validation.py.
  Covers FR-003, FR-007, FR-008, SC-003, and SC-004.
  (delivered: tests/unit/api/test_tenant_identifier_validation.py)
- [x] T009 [US2] Prove resolver exceptions, HTTP 4xx, HTTP 5xx, and parse
  failures retain their contracts in
  tests/unit/api/test_tenant_identifier_validation.py.
  Covers FR-009 and FR-010.
  (delivered: tests/unit/api/test_tenant_identifier_validation.py)
- [x] T010 [US2] Run the unchanged tenant, response-integrity, and discovery
  suites. Record exact results in quickstart.md.
  Covers FR-008, FR-009, FR-010, and SC-006.
  (delivered: quickstart.md)

## Phase 4: Local Delivery

- [x] T011 Measure changed-method coverage and run all applicable local gates.
  Record exact commands, results, and limitations in quickstart.md.
  Covers SC-005.
  (delivered: quickstart.md)
- [x] T012 Add the user-visible refusal note in
  changelog.d/issue-2863-tenant-identifier-validation.md.
  (delivered: changelog.d/issue-2863-tenant-identifier-validation.md)
- [x] T013 Analyze spec.md, plan.md, and tasks.md for complete requirement
  coverage and bounded scope.
  (delivered: spec.md)
- [x] T014 Verify the exact local delivery manifest and the open audit state.
  Record the manifest in plan.md. Covers FR-012.
  (delivered: plan.md)

## Dependencies & Execution Order

T001 and T002 precede all source work.
T003 precedes T004. The red result precedes T005.
T006 through T010 verify T005.
T011 follows the behavior proofs.
T012 and T013 precede the final local commit.
T014 follows every local gate.

The local commit follows the verified manifest.
The parent handoff records its exact clean SHA and required author trailer.
No publication task can start before the parent's explicit verified-main grant.
The broader audit stays open after this local slice.
