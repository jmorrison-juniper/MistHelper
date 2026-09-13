# Tasks: Remove Coverage Omit Entries for In-Scope Modules

**Input**: Design documents from `specs/1017-remove-coverage-omits/`

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)

**Tests**: This workflow is fundamentally a test-authoring workflow. Every PR from T-01 through T-08 lands new tests under `tests/unit/` (and optionally `tests/integration/` where a `@pytest.mark.integration` fixture is more accurate than mocks) whose sole purpose is to raise per-module coverage to ≥ 90% BEFORE the corresponding `pyproject.toml` omit entries are deleted. No production module is edited by this workflow; only tests are added and `pyproject.toml` is trimmed.

**Organization**: Tasks are grouped by delivery pull request (T-01 through T-08 map to PR-1 through PR-8, with T-04 split into T-04a/T-04b and T-05 split into T-05a/T-05b to keep each PR reviewable), plus a T-Final workflow-level cleanup and verification PR. Every PR is strictly sequential per FR-003 (SC-008) — PR N+1 does NOT open until PR N is merged. Within a PR, sub-tasks are strictly sequential unless marked `[P]`.

## Format: `[TaskID] [P?] [Story?] Description`

- **[P]**: Can run in parallel with other `[P]` tasks in the same PR (different files/edits, no ordering deps)
- **[Story]**: Which user story this task belongs to (US1–US8, one per PR-family)
- Include exact file paths in descriptions

## Path Conventions

Single-project layout (per `plan.md` Project Structure). All test additions land under `tests/unit/` (or `tests/integration/` where explicitly noted). The final PR (T-Final) edits `pyproject.toml` only. No production `src/` module is modified by this workflow (FR-010).

Delta modules (in-scope but not enumerated in spec.md § User Stories at plan time, mapped per FR-016):

- `src/analytics/insight_metrics_utils.py` → P3 (analytics/API cluster)
- `src/api/api_core_fetch_utils.py` → P3 (API cluster)
- `src/cache/cache_utils.py` → P3 (API-adjacent)
- `src/export/data_exporter.py` → P2 (export helper)
- `src/export/org_site_exporter.py` → P4 (org exporter cluster, PR-4a)
- `src/ui/prompt_utils.py` → P7 (UI cluster)

---

## PR-0: Phase 0/1 Design Artifacts (Priority: P0 — prerequisite for PR-1)

**Goal**: Create the six Phase 0/1 deliverables enumerated in `plan.md` § File Structure and § Phase 0/1 so PR-1 opens against a complete design record. This PR touches only `specs/1017-remove-coverage-omits/` — no `src/`, `tests/`, or `pyproject.toml` edits.

**Target artifacts**:

- `specs/1017-remove-coverage-omits/research.md` (Phase 0 output — omit-list audit, `src/websocket/*` file enumeration, per-cluster mocking decisions, fixture-migration order)
- `specs/1017-remove-coverage-omits/data-model.md` (Phase 1 — per-module test manifest, retained non-source inventory, integration-only path inventory, fixture registry)
- `specs/1017-remove-coverage-omits/contracts/shared_fixtures.md` (fixture shape + tier contracts per plan.md Decision 1)
- `specs/1017-remove-coverage-omits/contracts/coverage_assertion.md` (per-file + full-suite coverage invocations)
- `specs/1017-remove-coverage-omits/contracts/mocking_conventions.md` (`MagicMock(spec=…)` rules for mistapi/paramiko/`websocket-client`)
- `specs/1017-remove-coverage-omits/quickstart.md` (per-story verification recipes P1–P8)

**Estimated PR size**: docs-only; ~500–900 net lines across six new markdown files under `specs/1017-remove-coverage-omits/`. No `pyproject.toml` diff.

**Independent Test**: `ls specs/1017-remove-coverage-omits/` shows `research.md`, `data-model.md`, `quickstart.md`, and a `contracts/` directory containing `shared_fixtures.md`, `coverage_assertion.md`, `mocking_conventions.md`; every file references the exact same 6-entry retained non-source omit set (SC-001) and 90% coverage threshold (SC-003); `research.md` records a snapshot of `pyproject.toml [tool.coverage.run].omit` as it exists at PR-0 branch-cut time.

- [ ] T-00.1 [US0] Branch: `git switch main && git pull && git switch -c coverage-omits-p0-design-artifacts-1017`.
- [ ] T-00.2 [US0] Author `research.md`: refresh the omit-list audit at current `main` HEAD; enumerate the 35 in-scope + 6 retained entries; enumerate every `.py` file under `src/websocket/`, `src/websocket/diagnostics/`, `src/websocket/polling/` (bounds P8); record per-cluster mocking-library choices (mistapi, `websocket-client` sync + threading, paramiko, no sqlite3); record fixture-migration order for `mock_mistapi_session`, `mock_config`, `mock_websocket_transport`.
- [ ] T-00.3 [US0] Author `data-model.md`: for each of the 35 in-scope modules, record target test file path, external touch points, expected fixture bundle location; enumerate retained non-source entries verbatim from FR-011; enumerate integration-only paths with mock-vs-`@pytest.mark.integration` decision + reason.
- [ ] T-00.4 [US0] Author `contracts/shared_fixtures.md`, `contracts/coverage_assertion.md`, `contracts/mocking_conventions.md` per plan.md Phase 1 § 2 (create the `contracts/` directory first). Each contract file MUST include an explicit `Validation rule:` line so reviewers can grep for it.
- [ ] T-00.5 [US0] Author `quickstart.md`: per-story verification recipes (P1–P8) with exact `grep` + `pytest --cov=… --cov-fail-under=90` invocations; include the `podman run --network=none` recipe for SC-007 verification (per plan.md line 286).
- [ ] T-00.6 [US0] Verify locally: `ls specs/1017-remove-coverage-omits/contracts/` shows the three contract files; `grep -l "SC-001" specs/1017-remove-coverage-omits/*.md specs/1017-remove-coverage-omits/contracts/*.md` returns every new file; no formatter/lint gates apply (docs-only PR).
- [ ] T-00.7 [US0] Commit + push: stage the six new files; commit body cites `Refs #878` and plan.md § Phase 0 / § Phase 1; push the `coverage-omits-p0-design-artifacts-1017` branch.
- [ ] T-00.8 [US0] Open PR with `Refs #878` trailer (intermediate PR — no code changes to gate CI failures) via `gh pr create --base main --head coverage-omits-p0-design-artifacts-1017`.
- [ ] T-00.9 [US0] Wait for CI + `mergeStateStatus=CLEAN`; arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-00.10 [US0] Confirm merged; branch deleted. PR-1 is now unblocked.

