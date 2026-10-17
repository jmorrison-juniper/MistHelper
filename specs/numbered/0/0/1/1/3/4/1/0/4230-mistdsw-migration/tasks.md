# Tasks: MistDSW Migration

**Input**: [Specification](spec.md), [plan](plan.md), [research](research.md), and [design](design/data-model.md).
**Contracts**: [Preparation](design/contracts/preparation.md) and [payloads](design/contracts/payloads.md).

**Status**: Future implementation tasks only. All 27 tasks remain unchecked.
This planning PR does not authorize their execution.
Tests are mandatory under the repository constitution.

## Phase 1: Setup

- [ ] T001 Record B1 permission or approved independent-development evidence and B2 profile approval in `research.md`. Retain source notices if reuse becomes permitted.
- [ ] T002 Validate the proposed package capacity and portal ownership integration in `plan.md`. Resolve B3 and reserve the exact nested package before product edits.

Task document paths above are relative to this feature directory.
Product paths below are relative to the repository root.
The proposed root is `src/operations/execution/configuration/mistdsw/`.
If T002 changes it, update every task and test import before implementation.

## Phase 2: Foundational

- [ ] T003 Write shared-storage and ownership tests in `tests/integration/mistdsw/test_run_storage.py`. Cover one configured ArangoDB database, cross-session denial, outage, idempotency conflict, expiration, interrupted writes, backup readability, and recovered artifact verification.
- [ ] T004 Write input and privacy boundary tests in `tests/unit/mistdsw/test_validation.py`. Cover 5 MiB, 500 stores, duplicate keys, UTF-8 errors, secret canaries, traversal, and unsafe file replacement.
- [ ] T005 Implement validated inputs and run storage in `src/operations/execution/configuration/mistdsw/domain/validation.py`, `storage/records.py`, and `storage/artifacts.py`. Apply `design/data-model.md` constraints exactly. Reject unavailable storage instead of declaring file-only success.

T005 includes session-owner digest, UUID run keys, profile revision, UTC timestamps, and the five documented run states.
Site names must be nonblank, unique within a run, and at most 128 characters.
VLANs are unique integers from 1 through 4094.
Private files expire after 24 hours.
Use one `mistdsw_preparation_runs` collection in the existing ArangoDB database.
Do not add SQLite or Redis run storage.

## Phase 3: User Story 1 - Prepare Store Variables (P1)

**Goal**: Prepare one store or a complete validated batch.
**Independent test**: Compare two synthetic stores against exact transposed CSV values without templates or cloud credentials.

### Tests

- [ ] T006 [P] [US1] Write addressing unit tests in `tests/unit/mistdsw/test_variables.py`. Cover `/22` normalization, four `/24` offsets, explicit gateways, upper-side DHCP ties, `/27` management, `/29` WAN, invalid IPv4, and network or broadcast gateways.
- [ ] T007 [P] [US1] Write CSV contract tests in `tests/contract/mistdsw/test_variables_csv.py`. Cover 36 baseline rows, 45 optional rows, site order, exact placeholder names, empty optional cells, and formula rejection.
- [ ] T008 [P] [US1] Write CLI integration tests in `tests/integration/mistdsw/test_variables_cli.py`. Cover all TSV shapes, empty management with WAN, partial columns, duplicates, overlap, extra fields, invalid-row atomic failure, and exit codes.

### Implementation

- [ ] T009 [US1] Implement store parsing and variables in `src/operations/execution/configuration/mistdsw/domain/inputs.py` and `domain/variables.py`. Match contracts, require normalized-address acknowledgment, and preserve explicit gateways.
- [ ] T010 [US1] Add shared CLI dispatch in `src/operations/execution/configuration/mistdsw/presentation/cli.py` and wire `--prepare-mistdsw` in `MistHelper.py`. Require explicit input, profile, and managed output. Register no new menu number.
- [ ] T011 [US1] Add the owned variables preview in `src/operations/execution/configuration/mistdsw/presentation/routes.py` and `presentation/templates/mistdsw/variables.html`. Register its blueprint in `web_portal/app.py` and navigation in `web_portal/templates/base.html`.
- [ ] T012 [US1] Write browser and Flask tests in `tests/e2e/web_portal/mistdsw/test_variables_flow.py`. Cover correction, acknowledgment, keyboard access, stable selectors, private download, and retained failure traces.

## Phase 4: User Story 2 - Prepare Configuration Templates (P2)

**Goal**: Review switch or gateway transformation independently of store generation.
**Independent test**: Transform synthetic exports and compare only approved differences.

### Tests

- [ ] T013 [P] [US2] Write template unit tests in `tests/unit/mistdsw/test_templates.py`. Cover four-network replacement, unrelated settings, missing networks, invalid sections, multiple LAN ports, mixed tenants, and secret removal.
- [ ] T014 [P] [US2] Write template contract tests in `tests/contract/mistdsw/test_templates.py`. Cover ten IP entries, ten DHCP entries, wrapper objects, integer versus placeholder prefixes, metadata removals, and profile consistency.
- [ ] T015 [P] [US2] Write transform integration tests in `tests/integration/mistdsw/test_template_cli.py`. Cover explicit input, review acknowledgments, atomic export, backup verification, EOF, interruption, and unreadable files.

### Implementation

