# Tasks: Unit Test Domain Packages

**Input**: Numeric record at `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/`.

**Prerequisites**: `spec.md`, `plan.md`, `design/research.md`, `design/quickstart.md`

**Status rule**: A checked task means all its work is complete. Leave a task unchecked while any part remains.

**Resume status, 2026-10-26**: Tasks T039 through T043 complete four independent bounded splits and one cleared root move.
Keep T004 and the final acceptance tasks open.
The existing branch also overlaps PR #4415 at rename source `tests/unit/test_wan_hub_group_manager.py`.
PRs #4471, #4438, and #4436 overlap the existing `pyproject.toml` changes.
Do not publish or rebase this scope before the coordinator resolves these ownership conflicts.
The draft, merge hold, historical-link deferral, and previous path reservations remain unchanged.

**Current holds for later batches**: PR #4350 released
`tests/unit/refactors/test_sqlite_database_writer.py` and
`tests/unit/export/test_endpoint_family_exporter.py`. T046 uses only the SQLite writer test.
T047 applies the PR #4208 handoff for the five Arango tests and two named helper references.
Defer every other PR #4208 workflow and test path.
The latest T046 ownership scan found no exact PR, issue, or session claim.
Refresh ownership before each later batch.
PR #4226 merged. Its owner released the Cisco test path for T044.
Tasks T005 through T021 remain incomplete while these paths or other active claims remain reserved.
The coordinator must release the PR hold after #4353 before any pull request opens or changes.

## Phase 1: Setup

**Purpose**: Preserve the baseline and the path ownership evidence.

- [X] T001 Record the baseline unit test collection, full test result, and current open pull request and session claims in `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/design/research.md`.
- [X] T002 Map all 108 root test modules and the helper file to exact destination groups and child counts in `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/design/standalone-test-map.md`. The map has 109 unique source files and covers all 48 root directories.

## Phase 2: Foundational

**Purpose**: Prepare the path inventory before moving test packages.

- [X] T003 Inventory active imports, selectors, lint rules, workflows, the test-quality baseline, and current document references that name `tests/unit/` paths. Record broad scan counts and package-specific references in research.md. Mark paths selected by the PR-owned CI workflow as reserved. Preserve historical specifications, incident records, migration records, and handoff records.
- [ ] T004 Refresh open pull request file lists and active session claims before each move batch. Keep a PR path unchanged until its PR merges and its owner accepts the handoff. Keep an issue or session path unchanged until its owner clears the claim. Keep workflow-selected paths unchanged until the workflow owner accepts the handoff.

## Phase 3: User Story 1 - Find tests by domain (Priority: P1)

**Goal**: Place existing unit tests in source-aligned domain groups inside four existing root containers.

**Independent Test**: Inspect each new group and verify that it contains five or fewer children.

### Implementation for User Story 1

