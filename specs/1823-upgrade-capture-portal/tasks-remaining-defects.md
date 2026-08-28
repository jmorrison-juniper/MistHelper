---
description: "Task list for the remaining walkthrough defects (US1-US7, FR-096..FR-127)"
---

# Tasks: Upgrade Capture Portal - Remaining Walkthrough Defects

**Input**: Design documents from `specs/1823-upgrade-capture-portal/`

**Prerequisites**:

- `plan-remaining-defects.md` (required)
- `spec-remaining-defects.md` (required, US1-US7, FR-096..FR-127)
- `research-remaining-defects.md` (design decisions D1-D7)
- `data-model-remaining-defects.md`
- `contracts/remaining-defects-deltas.md` (deltas H1-H3, U1-U2, S1)

**Branch**: `integration/upgrade-portal-fixes`. Stay on this branch. Do not open a
new branch.

**Tests**: The spec asks for unit tests, contract tests, and browser tests. Every
test task below is required, not optional.

**Note on the file name**: The parent feature already owns `tasks.md`. This batch
writes `tasks-remaining-defects.md`, so it does not overwrite the parent list.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with its siblings. It touches a different
  file and depends on no incomplete task.
- **[Story]**: The user story the task serves (US1..US7). Setup, Foundational, and
  Polish tasks carry no story label.
- Each task names the exact file path it touches.

## Conventions for every code task

Every code task in this list MUST obey these rules. The rules come from the plan
Constitution Check and the batch conventions. A junior NOC engineer must read the
result with no help.

- **Simplified Technical English**. Short sentences. Active voice. One idea per
  sentence. Full words, not abbreviations.
- **Inline WHY comment**. Every new executable line carries a comment that states
  why the line exists (Constitution VI).
- **Action logging**. Every operation logs at info level before the action and at
  debug level after the action. Log records are ASCII and use `%s` placeholders
  (Constitution V and VII).
- **Five-Item Rule**. Every function takes at most 5 parameters and holds at most
  25 lines (Constitution I). A dataclass or a context object carries any extra
  value.
- **Anchor comments**. When a source comment names a contract line number, the
  same commit edits the contract text and the anchor comment together.

---

## Phase 1: Setup and Baseline (Shared)

**Purpose**: Prove a green start before any change. These tasks block every story.

- [X] T001 Confirm the branch and record the green baseline. Run `git status` to
  confirm the tree is `integration/upgrade-portal-fixes` and holds no unrelated
  change. Run `git log main..HEAD --oneline` to confirm the eleven sibling fixes
  are present. Run `python -m pytest tests/unit/upgrade_portal tests/contract/upgrade_portal`
  and `python -m pytest tests/e2e/upgrade_portal` from the repository root, and
  record the pass counts (about 13842 unit and 167 browser) as the baseline.
- [X] T002 [P] Confirm the batch adds no dependency and the stores answer. Read
  `requirements.txt` and `pyproject.toml` and confirm no new third-party package
  is needed. Confirm ArangoDB and Redis are reachable for the contract layer and
  the browser layer, as `spec-remaining-defects.md` names them.

**Checkpoint**: The baseline is green and the stores answer. Story work can start.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm the one shared mechanism that Phase A relies on. This batch
adds no shared module and no new subpackage, so this phase is small.

**⚠️ CRITICAL**: US1 (Phase 3) is the data-graph foundation. Phase B depends on it.
The whole comparison trusts a clean graph. So US1 lands before US2.

- [X] T003 Verify the empty-run edge guards in `src/upgrade_portal/capture/store.py`.
  Read `build_edge` (~line 1351), `write_edge` (~line 1458), and
  `_link_capture_to_run` (~line 1516). Confirm each one already skips an empty
  `run_id`. US1 relies on these guards, so no edge forms for a standalone capture.
  Record the exact line anchors for the US1 change. Read-only, no edit.

**Checkpoint**: The guards exist. US1 can build the standalone path with no edge.

---

