# Implementation Plan: CONV-LOG-FSTRING Sweep (Issue #429)

**Branch**: `refactor/429-conv-log-fstring-sweep` | **Date**: 2026-06-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/429-conv-log-fstring-sweep/spec.md`
**Issue**: [#429](https://github.com/jmorrison-juniper/MistHelper/issues/429)

## Summary

Convert every f-string-formatted (`G004`), `+`-concat (`G003`), and `error(..., exc_info=True)` (`G201`) logging call in `MistHelper.py` to lazy `%s`-style argument formatting via a libcst-based codemod (`tools/codemod_logging_lazy.py`), delivered in ~4 reviewable tranche commits (~170 sites each), followed by a final config commit that adds `"G"` to `[tool.ruff.lint] select`. The refactor is behavior-preserving: rendered log strings MUST be byte-identical pre/post (verified by a frozen baseline fixture + parity test + hypothesis property test + idempotency test + sentinel laziness test).

## Baseline Drift Notice (READ FIRST)

The spec was authored against a stale snapshot (`data/compliance_report.md` dated 2026-06-23 19:11 UTC pulled from the parent repo) that counted **1,099 G004 + 7 G003 + 36 G201 = 1,142** sites. A fresh `python tools/check_compliance.py MistHelper.py` run inside this worktree on the same date reports:

| Rule | Spec count | Actual (worktree) | Delta |
|---|---|---|---|
| G004 / CONV-LOG-FSTRING | 1,099 | **681** | -418 |
| G003 / logging-string-concat | 7 | **6** | -1 |
| G201 / logging-exc-info | 36 | **8** | -28 |
| **Total G** | **1,142** | **695** | **-447** |

Roughly 40% of the originally-counted sites have already been fixed (likely via incidental cleanup on other PRs since the spec was drafted). All plan artifacts below — tranche map, fixture sample, success criteria — use the **fresh 695-site baseline**. The spec text remains authoritative for *behavior*; the *count numbers* in the spec (SC-001, SC-002) MUST be re-anchored to 695 → 0 in the final tasks-phase exit gate. This drift does not change any acceptance criterion semantically; it only reduces the workload.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution Tech Constraints)
**Primary Dependencies**: libcst (new dev dep — see Phase 0), hypothesis ≥ 6.151.12 (already present), pytest ≥ 7 (present)
**Storage**: N/A — code refactor, no DB schema or data path change
**Testing**: pytest with **`caplog` fixture** (60 existing call sites; **zero** `assertLogs` usage in `tests/` — `caplog` is the project standard); hypothesis for property tests; new tests under `tests/test_issue_429_log_*.py`
**Target Platform**: Windows 11 dev + Linux container (Podman) runtime
**Project Type**: Single-file refactor — `MistHelper.py` (32,640 LOC) only
**Performance Goals**: No runtime budget; codemod runs offline. Expected runtime CPU savings at INFO+ levels unmeasured but non-zero (lazy interpolation skipped when level disabled)
**Constraints**: 5-Item Rule (codemod helper functions ≤ 25 lines, ≤ 5 params); inline comments on every executable line of new code (Principle VI); `logging.info` before / `logging.debug` after every meaningful action in the codemod itself (Principle VII); ASCII-only logs; idempotency (SC-007); each tranche commit MUST pass full CI independently
**Scale/Scope**: 695 logging call sites in one file; codemod ~300 LOC; tests ~400 LOC; 5 commits total (4 tranche + 1 ruff-config)

## Constitution Check

| Principle | Compliance |
|---|---|
| I. Five-Item Rule | PASS — codemod split into ≤ 5 helper classes; each transformer method ≤ 25 lines |
| II. Class-Based Architecture (No Wrappers) | PASS — codemod entry point is a `LoggingLazyCodemod(libcst.codemod.Codemod)` class; CLI wrapper is the only non-class function (argparse glue) and is unavoidable per libcst convention |
| III. Safety-First | PASS — codemod is offline tool; no new runtime input prompts; secret-name audit (`(?i)(token\|password\|secret\|cred\|key)`) enforced per spec §4 with human signoff in `checklists/security-audit.md` |
| IV. Full Deployment Pipeline | PASS — every tranche commit runs the full pipeline (ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright); final commit triggers container build per Principle IV |
| V. Observability & Logging | PASS — the codemod itself uses `%s`-style logging (eat your own dogfood); rendered log output is byte-identical post-refactor (SC-003) |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS — every new line in `tools/codemod_logging_lazy.py` and the four new test modules has a same-line `# why` comment; **the codemod MUST NOT add or remove inline comments on refactored lines** — comment preservation is libcst's main reason for selection over `ast.unparse` |
| VII. Action Logging (NON-NEGOTIABLE) | PASS — codemod CLI logs `info` before each tranche run and `debug` after with site count; test modules log `info` before each parity comparison |

