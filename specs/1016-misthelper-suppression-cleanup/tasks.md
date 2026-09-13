# Tasks: MistHelper.py Suppression Cleanup

**Input**: Design documents from `specs/1016-misthelper-suppression-cleanup/`

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/public_api.md`, `contracts/misthelper_facade_protocols.md`, `contracts/subprocess_runner.md`

**Tests**: Tests are ONLY required for helpers/Protocols/subprocess_runner introduced by Stories 3, 4, and 7. No new tests for pure suppression-removal PRs.

**Organization**: Tasks are grouped by delivery pull request (T-01 through T-08 map to PR-1 through PR-8), plus a T-09 final workflow-level verification. Every PR is strictly sequential per FR-003 (SC-008) — PR N+1 does NOT open until PR N is merged. Within a PR, sub-tasks are strictly sequential unless marked `[P]`.

## Format: `[TaskID] [P?] [Story?] Description`

- **[P]**: Can run in parallel with other `[P]` tasks in the same PR (different files/edits, no ordering deps)
- **[Story]**: Which user story this task belongs to (US1–US8, one per PR)
- Include exact file paths in descriptions

## Path Conventions

Single-project layout (per `plan.md` Project Structure). All work lands in `MistHelper.py` at repo root, plus two conditional `src/utils/` additions:

- `src/utils/misthelper_facade.py` (Story 4, mandatory)
- `src/utils/subprocess_runner.py` (Story 7, conditional per `research.md` threshold)

No other `src/` files may be modified (FR-012).

---

## PR-1: Issue #895 — Bootstrap `__all__` + F401/unused-import removal (Priority: P1) 🎯 MVP

**Goal**: Add an `__all__` declaration to `MistHelper.py` that enumerates every re-exported symbol, then delete all `# noqa: F401` and `# pylint: disable=unused-import` comments from the bootstrap import block.

**Independent Test**: After merge, `ruff check MistHelper.py --select F401` and `pylint MistHelper.py --disable=all --enable=unused-import` both report zero findings; `grep -nE '# (noqa: F401|pylint: disable=unused-import)' MistHelper.py` returns zero matches; `python -c "import MistHelper; print(len(MistHelper.__all__))"` succeeds; every `from MistHelper import <name>` used by `tools/`, `tests/`, `web_portal/`, and `wsgi.py` continues to resolve.