- [ ] T016 [US2] Implement switch and gateway transformation classes in `src/operations/execution/configuration/mistdsw/domain/templates.py`. Preserve nonsecret fields, selected ports, and unrelated tenants. Require approved policy mappings.
- [ ] T017 [US2] Extend the shared routes and CLI in `src/operations/execution/configuration/mistdsw/presentation/routes.py` and `presentation/cli.py`. Add `presentation/templates/mistdsw/templates.html` for differences, LAN selection, and downloads.
- [ ] T018 [US2] Write browser and Flask tests in `tests/e2e/web_portal/mistdsw/test_template_flow.py`. Cover switch and gateway previews, ambiguous LAN selection, private export rejection, metadata review, and failed downloads.

## Phase 5: User Story 3 - Prepare Network and Service Payloads (P2)

**Goal**: Generate a complete approved bundle without template or store inputs.
**Independent test**: Validate ten networks and four services against a synthetic profile.

### Tests

- [ ] T019 [P] [US3] Write profile and bundle unit tests in `tests/unit/mistdsw/test_bundles.py`. Cover Guest and Realo conflicts, all names, VLAN bounds, DHCP agreement, unknown placeholders, and explicit access-policy values.
- [ ] T020 [P] [US3] Write bundle contract tests in `tests/contract/mistdsw/test_bundles.py`. Cover 16 network and service files, combined arrays, JSON value types, four service references, and B4 local schema evidence.
- [ ] T021 [P] [US3] Write offline bundle integration tests in `tests/integration/mistdsw/test_bundle_cli.py`. Cover deterministic digests, zero cloud calls, zero source organization defaults, and partial-write failure.

### Implementation

- [ ] T022 [US3] Implement bundle generation in `src/operations/execution/configuration/mistdsw/domain/bundles.py`. Require the approved profile and produce exactly the contract shapes without copied source assets.
- [ ] T023 [US3] Extend shared CLI and routes in `src/operations/execution/configuration/mistdsw/presentation/cli.py` and `presentation/routes.py`. Add `presentation/templates/mistdsw/bundles.html` and `tests/e2e/web_portal/mistdsw/test_bundle_flow.py` for reviewed downloads and manual-deployment warnings.

## Phase 6: Cross-Cutting Validation and Documentation

- [ ] T024 Write recovery and performance tests in `tests/integration/mistdsw/test_failure_safety.py`. Measure 500 stores within five seconds on the reference host. Cover two concurrent sessions, expiration cleanup, canaries, denied downloads, and storage outage.
- [ ] T025 Document the approved workflow in `documentation/mistdsw-preparation.md` and link it from `README.md`. Add one `changelog.d/issue-4230-mistdsw-preparation.md` fragment. Document every intentional source difference.
- [ ] T026 Run the exact applicable gate commands in `design/quickstart.md`. Record measured counts, failures, fixes, and command output in the implementation PR. Do not change test-quality baselines.
- [ ] T027 Record B1-B4 release evidence in `design/analysis.md`. Obtain human approval for release. Do not add automatic deployment or close an approval condition without proof.

## Dependencies & Execution Order

| Tasks | Prerequisites |
| --- | --- |
| T001, T002 | Explicit future implementation authorization. |
| T003, T004 | T001 and T002. These tests use different files. |
| T005 | T003 and T004 must fail for the intended missing behavior first. |
| T006-T008 | T005. Test files are independent. |
| T009 | T006-T008. |
| T010, T011 | T009. They share presentation ownership and run serially. |
| T012 | T010 and T011. |
| T013-T015 | T005. Test files are independent. |
| T016 | T013-T015. |
| T017 | T016 and the shared presentation from T010-T011. |
| T018 | T017. |
| T019-T021 | T005. Test files are independent. |
| T022 | T019-T021. |
| T023 | T022 and the shared presentation from T010-T011. |
| T024 | T012, T018, and T023. |
| T025 | All user stories. |
| T026 | T024 and T025. |
| T027 | T026 and proof for B1-B4. |

Run story implementations in order US1, US2, US3 to avoid shared presentation conflicts.
Each story remains independently testable after foundation completion.
Do not reserve shared hot files while a different PR owns them.

## Parallel Examples

US1: T006, T007, and T008 can run together after T005.
US2: T013, T014, and T015 can run together after T005.
US3: T019, T020, and T021 can run together after T005.
Do not run agents against the same routes, CLI, menu, or base-template files.

## Implementation Strategy

After explicit authorization and setup approvals, deliver US1 as the first useful increment.
Validate its CSV contract before adding templates.
Add US2, then US3, without introducing separate services.
Use the nine source regression scenarios as behavioral evidence, not copied tests.
This document is a future execution plan. Stop after the current planning PR.

## Requirement Coverage

| Requirements | Tasks |
| --- | --- |
| FR-001 | T009, T016, T022 |
| FR-002 | T006, T008, T009 |
| FR-003, FR-004 | T006, T009 |
| FR-005 | T007, T009 |
| FR-006, FR-007 | T013-T018 |
| FR-008, FR-009 | T014, T019-T023 |
| FR-010 | T001, T019, T022 |
| FR-011, FR-012 | T010-T012, T017-T018, T023 |
| FR-013 | T003, T005, T024 |
| FR-014, FR-015 | T003-T005, T012, T018, T024 |
| FR-016 | T021, T023, T025 |
| FR-017 | T001, T027 |
| FR-018 | Current planning validation in `design/analysis.md`, then T026. |
| SC-001, SC-002 | T006-T008, T013-T015, T019-T021 |
| SC-003 | T024 |
| SC-004, SC-005 | T004, T012, T018, T024 |
| SC-006, SC-007 | T003, T021, T024 |
| SC-008 | Current cross-artifact analysis, then T027. |
