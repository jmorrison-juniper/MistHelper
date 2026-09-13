# Research: Decomposition Pattern Decisions

**Feature**: 198-radon-complexity-decomposition
**Phase**: 0 (Outline & Research)

All NEEDS CLARIFICATION items from Technical Context were resolved during spec authoring (the spec's Edge Cases and Assumptions sections already covered the unknowns). This document records the *why* behind each refactoring pattern decision so reviewers and future agents can audit the choice without re-deriving it.

---

## Decision 1 — `WebSocketManager.wait_for_command_result` (CC=110): Extract Class + State Dataclass

- **Decision**: Extract `WebSocketResultPoller` (drains incoming WS frames into a buffer), `CompletionDetector` (decides when polling is done based on accumulated state), and a `PollState` dataclass (the single shared state object passed by reference between collaborators).
- **Rationale**: At CC=110, no number of extracted private methods on `WebSocketManager` will land any individual method under CC=10 — the branching density is too high. The conditional logic falls into two cohesive groups (frame parsing/buffering vs. termination detection). A `PollState` dataclass replaces a tangle of local variables that today accumulate across nested loops (per the spec's Edge Cases: "no module-level globals"); explicit parameter passing is required by the project's 5-Item Rule (max 5 params, so a single dataclass param replaces 8+ locals).
- **Alternatives considered**:
  - *Pure Extract Method on `WebSocketManager`*: rejected — keeps `WebSocketManager` over the 5-Item file limit and each helper still inherits the deep nesting.
  - *Move to a single new class*: rejected — violates single-responsibility (polling vs. detection are distinct concerns).
  - *Async refactor*: rejected — out of scope per FR-006 (public surface preserved) and would change behavior.

---

## Decision 2 — `MistHelperTUI.handle_input` (CC=65) and similar long if/elif chains: Replace Conditional with Dispatch Table

- **Decision**: Build a `{key: bound_method}` dictionary once in `__init__` (or in the collaborator's constructor), keyed by the raw key code. Each handler method has its own CC ≤ 10. The dispatch lookup itself is O(1) and CC=1.
- **Rationale**: Long if/elif chains are pure conditional dispatch — the canonical refactor is a table. Building it once at construction (per the spec's Edge Cases) avoids the silent per-call cost of building the dict inside `handle_input` itself. mypy is happy with `Callable[[KeyCode], None]` annotation on the dict value type.
- **Alternatives considered**:
  - *Match statement (Python 3.10+ structural pattern matching)*: rejected — Radon still scores `match` statements with branching weight, and the project lint config prefers explicit dispatch tables for handler-style code.
  - *Visitor pattern*: rejected — overkill for a flat key->handler mapping; adds class hierarchy with no behavioral benefit.

---

## Decision 3 — `EnhancedSSHRunner._execute_with_shell` (CC=51) and `run_application` (CC=64): Extract Class per cohesive responsibility

- **Decision**: Extract `ShellSession` (owns the interactive shell channel lifecycle), `ApplicationRunner` (orchestrates application-style menu execution), `InteractiveOrchestrator` / `BatchOrchestrator` (multi-host execution modes). Each new class lives in a new submodule directory under `src/ssh/`.
- **Rationale**: `EnhancedSSHRunner` is the largest single class in the codebase (CC=12 at the class level, 13+ methods over CC=10). Method-extraction alone leaves the class itself over the 5-Item Rule. Submodule extraction grouped by responsibility (shell session vs. multi-host orchestration vs. config loading) keeps each new file ≤ 5 children and matches how operators reason about SSH operations.
- **Alternatives considered**:
  - *Inheritance hierarchy (`InteractiveSSHRunner(EnhancedSSHRunner)`, etc.)*: rejected — changes public surface (`isinstance` checks in callers), violates FR-006.
  - *Mixin classes*: rejected — mixins make the class diagram harder for junior NOC engineers (target audience) to follow.

---

## Decision 4 — Shared state passing across extracted collaborators: Dataclasses, not tuples or dicts

- **Decision**: When 3+ values must travel together between an extracted method and its caller (e.g., `PollState`, `LayoutContext`, `ExecCtx`), use a `@dataclass` with explicit named fields. Tuples are forbidden for this purpose. Dicts are forbidden because mypy can't enforce key presence.
- **Rationale**: Dataclasses keep the 5-param limit intact (one dataclass argument replaces 8+ positional args), give mypy full type coverage, and self-document the state shape. Tuples lose names; dicts lose typing.
- **Alternatives considered**:
  - *`typing.NamedTuple`*: acceptable fallback for immutable state, but immutability is rarely desired in TUI/polling state where fields update across the loop.
  - *`pydantic.BaseModel`*: rejected — adds a runtime dependency on pydantic that the codebase does not currently require.

---

## Decision 5 — Façade preservation: keep original class file as a thin delegator

- **Decision**: After extracting submodules, the original file (e.g., `src/ui/tui.py`) keeps `class MistHelperTUI` with all its public methods. Each public method body shrinks to: (a) one-line construction or lookup of the collaborator, (b) one-line delegation call, (c) one-line return. Inline comments and a `logging.info` / `logging.debug` bookend pair go on each delegation.
- **Rationale**: FR-006 requires public surface preservation. The façade pattern achieves this with zero risk of breaking external callers (`MistHelper.py`, `tests/`, `web_portal/`, `wsgi.py`) while keeping the per-method CC at 1–2.
- **Alternatives considered**:
  - *Import-time aliasing (e.g., `MistHelperTUI = NewTuiFacade`)*: rejected — opaque, breaks IDE navigation.
  - *Move the original class entirely and re-export*: rejected — changes the qualified name (`src.ui.tui.MistHelperTUI` -> `src.ui.tui.tui_facade.MistHelperTUI`), which `isinstance` checks and pickle would notice.

---

## Decision 6 — Inline comments + action logging on extracted code

- **Decision**: Every executable line in every new file carries a same-line inline comment explaining *why*. Every meaningful action (API call, file write, subprocess spawn, state mutation that affects another collaborator, user prompt) has `logging.info(...)` before and `logging.debug(...)` after.
- **Rationale**: NON-NEGOTIABLE per constitution principles VI and VII. SC-008 and SC-009 require ≥ 95% sampled compliance. Moving code out of an existing function without re-commenting and re-logging would actually *reduce* the project's observability footprint (the old code had at least some logging — the new helpers must match or exceed).
- **Alternatives considered**: *Skip comments on "obvious" lines* — rejected by principle VI: "Code without comments is incomplete code." Even one-line delegations get a comment explaining *which* collaborator and *why*.

---

## Decision 7 — Test-import compatibility for relocated private helpers

- **Decision**: Run `grep -RIn "from src.<module> import _" tests/` before each tier push; for any hit, update the test import to the new location in the same commit that moves the helper. Test *behavior* and *assertions* stay unchanged.
- **Rationale**: Tests must remain green after each commit (validation gate). Edge Cases section of the spec explicitly authorizes this.

---

## Decision 8 — Radon C-vs-B grade thresholding during interim work

- **Decision**: Per-tier validation gates use `radon cc -n D` (only D/E/F) after Tier 1 and `radon cc -n C` (C/D/E/F) after Tier 2 and Tier 3, matching the spec's tier definitions. Final gate uses `radon cc src/ -j` parsed with a Python one-liner that confirms zero offenders.
- **Rationale**: Allows intermediate-state pushes (e.g., after Tier 1, a few C-grade methods may still remain in Tier 2/3 files); without staged thresholding, no incremental commit could land. Final gate (after Tier 3) is the binary pass/fail CI condition.

---

All NEEDS CLARIFICATION items resolved. No outstanding research questions.
