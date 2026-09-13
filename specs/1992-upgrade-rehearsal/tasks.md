# Tasks: The upgrade rehearsal harness

**Input**: Design documents from `specs/1992-upgrade-rehearsal/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/rehearsal-cloud.md`, `contracts/rehearsal-clock.md`

**Tests**: This feature is a test harness. Almost every task therefore writes
test code or test support code. No task changes a file under `src/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run at the same time as its neighbours. It touches its
  own file, and it waits for no earlier task of the same phase.
- **[Story]**: The user story of the task. The stories are US1, US2, US3, and
  US4.
- Each task names the exact file that it creates or changes.

## Path Conventions

- The harness lives in `tests/support/rehearsal/`.
- The rehearsal tests live in `tests/unit/upgrade_portal/`.
- The prose of the feature lives in `specs/1992-upgrade-rehearsal/`.
- Every command uses `.venv\Scripts\python.exe`.

---

## Phase 1: Setup

**Purpose**: Make the package and the shared errors ready.

- [X] T001 Create the package directory and the package marker
      `tests/support/rehearsal/__init__.py`. The marker exports the public names
      of the harness, and it holds no logic.
- [X] T002 [P] Create `tests/support/rehearsal/errors.py` with
      `RehearsalNetworkError` and `RehearsalFirmwareError`. Design decision 5 of
      `plan.md` names both errors.
- [X] T003 [P] Add the three planned test modules to the pytest paths of
      `pyproject.toml` if the current configuration misses them. Confirm that
      `.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal -q` still
      collects the shipped tests.

**Checkpoint**: The package imports, and the test command still runs.

---

## Phase 2: Foundational

**Purpose**: Build the clock, the scripts, the stand-in cloud, and the harness.
Every user story needs all four.

- [X] T004 Create `tests/support/rehearsal/clock.py` with `RehearsalClock`. The
      class holds the reading, the lock, and the sleep record. It publishes
      `now`, `sleep`, `now_text`, and `advance`. Section 2 of
      `contracts/rehearsal-clock.md` states each shape.
- [X] T005 [P] Create `tests/support/rehearsal/script.py` with `DeviceScript`
      and `FleetScript`. Sections 2 and 3 of `data-model.md` state the fields,
      the methods, and the rules.
- [X] T006 Add the two fleet builders to `tests/support/rehearsal/script.py`.
      The first builder answers 2 gateways, 2 switches, and 2 access points. The
      second builder adds 1 session smart router for the stop tests.
- [X] T007 Create `tests/support/rehearsal/cloud.py` with `StandInResponse` and
      the call record. Sections 6 and 7 of `contracts/rehearsal-cloud.md` state
      both shapes.
- [X] T008 Add `StandInCloud` to `tests/support/rehearsal/cloud.py` with the
      five answer methods. Each method copies the signature of section 1 to
      section 5 of `contracts/rehearsal-cloud.md`. The resolver raises
      `RehearsalFirmwareError` for `upgradeSiteDevices`, for `upgradeDevice`,
      and for `upgradeOrgSsrs`.
- [X] T009 Add the counters and the pause hook to
      `tests/support/rehearsal/cloud.py`. `calls_of` reports the count of one
      call name. The pause hook blocks one poll round for the run status test of
      Q8 in `research.md`.
- [X] T010 Create `tests/support/rehearsal/harness.py`. The module holds
      `RehearsalDeps` and `RehearsalHarness`. `attach` replaces the five
      attachment points through `monkeypatch`. `start` builds the run record and starts `RunDriver.start`.
      `join` waits 5 real seconds at most. `record` answers the run record.
- [X] T011 Fill the four time seats inside
      `tests/support/rehearsal/harness.py`. The seats are
      `SettleGate(clock=...)`, `PhaseGateDeps.sleep`,
      `CloudReconnectReader(clock=...)`, and `RunDriverDeps.clock`. One
      `RehearsalClock` object fills all four.
- [X] T012 [P] Create `tests/unit/upgrade_portal/conftest.py` entries for the
      network guard. The guard replaces `socket.socket` with a function that
      raises `RehearsalNetworkError`, and it counts each attempt.
- [X] T013 [P] Create `tests/unit/upgrade_portal/test_rehearsal_support.py`.
      The tests prove the clock, the scripts, and the stand-in answers alone.
      A broken support module then fails here and not inside a whole run.

**Checkpoint**: The harness starts a run against the stand-in cloud. The story
phases can now begin.

---

## Phase 3: User Story 1 - Prove the settle gate through the whole cascade (Priority: P1)

**Goal**: One composed run drives the shipped driver through all four phases.
The suite reads the phase order, the settle signals, and the post-check.

**Independent Test**: Run
`.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_cascade.py`.
The test needs no browser and no network.

- [X] T014 [US1] Create `tests/unit/upgrade_portal/test_rehearsal_cascade.py`
      with the fixture that builds the harness, attaches the stand-in cloud, and
      starts the run.
- [X] T015 [US1] Add the phase order test to
      `tests/unit/upgrade_portal/test_rehearsal_cascade.py`. The test asserts the
      order gateways, switches, access points, clients. This test meets FR-017.
- [X] T016 [US1] Add the phase guard test to the same file. The test asserts
      that no later phase started before the earlier phase settled. This test
      meets FR-018.
- [X] T017 [P] [US1] Add the settle window test to the same file. The test finds
      the round that proved the reboot, and it reads that reading as `T`. It
      asserts that the device stayed unsettled below `T` plus the wait, and that
      it settled at the first round at or above that point. The test reads the
      wait from `gate.settle_wait_seconds`. This test meets FR-019.
- [X] T018 [P] [US1] Add the access point test to the same file. The test proves
      the longer wait of an access point through the same five steps of section
      5 of `contracts/rehearsal-clock.md`. This test meets FR-020.
- [X] T019 [P] [US1] Add the post-check test to the same file. The test asserts
      that the driver started the capture double after the client phase settled.
      This test meets FR-022.
- [X] T020 [US1] Add the run status test to the same file. The pause hook of
      T009 holds one poll round. The test reads the record and asserts that the
      read took under 1 second. This test meets FR-021.
- [X] T021 [P] [US1] Add the call shape test to the same file. The test reads
      the call record of each stand-in and compares the keyword names against
      `contracts/rehearsal-cloud.md`. This test meets FR-007 and FR-008.
- [X] T022 [P] [US1] Add the page shape test to the same file. The stand-in
      answers `results`, `total`, and `next`, so the shipped page guard runs
      against a real page count. This test meets FR-009.
- [X] T023 [P] [US1] Add the edge case tests to the same file. The cases are the
      phase timeout, the partial poll round, the version change with no earlier
      uptime, and the stale statistics record. The `Edge Cases` section of
      `spec.md` names all four.
- [X] T024 [US1] Add the guard test to the same file. The test asserts that the
      network attempt count is zero, and that `calls_of` answers zero for the
      three firmware write names. This test measures SC-004 and SC-005.

**Checkpoint**: User Story 1 is complete. A reader may stop here and still hold
a working harness.

---

## Phase 4: User Story 2 - Prove the stop control in mid-run (Priority: P1)

**Goal**: A stop in the middle of a run cancels the right devices, spares the
device that writes firmware, and reports a clear message.

**Independent Test**: Run
`.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_stop.py`.

- [X] T025 [US2] Add the upgrade status answers to
      `tests/support/rehearsal/cloud.py`. The answer carries `status`,
      `current_phase`, `targets.reboot_in_progress`, `upgrade_id`, and
      `status_known`. Section 5 of `contracts/rehearsal-cloud.md` states the
      shape. This task meets FR-013.
- [X] T026 [US2] Create `tests/unit/upgrade_portal/test_rehearsal_stop.py` with
      the fixture that starts a run and holds one device in the write state.
- [X] T027 [US2] Add the cancel test to the same file. The test asserts that the
      stop cancelled every device that did not start to write firmware. This
      test meets FR-024.
- [X] T028 [P] [US2] Add the mid-write test to the same file. The test asserts
      that the portal did not interrupt the device that writes firmware, and
      that the device appears in the `already_writing` list. This test meets
      FR-025.
- [X] T029 [P] [US2] Add the message test to the same file. The test asserts
      that the message states that the device in mid-write will finish. This
      test meets FR-026.
- [X] T030 [P] [US2] Add the session smart router test to the same file. The
      test asserts the cancel through the organization scope call, and it
      asserts `scope: "org"` in the run record. This test meets FR-027.
- [X] T031 [P] [US2] Add the stop edge case tests to the same file. The cases
      are the early stop, the late stop, and the unreadable state of one device.
- [X] T032 [US2] Add the guard test to the same file, in the shape of T024. The
      test measures SC-004 and SC-005 for the stop run.

**Checkpoint**: Both P1 stories pass. The suite now proves the 9 portal pass
conditions of SC-001.

---

## Phase 5: User Story 3 - Catch the three known defect classes (Priority: P2)

**Goal**: The harness fails against broken code. A harness that passes against
broken code gives false confidence.

**Independent Test**: Run
`.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_defects.py`.

- [X] T033 [US3] Create `tests/support/rehearsal/defects.py` with `DefectDrill`.
      The class publishes one applier for each defect class. Each applier takes
      the `monkeypatch` fixture and the stand-in cloud.
- [X] T034 [US3] Create `tests/unit/upgrade_portal/test_rehearsal_defects.py`
      with the fixture that builds the drill and the harness.
- [X] T035 [P] [US3] Add the first drill test to the same file. The drill drops
      the `device_type` parameter of the event search. The stand-in then answers
      access points only. The test passes when the gateway phase and the switch
      phase fail to settle.
- [X] T036 [P] [US3] Add the second drill test to the same file. The drill
      replaces `gate.uptime_decreased` with a rule that compares a cloud stamp
      against the local clock. The test passes when a device settles at once and
      the cascade assertion fails.
- [X] T037 [P] [US3] Add the third drill test to the same file. The drill
      replaces `upgrade_service._normalize_status` with a copy that reads
      `phase`. The test passes when the stop run reports the missing field.
- [X] T038 [US3] Add the drill summary test to the same file. The test asserts
      that each of the 3 defect classes made at least one rehearsal test fail,
      and that `monkeypatch` reverted every patch. This test measures SC-006 and
      meets FR-028.

**Checkpoint**: The harness proves itself against broken code.

---

## Phase 6: User Story 4 - Reduce the live run to a short confirmation (Priority: P3)

**Goal**: A short checklist names only the facts that the rehearsal cannot
prove. The live run of scenario C and scenario D stays a human decision.

**Independent Test**: Read the checklist and confirm that each item needs real
hardware.

- [X] T039 [US4] Create `specs/1992-upgrade-rehearsal/live-checklist.md`. The
      file holds 5 items or fewer. Each item needs real hardware. The two facts
      are the cloud acceptance of the call and the reboot of the hardware. This
      task meets FR-030 and measures SC-007.
- [X] T040 [US4] Add the reboot warning to the same file. The warning names the
      reboot risk, names issue #2007, and states the outage of six access points
      for about six minutes. This task meets FR-031.
- [X] T041 [US4] Add the scope note to the same file. The note states that this
      feature does not close issue #1992, and that a person must decide the live
      run. This task meets FR-029. No task of this list runs scenario C or
      scenario D against real hardware.

---

## Phase 7: Polish and Quality Gates

**Purpose**: Measure the budget and pass every gate of the repository.

- [X] T042 Measure the suite duration and the longest wait. Run the three
      rehearsal modules with `--durations=20` and record the result in
      `specs/1992-upgrade-rehearsal/quickstart.md`. The whole suite must finish
      under 60 real seconds, and no test may wait more than 1 real second. This
      task measures SC-002 and SC-003.
- [X] T043 [P] Run `.venv\Scripts\python.exe -m ruff check tests/support/rehearsal tests/unit/upgrade_portal`
      and repair every finding.
- [X] T044 [P] Run `.venv\Scripts\python.exe -m black --check tests/support/rehearsal tests/unit/upgrade_portal`
      and repair every finding.
- [X] T045 [P] Run `.venv\Scripts\python.exe -m mypy tests/support/rehearsal`
      and repair every finding.
- [X] T046 [P] Run `.venv\Scripts\python.exe -m pylint tests/support/rehearsal`
      and reach a score of 9.5 or above.
- [X] T047 [P] Run `.venv\Scripts\python.exe -m radon cc tests/support/rehearsal -n C`
      and hold every block below a complexity of 10.
- [X] T048 [P] Run `.venv\Scripts\python.exe -m vulture tests/support/rehearsal`
      and remove every unused name.
- [X] T049 [P] Run `.venv\Scripts\python.exe -m pydocstyle tests/support/rehearsal`
      and repair every finding.
- [X] T050 [P] Run `.venv\Scripts\python.exe -m interrogate -f 90 tests/support/rehearsal`
      and reach 90 percent or above.
- [X] T051 Run the STE linter command from section 9 of
      `specs/1992-upgrade-rehearsal/quickstart.md` for each Markdown file of the
      feature. Reach 80 or above for every file. This task meets FR-032 and
      measures SC-008.
- [X] T052 Add the inline comment on every executable line of the new modules,
      as principle VI of the constitution asks. Confirm the `info` line and the
      `debug` line of each action, as principle VII asks.
- [X] T053 Update `CHANGELOG.md` with the new harness and the live checklist.
      Name issue #1992 and issue #2007.

---

## Dependencies

- Phase 1 blocks Phase 2. The package must import first.
- Phase 2 blocks every story phase. T004 blocks T010 and T011. T005 blocks T006,
  T007, and T008.
- User Story 1 and User Story 2 both hold priority P1. Both need Phase 2 only,
  so the two phases may run at the same time after T013.
- User Story 3 needs the tests of User Story 1 and of User Story 2, because each
  drill fails one of those tests.
- User Story 4 needs no code. It may run at any point after Phase 1.
- Phase 7 needs every earlier phase.

## Parallel Work

- Phase 2: T005 runs beside T004. T012 and T013 run beside each other.
- User Story 1: T017, T018, T019, T021, T022, and T023 run beside each other.
- User Story 2: T028, T029, T030, and T031 run beside each other.
- User Story 3: T035, T036, and T037 run beside each other.
- Phase 7: T043 to T050 run beside each other.

## Implementation Strategy

The smallest useful product is Phase 1, Phase 2, and User Story 1. That set
proves the settle gate through the whole cascade, and it guards the network and
the firmware. User Story 2 adds the stop proof. User Story 3 proves the harness
itself. User Story 4 shortens the eventual live run.
