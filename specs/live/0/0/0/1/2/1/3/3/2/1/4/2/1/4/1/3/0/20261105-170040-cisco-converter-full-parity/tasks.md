# Tasks: Cisco Converter Full Observed Parity

**Input**: [Specification](spec.md), [plan](plan.md), and supporting artifacts under `design/`.

**Prerequisites**: This workflow authorizes documentation only. Each task below describes later work and remains unchecked.

**Tests**: Unit, contract, integration, edge-case, and browser tests are mandatory.
Use original synthetic fixtures and simulated SDK responses.
Do not copy source tests or use live credentials.

**Organization**: Tasks follow the five user stories. The dependency table controls execution, not document order.

## Format and File Ownership

Each task has a unique ID, explicit paths, and dependencies.
Do not mark a task complete until its evidence exists and its gates pass.
Add `(delivered: path)` only after verification.
An approval task needs a recorded owner decision, not an agent assumption.
All paths below are proposed future work.
No application file is part of this documentation assignment.

Shared portal paths require integration-owner handover.
Task T004 must resolve package capacity before adding new source children.
If a proposed path conflicts with ownership or structure, revise this record before implementation.

## Phase 1: Setup

- [ ] T001 Obtain implementation authorization and integration-owner handover. Record approved file ownership and G3/G4 scope in `design/research.md`. Do not access another dirty worktree.
- [ ] T002 Obtain G1 legal review and record independent-authorship and distribution decisions in `design/research.md`. No source expression reuse is approved.
- [ ] T003 Verify every mapping's OpenAPI path, schema pointer, installed signature, and positive/negative fixture. Record G2 evidence in `design/contracts/mist.md`.
- [ ] T004 Inventory converter package capacity and touched structure debt. Define bounded replacement paths and all import updates in `plan.md`. No compatibility shims or unrelated restructuring.

## Phase 2: Foundational

- [ ] T005 Reproduce the current DNS unit, route, and isolated browser baseline. Record exact results in `analysis.md` and protect current preview/review/export contracts.
- [ ] T006 Define private source, review, proposal, approval, operation, and backup types in `src/interfaces/portals/cisco_config_converter/models.py`. Test digest, ownership, redaction, expiry, and transitions in `tests/contract/cisco_config_converter/test_state.py`. Obtain owner-approved identity and authorization design before any cloud write. Test stable session secrets, restart, and multiworker behavior. Use a 15-minute review lifetime until the owner approves another value.

## Phase 3: US1 - Select and Inspect Input (P1)

**Goal**: Stored or uploaded input reaches structured review without conversion or cloud access.

**Independent Test**: Use valid, malformed, and adversarial files with external requests blocked.

- [ ] T007 [US1] Add input contract tests in `tests/contract/cisco_config_converter/test_input.py`. Cover six suffixes, exact 16 MiB, one extra byte, UTF-8, null bytes, traversal, drive paths, symlinks, upload collisions, and failed-review invalidation.
- [ ] T008 [US1] Add contained catalog, private prepopulation, and validated upload/select behavior in `src/interfaces/portals/cisco_config_converter/routes.py` and `models.py`. Use opaque IDs, transient default storage, and no silent overwrite. Cover C01-C02 and C37.
- [ ] T009 [US1] Add original parser review tests in `tests/contract/cisco_config_converter/test_parser.py`. Cover C03, C07-C17, banners, masks, duplicate directives, unknown syntax, redacted identity data, and no cloud calls.
- [ ] T010 [US1] Add independent sectioned display-only review through `src/interfaces/portals/cisco_config_converter/routes.py` and `presentation/converter.html`. Show every observed family and distinguish unsupported conversion from parsed observations.

**Checkpoint**: US1 passes without Mist credentials and without converting an uncertain setting.

## Phase 4: US2 - Hardware and Proposal Review (P1)

**Goal**: The engineer verifies role, family, model, mappings, and the exact proposal before export.

**Independent Test**: Exercise six role/family combinations, unknown models, and ambiguous ports.