## Phase 3: Phase A - User Story 1 - A capture that names no run leaves a clean graph (Priority: P1) 🎯 Foundation / MVP

**Resolves**: #2096.

**Goal**: A capture that names no run stands alone. It writes no run document and
no `capture_for_run` edge. A one-time repair removes the dangling edges the old
behavior left.

**Independent Test**: Start a capture on a site with devices and name no run. Read
the edge collection. Confirm the capture wrote no `capture_for_run` edge and no run
document. Then create a run through the documented endpoint and confirm every page
renders the correct plan.

### Tests for User Story 1 (write first, ensure they FAIL)

- [X] T004 [P] [US1] Create the failing unit test
  `tests/unit/upgrade_portal/test_capture_standalone_key.py`. Assert two standalone
  captures hold different `cap-{hex}-01` keys and write no `capture_for_run` edge
  (D1, FR-096, Risk 1).
- [X] T005 [P] [US1] Create the failing unit test
  `tests/unit/upgrade_portal/test_store_repair_dangling_edges.py`. Seed one live
  edge and one dangling edge in one store. Assert the repair removes the dangling
  edge, keeps the live edge, logs each removal, leaves every capture document, and
  removes zero on a second run (D2, FR-098, FR-099, SC-017, Risk 2).

### Implementation for User Story 1

- [X] T006 [US1] Add a standalone key builder in
  `src/upgrade_portal/capture/assembly.py`. The builder reads a fresh `uuid4` hex
  nonce, not a run, and returns `cap-{hex}-01`. Keep `capture_key` for the run path
  (D1).
- [X] T007 [US1] In `src/upgrade_portal/app/routes/capture.py::build_job`
  (~line 606, invented value at ~line 618): when the body names no run, set
  `run_id=""` and build the key from the standalone builder of T006. Do not invent
  a run identifier (D1, FR-096).
- [X] T008 [US1] In `src/upgrade_portal/capture/collector.py::capture_identity`
  (~line 949): accept a job that names no run and carries a prebuilt standalone
  key. Build the document from that key instead of raising `MISSING_RUN_MESSAGE`
  for an empty run (D1).
- [X] T009 [P] [US1] Add `repair_dangling_edges` to
  `src/upgrade_portal/capture/store.py`. Scan the `capture_for_run` edges. Read the
  run document that each edge names in `_from` before any removal. Remove only an
  edge whose run document does not exist. Log each removed edge with its key and
  the missing run key. Leave every capture document (D2, FR-097, FR-098, Risk 2).
- [X] T010 [US1] Call `repair_dangling_edges` once from the ensure path in
  `src/upgrade_portal/capture/store.py`, near `_ensure_collection` (~line 577), so
  it runs once for each worker at start and stays idempotent (D2). Depends on T009.

### Contract and data-model updates for User Story 1

- [X] T011 [P] [US1] Update `specs/1823-upgrade-capture-portal/contracts/http-api.md`
  for Delta H2. State that a body with no run derives the key from a fresh nonce,
  stands alone as a site pre-check, and writes no run and no edge. Update the source
  anchor comments that name the http-api line numbers in the same commit.
- [X] T012 [P] [US1] Record the run-less capture decision in
  `specs/1823-upgrade-capture-portal/data-model.md` (FR-100). State the four facts:
  no run and no edge for a run-less capture; the standalone key comes from a nonce;
  the upgrade start writes the edge at adoption time; a one-time repair clears old
  dangling edges.

### Checkpoint for User Story 1

- [X] T013 [US1] Run the US1 gate. Confirm T004 and T005 now pass. Run `ruff`,
  `black --check`, and `mypy` strict on `src/upgrade_portal/capture/assembly.py`,
  `src/upgrade_portal/capture/collector.py`, `src/upgrade_portal/capture/store.py`,
  and `src/upgrade_portal/app/routes/capture.py`. Confirm zero dangling edges after
  20 run-less captures (SC-017). US1 is now independently testable.

---

