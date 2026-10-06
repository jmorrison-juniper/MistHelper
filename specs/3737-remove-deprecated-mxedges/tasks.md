# Tasks: Remove Deprecated Mist Edge WebSocket Channels

**Input**: Design documents from `specs/3737-remove-deprecated-mxedges/`

**Scope**: Remove only the two deprecated WebSocket catalog rows and update their direct
verification. Do not change Mist Edge REST operations, statistics handling, transport code, or
unrelated tests.

**Tests**: Focused unit, contract, and inventory verification is required by `spec.md`.

## Phase 1: Setup

**Purpose**: Reuse the existing catalog and verification structure.

No setup tasks are required. The plan identifies the existing Python modules and test files.

## Phase 2: Foundational

**Purpose**: Establish shared prerequisites for the catalog and verification changes.

No foundational tasks are required. The existing catalog, SDK dependency, and test fixtures provide
the required foundation.

## Phase 3: Remove deprecated catalog entries (Priority: P1) 🎯 MVP

**Goal**: Keep only supported Mist Edge statistics channels in the immutable WebSocket catalog.

**Independent test criteria**: `ChannelCatalog().entries()` contains 16 rows, excludes
`org.mxedges` and `site.mxedges`, retains both statistics keys, and preserves all other relative
order and behavior.

- [ ] T001 [US1] Remove the `org.mxedges` and `site.mxedges` rows from `_ROWS` in
  `src/mist/realtime/websocket_streams/catalog/channels.py`. Keep `org.stats.mxedges` and
  `site.stats.mxedges` in their existing relative positions with their identifier fields and
  `/orgs/{org_id}/stats/mxedges` and `/sites/{site_id}/stats/mxedges` path templates.

## Phase 4: Verify catalog lookup and path behavior

**Purpose**: Prove the catalog exposes the supported streams and rejects the removed keys.

### User Story 1 - Select supported Mist Edge streams (Priority: P1)

**Goal**: Let an engineer select supported Mist Edge statistics streams without exposing
deprecated event streams.

**Independent test criteria**: Use synthetic identifiers to verify the 16-entry catalog, absent
removed lookups, retained statistics lookups, exact path construction, and unchanged catalog order.

- [ ] T002 [P] [US1] Update
  `tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py` to expect 16 entries and
  assert that `org.mxedges` and `site.mxedges` are absent from entry keys and return `None` from
  `ChannelCatalog.get()`.
- [ ] T003 [P] [US1] Add focused unit assertions in
  `tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py` for the retained statistics
  entries. Build `/orgs/11111111-1111-4111-8111-111111111111/stats/mxedges` and
  `/sites/22222222-2222-4222-8222-222222222222/stats/mxedges`, and verify the first, last, and
  unaffected relative order of catalog keys.

## Phase 5: Verify SDK parity and inventory expectations

**Purpose**: Keep supported catalog paths aligned with public SDK channels and keep diagnostic
inventory checks consistent with the reduced catalog.

### User Story 2 - Preserve supported SDK channel parity (Priority: P2)

**Goal**: Prove both retained statistics entries match the public SDK WebSocket channel paths.

**Independent test criteria**: Compare catalog paths built with synthetic identifiers against
`orgs.MxEdgesStatsEvents` and `sites.MxEdgesStatsEvents`, without credentials or a live stream.

- [ ] T004 [P] [US2] Update
  `tests/contract/websocket_streams/test_ws_channel_parity.py` to remove parity cases for
  deprecated `MxEdgesEvents` classes while retaining parity cases for
  `MxEdgesStatsEvents` with valid synthetic organization and site identifiers.
- [ ] T005 [P] [US2] Review
  `tests/e2e/websockets_tab/dialog_audit/support/inventory.py` and update only catalog inventory
  expectations that require the removed deprecated SDK event classes. Keep supported statistics
  classes and the dynamic catalog inventory checks. Do not remove SDK classes or lower a broad
  inventory safety threshold without an assertion for the 16-entry catalog.