- [ ] T005 [US1] Move unowned foundation packages, including `bootstrap` and the contents of the existing `config` container, into their mapped groups. Split each moved package by test topic when its destination would exceed five children. Keep the completed `serial_cc`, `audit`, and `auth` moves. Defer `dataclasses`, `db_discovery`, and every other package with a current claim.
- [ ] T006 [US1] Move unowned Mist packages, including the contents of the existing `marvis` container, into their mapped groups. Split each moved package by test topic when its destination would exceed five children. Keep the root `marvis` container. Defer `api`, `org`, `websocket_streams`, and every other package with a current claim.
- [ ] T007 [US1] Move unowned operations packages, including packet capture, firmware policy, and MIB generator tests, into their exact topic groups. Keep each group at five children or fewer. Keep the root `prod_readiness` container. Defer `export`, `ssh`, and every other package with a current claim.
- [ ] T008 [US1] Move unowned interface packages, including the contents of the existing `maps` container, into their mapped groups. Split each moved package by test topic when its destination would exceed five children. Keep the root `maps` container. Defer `scripts`, `upgrade_portal`, and each other reserved or workflow-selected path.
- [ ] T009 [US1] Move the 108 root test modules and `_test_arango_writer_helpers.py` from `tests/unit/` into the exact groups in `design/standalone-test-map.md`. Keep the Arango writer test and helper together. Do not move any reserved or workflow-selected path.
- [ ] T010 [US1] Keep each new grouping directory at five children or fewer. Verify every mapped topic group, including `bootstrap/`, `serial_cc/`, `container/`, packet capture, firmware policy, MIB generator, troubleshooting, and Juniper Docs. Verify that `tests/unit/` gains no direct child.
- [X] T027 [US1] Correct the four oversized Juniper RMA destination groups through the exact bounded map. Update the JSON fixture root. Compare full unit collection, run the RMA and browser tests, and verify baseline path fields and child counts.
- [X] T028 [US1] Move the four unclaimed aggregate-cancellation tests into the mapped firmware aggregation group. Preserve the reserved aggregate service test. Verify focused tests, full node IDs, the unchanged baseline, and applicable guards.
- [X] T029 [US1] Move the unclaimed proxy and SSR manager tests into their mapped firmware manager groups. Verify focused tests, full node IDs, baseline path fields, and applicable guards.
- [X] T030 [US1] Move the three unclaimed device health report tests into the mapped report topic group. Verify focused tests, full node IDs, baseline path fields, and applicable guards.
- [X] T031 [US1] Move the four unclaimed assurance report packages into the exact bounded map. Preserve fixtures and update the AP support-file root. Verify focused tests, full node IDs, the unchanged baseline, and applicable guards.
- [X] T032 [US1] Move the four unclaimed certificate, subscription, rogue-evidence, and client-census packages into the mapped audit groups. Update helper imports and repository-root references. Verify tests, full node IDs, the baseline, and applicable guards.
- [X] T033 [US1] Move and split the three remaining unowned audit-report packages through the exact bounded map. Keep PSK and wired-client reports deferred. Verify helper imports, tests, full node IDs, the baseline, and applicable guards.
- [X] T034 [US2] Preserve the complete move commit and rebase onto the coordinator-approved main after PR #4353. Restore the held Arango package and its callers to main. Retain main's new posture outcome test and verify its fixture import. Compare both rename endpoints against all open pull requests. Verify focused tests, full node IDs, baseline fields, and changed-file style. Record results in `design/research.md`.
- [X] T035 [US2] Defer the insight-metrics test move to preserve its historical specification link under FR-004. Restore the original test path without a shim or duplicate. Verify baseline path values, ownership, complete node IDs, Markdown links, and required quality gates before the correction push.
- [X] T036 [US2] Rebase onto the coordinator-approved current main after PR #4357. Preserve the published correction and the merged UI test. Repair the moved MSP fixture's shared SDK mutation. Verify the failing seven-module order, the complete root-unit shard, node IDs, baseline fields, ownership, style, and required quality gates. Publish only after local validation.
- [X] T037 [US2] After the green current-main checks, preserve that remote head and rebase onto the coordinator-approved main after PR #4361. Verify the merged credential test, both fixes, node IDs, baseline fields, ownership, style, and required quality gates. Keep the pull request draft with auto-merge disabled.
- [X] T038 [US2] Preserve the green published head and rebase onto exact coordinated main `1c089ed07ba865a7e505df4774a79751c72187cf`. Verify merged WAN service tests, both fixes, complete node IDs, baseline fields, ownership, style, prerequisites, and quality gates. Keep the pull request draft without auto-merge.
- [X] T039 [US1] Split the unclaimed MIB generator tests into the mapped CLI, generator, and performance groups. Move the JSON fixture with its reader. Verify focused tests, complete node IDs, unchanged baseline fields, group sizes, path guards, and style.
- [X] T040 [US1] Split the unclaimed firmware policy tests into changes, recovery bundles, and recovery selection groups. Keep shared fixtures and helpers at their current paths. Verify focused tests, complete node IDs, unchanged baseline fields, group sizes, path guards, and style.
- [X] T041 [US1] Split the unclaimed container tests into mapped build-support and runtime groups. Update helper imports, repository-root depths, and the current container guide. Verify focused tests, complete node IDs, unchanged baseline fields, group sizes, path guards, and style.
- [X] T042 [US1] Apply the bounded troubleshooting map to core tests, credential tests, SMS tests, synthetic tests, and RF diagnostics. Update the standalone consumer import and RF manifest root. Preserve all baseline non-path fields. Verify focused tests, full node-ID parity, group sizes, declarations, path guards, and style.
- [X] T043 [US1] Move the cleared `tests/unit/test_fast_mode_flag.py` to its mapped startup group without a content change. Verify focused tests, full node-ID parity, the root reduction, target group size, active references, path guards, and style. Keep all other claimed root files deferred.
- [X] T044 [US1] Move the released Cisco test into its mapped group. Preserve its canonical content and five-child limit. Verify node IDs, tests, guards, style, compilation, and the quality baseline. (completed: see `design/research.md`)
- [X] T045 [US1] Move the released CSV-import test package into its mapped inventory group. Update only active scratch paths. Verify node IDs, tests, guards, group counts, baseline semantics, style, and compilation. (completed: see `design/research.md`)
- [X] T046 [US1] Move the four released device-replacement tests and the released SQLite writer test to their mapped groups. Preserve file bytes and all node IDs. Verify ownership, hierarchy, active references, baseline semantics, focused tests, guards, style, compilation, and committed test-quality gates. Record evidence in `design/research.md`.
- [X] T047 [US1] Move the five released Arango tests to their mapped storage group. Update only their internal helper imports and the approved imports in `tests/unit/db_discovery/test_probe.py` and `tests/contract/test_arango_declared_indexes.py`. Preserve all other file content and test behavior. Verify current ownership, hierarchy, active references, baseline semantics, the complete mapped unit collection, focused tests, guards, style, compilation, and committed test-quality gates. Record evidence in `design/research.md`.