- [ ] T-01.1 [US1] Audit: run `grep -cE '# (noqa: F401|pylint: disable=unused-import)' MistHelper.py` and record the current count in the PR body; compare against the 2026-07-13 baseline in `research.md` and flag any delta.
- [ ] T-01.2 [US1] Branch: run `git switch main && git pull && git switch -c misthelper-bootstrap-all-895` from repo root.
- [ ] T-01.3 [US1] Implement in `MistHelper.py`: enumerate every symbol imported by external consumers by grepping the repo for `from MistHelper import` and `import MistHelper` across `tools/`, `tests/`, `web_portal/`, and `wsgi.py`; use that union set (validated against `contracts/public_api.md`) to define `__all__ = [...]` in `MistHelper.py`; remove every `# noqa: F401` and `# pylint: disable=unused-import` comment from the bootstrap re-export block. Optionally hoist the import block to `src/_bootstrap.py` ONLY if it eliminates more suppressions than it introduces (per `research.md` hoist threshold).
- [ ] T-01.4 [US1] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest`, then `grep -cE '# (noqa: F401|pylint: disable=unused-import)' MistHelper.py` and confirm zero. Diff `python -c "import MistHelper; print('\n'.join(sorted(dir(MistHelper))))"` against `specs/1016-misthelper-suppression-cleanup/contracts/public_api.md` to confirm SC-007.
- [ ] T-01.5 [US1] Commit + push: stage `MistHelper.py` (and `src/_bootstrap.py` if the hoist was taken); commit with a body referencing the audit delta; push the `misthelper-bootstrap-all-895` branch to remote.
- [ ] T-01.6 [US1] Open PR with `Closes #895` trailer using `gh pr create --base main --head misthelper-bootstrap-all-895` and include the pre/post grep counts in the PR body per FR-015.
- [ ] T-01.7 [US1] Wait for CI + `mergeStateStatus=CLEAN`: poll `gh pr view <N> --json mergeStateStatus,statusCheckRollup` until state is CLEAN and all required checks are SUCCESS.
- [ ] T-01.8 [US1] Arm auto-merge and land: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch` (no `--admin` bypass under any circumstance per FR-006).
- [ ] T-01.9 [US1] Confirm merged: `gh pr view <N> --json state,mergeCommit` returns `MERGED`; issue #895 is closed by GitHub auto-close; branch `misthelper-bootstrap-all-895` is deleted on remote. Refresh audit via `tools/refactor_analyzer/` and commit the refreshed numbers to the feature branch before opening PR-2.

**Checkpoint**: MistHelper.py bootstrap import block is suppression-free; ~124 suppressions removed.

---

## PR-2: Issue #899 — Mypy grab-bag (assignment/misc/no-any-return/arg-type/operator) (Priority: P2)

**Goal**: Eliminate the mixed mypy suppression cluster in `MistHelper.py`. For the 12 `assignment` sites, promote to typed declarations (`X: type[Foo] | None = None`). For the 11 `misc` sites, resolve root cause per site. For no-any-return/arg-type/operator, fix per site — no bulk pattern.

**Independent Test**: After merge, `mypy MistHelper.py --strict` reports zero findings in categories `misc`, `assignment`, `no-any-return`, `arg-type`, `operator`; `grep -nE '# type: ignore\[(misc|assignment|no-any-return|arg-type|operator)' MistHelper.py` returns zero matches.

- [ ] T-02.1 [US2] Audit: run `grep -cE '# type: ignore\[(misc|assignment|no-any-return|arg-type|operator)' MistHelper.py` and record the count per subcategory; compare against `research.md` 2026-07-13 baseline and flag any delta.
- [ ] T-02.2 [US2] Branch: run `git switch main && git pull && git switch -c misthelper-mypy-grabbag-899`.
- [ ] T-02.3 [US2] Implement in `MistHelper.py`: for each of the 12 `assignment` sites, replace `X = None  # type: ignore[assignment]` with `X: type[Foo] | None = None` (use the concrete class name — no `Any`); for each of the 11 `misc` sites, read the surrounding call context and fix the root cause (typically a legitimate `Any` narrowing, an incorrect return-type declaration, or a missing overload). For no-any-return, arg-type, and operator sites, fix per site: add explicit return annotations for no-any-return; narrow argument types for arg-type; add `__add__`/`__eq__`-style method signatures or use `typing.cast` sparingly for operator. Delete every matching `# type: ignore[...]` comment.
- [ ] T-02.4 [US2] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest`, `mypy MistHelper.py --strict`, then `grep -cE '# type: ignore\[(misc|assignment|no-any-return|arg-type|operator)' MistHelper.py` — confirm zero. Diff `dir(MistHelper)` against `contracts/public_api.md`.
- [ ] T-02.5 [US2] Commit + push: stage `MistHelper.py`; commit with the pre/post grep counts in the body; push the branch.
- [ ] T-02.6 [US2] Open PR with `Closes #899` trailer via `gh pr create --base main --head misthelper-mypy-grabbag-899`; include audit delta per FR-015.
- [ ] T-02.7 [US2] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-02.8 [US2] Arm auto-merge and land: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-02.9 [US2] Confirm merged, #899 closed, branch deleted; refresh audit via `tools/refactor_analyzer/` before PR-3.

**Checkpoint**: Assignment/misc/no-any-return/arg-type/operator suppressions in MistHelper.py are zero.

---

## PR-3: Issue #901 — Complexity extraction (C901 + PLR0913) (Priority: P3)

**Goal**: Extract narrow helper methods inside `GlobalImportManager`, split `main()` argparser + dispatch, and break `DeviceFetchConfig`'s PLR0913 signature via a small dataclass or two-phase init. Public signatures of all three symbols MUST remain unchanged.

**Independent Test**: After merge, `ruff check MistHelper.py --select C901,PLR0913` returns zero findings; no `# noqa: C901` or `# noqa: PLR0913` comments remain; each extracted helper has ≥1 unit test with helper coverage ≥ 90%; overall project coverage ≥ 90%.