No violations. Complexity Tracking table empty.

## Project Structure

### Documentation (this feature)

```text
specs/429-conv-log-fstring-sweep/
├── spec.md                          # already authored
├── plan.md                          # this file
├── tranche-map.md                   # Phase 0 supplement — exact line ranges per tranche
├── baseline-fixture-sample.md       # Phase 0 supplement — fixture call-site catalog
├── research.md                      # Phase 0 — libcst vs ast.unparse, caplog vs assertLogs decision log
├── data-model.md                    # Phase 1 — LoggingCallSite / Tranche / FixtureEntry entity catalog
├── quickstart.md                    # Phase 1 — per-tranche execution + validation runbook
├── checklists/
│   └── security-audit.md            # per spec §4 — secret-name flagged sites, reviewer initials
├── contracts/
│   └── codemod-cli-contract.md      # Phase 1 — codemod argparse interface + exit codes
└── tasks.md                         # Phase 2 — generated later by /speckit.tasks
```

### Source Code Delta

```text
tools/
└── codemod_logging_lazy.py          # NEW — libcst codemod, CLI entry point

tests/
├── fixtures/
│   └── issue_429_log_baseline.json  # NEW — frozen pre-refactor log output (≥ 30 entries)
├── test_issue_429_log_parity.py     # NEW — caplog parity test against frozen fixture
├── test_issue_429_log_property.py   # NEW — hypothesis property test for format-spec equivalence
├── test_issue_429_codemod_idempotent.py  # NEW — codemod-on-codemod-output yields 0-byte diff
└── test_issue_429_log_sentinel.py   # NEW — sentinel-__str__-raises test proves laziness

pyproject.toml                       # MODIFIED — add libcst to [project.optional-dependencies].dev; FINAL commit also adds "G" to [tool.ruff.lint].select

requirements.txt                     # MODIFIED — add libcst (pinned, dev marker if a marker convention exists in this file)

MistHelper.py                        # MODIFIED — 695 call sites converted across 4 tranche commits
```

**Structure Decision**: Single-project codebase per project constitution; codemod lives in `tools/` alongside the existing `tools/check_compliance.py`. Tests live under `tests/` with the project naming convention `test_issue_<num>_<scope>.py`.

## Module / File Map