**Checkpoint**: Phase 0/1 design artifacts merged to `main`. Every downstream PR (T-01…T-Final) can cite `research.md`, `data-model.md`, and the three contract files as authoritative.

---

## PR-1: Issue #878 — P1 utility modules coverage (Priority: P1) 🎯 MVP

**Goal**: Author tests to reach ≥ 90% coverage on the 4 P1 utility modules and delete their omit entries from `pyproject.toml`.

**Target modules**:

- `src/utils/environment_utils.py`
- `src/utils/filter_operator_engine.py`
- `src/troubleshooting/troubleshoot_utils.py`
- `src/input/prompt_client_utils.py`

**Estimated PR size**: ~4–8 new test files under `tests/unit/`, ~800–1500 net lines added. `pyproject.toml` diff: −4 lines.

**Independent Test**: After merge, `pytest --cov=src/utils/environment_utils --cov=src/utils/filter_operator_engine --cov=src/troubleshooting/troubleshoot_utils --cov=src/input/prompt_client_utils --cov-report=term-missing --cov-fail-under=90` passes; the four corresponding lines are absent from `[tool.coverage.run].omit` in `pyproject.toml`; repo-wide `pytest --cov` still reports total coverage ≥ 90%.

- [ ] T-01.1 [US1] Audit: run `pytest --cov=src/utils/environment_utils --cov=src/utils/filter_operator_engine --cov=src/troubleshooting/troubleshoot_utils --cov=src/input/prompt_client_utils --cov-report=term-missing --no-cov-on-fail` with the omit entries temporarily commented out locally to establish the current per-module coverage baseline; record numbers in the PR body (do NOT commit the commented pyproject).
- [ ] T-01.2 [US1] Branch: run `git switch main && git pull && git switch -c coverage-omits-p1-utilities-878` from repo root.
- [ ] T-01.3 [US1] Author tests under `tests/unit/utils/` and `tests/unit/troubleshooting/` and `tests/unit/input/`: create `test_environment_utils.py`, `test_filter_operator_engine.py`, `test_troubleshoot_utils.py`, and `test_prompt_client_utils.py`. Use `unittest.mock.MagicMock(spec=...)` for external SDK objects (mistapi client, filesystem), `monkeypatch` for environment variables and stdin prompts, and `@pytest.mark.integration` for any test that must call the real Mist API (guarded by `.env` credentials). Aim for ≥ 90% per-module line coverage; document any legitimately unreachable branches with `# pragma: no cover` INLINE (not by re-adding to omit).
- [ ] T-01.4 [US1] Remove omit entries in `pyproject.toml`: delete the four lines `"src/troubleshooting/troubleshoot_utils.py"`, `"src/input/prompt_client_utils.py"`, `"src/utils/environment_utils.py"`, `"src/utils/filter_operator_engine.py"` from `[tool.coverage.run].omit`. No other pyproject edits (FR-009, FR-011).
- [ ] T-01.5 [US1] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`, then `mypy` on any test helpers. Confirm the four modules now appear in the coverage report and each is at ≥ 90%; confirm repo-wide total ≥ 90%. If a per-module target is below 90% and cannot be met without touching production code, halt and evaluate FR-015 escape hatch (max 2 modules total across the workflow).
- [ ] T-01.6 [US1] Commit + push: stage `tests/unit/utils/`, `tests/unit/troubleshooting/`, `tests/unit/input/`, and `pyproject.toml`; commit with a body reporting pre/post per-module coverage numbers; push the `coverage-omits-p1-utilities-878` branch to remote.
- [ ] T-01.7 [US1] Open PR with `Refs #878` trailer (intermediate PR — the tracking issue closes only after T-Final) using `gh pr create --base main --head coverage-omits-p1-utilities-878`; include per-module coverage numbers and the pyproject diff in the PR body per plan.md Decision 2.
- [ ] T-01.8 [US1] Wait for CI + `mergeStateStatus=CLEAN`: poll `gh pr view <N> --json mergeStateStatus,statusCheckRollup` until state is CLEAN and all required checks are SUCCESS.
- [ ] T-01.9 [US1] Arm auto-merge and land: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch` (no `--admin` bypass under any circumstance per FR-006).
- [ ] T-01.10 [US1] Confirm merged: `gh pr view <N> --json state,mergeCommit` returns `MERGED`; the P1 tracking issue is closed by GitHub auto-close; branch `coverage-omits-p1-utilities-878` is deleted on remote.

**Checkpoint**: 4 P1 utility modules are covered ≥ 90% and removed from the omit list.

---

## PR-2: Issue #TBD — P2 export helper coverage (Priority: P2)

**Goal**: Author tests to reach ≥ 90% coverage on the P2 export helper modules and delete their omit entries.

**Target modules**:

- `src/export/org_export_utils.py`
- `src/export/license_export_utils.py`
- `src/export/const_definitions_exporter.py`
- `src/export/gateway_test_exporter.py`
- `src/export/data_exporter.py` (delta from FR-016)

**Estimated PR size**: ~5–8 new test files under `tests/unit/export/`, ~1000–1800 net lines added. `pyproject.toml` diff: −5 lines.

**Independent Test**: After merge, `pytest --cov=src/export/org_export_utils --cov=src/export/license_export_utils --cov=src/export/const_definitions_exporter --cov=src/export/gateway_test_exporter --cov=src/export/data_exporter --cov-report=term-missing --cov-fail-under=90` passes; the five corresponding lines are absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%.

- [ ] T-02.1 [US2] Audit: run coverage locally with the five omit lines temporarily commented out; record per-module baseline in PR body.
- [ ] T-02.2 [US2] Branch: run `git switch main && git pull && git switch -c coverage-omits-p2-export-helpers`.
- [ ] T-02.3 [US2] Author tests under `tests/unit/export/`: create `test_org_export_utils.py`, `test_license_export_utils.py`, `test_const_definitions_exporter.py`, `test_gateway_test_exporter.py`, `test_data_exporter.py`. Reuse shared fixtures where the exporters share JSON/CSV writer patterns; use `tmp_path` for filesystem writes; mock `mistapi` client with `MagicMock(spec=mistapi.APISession)`. Land ≥ 90% per-module line coverage.
- [ ] T-02.4 [US2] Remove the five omit entries from `pyproject.toml`: `"src/export/const_definitions_exporter.py"`, `"src/export/data_exporter.py"`, `"src/export/gateway_test_exporter.py"`, `"src/export/license_export_utils.py"`, `"src/export/org_export_utils.py"`.
- [ ] T-02.5 [US2] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`; confirm the five modules appear at ≥ 90% and repo total ≥ 90%.
- [ ] T-02.6 [US2] Commit + push: stage `tests/unit/export/` additions and `pyproject.toml`; commit with pre/post coverage; push the branch.
- [ ] T-02.7 [US2] Open PR with `Refs #<P2-issue>` trailer (intermediate PR) via `gh pr create --base main --head coverage-omits-p2-export-helpers`; include coverage numbers and pyproject diff per plan.md Decision 2.
- [ ] T-02.8 [US2] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-02.9 [US2] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-02.10 [US2] Confirm merged, P2 issue closed, branch deleted.