- [ ] T-03.1 [US3] Audit: run `grep -cE '# noqa: (C901|PLR0913)' MistHelper.py` and record; compare against `research.md` baseline.
- [ ] T-03.2 [US3] Branch: run `git switch main && git pull && git switch -c misthelper-complexity-901`.
- [ ] T-03.3 [US3] Implement in `MistHelper.py`: (a) extract narrow helper methods inside `GlobalImportManager` per the boundaries enumerated in `data-model.md` (each helper ≤ 25 lines, single responsibility, inline-commented per constitution Principle VI); (b) split `main()` into `_build_arg_parser()` + `_dispatch_command()` helpers plus a thin `main()` orchestrator; (c) break `DeviceFetchConfig`'s PLR0913 signature by grouping args into a small dataclass or two-phase init as chosen in `data-model.md`. Delete every `# noqa: C901` and `# noqa: PLR0913` comment. Public signatures of `GlobalImportManager`, `DeviceFetchConfig`, and `main()` MUST be byte-identical to pre-PR HEAD.
- [ ] T-03.4 [US3] Add tests: land at least one unit test per extracted helper in `tests/` (next to the closest existing test file); confirm helper coverage ≥ 90% via `pytest --cov`.
- [ ] T-03.5 [US3] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov`, `pylint --fail-under=9.5 MistHelper.py`, then `grep -cE '# noqa: (C901|PLR0913)' MistHelper.py` — confirm zero. Diff `dir(MistHelper)` against `contracts/public_api.md`.
- [ ] T-03.6 [US3] Commit + push: stage `MistHelper.py` and new test files; push the branch.
- [ ] T-03.7 [US3] Open PR with `Closes #901` trailer via `gh pr create --base main --head misthelper-complexity-901`; include audit delta and coverage numbers per FR-015.
- [ ] T-03.8 [US3] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-03.9 [US3] Arm auto-merge and land: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`; confirm #901 closed, branch deleted; refresh audit before PR-4.

**Checkpoint**: `GlobalImportManager`, `DeviceFetchConfig`, and `main()` are C901/PLR0913-clean; their public signatures are unchanged.

---

## PR-4: Issue #898 — no-untyped-call via Protocol classes (Priority: P4)

**Goal**: Read `contracts/misthelper_facade_protocols.md`, create/update `src/utils/misthelper_facade.py` with Protocol classes typing every Any-typed facade global (mistapi client, session-like objects, etc.), retype the module-level declarations in `MistHelper.py` using those Protocols, and delete every `# type: ignore[no-untyped-call]` comment.

**Independent Test**: After merge, `mypy MistHelper.py --strict` reports zero `no-untyped-call` findings; no `# type: ignore[no-untyped-call]` comments remain in `MistHelper.py`; `src/utils/misthelper_facade.py` defines Protocol classes whose method coverage is exact (no unused methods, no missing methods) per Story 4 Acceptance Scenario 3.

