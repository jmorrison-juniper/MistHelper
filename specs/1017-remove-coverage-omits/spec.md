# Feature Specification: Remove Coverage Omits and Test 36 Excluded Modules

**Feature Branch**: `1017-remove-coverage-omits`

**Created**: 2026-07-13

**Status**: Draft

**Input**: GitHub issue [#878](https://github.com/jmorrison-juniper/MistHelper/issues/878) — "test: remove coverage omits and add tests for 36 excluded modules"

## User Scenarios & Testing *(mandatory)*

<!--
  Each user story below corresponds to a themed cluster of modules currently
  hidden from coverage measurement by the `[tool.coverage.run].omit` list in
  `pyproject.toml`. Stories are ordered smallest-and-safest first, riskiest
  (async/interactive) last, mirroring the serial PR cadence used by initiative
  #1016. Each story is independently testable, reviewable, and revertable —
  landing any single story deletes real omit entries and lands real tests
  without dropping the repo below its `fail_under = 90` coverage gate.
-->

### User Story 1 - Low-Level Utility Modules Un-Omitted (Priority: P1)

Codebase maintainers need the small, pure-Python utility modules (`environment_utils`, `filter_operator_engine`, `troubleshoot_utils`, `prompt_client_utils`) removed from the coverage omit list and covered by real unit tests, so the safest cluster of modules stops gaming the coverage gate and establishes a working test pattern for the rest of the workflow.

**Why this priority**: These modules are small, dependency-light, and mostly pure functions. They are the lowest-risk cluster to land first and produce the highest confidence signal that the workflow's test-authoring conventions (fixtures, mock scope, marker usage) are correct before the workflow tackles harder clusters. Landing this first also removes 4 omit entries with minimal churn.

**Independent Test**: After merge, the four listed omit entries are absent from `pyproject.toml`, each module has at least one dedicated test file under `tests/` exercising every public entry point without `# pragma: no cover` or dummy imports, and `pytest --cov` passes with `fail_under = 90` and no drop in overall project coverage.

**Acceptance Scenarios**:

1. **Given** the PR branch at HEAD, **When** `grep -E "^\\s*\"src/(utils/environment_utils|utils/filter_operator_engine|troubleshooting/troubleshoot_utils|input/prompt_client_utils)\\.py\"" pyproject.toml` runs, **Then** the command returns zero matches.
2. **Given** the PR branch at HEAD, **When** `pytest --cov=src --cov-fail-under=90` runs under CI, **Then** the run passes and per-module coverage for each of the four un-omitted modules is at least 90%.
3. **Given** the PR branch at HEAD, **When** the four new/expanded test files are grepped for `# pragma: no cover`, **Then** zero matches are found.

---

### User Story 2 - Export Helper Utilities Un-Omitted (Priority: P2)

Codebase maintainers need the export-helper utility modules (`org_export_utils`, `license_export_utils`, `const_definitions_exporter`, `gateway_test_exporter`) removed from the coverage omit list and covered by real unit tests, so the shared helpers underpinning the larger org/site exporter clusters are proven correct before the exporters themselves are un-omitted.

**Why this priority**: These modules are consumed by the larger exporter clusters in P3–P4. Landing tests here first means the exporter tests that follow can rely on validated helper contracts, reducing rework and letting the helper tests catch bugs before exporter tests trip on them.

**Independent Test**: After merge, the four listed omit entries are absent from `pyproject.toml`, each module has dedicated tests under `tests/`, and `pytest --cov` passes at `fail_under = 90`.

**Acceptance Scenarios**:

1. **Given** the PR branch at HEAD, **When** the four omit lines are searched in `pyproject.toml`, **Then** zero matches remain.
2. **Given** the PR branch at HEAD, **When** the coverage report is inspected, **Then** each of the four un-omitted modules reports coverage of at least 90%.
3. **Given** the PR branch at HEAD, **When** integration-only paths (real Mist API calls) exist in these helpers, **Then** those paths are covered via `unittest.mock` doubles OR marked with the existing `integration` pytest marker — never left unexecuted.

---

### User Story 3 - API + Database + Analytics Data Path Un-Omitted (Priority: P3)

Codebase maintainers need the data-plumbing modules (`api_data_fetcher`, `api_fetch_utils`, `database_schema_utils`, `data_collection_manager`) removed from the coverage omit list and covered by real unit tests with mocked network and DB dependencies, so the core data path stops silently under-testing and the exporter clusters that consume it can be tested with confidence.

**Why this priority**: The data-fetch layer is upstream of most exporters. Landing its coverage before the exporter clusters (P4–P5) reduces the risk that an exporter test masks a bug in the fetcher. It comes after P2's helpers because the fetcher's test doubles reuse fixtures that P2 introduces.

**Independent Test**: After merge, the four listed omit entries are absent from `pyproject.toml`, each module has dedicated tests under `tests/` with network and DB calls mocked (or marked `integration`), and `pytest --cov` passes at `fail_under = 90`.

**Acceptance Scenarios**:

1. **Given** the PR branch at HEAD, **When** the four omit lines are searched in `pyproject.toml`, **Then** zero matches remain.
2. **Given** the PR branch at HEAD, **When** the new tests execute, **Then** no real Mist API call is issued (verified by `responses` / `pytest-httpx` / `unittest.mock` inspection, or by tests being marked `integration` and skipped by default).
3. **Given** the PR branch at HEAD, **When** the coverage report is inspected, **Then** each of the four un-omitted modules reports coverage of at least 90%.

---

### User Story 4 - Organization-Level Exporters Un-Omitted (Priority: P4)

Codebase maintainers need the org-level exporter modules (`org_admin_exporter`, `org_alarm_event_exporter`, `org_client_security_exporter`, `org_config_exporter`, `org_device_stats_exporter`, `org_template_exporter`) removed from the coverage omit list and covered by real unit tests, so the largest exporter cluster stops hiding behind coverage exclusions and every output format the org exporters produce is validated end-to-end against fixtures.

**Why this priority**: This is the largest single exporter cluster (six files). Landing it after P3 ensures the underlying data fetcher is validated first, so exporter tests exercise real code paths rather than compensating for unproven upstream behavior. Splitting into 6 sub-PRs may be warranted if any single exporter needs more than ~150 lines of test fixtures — implementation decides that, spec sets the ceiling per PR.

**Independent Test**: After merge, the six listed omit entries are absent from `pyproject.toml`, each exporter has dedicated tests validating at least one happy-path output and one error-path output, and `pytest --cov` passes at `fail_under = 90`.

**Acceptance Scenarios**:

1. **Given** the PR branch (or series of PRs) at HEAD, **When** the six omit lines are searched in `pyproject.toml`, **Then** zero matches remain.
2. **Given** the PR branch at HEAD, **When** the coverage report is inspected, **Then** each of the six un-omitted exporters reports coverage of at least 90%.
3. **Given** the PR branch at HEAD, **When** exporters that write files or emit CSV/JSON are tested, **Then** the tests assert against fixture-comparable output (either golden files or in-memory buffers), not just "did not raise".

---

### User Story 5 - Site-Level Exporters and Report Generators Un-Omitted (Priority: P5)

Codebase maintainers need the site-level exporter modules (`site_anomaly_exporter`, `site_config_exporter`, `site_device_exporter`, `sites_by_ap_model_exporter`) and report generators (`global_wired_client_report_generator`, `offline_device_reporter`, `sfp_transceiver_data_processor`, `wired_client_manufacturer_report_generator`) removed from the coverage omit list and covered by real unit tests, so the site-scope reporting surface reaches the project coverage bar.

**Why this priority**: These modules parallel the org-level exporters in structure but scope down to sites. Landing them after P4 lets P4's fixture patterns be reused. Each module is independently testable, so this may split into 2–3 sub-PRs if fixture surface warrants.

**Independent Test**: After merge, the eight listed omit entries are absent from `pyproject.toml`, each module has dedicated tests, and `pytest --cov` passes at `fail_under = 90`.

**Acceptance Scenarios**:

1. **Given** the PR branch (or series of PRs) at HEAD, **When** the eight omit lines are searched in `pyproject.toml`, **Then** zero matches remain.
2. **Given** the PR branch at HEAD, **When** the coverage report is inspected, **Then** each of the eight un-omitted modules reports coverage of at least 90%.
3. **Given** the PR branch at HEAD, **When** report generators that produce tabular output are tested, **Then** at least one test validates column order, header text, and one row of data.

---

### User Story 6 - Device, Firmware, and Inventory Managers Un-Omitted (Priority: P6)

Codebase maintainers need the device/firmware/inventory management modules (`arp_command_manager`, `device_reboot_manager`, `firmware_manager`, `org_device_inventory_summary_facade`, `bulk_radius_wlan_config_manager`, `gateway_ha_exporter`, `org_ticket_manager`) removed from the coverage omit list and covered by real unit tests with device-side calls mocked, so state-changing operational code paths are covered by tests that assert the correct API calls are issued without hitting real infrastructure.

**Why this priority**: These modules perform state-changing operations (reboots, firmware upgrades, RADIUS reconfiguration, ticket creation). They require the most careful mocking to avoid accidental live-device calls in CI. Landing them mid-workflow ensures the P2–P3 mock fixtures are stable before this cluster relies on them.

**Independent Test**: After merge, the seven listed omit entries are absent from `pyproject.toml`, each module has dedicated tests with all state-changing calls mocked (or marked `integration`), and `pytest --cov` passes at `fail_under = 90`.

**Acceptance Scenarios**:

1. **Given** the PR branch (or series of PRs) at HEAD, **When** the seven omit lines are searched in `pyproject.toml`, **Then** zero matches remain.
2. **Given** the PR branch at HEAD, **When** the new tests execute in a network-isolated container, **Then** no test issues a real HTTP request, SSH connection, or subprocess to a device (verified by network sandboxing or mock-strict assertions).
3. **Given** the PR branch at HEAD, **When** the coverage report is inspected, **Then** each of the seven un-omitted modules reports coverage of at least 90%.

---

### User Story 7 - SSH and UI Modules Un-Omitted (Priority: P7)

Codebase maintainers need the SSH and TUI modules (`cli_shell_manager`, `tui`) removed from the coverage omit list and covered by real unit tests that mock the SSH transport and TUI rendering surface, so the interactive-terminal code paths stop hiding behind exclusions.

**Why this priority**: SSH and TUI code paths require specialized mocking (paramiko / prompt_toolkit / textual). Landing this after P6's device managers ensures any shared SSH fixtures introduced in P6 are already in place. Small cluster (two modules) so it stays a single PR.

**Independent Test**: After merge, the two listed omit entries are absent from `pyproject.toml`, each module has dedicated tests with SSH and terminal-rendering calls mocked, and `pytest --cov` passes at `fail_under = 90`.

**Acceptance Scenarios**:

1. **Given** the PR branch at HEAD, **When** the two omit lines are searched in `pyproject.toml`, **Then** zero matches remain.
2. **Given** the PR branch at HEAD, **When** the new SSH tests execute, **Then** no test opens a real SSH connection (verified by mocked transport assertions).
3. **Given** the PR branch at HEAD, **When** the new TUI tests execute, **Then** no test opens a real terminal or blocks on user input.

---

### User Story 8 - WebSocket Cluster Un-Omitted (Priority: P8)

Codebase maintainers need the `src/websocket/*` wildcard entry removed from the coverage omit list and every file under `src/websocket/` covered by real unit tests with the async transport and Mist WebSocket protocol mocked, so the async streaming surface reaches the project coverage bar.

**Why this priority**: The WebSocket cluster is the hardest to test cleanly — async transport, long-lived connections, service-ping discovery, and diagnostic subscriptions all live here. Landing it last means every mocking pattern the earlier stories developed (network, subprocess, SSH, TUI) is already available, and this cluster's PR can lean on them. Because the omit line is a wildcard, removing it un-omits every current and future file under `src/websocket/`, so the PR must land tests for all files present at merge time.

**Independent Test**: After merge, `"src/websocket/*"` is absent from `pyproject.toml`, every `.py` file directly under `src/websocket/` (and its subpackages `diagnostics/`, `polling/`) has dedicated tests, and `pytest --cov` passes at `fail_under = 90` with per-file coverage of at least 90% for every file the wildcard previously hid.

**Acceptance Scenarios**:

1. **Given** the PR branch at HEAD, **When** the wildcard omit line is searched in `pyproject.toml`, **Then** zero matches remain.
2. **Given** the PR branch at HEAD, **When** the coverage report is inspected, **Then** every file under `src/websocket/` (recursively) reports coverage of at least 90%.
3. **Given** the PR branch at HEAD, **When** the new WebSocket tests execute, **Then** no test opens a real WebSocket connection to `api.mist.com` or any external host (verified by `unittest.mock` strict-assert usage on the sync `websocket-client` `WebSocketApp` — the transport library imported by `src/websocket/manager.py`), and any long-running polling loop is exercised via at most two mocked iterations.

---

### Edge Cases

- **Coverage regression on an un-omitted module**: If any un-omitted module lands below the project's 90% coverage threshold, the PR must add tests before merge. No `# pragma: no cover` or dummy `import module` tests are permitted to game the gate.
- **Integration-only paths**: If a code path genuinely requires a live Mist API (e.g., WebSocket handshake against a real controller), it is covered via mocked doubles OR marked with the existing `integration` pytest marker. Marking with `integration` counts as tested for coverage purposes if and only if the marker keeps the code path out of the coverage denominator — otherwise the mocked-double route is used.
- **New omit entry appears mid-workflow**: Between the writing of issue #878 (35 named files + `src/websocket/*`) and today, extra files may have been added to the omit list (e.g., `src/analytics/insight_metrics_utils.py`, `src/api/api_core_fetch_utils.py`, `src/cache/cache_utils.py`, `src/export/data_exporter.py`, `src/export/org_site_exporter.py`, `src/ui/prompt_utils.py`). The workflow MUST audit `pyproject.toml` at start and treat the current omit list (minus the six legitimately-non-source entries preserved by the issue's acceptance criteria) as the working set. Delta from the issue's original 35 entries is captured in Assumptions.
- **Merge conflict from CI**: If any PR fails to merge cleanly on main (e.g., because a peer PR landed first), the branch is rebased and re-tested; no `--admin` bypass is used and no merge proceeds unless `mergeStateStatus=CLEAN`.
- **Test file collision**: If a test file for an un-omitted module already exists under `tests/` but is a dummy placeholder (import-only or `pragma: no cover`-wrapped), the PR MUST replace it with real tests, not augment it silently.
- **Refactor temptation**: If, while writing tests, a module is discovered to be untestable without refactoring, the PR MUST NOT refactor the module (per issue #878 non-goals). Instead, open a follow-up issue and defer coverage for that specific module — but retain coverage for the parts that ARE testable, and keep the omit entry removed only if the file still meets the 90% bar. Otherwise, leave the omit entry in place with a `# TODO(1017): refactor pending` comment and open a tracking issue.
- **Stale audit numbers**: The current omit list in `pyproject.toml` differs from the issue body. The workflow refreshes the omit-list snapshot at the start of each PR and uses that as ground truth for the story's scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workflow MUST deliver a series of pull requests, each closing one User Story (P1 through P8), following the ordered sequence P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8. A single User Story MAY be delivered as more than one PR if scope warrants (see FR-013), but no story may be reordered.
- **FR-002**: Each pull request MUST reference the covered User Story in its description and MUST include a `Refs #878` trailer (with `Closes #878` on the final PR of the workflow).
- **FR-003**: The workflow MUST use serial dispatch across stories: pull request(s) for Story N+1 MUST NOT be opened until all pull requests for Story N have landed cleanly on `main`. Within a single story, sub-PRs MAY be opened in parallel if they touch disjoint files.
- **FR-004**: Each pull request MUST originate from its own short-lived branch cut from the current `main` at the moment the PR is opened; the `1017-remove-coverage-omits` feature branch is used ONLY as the coordination home for spec/plan/tasks artifacts, not as the base for delivery PRs.
- **FR-005**: Each pull request MUST pass `black --check` and `ruff check` locally before being pushed to the remote branch (per the "Pre-push black + ruff gate" repo convention).
- **FR-006**: No pull request MUST use administrative merge bypass; each PR MUST wait for `mergeStateStatus=CLEAN` before merging (per the "No `--admin` merge bypass" repo convention).
- **FR-007**: Every module removed from the omit list MUST have at least one dedicated test file under `tests/` that exercises real code paths. Dummy `import module` tests and `# pragma: no cover` wrappers MUST NOT be used to game the coverage gate.
- **FR-008**: After every merged PR in the workflow, `pytest --cov=src --cov-fail-under=90` MUST pass on `main` without lowering `fail_under` and without adding any new omit entry.
- **FR-009**: The workflow MUST NOT modify the fail_under threshold in `pyproject.toml` from its current value of 90.
- **FR-010**: The workflow MUST NOT modify the modules themselves except where a non-cosmetic change is required to make them testable, in which case the change MUST be recorded in the PR body with rationale and MUST be limited to that PR (per issue #878 non-goals; also see the Refactor Temptation edge case).
- **FR-011**: Retained omit entries (`tests/*`, `venv/*`, `.venv/*`, `setup.py`, `*/site-packages/*`, `src/maps/*`) MUST remain in the omit list at the end of the workflow — those are legitimately non-source.
- **FR-012**: Integration-only code paths (real Mist API calls, real device SSH, real WebSocket handshakes) MUST be covered via mocked doubles OR marked with the existing `integration` pytest marker. No live-network call is permitted in the default CI test suite.
- **FR-013**: A single User Story MAY be split into multiple pull requests if the total diff (test code + minimal test-affordance changes) exceeds ~500 net lines added or ~150 fixture lines per module. Sub-PRs of a story MUST land before the workflow advances to the next story.
- **FR-014**: The workflow's coordination artifacts (`specs/1017-remove-coverage-omits/spec.md`, and any follow-up `plan.md` / `tasks.md`) MUST NOT be modified after the first delivery PR opens except to record deltas — no scope creep, no post-hoc story insertion.
- **FR-015**: If a module cannot reach 90% coverage without refactoring (per the Refactor Temptation edge case), the workflow MUST retain that specific omit entry, add a `# TODO(1017): refactor pending` comment, and open a tracking issue that references #878. This exception MUST be documented in the PR body and MUST NOT be used to skip more than 2 modules across the entire workflow.
- **FR-016**: The current omit list in `pyproject.toml` (which contains ~41 entries as of 2026-07-13, slightly more than the 35 named in issue #878) is treated as the authoritative working set. Any file present in `pyproject.toml`'s omit list at workflow start that is NOT in the "legitimately non-source" retained set (FR-011) MUST be un-omitted by the workflow. See Assumptions for the delta.

### Key Entities *(include if feature involves data)*

- **Omit Entry**: A single line in the `[tool.coverage.run].omit` array of `pyproject.toml` that instructs `coverage.py` to exclude a specific file (or, for `src/websocket/*`, a directory tree) from the coverage calculation. In this workflow, each such entry (except the retained non-source entries) is a work item; success is measured by driving the count to zero.
- **Un-Omitted Module**: A Python source file that (a) previously had an omit entry, (b) has had that entry removed by a PR in this workflow, and (c) is now measured by `coverage.py`. Success for an un-omitted module is per-file coverage ≥ 90%.
- **Retained Non-Source Entry**: An omit entry that does NOT map to first-party source under `src/` (or `src/maps/` which is generated). The retained set at workflow start is `{tests/*, venv/*, .venv/*, setup.py, */site-packages/*, src/maps/*}`. These MUST remain in the omit list per FR-011.
- **Integration-Only Path**: A code path inside an un-omitted module that requires a live external resource (Mist API, device SSH, WebSocket handshake to controller). Per FR-012, these are covered by mocks OR marked with the existing `integration` pytest marker.
- **Test Fixture Bundle**: The per-module test scaffolding (JSON fixture files, mock factories, `conftest.py` additions) needed to exercise an un-omitted module. Owned by the story that un-omits that module. Reusable across stories where possible (P4 exporters reuse P3 fetcher mocks, P8 WebSocket tests reuse P6 SSH mock patterns).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After all workflow PRs are merged, the `[tool.coverage.run].omit` array in `pyproject.toml` contains exactly the retained non-source entries `{tests/*, venv/*, .venv/*, setup.py, */site-packages/*, src/maps/*}` and no other entries (verified via `python -c "import tomllib; print(sorted(tomllib.load(open('pyproject.toml', 'rb'))['tool']['coverage']['run']['omit']))"`).
- **SC-002**: GitHub issue #878 is closed by the workflow's final merge, verified by GitHub's issue-linking status on the last PR.
- **SC-003**: `pytest --cov=src --cov-fail-under=90` passes on `main` on every merge commit produced by this workflow, without any lowering of the `fail_under` threshold and without any new omit entry.
- **SC-004**: Every un-omitted module reports per-file coverage of at least 90% on the final merge commit (verified via `coverage report --fail-under=90 --skip-covered`).
- **SC-005**: No pull request in this workflow uses administrative merge bypass — every merge lands with `mergeStateStatus=CLEAN`.
- **SC-006**: No test file added by this workflow contains `# pragma: no cover`, `# type: ignore`, or dummy `import module` statements used purely to reach the 90% bar (verified by lint check on the tests/ diff of each PR).
- **SC-007**: No test added by this workflow issues a live HTTP, WebSocket, or SSH connection during the default CI run (verified by running the suite in a network-isolated container and observing zero external egress, OR by inspecting each new test file for mock usage or `@pytest.mark.integration`).
- **SC-008**: At most 2 modules across the entire workflow invoke the FR-015 refactor-pending escape hatch. If more than 2 modules cannot reach coverage without refactoring, the workflow pauses and the scope is renegotiated via a follow-up issue rather than lowering the bar.
- **SC-009**: The end-to-end elapsed time from opening Story 1's first PR to merging Story 8's final PR is within the team's target of two working months (8 calendar weeks), assuming standard review cadence at approximately one PR per 2–3 working days.
- **SC-010**: The pylint fail-under threshold (9.5) and the coverage fail_under threshold (90) both continue to hold on every merged commit — no gate is lowered anywhere in `pyproject.toml`.

## Assumptions

- The `[tool.coverage.run].omit` list in `pyproject.toml` at workflow start (as of 2026-07-13) contains the 35 entries named in issue #878 plus `src/websocket/*` (matching the issue title "36 excluded modules") AND the following additional entries added between issue creation and today: `src/analytics/insight_metrics_utils.py`, `src/api/api_core_fetch_utils.py`, `src/cache/cache_utils.py`, `src/export/data_exporter.py`, `src/export/org_site_exporter.py`, `src/ui/prompt_utils.py`. Per FR-016, these additional entries are also in scope; they will be folded into the P1–P8 clusters based on module theme (utilities → P1/P2, exporters → P4/P5, API → P3, UI → P7).
- Initiative #1015 (`misthelper-refactor-final-15`) and initiative #1016 (`misthelper-suppression-cleanup`) are complete or nearing completion; no cross-initiative rebase conflicts are expected. Any overlap between a module's refactor PR (from #1015) and its coverage PR (from this workflow) is resolved by landing the refactor first.
- The project's pytest configuration (`pyproject.toml` `[tool.pytest.ini_options]`) already defines the `integration` marker used by FR-012; no marker registration change is required by this workflow.
- The `tests/` directory already contains a `conftest.py` with reusable fixtures for common mocks (mistapi client, sessions, config). This workflow may extend `conftest.py` but does not rewrite it.
- The project's CI pipeline runs `pytest --cov` on every push and enforces `fail_under = 90` as a hard gate. Removing an omit entry without adding sufficient tests will fail CI, which is the desired behavior — no PR merges without honest coverage.
- No consumer of the un-omitted modules depends on their being un-covered — i.e., no downstream code inspects `coverage.py`'s output or the omit list itself.
- Reviewers have capacity to review PRs at roughly one PR per 2–3 working days, matching SC-009's target elapsed time of ~8 calendar weeks for 8+ stories.
- The `tools/refactor_analyzer/` tooling and existing lint/coverage tooling remain functional throughout the workflow; no tooling upgrades are gated on this workflow.
- Any module that turns out to be genuinely dead code (imported nowhere in `src/` after audit) will be handled by a follow-up refactor issue outside this workflow, per issue #878 non-goals. This workflow will keep its omit entry and add a `# TODO(1017): dead code candidate` comment in `pyproject.toml`, then open a tracking issue.