- [ ] T006 [US2] Add or update the direct inventory assertion in
  `tests/e2e/websockets_tab/dialog_audit/test_inventory.py` so the diagnostic inventory confirms
  both deprecated keys are absent, both statistics keys remain, and the catalog count is 16
  without opening a WebSocket or requiring a Mist credential.

## Phase 6: Document the user-visible change

**Purpose**: Record the removal for the next release.

- [ ] T007 [P] Add `changelog.d/issue-3737-remove-deprecated-mxedges.md` with one `###` heading and
  one `Changed` or `Removed` bullet that names issue #3737 and states that the deprecated
  `org.mxedges` and `site.mxedges` catalog channels were removed while the statistics channels
  remain supported.

## Phase 7: Validate the complete change

**Purpose**: Run focused tests and applicable Python quality checks without live Mist access.

- [ ] T008 Run
  `python -m pytest tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py tests/contract/websocket_streams/test_ws_channel_parity.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py`
  and confirm the catalog count, removed-key lookup, retained paths, SDK parity, and inventory
  expectations pass.
- [ ] T009 [P] Run
  `python -m py_compile src/mist/realtime/websocket_streams/catalog/channels.py tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py tests/contract/websocket_streams/test_ws_channel_parity.py tests/e2e/websockets_tab/dialog_audit/support/inventory.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py`
  and confirm no syntax errors.
- [ ] T010 [P] Run
  `python -m ruff check src/mist/realtime/websocket_streams/catalog/channels.py tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py tests/contract/websocket_streams/test_ws_channel_parity.py tests/e2e/websockets_tab/dialog_audit/support/inventory.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py`
  and confirm the focused files pass lint.
- [ ] T011 [P] Run
  `python -m black --check src/mist/realtime/websocket_streams/catalog/channels.py tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py tests/contract/websocket_streams/test_ws_channel_parity.py tests/e2e/websockets_tab/dialog_audit/support/inventory.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py`
  and confirm the focused files use the repository format.
- [ ] T012 Run the repository task-quality preflight and the changed-test gate after the
  implementation commit. Use the intended base branch and do not change
  `.github/test-quality-baseline.json`.

Do not use a live Mist credential, start a production WebSocket, call the Mist REST API, or change
Mist Edge REST behavior during validation.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: No tasks are required.
- **Foundational**: No tasks are required.
- **User Story 1**: T001 must complete before T002 and T003.
- **User Story 2**: T001 must complete before T004, T005, and T006.
- **Documentation**: T007 can run after the intended behavior is confirmed.
- **Validation**: T008 through T012 require the implementation and verification changes to exist.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after the empty foundational phase and delivers the MVP.
- **User Story 2 (P2)**: Starts after T001 and does not depend on User Story 1 test edits.
- Complete User Story 1 before release validation. User Story 2 can proceed in parallel after T001.

### Task Dependency Graph

```text
T001 -> T002 and T003
T001 -> T004, T005, and T006
T002, T003, T004, T005, T006 -> T007
T002, T003, T004, T005, T006, T007 -> T008
T008 -> T009, T010, and T011
T008, T009, T010, T011 -> T012
```

### Parallel Opportunities

- T002 and T003 can run in parallel after T001 because they update focused unit expectations.
- T004, T005, and T006 can run in parallel after T001 because they cover separate contract and
  inventory surfaces.
- T009, T010, and T011 can run in parallel after T008.

## Parallel Execution Examples

```text
After T001:
Run T002 and T003 together.
Run T004, T005, and T006 together.

After T008 passes:
Run T009, T010, and T011 together.
```

## Implementation Strategy

### MVP First

1. Complete T001, T002, and T003.
2. Run the User Story 1 focused unit tests.
3. Complete T004 and T005, then add T006 for the inventory boundary.
4. Add T007 and run T008 through T012.

### Incremental Delivery

1. Remove the two deprecated rows and prove the 16-entry catalog.
2. Prove retained SDK path parity.
3. Align the diagnostic inventory expectation.
4. Add the release note and complete focused validation.

## Format Validation

Every task uses `- [ ]`, a sequential `T###` identifier, a `[P]` marker only for parallel work,
and a `[US#]` label for user story tasks. Each implementation or validation task names an exact
file path or command.