- [ ] T-04.1 [US4] Audit: run `grep -cE '# type: ignore\[no-untyped-call' MistHelper.py` and record; compare against `research.md`.
- [ ] T-04.2 [US4] Branch: run `git switch main && git pull && git switch -c misthelper-facade-protocols-898`.
- [ ] T-04.3 [US4] Implement Protocols in `src/utils/misthelper_facade.py`: create the Protocol classes per `contracts/misthelper_facade_protocols.md`, one class per facade surface (mistapi client, session-like objects, etc.), each with the exact method signatures the contract specifies. Inline-comment each Protocol per constitution Principle VI.
- [ ] T-04.4 [US4] Retype declarations in `MistHelper.py`: annotate every module-level facade global with the Protocol from step T-04.3 (e.g., `mistapi_client: MistApiClientProtocol | None = None`). Delete every `# type: ignore[no-untyped-call]` comment.
- [ ] T-04.5 [US4] Add Protocol coverage tests: land tests under `tests/` verifying the Protocol classes match the exact facade surface (structural conformance test); confirm no unused methods, no missing methods per Story 4 Acceptance Scenario 3.
- [ ] T-04.6 [US4] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest`, `mypy MistHelper.py src/utils/misthelper_facade.py --strict`, then `grep -cE '# type: ignore\[no-untyped-call' MistHelper.py` — confirm zero. Diff `dir(MistHelper)` against `contracts/public_api.md`.
- [ ] T-04.7 [US4] Commit + push + open PR with `Closes #898` via `gh pr create --base main --head misthelper-facade-protocols-898`; include audit delta.
- [ ] T-04.8 [US4] Wait for CI + `mergeStateStatus=CLEAN`; arm auto-merge with `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-04.9 [US4] Confirm merged, #898 closed, branch deleted; refresh audit before PR-5.

**Checkpoint**: All no-untyped-call sites in `MistHelper.py` resolve through Protocol classes.

---

## PR-5: Issue #897 — type-arg concrete generics (Priority: P5)

**Goal**: Grep the 3 `type-arg` sites in `MistHelper.py`, add concrete generic parameters (`dict[str, Any]`, `list[SomeType]`, etc.), and delete the ignores.

**Independent Test**: After merge, `mypy MistHelper.py --strict` reports zero `type-arg` findings; `grep -nE '# type: ignore\[type-arg' MistHelper.py` returns zero matches.

- [ ] T-05.1 [US5] Audit: run `grep -cE '# type: ignore\[type-arg' MistHelper.py`, expect ~3 sites; compare against `research.md`.
- [ ] T-05.2 [US5] Branch: run `git switch main && git pull && git switch -c misthelper-typearg-897`.
- [ ] T-05.3 [US5] Implement in `MistHelper.py`: for each of the 3 `type-arg` sites, add the concrete generic parameter (`dict[str, Any]`, `list[SomeType]`, or the specific type indicated by call-site inspection — never bare `dict` or `list`); delete each `# type: ignore[type-arg]` comment.
- [ ] T-05.4 [US5] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest`, `mypy MistHelper.py --strict`, then `grep -cE '# type: ignore\[type-arg' MistHelper.py` — confirm zero. Diff `dir(MistHelper)` against `contracts/public_api.md`.
- [ ] T-05.5 [US5] Commit + push + open PR with `Closes #897` via `gh pr create --base main --head misthelper-typearg-897`; include audit delta.
- [ ] T-05.6 [US5] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-05.7 [US5] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-05.8 [US5] Confirm merged, #897 closed, branch deleted; refresh audit before PR-6.

**Checkpoint**: All type-arg suppressions in MistHelper.py are zero.

---

## PR-6: Issue #896 — E501 line-length hand-wrap (Priority: P6)

**Goal**: Hand-wrap each of the 54 `E501` lines in `MistHelper.py` (or, where clearly warranted, extract a narrow helper). Constraints: never reflow literal template strings or user-facing multi-line prompts; if any line is a literal template, escalate — do not force-wrap.

**Independent Test**: After merge, `ruff check MistHelper.py --select E501` returns zero findings; `grep -nE '# noqa: E501' MistHelper.py` returns zero matches; `black --check MistHelper.py` reports no diffs; file diff contains no logic changes, only whitespace/parenthesization/narrow-helper extractions.

- [ ] T-06.1 [US6] Audit: run `grep -cE '# noqa: E501' MistHelper.py`, expect ~54 sites; compare against `research.md`. Cross-reference each site against the rendered-output-exempt list in `research.md` and confirm the escalation set is empty (if not, halt and escalate per Story 6 constraints).
- [ ] T-06.2 [US6] Branch: run `git switch main && git pull && git switch -c misthelper-line-length-896`.
- [ ] T-06.3 [US6] Implement in `MistHelper.py`: hand-wrap each of the 54 `E501` lines using black-compatible parenthesization, trailing commas, and continuation-line indentation. Where a single-line f-string clearly warrants a helper (e.g., building a multi-line log record), extract a narrow helper (≤ 10 lines) rather than force-wrap. Never reflow literal template strings or user-facing multi-line prompts; those must be hand-wrapped without changing rendered characters (per `plan_wave_builder.py` precedent). Delete every `# noqa: E501` comment.
- [ ] T-06.4 [US6] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest`, then `grep -cE '# noqa: E501' MistHelper.py` — confirm zero. Confirm rendered CLI output is byte-identical (spot-check `python -m MistHelper --help` output against pre-PR HEAD). Diff `dir(MistHelper)` against `contracts/public_api.md`.
- [ ] T-06.5 [US6] Commit + push + open PR with `Closes #896` via `gh pr create --base main --head misthelper-line-length-896`; include audit delta per FR-015; note in the PR body that the diff contains no logic changes.
- [ ] T-06.6 [US6] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-06.7 [US6] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-06.8 [US6] Confirm merged, #896 closed, branch deleted; refresh audit before PR-7.