## Phase 4: Phase B - User Story 2 - The browser leads from a capture to an upgrade (Priority: P1)

**Resolves**: #2098. **Depends on**: Phase A (US1). The adoption trusts a clean graph.

**Goal**: The capture page offers a control that creates the run and opens the
options page. The server adopts the newest verified standalone pre-check and writes
the `pre` edge. No operator types a site address.

**Independent Test**: Sign in, take the site lock, and run a capture. Press the new
upgrade control. Confirm the browser reaches the options page and then the confirm
page with no typed address.

### Tests for User Story 2 (write first, ensure they FAIL)

- [X] T014 [P] [US2] Create the failing unit test
  `tests/unit/upgrade_portal/test_run_adopts_precheck.py`. Seed several captures.
  Assert `latest_standalone_precheck` returns the newest capture with `role=pre`,
  an empty `run_id`, and a verified state (FR-103, Risk 3).
- [X] T015 [P] [US2] Create the failing contract test
  `tests/contract/upgrade_portal/test_run_create_adopts_precheck.py`. Assert
  `POST /api/sites/<site_id>/runs` writes the `capture_for_run` edge with role
  `pre` to the new run and sets the run pre-check field (Delta H3, FR-103).

### Implementation for User Story 2

- [X] T016 [US2] Add `latest_standalone_precheck(site_id)` to
  `src/upgrade_portal/capture/store.py`. Filter role `pre`, an empty `run_id`, and
  a verified state. Read the newest by date (FR-103, Risk 3). Depends on Phase A.
- [X] T017 [US2] In `src/upgrade_portal/app/routes/upgrade.py::create_run`
  (~line 766): adopt the newest verified standalone pre-check, write the `pre`
  edge, and set the run pre-check field. Keep the existing lock refusal and the
  live-run refusal in front of the adoption (Delta H3, FR-103, FR-104, FR-105).
- [X] T018 [US2] Add the start-upgrade control and its error region to
  `src/upgrade_portal/app/assets/templates/capture/capture.html`. Use the test
  identifiers `capture-start-upgrade-button` and `capture-start-upgrade-error`
  (Delta U1, FR-101).
- [X] T019 [US2] In `src/upgrade_portal/app/assets/static/js/portal.js`: post
  `POST /api/sites/<site_id>/runs`, read the new run identifier, open the options
  page, and render a refusal that names the lock holder or the unfinished run
  (FR-102, FR-104, FR-105). Shared file: sequence before US3 and US6 edits.

### Contract updates for User Story 2

- [X] T020 [P] [US2] Update
  `specs/1823-upgrade-capture-portal/contracts/http-api.md` for Delta H3 (the run
  create adopts a standalone pre-check) and
  `specs/1823-upgrade-capture-portal/contracts/ui-testids.md` for Delta U1 (the two
  new capture-page controls). Update the source anchor comments in the same commit.

### Browser journey and checkpoint for User Story 2

- [X] T021 [US2] Update the browser test
  `tests/e2e/upgrade_portal/test_capture.py`. Walk from the site list, to the
  capture view, to the options page, to the confirm page, with no typed address
  (FR-106, SC-018).
- [X] T022 [US2] Run the US2 gate. Confirm T014, T015, and T021 pass. Run `ruff`,
  `black --check`, and `mypy` strict on `src/upgrade_portal/capture/store.py` and
  `src/upgrade_portal/app/routes/upgrade.py`. Confirm the browser reaches the
  confirm page with no typed address. US2 is now independently testable.

**Checkpoint**: Phase A and Phase B are complete. The five Phase C stories can now
start in parallel.

---

## Phase 5: Phase C - User Story 3 - The lock banner tells the truth after a capture takes the site (Priority: P1)

**Resolves**: #2108. **Parallel with**: US4, US5, US6, US7.

**Goal**: The capture-start answer carries the lock grant. The browser repaints the
banner with no reload and starts the renewal beat. The stored record holds an empty
run value, never the text `None`.

