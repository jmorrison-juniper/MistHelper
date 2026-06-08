# Feature Specification: Radon Cyclomatic Complexity Decomposition — PR #391 CI Unblock

**Feature Branch**: `feat/391-clone-device-config-to-gateway-template` (existing PR #391)
**Created**: 2026-06-08
**Status**: Draft
**Input**: User description: "Decompose all functions in `src/` with cyclomatic complexity > 10 into focused helper methods and (where cohesive) extracted classes/submodules. No exemptions, no `# noqa: C901`, no Radon allowlists. Unblock PR #391's CI."

## DIRECTIVE OVERRIDE (2026-06-08, applied retroactively)

**NO FAÇADES.** The original file is either deleted (with all callers updated to import
from the new submodule package directly) or it becomes the new primary implementation —
never a thin delegation shim. Public classes / method signatures may be renamed, relocated,
or removed; callers, tests, and imports MUST be updated in the same commit. Existing
`__init__.py` re-exports that exist solely for backwards compatibility must also go.

This supersedes any "preserve public class / preserve signature / façade pattern" language
below. The three Tier 1 façades already produced under the old approach
(`gateway_override_analyzer.py`, `gateway_override_analysis.py`, `auth/interactive_session.py`,
`websocket/diag_commands.py`) have been removed in commits `ac470f0`, `bf945cc`, `3952234`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Unblock PR #391 by Clearing Tier 1 Offenders (Priority: P1)

A maintainer pushes PR #391 (clone device config to gateway template). The Radon quality gate fails on CI because the base branch `feat/196` carries 75+ pre-existing functions with cyclomatic complexity > 10. The worst offenders (CC > 40) sit in `src/websocket/`, `src/ui/tui.py`, `src/ssh/ssh_runner.py`, and `src/auth/interactive_session.py`. The maintainer needs these six files restructured first because they alone account for the majority of the Radon gate's failure surface and are the most-touched modules in active development.

**Why this priority**: Without clearing the Tier 1 worst offenders the Radon gate will continue to fail, no matter how many smaller functions are fixed. These six files are also the highest-risk to refactor blindly, so they need first attention while the rest of the change set is still small.

**Independent Test**: After Tier 1 work merges, running `python -m radon cc src/websocket src/ui/tui.py src/ssh/ssh_runner.py src/auth/interactive_session.py src/gateway/gateway_override_analyzer.py -n C` returns "No blocks found" (no C-or-worse), and the existing test suite for these modules passes unchanged.

**Acceptance Scenarios**:

1. **Given** `src/websocket/manager.py` contains `wait_for_command_result` at CC=110, **When** Tier 1 refactor is applied, **Then** `wait_for_command_result` and every extracted helper has CC ≤ 10 and the websocket integration tests still pass.
2. **Given** `src/ui/tui.py` contains `handle_input` (CC=65), `check_keyboard_input` (CC=59), `execute_current_item` (CC=54), and `create_layout` (CC=52), **When** Tier 1 refactor is applied, **Then** each method and its helpers have CC ≤ 10 and the TUI continues to render menus, accept keyboard input, and execute selected items identically.
3. **Given** `src/ssh/ssh_runner.py` contains `_execute_with_shell` (CC=51) and related methods, **When** Tier 1 refactor is applied, **Then** SSH command execution, multi-host execution, and shell interactivity behave identically and CC ≤ 10 everywhere.

---

### User Story 2 — Clear Tier 2 Files for a Green Radon Gate (Priority: P2)

After Tier 1 lands, a smaller batch of high-complexity functions (CC 25–40) remains across `src/maps/`, `src/export/`, `src/auth/`, `src/ssh/`, and `src/websocket/`. The maintainer needs these cleared so `radon cc src/` reports zero offenders globally — the condition CI checks.

**Why this priority**: The Radon CI gate is binary: it only passes when every function in `src/` is ≤ 10. Tier 2 must complete before the gate can possibly turn green; however, these functions are individually less risky and less central than Tier 1.

**Independent Test**: After Tier 2 work merges, `python -m radon cc src/ -n C` returns no C-or-worse functions across the Tier 2 file list, and the export, maps, and auth test suites pass unchanged.

**Acceptance Scenarios**:

1. **Given** `src/maps/maps_manager.py::_launch_plotly_viewer` is CC=36, **When** Tier 2 refactor is applied, **Then** the Plotly viewer launches identically and CC ≤ 10.
2. **Given** `src/export/wifi_clients_exporter.py::execute` is CC=30, **When** Tier 2 refactor is applied, **Then** WiFi client CSV/SQLite/ArangoDB output is byte-identical and CC ≤ 10.
3. **Given** `src/auth/interactive_session.py::select_msp_and_org` is CC=26, **When** Tier 2 refactor is applied, **Then** the interactive MSP/org selection flow shows the same prompts and CC ≤ 10.

---

### User Story 3 — Finish the Long Tail (Tier 3) and Auto-Merge PR #391 (Priority: P3)

After Tiers 1 and 2 land, roughly 40 medium-complexity functions (CC 11–24) remain spread across `src/inventory/`, `src/troubleshooting/`, `src/gateway/`, `src/analytics/`, `src/site/`, `src/capture/`, and a few stragglers. With Tier 3 cleared, the Radon gate finally passes, `auto-merge` can be added to PR #391, and the clone-device-config-to-gateway-template feature reaches `main`.

**Why this priority**: Lowest individual risk per function but largest in count. Must finish to clear the gate, but each function is a small, mechanical extract-method change.

**Independent Test**: After Tier 3 work merges, `python -m radon cc src/ -j` reports zero functions with `complexity > 10` org-wide, the full CI pipeline (ruff, black, mypy, radon, pytest, bandit, pip-audit, codeql) is green on PR #391, and the `auto-merge` label successfully squashes PR #391 into `main`.

**Acceptance Scenarios**:

1. **Given** all Tier 1 and Tier 2 work has merged, **When** Tier 3 work is applied across the listed modules, **Then** `radon cc src/ -j | python -c "..."` reports "All functions within complexity threshold."
2. **Given** the full Radon gate now passes, **When** the maintainer adds the `auto-merge` label to PR #391 after CodeQL completes, **Then** the squash-merge succeeds and `main` contains the clone-device-config feature.

---

### Edge Cases

- **Class-level complexity (NC metric)**: Radon also reports class-level complexity (e.g., `WebSocketNetworkDiagCommands` CC=50, `WebSocketCommands` CC=29). Extract-method refactors at the method level naturally reduce class CC; if any class still exceeds 10 after method extraction, extract a collaborator class into a new submodule.
- **Methods called from outside `src/`** (e.g., from `MistHelper.py` or `tests/`): public signatures and class names MUST remain stable. Internal/private helpers may be added or renamed freely.
- **Hidden state in long methods**: Some Tier 1 methods (notably `wait_for_command_result`) accumulate state across nested loops. Extracted helpers must receive state explicitly via parameters or via a small dataclass — no module-level globals.
- **Logging continuity**: All existing user-facing log lines and prompts must be preserved verbatim so NOC engineers see the same output stream before and after refactor.
- **Dispatch-table refactors for long `if/elif` chains**: When replacing conditionals (e.g., TUI keyboard handlers, diag command parsers) with `{key: handler}` dictionaries, the dispatch table must be built once at construction time (not on every call) to avoid silent performance regressions.
- **Test fixtures referring to private helpers**: If any existing test imports a private `_helper` that gets relocated, the test is updated to the new location; test *behavior* and assertions stay unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every function and method in `src/` MUST have cyclomatic complexity ≤ 10 as reported by `radon cc src/ -j`.
- **FR-002**: The refactor MUST NOT use any complexity suppression marker — no `# noqa: C901`, no `# pylint: disable=too-many-branches/statements/locals/nested-blocks`, no Radon allowlist additions, no `pyproject.toml` exemption entries.
- **FR-003**: Every Tier 1 file (`src/websocket/manager.py`, `src/ui/tui.py`, `src/websocket/diag_commands.py`, `src/ssh/ssh_runner.py`, `src/auth/interactive_session.py`, `src/gateway/gateway_override_analyzer.py`) MUST be decomposed first, before Tier 2 or Tier 3 work begins.
- **FR-004**: Decomposition MUST use one or more of: Extract Method (private helper), Extract Class (collaborator in same module), Extract Submodule (new directory under the parent package), Replace Conditional with Dispatch Table, Guard Clauses / Early Returns.
- **FR-005**: All extracted helper methods MUST themselves have CC ≤ 10.
- **FR-006**: All public class names, public method names, and public method signatures called from outside `src/` (`MistHelper.py`, `tests/`, `web_portal/`, or other top-level modules) MUST remain unchanged.
- **FR-007**: All extracted submodules MUST live under `src/<parent_package>/<new_submodule>/` and follow the project's 5-Item Rule (max 5 children per level).
- **FR-008**: Every line of new code (every extracted helper, every new class, every new submodule) MUST carry an inline comment explaining *why* per the project's NON-NEGOTIABLE inline-comment standard.
- **FR-009**: Every meaningful action in new code MUST be wrapped in action logging — `logging.info(...)` before the action, `logging.debug(...)` after with a result summary, per the project's NON-NEGOTIABLE action-logging standard.
- **FR-010**: All existing user-facing strings (prompts, log lines, error messages, menu labels) MUST be preserved verbatim in the new code paths.
- **FR-011**: No new third-party dependencies MAY be added; the refactor is pure restructuring of existing code.
- **FR-012**: `MistHelper.py` top-level dispatcher logic MUST NOT be modified by this work; only `src/` package code is in scope.
- **FR-013**: Database schemas, primary-key strategies in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, CLI flags, and menu numbers MUST remain unchanged.
- **FR-014**: Work MUST be delivered in three sequential tier waves (Tier 1 → Tier 2 → Tier 3); each wave MUST pass all local quality gates (`ruff check`, `black --check`, `mypy src/`, `pytest tests/guardrails/`, `radon cc -n C src/` over the wave's file set) before being pushed.
- **FR-015**: On completion, PR #391 MUST pass the full CI pipeline (ruff, black, mypy, radon, pytest, bandit, pip-audit, codeql) and MUST be eligible for the `auto-merge` label per the project's existing auto-merge policy (CodeQL must finish before label is added).

### Key Entities

- **Tier 1 Offenders (Files)**: The six files containing CC > 40 functions/classes. Must be fully cleared before any Tier 2 work starts. Carry the highest behavioral risk.
- **Tier 2 Offenders (Files)**: Files containing CC 25–40 functions. Cleared after Tier 1. Medium behavioral risk.
- **Tier 3 Offenders (Files)**: ~10–15 files containing the long tail of CC 11–24 functions. Cleared last. Lowest risk per function but largest in count.
- **Extracted Helper Method**: A new private method (`_verb_noun`) on the same class as the original. Receives state explicitly via parameters. Has CC ≤ 10. Carries inline comments and action logging.
- **Extracted Collaborator Class**: A new class in the same module (or a new submodule) when 3+ logically distinct responsibility groups are pulled out of one method. Example: `WebSocketResultPoller` and `WebSocketCompletionDetector` extracted from `wait_for_command_result`.
- **Extracted Submodule**: A new directory (e.g., `src/websocket/polling/`, `src/ui/input_handlers/`) holding one or more collaborator classes that form a coherent unit.
- **Dispatch Table**: A `{key: bound_method}` dictionary built once in `__init__` that replaces a long `if/elif` chain (TUI key handlers, diag command parsers). Each handler method has CC ≤ 10.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python -m radon cc src/ -j` reports zero functions with `complexity > 10` across the entire `src/` tree.
- **SC-002**: `python -m radon cc -n C src/` produces no output (no C-grade-or-worse blocks found).
- **SC-003**: Zero new `# noqa: C901`, zero new `# pylint: disable` directives, and zero new Radon-suppression entries in `pyproject.toml` are introduced by this work (verified by `git diff` of merged PRs).
- **SC-004**: The full local gate suite passes on `feat/391-clone-device-config-to-gateway-template` after each tier wave: `ruff check .` clean, `black --check .` clean, `mypy src/ --config-file pyproject.toml` clean, `pytest tests/guardrails/ -q` shows 40+ tests passing.
- **SC-005**: PR #391 CI shows green for all required checks (ruff, black, mypy, radon, pytest, bandit, pip-audit, codeql), the `auto-merge` label is successfully added after CodeQL completes, and the squash-merge to `main` succeeds.
- **SC-006**: Test coverage on `src/` (as reported by `pytest --cov=src`) remains ≥ 80% — i.e., does not drop versus the pre-refactor baseline on `feat/391-clone-device-config-to-gateway-template`.
- **SC-007**: No regression in observable behavior: spot-validation runs of representative menu operations (one per affected module — websocket diag, TUI menu navigation, SSH multi-host execute, MSP/org selection, WiFi clients export, Plotly maps viewer) produce identical output to a pre-refactor baseline capture.
- **SC-008**: Every new code line in extracted helpers/classes/submodules carries an inline comment (sampled audit: ≥ 95% of new executable lines have a same-line comment).
- **SC-009**: Every meaningful action in new code has a `logging.info` before and a `logging.debug` after (sampled audit: ≥ 95% of new actions have both bookends).

## Assumptions

- The pre-existing baseline of 75+ Radon violations is inherited from `feat/196` and is not the work of PR #391 itself; this spec accepts responsibility for clearing the entire baseline as the cost of merging PR #391.
- The existing test suite under `tests/` (especially `tests/guardrails/`) is considered the authoritative behavioral contract; any extracted helper must satisfy these tests unchanged.
- The 5-Item Rule (max 5 children per hierarchy level, max 5 parameters, max 25 lines per function) from `coding-standards.instructions.md` applies to all new code and constrains the granularity of helper extraction.
- The user accepts a multi-PR delivery model if the tier waves grow too large for a single PR, but the *preferred* path is one PR per tier wave (three PRs total, all targeting `main`, the last one of which unblocks PR #391's rebase + auto-merge). Final shape (single PR vs three PRs) is a maintainer judgment call based on diff size — both shapes satisfy this spec.
- The `auto-merge` policy from `.github/copilot-instructions.md` (wait for CodeQL on code PRs) applies to every PR produced by this work.
- All tier waves stay on Windows 11 + the existing `.venv` Python 3.13 environment; no environment changes are needed.
- The `data/` directory, container images, `.env` configuration, and SSH runner credentials remain untouched.
- Dispatch-table refactors are acceptable to type checkers (`mypy`) as long as handler methods share a compatible signature; if `mypy` complains, a `typing.Protocol` or `Callable[..., None]` annotation may be added.
- If a Tier 1 method (e.g., `wait_for_command_result` at CC=110) cannot reach CC ≤ 10 with method extraction alone, extracting a collaborator class is required — the spec authorizes this without further design review.
