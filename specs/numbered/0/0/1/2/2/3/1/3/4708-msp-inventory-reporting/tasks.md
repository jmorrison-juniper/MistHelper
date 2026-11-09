# Tasks: Accurate MSP inventory coverage

## Phase 1: Setup

- [x] T001 Confirm issue ownership and managed routing in specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/plan.md.

## Phase 2: Foundation

- [x] T002 Block DNS and sockets in tests/unit/inventory/test_org_device_inventory_msp.py.

## Phase 3: Accurate batch results

**Goal**: Report exact coverage and visible exclusion causes.

**Independent test**: Complete, missing-ID, failure, empty-result, and zero-success scenarios report exact counts.

- [x] T003 [US1] Add failing batch-count scenarios in tests/unit/inventory/test_org_device_inventory_msp.py.
- [x] T004 [US1] Repair batch counts and missing-ID output in src/mist/resources/inventory/org_device_inventory_msp.py.

## Phase 4: Partial combined reports

**Goal**: Identify partial coverage in every combined-report heading without changing exports.

**Independent test**: Two successful organizations and one failure produce three partial headings and unchanged export records.

- [x] T005 [US2] Add complete and partial combined-report assertions in tests/unit/inventory/test_org_device_inventory_msp.py.
- [x] T006 [US2] Pass coverage labels to all combined renderers in src/mist/resources/inventory/org_device_inventory_msp.py.

## Phase 5: Verification and documentation

- [x] T007 [P] Add changelog.d/issue-4708-msp-inventory-reporting.md.
- [x] T008 Run focused gates and record evidence in specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/analysis.md.

## Dependencies

T002 follows T001. T003 and T005 follow T002 and precede the source repair.
T004 follows T003. T006 follows T004 and T005.
T007 can proceed independently after T001. T008 follows T006 and T007.

## Parallel Execution

The release note can proceed independently of the tests.
Keep both stories serial because they share the reserved source and test modules.
No additional agents are necessary.

## Implementation Strategy

First prove the incorrect counts and headings with failing tests.
Then repair both stories and run the complete reserved test module.
Keep all changes local and preserve the assigned file boundary.
