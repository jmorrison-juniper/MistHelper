# Tasks: Systematic mistapi Upgrade Alignment

**Feature**: 017-mistapi-upgrade-alignment

---

## Phase 1: Setup

- [ ] T001 Update mistapi version pin to ">=0.61.3" in requirements.txt
- [ ] T002 Add mistapi version check at startup in MistHelper.py

## Phase 2: Foundational

- [ ] T003 Implement session exception handling per contract in MistHelper.py
- [ ] T004 Validate all menu-to-API mappings in MistHelper.py against data-model.md

## Phase 3: User Story 1 - Breaking Change Fixes (P1)

- [ ] T005 [P] [US1] Update Menu 68 (Site Insight Metrics) to use correct positional/query param for metrics in MistHelper.py
- [ ] T006 [P] [US1] Update Menu 69 (Client Insight Metrics) to use correct positional/query param for metrics in MistHelper.py
- [ ] T007 [P] [US1] Update Menu 81 (Device Insight Metrics) to support new port_id param and add getSiteInsightMetricsForAP if applicable in MistHelper.py
- [ ] T008 [US1] Replace any deprecated SLE function calls with trend variants in MistHelper.py
- [ ] T009 [US1] Add/verify test for all safe menu options: python MistHelper.py --test

## Phase 4: User Story 2 - Enhanced Alarm and Search Operations (P2)

- [ ] T010 [P] [US2] Update Menu 1 (Org Alarms) to support new filter params (group, severity, ack_admin_name, acked, search_after) in MistHelper.py
- [ ] T011 [P] [US2] Update all paginated search endpoints to use search_after where available in MistHelper.py
- [ ] T012 [US2] Add/verify test for alarm export and search_after pagination

## Phase 5: User Story 3 - Device Utility Commands Use device_utils (P2)

- [ ] T013 [P] [US3] Refactor Menu 123 (Traceroute) to use device_utils module in MistHelper.py
- [ ] T014 [P] [US3] Refactor Menu 124-129 (Gateway/Switch utilities) to use device_utils module in MistHelper.py
- [ ] T015 [P] [US3] Refactor Menu 130-132 (BGP, ARP, DHCP) to use device_utils module in MistHelper.py
- [ ] T016 [P] [US3] Refactor Menu 136-137 (Monitor Traffic, Top Command) to use device_utils module in MistHelper.py
- [ ] T017 [US3] Add/verify test for all device utility commands

## Phase 6: User Story 4 - WebSocket Operations Use mistapi.websockets (P3)

- [ ] T018 [P] [US4] Refactor WebSocketManager to use mistapi.websockets module in MistHelper.py
- [ ] T019 [P] [US4] Refactor PacketCaptureManager to use mistapi.websockets module in MistHelper.py
- [ ] T020 [US4] Add/verify test for WebSocket and packet capture operations

## Phase 7: Polish & Cross-Cutting

- [ ] T021 Update README.md with new version, changelog, and menu operation notes
- [ ] T022 Run python -m py_compile MistHelper.py and resolve any syntax errors
- [ ] T023 Run python MistHelper.py --test and resolve any test failures
- [ ] T024 Validate requirements.txt and README.md for accuracy
- [ ] T025 Final review: ensure all exception/logging patterns are ASCII-only and safe

---

## Dependencies

| Story | Depends On |
| - | - |
| US1 | Setup, Foundational |
| US2 | Setup, Foundational |
| US3 | Setup, Foundational |
| US4 | Setup, Foundational |
| Polish | All stories |

## Parallel Execution Examples

- T005, T006, T007 can be done in parallel (different menu code blocks)
- T010, T011 can be done in parallel (alarm/search code)
- T013-T016 can be done in parallel (device utility menus)
- T018, T019 can be done in parallel (WebSocket/PacketCapture)

## Implementation Strategy

- MVP: Complete all tasks for User Story 1 (T005-T009)
- Incremental: Complete each user story phase independently, run tests after each
- Polish: Only after all user stories pass tests