**Checkpoint**: 5 P2 export helper modules are covered ≥ 90% and removed from the omit list.

---

## PR-3: Issue #TBD — P3 API/DB/analytics coverage (Priority: P3)

**Goal**: Author tests to reach ≥ 90% coverage on the P3 API-adjacent modules and delete their omit entries.

**Target modules**:

- `src/api/api_data_fetcher.py`
- `src/api/api_fetch_utils.py`
- `src/api/api_core_fetch_utils.py` (delta)
- `src/cache/cache_utils.py` (delta)
- `src/db/database_schema_utils.py`
- `src/analytics/data_collection_manager.py`
- `src/analytics/insight_metrics_utils.py` (delta)

**Estimated PR size**: ~7–10 new test files under `tests/unit/api/`, `tests/unit/cache/`, `tests/unit/db/`, `tests/unit/analytics/`. ~1500–2500 net lines added. `pyproject.toml` diff: −7 lines. If the API cluster proves too large for a single reviewable PR, split into T-03a (`api_*`, `cache_utils`) and T-03b (`db/analytics`) — allowed by plan.md Complexity Table Row P3 (1–2 sub-PRs).

**Independent Test**: After merge, `pytest --cov=src/api --cov=src/cache/cache_utils --cov=src/db/database_schema_utils --cov=src/analytics/data_collection_manager --cov=src/analytics/insight_metrics_utils --cov-fail-under=90` passes; the seven corresponding lines are absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%.

- [ ] T-03.1 [US3] Audit: run coverage locally with the seven omit lines commented out; record per-module baseline.
- [ ] T-03.2 [US3] Branch: `git switch main && git pull && git switch -c coverage-omits-p3-api-db-analytics`.
- [ ] T-03.3 [US3] Author tests: create `tests/unit/api/test_api_data_fetcher.py`, `test_api_fetch_utils.py`, `test_api_core_fetch_utils.py`; `tests/unit/cache/test_cache_utils.py`; `tests/unit/db/test_database_schema_utils.py`; `tests/unit/analytics/test_data_collection_manager.py`, `test_insight_metrics_utils.py`. Mock `python-arango` and `redis` clients with `MagicMock(spec=...)`; use `pytest.fixture` for reusable mistapi session fixtures; add a shared `conftest.py` under `tests/unit/api/` for the API session mock if two or more tests need it.
- [ ] T-03.4 [US3] Remove the seven omit entries from `pyproject.toml`: `"src/analytics/data_collection_manager.py"`, `"src/analytics/insight_metrics_utils.py"`, `"src/api/api_data_fetcher.py"`, `"src/api/api_fetch_utils.py"`, `"src/api/api_core_fetch_utils.py"`, `"src/cache/cache_utils.py"`, `"src/db/database_schema_utils.py"`.
- [ ] T-03.5 [US3] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`; confirm ≥ 90% per module and repo total ≥ 90%.
- [ ] T-03.6 [US3] Commit + push: stage `tests/unit/api/`, `tests/unit/cache/`, `tests/unit/db/`, `tests/unit/analytics/` additions and `pyproject.toml`; push branch.
- [ ] T-03.7 [US3] Open PR with `Refs #<P3-issue>` trailer (intermediate PR) via `gh pr create --base main --head coverage-omits-p3-api-db-analytics`; include coverage numbers per plan.md Decision 2. If the PR exceeds ~2500 lines, split into T-03a (branch `coverage-omits-p3a-api-cache`) and T-03b (branch `coverage-omits-p3b-db-analytics`) — merge T-03a fully (CI green + branch deleted) before opening T-03b.
- [ ] T-03.8 [US3] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-03.9 [US3] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-03.10 [US3] Confirm merged, P3 issue closed, branch deleted.

**Checkpoint**: 7 P3 API/DB/analytics modules are covered ≥ 90% and removed from the omit list.

---

## PR-4a: Issue #TBD — P4 org exporters (part 1: stats + templates + admin) (Priority: P4)

**Goal**: Author tests for the first half of the P4 org-exporter cluster and delete those omit entries.

**Target modules**:

- `src/export/org_device_stats_exporter.py`
- `src/export/org_template_exporter.py`
- `src/export/org_admin_exporter.py`

**Estimated PR size**: ~3–5 new test files under `tests/unit/export/`, ~800–1400 net lines. `pyproject.toml` diff: −3 lines.

**Independent Test**: After merge, `pytest --cov=src/export/org_device_stats_exporter --cov=src/export/org_template_exporter --cov=src/export/org_admin_exporter --cov-fail-under=90` passes; the three corresponding lines are absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%. The remaining P4 org exporters are still omitted and will be picked up by PR-4b.

