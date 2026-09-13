# Implementation Plan: Remove Coverage Omits and Test 36 Excluded Modules

**Branch**: `1017-remove-coverage-omits` | **Date**: 2026-07-13 | **Spec**: `specs/1017-remove-coverage-omits/spec.md`

**Input**: Feature specification from `specs/1017-remove-coverage-omits/spec.md`; GitHub issue [#878](https://github.com/jmorrison-juniper/MistHelper/issues/878).

## Summary

Drive the `[tool.coverage.run].omit` array in `pyproject.toml` from its current ~41 entries down to the six legitimately-non-source entries (`tests/*`, `venv/*`, `.venv/*`, `setup.py`, `*/site-packages/*`, `src/maps/*`) across 8 serial User-Story clusters (P1 -> P8), one or more delivery PRs per story. The technical approach is **honest test authoring, not gate manipulation**: for every module removed from the omit list, land a dedicated test file under `tests/` that exercises real code paths against mocked externals (mistapi client, SSH transport, WebSocket transport, DB connections, subprocess), reaching per-file coverage >= 90%. Ordering is smallest-and-safest first (utilities), then data-plumbing, then exporters, then state-changing device managers, then SSH/TUI, then the async WebSocket cluster last (so every mocking pattern the earlier stories build up is available before it's needed). Source modules are **not refactored** as part of this workflow (issue #878 non-goal); the FR-015 escape hatch permits up to 2 modules to retain their omit entry with a `# TODO(1017): refactor pending` comment and a tracking issue if a module is genuinely untestable without refactor. The `fail_under=90` and pylint `fail-under=9.5` gates are never lowered; every merge lands with `mergeStateStatus=CLEAN`, no `--admin` bypass.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution Technology & Compatibility Constraints).

**Primary Dependencies**: `pytest 9.0.3`, `coverage 7.13.5`, `unittest.mock` (stdlib), `pytest`'s built-in `monkeypatch` fixture, `mistapi>=0.63.1` (mocked, never live in default suite). Optional per-module: `responses` / `pytest-httpx` for HTTP mocking IF the mocking surface exceeds ~30 lines of `unittest.mock` boilerplate (see Phase 0 decision matrix). No new runtime deps.

**Storage**: N/A for the workflow itself. `src/db/database_schema_utils.py` is a pure SQL DDL **string builder** (verified: only stdlib imports `inspect`, `logging`, `re`, `datetime`, `typing`); it never opens a database connection. Tests assert on the generated SQL text directly; no `sqlite3` fixture needed.

**Testing**: `pytest -v --tb=short` with `coverage.fail_under=90`; `pylint --fail-under=9.5`. Per-file coverage assertion via `coverage report --fail-under=90 --skip-covered` after each merge (see verification commands below).

**Target Platform**: Windows 11 dev (local venv), Linux container runtime (Podman) for CI. Tests must be OS-neutral — no hardcoded `/` or `\\` separators, always `os.path.join()` or `pathlib.Path()`.

**Project Type**: Single-project CLI tool with extracted `src/` subsystems. Test suite mirrors `src/` layout under `tests/unit/<pkg>/` (existing convention — e.g., `tests/unit/ui/`, `tests/unit/analytics/`, etc.).

**Performance Goals**: Unit tests must run offline with zero API credentials in under 30 seconds (per `tests/conftest.py` docstring). Any test added by this workflow that pushes total suite runtime beyond 60 seconds MUST be reviewed for over-broad fixtures.

**Constraints**:
- **No source refactor** (issue #878 non-goal; FR-010). Test-affordance changes (e.g., extracting an inner helper to make it importable) MUST be recorded in the PR body with rationale and MUST NOT be structural (no new classes, no re-partitioning of a module across files). Constitution Principle II (Class-Based Architecture) is respected — this workflow adds tests, not new classes in `src/`.
- **FR-015 escape hatch capped at 2 modules across the entire workflow** — if more than 2 modules cannot reach 90% without refactor, the workflow pauses and scope is renegotiated via a follow-up issue rather than lowering the bar (SC-008).
- **No live-network calls in the default CI run** (FR-012 / SC-007). Every external touch point (mistapi, paramiko SSH, websocket, subprocess to a device, sqlite file writes) is mocked or gated behind `@pytest.mark.integration`.
- **Coverage gate frozen at 90** (FR-009); pylint fail-under frozen at 9.5 (SC-010).
- **No `# pragma: no cover`, `# type: ignore`, or dummy `import <module>` tests** used to game the gate (SC-006).
- **Retained omit entries frozen at 6**: `tests/*`, `venv/*`, `.venv/*`, `setup.py`, `*/site-packages/*`, `src/maps/*` (FR-011 / SC-001).
- **Serial dispatch across stories** (FR-003): PRs for Story N+1 do not open until every PR for Story N has landed cleanly on `main`. Within a single story, sub-PRs MAY open in parallel iff they touch disjoint files.
- **Every delivery PR branches from current `main`** at PR-open time; `1017-remove-coverage-omits` is coordination-only (FR-004).

**Scale/Scope**:
- **Working set (2026-07-13 audit)**: 41 total omit entries. 6 are retained non-source (out of scope). 35 are in-scope in-workflow (matches issue #878's "36 excluded modules" less one, adjusted per the current omit list snapshot recorded in `pyproject.toml`).
- **Wildcard cluster**: `src/websocket/*` (Story 8) recursively covers 15 `.py` files under `src/websocket/`, `src/websocket/diagnostics/`, and `src/websocket/polling/`. Removing the wildcard un-omits every file present at merge time — the PR MUST land tests for all of them.
- **Delta from issue body**: The 2026-07-13 audit shows 6 entries added between issue creation and today (`src/analytics/insight_metrics_utils.py`, `src/api/api_core_fetch_utils.py`, `src/cache/cache_utils.py`, `src/export/data_exporter.py`, `src/export/org_site_exporter.py`, `src/ui/prompt_utils.py`). Per FR-016, these are in scope and folded into P1/P2/P3/P4/P5/P7 clusters by module theme.
- **Fresh audit refresh**: Between every merged PR in this workflow, the omit list in `pyproject.toml` on `main` is re-read as ground truth. Issue-body counts are stale after 2026-07-13 and MUST NOT be used to size any single PR.

**Repo layout notes**:
- `tests/` mirrors `src/` layout under `tests/unit/<pkg>/` (existing convention). New test files for a module in `src/<pkg>/<module>.py` land at `tests/unit/<pkg>/test_<module>.py`. Non-conforming placements (root-level `tests/test_*.py`) are permitted only if a peer test file already sits there — new work MUST use the mirrored layout.
- Existing fixtures: `tests/conftest.py` (repo-wide autouse `isolate_working_directory`, `tmp_data_dir`, `tmp_jsonl_file`, plus MistHelper pre-loader), `tests/integration/conftest.py` (live-network fixtures — untouched by this workflow), `tests/unit/ui/conftest.py` (UI-specific mocks). This workflow MAY extend `tests/conftest.py` with **new shared fixtures**, but MUST NOT rewrite existing fixtures.
- The `integration` pytest marker is already registered in `pyproject.toml`. No marker registration change needed.

**Development gates (mandatory before every push)**:
1. `rtk black --check .` — repo-wide format check; fix locally, never push and rely on CI.
2. `rtk ruff check .` — repo-wide lint; fix locally.
3. `pytest -v --tb=short --cov=src --cov-fail-under=90` — full suite green locally with coverage gate satisfied.
4. `mypy --strict src/` — no new errors on files this PR touches.

**PR gates (mandatory before every merge)**:
- Wait for `mergeStateStatus=CLEAN` from `gh pr view <N> --json mergeStateStatus`. No `--admin` bypass under any condition (FR-006).
- Merge command pattern: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch` armed once, then poll.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: PASS (with explicit alignment).

The MistHelper Constitution v1.4.0 exists at `.specify/memory/constitution.md`. Every principle is respected by this workflow:

- **Principle I (Five-Item Rule)**: New test functions MUST stay under 25 lines each and 5 parameters each. Test fixtures use dataclass or dict factories when parameter count exceeds the limit.
- **Principle II (Class-Based Architecture, No Wrappers)**: This workflow adds tests, not new source classes. Any test-affordance change discovered mid-work that would require a new class in `src/` MUST invoke the FR-015 escape hatch instead — no drive-by class extractions.
- **Principle III (Safety-First, NON-NEGOTIABLE)**: State-changing modules in P6 (reboot, firmware upgrade, RADIUS reconfig, ticket create) MUST have tests that assert `safe_input()`-guarded confirmation paths are exercised with both accept and reject inputs; destructive-op tests MUST verify the `confirmation != "UPGRADE"` early-return path is hit.
- **Principle IV (Full Deployment Pipeline, NON-NEGOTIABLE)**: Runtime behavior of `src/` modules MUST NOT change from any test-affordance edit; the deployment pipeline (build container, restart, verify) runs on every merged PR as normal.
- **Principle V (Observability & Logging)**: Tests MUST assert ASCII-only log output where log content is checked; no unicode/emoji in test-authored log strings.
- **Principle VI (Inline Comments, NON-NEGOTIABLE)**: Every non-trivial line in a new test file MUST carry an inline comment explaining what the assertion or setup is doing. Boilerplate lines (imports, decorators, blank lines) exempt.
- **Principle VII (Action Logging, NON-NEGOTIABLE)**: Tests do not need to add `logging.info()` before/after (they are the observers, not the actor). BUT: if a test-affordance edit adds any executable line to a source module, that line MUST carry inline comments AND, if it wraps a meaningful action, before/after logging — matching the touched function's existing style.

Secondary alignment with **"Security Findings: Fix Over Suppress (NON-NEGOTIABLE)"**: New test files MUST NOT introduce `#nosec`, `# type: ignore`, `# noqa`, or `# pylint: disable` comments to silence findings. Bandit false positives (e.g., B105 hardcoded-password-string on mock passwords) MUST use the well-known safe pattern (`"REDACTED"` sentinel) rather than annotation.

No entries required in the Complexity Tracking table on the basis of constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/1017-remove-coverage-omits/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output: audit + per-cluster mocking pattern decisions
├── data-model.md        # Phase 1 output: per-module test scope + fixture inventory
├── quickstart.md        # Phase 1 output: verification recipes per PR
├── contracts/           # Phase 1 output: shared-fixture contracts + coverage assertion contract
│   ├── shared_fixtures.md
│   ├── coverage_assertion.md
│   └── mocking_conventions.md
├── checklists/          # Existing: requirements.md
└── tasks.md             # NOT produced by this command — /speckit.tasks generates it
```

### Source Code (repository root)

```text
pyproject.toml                                 # Target of every PR: omit-list entries deleted.
                                               # No other pyproject.toml changes permitted
                                               # (no fail_under change, no marker additions,
                                               # no new omit entries — FR-009, FR-011).

src/
├── analytics/  api/  cache/  db/  device/
├── export/     firmware/  gateway/  input/
├── inventory/  org/  reports/  site/  ssh/
├── troubleshooting/  ui/  utils/  websocket/  # Existing source, untouched except for
                                               # FR-010-guarded test-affordance edits.

tests/
├── conftest.py                                # Existing repo-wide fixtures. This workflow
│                                              # MAY add new shared fixtures here (see
│                                              # contracts/shared_fixtures.md).
├── integration/  e2e/  contract/              # Existing; untouched.
├── unit/
│   ├── <pkg>/                                 # Mirrors src/<pkg>/ layout. New test files
│   │                                          # land here at test_<module>.py.
│   │   └── conftest.py                        # Optional per-package fixtures (added only
│   │                                          # when a fixture is used by 2+ test files
│   │                                          # within the same package).
│   └── <existing test files>
└── fixtures/                                  # Existing JSON/CSV fixture bundles.
                                               # New fixture files added here per module.
```

**Structure Decision**: Option 1 (single-project) layout is unchanged. This workflow does not introduce new top-level packages, does not restructure `src/`, and does not create new `tests/` subtrees. All new test files land under the existing `tests/unit/<pkg>/` mirror layout. Per-package `conftest.py` is added inside `tests/unit/<pkg>/` **only** when a fixture is shared by 2+ test files within that package (see planning decision #1 below).

## Planning Decisions

The six planning decisions called out in the `/speckit.plan` invocation are recorded here as authoritative choices for the workflow. Every task in `tasks.md` and every PR body in this workflow MUST cite the applicable decision by number.

### Decision 1 — Test authoring pattern

**Shared fixture location** (three-tier hierarchy):

1. **`tests/conftest.py` (repo-wide)** — Add a fixture here IFF it is used by 3+ test files across 2+ packages. Example candidates from this workflow:
   - `mock_mistapi_session` — a `unittest.mock.MagicMock` shaped like `mistapi.APISession` with commonly-stubbed methods (`.mist_get`, `.mist_post`, `.mist_delete`, `.mist_put`) pre-configured to return empty dicts. Used by every P3, P4, P5 exporter test.
   - `mock_config` — a dict-shaped config that mirrors `MistHelper`'s runtime config surface. Used by exporter and manager tests.
2. **`tests/unit/<pkg>/conftest.py` (per-package)** — Add a fixture here IFF it is used by 2+ test files inside a single package. Example candidates:
   - `tests/unit/export/conftest.py` — a `mock_org_snapshot` fixture with a small representative org payload, shared across all six P4 exporter tests.
   - `tests/unit/websocket/conftest.py` — a `mock_websocket_transport` fixture with `send`, `recv`, `close` stubs, shared across all P8 tests.
3. **In-file (per-test-file)** — Everything else lives inside the specific `test_<module>.py`, using the `@pytest.fixture` decorator. Default location; use when the fixture serves a single test file.

**Mock scope conventions**:
- Default scope is **`function`** (pytest's default) — every test gets a fresh mock, no cross-test state bleed.
- **`module`** scope is permitted only for fixtures that build a costly in-memory object with no mutable state (e.g., loading a JSON fixture file). Never for mocks that a test might mutate.
- **`session`** scope is prohibited for anything touching source modules in this workflow — leaves too much room for cross-test bleed and masks real bugs.

**`monkeypatch` vs. `unittest.mock`** (decision tree):
- **Use `monkeypatch`** when: (a) replacing an attribute on an imported module (`monkeypatch.setattr("src.api.api_data_fetcher.some_helper", fake)`), (b) setting environment variables (`monkeypatch.setenv`), (c) changing the working directory (already done by the repo-wide `isolate_working_directory` autouse fixture).
- **Use `unittest.mock`** when: (a) verifying call counts and argument shapes on a returned object (`mock.assert_called_once_with(...)`), (b) stubbing out a class instance passed as a parameter, (c) building a nested mock tree for a mistapi client (attribute access chains), (d) patching decorators via `@patch("module.attribute")`.
- **Never mix** the two on the same target — pick one per attribute. If a test needs both a state-swap and call-count verification, use `mock.patch` with an inline `MagicMock` and inspect `.call_args_list` afterwards.

**Anti-patterns** (explicitly prohibited):
- **Dummy `import module` tests** — SC-006 forbids these. If a test file only does `import src.foo.bar` and asserts nothing, it does not count as coverage even if `coverage.py` reports 100%.
- **`# pragma: no cover` wrappers around dead branches** — SC-006 forbids these. If a branch is genuinely unreachable, the branch (not the test) is refactored — or, if refactoring is out of scope per FR-010, the FR-015 escape hatch is invoked.
- **`unittest.mock.MagicMock()` with no `spec=` argument** for anything imported from `mistapi` or `paramiko` — always pass `spec=mistapi.APISession` (or equivalent) so typos in method names raise `AttributeError` immediately. This catches drift when the SDK version bumps.

### Decision 2 — Coverage measurement approach

**Local per-module verification** (run before every push):

```bash
# 1. Run the full suite with coverage measurement enabled.
pytest -v --tb=short --cov=src --cov-report=term-missing --cov-fail-under=90

# 2. Assert per-file coverage for the module(s) this PR just un-omitted.
#    --skip-covered hides files already at 100%; --fail-under=90 asserts the floor.
coverage report --include="src/<pkg>/<module>.py" --fail-under=90

# 3. Confirm no omit-list regression on other files by producing a full report.
coverage report --skip-covered --sort=cover | head -30
```

**CI verification**: The project's existing CI pipeline (per Assumptions in the spec) runs `pytest --cov` on every push and enforces `fail_under=90` as a hard gate. This workflow relies on that gate — removing an omit entry without landing sufficient tests causes CI failure by design. No new CI steps are required.

**Per-PR coverage artifact**: Each PR body MUST include a coverage report snippet for the un-omitted modules, generated by:

```bash
coverage report --include="src/<pkg>/<module1>.py,src/<pkg>/<module2>.py" --skip-covered
```

This snippet lives in the PR description, not in a committed file — no coverage HTML/XML is added to the repo.

**Gate-invariant check**: `pyproject.toml`'s `fail_under = 90` line is verified by grep at every PR-open time. Any PR that changes this line fails review immediately (FR-009).

### Decision 3 — Per-PR delivery contract

**Every delivery PR MUST satisfy all criteria below before merge.** This is the uniform exit template for all sub-phases in Phase 2.

| # | Criterion | Verification |
|---|-----------|-------------|
| a | Target user story cited | PR description contains `Refs #878` and names the user story (P1–P8) plus the omit entries removed. Final PR of P8 uses `Closes #878`. |
| b | Omit entries deleted | `grep -E "^\\s*\"src/(<pkg>/<module>)\\.py\"" pyproject.toml` returns zero matches for every module the PR claims to un-omit. |
| c | Per-module coverage >= 90% | `coverage report --include=<un-omitted-files> --fail-under=90` passes locally and in CI. |
| d | Test files use real assertions | `grep -E "# pragma: no cover\|# type: ignore" tests/<new files>` returns zero matches (SC-006). |
| e | No live-network calls | New test files inspected for either (a) explicit `unittest.mock` / `monkeypatch` usage on network entry points, OR (b) `@pytest.mark.integration` marker. Verified by manual review + CI running default suite in network-isolated container per SC-007. |
| f | Black + ruff clean | `rtk black --check .` and `rtk ruff check .` return zero findings locally AND in CI. |
| g | mypy clean on touched files | `mypy --strict src/<pkg>/<module>.py` output has zero net-new errors relative to `main` at PR-open time. |
| h | Full test suite green | `pytest -v --tb=short --cov=src --cov-fail-under=90` passes in CI on the PR's head commit. |
| i | Pylint >= 9.5 | `pylint --fail-under=9.5` satisfied on the PR's merge commit. |
| j | `mergeStateStatus=CLEAN` | `gh pr view <N> --json mergeStateStatus` returns `CLEAN` immediately before invoking merge; no `--admin` bypass under any condition. |
| k | Coverage report snippet in PR body | PR description includes the `coverage report --include=...` output for the un-omitted modules (see Decision 2). |
| l | If FR-015 invoked, tracking issue linked | PR body cites the tracking issue for any module retained with `# TODO(1017): refactor pending`. Escape-hatch use counted against the 2-module cap. |

**Refactor-pending modules** (FR-015 handling):
- Precondition: the module was audited, at least one attempt at test authoring against real behavior was made, and the module was found to require structural refactor to reach 90% coverage.
- Action: leave the omit entry in `pyproject.toml`. Add a `# TODO(1017): refactor pending — see #<tracking-issue>` comment immediately above the omit entry. Open a `refactor` label tracking issue referencing #878 with a specific unblocking hypothesis (e.g., "extract inner closure from Foo.bar so branch X is directly callable").
- Counter: track escape-hatch usage in the workflow's running tally. Cap = 2. If the count would exceed 2, the PR does NOT merge; instead the workflow pauses, a decision is escalated (SC-008), and scope is renegotiated via a follow-up issue.

**Dead-code modules** (per spec Assumptions): if audit shows a module is imported nowhere in `src/`, keep its omit entry with a `# TODO(1017): dead code candidate — see #<tracking-issue>` comment and open a follow-up refactor issue. Dead-code exemptions DO NOT count against the FR-015 2-module cap because they trigger a different follow-up (deletion, not refactor).

### Decision 4 — Ordering rationale for P1 -> P8 clusters

The spec fixes ordering (FR-001); this decision carries the rationale forward as an implementation-facing map. Serial dispatch (FR-003) is strict — no story is reordered.

| Story | Cluster theme | Rationale for slot |
|-------|---------------|-------------------|
| P1 | Low-level utilities (`environment_utils`, `filter_operator_engine`, `troubleshoot_utils`, `prompt_client_utils`, plus deltas per FR-016) | Smallest, purest, dependency-light. Establishes the test-authoring patterns (fixture placement, mock scope, `monkeypatch` vs. `unittest.mock` split) that every later story reuses. Removing 4+ omit entries with minimal churn signals workflow works. |
| P2 | Export helpers (`org_export_utils`, `license_export_utils`, `const_definitions_exporter`, `gateway_test_exporter`) | Consumed by the larger exporter clusters in P3/P4/P5. Landing their tests first means downstream exporter tests exercise validated helper contracts — bugs surface in the smaller helper tests before they cascade. |
| P3 | API + DB + analytics data path (`api_data_fetcher`, `api_fetch_utils`, `database_schema_utils`, `data_collection_manager`, plus deltas per FR-016) | Upstream of every exporter. Landing coverage here first means P4/P5 exporter tests exercise real fetch code paths rather than compensating for unproven upstream behavior. Also crystallizes the `mock_mistapi_session` shared fixture. |
| P4 | Org-level exporters (six modules) | Largest single exporter cluster. Depends on P2's validated helpers and P3's validated fetcher. May split into up to 6 sub-PRs if any exporter's fixture surface exceeds ~150 lines (FR-013). |
| P5 | Site-level exporters + report generators + read-only facades (ten modules; split PR-5a exporters / PR-5b reports+inventory-facade) | Parallels P4 in structure at site scope. Reuses P4's fixture patterns. Absorbs two read-only modules originally listed under spec.md P6 (`offline_device_reporter`, `org_device_inventory_summary_facade`) to keep P6 focused on state-changing code per Constitution Principle III — see tasks.md line 259 for the reshuffle rationale. |
| P6 | State-changing device / firmware / RADIUS / ticket managers (five modules: `arp_command_manager`, `device_reboot_manager`, `firmware_manager`, `bulk_radius_wlan_config_manager`, `org_ticket_manager`) | State-changing operations (reboots, firmware upgrades, RADIUS reconfig, ticket creation). Requires the most careful mocking to prevent accidental live-device calls in CI. Landing after P3 ensures the mock fixtures the managers need are stable. Constitution Principle III (Safety-First) tests for destructive-op confirmation paths live here. |
| P7 | SSH + TUI (`cli_shell_manager`, `tui`) | Interactive-terminal code paths. Depends on P6 for any shared SSH mock patterns. Small cluster (two modules), single PR unless one module's fixture surface pushes past the FR-013 500-line threshold. |
| P8 | WebSocket wildcard cluster (`src/websocket/*` — 15 files) | Hardest cluster: async transport, long-lived connections, service-ping discovery, diagnostic subscriptions. Lands last so every mocking pattern (network, subprocess, SSH, TUI) is already in place. Wildcard removal un-omits every current and future file under `src/websocket/`; PR must land tests for all 15 files present at merge time. |

### Decision 5 — Risk register

Modules most likely to need heavy mocking or FR-015 escape-hatch treatment. Risk score is the assessment for planning purposes; actual invocation is decided per-PR based on real testability.

| Module | Cluster | Risk | Mocking surface | Mitigation |
|--------|---------|------|-----------------|------------|
| `src/websocket/service_ping_discovery.py` (~805 LOC) | P8 | High | Injected `utility` deps; no direct websocket library import — orchestrates discovery via injected dependencies | Mock the injected `utility` deps with `MagicMock(spec=...)`; assert loop exits after at most 2 mocked iterations (per Story 8 Acceptance 3). Candidate for sub-PR split. |
| `src/websocket/service_ping_manager.py` (~1000 LOC) | P8 | High | Async lifecycle + service registry | Same pattern as `service_ping_discovery`; share fixtures in `tests/unit/websocket/conftest.py`. |
| `src/ssh/cli_shell_manager.py` | P7 | High | Paramiko `SSHClient`, `Channel`, `Transport` object graph + interactive prompts + I/O timeouts | Mock at `paramiko.SSHClient` class boundary; use `MagicMock(spec=paramiko.SSHClient)` for typo-safety. Interactive prompt path uses `monkeypatch` on `safe_input()`. |
| `src/ui/tui.py` | P7 | High | Terminal rendering + blocking user input | Mock `sshkeyboard.listen_keyboard` (project uses this per requirements.txt); assert `on_press` callback firing with synthetic key events. No real terminal open. |
| `src/firmware/firmware_manager.py` | P6 | Medium-High | State-changing API calls (upgrade) + confirmation prompts (Principle III) | Mock `mistapi` client; test BOTH accept (`"UPGRADE"`) and reject paths for the safe_input confirmation. |
| `src/device/device_reboot_manager.py` | P6 | Medium-High | State-changing API + destructive confirmation | Same pattern as firmware_manager. |
| `src/site/bulk_radius_wlan_config_manager.py` | P6 | Medium | Multi-step config write + rollback | Mock `mistapi`; assert rollback path is exercised via injected exception on step 2 of 3. |
| `src/api/api_data_fetcher.py` | P3 | Medium | Pagination loop + mistapi client | Mock returns page-token-terminated responses. Assert loop exits after N pages (N=3 fixture default). |
| `src/api/api_core_fetch_utils.py` | P3 | Medium | Cursor-based iteration | Same pattern as api_data_fetcher. |
| `src/db/database_schema_utils.py` | P3 | Low | Pure SQL DDL string builder (no DB driver imported) | Assert on the returned DDL text directly with `assert "CREATE TABLE" in sql`, `assert "PRIMARY KEY (foo, bar)" in sql`, etc. No fixture, no mocking, no in-memory DB. |
| Six P4 org exporters | P4 | Medium (each) | Large JSON output shapes | Fixture-based golden-file comparison OR in-memory buffer inspection (Story 4 Acceptance 3). Golden fixtures land in `tests/fixtures/`. |
| Eight P5 site exporters + reporters | P5 | Medium (each) | Tabular output shape + column ordering | At least one test per module MUST validate column order, header text, one row of data (Story 5 Acceptance 3). |

**FR-015 candidates** (advance-flagged as likely escape-hatch users, not commitments):
- `src/websocket/service_ping_discovery.py` — if async lifecycle proves untestable without splitting the class, retain omit + open refactor issue. Counts against the 2-cap.
- `src/ui/tui.py` — if the render loop is too coupled to `sshkeyboard` internals to mock cleanly, retain omit + open refactor issue. Counts against the 2-cap.

If either candidate consumes an escape-hatch slot, the workflow proceeds with 0 or 1 slots remaining. If a third module surfaces mid-workflow requiring escape-hatch, the workflow pauses per SC-008.

### Decision 6 — Verification commands for the final state

**Terminal-state assertions** (run against `main` after the last PR of Story 8 merges):

```bash
# SC-001: omit list contains exactly the 6 retained non-source entries.
python -c "
import tomllib, sys
with open('pyproject.toml', 'rb') as f:
    omit = sorted(tomllib.load(f)['tool']['coverage']['run']['omit'])
expected = sorted([
    'tests/*', 'venv/*', '.venv/*', 'setup.py',
    '*/site-packages/*', 'src/maps/*'
])
if omit != expected:
    print('FAIL: unexpected omit entries')
    print('  present:', omit)
    print('  expected:', expected)
    sys.exit(1)
print('PASS: omit list is exactly the 6 retained non-source entries')
"

# SC-003 / SC-004: coverage passes at 90 project-wide AND per-file.
pytest -v --tb=short --cov=src --cov-report=term-missing --cov-fail-under=90
coverage report --fail-under=90 --skip-covered

# SC-006: no gate-gaming annotations in workflow-added test files.
git diff --name-only origin/main..HEAD -- tests/ | \
  xargs grep -lE "# pragma: no cover|# type: ignore" || echo "PASS: zero gate-gaming annotations"

# SC-007: default CI suite issues no live network calls.
# Verified by running the suite in a network-isolated container (Podman with --network=none)
# and observing zero external egress. See quickstart.md for the exact recipe.

# SC-010: pylint gate holds.
pylint --fail-under=9.5 src/

# FR-009: fail_under is still 90.
grep -E "^fail_under\\s*=\\s*90$" pyproject.toml || (echo "FAIL: coverage.fail_under changed"; exit 1)

# FR-015 cap check: at most 2 modules retain omit entry with refactor-pending TODO.
grep -c "TODO(1017): refactor pending" pyproject.toml
# Value MUST be <= 2. If value == 0, workflow completed without invoking escape hatch.
```

**Per-PR verification** (run before every merge; see Decision 3 exit criteria):

```bash
# Un-omit assertion for THIS PR's modules.
for module in <list-of-un-omitted-modules>; do
  grep -E "^\\s*\"$module\"" pyproject.toml && echo "FAIL: $module still omitted" && exit 1
done
echo "PASS: all target modules removed from omit list"

# Coverage floor for THIS PR's modules.
coverage report --include="<comma-separated-module-paths>" --fail-under=90
```

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Constitution Check passed with explicit alignment; no violations to track. The table below repurposes the section for its analogue use in this workflow: **per-story effort estimate** to help pace serial dispatch under SC-009 (eight calendar weeks target for eight stories at ~1 PR per 2–3 working days).

| Story | Cluster | In-scope module count | Est. sub-PR count | Est. effort | Ordering-dependency notes |
|-------|---------|-----------------------|-------------------|-------------|--------------------------|
| P1 | Low-level utilities | 4 base + up to 2 delta (FR-016) = ~6 | 1 | Day–1.5 days | Establishes fixture patterns. First PR of workflow. |
| P2 | Export helpers | 4 | 1 | Day | Depends on P1 fixtures existing. Introduces `mock_mistapi_session` shared fixture (Decision 1). |
| P3 | API + DB + analytics data path | 4 base + up to 2 delta = ~6 | 1–2 | 2 days | Depends on P2 mock patterns. Introduces pagination-loop mock pattern (no in-memory DB needed — `database_schema_utils` is a pure string builder). |
| P4 | Org-level exporters | 6 base + 1 delta (`org_site_exporter`) = ~7 | 2–4 | 4–6 days | Largest cluster. Reuses P2/P3 fixtures. Golden-fixture setup pattern lands here (Decision 5). |
| P5 | Site-level exporters + reporters + read-only inventory facade | 10 (5 exporters + 4 reporters + 1 facade; absorbs 2 read-only modules originally scoped to P6) | 2 (PR-5a exporters, PR-5b reports+facade) | 3–5 days | Parallels P4. Reuses P4 fixture patterns; tabular-output assertion pattern (Story 5 Acceptance 3) crystallizes here. |
| P6 | State-changing device / firmware / RADIUS / ticket managers | 5 (`arp_command_manager`, `device_reboot_manager`, `firmware_manager`, `bulk_radius_wlan_config_manager`, `org_ticket_manager`) | 1 (optionally split into T-06a device/firmware + T-06b site/org per tasks.md line 261) | 4–6 days | State-changing tests + Principle III safe_input coverage (Decision 5). Highest-risk mocking. |
| P7 | SSH + TUI | 2 | 1 | 2–4 days | Two hard modules, small count. Highest FR-015 risk (Decision 5 flag). |
| P8 | WebSocket wildcard cluster | 15 (from wildcard expansion) | 2–4 | 5–7 days | Last story. Highest complexity per module. May consume 1 of 2 FR-015 slots. |

Effort estimates assume the standard review cadence of ~1 PR per 2–3 working days (SC-009) and are advisory, not gating. Total workflow envelope: ~8 calendar weeks, ~15–25 delivery PRs across 8 stories.

---

## Phase 0: Outline & Research

**Prerequisite**: none (spec captured all clarifications).

Phase 0 for this workflow is short — the spec fixed ordering and the plan fixed patterns. The Phase 0 deliverable (`research.md`) consolidates three inputs into a single reviewable document, produced BEFORE Story 1's first PR opens:

1. **Refresh the omit-list audit at current `main` HEAD**. Capture the exact set of 35 in-scope entries (per FR-016) and 6 retained non-source entries. Preserve the raw `pyproject.toml` omit-array snapshot as an appendix. Diff the current list against issue #878's original 35 and record the delta (~6 entries added post-issue) with confirmed cluster assignments (which entries go into which of P1–P8).

2. **Enumerate the 15 files under `src/websocket/*`** at current `main` HEAD (per `find src/websocket -name "*.py" -type f`). Record each file's LOC and imports. This bounds Story P8's scope precisely — if a new file appears in `src/websocket/` between now and Story P8 opening, P8's PR MUST cover it.

3. **Record per-cluster mocking decisions** in Decision / Rationale / Alternatives format:
   - **P3 API pagination mocking pattern**: paginated mistapi calls (`.mist_get` returning `{"next": ...}`-shaped responses). Decision: mock at `mistapi.APISession` boundary via `unittest.mock.MagicMock(spec=mistapi.APISession)`. Rationale: matches existing fixture patterns in `tests/unit/api/`. Alternative rejected: `responses` library — heavier dep, unnecessary for stdlib-mock-adequate shape.
   - **P4/P5 exporter output-shape assertions**: Decision — golden JSON/CSV fixtures under `tests/fixtures/` compared via `assert exported == expected_fixture`. Rationale: rewards fixture-comparable output, forces exporters to have deterministic serialization. Alternative rejected: schema-only assertions — hides drift.
   - **P6 destructive-op confirmation coverage**: Decision — parametrize each destructive-op test with `("UPGRADE", expected_action_called), ("cancel", expected_no_action)`. Rationale: exercises the safe_input early-return path (Principle III). Alternative rejected: only-happy-path — misses the safety-critical branch.
   - **P7 SSH mock boundary**: Decision — mock `paramiko.SSHClient` class, not `Channel` or `Transport`. Rationale: `SSHClient` is the entry point every call site touches; mocking it once suffices. Alternative rejected: mock all three — over-mocks, misses call-flow bugs.
   - **P7 TUI mock boundary**: Decision — mock `sshkeyboard.listen_keyboard` at its import location per test file. Rationale: single entry point; predictable synthetic events. Alternative rejected: subprocess-launch TUI in headless PTY — too slow, too fragile for CI.
   - **P8 WebSocket transport mocking**: Decision — mock `websocket.WebSocketApp` (sync `websocket-client` library, NOT the async `websockets` package) with `MagicMock(spec=websocket.WebSocketApp)`, feeding recorded frames through the reader-thread callback. Rationale: `src/websocket/manager.py` imports `websocket-client` and uses `threading` for the background reader; there is no `asyncio` in the transport path. Alternative rejected: any async-mock helper (`aioresponses`, `websockets-mock`) — the source is not async.

4. **Record the fixture-migration order** for the three shared fixtures introduced by this workflow (per Decision 1): `mock_mistapi_session` (introduced in P2, promoted to `tests/conftest.py` in P3 once used by 3+ files), `mock_config` (introduced in P2), `mock_websocket_transport` (introduced in P8, stays in `tests/unit/websocket/conftest.py`).

**Output**: `research.md` with all clarifications resolved, containing:
- Fresh 2026-07-13 omit-list snapshot with cluster assignments (P1–P8) for every in-scope entry.
- `src/websocket/*` file enumeration (bounds P8 scope).
- Per-cluster mocking pattern decisions in Decision / Rationale / Alternatives format.
- Fixture-migration order for the three shared fixtures.

## Phase 1: Design & Contracts

**Prerequisite**: `research.md` complete.

### 1. Extract entities → `data-model.md`

The spec's Key Entities section names five operational entities. `data-model.md` records each entity's concrete shape as it applies to this workflow:

- **Omit Entry inventory (35 in-scope)**: The exact list of module paths to remove, grouped by cluster (P1–P8), with per-entry columns for `pyproject.toml` line number at workflow start, cluster assignment, and Phase 0 audit disposition (in-scope / retained / dead-code candidate / refactor-pending candidate).
- **Un-Omitted Module test manifest**: For each of the 35 in-scope modules, record:
  - Target test file path (mirrored `tests/unit/<pkg>/test_<module>.py`).
  - Public-API surface to cover (list of top-level classes and functions with docstring-declared entry points).
  - External touch points requiring mocks (mistapi calls, subprocess, SSH, WebSocket, filesystem, DB).
  - Expected fixture bundle location (`tests/fixtures/<cluster>/<module>_fixtures.json` or in-file dataclass factories).
- **Retained Non-Source Entry inventory**: Enumerated verbatim from FR-011: `tests/*`, `venv/*`, `.venv/*`, `setup.py`, `*/site-packages/*`, `src/maps/*`. Validation rule: `data-model.md` MUST assert this set is exactly the omit-list terminal state (SC-001).
- **Integration-Only Path inventory**: Per-module list of code paths that CANNOT be covered without live infrastructure (e.g., a WebSocket handshake in `service_ping_manager.py` that requires a real controller). Each entry cites the decision (mock double OR `@pytest.mark.integration`) and the reason.
- **Test Fixture Bundle registry**: Per-cluster inventory of new fixture files added to `tests/fixtures/` and per-package `conftest.py` files added to `tests/unit/<pkg>/`. Each entry records first-consumer story (P#) and shared-scope tier (Decision 1 tier 1/2/3).

State transitions: this workflow's tracked "state" is the omit-list count, decrementing monotonically as PRs merge. The Phase 0 audit is the baseline count (~35); the terminal state is 0 in-scope entries (SC-001).

### 2. Define interface contracts → `contracts/`

This workflow doesn't touch public APIs of source modules (FR-010). Contracts here document the internal contracts the test suite relies on, captured as Markdown fragments (project convention — no OpenAPI / IDL applies to test infrastructure):

- **`contracts/shared_fixtures.md`**: The contract for every shared fixture introduced by this workflow. One section per fixture, listing:
  - Fixture name and location tier (Decision 1 tier).
  - Return-type shape (class or dict schema with field names + types).
  - Mock-scope decision and rationale.
  - Consumer stories (P#) and expected consumer count.
  - Validation rule: shared fixtures MUST NOT mutate global state; each fixture call MUST return a fresh object graph.

- **`contracts/coverage_assertion.md`**: The contract for per-file coverage verification. Enumerates:
  - The `coverage report --include=<path> --fail-under=90` invocation used per PR.
  - The full-suite coverage assertion (`pytest --cov=src --cov-fail-under=90`).
  - The FR-009 assertion (`fail_under=90` line unchanged in `pyproject.toml`).
  - The FR-015 counter assertion (`grep -c "TODO(1017): refactor pending" pyproject.toml <= 2`).
  - Validation rule: every PR body MUST include the per-file coverage snippet output.

- **`contracts/mocking_conventions.md`**: The contract for how source modules are mocked. Enumerates:
  - The `MagicMock(spec=<real class>)` convention for mistapi, paramiko, and `websocket-client` (the sync `websocket.WebSocketApp` — not the async `websockets` package) (Decision 1 anti-patterns). No in-scope module imports `sqlite3` or the async `websockets` library at runtime.
  - The `monkeypatch` vs. `unittest.mock` decision tree (Decision 1).
  - The `@pytest.mark.integration` gate for any code path that cannot be mocked cleanly (FR-012).
  - The prohibition on `session`-scope mocks touching source modules (Decision 1).
  - Validation rule: reviewers grep new test files for `MagicMock()` without `spec=` on mistapi/paramiko/`websocket-client` imports and reject PRs that violate the convention.

### 3. Quickstart → `quickstart.md`

`quickstart.md` records the verification recipe an operator or reviewer runs to confirm a given story's PR is complete. One section per story (P1–P8), each containing:

- The exact `grep` command to assert the target omit entries are deleted from `pyproject.toml`.
- The exact `coverage report --include=<paths> --fail-under=90` command for the un-omitted modules.
- The exact `pytest -v tests/unit/<pkg>/` invocation for the story's new test files.
- The `black --check` + `ruff check` + `mypy --strict src/<pkg>/` commands for the touched source files.
- The `gh pr view <N> --json mergeStateStatus` command asserting `CLEAN` before merge.
- For P8 specifically: the `find src/websocket -name "*.py" | xargs -I{} coverage report --include={} --fail-under=90` recursive per-file assertion covering all 15 files un-omitted by the wildcard removal (Story 8 Acceptance 2).
- The network-isolation recipe (Podman with `--network=none`) for verifying SC-007 on each PR.

### 4. Agent context update

Update the plan reference block between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` in `.github/copilot-instructions.md` to point at this plan file (`specs/1017-remove-coverage-omits/plan.md`). No other agent-context files change.

**Output**: `research.md`, `data-model.md`, `contracts/shared_fixtures.md`, `contracts/coverage_assertion.md`, `contracts/mocking_conventions.md`, `quickstart.md`, updated `.github/copilot-instructions.md`.

---

## Phase 2: Implementation Planning (Strategy)

> **Note**: `/speckit.tasks` generates `tasks.md` with per-module, per-fixture task decomposition. This section captures cross-PR strategy, ordering rationale, and the shared exit-criteria template. Individual test-file enumeration lives in `tasks.md`, not here.

### Merge ordering rationale

The 8 stories land in the fixed order P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7 -> P8 (FR-001; Decision 4). Each story may split into 1–4 sub-PRs (Decision 4 estimated column) if the FR-013 threshold (~500 net lines OR ~150 fixture lines per module) is met. Within a single story, sub-PRs MAY open in parallel iff they touch disjoint files; between stories, dispatch is strict serial (FR-003).

### Cross-PR invariants (apply to every PR)

- Every module removed from the omit list has a dedicated test file under `tests/unit/<pkg>/test_<module>.py` with real assertions (SC-006).
- No `# pragma: no cover`, `# type: ignore`, or dummy `import module` tests added to `tests/` (SC-006).
- No live-network calls in the default suite (SC-007). Every `mistapi`, `paramiko`, `websocket-client`, `subprocess` touch point is mocked OR gated by `@pytest.mark.integration`.
- `pyproject.toml` changes limited to omit-entry deletions (FR-009 forbids fail_under change; FR-011 requires retained set unchanged).
- Only one PR from this workflow open on `main` at any moment within a single story cluster (FR-003 strict-serial across stories); intra-story parallel sub-PRs permitted iff file-disjoint.
- Delivery branches cut fresh from `main` — never from `1017-remove-coverage-omits` (FR-004).
- Pre-push local gate: `rtk black --check .`, `rtk ruff check .`, `pytest -v --tb=short --cov=src --cov-fail-under=90`, `mypy --strict src/` (on touched files) MUST all be clean before push.
- FR-015 escape-hatch invocations counted against the 2-module cap; workflow pauses if a third would push count to 3 (SC-008).

### PR sub-phase enumeration

Each sub-phase corresponds to one User Story cluster (P1–P8). Exit criteria are identical across sub-phases per Decision 3; only the target cluster, module set, and expected omit-count delta vary. Per-story deliverable summaries:

**Sub-phase 1 — Story P1 — Low-level utilities**
- Entry: Phase 0 audit committed to `research.md`; Phase 1 artifacts merged into feature branch.
- Deliverable: 4 base modules + up to 2 delta modules (per FR-016) removed from omit list; per-module tests under `tests/unit/utils/`, `tests/unit/troubleshooting/`, `tests/unit/input/`.
- Fixture introductions: baseline patterns established; nothing yet lifted to `tests/conftest.py`.

**Sub-phase 2 — Story P2 — Export helpers**
- Entry: P1 merged; `main` audit refreshed.
- Deliverable: 4 export-helper modules un-omitted; tests under `tests/unit/export/`. `mock_mistapi_session` fixture introduced at package-scope `tests/unit/export/conftest.py`.

**Sub-phase 3 — Story P3 — API + DB + analytics data path**
- Entry: P2 merged; `main` audit refreshed. `mock_mistapi_session` promoted from `tests/unit/export/conftest.py` to `tests/conftest.py` once P3 tests reference it from 3+ files across 2+ packages (Decision 1 tier promotion).
- Deliverable: 4 base + up to 2 delta modules un-omitted; tests under `tests/unit/api/`, `tests/unit/db/`, `tests/unit/analytics/`, `tests/unit/cache/`. Pagination-loop mock pattern crystallizes here (`database_schema_utils` needs only string-assertion tests — no DB fixture).

**Sub-phase 4 — Story P4 — Org-level exporters**
- Entry: P3 merged; `main` audit refreshed. Golden-fixture setup complete under `tests/fixtures/org_exporters/`.
- Deliverable: 6 base + 1 delta (`org_site_exporter`) exporter modules un-omitted; tests under `tests/unit/export/`. May split into up to 4 sub-PRs by exporter theme (admin, alarm, config, device_stats, template, site).

**Sub-phase 5 — Story P5 — Site-level exporters + report generators**
- Entry: P4 merged; `main` audit refreshed.
- Deliverable: 8 modules un-omitted; tests under `tests/unit/export/` and `tests/unit/reports/`. Tabular-output column-order assertion pattern (Story 5 Acceptance 3) crystallizes here. May split into 2–3 sub-PRs.

**Sub-phase 6 — Story P6 — Device / firmware / inventory managers**
- Entry: P5 merged; `main` audit refreshed.
- Deliverable: 7 modules un-omitted; tests under `tests/unit/device/`, `tests/unit/firmware/`, `tests/unit/inventory/`, `tests/unit/org/`, `tests/unit/site/`, `tests/unit/gateway/`. Principle III safe_input confirmation coverage lands here. May split into 2–3 sub-PRs.

**Sub-phase 7 — Story P7 — SSH + TUI**
- Entry: P6 merged; `main` audit refreshed.
- Deliverable: 2 modules un-omitted; tests under `tests/unit/ssh/` and `tests/unit/ui/`. Paramiko-mock and sshkeyboard-mock patterns crystallize here. Single PR unless FR-013 threshold breached. Highest FR-015 escape-hatch risk (Decision 5); may consume 1 of 2 slots.

**Sub-phase 8 — Story P8 — WebSocket wildcard cluster**
- Entry: P7 merged; `main` audit refreshed; `find src/websocket -name "*.py" -type f` re-run to bound scope.
- Deliverable: `"src/websocket/*"` wildcard removed from omit list; tests for all 15 files under `src/websocket/` (recursively including `diagnostics/` and `polling/`) landed under `tests/unit/websocket/`. `mock_websocket_transport` fixture at `tests/unit/websocket/conftest.py`. Long-running poll loops mocked to exit after ≤2 iterations (Story 8 Acceptance 3). May split into up to 4 sub-PRs. Final PR uses `Closes #878`.

### Per-PR exit criteria template

Every delivery PR MUST satisfy all 12 criteria enumerated in Decision 3 (rows a–l). Story-specific supplementary criteria:

- **P3, P4, P5**: PR body includes a snippet from `coverage report --include=<un-omitted-files>` showing per-file coverage >= 90%.
- **P4**: Golden-fixture files committed under `tests/fixtures/org_exporters/` are byte-for-byte deterministic (no timestamps, no non-deterministic ordering).
- **P5**: At least one test per module validates column order, header text, and one row of data (Story 5 Acceptance 3).
- **P6**: For every module performing state-changing operations, at least one test invokes the destructive path and asserts the safe_input confirmation branch (Principle III).
- **P7**: PR body confirms no `paramiko.SSHClient()` or `sshkeyboard.listen_keyboard()` invocation runs without a mock (grep test files).
- **P8**: PR body enumerates the 15 files under `src/websocket/` at merge time and shows per-file coverage >= 90% for every one (Story 8 Acceptance 2). Final P8 PR body uses `Closes #878`.

### Merge invocation pattern

Once all 12 exit criteria pass locally and in CI, and `mergeStateStatus=CLEAN`:

```bash
GITHUB_TOKEN= gh pr merge <PR_NUMBER> --auto --squash --delete-branch
```

Arm once, then poll `gh pr view <PR_NUMBER> --json state,mergeCommit` until state is `MERGED`. After merge, refresh the audit via `python -c "import tomllib; print(sorted(tomllib.load(open('pyproject.toml','rb'))['tool']['coverage']['run']['omit']))"` before opening the next sub-phase's PR (FR-014).

---

## Stop-and-report

Phase 0 and Phase 1 artifacts are the deliverables of this command. `tasks.md` is intentionally NOT produced — it is the output of the separate `/speckit.tasks` step. Individual test-file and per-module task enumeration lives in `tasks.md`, not here.