- [X] T048 [US1] Move the two inventory utility tests and the anomaly metrics discovery test to their mapped refactor groups. Preserve file bytes and all node IDs. Verify ownership, hierarchy, active references, baseline semantics, focused tests, guards, style, compilation, and committed test-quality gates. Record evidence in `design/research.md`.
- [X] T049 [US1] Move the two entrypoint tests to their mapped runtime entrypoint group. Preserve file bytes and all node IDs. Verify ownership, hierarchy, active references, baseline semantics, focused tests, guards, style, compilation, and committed test-quality gates. Record evidence in `design/research.md`.
- [X] T050 [US1] Move `test_connection_pool_executor.py`, `test_maps_manager_launcher.py`, and `test_wan2_migration_launcher.py` to `network/launchers/`. Preserve file bytes and node IDs. Update only four baseline path fields. Verify ownership, hierarchy, references, baseline semantics, tests, guards, style, compilation, and committed test-quality checks. Record evidence in `design/research.md`.

- [X] T051 [US1] Move `test_data_directory_checker.py` to its mapped `data/filesystem/` group. Preserve file bytes, historical references, baseline records, and node IDs. Verify ownership, hierarchy, tests, guards, style, compilation, links, and committed test-quality checks.

- [X] T052 [US1] Move `test_main_entrypoint.py` to its mapped runtime entrypoint group. Preserve file bytes and node IDs. Update four baseline path fields and three active quickstart command paths. Verify ownership, hierarchy, historical evidence, tests, guards, style, compilation, links, and committed test-quality checks.

- [X] T053 [US1] Move `test_reject_unsupported_flag_variants.py` to its mapped runtime entrypoint group. Adjust only its repository-root depth and four baseline path fields. Preserve historical evidence and node IDs. Verify ownership, hierarchy, tests, guards, style, compilation, links, and committed test-quality checks.