- [ ] T-04a.1 [US4] Audit: run coverage locally with the three omit lines commented out; record baseline.
- [ ] T-04a.2 [US4] Branch: `git switch main && git pull && git switch -c coverage-omits-p4a-org-stats-templates-admin`.
- [ ] T-04a.3 [US4] Author tests under `tests/unit/export/`: `test_org_device_stats_exporter.py`, `test_org_template_exporter.py`, `test_org_admin_exporter.py`. Introduce a shared `tests/unit/export/conftest.py` fixture set for `mistapi.APISession` mock, sample org payloads, and `tmp_path` output paths — this fixture MUST be shared with PR-4b/PR-5a/PR-5b to keep future exporter tests DRY.
- [ ] T-04a.4 [US4] Remove the three omit entries: `"src/export/org_admin_exporter.py"`, `"src/export/org_device_stats_exporter.py"`, `"src/export/org_template_exporter.py"`.
- [ ] T-04a.5 [US4] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`.
- [ ] T-04a.6 [US4] Commit + push: stage `tests/unit/export/` additions (including `conftest.py`) and `pyproject.toml`; push branch.
- [ ] T-04a.7 [US4] Open PR with `Closes #<P4a-issue>` trailer via `gh pr create --base main --head coverage-omits-p4a-org-stats-templates-admin`; note in PR body that a shared `conftest.py` was introduced and will be reused by PR-4b/PR-5a/PR-5b.
- [ ] T-04a.8 [US4] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-04a.9 [US4] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-04a.10 [US4] Confirm merged, P4a issue closed, branch deleted.

**Checkpoint**: 3 org exporters covered ≥ 90% and removed from omit list; shared `tests/unit/export/conftest.py` fixture library is in place.

---

## PR-4b: Issue #TBD — P4 org exporters (part 2: config + alarms + client-security + sites) (Priority: P4)

**Goal**: Complete the P4 org-exporter cluster by covering the remaining four modules.

**Target modules**:

- `src/export/org_config_exporter.py`
- `src/export/org_alarm_event_exporter.py`
- `src/export/org_client_security_exporter.py`
- `src/export/org_site_exporter.py` (delta)

**Estimated PR size**: ~4–6 new test files under `tests/unit/export/`, ~1000–1600 net lines. `pyproject.toml` diff: −4 lines.

**Independent Test**: After merge, `pytest --cov=src/export/org_config_exporter --cov=src/export/org_alarm_event_exporter --cov=src/export/org_client_security_exporter --cov=src/export/org_site_exporter --cov-fail-under=90` passes; the four corresponding lines are absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%.

- [ ] T-04b.1 [US4] Audit: coverage baseline with the four omit lines commented out.
- [ ] T-04b.2 [US4] Branch: `git switch main && git pull && git switch -c coverage-omits-p4b-org-config-alarms-security-sites`.
- [ ] T-04b.3 [US4] Author tests: `tests/unit/export/test_org_config_exporter.py`, `test_org_alarm_event_exporter.py`, `test_org_client_security_exporter.py`, `test_org_site_exporter.py`. Reuse `tests/unit/export/conftest.py` from PR-4a for the `mistapi.APISession` mock and shared payload fixtures.
- [ ] T-04b.4 [US4] Remove the four omit entries: `"src/export/org_alarm_event_exporter.py"`, `"src/export/org_client_security_exporter.py"`, `"src/export/org_config_exporter.py"`, `"src/export/org_site_exporter.py"`.
- [ ] T-04b.5 [US4] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`.
- [ ] T-04b.6 [US4] Commit + push.
- [ ] T-04b.7 [US4] Open PR with `Closes #<P4b-issue>` trailer via `gh pr create --base main --head coverage-omits-p4b-org-config-alarms-security-sites`.
- [ ] T-04b.8 [US4] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-04b.9 [US4] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-04b.10 [US4] Confirm merged, P4b issue closed, branch deleted.

**Checkpoint**: All 7 P4 org exporters (3 from PR-4a + 4 from PR-4b) are covered ≥ 90% and removed from the omit list.

---

## PR-5a: Issue #TBD — P5 site exporters (Priority: P5)

**Goal**: Author tests for the site-exporter half of P5 and delete those omit entries.

**Target modules**:

- `src/export/site_anomaly_exporter.py`
- `src/export/site_config_exporter.py`
- `src/export/site_device_exporter.py`
- `src/export/sites_by_ap_model_exporter.py`
- `src/gateway/gateway_ha_exporter.py`

**Estimated PR size**: ~5–7 new test files under `tests/unit/export/` and `tests/unit/gateway/`, ~1200–1800 net lines. `pyproject.toml` diff: −5 lines.

**Independent Test**: After merge, `pytest --cov=src/export/site_anomaly_exporter --cov=src/export/site_config_exporter --cov=src/export/site_device_exporter --cov=src/export/sites_by_ap_model_exporter --cov=src/gateway/gateway_ha_exporter --cov-fail-under=90` passes; the five lines are absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%.

- [ ] T-05a.1 [US5] Audit: coverage baseline with the five omit lines commented out.
- [ ] T-05a.2 [US5] Branch: `git switch main && git pull && git switch -c coverage-omits-p5a-site-exporters`.
- [ ] T-05a.3 [US5] Author tests: `tests/unit/export/test_site_anomaly_exporter.py`, `test_site_config_exporter.py`, `test_site_device_exporter.py`, `test_sites_by_ap_model_exporter.py`; `tests/unit/gateway/test_gateway_ha_exporter.py`. Reuse `tests/unit/export/conftest.py` for shared session/payload fixtures; add a `tests/unit/gateway/conftest.py` if a gateway-specific mock is needed.
- [ ] T-05a.4 [US5] Remove the five omit entries: `"src/export/site_anomaly_exporter.py"`, `"src/export/site_config_exporter.py"`, `"src/export/site_device_exporter.py"`, `"src/export/sites_by_ap_model_exporter.py"`, `"src/gateway/gateway_ha_exporter.py"`.
- [ ] T-05a.5 [US5] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`.
- [ ] T-05a.6 [US5] Commit + push.
- [ ] T-05a.7 [US5] Open PR with `Closes #<P5a-issue>` trailer via `gh pr create --base main --head coverage-omits-p5a-site-exporters`.
- [ ] T-05a.8 [US5] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-05a.9 [US5] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-05a.10 [US5] Confirm merged, P5a issue closed, branch deleted.

**Checkpoint**: 5 site exporters (+ gateway HA exporter) covered ≥ 90% and removed from the omit list.

---

## PR-5b: Issue #TBD — P5 reporters + inventory facade (Priority: P5)

**Goal**: Author tests for the reporter/inventory half of P5 and delete those omit entries.

**Target modules**:

- `src/reports/global_wired_client_report_generator.py`
- `src/reports/offline_device_reporter.py`
- `src/reports/sfp_transceiver_data_processor.py`
- `src/reports/wired_client_manufacturer_report_generator.py`
- `src/inventory/org_device_inventory_summary_facade.py`

**Estimated PR size**: ~5–7 new test files under `tests/unit/reports/` and `tests/unit/inventory/`, ~1200–1800 net lines. `pyproject.toml` diff: −5 lines.