**Independent Test**: Sign in and open the capture page of a free site. Press
`Start the capture` and do not press `Take the site`. Read the banner with no
reload. Confirm the banner reports the operator as the holder.

### Tests for User Story 3 (write first, ensure they FAIL)

- [X] T023 [P] [US3] Create the failing unit test
  `tests/unit/upgrade_portal/test_lock_record_empty_run.py`. Assert the stored lock
  record holds an empty run string, never the text `None`, when the lock names no
  run (FR-112, Risk 4).
- [X] T024 [P] [US3] Create the failing contract test
  `tests/contract/upgrade_portal/test_capture_start_lock_grant.py`. Assert the 202
  answer carries the `lock` object after a lock take, and holds no `lock` object on
  a refusal and on a start with no owner (Delta H1, FR-109, FR-111, Risk 5).

### Implementation for User Story 3

- [X] T025 [US3] In `src/upgrade_portal/runtime/lock.py`: ensure the stored run
  value is an empty string, never `str(None)` (`LockRecord.run_id` ~line 564,
  `LockRequest.run_id` ~line 727) (FR-112, Risk 4).
- [X] T026 [US3] In `src/upgrade_portal/app/routes/capture.py`: thread the grant
  from `capture_conflict` (~line 814) and `take_site_lock` (~line 761) through
  `launch_capture` into the 202 body. Send the grant on the success answer only
  (Delta H1, FR-109, Risk 5).
- [X] T027 [US3] In `src/upgrade_portal/app/assets/static/js/portal.js`: on a
  capture-start success, read the grant and call the existing painters
  `paintLockHeld` (~line 1928) and `startLockBeat` (~line 2185). Add no new painter
  (FR-107, FR-108, FR-110). Shared file: this edit lands before the US6 edit.

### Contract update and checkpoint for User Story 3

- [X] T028 [P] [US3] Update
  `specs/1823-upgrade-capture-portal/contracts/http-api.md` for Delta H1 (the 202
  answer carries the lock grant after a lock take). Update the source anchor
  comments in the same commit.
- [X] T029 [US3] Run the US3 gate. Confirm T023 and T024 pass. Run `ruff`,
  `black --check`, and `mypy` strict on `src/upgrade_portal/runtime/lock.py` and
  `src/upgrade_portal/app/routes/capture.py`. Confirm the banner reports the true
  holder with no reload (SC-019) and the lock survives one renewal period (SC-020).

---

## Phase 6: Phase C - User Story 4 - The comparison proves a quiet site kept every client (Priority: P1)

**Resolves**: #2109. **Parallel with**: US3, US5, US6, US7. Mirrors device commit
`c9431881`.

**Goal**: The client comparison reports the true present count for a quiet site. A
digest match proves the clients of a skipped section present, and the count states
how many. The client return rate corrects itself.

**Independent Test**: Compare two verified captures of a quiet site whose wired
clients and wireless clients did not change. Confirm the present count equals the
true client count and the return rate reads correctly.

### Tests for User Story 4 (write first, ensure it FAILS)

- [X] T030 [P] [US4] Create the failing unit test
  `tests/unit/upgrade_portal/test_compare_client_present_counts.py`. Compare two
  identical captures and assert the present count equals the client count. Guard
  against a double count. Assert a genuine empty section still reads zero. Assert
  the count reads the larger of the two client index sizes (FR-113, FR-114, FR-116,
  FR-117).

### Implementation for User Story 4

- [X] T031 [US4] In `src/upgrade_portal/compare/clients.py`: add `proved_present`
  to `ClientComparison` and add a section-size reader that takes the larger of the
  two client index sizes. Fill the field in `compare_clients` (~line 494) by
  summing the proved present count over the three skipped sections (wired,
  wireless, guest) (D3, FR-113, FR-114).
- [X] T032 [US4] In `src/upgrade_portal/compare/statistics.py::count_clients`
  (~line 338): add the proved present count to the present count. The return rate
  reads the corrected present count with no further change (D3, FR-115). Depends on
  T031.