| Path | Status | Purpose |
|---|---|---|
| `tools/codemod_logging_lazy.py` | **new** | libcst codemod — `LoggingLazyCodemod` class + `FStringToLazyTransformer` + `ConcatToLazyTransformer` + `ExcInfoToExceptionTransformer` + CLI argparse glue (`--dry-run`, `--max-sites N`, `--start-line N`, `--end-line N`, `--report`) |
| `tools/check_compliance.py` | unchanged | Existing tool reused as CONV-LOG-FSTRING site counter between tranches |
| `tests/test_issue_429_log_parity.py` | **new** | Loads `issue_429_log_baseline.json`, re-runs each captured code path under `caplog`, asserts `record.getMessage()` byte-identical |
| `tests/test_issue_429_log_property.py` | **new** | hypothesis strategies for ints/floats/strs/None/NaN/multi-byte unicode; for each known format-spec template asserts `template % args == original_f_string_eval` |
| `tests/test_issue_429_codemod_idempotent.py` | **new** | Runs `LoggingLazyCodemod` on `MistHelper.py`, captures output, runs codemod again, asserts second pass produces 0-byte diff (SC-007) |
| `tests/test_issue_429_log_sentinel.py` | **new** | Installs object whose `__str__` raises `AssertionError`, sets logger to WARNING, calls `logger.debug(template, sentinel)`, asserts no exception (proves laziness, AC §1.2) |
| `tests/fixtures/issue_429_log_baseline.json` | **new** | Frozen baseline — see `baseline-fixture-sample.md` for ≥ 30 selected sites |
| `pyproject.toml` | **modified** | (a) add `libcst>=1.5` to dev deps in Phase 0; (b) add `"G"` to `[tool.ruff.lint].select` in final commit |
| `requirements.txt` | **modified** | Add `libcst>=1.5` (line ordering: keep alphabetical with existing entries) |
| `MistHelper.py` | **modified** | 695 call sites rewritten across 4 tranche commits |
| `CHANGELOG.md` | **modified** | One entry per tranche commit + final config commit, all with UTC `YY.MM.DD.HH.MM` timestamps (Principle IV) |
| `specs/429-conv-log-fstring-sweep/checklists/security-audit.md` | **new** | One row per call site matching `(?i)(token\|password\|secret\|cred\|key)`; reviewer initials + disposition; signed off before final tranche merges |

## Phased Delivery

### Phase 0 — Tooling Setup (1 commit)

**Entry**: branch created from `main`, baseline drift noted.
**Work**:
1. Add `libcst>=1.5` to `requirements.txt` and `pyproject.toml` `[project.optional-dependencies].dev`.
2. Install in dev environment: `pip install libcst>=1.5`.
3. Scaffold `tools/codemod_logging_lazy.py` with empty `LoggingLazyCodemod` class + CLI argparse. No transforms yet.
4. Run `python tools/check_compliance.py MistHelper.py` and freeze the exact list of 681 CONV-LOG-FSTRING line numbers into `specs/429-conv-log-fstring-sweep/tranche-map.md` (already drafted — confirm at commit time).
5. Generate `tests/fixtures/issue_429_log_baseline.json` from `main` (pre-refactor) for the ≥ 30 fixture sites enumerated in `baseline-fixture-sample.md`. Capture mechanism: a one-off `scripts/capture_log_baseline.py` script that imports the fixture call sites' enclosing functions, exercises them with deterministic inputs under `caplog`, and dumps `{"site_id": ..., "rendered": ...}` to the JSON fixture. Script may live in `tools/` or be deleted after baseline is captured — keep in repo under `tools/capture_log_baseline.py` for re-runs.

**Exit**: `libcst` importable; codemod CLI exits 0 with `--help`; baseline fixture committed; tranche map committed. CI green.
**Commit message**: `version 26.06.23.HH.MM - chore(#429): scaffold libcst codemod + freeze log baseline fixture`

### Phase 1 — Tranche 1 (sites 315–6970, ~171 conversions)

**Entry**: Phase 0 merged or in-place; codemod transforms implemented; idempotency test green.
**Work**:
1. Implement `FStringToLazyTransformer` (G004), `ConcatToLazyTransformer` (G003), `ExcInfoToExceptionTransformer` (G201) in `tools/codemod_logging_lazy.py`.
2. Run security audit grep over the tranche range; populate `checklists/security-audit.md`; await human signoff for any flagged site **before** committing.
3. Execute codemod: `python tools/codemod_logging_lazy.py --start-line 315 --end-line 6970 MistHelper.py`.
4. Run `python -m black MistHelper.py && python -m ruff format MistHelper.py`.
5. Run full local quality gates (see "Quality Gates per Phase" below).
6. Manual review of `git diff` — confirm comment preservation, no behavior change, no broken multi-line wraps.