**Checkpoint**: All E501 suppressions in MistHelper.py are zero.

---

## PR-7: Issue #900 — Bandit subprocess audit + `subprocess_runner` helper (Priority: P7)

**Goal**: For 9 `B603` subprocess sites, audit input validation. Where inputs come from validated CLI args or hardcoded values, remove `nosec` after documenting the validation. Where inputs are untrusted, add explicit allow-list validation. For `B404` module-import `nosec`, create `src/utils/subprocess_runner.py` per contract; move the `subprocess` import there once; call sites use the helper's exported functions.

**Independent Test**: After merge, `bandit -r MistHelper.py` reports zero findings; `grep -nE '# nosec' MistHelper.py` returns zero matches; each affected subprocess call site is either (a) documented with validated inputs in an inline comment or (b) routed through `subprocess_runner`; if `subprocess_runner.py` was introduced, its coverage ≥ 90%.

- [ ] T-07.1 [US7] Audit: run `grep -cE '# nosec' MistHelper.py`, expect ~10 sites (9 B603 + 1 B404); enumerate each site with its subprocess-call context. Compare against `research.md` 2026-07-13 baseline and confirm the `subprocess_runner` threshold decision (introduce helper if ≥ 3 call sites remain post-validation; else per-site validation only).
- [ ] T-07.2 [US7] Branch: run `git switch main && git pull && git switch -c misthelper-bandit-subprocess-900`.
- [ ] T-07.3 [US7] [P] Implement `src/utils/subprocess_runner.py` (conditional, only if T-07.1 triggered the threshold): create the helper per `contracts/subprocess_runner.md` — one public entry point (e.g., `run_validated(cmd: list[str], *, allow_list: Sequence[str], ...)`), input-validation contract via allow-list, explicit error-handling contract, structured logging per constitution Principle VII. Move the `subprocess` import to this module so `B404` collapses to one call site. Inline-comment per constitution Principle VI.
- [ ] T-07.4 [US7] [P] Add tests for `subprocess_runner` (if introduced): land tests under `tests/` covering happy path, allow-list rejection, and error propagation; confirm coverage ≥ 90% via `pytest --cov=src.utils.subprocess_runner`.
- [ ] T-07.5 [US7] Retype call sites in `MistHelper.py`: for each of the 9 B603 sites, either (a) document inline validation and delete `# nosec` where inputs are validated CLI args or hardcoded, or (b) route the call through `subprocess_runner.run_validated(...)`. Delete every `# nosec` comment.
- [ ] T-07.6 [US7] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest --cov`, `bandit -r MistHelper.py src/utils/subprocess_runner.py`, then `grep -cE '# nosec' MistHelper.py` — confirm zero. Diff `dir(MistHelper)` against `contracts/public_api.md`.
- [ ] T-07.7 [US7] Commit + push + open PR with `Closes #900` via `gh pr create --base main --head misthelper-bandit-subprocess-900`; include audit delta and (if applicable) `subprocess_runner` coverage numbers per FR-015.
- [ ] T-07.8 [US7] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-07.9 [US7] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`; confirm merged, #900 closed, branch deleted; refresh audit before PR-8.

**Checkpoint**: All bandit suppressions in MistHelper.py are zero; subprocess call sites are validated or routed through `subprocess_runner`.

---

## PR-8: Issue #902 — Long-tail sweep (PLC0415 / E402 / residual mypy-misc / etc.) (Priority: P8)

**Goal**: Per-site fixes for `PLC0415` (2 late-import sites — hoist if safe), `E402` (7 sites — mostly the version-check preamble; document if unavoidable and remove exemption), and remaining `mypy-misc`/`name-defined`/`var-annotated` per site. Any sites that truly cannot be fixed require a `plan.md` update explaining why — this should not happen because spec forbids new suppressions.

**Independent Test** (also serves as the final SC-001 gate): After merge, `grep -nE '# (noqa|type: ignore|nosec|pylint: disable)' MistHelper.py` returns zero matches; full lint stack (`ruff check`, `pylint`, `mypy --strict`, `bandit -r`, `black --check`) passes on the file with no suppressions.

- [ ] T-08.1 [US8] Audit: run `grep -nE '# (noqa|type: ignore|nosec|pylint: disable)' MistHelper.py`; every remaining match belongs to this PR. Categorize per rule (PLC0415, E402, mypy-misc, name-defined, var-annotated, PLW0602) and compare against `research.md` baseline.
- [ ] T-08.2 [US8] Branch: run `git switch main && git pull && git switch -c misthelper-long-tail-902`.
- [ ] T-08.3 [US8] Implement in `MistHelper.py`: (a) for 2 `PLC0415` late-import sites, hoist to the module-level import block if safe (no circular-import risk, no lazy-load requirement); if unsafe, escalate — do NOT suppress. (b) For 7 `E402` sites, remove the exemption where the version-check preamble can move (or where the pattern can be restructured); if the version-check preamble MUST remain before imports, restructure `pyproject.toml`'s per-file-ignore only (FR-010 allows per-file-ignore removals, not additions — if the constraint is truly unresolvable, halt and update `plan.md`). (c) For each residual `mypy-misc`, `name-defined`, `var-annotated`, and `PLW0602` site, fix per site (declare missing names, add explicit annotations, resolve global-not-assigned by proper initialization). Delete every remaining `# noqa`, `# type: ignore`, `# nosec`, and `# pylint: disable` comment in `MistHelper.py`.
- [ ] T-08.4 [US8] Verify locally: run `rtk black --check .`, `rtk ruff check .`, `rtk pytest`, `mypy MistHelper.py --strict`, `pylint --fail-under=9.5 MistHelper.py`, `bandit -r MistHelper.py`, then run the final zero-suppression grep: `grep -nE '# (noqa|type: ignore|nosec|pylint: disable)' MistHelper.py` — MUST return zero output. Diff `dir(MistHelper)` against `contracts/public_api.md`.
- [ ] T-08.5 [US8] Commit + push + open PR with `Closes #902` via `gh pr create --base main --head misthelper-long-tail-902`; include final audit delta per FR-015 and explicit confirmation that the zero-suppression grep returns nothing.
- [ ] T-08.6 [US8] Wait for CI + `mergeStateStatus=CLEAN`.
- [ ] T-08.7 [US8] Arm auto-merge: `GITHUB_TOKEN= gh pr merge <N> --auto --squash --delete-branch`.
- [ ] T-08.8 [US8] Confirm merged, #902 closed, branch deleted.

