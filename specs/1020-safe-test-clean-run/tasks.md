---

description: "Task list for Safe, Repeatable MistHelper `--test` Clean-Run Workflow"
---

# Tasks: Safe, Repeatable MistHelper `--test` Clean-Run Workflow

**Input**: Design documents from `/specs/1020-safe-test-clean-run/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/operation_registry_classification_contract.md`, `contracts/preflight_failure_contract.md`, `quickstart.md` (all present and read in full before this file was generated)

**Tests**: Included. The feature spec and constraints explicitly require targeted unit/guardrail tests; all new tests are unit/guardrail-only (zero credentials, zero network, no new `integration`-marked tests) per `research.md` R6 and `pyproject.toml`'s `integration` marker convention.

**Organization**: Tasks are grouped by user story (P1-P4 from `spec.md`) in the exact order mandated for this feature: **US1 (fail-closed registry + guardrails) -> US2 (isolated venv guard) -> US3 (credential/config preflight + config-template correction) -> Docs -> US4 (iterative validation loop)**. This sequencing is a hard requirement (not just priority order) because US4's validation loop depends on US1-US3 being in place, and the credential preflight's remediation text (US3) should reference the corrected config-template guidance produced by US3 itself.

**Scope discipline**: This file is Phase 2 output only (`/speckit.tasks`). No production code is written by generating this file — implementation happens later via `/speckit.implement` or manual execution of the tasks below.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no ordering dependency on an incomplete task)
- **[Story]**: US1/US2/US3/US4 — omitted for Setup, Foundational, Docs, and Polish tasks
- Every task names its exact file path(s)

## Path Conventions

Single-project CLI layout (confirmed in `plan.md` Project Structure): `MistHelper.py` at repo root, `src/` package, `tests/` package. No `backend`/`frontend` split applies.

## Execution Status (2026-07-17)

- **Completed:** T001-T049. The workflow implementation, guardrails,
  documentation, static gates, non-integration validation, and live
  credentialed validation are complete.
- **T040 clean:** `py_compile`, Ruff, Black, and configured `mypy src` pass.
  The Black baseline formatting and Windows Unix-UID type-check blocker were
  repaired without altering Unix container behavior.
- **T044 complete:** a credentialed `MistHelper.py --test` run passed all 59
  safe operations, skipped all 138 unsafe operations, and wrote a zero-failure
  telemetry summary. A menu-33 runtime dependency failure discovered during
  this run was fixed with focused regression coverage.
- **T045 complete:** a credentialed `MistHelper.py --testinteractive` run
  passed all 37 interactive-safe operations and skipped all 160 other options,
  with a zero-failure telemetry summary.
- **T047 clean:** the worktree-local Wave 1 gate passed all six stages,
  including a final 59/59 credentialed systematic sweep.
- **Final validation verdict (T046):** **clean run achieved**. The fresh
  isolated venv contains 6,306 passing non-integration tests at 91.56%
  coverage, and both live test modes complete with zero failed operations.

---

## Phase 1: Setup

**Purpose**: Confirm the environment/tooling baseline before any change is made. No production code is touched.

- [ ] T001 Record the pre-change tooling baseline by running (and saving console output as an implementation note, not a new file) `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py src tests`, `python -m black --check MistHelper.py src tests`, `python -m mypy src --config-file pyproject.toml`, and `python -m pytest -m "not integration" --cov=src --cov=tests --cov-report=term-missing` from the repository root — this is the "before" state every later gate re-run is compared against.
- [ ] T002 [P] Confirm an isolated virtual environment is active for all subsequent work: `python -c "import sys; print(sys.prefix != sys.base_prefix)"` must print `True` (per `quickstart.md` Prerequisites) — Phase 4 (US2) tests assume/verify exactly this signal, so implementation work itself must not run under system Python.
- [ ] T003 [P] Produce the authoritative inventory of the 60 currently-unregistered `menu_actions` keys and their handler functions by diffing `set(MistHelper.menu_actions.keys())` (`MistHelper.py:3641-4608`) against `set(MistHelper.OperationRegistry._REGISTRY.keys())` (`src/utils/operation_registry.py:51-274`) in a scratch/REPL check (no file committed) — this list, cross-checked against `research.md` R1's preliminary table, is the exact work-list T011 consumes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared scaffolding required before User Story 2's tests can be written. Minimal by design — nearly all other work extends existing classes/files in place.

**⚠️ CRITICAL**: T004 must exist before any Phase 4 (US2) task runs.