**Exit**: All CI green on tranche commit in isolation; CONV-LOG-FSTRING count drops by ~171; G003 sites at L6120 / L8316 (if in range) converted; no G201 sites in this range. Parity test passes for fixture entries in this range.
**Commit message**: `version 26.06.23.HH.MM - refactor(#429): convert logging f-strings tranche 1/4 (lines 315-6970, ~171 sites)`

### Phase 2 — Tranche 2 (sites 6988–10282, ~171 conversions)

Same as Phase 1, scoped to `--start-line 6988 --end-line 10282`. Includes G003 site at L8316 and G201 sites at L8684 and L9286.

**Exit / commit**: as above with `tranche 2/4`.

### Phase 3 — Tranche 3 (sites 10298–15076, ~171 conversions)

Same as Phase 1, scoped to `--start-line 10298 --end-line 15076`. Includes G003 sites at L10898, L10991, L13421 and G201 sites at L12303 plus any in 10298–15076 range.

**Exit / commit**: as above with `tranche 3/4`.

### Phase 4 — Tranche 4 (sites 15088–23933, ~168 conversions)

Same as Phase 1, scoped to `--start-line 15088 --end-line 23933`. Final remaining G003 and G201 sites swept up.

**Exit / commit**: as above with `tranche 4/4`. After this commit, `python -m ruff check --select G003,G004,G201 MistHelper.py` MUST exit 0.

### Phase 5 — Ruff Config Lock-In (1 commit, MUST be LAST)

**Entry**: All 4 tranches merged; `ruff check --select G003,G004,G201 MistHelper.py` reports zero.
**Work**:
1. Edit `pyproject.toml` `[tool.ruff.lint] select` from `["E", "F", "W", "I", "UP", "B"]` → `["E", "F", "W", "I", "UP", "B", "G"]`.
2. Run full `python -m ruff check .` — MUST exit 0.
3. Run all five new tests + full existing suite.
4. Add CHANGELOG entry.