- [X] T054 [US1] Move the template cloner, WAN probe configuration, and WLAN RADIUS timer tests to mapped `network/configuration/`. Preserve file bytes, historical evidence, baseline semantics, and node IDs. Verify ownership, hierarchy, tests, guards, style, compilation, links, and committed test-quality checks.
- [X] T055 [US1] Repair the relocated WLAN fixture teardown for issue #4492. Restore the exact previous resolver host. Prove normal and exception teardown, then run the affected downstream tests. Preserve the unpublished #2746 HTTP 403 append for later integration from `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` into `tests/unit/config/foundation/support/refactors/network/configuration/test_wlanradius_timer_manager_paths.py`. Do not import that separate change or alter its branch. Require green exact-head CI before another batch.
- [X] T056 [US1] Move the unowned keyboard listener and TUI launcher tests into mapped `runtime/console/`. Preserve test bytes, all node IDs, historical records, and baseline semantics. Change only two baseline path fields. Verify ownership, hierarchy, affected test order, guards, style, compilation, links, and committed quality gates. Keep the fast-mode test outside this batch.
- [X] T057 [US1] Move the unowned service-ping launcher test into mapped `network/clients/`. Preserve test bytes, all node IDs, historical records, and baseline semantics. Update only its baseline path fields and direct feature evidence. Verify ownership, hierarchy, affected test order, guards, style, compilation, links, and committed quality gates. Keep the other two client tests and their quickstart references outside this batch.
- [X] T058 [US1] Move the unowned interactive session initializer and switch-login tests into mapped `runtime/session/`. Preserve test bytes, node IDs, historical records, and the unchanged baseline. Verify ownership, hierarchy, affected test order, guards, style, compilation, links, and committed quality gates. Keep the application-context and session initializer tests outside this batch.
- [X] T059 [US1] Move the unowned fast-mode seam test into mapped `runtime/console/`. Preserve test bytes, node IDs, historical records, and baseline semantics. Change only four baseline path fields. Verify ownership, hierarchy, affected test order, guards, style, compilation, links, and committed quality gates.
- [X] T060 [US1] Move the unowned output-formatter test into mapped `interfaces/ui/display/`. Preserve test bytes, node IDs, historical records, shared fixtures, and the unchanged baseline. Verify ownership, fixture independence, hierarchy, UI tests, guards, style, compilation, links, and committed quality gates. Preserve the application-context test and historical quickstart under the explicit user hold.
- [X] T061 [US1] Move the unowned display-utils test into mapped `interfaces/ui/display/`. Preserve test bytes, node IDs, shared fixtures, baseline, and historical records. Verify ownership, fixture independence, hierarchy, UI tests, narrow guards, style, compilation, documentation, and committed quality gates.
- [X] T062 [US1] Move the independent TUI orchestrator test into mapped `interfaces/ui/interaction/tui/`. Preserve test bytes, node IDs, historical references, shared fixtures, and the baseline. Keep the #2711 parameter-collector reservation unchanged. Verify ownership, UI tests, narrow guards, collection parity, style, compilation, documentation, and committed quality gates.
- [X] T063 [US1] Move the independent device-prompt rename guard into mapped `interfaces/ui/interaction/dispatch/`. Adjust only its repository-root depth and four baseline path fields. Verify the exact source scan, negative control, node IDs, baseline semantics, fixture preservation, ownership, scoped tests, style, documentation, and committed quality gates.
- [X] T064 [US1] Move the independent interactive-display test into mapped `interfaces/ui/interaction/dispatch/`. Preserve test bytes and shared fixtures. Update only four baseline path fields. Verify ownership, resolver-sensitive test order, full collection parity, baseline semantics, hierarchy, style, documentation, and committed quality gates.
- [X] T065 [US1] Move the unowned inventory versioning test into mapped `inventory/support/versioning/`. Preserve every test byte, shared fixtures, baseline, and historical specifications. Verify ownership, inventory tests, collection parity, hierarchy, style, documentation, and committed quality gates.
- [X] T066 [US1] Move the unowned inventory pivot-renderer package and its existing marker into mapped `inventory/inventory_summary/`. Preserve every file byte, baseline, fixtures, and historical records. Verify ownership, inventory tests, collection parity, hierarchy, style, documentation, and committed quality gates.

## Phase 4: User Story 2 - Run the existing unit tests (Priority: P1)

**Goal**: Preserve test discovery, imports, and test selection after each move.

**Independent Test**: Collect the unit tests after each batch and compare the result with the recorded baseline.

### Implementation for User Story 2