### Checkpoint for User Story 4

- [X] T033 [US4] Run the US4 gate. Confirm T030 passes. Run `ruff`,
  `black --check`, and `mypy` strict on `src/upgrade_portal/compare/clients.py` and
  `src/upgrade_portal/compare/statistics.py`. Confirm the `to_dict` form still names
  only `client_deltas` and `skipped_sections`. Re-run the existing
  `tests/unit/upgrade_portal/test_compare_statistics.py` and
  `tests/unit/upgrade_portal/test_compare_skipped_counts.py` to confirm no
  regression (SC-021).

---

## Phase 7: Phase C - User Story 5 - Every page reports the same site lock (Priority: P2)

**Resolves**: #2097. **Parallel with**: US3, US4, US6, US7.

**Goal**: A page that cannot name its site reports a `site_unknown` state. The
`unknown` sentence stays reserved for an unreachable lock store.

**Independent Test**: Open a page whose run identifier resolves to no run. Confirm
the page reports that it cannot name the site. Confirm the page does not report an
unreachable lock store.

### Tests for User Story 5 (write first, ensure it FAILS)

- [X] T034 [P] [US5] Create the failing unit test
  `tests/unit/upgrade_portal/test_lock_banner_site_unknown.py`. Assert an empty
  site identifier reads the `site_unknown` state. Assert the `unknown` state stays
  reserved for an unreachable store. Assert a run identifier that resolves to no
  run reads the correct message (FR-118, FR-119, FR-120, Risk 7).

### Implementation for User Story 5

- [X] T035 [US5] In `src/upgrade_portal/app/routes/select.py`: add the
  `site_unknown` state constant and return it from `lock_banner_context`
  (~line 1790) when the site identifier is empty. Keep `site_lock_state`
  (~line 614) `unknown` reserved for an unreachable store (D5, FR-118, FR-119).
- [X] T036 [US5] Add one sentence for the `site_unknown` state to
  `src/upgrade_portal/app/assets/templates/partials/lock_banner.html`. Do not
  change the `held`, `free`, `locked`, or `unknown` wording (D5, FR-119).

### Contract update and checkpoint for User Story 5

- [X] T037 [P] [US5] Update
  `specs/1823-upgrade-capture-portal/contracts/site-lock.md` for Delta S1 (the
  fifth banner state `site_unknown`). Update the source anchor comments in the same
  commit.
- [X] T038 [US5] Run the US5 gate. Confirm T034 passes. Run `ruff`,
  `black --check`, and `mypy` strict on `src/upgrade_portal/app/routes/select.py`.
  Confirm a page with a resolvable site reports a lock state that agrees with every
  other page in the session (FR-119).

---

## Phase 8: Phase C - User Story 6 - The upgrade options show every choice at once (Priority: P3)

**Resolves**: #2101. **Parallel with**: US3, US4, US5, US7. Shares `portal.js` with
US3, so the US6 `portal.js` edit lands after the US3 edit.

**Goal**: The strategy control, the reboot control, and the Junos-file-action
control become radio groups. The two version controls stay dropdowns. The saved
body keeps the same three field names and the same defaults. The old test
identifiers retire, and no test reads a stale identifier.

**Independent Test**: Open the options page. Confirm the strategy group, the reboot
group, and the Junos file action group each render as a radio group. Confirm the
version controls stay dropdowns. Confirm every default is unchanged.

### Tests for User Story 6 (write first, ensure it FAILS)

- [X] T039 [P] [US6] Update the contract test
  `tests/contract/upgrade_portal/test_upgrade_options.py`. Read the new group and
  option identifiers (`upgrade-strategy-group`, `upgrade-reboot-group`,
  `upgrade-junos-file-action-group`). Assert the saved body keeps the three field
  names `strategy`, `reboot`, and `junos_file_action` with the same defaults
  (Delta U2, FR-121, FR-123, FR-124).

### Implementation for User Story 6