**Exit**: Final commit lands. Any future PR reintroducing a G-rule violation fails CI.
**Commit message**: `version 26.06.23.HH.MM - chore(#429): enable ruff G rule family (lock in lazy logging)`

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **Security false-positives** — codemod inlines a variable named `auth_token` into log args, breaking redaction expectations | Medium | High (credential leak) | Mandatory `(?i)(token\|password\|secret\|cred\|key)` grep over each tranche range; manual signoff in `checklists/security-audit.md` per spec §4; codemod CLI takes `--skip-lines L1,L2,...` flag to honor audit decisions |
| 2 | **Codemod bug — format-spec mismatch** — e.g., `f"{x:b}"` (binary) has no direct `%`-spec equivalent and silently corrupts output | Medium | High (rendered-string drift, fails SC-003) | Hypothesis property test covers every format-spec literal observed in `MistHelper.py`; codemod emits FAIL (not silent fallback) on any unrecognized format spec — operator MUST hand-convert or extend the codemod's spec table; pre-flight scan in Phase 0 enumerates all distinct format specs to drive the property test |
| 3 | **CI noise — partial-state failure** — a tranche commit passes ruff but breaks pytest (e.g., a test asserts an exact log message that the refactor accidentally altered) | Medium | Medium | Each tranche commit runs the FULL CI suite locally before push; parity test (fixture-based) catches rendered-string drift in tests that assert log content; CI on the branch protects all 4 tranche commits independently per User Story 3 |
| 4 | **Hot-file conflict** — another agent opens a PR touching `MistHelper.py` mid-sweep | High (per constitution: "MistHelper.py is a hot file") | High (3-way merge in 32K-line file) | Per constitution §Multi-Agent Git Workflow: claim `#429` with `in-progress` label BEFORE Phase 0; run `gh pr list --search "is:open MistHelper.py" --json number,title,files` before EACH tranche commit; if another PR opens, **pause sweep** until the conflicting PR merges, then `git rebase main` and re-run the codemod (idempotent — SC-007 guarantees re-run on already-converted sites is a no-op so only the new sites get converted) |
| 5 | **libcst gaps for Python 3.13 features** — match/case patterns or PEP 695 generics in newly-added code may not parse cleanly | Low (logging calls don't use these) | Medium (codemod crash, not data loss) | Phase 0 includes a smoke-test pass: `LoggingLazyCodemod().transform_module(libcst.parse_module(open("MistHelper.py").read()))` MUST complete without raising; if it does, pin `libcst>=1.5` (which has 3.13 support) and pre-test with `python -c "import libcst; libcst.parse_module(open('MistHelper.py').read())"` |

## Quality Gates per Phase

Each tranche commit (and the final config commit) MUST pass all gates below **locally before push** and **in CI on the branch**:

| Gate | Command | Pass criterion |
|---|---|---|
| Syntax | `python -m py_compile MistHelper.py` | exit 0 (Principle IV) |
| Ruff (existing selection) | `python -m ruff check .` | exit 0 |
| Ruff (G subset, scope check) | `python -m ruff check --select G003,G004,G201 MistHelper.py` | per-phase decreasing count; **0 after Phase 4** |
| Black format | `python -m black --check .` | exit 0 |
| Ruff format | `python -m ruff format --check .` | exit 0 |
| mypy | per project `mypy.ini` / `pyproject.toml` config | exit 0 |
| pytest + coverage | `pytest --cov` | exit 0, coverage ≥ 70% (SC-006) |
| Bandit | `bandit -r MistHelper.py tools/codemod_logging_lazy.py` | no new HIGH/CRITICAL |
| pip-audit | `pip-audit -r requirements.txt` | no new vulnerabilities |
| CodeQL | GitHub Action | green |
| Playwright | GitHub Action | green (regression gate only) |
| Compliance | `python tools/check_compliance.py MistHelper.py` | CONV-LOG-FSTRING count strictly decreasing each tranche; **0 after Phase 4** |
| Idempotency | `pytest tests/test_issue_429_codemod_idempotent.py` | exit 0 (SC-007) |
| Parity | `pytest tests/test_issue_429_log_parity.py` | exit 0 (SC-003) for fixture sites in tranche range |
| Sentinel laziness | `pytest tests/test_issue_429_log_sentinel.py` | exit 0 (AC §1.2) |

## Test Strategy

Per spec §5, four test types plus a sentinel:

| Type | File | Mechanism | Asserts |
|---|---|---|---|
| **Parity** | `tests/test_issue_429_log_parity.py` | `caplog` fixture re-runs fixture sites, compares `record.getMessage()` to JSON baseline | SC-003: byte-identical rendered output |
| **Hypothesis property** | `tests/test_issue_429_log_property.py` | `@given(st.floats(allow_nan=True), st.integers(), st.text())` over every format-spec template observed in `MistHelper.py` | `template % args == original_f_string_expr` over the input space |
| **Idempotency** | `tests/test_issue_429_codemod_idempotent.py` | Run codemod twice on `MistHelper.py`, diff byte ranges | SC-007: second pass is 0-byte diff |
| **Sentinel laziness** | `tests/test_issue_429_log_sentinel.py` | Install object whose `__str__` raises; set logger WARNING; call `.debug(template, sentinel)` | No exception fires (proves lazy formatting) — AC §1.2 |
| **Lint regression** | CI step (no test file) | `ruff check --select G MistHelper.py` | exit 0 — guards SC-001 / SC-008 |

`caplog` chosen over `assertLogs` per research note: project has 60 existing `caplog` usages and **zero** `assertLogs` usages in `tests/`. Switching idioms mid-codebase would violate the implicit project convention.

## Rollback Plan

**Per-tranche rollback** (most likely scenario):
1. Identify failing tranche commit SHA: `git log --oneline refactor/429-conv-log-fstring-sweep`.
2. `git revert <tranche-SHA>` — produces a clean revert commit.
3. Push the revert; CI re-runs. Other tranches (which are independent CI-green commits per User Story 3) remain valid.
4. Re-run codemod with refined transformer over the same line range; new tranche commit replaces the reverted one.

**Full-feature rollback** (if multiple tranches must be reverted):
1. **Revert the ruff-config commit FIRST** — otherwise CI will fail on the partially-rolled-back state because remaining f-string sites will violate the now-enabled `G` rule.
2. Then `git revert` each tranche commit in **reverse chronological order** (tranche 4, 3, 2, 1, then Phase 0 scaffold).
3. Final state: `MistHelper.py` matches `main` pre-sweep; new test files and codemod tool may be retained (no harm) or also reverted.

**Rollback validation**: after each revert, run `python -m ruff check --select G003,G004,G201 MistHelper.py --statistics` and confirm count matches expected (pre-sweep baseline = 695 if everything reverted; partial counts if only some tranches reverted).

## Coordination Notes

**`MistHelper.py` is a hot file** (per constitution §Multi-Agent Git Workflow, item 3). Coordination protocol:

1. **Before Phase 0**: Add `in-progress` label to issue #429. If any other PR already has `in-progress` on a MistHelper.py-touching issue, **wait** for that PR to merge first.
2. **Before EACH tranche commit**: Run
   ```powershell
   gh pr list --state open --json number,title,headRefName,files --jq '.[] | select(.files[].path == "MistHelper.py") | {number, title, headRefName}'
   ```
   If any non-`#429` PR shows up, **pause the sweep**. Options:
   - **Wait** for that PR to merge, then `git rebase main` (codemod is idempotent — re-running on the rebased file just re-converts the newly-added sites that the other PR introduced).
   - **Coordinate manually** with the other PR's author if their PR is also large/long-running.
3. **After each tranche merges**: Open the next tranche's PR immediately — do not batch them, because batching risks one of them growing stale relative to main.
4. **Final config commit**: Open as a separate PR titled `chore(#429): enable ruff G rule family`; this PR is small (one-line change to `pyproject.toml`) and MUST merge after all 4 tranche PRs land.

## Open Questions / NEEDS DECISION

1. **NEEDS DECISION — fixture-capture mechanism delivery**: `tools/capture_log_baseline.py` is described in Phase 0 as a one-off script. Decide before Phase 0 commits: (a) keep the script in `tools/` permanently (re-runnable, but adds maintenance surface), or (b) delete after baseline JSON is committed (lighter, but baseline cannot be regenerated if the underlying call sites are later refactored). **Recommended: keep** — small file, future-proof.
2. **NEEDS DECISION — `requirements.txt` dev-dep marker**: project uses both `requirements.txt` (flat) and `pyproject.toml` `[project.optional-dependencies].dev`. Confirm whether `libcst` should land in both, or only in `pyproject.toml` dev extras (since libcst is dev-time only, not runtime). **Recommended: pyproject.toml dev extras only** — matches `pytest`/`hypothesis` placement.
3. **No remaining unknowns** from the spec's three deferred items — all resolved in `tranche-map.md`, `baseline-fixture-sample.md`, and the `caplog` choice documented in this file's Test Strategy section.

## Phase 0 Artifacts (already drafted in this commit)

- `tranche-map.md` — exact line ranges, expected counts, fresh-baseline derivation
- `baseline-fixture-sample.md` — ≥ 30 named fixture call sites covering every edge-case pattern from spec §Edge Cases
- (research.md / data-model.md / quickstart.md / contracts/ / checklists/security-audit.md will be generated by subsequent `/speckit.plan` or `/speckit.tasks` invocations or created in Phase 0 commits)

## Complexity Tracking

*No Constitution Check violations. Table intentionally empty.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| — | — | — |