**Checkpoint**: MistHelper.py has zero suppressions of any family.

---

## T-09: Final workflow verification (post-PR-8)

**Purpose**: Confirm all 8 issues are closed, the zero-suppression state holds, and workflow-level success criteria SC-001 through SC-008 are all satisfied.

- [ ] T-09.1 Run the definitive zero-suppression grep against `MistHelper.py`:
  ```bash
  grep -nE '# (noqa|type: ignore|nosec|pylint: disable)' MistHelper.py
  ```
  Expect zero output. If any match appears, halt and open a follow-up issue — do not close the workflow.
- [ ] T-09.2 Confirm all 8 issues (#895, #896, #897, #898, #899, #900, #901, #902) are closed by running `gh issue view <NNN> --json state` for each and verifying `state=CLOSED`.
- [ ] T-09.3 Confirm public API surface is byte-identical to workflow start: diff `python -c "import MistHelper; print('\n'.join(sorted(dir(MistHelper))))"` against `specs/1016-misthelper-suppression-cleanup/contracts/public_api.md`; the diff MUST be empty (SC-007).
- [ ] T-09.4 Confirm project coverage ≥ 90% on the merge commit of PR-8 (SC-005) and pylint ≥ 9.5 (SC-006).
- [ ] T-09.5 Refresh the audit via `tools/refactor_analyzer/` and commit the final report to the feature branch; note the total suppression-count delta versus the 2026-07-13 baseline (should be exactly the sum of the per-PR deltas reported in T-01.6 through T-08.5).
- [ ] T-09.6 Close the feature branch `1016-misthelper-suppression-cleanup` (retain locally as historical reference; no PR merges into it).

**Checkpoint**: Workflow complete. `MistHelper.py` contains zero suppression comments. All 8 issues closed.

---

## Dependencies & Execution Order

### PR-to-PR Dependencies (strict)

All 8 PRs are strictly sequential per FR-003 and SC-008. PR N+1 does NOT open until PR N is merged, its branch deleted, and its target issue closed. No two workflow PRs may be open simultaneously.

```
PR-1 (#895) → PR-2 (#899) → PR-3 (#901) → PR-4 (#898) → PR-5 (#897) → PR-6 (#896) → PR-7 (#900) → PR-8 (#902) → T-09
```

Rationale (from `plan.md` § Merge ordering):

- PR-1 first: removes ~124 import suppressions, cleaning lint signal for all subsequent PRs.
- PR-2 → PR-3 → PR-4: typing/complexity braid — assignment fixes create typed globals PR-4's Protocol integration relies on; PR-3's helper extraction stabilizes the code shape PR-4 must annotate.
- PR-5: small `type-arg` cluster piggybacks on stable Protocols.
- PR-6: `E501` after all typing/complexity PRs so no earlier PR reflows lines PR-6 wraps.
- PR-7: bandit after subprocess-adjacent complexity is settled.
- PR-8: long-tail sweep last — residual set is well-defined only after all earlier clusters land.

### Within-PR Dependencies

Each PR's sub-tasks are strictly sequential (audit → branch → implement → verify → commit → push → PR → CI wait → merge → confirm). The only in-PR parallelism appears in PR-7, where T-07.3 (`subprocess_runner` helper creation) and T-07.4 (its tests) can be authored together with the retype work — both marked `[P]` because they touch different files (`src/utils/subprocess_runner.py`, `tests/`) versus `MistHelper.py`.

### Parallel Opportunities

Between PRs: none (strict serial dispatch).

Within PRs:

- PR-7: T-07.3 and T-07.4 are `[P]` — helper module and its tests land in different files.
- All other PRs: single-file focus on `MistHelper.py`; no in-PR parallelism.

---

## Implementation Strategy

### MVP Scope

The MVP is PR-1 (#895) alone. Landing it drops ~124 suppressions and unblocks accurate lint signal for the remaining 7 PRs. If the workflow must pause at any point, pausing after PR-1 leaves the codebase strictly better than baseline.

### Incremental Delivery

Each PR delivers an independently valuable and revertable increment:

1. PR-1 (#895): bootstrap `__all__` — ~124 suppressions gone; import signal trustworthy.
2. PR-2 (#899): typing grab-bag — mypy signal trustworthy for downstream PRs.
3. PR-3 (#901): complexity extraction — three monolithic symbols become testable.
4. PR-4 (#898): Protocol classes — facade globals typed end-to-end.
5. PR-5 (#897): concrete generics — small isolated win.
6. PR-6 (#896): line-length hand-wrap — file conforms to E501 gate.
7. PR-7 (#900): bandit audit — subprocess calls validated or routed through helper.
8. PR-8 (#902): long-tail sweep — final zero-suppression state achieved.

### Serial Execution Discipline

Only one workflow PR open at a time (SC-008). After each merge:

1. Wait for GitHub to auto-close the target issue.
2. Confirm the delivery branch is deleted on remote.
3. Refresh the audit via `tools/refactor_analyzer/`.
4. Commit the refreshed audit to the feature branch.
5. Open the next PR's branch from the fresh `main`.

---

## Notes

- `[P]` tasks = different files, no dependencies. Rare in this workflow — most sub-tasks are strictly sequential because they all edit `MistHelper.py`.
- `[Story]` label maps each task to its user story / PR (US1 → PR-1, ..., US8 → PR-8).
- Every delivery PR branches from current `main` at PR-open time (FR-004) — never from `1016-misthelper-suppression-cleanup`.
- No `--admin` bypass anywhere (FR-006). Wait for `mergeStateStatus=CLEAN`. SKIPPED conditional checks are not blocking; failing required checks are.
- Pre-push gate: `rtk black --check .` and `rtk ruff check .` MUST be clean before every push. Never rely on CI to catch format/lint issues.
- No new `# noqa`, `# type: ignore`, `# nosec`, or `# pylint: disable` may be introduced anywhere in the repository (FR-008). Reviewers grep the diff.
- `pyproject.toml` edits limited to per-file-ignore removals (FR-010).
- Public API surface of `MistHelper.py` is frozen (FR-007); verify with `dir(MistHelper)` diff against `contracts/public_api.md` on every PR.
- Coverage ≥ 90% and pylint ≥ 9.5 hold on every merged commit (FR-016).
- Refresh audit between PRs; PR body must include pre/post grep counts per FR-015.