- [X] T040 [US6] Convert three controls to radio groups in
  `src/upgrade_portal/app/assets/templates/upgrade/options.html`. Add
  `upgrade-strategy-group` with `upgrade-strategy-big-bang` and
  `upgrade-strategy-canary`; `upgrade-reboot-group` with `upgrade-reboot-yes` and
  `upgrade-reboot-no`; `upgrade-junos-file-action-group` with
  `upgrade-junos-file-action-yes` and `upgrade-junos-file-action-no`. Keep the
  version dropdowns `upgrade-version-select-all` and `upgrade-version-select-<mac>`
  (D6, FR-122). Keep the defaults: strategy all-at-once, reboot yes, Junos file
  action no (FR-123).
- [X] T041 [US6] In `src/upgrade_portal/app/assets/static/js/portal.js`: read the
  checked radio for each group. Replace the `UPGRADE_REBOOT_TESTID`,
  `UPGRADE_JUNOS_TESTID`, and `UPGRADE_STRATEGY_TESTID` constants (~lines 72-74)
  with the new group identifiers. Keep the saved body field names and defaults
  (D6, FR-124). Shared file: land this edit after the US3 edit T027.
- [X] T042 [P] [US6] Style the radio groups in
  `src/upgrade_portal/app/assets/static/css/portal.css`.

### RISK task - retire every old identifier (US6)

- [X] T043 [US6] **Find and update every existing test and asset that reads a
  retired identifier.** Grep `tests/` and
  `specs/1823-upgrade-capture-portal/contracts/` for `upgrade-strategy-select`,
  `upgrade-reboot-toggle`, and `upgrade-junos-file-action-toggle`. Update each hit
  to the new group and option identifiers. Known hits: `tests/e2e/upgrade_portal/test_upgrade.py`
  (`STRATEGY_SELECT_ID` at line 58, `REBOOT_TOGGLE_ID` at line 57) and, per the
  plan, `tests/contract/upgrade_portal/test_upgrade_options.py`. The rename retires
  the old identifiers in the same change, so no test reads a stale identifier
  (Risk 6). Depends on T040 and T041.

### Contract update, browser journey, and checkpoint for User Story 6

- [X] T044 [P] [US6] Update
  `specs/1823-upgrade-capture-portal/contracts/ui-testids.md` for Delta U2 (retire
  the three old identifiers; add the group and option identifiers; the version
  identifiers do not change). Update the source anchor comments in the same commit.
- [X] T045 [US6] Update the browser test
  `tests/e2e/upgrade_portal/test_upgrade.py`. Drive the three radio groups through
  the options page with the new identifiers (FR-121). Depends on T043.
- [X] T046 [US6] Run the US6 gate. Confirm T039 and T045 pass. Run `ruff`,
  `black --check`, and `mypy` strict on the touched source. Grep `src/`, `tests/`,
  and `specs/1823-upgrade-capture-portal/` and confirm zero retired identifiers
  remain (FR-124, Risk 6).

---

## Phase 9: Phase C - User Story 7 - The comparison view matches the specification (Priority: P3)

**Resolves**: #2104. **Parallel with**: US3, US4, US5, US6. Documentation only.

**Goal**: Align `spec.md` with the working single-difference-table view and record
the reason. No behavior changes.

**Independent Test**: Open the comparison of two captures. Confirm the page shows
one device difference table and one client difference table. Confirm each changed
row names the value before and the value after.

### Implementation for User Story 7

- [X] T047 [US7] Amend `specs/1823-upgrade-capture-portal/spec.md`. Rewrite FR-065
  and FR-066 to describe one device difference table and one client difference
  table, each sorted by address. Rewrite User Story 2 Acceptance Scenario 1 to
  match. Amend FR-017 for the radio groups and the version-list dropdown exception.
  Align the User Story 2 and User Story 3 story text. Record the reason for the
  single difference table (D7, FR-125, FR-126, FR-127). This task is the sole owner
  of parent `spec.md` edits, so US6 does not also edit `spec.md`.