**Independent Test**: After merge, `pytest --cov=src/reports/global_wired_client_report_generator --cov=src/reports/offline_device_reporter --cov=src/reports/sfp_transceiver_data_processor --cov=src/reports/wired_client_manufacturer_report_generator --cov=src/inventory/org_device_inventory_summary_facade --cov-fail-under=90` passes; the five lines are absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%.

- [ ] T-05b.1 [US5] Audit: coverage baseline with the five omit lines commented out.
- [ ] T-05b.2 [US5] Branch: `git switch main && git pull && git switch -c coverage-omits-p5b-reports-inventory`.
- [ ] T-05b.3 [US5] Author tests: `tests/unit/reports/test_global_wired_client_report_generator.py`, `test_offline_device_reporter.py`, `test_sfp_transceiver_data_processor.py`, `test_wired_client_manufacturer_report_generator.py`; `tests/unit/inventory/test_org_device_inventory_summary_facade.py`. Mock `prettytable` output where needed; verify sort/filter logic with parametrized cases.
- [ ] T-05b.4 [US5] Remove the five omit entries: `"src/reports/global_wired_client_report_generator.py"`, `"src/reports/offline_device_reporter.py"`, `"src/reports/sfp_transceiver_data_processor.py"`, `"src/reports/wired_client_manufacturer_report_generator.py"`, `"src/inventory/org_device_inventory_summary_facade.py"`.
- [ ] T-05b.5 [US5] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`.
- [ ] T-05b.6 [US5] Commit + push.
- [ ] T-05b.7 [US5] Open PR with `Closes #<P5b-issue>` trailer via `gh pr create --base main --head coverage-omits-p5b-reports-inventory`.
- [ ] T-05b.8 [US5] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-05b.9 [US5] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-05b.10 [US5] Confirm merged, P5b issue closed, branch deleted.

**Checkpoint**: 5 report generators + inventory facade covered ≥ 90% and removed from the omit list. All P5 modules are now fully covered.

---

## PR-6: Issue #TBD — P6 device/firmware/inventory managers (Priority: P6)

**Goal**: Author tests for the P6 state-changing device managers. Because these modules perform destructive actions (reboots, firmware pushes, ARP-cache clears, ticket writes), tests MUST NOT mutate real infrastructure. Every state-changing path is exercised through `unittest.mock.MagicMock(spec=mistapi.APISession)` and asserts on outbound call arguments; any test that requires a real device must be gated with `@pytest.mark.integration` and skipped by default.

**Target modules**:

- `src/device/arp_command_manager.py`
- `src/device/device_reboot_manager.py`
- `src/firmware/firmware_manager.py`
- `src/site/bulk_radius_wlan_config_manager.py`
- `src/org/org_ticket_manager.py`

Note: `src/reports/offline_device_reporter.py` and `src/inventory/org_device_inventory_summary_facade.py` from spec.md's P6 list are picked up by PR-5b (report/inventory cluster) to keep P6 focused on state-changing modules per Constitution Principle III.

**Estimated PR size**: ~5–8 new test files under `tests/unit/device/`, `tests/unit/firmware/`, `tests/unit/site/`, `tests/unit/org/`. ~1500–2400 net lines. `pyproject.toml` diff: −5 lines. If reviewer feedback finds this PR too large, split into T-06a (device/firmware) and T-06b (site/org) — allowed by plan.md Complexity Table Row P6 (2–3 sub-PRs).

**Independent Test**: After merge, `pytest --cov=src/device/arp_command_manager --cov=src/device/device_reboot_manager --cov=src/firmware/firmware_manager --cov=src/site/bulk_radius_wlan_config_manager --cov=src/org/org_ticket_manager --cov-fail-under=90` passes; the five lines are absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%. No test writes to a real Mist org (verified by grepping test files for `@pytest.mark.integration` and confirming every real-API test is gated).

- [ ] T-06.1 [US6] Audit: coverage baseline with the five omit lines commented out. In the PR body, explicitly enumerate every outbound state-changing API call each module makes (Constitution Principle III artifact) and confirm each is mocked in the new tests.
- [ ] T-06.2 [US6] Branch: `git switch main && git pull && git switch -c coverage-omits-p6-state-changing-managers`.
- [ ] T-06.3 [US6] Author tests: `tests/unit/device/test_arp_command_manager.py`, `test_device_reboot_manager.py`; `tests/unit/firmware/test_firmware_manager.py`; `tests/unit/site/test_bulk_radius_wlan_config_manager.py`; `tests/unit/org/test_org_ticket_manager.py`. For each destructive method (reboot, firmware upgrade, ARP clear, ticket write, config bulk-apply), assert (a) the correct mistapi method is called with the correct arguments, (b) confirmation prompts route through a mockable dependency (never `input()` directly in the test path), (c) dry-run/simulate paths do NOT call the destructive API. Add `@pytest.mark.integration` markers for any test that requires a live device; keep default `pytest` runs skipping them.
- [ ] T-06.4 [US6] Remove the five omit entries: `"src/device/arp_command_manager.py"`, `"src/device/device_reboot_manager.py"`, `"src/firmware/firmware_manager.py"`, `"src/site/bulk_radius_wlan_config_manager.py"`, `"src/org/org_ticket_manager.py"`.
- [ ] T-06.5 [US6] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90` — MUST pass without needing `-m "not integration"`; run `rtk pytest -m integration` separately if `.env` credentials are set locally.
- [ ] T-06.6 [US6] Commit + push.
- [ ] T-06.7 [US6] Open PR with `Closes #<P6-issue>` trailer via `gh pr create --base main --head coverage-omits-p6-state-changing-managers`; include the Constitution Principle III artifact from T-06.1 in the PR body.
- [ ] T-06.8 [US6] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-06.9 [US6] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-06.10 [US6] Confirm merged, P6 issue closed, branch deleted.

**Checkpoint**: 5 P6 state-changing managers are covered ≥ 90% (unit-mocked, no live-infra mutation) and removed from the omit list.

---

## PR-7: Issue #TBD — P7 SSH + TUI + prompt (Priority: P7)

**Goal**: Author tests to reach ≥ 90% coverage on the SSH shell/TUI/prompt cluster. Because `cli_shell_manager.py` and `tui.py` rely on interactive terminal state (pyte, sshkeyboard, tqdm), tests must mock the terminal-emulator surface via `MagicMock(spec=pyte.Screen)` and drive keystroke sequences through fixtures. If SSH shell coverage cannot reach 90% without touching production code, this module is a candidate for FR-015 escape hatch (retain omit + `# TODO(1017): refactor pending` annotation) — max 2 modules across the whole workflow.

