# Tasks: Rogue PCI Evidence Pack

**Input**: Design documents from `specs/3562-rogue-pci-evidence/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/evidence-pack.md](./contracts/evidence-pack.md)

## Phase 1: Setup

- [x] T001 Create package directory and `__init__.py` in `src/reports/rogue_pci_evidence/__init__.py`.
- [x] T002 Create test directory and `__init__.py` in `tests/unit/reports/rogue_pci_evidence/__init__.py`.
- [x] T003 Create release note fragment in `changelog.d/issue-3562-rogue-pci-evidence.md`.
- [x] T004 Update wiring manifest in `specs/3562-rogue-pci-evidence/wiring.md` with final handler, menu, primary key, and deferred registration details.

## Phase 2: Foundational

- [x] T005 Implement dataclasses and constants in `src/reports/rogue_pci_evidence/model.py`.
- [x] T006 Implement CSV row builders and summary builder in `src/reports/rogue_pci_evidence/model.py`.
- [x] T007 Implement no-network model fixtures in `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_model.py`.
- [x] T008 Implement client test doubles in `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_client.py`.

## Phase 3: User Story 1 - Export PCI rogue evidence pack (P1)

**Goal**: The operation writes `RogueEvidence.csv`, `RogueSiteSettings.csv`, and `RogueEvidenceSummary.md` under `data/`.

**Independent Test**: Run the operation with fake client data and fake exporters. Confirm that all three outputs are written with no prompt.

- [x] T009 [P] [US1] Add operation tests for the three evidence outputs in `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_operation.py`.
- [x] T010 [US1] Implement the Mist API client shell in `src/reports/rogue_pci_evidence/client.py`.
- [x] T011 [US1] Implement `RoguePciEvidencePack.run()` orchestration in `src/reports/rogue_pci_evidence/operation.py`.
- [x] T012 [US1] Implement Markdown summary writing in `src/reports/rogue_pci_evidence/operation.py`.

## Phase 4: User Story 2 - Classify rogue detections (P2)

**Goal**: The model classifies honeypot, rogue, and neighbor detections.

**Independent Test**: Use fixture rows where one SSID equals an org WLAN SSID and the BSSID is not an org AP BSSID. Confirm `honeypot`.

- [x] T013 [P] [US2] Add honeypot, rogue, and neighbor classification tests in `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_model.py`.
- [x] T014 [US2] Implement detection normalization and classification in `src/reports/rogue_pci_evidence/model.py`.
- [x] T015 [US2] Implement rogue AP and org event row aggregation in `src/reports/rogue_pci_evidence/client.py`.

## Phase 5: User Story 3 - Report site detection settings (P3)

**Goal**: The operation reports one settings row per site and counts detection-off sites.

**Independent Test**: Use fixture settings with one `rogue.enabled` false site. Confirm CSV and summary counts.

- [x] T016 [P] [US3] Add site settings and detection-off summary tests in `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_model.py`.
- [x] T017 [US3] Implement paced `getSiteSetting` reads in `src/reports/rogue_pci_evidence/client.py`.
- [x] T018 [US3] Implement site settings row mapping in `src/reports/rogue_pci_evidence/model.py`.

## Phase 6: Polish and Cross-Cutting

- [x] T019 Run `py_compile`, `ruff`, `black --check`, `mypy`, `pydocstyle`, and `pytest` on the new package and tests.
- [x] T020 Run `vulture` and `interrogate` on `src/reports/rogue_pci_evidence`.
- [x] T021 Repair any `speckit.analyze` findings in `specs/3562-rogue-pci-evidence/`, `src/reports/rogue_pci_evidence/`, and `tests/unit/reports/rogue_pci_evidence/`.
- [x] T022 Create the draft pull request body in `specs/3562-rogue-pci-evidence/pr-body.md`.

## Deferred Integration Tasks

- [ ] D001 Register menu 282 in `MistHelper.py` during the integration pull request only.
- [ ] D002 Register menu 282 in `src/utils/operation_registry.py` during the integration pull request only.
- [ ] D003 Add primary key strategies to `src/refactors/endpoint_primary_key_strategies.py` during the integration pull request only.
- [ ] D004 Update generated menu references during the integration pull request only.

## Dependencies

- Phase 1 must finish before Phase 2.
- Phase 2 must finish before User Stories 1, 2, and 3.
- User Story 1 can finish before User Stories 2 and 3 for a minimal evidence pack.
- User Stories 2 and 3 can proceed in parallel after Phase 2.
- Polish tasks run after all user stories.

## Parallel Execution Examples

- After T005, run T007 and T008 in parallel because they touch different test files.
- During User Story 1, run T009 while T010 starts because the test uses fakes.
- During User Story 2, run T013 while T014 starts because the test file and model file differ.
- During User Story 3, run T016 while T017 starts because the test file and client file differ.

## Implementation Strategy

1. Build the package and release note first.
2. Build the pure model before the client.
3. Build the operation after the model and client seams exist.
4. Prove each user story with a no-network unit test.
5. Keep MistHelper registration deferred to [wiring.md](./wiring.md).