- [ ] T011 [US2] Add role/model contract tests in `tests/contract/cisco_config_converter/test_hardware.py`. Cover Branch/Hub/Standalone, SRX/SSR, inventory evidence, unsupported models, duplicate ports, stale models, and changed-selection invalidation.
- [ ] T012 [US2] Add explicit role, family, model, and port selection in `src/interfaces/portals/cisco_config_converter/presentation/converter.html` and `converter.js`. Implement verified mappings in `conversion.py`. Unknown models and conflicting assignments block apply.
- [ ] T013 [US2] Add independent conversion tests in `tests/contract/cisco_config_converter/test_conversion.py`. Cover C08-C12, WAN/LAN ambiguity, addressing, VLAN/aggregation, DHCP exclusions, routes, BGP, VRF, DNS, NTP, and variables.
- [ ] T014 [US2] Implement verified network and routing transformations in `src/interfaces/portals/cisco_config_converter/conversion.py`. Preserve the existing DNS behavior. Omit uncertain fields with explicit reasons rather than inventing output.
- [ ] T015 [US2] Add management/security family tests in `tests/contract/cisco_config_converter/test_management.py`. Cover C13-C17, secret redaction, one-way hashes, syslog placement, parser-only families, and prohibited raw-command generation.
- [ ] T016 [US2] Implement contract-verified management mappings and explicit display-only limits in `src/interfaces/portals/cisco_config_converter/conversion.py`. Never reconstruct hashes or expose decoded secrets.
- [ ] T017 [US2] Add proposal and export tests in `tests/integration/web_portal/cisco_config_converter/test_proposals.py`. Verify object changes, omissions, unavailable checks, version shape, altered scope, exact reviewed export, and zero secrets.
- [ ] T018 [US2] Add structured proposal review and versioned full-parity operations in `src/interfaces/portals/cisco_config_converter/routes.py` and `presentation/converter.js`. Preserve current clients and invalidate review after every source, model, target, or proposal change.

**Checkpoint**: US2 completes offline. Unsupported families remain visible and do not produce fabricated settings.

## Phase 5: US3 - Controlled Cloud Apply (P1)

**Goal**: Discovery and apply use verified contracts, exact scope, fresh permission, and recovery evidence.

**Independent Test**: Simulate all cloud responses. Assert zero writes on every refused approval.

- [ ] T019 [US3] Add discovery tests in `tests/contract/cisco_config_converter/test_discovery.py`. Cover C19-C21, all pages, unavailable/denied/failed states, duplicate site names, assigned/unassigned gateways, and organization membership.
- [ ] T020 [US3] Add read-only status/site/gateway discovery in `src/interfaces/portals/cisco_config_converter/routes.py`. Use the existing credential/session service and explicit SDK arguments. Never create a site during lookup or preview.
- [ ] T021 [US3] Add apply tests in `tests/contract/cisco_config_converter/test_apply.py`. Cover C22-C24, exact APPLY, permission, expiry, changed scope, incomplete backup, duplicate submission, locks, stale state, 4xx/5xx/429, timeout, partial results, and indeterminate writes.
- [ ] T022 [US3] Implement approved apply and result reconciliation through `src/interfaces/portals/cisco_config_converter/routes.py` and `models.py`. Preserve unrelated object fields. G2, G4, and per-operation G5 must pass. Never automatically retry an unknown write.

**Checkpoint**: US3 passes simulated execution and refusal tests.
Live apply remains prohibited without separate owner approval and current operator confirmation.

## Phase 6: US4 - Administration and Recovery (P2)

**Goal**: Scoped backup, restore, delete, unassign, and recovery preserve unrelated state.

**Independent Test**: Simulate each object family, damaged backups, naming conflicts, and partial recovery.

- [ ] T023 [US4] Add backup/catalog tests in `tests/contract/cisco_config_converter/test_backup.py`. Cover C26-C27, complete pagination, private storage, UTC manifests, checksums, relationships, wrong organization, wrong family, and symlink escapes. Prove new private paths cannot enter browser listings, previews, downloads, output scans, or logs.
- [ ] T024 [US4] Implement private policy/service/network backup and catalog behavior in `src/interfaces/portals/cisco_config_converter/routes.py` and `models.py`. A missing page or invalid manifest blocks recovery and destructive execution.
- [ ] T025 [US4] Add administrative permission and refusal tests in `tests/contract/cisco_config_converter/test_administration.py`. Cover C25 and C29-C30, disabled mode, exact scope, two confirmations, exact CONFIRM, changed references, backup failure, and zero refused writes.
- [ ] T026 [US4] Implement approved scoped service/network/template deletion and site-template/device-profile unassignment in `src/interfaces/portals/cisco_config_converter/routes.py`. G2, G4, and G5 must pass. Record every object outcome.
- [ ] T027 [US4] Add restore/recovery tests in `tests/contract/cisco_config_converter/test_recovery.py`. Cover C28 and C31, update/create decisions, duplicate names, partial apply, unknown outcomes, unrelated changes, expired approval, and failed rollback.
- [ ] T028 [US4] Implement reviewed restore and recovery through `src/interfaces/portals/cisco_config_converter/routes.py` and `models.py`. Use recorded natural IDs and fresh approval. Never delete an object merely because a backup omits it.