- [X] T048 [US7] Confirm no code change is needed. Read
  `src/upgrade_portal/compare/render.py` and confirm it already builds one device
  difference table and one client difference table (D7). Re-run
  `tests/unit/upgrade_portal/test_compare_render.py` to confirm the view is
  unchanged.

**Checkpoint**: All seven stories are complete and independently testable.

---

## Phase 10: Polish and Final Verification (Cross-Cutting)

**Purpose**: Confirm the batch-wide gates on every touched file.

- [X] T049 [P] Audit the Constitution gates on every file that US1 through US6
  touched. Confirm each new line carries an inline WHY comment. Confirm each
  operation logs before and after with ASCII `%s` records. Confirm each new or
  edited function stays within 5 parameters and 25 lines. Files: `capture/assembly.py`,
  `capture/collector.py`, `capture/store.py`, `app/routes/capture.py`,
  `app/routes/upgrade.py`, `app/routes/select.py`, `runtime/lock.py`,
  `compare/clients.py`, `compare/statistics.py`, and the touched templates, the
  `portal.js` file, and `portal.css`.
- [X] T050 **FINAL VERIFICATION - run every quality gate from the repository root.**
  All must pass with no regression against the T001 baseline.
  - `python -m ruff check .`
  - `python -m black --check .`
  - `python -m mypy src/upgrade_portal` (strict)
  - `python -m pytest tests/unit/upgrade_portal tests/contract/upgrade_portal`
  - `python -m pytest tests/e2e/upgrade_portal`
  Confirm every new test passes, the 13842 unit tests and the 167 browser tests
  stay green, and the success criteria SC-017 through SC-023 hold.

---

## Dependencies and Execution Order

### Plan phase map

- **Phase A = US1** (Phase 3). The honest graph. The foundation.
- **Phase B = US2** (Phase 4). The capture-to-upgrade journey. Depends on Phase A.
- **Phase C = US3, US4, US5, US6, US7** (Phases 5-9). Five independent stories that
  run in parallel with each other.

### Phase dependencies

- **Setup (Phase 1)** blocks every later phase.
- **Foundational (Phase 2)** confirms the edge guards US1 relies on.
- **Phase A / US1 (Phase 3)** depends on Setup and Foundational. It is the data
  foundation for Phase B.
- **Phase B / US2 (Phase 4)** depends on Phase A. The adoption reads a clean graph
  and the new `latest_standalone_precheck` query.
- **Phase C (Phases 5-9)** depends on Phase A and Phase B being complete. The five
  stories then run in parallel.
- **Polish (Phase 10)** depends on every story that the team lands.

### Cross-story shared files (must serialize)

- **`src/upgrade_portal/app/assets/static/js/portal.js`** is edited by US2 (T019),
  US3 (T027), and US6 (T041). Phase B lands first. Inside Phase C, land the US3
  edit (T027) before the US6 edit (T041).
- **`src/upgrade_portal/app/routes/capture.py`** is edited by US1 (T007) and US3
  (T026). Phase A lands before Phase C, so the order is safe.
- **`src/upgrade_portal/capture/store.py`** is edited by US1 (T009, T010) and US2
  (T016). Phase A lands before Phase B, so the order is safe.
- **`specs/.../contracts/http-api.md`** is edited by US1 (T011), US2 (T020), and
  US3 (T028). Land each in phase order.
- **`specs/.../spec.md`** is edited by US7 only (T047). US7 owns every parent spec
  amendment, including the FR-017 radio amendment, so US6 does not edit `spec.md`.

### Within each story

- Write the test first and confirm it fails before the implementation.
- Route decides the identity, assembly builds the key, collector builds the
  document, store owns every edge (US1 boundary).
- Model or store change before the route change. Route change before the browser
  change.
- The story gate runs last in the story.

---

## Parallel Opportunities