**Target modules**:

- `src/ssh/cli_shell_manager.py`
- `src/ui/tui.py`
- `src/ui/prompt_utils.py` (delta)

**Estimated PR size**: ~3–6 new test files under `tests/unit/ssh/` and `tests/unit/ui/`, ~800–1600 net lines. `pyproject.toml` diff: −3 lines (or −2 if FR-015 escape hatch is invoked on `cli_shell_manager` or `tui`).

**Independent Test**: After merge, `pytest --cov=src/ssh/cli_shell_manager --cov=src/ui/tui --cov=src/ui/prompt_utils --cov-fail-under=90` passes for every module not covered by FR-015 escape hatch; the corresponding lines are absent from `[tool.coverage.run].omit` (unless retained under FR-015 with the required `# TODO(1017): refactor pending` inline comment); repo-wide coverage ≥ 90%.

- [ ] T-07.1 [US7] Audit: coverage baseline with the three omit lines commented out. If a module's realistic ceiling is < 80%, document the reason and mark it as an FR-015 candidate in the PR body; consumption of the 2-module escape-hatch budget MUST be explicitly noted.
- [ ] T-07.2 [US7] Branch: `git switch main && git pull && git switch -c coverage-omits-p7-ssh-tui-prompt`.
- [ ] T-07.3 [US7] Author tests: `tests/unit/ssh/test_cli_shell_manager.py`; `tests/unit/ui/test_tui.py`, `test_prompt_utils.py`. Mock `pyte.Screen`, `sshkeyboard.listen_keyboard`, and `tqdm` via `MagicMock(spec=...)`; drive keystroke sequences through parametrized fixtures; use `capsys` for stdout assertions on TUI rendering. For `prompt_utils.py`, `monkeypatch.setattr('builtins.input', ...)` to inject prompt responses.
- [ ] T-07.4 [US7] Remove the three omit entries: `"src/ssh/cli_shell_manager.py"`, `"src/ui/tui.py"`, `"src/ui/prompt_utils.py"` — unless FR-015 escape hatch was invoked on one of them (see T-07.1). In the escape-hatch case, leave that specific line in `pyproject.toml` but add a `# TODO(1017): refactor pending — see #<issue>` comment on the same line and open a follow-up refactor issue linked from the PR body.
- [ ] T-07.5 [US7] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90`.
- [ ] T-07.6 [US7] Commit + push.
- [ ] T-07.7 [US7] Open PR with `Closes #<P7-issue>` trailer via `gh pr create --base main --head coverage-omits-p7-ssh-tui-prompt`; if FR-015 was invoked, include the escape-hatch justification and the follow-up refactor issue link in the PR body.
- [ ] T-07.8 [US7] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-07.9 [US7] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-07.10 [US7] Confirm merged, P7 issue closed, branch deleted; if FR-015 was invoked, confirm the follow-up refactor issue is open and linked.

**Checkpoint**: SSH shell + TUI + prompt modules are covered ≥ 90% (or ≤ 2 total FR-015 escape-hatch entries remain, each with a `# TODO(1017): refactor pending` marker and a follow-up refactor issue).

---

## PR-8: Issue #TBD — P8 websocket wildcard expansion (Priority: P8)

**Goal**: Replace the `src/websocket/*` wildcard omit entry with per-file coverage for every websocket module. Because the websocket subsystem contains ~14 files organized under `src/websocket/`, `src/websocket/diagnostics/`, and `src/websocket/polling/`, this PR is the largest of the workflow and MAY split into 2–4 sub-PRs (plan.md Complexity Table Row P8 permits it). Sub-PR splits are recommended along subpackage boundaries.

**Target files** (enumerated from `ls src/websocket/`):

- `src/websocket/__init__.py`
- `src/websocket/commands.py`
- `src/websocket/context.py`
- `src/websocket/manager.py`
- `src/websocket/service_ping_discovery.py`
- `src/websocket/service_ping_manager.py`
- `src/websocket/diagnostics/__init__.py`
- `src/websocket/diagnostics/arp_executor.py`
- `src/websocket/diagnostics/common.py`
- `src/websocket/diagnostics/ping_executor.py`
- `src/websocket/polling/__init__.py`
- `src/websocket/polling/completion_detector.py`
- `src/websocket/polling/message_router.py`
- `src/websocket/polling/result_collector.py`
- `src/websocket/polling/result_combiner.py`

**Estimated PR size**: If shipped as one PR: ~14 new test files under `tests/unit/websocket/`, `tests/unit/websocket/diagnostics/`, `tests/unit/websocket/polling/`; ~3000–5000 net lines. If split (recommended): PR-8a = `src/websocket/` top-level, PR-8b = `diagnostics/`, PR-8c = `polling/`. `pyproject.toml` diff: −1 wildcard line, +0 (or leave the wildcard until every module is covered, whichever is safer).

**Recommended split** (from plan.md Decision 5, Risk Register — websocket is the flagship refactor candidate):

- **PR-8a**: `src/websocket/` top-level (`commands.py`, `context.py`, `manager.py`, `service_ping_discovery.py`, `service_ping_manager.py`, `__init__.py`) — 6 files
- **PR-8b**: `src/websocket/diagnostics/` (`arp_executor.py`, `common.py`, `ping_executor.py`, `__init__.py`) — 4 files
- **PR-8c**: `src/websocket/polling/` (`completion_detector.py`, `message_router.py`, `result_collector.py`, `result_combiner.py`, `__init__.py`) — 5 files
- **PR-8d** (only if needed): remove the `src/websocket/*` wildcard from `pyproject.toml` after all three sub-PRs land; this may fold into PR-8c's pyproject edit if all coverage is green.

Each sub-PR MUST be merged fully (branch deleted, issue closed) before the next opens. Within each sub-PR, the wildcard entry stays in `pyproject.toml` until PR-8c (or PR-8d) — the omit is only removed once every websocket module is at ≥ 90%.

**Independent Test**: After the final sub-PR merges, `pytest --cov=src/websocket --cov-fail-under=90` passes; the line `"src/websocket/*"` is absent from `[tool.coverage.run].omit`; repo-wide coverage ≥ 90%. If any websocket module cannot reach 90% and FR-015 escape hatch was already spent on P7, halt and refactor — do NOT re-introduce the wildcard.

