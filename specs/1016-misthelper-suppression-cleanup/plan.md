# Implementation Plan: MistHelper.py Suppression Cleanup

**Branch**: `1016-misthelper-suppression-cleanup` | **Date**: 2026-07-13 | **Spec**: `specs/1016-misthelper-suppression-cleanup/spec.md`

**Input**: Feature specification from `specs/1016-misthelper-suppression-cleanup/spec.md`

## Summary

Drive the four suppression comment families (`# noqa`, `# type: ignore`, `# nosec`, `# pylint: disable`) in `MistHelper.py` to exactly zero across 8 serial pull requests, one per GitHub issue in `{#895–#902}`. The technical approach is a targeted, low-blast-radius sequence: bootstrap `__all__` declaration first (removes the ~124-site import-suppression cluster and lets subsequent lint runs produce trustworthy signal), then typing hardening (assignment/misc mypy fixes, Protocol classes for the facade globals, concrete generic parameters), then complexity extraction on the residual monolithic symbols (`GlobalImportManager`, `DeviceFetchConfig`, `main()`), then presentation cleanup (E501 hand-wraps), then security review of subprocess call sites (with optional `subprocess_runner` helper), and finally a long-tail sweep. The public API surface of `MistHelper.py` is frozen for the entire workflow (FR-007), no new suppressions may be introduced anywhere in the repo (FR-008), and each PR waits for `mergeStateStatus=CLEAN` without administrative bypass.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution Technology & Compatibility Constraints).

**Primary Dependencies**: `ruff`, `pylint`, `mypy` (strict), `bandit`, `black`, `pytest`, `coverage`. Runtime deps unchanged (`mistapi>=0.59`, `structlog`, `sqlite3`).

**Storage**: N/A for this workflow — no schema or DB changes.

**Testing**: `pytest -v --tb=short` with `coverage.fail_under=90`; `pylint --fail-under=9.5`. Full test suite must pass on every merged commit.

**Target Platform**: Windows 11 dev (local venv), Linux container runtime (Podman) for CI. No platform-specific code touched.

**Project Type**: Single-project CLI tool with extracted `src/` subsystems.

**Performance Goals**: N/A — this is a suppression-hygiene workflow with no perf implications. Runtime behavior of `MistHelper.py` MUST be byte-identical from Story 1 start to Story 8 merge (SC-007).

**Constraints**:
- Public API surface of `MistHelper.py` frozen (FR-007); verified by `dir(MistHelper)` diff.
- Zero net new suppressions anywhere in the repository (FR-008).
- `pyproject.toml` edits limited to per-file-ignore removals (FR-010) — no rule disables, no fail-under lowering.
- Coverage ≥ 90% and pylint ≥ 9.5 hold on every merged commit (FR-016).
- Serial dispatch: PR N+1 does not open until PR N lands cleanly on `main` (FR-003).
- Each delivery PR branches from current `main` at PR-open time, NOT from `1016-misthelper-suppression-cleanup` (FR-004).