- **T002** runs in parallel with the T001 baseline read where staffing allows.
- **All test-writing tasks marked [P]** (T004, T005, T014, T015, T023, T024, T030,
  T034, T039) touch new files and run in parallel.
- **Phase C stories run in parallel.** With five engineers: US3, US4, US5, US6, and
  US7 proceed at once. Honor the one shared-file rule: the US6 `portal.js` edit
  lands after the US3 `portal.js` edit.
- **Documentation tasks marked [P]** (T011, T012, T020, T028, T037, T044) touch
  separate contract or model files and run in parallel with the code of their story.

### Parallel example: Phase C launch

```bash
# After Phase A and Phase B are green, launch the five Phase C stories:
Engineer A: US3 - lock grant on the 202     (T023..T029)
Engineer B: US4 - proved present clients     (T030..T033)
Engineer C: US5 - site_unknown lock state    (T034..T038)
Engineer D: US6 - radio groups and renames   (T039..T046)
Engineer E: US7 - spec documentation align   (T047..T048)
# Rule: Engineer D lands the portal.js edit (T041) after Engineer A lands T027.
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Complete Phase 1 Setup and Phase 2 Foundational.
2. Complete Phase 3 / US1 - the honest graph.
3. Stop and validate: no dangling edge after 20 run-less captures (SC-017).
4. This is the trust foundation for every later page.

### Incremental delivery

1. Setup and Foundational, then US1 (Phase A) - deliver the clean graph (MVP).
2. Add US2 (Phase B) - deliver the capture-to-upgrade journey.
3. Add the five Phase C stories in parallel - each adds value on its own.
4. Run the final verification gate (T050).

### Parallel team strategy

1. The team lands Phase A and Phase B together, because Phase C depends on both.
2. Once Phase B is green, five engineers take the five Phase C stories.
3. Each Phase C story completes and tests on its own.
4. The team runs T049 and T050 before the merge.

---

## Task Summary

- **Total tasks**: 50 (T001-T050).
- **Setup (Phase 1)**: 2 tasks (T001-T002).
- **Foundational (Phase 2)**: 1 task (T003).
- **Phase A / US1 (Phase 3)**: 10 tasks (T004-T013), 2 tests.
- **Phase B / US2 (Phase 4)**: 9 tasks (T014-T022), 2 tests.
- **Phase C / US3 (Phase 5)**: 7 tasks (T023-T029), 2 tests.
- **Phase C / US4 (Phase 6)**: 4 tasks (T030-T033), 1 test.
- **Phase C / US5 (Phase 7)**: 5 tasks (T034-T038), 1 test.
- **Phase C / US6 (Phase 8)**: 8 tasks (T039-T046), includes the identifier-rename
  risk task T043.
- **Phase C / US7 (Phase 9)**: 2 tasks (T047-T048), documentation only.
- **Polish (Phase 10)**: 2 tasks (T049-T050), includes the final all-gate task.

### Test layer coverage

- **Unit** (`tests/unit/upgrade_portal/`): `test_capture_standalone_key.py`,
  `test_store_repair_dangling_edges.py`, `test_run_adopts_precheck.py`,
  `test_lock_record_empty_run.py`, `test_compare_client_present_counts.py`,
  `test_lock_banner_site_unknown.py`.
- **Contract** (`tests/contract/upgrade_portal/`):
  `test_run_create_adopts_precheck.py`, `test_capture_start_lock_grant.py`,
  `test_upgrade_options.py` (updated).
- **E2E** (`tests/e2e/upgrade_portal/`): `test_capture.py` (updated),
  `test_upgrade.py` (updated).

### Contract and document files touched

- `contracts/http-api.md` (H1, H2, H3), `contracts/ui-testids.md` (U1, U2),
  `contracts/site-lock.md` (S1), `data-model.md` (FR-100), `spec.md` (FR-017,
  FR-065, FR-066, US2 AS1).

### Suggested MVP scope

- **US1 (Phase A)** alone. It removes the root cause of #2097 and unblocks #2098.
  The store leaves a clean graph that every later page can walk.