- [ ] T-08.1 [US8] Audit: enumerate every file under `src/websocket/` via `find src/websocket -name '*.py' -type f | sort` and record the count in the PR body (expected: 14 excluding `__init__.py` shims). Run coverage locally with the `"src/websocket/*"` line commented out to establish per-file baselines.
- [ ] T-08.2 [US8] Branch (sub-PR-8a): `git switch main && git pull && git switch -c coverage-omits-p8a-websocket-toplevel`.
- [ ] T-08.3 [US8] Author tests under `tests/unit/websocket/`: `test_commands.py`, `test_context.py`, `test_manager.py`, `test_service_ping_discovery.py`, `test_service_ping_manager.py`. Mock `websocket-client` (`websocket.WebSocketApp`) with `MagicMock(spec=websocket.WebSocketApp)`; drive incoming-message sequences through fixtures that invoke the reader-thread callback directly; use `threading.Event` for synchronization (the transport is sync + threaded — NO asyncio); add a `tests/unit/websocket/conftest.py` for shared connection/session mocks.
- [ ] T-08.4 [US8] Do NOT remove the `"src/websocket/*"` line from `pyproject.toml` yet — the wildcard stays until every websocket file is covered (final sub-PR). Track per-file coverage in the PR body.
- [ ] T-08.5 [US8] Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90` (wildcard still active — repo total ≥ 90% is achieved via the wildcard until the final sub-PR).
- [ ] T-08.6 [US8] Commit + push + open PR-8a with `Refs #<P8-issue>` trailer (not `Closes` — the umbrella issue closes only after PR-8c/PR-8d).
- [ ] T-08.7 [US8] Wait for CI + `mergeStateStatus=CLEAN`; arm auto-merge; confirm merged, branch deleted.
- [ ] T-08.8 [US8] Repeat T-08.2 through T-08.7 for PR-8b (`coverage-omits-p8b-websocket-diagnostics`, targets `diagnostics/*.py`, tests land under `tests/unit/websocket/diagnostics/`).
- [ ] T-08.9 [US8] Repeat T-08.2 through T-08.7 for PR-8c (`coverage-omits-p8c-websocket-polling`, targets `polling/*.py`, tests land under `tests/unit/websocket/polling/`). In PR-8c (or a follow-on PR-8d if the diff would be too large), remove the `"src/websocket/*"` line from `pyproject.toml` and use `Closes #<P8-issue>` in that final PR only after per-file coverage ≥ 90% is proven on every websocket module.
- [ ] T-08.10 [US8] Confirm all P8 sub-PRs merged, P8 umbrella issue closed by the final sub-PR, all branches deleted.

**Checkpoint**: Every file under `src/websocket/` is covered ≥ 90%; the `"src/websocket/*"` wildcard is removed from the omit list.

---

## T-Final: pyproject.toml omit-list cleanup + repo-wide verification (post-PR-8)

**Purpose**: Confirm the coverage omit list contains only the 6 non-source exclusions per FR-011 and SC-001, that repo-wide coverage ≥ 90% (SC-003), and that the workflow succeeded end-to-end.

**Estimated PR size**: `pyproject.toml` diff only (any leftover stale entries or comment updates); ~5–15 lines. No test additions.

**Independent Test**: After merge, `[tool.coverage.run].omit` in `pyproject.toml` contains exactly `tests/*`, `venv/*`, `.venv/*`, `setup.py`, `*/site-packages/*`, and `src/maps/*` (and up to 2 FR-015 escape-hatch entries with `# TODO(1017): refactor pending` markers). Repo-wide `pytest --cov --cov-fail-under=90` passes.

- [ ] T-Final.1 Run `grep -nE '^\s*"src/' pyproject.toml` scoped to the `[tool.coverage.run].omit` block; every remaining entry MUST either (a) be `src/maps/*` or (b) be one of the ≤ 2 FR-015 escape-hatch modules with an inline `# TODO(1017): refactor pending — see #<issue>` comment. If any other in-scope module remains, halt and open a follow-up issue — do NOT close the workflow.
- [ ] T-Final.2 Branch: `git switch main && git pull && git switch -c coverage-omits-final-cleanup`.
- [ ] T-Final.3 Edit `pyproject.toml`: delete any stale in-scope module entries that remain (should be zero if T-01 through T-08 landed correctly); confirm the FR-015 escape-hatch entries carry the `# TODO(1017): refactor pending` marker and a live follow-up issue link.
- [ ] T-Final.4 Verify locally: `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov --cov-fail-under=90` — must be green with zero suppressions of any kind added.
- [ ] T-Final.5 Run the definitive omit-list check:
  ```bash
  python -c "import tomllib; import pathlib; d = tomllib.loads(pathlib.Path('pyproject.toml').read_text()); print('\n'.join(d['tool']['coverage']['run']['omit']))"
  ```
  Expect exactly `tests/*`, `venv/*`, `.venv/*`, `setup.py`, `*/site-packages/*`, `src/maps/*`, plus any FR-015 escape-hatch entries. Any other line is a workflow bug.
- [ ] T-Final.6 Commit + push: stage `pyproject.toml`; push the branch.
- [ ] T-Final.7 Open PR with `Closes #<workflow-tracking-issue>` trailer via `gh pr create --base main --head coverage-omits-final-cleanup`; include the T-Final.5 output in the PR body per plan.md Decision 2.
- [ ] T-Final.8 Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-Final.9 Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-Final.10 Confirm merged, workflow issue closed, branch deleted. Confirm the FR-015 escape-hatch follow-up issue(s) (if any) remain open in the tracker.

**Checkpoint**: Workflow complete. `pyproject.toml`'s coverage omit list contains only non-source exclusions plus ≤ 2 FR-015 escape-hatch entries. Repo-wide coverage ≥ 90% with the true source surface measured.

---

## Dependencies & Execution Order

### PR-to-PR Dependencies (strict)

All PRs are strictly sequential per FR-003 and SC-008. PR N+1 does NOT open until PR N is merged, its branch deleted, and its target issue closed. No two workflow PRs may be open simultaneously.

```
PR-0 (P0 design artifacts) → PR-1 (P1) → PR-2 (P2) → PR-3 (P3) → PR-4a (P4) → PR-4b (P4) → PR-5a (P5) → PR-5b (P5) → PR-6 (P6) → PR-7 (P7) → PR-8a (P8) → PR-8b (P8) → PR-8c (P8) → T-Final
```