**Scale/Scope**:
- Target file: `MistHelper.py` (~5000 LOC residual after #1014). Contains bootstrap glue, module-level CLI/main, and `GlobalImportManager`/`DeviceFetchConfig`/`main()` symbols coupled to globals.
- Extracted subsystems in `src/`: `analytics`, `api`, `cache`, `device`, `export`, `gateway`, `input`, `inventory`, `org`, `reports`, `site`, `ssh`, `troubleshooting`, `ui`, `websocket`, `utils`, `db`.
- Two conditional `src/` additions permitted (FR-012): `src/utils/misthelper_facade.py` Protocol classes (Story 4) and `src/utils/subprocess_runner.py` helper (Story 7). Only these two additions to `src/` are allowed; all other edits must land in `MistHelper.py`.
- Audit source of truth: `tools/refactor_analyzer/` run on 2026-07-13; issue-body projections are stale (FR-014).

**Repo layout notes**:
- `MistHelper.py` residual functions are module-level CLI/bootstrap glue coupled to globals set by `GlobalImportManager`. Refactoring residual module-level functions into classes is **out of scope** for this workflow (FR-011); helper extraction is permitted only when narrowly required to eliminate a suppression in the current story.

**Development gates (mandatory before every push)**:
1. `rtk black --check .` — repo-wide format check; fix locally, never push and rely on CI.
2. `rtk ruff check .` — repo-wide lint; fix locally.
3. Full pytest suite green locally before opening PR.

**PR gates (mandatory before every merge)**:
- Wait for `mergeStateStatus=CLEAN` from `gh pr view <N> --json mergeStateStatus`. No `--admin` bypass under any circumstance (FR-006).
- Merge command pattern: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch` armed once, then poll.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: PASS (with explicit alignment).

The MistHelper Constitution v1.4.0 exists at `.specify/memory/constitution.md`. The most relevant principle for this workflow is **"Security Findings: Fix Over Suppress (NON-NEGOTIABLE)"** in the Development Workflow & Quality Gates section, which states:

> Never use `#nosec`, `# type: ignore`, `# noqa`, or similar suppressions as a shortcut to silence legitimate findings. If a finding requires more than a trivial fix, create a GitHub issue and track it.

This workflow is the direct realization of that principle: every suppression in `MistHelper.py` is being resolved at the root cause rather than moved, renamed, or bulk-disabled. No principle gates are violated. No entries are required in the Complexity Tracking table below on the basis of constitution violations.

Secondary alignment:
- **Principle II (Class-Based Architecture, No Wrappers)**: FR-011 explicitly forbids extracting further classes beyond narrow suppression-fix helpers, preserving the completed #1013/#1014 class boundaries.
- **Principle IV (Full Deployment Pipeline)**: The mandatory `rtk black --check .` + `rtk ruff check .` local gate documented above is the pre-push slice of the deployment pipeline; the container-build slice is unaffected because runtime behavior is unchanged.
- **Principles VI & VII (Inline Comments & Action Logging)**: Any new lines introduced by helper extractions (Story 3), Protocol definitions (Story 4), or `subprocess_runner` helpers (Story 7) MUST carry inline comments and, where they wrap meaningful actions, before/after logging.

## Project Structure

### Documentation (this feature)

```text
specs/1016-misthelper-suppression-cleanup/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output: audit + per-issue fix patterns
├── data-model.md        # Phase 1 output: __all__ list, Protocol shapes, helper boundaries
├── quickstart.md        # Phase 1 output: verification recipes per PR
├── contracts/           # Phase 1 output: contract fragments for public API + Protocols
│   ├── public_api.md
│   ├── misthelper_facade_protocols.md
│   └── subprocess_runner.md
└── tasks.md             # NOT produced by this command — /speckit.tasks generates it
```

### Source Code (repository root)

```text
MistHelper.py                                 # Target of every PR in this workflow.
                                              # Only the __all__ declaration, per-site
                                              # suppression removals, and narrow helper
                                              # extractions land here. No class extractions.

src/
├── utils/
│   ├── misthelper_facade.py                  # NEW in Story 4 (if not already present):
│   │                                         # Protocol classes covering facade call
│   │                                         # surface exposed to MistHelper.py.
│   └── subprocess_runner.py                  # NEW in Story 7 (conditional):
│                                             # centralized, audited subprocess entry
│                                             # point so B404 import moves to one file.
├── analytics/  api/  cache/  device/  export/  gateway/  input/  inventory/
├── org/        reports/  site/  ssh/  troubleshooting/  ui/  websocket/  db/
                                              # Untouched by this workflow (FR-012).

tools/refactor_analyzer/                      # Audit source of truth for FR-014/FR-015.
                                              # Re-run between stories to refresh deltas.

tests/                                        # Existing structure preserved. New tests
                                              # land next to the helpers/Protocols they
                                              # cover (Story 3 helpers, Story 4 Protocols,
                                              # Story 7 subprocess_runner).
```

**Structure Decision**: The Option 1 (single-project) layout is unchanged. This workflow does not introduce new top-level packages, does not restructure `src/`, and does not create a new `tests/` hierarchy. Two conditional additions inside `src/utils/` are the only permitted `src/` modifications (FR-012). All other work is confined to `MistHelper.py` and its accompanying test files.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Constitution Check passed with explicit alignment; no violations to track. The table below repurposes the section for its analogue use in this workflow: **per-issue effort estimate** to help pace serial dispatch under SC-009 (four calendar weeks target).

| Issue | Category | Est. suppression count | Est. effort | Ordering rationale |
|-------|----------|------------------------|-------------|--------------------|
| #895 | Bootstrap re-exports (`F401`, `pylint:unused-import`) | ~124 | Largest single cluster; day-scale | Must land first — cleans import signal for all subsequent lint runs. |
| #899 | Mypy grab-bag (`misc`, `assignment`, `no-any-return`, `arg-type`, `operator`) | 12–20 | Half-day–day | Fixes assignment sites (`X: type[Foo] \| None = None`) that gate Story 4's `no-untyped-call` fixes. |
| #901 | Complexity (`C901`, `PLR0913`) | 3–5 | Day | Helper extraction on `GlobalImportManager`, `DeviceFetchConfig`, `main()`. Landing before typing PRs shrinks their diff surface. |
| #898 | `no-untyped-call` | 8–15 | Day | Requires Protocol classes in `src/utils/misthelper_facade.py`. Depends on #899 assignment cleanup and #901 helper stabilization. |
| #897 | `type-arg` | ~3 | Half-day | Concrete generics; small isolated cluster. Runs after Protocols exist so annotations can reference them. |
| #896 | Line length (`E501`) | 5–15 | Half-day | Hand-wraps. Deferred so typing PRs don't reflow the same lines. Literal-template exemptions follow `plan_wave_builder.py` precedent. |
| #900 | Bandit (`B603`, `B404`) | 4–8 | Day | Input-validation audit + optional `subprocess_runner` helper. Deferred so security review lands on stable code. |
| #902 | Long tail (`PLC0415`, `E402`, `PLW0602`, residual mypy-misc) | 5–10 | Half-day | Final sweep; runs last so residual set is well-defined. |

Effort estimates assume the standard review cadence of ~1 PR per 2–3 working days (SC-009) and are advisory, not gating.

---

## Phase 0: Outline & Research

**Prerequisite**: none (spec captured all clarifications).

Phase 0 for this workflow is short — the spec already captured the audit, the ordering, and the fix pattern per cluster. The Phase 0 deliverable (`research.md`) consolidates three inputs into a single reviewable document:

1. **Read all 8 GitHub issue bodies** (`#895` through `#902`) via `gh issue view` and record their claimed suppression counts and locations. These numbers are historical projections and MUST be flagged as stale per FR-014 wherever they disagree with the 2026-07-13 audit.
2. **Re-run `tools/refactor_analyzer/`** on `MistHelper.py` at current `main` HEAD and capture fresh 2026-07-13 counts per suppression family. These counts are the ground truth (FR-014). Preserve the raw analyzer output as an appendix in `research.md`.
3. **Record the fix pattern per cluster** in the format Decision / Rationale / Alternatives Considered, mirroring the "Fix patterns per issue cluster" list embedded in this plan's Technical Context. Explicitly resolve the following pattern decisions:
   - **#895 hoist vs. inline `__all__`**: Decide whether to add `__all__` directly in `MistHelper.py` or hoist to `src/_bootstrap.py`. Default per user guidance: inline `__all__`; hoist only if it materially reduces suppression count. Record the trigger threshold for choosing hoist.
   - **#900 `subprocess_runner` helper**: Decide whether Story 7 introduces `src/utils/subprocess_runner.py` or performs per-site validation without a helper module. Trigger: if 3+ subprocess call sites remain post-audit, introduce the helper; otherwise per-site validation.
   - **#896 rendered-output exemptions**: Enumerate MistHelper.py lines whose reflow would change rendered CLI output (banners, table columns, prompt text). These follow the `plan_wave_builder.py` / `reporting.py` precedent and MUST be hand-wrapped without altering the rendered characters.

**Output**: `research.md` with all clarifications resolved, containing:
- Fresh 2026-07-13 audit counts per suppression family (baseline for FR-015 delta tracking).
- Per-issue fix-pattern decisions in Decision / Rationale / Alternatives format.
- Explicit hoist / helper thresholds for #895 and #900.
- Rendered-output exemption list for #896.

## Phase 1: Design & Contracts

**Prerequisite**: `research.md` complete.

### 1. Extract entities → `data-model.md`

The spec's Key Entities section names four operational entities. `data-model.md` records their concrete shape as it applies to this workflow:

- **`__all__` list (Story 1)**: The concrete list of module-level names to export from `MistHelper.py`. `data-model.md` captures the enumerated list, grouped by source subsystem (`analytics/`, `api/`, etc.), and the validation rule that this list must be a strict superset of every name currently accessible via `from MistHelper import <name>` at the workflow start (SC-007). Record whether the list will be defined inline in `MistHelper.py` or hoisted to `src/_bootstrap.py` per the Phase 0 decision.
- **Facade Global → Protocol mapping (Story 4)**: For each Any-typed module-level attribute in `MistHelper.py` currently exposed to callers, record the Protocol name, the exact method signatures it must cover, and the call sites in `MistHelper.py` that route through it. Validation rule: Protocol coverage MUST be exact — no unused methods, no missing methods, per Story 4 Acceptance Scenario 3.
- **Helper extraction boundaries (Story 3)**: For each of `GlobalImportManager`, `DeviceFetchConfig`, and `main()`, enumerate the intended helper functions/methods (name, single-sentence purpose, target size ≤ 25 lines per constitution Principle I). Validation rule: public signatures of the three target symbols MUST be unchanged post-extraction (Story 3 Acceptance Scenario 2).
- **`subprocess_runner` surface (Story 7, conditional)**: If Phase 0 triggered the helper, record its intended public entry point signature, the input-validation contract (allow-list vs. shlex.quote-equivalent), and the error-handling contract. Validation rule: coverage ≥ 90% (Story 7 Acceptance Scenario 3).

State transitions: this workflow has no runtime state changes; the "state" being modified is source-code hygiene, tracked externally by the audit-count delta per FR-015.

### 2. Define interface contracts → `contracts/`

`MistHelper.py` exposes a public API surface to external tools (FR-007). This workflow freezes that surface but formally documents it for the first time. Contracts are captured as Markdown fragments (project convention — no OpenAPI / IDL applies to a CLI module):

- `contracts/public_api.md`: The frozen public API. Enumerates every module-level name in `dir(MistHelper)` at workflow start. This document is the authoritative comparison baseline for SC-007. No PR in this workflow may reduce this set; Story 1's `__all__` MUST be a superset.
- `contracts/misthelper_facade_protocols.md`: The Protocol contracts for `src/utils/misthelper_facade.py`. One section per Protocol class, listing method signatures with type annotations and a two-line contract note per method.
- `contracts/subprocess_runner.md` (conditional, Story 7): Public entry point signature, input-validation rules, error-handling behavior for `src/utils/subprocess_runner.py`.

### 3. Quickstart → `quickstart.md`

`quickstart.md` records the verification recipe an operator or reviewer runs to confirm a given story is complete. One section per story, each containing:
- The exact `ruff` / `pylint` / `mypy` / `bandit` / `grep` commands that MUST return zero findings.
- The command to compare public API surface against `contracts/public_api.md` (SC-007).
- The pytest invocation covering that story's new helpers/Protocols.

### 4. Agent context update

Update the plan reference block between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` in `.github/copilot-instructions.md` to point at this plan file (`specs/1016-misthelper-suppression-cleanup/plan.md`). No other agent-context files change.

**Output**: `research.md`, `data-model.md`, `contracts/public_api.md`, `contracts/misthelper_facade_protocols.md`, `contracts/subprocess_runner.md` (conditional), `quickstart.md`, updated `.github/copilot-instructions.md`.

---

## Phase 2: Implementation Planning (Strategy)

> **Note**: `/speckit.tasks` generates `tasks.md` with per-file, per-code-site task decomposition. This section captures cross-PR strategy, ordering rationale, and the shared exit-criteria template. Individual code sites are NOT enumerated here.

### Merge ordering rationale

The 8 PRs land in the order `[#895, #899, #901, #898, #897, #896, #900, #902]`, chosen to minimize rework:

- **#895 first** removes ~124 import suppressions. Every subsequent lint run then produces trustworthy signal, reducing the noise ratio for reviewers of PRs 2–8.
- **#899 → #901 → #898** is a typing/complexity braid. #899's `assignment` fixes create the typed globals that #898's Protocol integration relies on; #901's helper extraction stabilizes the code shape #898 must annotate. Landing #901 between them shrinks the diff surface of #898.
- **#897** (small `type-arg` cluster) piggybacks on the now-stable Protocol/helper types.
- **#896** (E501 hand-wraps) lands after all typing PRs so no typing PR reflows lines already wrapped, avoiding merge conflicts.
- **#900** (bandit) reviews subprocess call sites that #901 may have restructured; landing after complexity is settled keeps the security audit tight.
- **#902** sweeps the residual long tail; deferring last guarantees the residual set is well-defined and not polluted by earlier PRs' side effects.

### Cross-PR invariants (apply to every PR)

- Public API surface of `MistHelper.py` unchanged; `diff <(python -c "import MistHelper; print('\n'.join(sorted(dir(MistHelper))))") contracts/public_api.md` produces no diff.
- No `# noqa`, `# type: ignore`, `# nosec`, or `# pylint: disable` comments are added anywhere in the repository (FR-008). Reviewers must grep the diff.
- `pyproject.toml` changes limited to per-file-ignore removals (FR-010).
- Only one PR from this workflow open at a time (SC-008); serial dispatch (FR-003).
- Delivery branches cut fresh from `main` — never from `1016-misthelper-suppression-cleanup` (FR-004).
- Pre-push local gate: `rtk black --check .` and `rtk ruff check .` MUST be clean before push.

### PR sub-phase enumeration

Each sub-phase corresponds to one delivery PR. The exit criteria are identical across sub-phases; only the target issue, cluster, and expected suppression-count delta vary.

**Sub-phase 1 — Story 1 / Issue #895 — Bootstrap re-exports**
- Entry: Phase 1 artifacts (`data-model.md` `__all__` list, `contracts/public_api.md`) merged into the feature branch. Fresh audit committed to `research.md`.
- Deliverable: `__all__ = [...]` declared in `MistHelper.py` (or hoisted to `src/_bootstrap.py` per Phase 0 decision); all `# noqa: F401` and `# pylint: disable=unused-import` comments removed from the file.
- Exit criteria: see template below.

**Sub-phase 2 — Story 2 / Issue #899 — Mypy grab-bag**
- Entry: PR #895 merged; `main` audit refreshed.
- Deliverable: `assignment` sites converted to `X: type[Foo] | None = None` typed declarations; per-site fixes for `misc`, `no-any-return`, `arg-type`, `operator`. All matching `# type: ignore` comments removed.
- Exit criteria: template.

**Sub-phase 3 — Story 3 / Issue #901 — Complexity extraction**
- Entry: PR #899 merged; `main` audit refreshed.
- Deliverable: narrow helpers extracted inside `GlobalImportManager`, `DeviceFetchConfig`, and `main()` per the boundaries in `data-model.md`. Public signatures of all three symbols unchanged. `# noqa: C901` and `# noqa: PLR0913` comments removed.
- Exit criteria: template + Story-3-specific: each extracted helper has at least one unit test invoked from the existing test suite, and helper coverage ≥ 90%.

**Sub-phase 4 — Story 4 / Issue #898 — no-untyped-call via Protocols**
- Entry: PR #901 merged; `main` audit refreshed; `contracts/misthelper_facade_protocols.md` up to date.
- Deliverable: `src/utils/misthelper_facade.py` contains Protocol classes per the contract; `MistHelper.py` call sites through the facade are annotated so mypy resolves them without `# type: ignore[no-untyped-call]`. All matching comments removed.
- Exit criteria: template + Story-4-specific: Protocol coverage is exact (no unused, no missing methods).

**Sub-phase 5 — Story 5 / Issue #897 — type-arg**
- Entry: PR #898 merged; `main` audit refreshed.
- Deliverable: concrete generic parameters (`dict[str, Any]`, `list[SomeType]`, etc.) added at the small number of `type-arg` sites. Matching `# type: ignore` comments removed.
- Exit criteria: template.

**Sub-phase 6 — Story 6 / Issue #896 — Line length**
- Entry: PR #897 merged; `main` audit refreshed.
- Deliverable: hand-wrapped long lines (or narrow helper extractions where clearly warranted) at every remaining `E501` site. Rendered-output-exempt lines per the Phase 0 list are wrapped without changing rendered characters. All `# noqa: E501` comments removed.
- Exit criteria: template + Story-6-specific: `black --check MistHelper.py` reports no diffs; file diff against pre-PR HEAD contains no logic changes, only whitespace/parenthesization/narrow-helper extractions.

**Sub-phase 7 — Story 7 / Issue #900 — Bandit**
- Entry: PR #896 merged; `main` audit refreshed.
- Deliverable: input-validation audit per subprocess call site with either (a) documented safe-usage justification (validated inputs, allow-list) and `# nosec` removed, or (b) call site routed through `src/utils/subprocess_runner.py` (introduced this PR if the Phase 0 threshold was met). `B404` addressed by encapsulating the subprocess import at the helper module. All `# nosec` comments in `MistHelper.py` removed.
- Exit criteria: template + Story-7-specific: if `subprocess_runner` was introduced, its coverage ≥ 90%.

**Sub-phase 8 — Story 8 / Issue #902 — Long tail**
- Entry: PR #900 merged; `main` audit refreshed.
- Deliverable: `PLC0415` late imports hoisted where safe; `E402` exemptions removed if the version-check pattern moves; residual mypy-misc / name-defined / var-annotated / `PLW0602` cleared. All remaining suppression comments in `MistHelper.py` removed.
- Exit criteria: template + Story-8-specific (final gate): grep `MistHelper.py` for `# noqa|# type: ignore|# nosec|# pylint: disable` returns zero matches (SC-001).

### Per-PR exit criteria template

Every delivery PR MUST satisfy all eight criteria before merge. This template is applied uniformly across sub-phases 1–8:

| # | Criterion | Verification |
|---|-----------|-------------|
| a | Target issue closed | PR description contains `Closes #<NNN>` referencing the sub-phase's issue; GitHub issue-linking status confirms auto-close on merge. |
| b | Suppression count for the target category → 0 in `MistHelper.py` | Category-specific grep or lint command returns zero findings (exact command per sub-phase; see `quickstart.md`). |
| c | Black + ruff clean | `rtk black --check .` and `rtk ruff check .` return zero findings locally AND in CI. |
| d | mypy for `MistHelper.py` has no new errors | `mypy MistHelper.py --strict` output has zero net-new errors relative to `main` at PR-open time (baseline captured in the PR description). |
| e | Full test suite green | `pytest -v --tb=short` passes in CI on the PR's head commit. |
| f | Coverage ≥ 90% | Coverage report on the PR's merge commit shows `coverage.fail_under=90` satisfied. |
| g | Pylint ≥ 9.5 | `pylint --fail-under=9.5` satisfied on the PR's merge commit. |
| h | `mergeStateStatus=CLEAN` | `gh pr view <N> --json mergeStateStatus` returns `CLEAN` immediately before invoking merge; no `--admin` bypass under any condition. |

Story-specific supplementary criteria (Stories 3, 4, 6, 7, 8) are enumerated inline in each sub-phase description above.

### Merge invocation pattern

Once all eight template criteria pass locally and in CI, and `mergeStateStatus=CLEAN`:

```bash
GITHUB_TOKEN= gh pr merge <PR_NUMBER> --auto --squash --delete-branch
```

Arm once, then poll `gh pr view <PR_NUMBER> --json state,mergeCommit` until state is `MERGED`. After merge, refresh the audit via `tools/refactor_analyzer/` before opening the next sub-phase's PR (FR-014 / FR-015).

---

## Stop-and-report

Phase 0 and Phase 1 artifacts are produced by this command. `tasks.md` is intentionally NOT produced — it is the output of the separate `/speckit.tasks` step. Individual code-site enumeration lives in `tasks.md`, not here.