**Checkpoint**: Each administrative action passes independent refusal and recovery tests.
No bulk production operation is approved by this task list.

## Phase 7: US5 - Integrated Visual Journey (P2)

**Goal**: The real portal exposes independent selection, review, proposal, confirmation, administration, and status views.

**Independent Test**: Exercise each visual journey with keyboard input in four theme intentions at desktop and narrow widths.

- [ ] T029 [US5] Add real-portal browser tests in `tests/e2e/web_portal/test_cisco_parity.py`. Cover C32-C35, centered card, structured review, proposal, typed confirmation, cancel/reset, all states, themes, focus, safe text rendering, and failure traces.
- [ ] T030 [US5] Independently author converter presentation in `src/interfaces/portals/cisco_config_converter/presentation/converter.html` and `converter.js`. Reuse host theme services. Do not copy source templates, styles, screenshots, prose, or animation.

**Checkpoint**: The owner reviews the independently authored visual journeys.
The isolated DNS page alone is insufficient evidence.

## Phase 8: Cross-Cutting Acceptance

- [ ] T031 Add full-parity integration, failure, and privacy tests in `tests/integration/web_portal/cisco_config_converter/test_parity.py`. Cover C36-C39, unchanged health/services, CSRF and converter-prefix content negotiation, safe responses, debug defaults, logs, no live requests, and every comparison row.
- [ ] T032 After G3 handover, integrate the feature through `web_portal/app.py` and `web_portal/templates/base.html`. Run the real-portal browser and existing regression suites. Preserve shared request handling, health, credentials, and service ownership.
- [ ] T033 Refresh `design/research.md` and `analysis.md` with row-level evidence and owner/legal/API decisions. Add an independently written converter guide only after documentation ownership approval. Full parity needs all rows accepted or an owner-approved unsupported disposition.

## Dependencies and Execution Order

Each row lists actual prerequisites.
Test tasks precede their implementation tasks.
G2 may complete by verified family, but a family implementation cannot start before that family's T003 evidence exists.
G4 authorization and G5 runtime confirmation cannot be inferred from G2.

| Task | Prerequisites |
| --- | --- |
| T001 | None |
| T002 | None |
| T003 | None |
| T004 | T001 |
| T005 | None |
| T006 | T001, T004, T005 |
| T007 | T006 |
| T008 | T007 |
| T009 | T006 |
| T010 | T008, T009 |
| T011 | T003, T006 |
| T012 | T010, T011 |
| T013 | T003, T006 |
| T014 | T012, T013 |
| T015 | T003, T006 |
| T016 | T012, T015 |
| T017 | T006 |
| T018 | T010, T014, T016, T017 |
| T019 | T003, T006 |
| T020 | T018, T019 |
| T021 | T003, T006 |
| T022 | T001, T002, T020, T021, T024 |
| T023 | T003, T006 |
| T024 | T001, T023 |
| T025 | T003, T006 |
| T026 | T001, T002, T024, T025 |
| T027 | T003, T006 |
| T028 | T001, T002, T022, T026, T027 |
| T029 | T006 |
| T030 | T018, T020, T029 |
| T031 | T006 |
| T032 | T001, T022, T028, T030, T031 |
| T033 | T002, T032 |

### User Story Order

US1 enables US2's complete input journey.
US2 enables US3's target review.
US4 backup precedes US3 execution.
US4 recovery follows apply and administration.
US5 isolated design can use fixtures, but final acceptance requires real integration.

### Parallel Examples

T001, T002, T003, and T005 can proceed independently with separate evidence ownership.
After T006, assign US1 tests T007/T009 to separate test files.
Assign US2 tests T011/T013/T015/T017 to separate test files.
US3 tests T019/T021, US4 tests T023/T025/T027, and US5 tests T029 use separate files.
No task has a blanket `[P]` marker because its approval prerequisites are not complete.
Do not parallelize edits to shared `routes.py`, `models.py`, `conversion.py`, or presentation files.

## Implementation Strategy

US1 is an initial review milestone, not the selected full-parity completion scope.
Complete all five stories and the comparison before claiming the migration is complete.
Use tests before implementation and validate each family independently.
Keep cloud features disabled until their contract and approval gates pass.
Do not run publication or deployment steps from this documentation-only assignment.