- [ ] T011 [US2] Update imports that name moved packages in `tests/unit/`, `tests/integration/`, and `tests/e2e/`. Update the Arango helper import and each package-helper import.
- [ ] T012 [US2] Update test path overrides in `pyproject.toml` for moved standalone test modules.
- [ ] T013 [US2] Update active path references in scripts, configuration, `.github/test-quality-baseline.json`, source comments, and current documents. Preserve historical specifications, incident records, migration records, handoff records, and release notes.
- [ ] T014 [US2] Update CI selectors in `.github/workflows/ci.yml` only after PR #4208 merges and its owner accepts the handoff. Keep every path selected by the current workflow in place until then.
- [ ] T015 [US2] Collect unit tests after each batch and compare every collected test with the baseline in `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/design/research.md`.
- [ ] T016 [US2] Run focused tests under each completed domain group and compare their results with the recorded baseline.

## Phase 5: User Story 3 - Avoid conflicts with active work (Priority: P1)

**Goal**: Move reserved paths only after their owners merge.

**Independent Test**: Compare the new paths with the merged pull request files and confirm that each change remains present.

### Implementation for User Story 3

- [ ] T017 [US3] Move `api`, `dataclasses`, `db_discovery`, `export`, `gateway`, `org`, and `ssh` only after each related pull request, issue, and session claim clears. Split each released package by test topic when its destination would exceed five children. Move `db_discovery` only after `tests/unit/upgrade_portal/test_store.py` is released, PR #4208 accepts the handoff, issue #2752 receives human review, and its owner clears related claims. The Cisco converter test moved under T044 after PR #4226 merged. Remaining holds include PR #4287, issue #2746, issue #2747, and issue #2752.
- [ ] T018 [US3] Move `tests/unit/websocket_streams/` only after PR #4208 merges, its owner accepts the handoff, and each active session claim clears. PRs #4308 and #4315 have merged.
- [ ] T019 [US3] Move `tests/unit/wan_performance/` to `tests/unit/maps/interfaces/portals/wan_performance/` only after PR #4208 merges and its owner accepts the handoff.
- [ ] T020 [US3] Move `tests/unit/scripts/` after PR #4208 merges and its owner accepts the handoff. Move `tests/unit/upgrade_portal/` after PR #4208 merges, issue #2752 work receives human review, and its owner clears all related claims. Do not enable auto-merge for portal work. Then update the CI selectors.
- [ ] T021 [US3] Confirm that no open pull request, active issue claim, session claim, or workflow selector owns any remaining path under `tests/unit/`.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the complete layout and run the required checks.

- [ ] T022 Run `python -m pytest tests/unit/ --collect-only -q`, verify the five final root entries, and compare the collection with the baseline in `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/design/research.md`.
- [ ] T023 Run `python -m ruff check .`, `python -m black --check .`, and `python -m py_compile MistHelper.py` for the applicable changed files.
- [ ] T024 Run `python -m pytest tests/guardrails/test_move_module_guidance.py tests/guardrails/test_portal_operation_coverage.py` for the changed test paths.
- [ ] T025 Confirm the final changed-file list contains only test files, test configuration, scripts, required CI selectors, Spec Kit artifacts, documentation, and `changelog.d/issue-4142-test-domain-packages.md`. Confirm that it contains no production code path.
- [ ] T026 Add `changelog.d/issue-4142-test-domain-packages.md` and complete the local gates, commit, rebase, pull request, CI, merge, build, revision check, and deployment steps required by Constitution IV. Stop before any step that lacks user authorization.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on the baseline inventory.
- **User Story 1 (Phase 3)**: Depends on the inventory and path map.
- **User Story 2 (Phase 4)**: Runs with each completed move batch.
- **User Story 3 (Phase 5)**: Each task waits for the named pull requests to merge.
- **Polish (Phase 6)**: Depends on all paths moving and all references updating.

### Parallel Opportunities

- No package moves run in parallel because they share `tests/unit/` and can alter path references.
- Focused tests for different completed groups can run in parallel after their moves and imports are complete.

## Implementation Strategy

1. Record the collection baseline and resolve destinations for each standalone test.
2. Move only unowned packages and standalone tests.
3. Update imports and path references in the same batch as each move.
4. Wait for each owning pull request before moving its reserved package.
5. Compare collection with the baseline and run the required checks after the final move.