- [ ] T004 Create the new `tests/bootstrap/` test directory (no `__init__.py` needed — `pytest`'s `testpaths = ["tests"]` rootdir discovery already works this way for the existing `tests/guardrails/` package) to host User Story 2's isolated-venv guardrail tests.

**Checkpoint**: Foundation ready — User Story 1 can start immediately (no dependency on T004); User Story 2 can start once T004 exists.

---

## Phase 3: User Story 1 - Unregistered menu options never run in `--test` (Priority: P1) 🎯 MVP

**Goal**: Flip `OperationRegistry.get()`'s fallback from fail-open (`"safe"`) to fail-closed (new `"unregistered"` category in `SKIP_CATEGORIES`); add explicit `_REGISTRY` entries for all 60 currently-unregistered keys (including destructive menu `194`); replace the brittle 11-key baseline with an exhaustive coverage guardrail; correct the one existing test whose baseline data encodes today's fail-open defect.

**Independent Test**: Add an unregistered test key to `menu_actions` (or a test double) and confirm classification excludes it from both the `--test` safe set and the `--testinteractive` interactive-safe set, with a loud warning — all unit-level, no live API calls, no credentials.

### Tests for User Story 1 ⚠️ (write first, confirm they FAIL before implementation)

- [ ] T005 [P] [US1] Create new guardrail test file `tests/guardrails/test_operation_registry_menu_coverage.py` with initial failing assertions for: (a) `set(MistHelper.menu_actions.keys()) == MistHelper.OperationRegistry.registered_options()` (fails today — `registered_options()` does not exist and 60 keys are missing), (b) every registered category is one of the 8 documented values, (c) every `category == "destructive"` entry has a `skip_reason` containing `"DESTRUCTIVE"`.
- [ ] T006 [P] [US1] Create new unit test file `tests/unit/test_operation_registry_fail_closed.py` asserting: a never-before-seen option key (e.g. `"__never_registered__"`) resolves via `OperationRegistry.get()` to `category == "unregistered"`; `is_safe()` and `is_interactive_safe()` are both `False` for it; `"unregistered"` is a member of `SKIP_CATEGORIES` — all fail today since the fallback still returns `{"category": "safe"}`.
- [ ] T007 [US1] Extend `tests/guardrails/test_operation_registry_menu_coverage.py` (from T005) with failing assertions that menu `"194"` is classified `destructive` with a `"DESTRUCTIVE"`-containing `skip_reason`, and is absent from both `OperationRegistry.safe_options(...)` and `OperationRegistry.interactive_safe_options(...)` over the full `menu_actions` key set (FR-004, SC-002).

### Implementation for User Story 1

- [ ] T008 [US1] In `src/utils/operation_registry.py`, add `"unregistered"` to `SKIP_CATEGORIES` (~lines 306-308) and change `OperationRegistry.get()`'s fallback (~lines 310-317) from `return {"category": "safe"}` to `return {"category": "unregistered", "skip_reason": "Unregistered menu option — fail-closed pending classification"}`, updating the `logging.warning(...)` message text from "defaulting to safe" to reflect the new fail-closed behavior.
- [ ] T009 [US1] In `src/utils/operation_registry.py`, add a `registered_options() -> set[str]` classmethod returning `set(cls._REGISTRY.keys())`, colocated with the existing `safe_options`/`unsafe_options` classmethods (~lines 339-352).
- [ ] T010 [US1] Update the module docstring (`src/utils/operation_registry.py` lines 1-18, the `Categories` list) and the `OperationRegistry` class docstring (lines 44-49, which currently says "defaults to safe with warning") to document the 9th `unregistered` fail-closed fallback category and correct the stale "defaults to safe" language.
- [ ] T011 [US1] In `src/utils/operation_registry.py`, add explicit `_REGISTRY` entries for all 60 currently-unregistered keys identified in T003, re-verifying each handler's read-only vs. state-changing behavior in `MistHelper.py`/`src/org/org_ticket_manager.py` before assigning a category — grounded in `research.md` R1's evidence table: menu `14`/`18` → `resource_intensive`; menu `189`/`190`/`191` → `destructive` (`OrgTicketManager.create_ticket`/`add_comment`/`update_ticket`); menu `192` → `interactive` (`OrgTicketManager.view_ticket` prompts via `_select_ticket`); the remaining ~55 read-only export handlers → `safe` (re-confirm `35`/`36` specifically per research.md's "not individually re-verified" note before finalizing).
- [ ] T012 [US1] In `src/utils/operation_registry.py`, add (or confirm) the explicit `"194": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Clone Device Config to Gateway Template"}` entry (or equivalent wording containing `"DESTRUCTIVE"`), matching FR-004 and the existing `menu_actions["194"]` label at `MistHelper.py:4602-4607` (`DeviceConfigTemplateClonerManager.clone`, requires typed `'CREATE'` confirmation — unchanged).
- [ ] T013 [US1] In `src/utils/operation_registry.py:294`, correct `WAVE1_SAFETY_CLASSIFICATION_BASELINE["safe_true"]` by removing or replacing the `"9999"` sentinel (a key absent from `menu_actions` that only reads `True` today because of the fail-open defect) — per spec Assumptions this is in-scope, intentional correction; `tests/guardrails/test_wave1_safety_classification_guardrails.py` itself is NOT modified, since it only consumes this baseline dict via `wave1_safety_classification_baseline()`.
- [ ] T014 [US1] Finalize `tests/guardrails/test_operation_registry_menu_coverage.py` (T005/T007) into its complete passing form per `contracts/operation_registry_classification_contract.md`'s 4 guarantees, adding the 4th assertion: zero entries resolve to `"unregistered"` via `OperationRegistry.get()` across the full `menu_actions` key set (the "dangerous incomplete categorization" detector).
- [ ] T015 [P] [US1] Add a small regression addition to `tests/guardrails/test_wave1_entry_routing_guardrails.py` confirming a sample of already-registered `safe`/`interactive_safe` options (e.g. `"26"`, `"58"`, `"62"`) are unaffected by the fail-closed default change (FR-006 — no regression to already-correct classifications).
- [ ] T016 [P] [US1] Finalize `tests/unit/test_operation_registry_fail_closed.py` (T006) into its complete passing form, including an explicit assertion that `is_safe(key)` and `is_interactive_safe(key)` for the same unregistered key are evaluated identically regardless of which is checked first (FR-007 — uniform fail-closed behavior across `--test` and `--testinteractive`).
- [ ] T017 [US1] Create new unit test file `tests/unit/test_systematic_test_unregistered_semantics.py` asserting that a synthetic unregistered key surfaces through `_build_systematic_test_options()`/`OperationRegistry.unsafe_options(...)` (`MistHelper.py:4766-4778`) with a named, non-empty `skip_reason` (category `unregistered`) — i.e. it appears in the unsafe/skip list with an actionable reason, never silently dropped and never silently run — proving FR-002's "loud, actionable warning" requirement at the telemetry/summary layer, not just the classification layer.

**Checkpoint**: Run `python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py tests/guardrails/test_wave1_safety_classification_guardrails.py tests/guardrails/test_wave1_entry_routing_guardrails.py tests/unit/test_operation_registry_fail_closed.py tests/unit/test_systematic_test_unregistered_semantics.py -v` — all green, zero network/credentials. User Story 1 is independently complete and testable here (MVP).

---

## Phase 4: User Story 2 - `--test` runs inside an isolated virtual environment, not system Python (Priority: P2)

**Goal**: Add an isolated-venv predicate to `DependencyCheckOrchestrator` that blocks automatic package install/upgrade into system Python by default, with a documented explicit override, composing cleanly with the existing `DISABLE_AUTO_INSTALL` gate.

**Independent Test**: Invoke the orchestrator with a dependency-injected fake `sys` module (controlled `prefix`/`base_prefix`) — no real package installs, no monkeypatching the real interpreter.

### Tests for User Story 2 ⚠️ (write first, confirm they FAIL before implementation)

- [ ] T018 [P] [US2] Create new test file `tests/bootstrap/test_dependency_check_venv_guard.py` with initial failing tests for a not-yet-implemented `_is_running_in_isolated_venv()` predicate on `DependencyCheckOrchestrator`: (a) fake `sys_module` with `prefix == base_prefix` and no `real_prefix` attribute → `False`; (b) fake `sys_module` with `prefix != base_prefix` → `True`; (c) fake `sys_module` with `prefix == base_prefix` but `real_prefix` set (legacy `virtualenv`) → `True`.
- [ ] T019 [P] [US2] Add a failing test (same file) asserting `DependencyCheckOrchestrator.run()` invokes zero `installer.install_with_pip(...)`/`installer.install_with_uv(...)` calls when the injected fake interpreter is non-isolated and no override env var is set — construct the orchestrator entirely with injected fakes/spies (no real subprocess, no real network) per the existing dependency-injection pattern in `src/bootstrap/dependency_check.py`.
- [ ] T020 [P] [US2] Add a failing test (same file) asserting install/upgrade behavior is unchanged (missing packages installed, outdated packages upgraded per existing `AUTO_UPGRADE_TO_LATEST`/`AUTO_UPGRADE_DEPENDENCIES` semantics) when the injected fake interpreter reports a genuine isolated venv (FR-011 — no regression for the supported case).
- [ ] T021 [P] [US2] Add failing tests (same file) for: (a) the new override env var (e.g. `MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL`) allowing install/upgrade to proceed on a non-isolated interpreter while emitting a loud warning log distinguishable from routine info logs (FR-010); and (b) `DISABLE_AUTO_INSTALL=true` combined with a non-isolated interpreter — both gates independently block with no conflicting/duplicate messages (spec Edge Case).

### Implementation for User Story 2

- [ ] T022 [US2] In `src/bootstrap/dependency_check.py`, add a new `_ENV_ALLOW_SYSTEM_PYTHON_INSTALL = "MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL"` module constant (following the existing `_ENV_DISABLE_AUTO_INSTALL` naming convention, line 11) and a `_is_running_in_isolated_venv()` predicate method on `DependencyCheckOrchestrator`, implemented as `self.sys_module.prefix != self.sys_module.base_prefix` with a `getattr(self.sys_module, "real_prefix", None)` fallback for legacy `virtualenv` — colocated near `_is_auto_install_disabled()` (~lines 77-80).
- [ ] T023 [US2] In `src/bootstrap/dependency_check.py`, wire the new predicate into `run()` (~lines 60-64) as an additional independent short-circuit guard alongside the existing `_is_auto_install_disabled()` check, so install/upgrade is skipped when not isolated and the override env var is unset; add new `_MSG_*` constants (matching the file's existing `_MSG_*` convention) distinguishing "no `.venv` was ever created/activated" from "a `.venv` appears configured but its launcher is missing/broken" in the diagnostic text (message-only distinction per `research.md` R3 — the predicate itself stays a single boolean check), plus a separate loud-warning `_MSG_*` constant for the explicit-override path.
- [ ] T024 [US2] Add inline "WHY" comments at the new predicate/guard call sites in `src/bootstrap/dependency_check.py`, matching the file's existing per-line comment density (Constitution VI).
- [ ] T025 [P] [US2] Finalize `tests/bootstrap/test_dependency_check_venv_guard.py` (T018-T021) into its complete passing form.

**Checkpoint**: Run `python -m pytest tests/bootstrap/ -v` — all green, zero real package installs, zero network. User Stories 1 and 2 are both independently functional here.

---

## Phase 5: User Story 3 - Clear, secret-safe credential/configuration preflight before a live systematic run (Priority: P3)

**Goal**: Add a host/token preflight at the top of `_establish_mist_session()` and a non-interactive org-id guard inside `ConfigUtils`, both failing closed with redacted, actionable messages referencing `deploy/.env.example` strictly before any `mistapi`/`requests` call — plus a config-template reference correction so the guidance names the variables the code actually reads.

**Independent Test**: Unset `MIST_HOST`/`MIST_APITOKEN`/`MIST_API_TOKEN`/org-id env vars, ensure no `.env` is discoverable in the test's working directory, and assert the preflight fails fast with a specific message before any HTTP request is attempted — no network access, no real credentials.

### Tests for User Story 3 ⚠️ (write first, confirm they FAIL before implementation)

- [ ] T026 [P] [US3] Create new unit test file `tests/unit/test_credential_preflight.py` with initial failing tests for a not-yet-implemented `_preflight_verify_credentials()` helper: (a) no `MIST_HOST`/`MIST_APITOKEN`/`MIST_API_TOKEN` set and no `.env` discoverable → fails closed with a message naming the missing variable(s) and referencing `deploy/.env.example`, before any session/network object is constructed; (b) host present but blank/placeholder → fails with a specific message; (c) valid non-placeholder host + present token → passes; (d) assert (via `ast`/`inspect` source scan or module-import check) that the helper's containing scope never imports `requests` or `mistapi` (SC-004's structural zero-HTTP guarantee).
- [ ] T027 [P] [US3] Add a failing test (same file) asserting no raw token, host override, or org-id value ever appears in the preflight's failure message or any logged output — only variable *names* and `_redact_tokens()`-style previews (`first4...last4` or `***`) may appear (SC-005).
- [ ] T028 [P] [US3] Create new unit test file `tests/unit/test_config_utils_org_id_preflight.py` with initial failing tests for a not-yet-implemented non-interactive guard in `ConfigUtils`: with `sys.argv` simulated to contain `--test` (and separately `--testinteractive`), no org id resolvable from cache/env (`org_id`/`ORG_ID`)/`.env` (`org_id=` line), and no `_apisession` injected, resolution fails closed with an actionable message naming `org_id`/`ORG_ID` and `deploy/.env.example`, and `mistapi.cli.select_org(...)` is never called (assert via mock/spy, zero invocations).
- [ ] T029 [P] [US3] Add a failing regression test (same file) confirming that when no test-mode flag is present in `sys.argv` and a session has been injected via `set_apisession`, `_resolve_org_id_via_prompt()` still calls `mistapi.cli.select_org(...)` exactly as today (interactive behavior unaffected by the new guard).

### Implementation for User Story 3

- [ ] T030 [US3] Add a `_preflight_verify_credentials()` helper function to `MistHelper.py`, colocated near `_parse_api_tokens()`/`_redact_tokens()` (~lines 2562-2605), reusing `_parse_api_tokens()` to read host/tokens and `_redact_tokens()` for any preview text; the function itself must not import `requests`/`mistapi` (structural, not mocked, zero-HTTP guarantee); on failure it prints a remediation message referencing `deploy/.env.example` and the exact env var names (`MIST_HOST`, `MIST_APITOKEN`/`MIST_API_TOKEN`) and calls `sys.exit(1)`.
- [ ] T031 [US3] Call `_preflight_verify_credentials()` at the very top of `_establish_mist_session()` (`MistHelper.py:5201`), before either the `--login` branch or the token branch, so every dispatch mode (`--test`, `--testinteractive`, TUI, CLI, interactive) is covered by one call site (FR-013, FR-017).
- [ ] T032 [US3] Add a non-interactive fail-closed guard inside `ConfigUtils.get_cached_or_prompted_org_id()` / `_resolve_org_id_via_prompt()` (`src/config/config_utils.py` lines 92-137): when `"--test" in sys.argv or "--testinteractive" in sys.argv` (computed locally with the already-imported `sys` module, preserving the module's "no `import MistHelper`" self-containment) and cache/env/`.env` resolution all miss, exit with an actionable message naming `org_id`/`ORG_ID`/`deploy/.env.example` instead of calling `mistapi.cli.select_org(cls._apisession)` (FR-016); interactive (non-test-mode) behavior is unchanged.
- [ ] T033 [US3] Add inline "WHY" comments at both new call sites (`MistHelper.py` and `src/config/config_utils.py`) documenting the two-insertion-point design rationale from `research.md` R4 (host/token vs. org-id are two distinct failure modes with different interactive-vs-non-interactive semantics) — Constitution VI.
- [ ] T034 [US3] **Config-template reference correction**: add a clarifying inline comment in `deploy/.env.example` near line 15 (`MIST_ORG_ID=your_org_id_here`) noting that the `--test`/`--testinteractive` non-interactive org-id resolution path (`ConfigUtils`) actually reads the lowercase `org_id`/`ORG_ID` environment variable, not `MIST_ORG_ID`, and cross-reference this exact nuance in the T030/T032 remediation message text — this corrects the misleading guidance called out in `research.md` R4 without renaming or removing the existing `MIST_ORG_ID` key (still read as a third fallback by `src/maps/maps_manager.py:2722`); no new template file is created (spec Assumptions).
- [ ] T035 [P] [US3] Finalize `tests/unit/test_credential_preflight.py` (T026-T027) into its complete passing form.
- [ ] T036 [P] [US3] Finalize `tests/unit/test_config_utils_org_id_preflight.py` (T028-T029) into its complete passing form, and add `python -m pytest --collect-only -m integration` as a documented check confirming none of T026/T027/T028/T029's tests are marked `integration`.

**Checkpoint**: Run `python -m pytest tests/unit/test_credential_preflight.py tests/unit/test_config_utils_org_id_preflight.py -v` — all green, zero real network/credentials. User Stories 1, 2, and 3 are all independently functional here.

---

## Phase 6: Documentation (cross-cutting, precedes the final validation loop)

**Purpose**: Bring operator-facing documentation in line with the corrected fail-closed/preflight/venv-guard behavior before the Phase 7 validation loop is run, per the Constitution's "Update README"/"Version Changelog" deployment steps and `research.md` R6's noted documentation follow-up.

- [ ] T037 [P] Update `README.md`'s architecture/testing narrative to describe the corrected fail-closed `OperationRegistry` default (no longer "unregistered options default to safe") and the new isolated-venv + credential preflight guards, keeping the existing "Update README" deployment-step convention in sync with actual behavior.
- [ ] T038 [P] Add an `## [Unreleased]` entry to `CHANGELOG.md` (following the file's existing `Keep a Changelog` bullet style) describing: (a) the registry fail-closed fix + exhaustive coverage guardrail (US1), (b) the isolated-venv install/upgrade guard (US2), (c) the credential/org-id preflight (US3), and (d) the `deploy/.env.example` clarifying comment (US3), per the Constitution's "Version Changelog" step (`version YY.MM.DD.HH.MM` format).
- [ ] T039 [P] Update `specs/1020-safe-test-clean-run/quickstart.md` Stage 2's command block to reference the exact final test file paths added in Phases 3-5 (`tests/guardrails/test_operation_registry_menu_coverage.py`, `tests/unit/test_operation_registry_fail_closed.py`, `tests/unit/test_systematic_test_unregistered_semantics.py`, `tests/bootstrap/test_dependency_check_venv_guard.py`, `tests/unit/test_credential_preflight.py`, `tests/unit/test_config_utils_org_id_preflight.py`), replacing the placeholder-style references and closing `research.md` R6's noted follow-up.

---

## Phase 7: User Story 4 - Iterative validation loop reaches a documented "clean run" or an explicit "externally blocked" status (Priority: P4)

**Goal**: Execute the documented 4-stage loop (static gates → full suite → root-cause diagnosis → live credentialed run) from `quickstart.md` against the repository state produced by Phases 1-6, reaching either a real "clean run achieved" verdict or an honest "externally blocked" report — never a false success claim.

**Independent Test**: Run the documented procedure against the current repository state and confirm that, without credentials, the loop stops at the credential preflight gate and reports "externally blocked", while its static/unit-level checks run and pass/fail deterministically with zero credentials/network.

- [ ] T040 [US4] Execute Stage 1 static gates in order — `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py src tests`, `python -m black --check MistHelper.py src tests`, `python -m mypy src --config-file pyproject.toml` — fixing any failure at its root cause (never loosening an assertion or adding an unjustified suppression, per Constitution "Security Findings: Fix Over Suppress" spirit) and re-running until all four are green, with zero credentials/network required (FR-021, SC-008).
- [ ] T041 [US4] Execute Stage 2: run the targeted guardrail/unit selection first — `python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py tests/guardrails/test_wave1_safety_classification_guardrails.py tests/guardrails/test_wave1_entry_routing_guardrails.py tests/bootstrap/ -v` then `python -m pytest tests/ -k "preflight or credential or org_id_preflight" -v`, then the full-coverage run `python -m pytest -m "not integration" --cov=src --cov=tests --cov-report=term-missing` — confirm the `fail_under = 90` gate passes and `python -m pytest --collect-only -m integration` lists none of this feature's new tests (FR-021, SC-008).
- [ ] T042 [US4] Verify the User Story 2 (isolated-venv) and User Story 3 (credential) preconditions are BOTH satisfied in the current working environment before any live `--test`/`--testinteractive` invocation is attempted: run `python -c "import sys; print(sys.prefix != sys.base_prefix)"` (must print `True`) and confirm whether a reachable repository-root `.env` (or equivalent env vars: `MIST_HOST`, `MIST_APITOKEN`/`MIST_API_TOKEN`, `org_id`) exists; if either precondition fails, stop here and report exactly which one blocked progress instead of invoking `--test` in a known-bad state (FR-012, contract `preflight_failure_contract.md`).
- [ ] T043 [US4] **Operator credential dependency — blocking gate; do not attempt to bypass**: given that the environment this specification was authored and implemented in has no reachable `.env`/Mist credentials (per spec Assumptions and the observed 2026-07-16 run), report the terminal status of the live-validation gate as **"externally blocked - operator-supplied credentials required"**, explicitly naming `deploy/.env.example` and the exact variables the operator must supply (`MIST_APITOKEN`/`MIST_API_TOKEN`, `MIST_HOST`, and `org_id` per T034's corrected guidance). Do NOT fabricate, request, discover, or guess credentials from any source, and do NOT loop retrying this step automatically (FR-019, FR-020, SC-007). This is the expected, honest outcome of this task in the current environment.
- [ ] T044 [US4] *(Conditional — perform only once an operator has supplied real credentials in a local repository-root `.env`, outside source control)* Invoke `python MistHelper.py --test`, then parse the printed pass/fail summary (`_report_systematic_outcome`), `data/script.log`, and the timestamped telemetry JSONL path (`_initialize_systematic_telemetry`) against the exact SC-006 clean-run definition: every `safe`-classified option attempted exactly once; zero non-`safe`/`unregistered` options invoked; telemetry file non-empty with a final summary event; zero failed operations reported; process exit code `0`. Report pass/fail with the specific failing metric(s) if any; on failure, repeat only Stage 1 (T040) and Stage 2 (T041) — never re-invoke this task automatically — until root-caused and fixed.
- [ ] T045 [US4] *(Conditional, same precondition as T044)* Repeat T044's evaluation for `python MistHelper.py --testinteractive` against the analogous interactive-safe clean-run criteria, additionally confirming zero `unregistered`/misclassified skips appear in the interactive-safe summary.
- [ ] T046 [US4] Record the final validation-loop verdict (in the PR description or an implementation note, not a new spec artifact) stating explicitly which terminal state was reached: "externally blocked - operator-supplied credentials required" (T043 — the expected outcome today) or "clean run achieved" (T044 and T045 both pass, once an operator later supplies credentials). Never report a false "clean run achieved" result (FR-019, SC-007).

**Checkpoint**: All four user stories are functionally complete; the feature's final live-evidence gate is honestly reported as blocked or clean, never fabricated.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final evidence-gathering and defense-in-depth checks across all stories, reusing existing tooling only.

- [ ] T047 [P] Run the full CI-equivalent gate `pwsh scripts/wave1/run_wave1_gate.ps1` end-to-end and record its console output as final evidence — expected to reach and stop cleanly at the `misthelper_test` step per T043's reported status today (or complete fully once credentials are supplied later).
- [ ] T048 [P] Re-run `tests/guardrails/test_wave1_gate_runner.py` to confirm the gate script's step order/structure (`py_compile` → `ruff` → `black_check` → `mypy` → `pytest_cov` → `misthelper_test`) is unchanged — this feature reuses, never bypasses, the existing pipeline (Constitution IV).
- [ ] T049 [P] Final secret-scan self-check: review the diff of all files changed in Phases 3-6 (`src/utils/operation_registry.py`, `src/bootstrap/dependency_check.py`, `MistHelper.py`, `src/config/config_utils.py`, `deploy/.env.example`, `README.md`, `CHANGELOG.md`, and all new test files) to confirm zero raw token/host/org-id literals were introduced anywhere (SC-005 defense-in-depth, no secrets committed).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: T004 has no dependency on Phase 1 but must complete before any Phase 4 (US2) task.
- **User Story 1 (Phase 3)**: Depends only on Setup (T001-T003 informational); no dependency on Phase 2. Can start immediately — this is the MVP path.
- **User Story 2 (Phase 4)**: Depends on Phase 2 (T004) for its test directory. Independent of US1's file changes (different files: `src/bootstrap/dependency_check.py` vs. `src/utils/operation_registry.py`).
- **User Story 3 (Phase 5)**: Independent of US1/US2's files (`MistHelper.py`'s `_establish_mist_session()` region and `src/config/config_utils.py`); may start any time after Setup.
- **Documentation (Phase 6)**: Depends on US1 + US2 + US3 all being functionally complete (T005-T036), since it documents their combined final behavior and the config-template correction from T034.
- **User Story 4 (Phase 7)**: Depends on Phase 6 completing (docs must be accurate before the loop is documented as run) and, substantively, on US1+US2+US3 (T005-T036) all being complete — this is the required order given in the task constraints (US1 → US2 → US3 → Docs → US4).
- **Polish (Phase 8)**: Depends on Phase 7 completing.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories — true MVP.
- **User Story 2 (P2)**: No functional dependency on US1 (different files); ordered after US1 per the feature's mandated sequencing, not a technical blocker.
- **User Story 3 (P3)**: No functional dependency on US1/US2 (different files); ordered third per the mandated sequencing and because its config-template correction (T034) is referenced by Phase 6 docs.
- **User Story 4 (P4)**: Functionally depends on US1+US2+US3 all being in place — it validates their combined effect and cannot report an honest "clean run" verdict without them.

### Within Each User Story

- Tests (marked ⚠️) are written first and confirmed to FAIL before their corresponding implementation task.
- Registry/config-file edits within a story are sequential (same file — no `[P]`), even when logically separable, to avoid edit races.
- Story is checkpoint-validated (dedicated `pytest` invocation) before moving to the next phase.

### Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel (different concerns, no file writes).
- **US1 tests**: T005 and T006 target different new files — parallel. T007 extends T005's file, so it is sequential after T005.
- **US1 non-file-conflicting finalization**: T015 (different file: `test_wave1_entry_routing_guardrails.py`) and T016 (different file: `test_operation_registry_fail_closed.py`) can run in parallel with each other, but both depend on T008-T013 (the registry file edits) being complete first.
- **US2 tests**: T018-T021 all target the same new file (`tests/bootstrap/test_dependency_check_venv_guard.py`) — marked `[P]` because they are independent *test cases* with no ordering dependency on each other's *content*, but a human/agent adding them should still avoid literal edit conflicts by appending sequentially in practice.
- **US3 tests**: T026/T027 (one file) and T028/T029 (a different file) can proceed in parallel with each other as two independent test-writing threads.
- **Docs (Phase 6)**: T037, T038, T039 are three different files — fully parallel.
- **Polish (Phase 8)**: T047, T048, T049 are independent verification activities — fully parallel.
- **Cross-story**: Once Phase 2 completes, US1 (Phase 3), US2 (Phase 4), and US3 (Phase 5) touch entirely disjoint file sets (`src/utils/operation_registry.py` vs. `src/bootstrap/dependency_check.py` vs. `MistHelper.py`'s session-init region + `src/config/config_utils.py` + `deploy/.env.example`) and could be implemented by different people in parallel; this task list still lists them in the mandated US1→US2→US3 order for a single implementer/agent to follow sequentially.

---

## Parallel Example: User Story 1

```bash
# Launch both new US1 test files together (different files, no shared state):
Task: "Create tests/guardrails/test_operation_registry_menu_coverage.py with coverage/category/destructive-marker assertions"
Task: "Create tests/unit/test_operation_registry_fail_closed.py with fail-closed default assertions"
```

## Parallel Example: Documentation (Phase 6)

```bash
# All three doc updates touch different files - fully parallel:
Task: "Update README.md architecture/testing narrative"
Task: "Add CHANGELOG.md Unreleased entry"
Task: "Update quickstart.md Stage 2 test file path references"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003).
2. Complete Phase 2: Foundational (T004) — needed for US2 later, not blocking US1 itself.
3. Complete Phase 3: User Story 1 (T005-T017) — this alone closes the actual safety defect (fail-open → fail-closed classification, menu 194 explicitly destructive, exhaustive coverage guardrail).
4. **STOP and VALIDATE**: run the Phase 3 checkpoint test invocation; confirm SC-001/SC-002 are met.
5. This is a deployable safety fix on its own even before US2-US4 land.

### Incremental Delivery (mandated order for this feature)

1. Setup + Foundational → ready.
2. User Story 1 (fail-closed registry) → validate independently → safety defect closed (MVP).
3. User Story 2 (isolated venv guard) → validate independently → environment-integrity defect closed.
4. User Story 3 (credential preflight + config-template correction) → validate independently → diagnostic-clarity defect closed.
5. Documentation (Phase 6) → operator-facing docs now match the corrected behavior.
6. User Story 4 (iterative validation loop) → run the loop; expect **"externally blocked - operator-supplied credentials required"** as the honest terminal state in this environment (T043), with Stages 1-2 fully green (T040-T041).
7. Polish (Phase 8) → final full-gate evidence + secret-scan self-check.

### Operator Action Required to Close Out User Story 4

This feature cannot itself produce a live "clean run achieved" verdict (SC-006/SC-007) without operator-supplied real Mist credentials. Per spec Assumptions and FR-020, the correct and complete outcome of this task list, absent those credentials, is:

- Phases 1-6 and Phase 7's T040-T043/T046 fully executed and reported.
- T044/T045 explicitly marked not-yet-run, pending an operator copying `deploy/.env.example` to the repository-root `.env` (or equivalent env vars) with a real `MIST_HOST`, `MIST_APITOKEN`/`MIST_API_TOKEN`, and `org_id`, outside of source control.
- No task in this list should be modified, skipped, or weakened to fake a "clean run achieved" result in the absence of those credentials.

---

## Notes

- `[P]` tasks touch different files with no ordering dependency — safe to parallelize.
- `[Story]` label maps each task to its user story for traceability back to `spec.md`.
- Tests are written first within each story and must fail before the corresponding implementation task lands.
- The credential-gated `MistHelper.py --test`/`--testinteractive` live runs (T044/T045) are the only tasks in this entire list that perform real network calls; every other test/task is unit/guardrail-level with zero network and zero credentials, per FR-021/SC-008.
- Avoid: loosening the coverage guardrail's key-parity assertion, downgrading a genuinely safe export to a skip category "to make the gate pass" (explicitly disallowed by `contracts/operation_registry_classification_contract.md`), or fabricating/bypassing the credential dependency in T043.