Optional splits:

- PR-3 → PR-3a + PR-3b if API cluster exceeds ~2500 lines
- PR-6 → PR-6a + PR-6b if the state-changing cluster exceeds reviewer bandwidth
- PR-8 → PR-8a/PR-8b/PR-8c (recommended default) or PR-8a/PR-8b/PR-8c/PR-8d if pyproject cleanup needs a dedicated final step

Rationale (from `plan.md` § Decision 4 — Ordering rationale):

- P1 first: pure-function utilities are lowest risk, highest test-authoring-speed; they build the fixture-authoring muscle memory needed for later clusters.
- P2 → P3 → P4 → P5: exporter/API clusters share the `mistapi.APISession` mock pattern established by PR-2; the shared `tests/unit/export/conftest.py` introduced in PR-4a is reused by PR-4b/PR-5a/PR-5b.
- P6 after P5: state-changing modules require the mocking discipline learned on read-only exporters; Constitution Principle III demands extra rigor.
- P7 after P6: SSH/TUI is the first cluster where FR-015 escape hatch may be invoked; the escape-hatch budget is only spent after simpler clusters prove the workflow is on track.
- P8 last: websocket is the largest and most likely to require refactoring; leaving it last preserves options.
- T-Final ensures the final omit list matches SC-002 exactly.

### Within-PR Dependencies

Each PR's sub-tasks are strictly sequential (audit → branch → author tests → edit pyproject → verify → commit → push → PR → CI wait → merge → confirm). PR-4a and PR-4b MUST run in that order because PR-4a introduces the shared `tests/unit/export/conftest.py` reused by PR-4b/PR-5a/PR-5b. PR-8a/PR-8b/PR-8c MUST run in order because the `src/websocket/*` wildcard stays in `pyproject.toml` until the final sub-PR.

### Parallel Opportunities

Between PRs: none (strict serial dispatch per FR-003 and SC-008).

Within PRs: sub-tasks for authoring separate `test_*.py` files under a shared `tests/unit/<cluster>/` directory are logically parallelizable during authoring — but they land as a single PR, so `[P]` markers are not used in this workflow. All sub-tasks are single-track sequential.

---

## Implementation Strategy

### MVP Scope

The MVP is PR-1 (P1 utilities) alone. Landing it removes 4 omit entries — 11% of the in-scope omit list — and validates the test-authoring pattern for the remaining 7 PR-families. If the workflow must pause at any point, pausing after PR-1 leaves the codebase strictly better than baseline.

### Incremental Delivery

Each PR delivers an independently valuable and revertable increment:

1. PR-1 (P1): utilities — 4 omits removed; test pattern validated.
2. PR-2 (P2): export helpers — 5 omits removed; `mistapi.APISession` mock pattern established.
3. PR-3 (P3): API/DB/analytics — 7 omits removed; DB mocks (arango, redis) validated.
4. PR-4a (P4): org exporters part 1 — 3 omits removed; shared `tests/unit/export/conftest.py` introduced.
5. PR-4b (P4): org exporters part 2 — 4 omits removed; conftest reuse proven.
6. PR-5a (P5): site exporters — 5 omits removed.
7. PR-5b (P5): report generators + inventory facade — 5 omits removed.
8. PR-6 (P6): state-changing device managers — 5 omits removed; Constitution Principle III artifact produced.
9. PR-7 (P7): SSH + TUI + prompt — 2–3 omits removed (FR-015 escape hatch candidate).
10. PR-8a/PR-8b/PR-8c (P8): websocket subpackage-by-subpackage — 1 wildcard removed once per-file coverage lands.
11. T-Final: pyproject.toml cleanup + workflow verification.

### Serial Execution Discipline

Only one workflow PR open at a time (SC-008). After each merge:

1. Wait for GitHub to auto-close the target issue.
2. Confirm the delivery branch is deleted on remote.
3. Re-run `pytest --cov --cov-fail-under=90` locally on the fresh `main` to confirm repo-wide coverage still ≥ 90%.
4. Open the next PR's branch from the fresh `main`.

### FR-015 Escape-Hatch Budget

Maximum 2 modules may retain an omit entry across the workflow, each requiring:

- Inline `# TODO(1017): refactor pending — see #<issue>` comment on the omit line.
- A follow-up refactor issue open in the tracker at PR-merge time.
- Explicit PR-body justification.

Candidates (from plan.md Risk Register): `src/websocket/service_ping_manager.py`, `src/ssh/cli_shell_manager.py`, `src/ui/tui.py`. Do not spend escape-hatch budget before PR-7.

---

## Notes

- `[P]` tasks = different files, no dependencies. Not used in this workflow — every sub-task is single-track sequential.
- `[Story]` label maps each task to its user story / PR-family (US1 → PR-1, US4 → PR-4a+PR-4b, US5 → PR-5a+PR-5b, US8 → PR-8a+PR-8b+PR-8c).
- Every delivery PR branches from current `main` at PR-open time (FR-004) — never from `1017-remove-coverage-omits`.
- No `--admin` bypass anywhere (FR-006). Wait for `mergeStateStatus=CLEAN`. SKIPPED conditional checks are not blocking; failing required checks are.
- Pre-push gate: `rtk black --check .` and `rtk ruff check .` MUST be clean before every push. Never rely on CI to catch format/lint issues.
- No new `# noqa`, `# type: ignore`, `# nosec`, or `# pylint: disable` may be introduced anywhere in the repository (SC-006). Reviewers grep the diff.
- Production `src/` modules MUST NOT be edited by this workflow (FR-010); only tests are added and `pyproject.toml` is trimmed. If a module cannot reach 90% without a refactor, invoke FR-015 escape hatch or halt.
- `pyproject.toml` edits are strictly limited to `[tool.coverage.run].omit` line deletions (FR-009, FR-011) plus the optional FR-015 `# TODO(1017): refactor pending` inline comment.
- Coverage ≥ 90% and pylint ≥ 9.5 hold on every merged commit (SC-010).
- Refresh coverage baseline between PRs; PR body must include pre/post per-module coverage numbers and the pyproject diff per plan.md Decision 2.
- Issue numbers marked `#TBD` above must be replaced with real tracking-issue numbers before PR-open time; the P1 tracking issue is `#878` per plan.md § Decision 3 exit criterion (a).
