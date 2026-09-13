# Tasks: CONV-LOG-FSTRING Sweep (Issue #429)

**Input**: Design documents from `specs/429-conv-log-fstring-sweep/`
**Prerequisites**: `spec.md`, `plan.md`, `tranche-map.md`, `baseline-fixture-sample.md`, `checklists/requirements.md` (green)
**Branch**: `refactor/429-conv-log-fstring-sweep` (worktree: `MistHelper-429-fstring`)
**Baseline (fresh)**: **695 violations** = 681 G004 + 6 G003 + 8 G201 (spec.md numbers are stale — use 695)

## How to use this file

Execute phases sequentially. Within a phase, tasks marked `[P]` are independent and may be done in parallel. Each task lists:

- **File path(s)** it touches
- **Depends on** — task IDs that MUST be complete first
- **Done when** — concrete, observable assertion

Commit only at the explicit commit tasks (T008, T020, T032, T044, T056, T064). Do **not** combine tranche commits. All quality gates from `plan.md` §Quality Gates per Phase MUST pass before each commit.

## Format

`- [ ] **TXXX** [P?] <Gerund title>`
followed by indented `- File:`, `- Depends on:`, `- Done when:` lines.

---

## Phase 0 — Tooling Setup (1 commit)

**Goal**: libcst installed, codemod scaffold importable, baseline log fixture frozen, tranche map verified against fresh ruff output.

- [ ] **T001** Adding `libcst>=1.5` to pyproject.toml dev extras
  - File: `pyproject.toml` (`[project.optional-dependencies].dev`)
  - Depends on: —
  - Done when: `grep -E '^\s*"libcst' pyproject.toml` returns a line with `>=1.5`.

- [ ] **T002** [P] Adding `libcst>=1.5` to requirements.txt (alphabetical position)
  - File: `requirements.txt`
  - Depends on: —
  - Done when: `grep -E '^libcst' requirements.txt` returns `libcst>=1.5` (or compatible pin); file remains sorted by existing convention.

- [ ] **T003** Installing libcst in worktree venv and smoke-parsing MistHelper.py
  - File: (venv only — no repo change)
  - Depends on: T001, T002
  - Done when: `python -c "import libcst; libcst.parse_module(open('MistHelper.py', encoding='utf-8').read())"` exits 0 with no output.

- [ ] **T004** Scaffolding `tools/codemod_logging_lazy.py` with empty `LoggingLazyCodemod` class + argparse CLI
  - File: `tools/codemod_logging_lazy.py` (NEW)
  - Depends on: T003
  - Done when: `python tools/codemod_logging_lazy.py --help` exits 0 and prints `--dry-run`, `--max-sites`, `--start-line`, `--end-line`, `--skip-lines`, `--report` flags; module docstring documents every flag; file ends with `if __name__ == "__main__":` guard.

- [ ] **T005** [P] Documenting the codemod CLI flags + exit codes in module docstring
  - File: `tools/codemod_logging_lazy.py` (docstring only)
  - Depends on: T004
  - Done when: docstring lists every CLI flag with semantics and the exit-code table (0=success, 1=parse error, 2=unrecognized format spec, 3=audit-flagged line not in `--skip-lines`).

- [ ] **T006** [P] Verifying tranche-map.md line ranges against fresh ruff output
  - File: `specs/429-conv-log-fstring-sweep/tranche-map.md`
  - Depends on: —
  - Done when: `python -m ruff check --select G004 MistHelper.py --output-format=concise | wc -l` returns 681; the 4 tranche ranges in the table cover every reported line with no gaps and no overlaps; document re-confirmed with a "Verified: <date>" footer.

- [ ] **T007** Implementing `tools/capture_log_baseline.py` per `baseline-fixture-sample.md` §Capture mechanism
  - File: `tools/capture_log_baseline.py` (NEW)
  - Depends on: T003
  - Done when: `python tools/capture_log_baseline.py --help` exits 0; script imports each fixture call site's enclosing function, exercises it with deterministic inputs under `caplog`, and writes JSON of shape `[{"site_id": str, "rendered": str}, ...]`.

- [ ] **T008** Generating `tests/fixtures/issue_429_log_baseline.json` (PRE-REFACTOR capture)
  - File: `tests/fixtures/issue_429_log_baseline.json` (NEW)
  - Depends on: T007
  - Done when: file exists; `python -c "import json; print(len(json.load(open('tests/fixtures/issue_429_log_baseline.json'))))"` reports ≥ 30; every `site_id` in the file appears in `baseline-fixture-sample.md`.

- [ ] **T009** Running Phase 0 quality gates locally
  - File: (no edits — verification only)
  - Depends on: T004, T005, T006, T008
  - Done when: all 14 gates in `plan.md` §Quality Gates pass on the current working tree.

- [ ] **T010** Committing Phase 0
  - File: (git operation)
  - Depends on: T009
  - Done when: `git log -1 --format=%s` matches `^version 26\.06\.23\.\d{2}\.\d{2} - chore\(#429\): scaffold libcst codemod \+ freeze log baseline fixture$`; tree clean.

**Checkpoint**: Phase 0 merged or in-place; codemod is importable but does nothing; baseline fixture frozen.

---

## Phase 0.5 — Cross-Cutting Test Harness (parallel with Phase 0)

**Goal**: All four new test modules implemented and passing against the **unmodified** `MistHelper.py`. These tests MUST be green before Phase 1's first conversion commit lands. Tasks here can be developed in parallel with Phase 0.

- [ ] **T011** [P] Implementing `tests/test_issue_429_log_parity.py` (caplog fixture replay)
  - File: `tests/test_issue_429_log_parity.py` (NEW)
  - Depends on: T008
  - Done when: `pytest tests/test_issue_429_log_parity.py -v` passes; test loads the JSON fixture, replays each captured code path under `caplog`, asserts `record.getMessage() == fixture_entry["rendered"]` byte-for-byte; every line has an inline `# why` comment (Principle VI).

- [ ] **T012** [P] Implementing `tests/test_issue_429_log_property.py` (hypothesis format-spec sweep)
  - File: `tests/test_issue_429_log_property.py` (NEW)
  - Depends on: T003
  - Done when: `pytest tests/test_issue_429_log_property.py -v` passes; hypothesis strategies cover int / float / str / None / NaN / multi-byte unicode; for every distinct format-spec template observed in `MistHelper.py` (pre-scan via grep), test asserts `template % args == f"{args!s:spec}"` equivalence.

- [ ] **T013** [P] Implementing `tests/test_issue_429_codemod_idempotent.py`
  - File: `tests/test_issue_429_codemod_idempotent.py` (NEW)
  - Depends on: T004
  - Done when: `pytest tests/test_issue_429_codemod_idempotent.py -v` passes (vacuously on empty codemod); test runs `LoggingLazyCodemod` on `MistHelper.py`, captures output, runs codemod again on that output, asserts second-pass diff is 0 bytes (SC-007).

- [ ] **T014** [P] Implementing `tests/test_issue_429_log_sentinel.py` (lazy-eval proof, AC §1.2)
  - File: `tests/test_issue_429_log_sentinel.py` (NEW)
  - Depends on: T003
  - Done when: `pytest tests/test_issue_429_log_sentinel.py -v` passes; test installs an object whose `__str__` raises `AssertionError`, sets a logger to WARNING level, calls `logger.debug("template %s", sentinel)`, asserts no exception raised; same call with `logger.warning(...)` MUST raise (control case).

- [ ] **T015** Confirming all four test modules green before any conversion commit
  - File: (verification only)
  - Depends on: T011, T012, T013, T014
  - Done when: `pytest tests/test_issue_429_log_parity.py tests/test_issue_429_log_property.py tests/test_issue_429_codemod_idempotent.py tests/test_issue_429_log_sentinel.py -v` exits 0.

---

## Phase 1 — Tranche 1 (lines 315–6970, ~171 G004 + L6120 G003)

**Goal**: First conversion tranche lands; codemod transformers implemented and proven on the smallest line range; CONV-LOG-FSTRING count drops from 681 → ~510.

- [ ] **T016** Implementing `FStringToLazyTransformer` (G004) in codemod
  - File: `tools/codemod_logging_lazy.py`
  - Depends on: T010, T015
  - Done when: class transforms `logger.info(f"x={x}")` → `logger.info("x=%s", x)`; preserves inline comments; emits exit code 2 on unrecognized format spec; `pytest tests/test_issue_429_codemod_idempotent.py` still green.

- [ ] **T017** Implementing `ConcatToLazyTransformer` (G003) in codemod
  - File: `tools/codemod_logging_lazy.py`
  - Depends on: T016
  - Done when: class transforms `logger.info("a=" + str(a))` → `logger.info("a=%s", a)`; covers `+` chains of arbitrary length; unit-tested via a small inline example in `tests/test_issue_429_codemod_idempotent.py` or a sibling test.

- [ ] **T018** Implementing `ExcInfoToExceptionTransformer` (G201) in codemod
  - File: `tools/codemod_logging_lazy.py`
  - Depends on: T017
  - Done when: class rewrites `logger.error("x", exc_info=True)` (inside `except:` block) → `logger.exception("x")`; refuses to transform outside `except:` block and logs a warning.

- [ ] **T019** [P] Running security-audit grep for tranche 1 (lines 315–6970)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T010
  - Done when: every line in 315–6970 matching `(?i)(token|password|secret|cred|key)` appears as a row in the checklist with line number, snippet, and empty `Reviewer / Disposition` columns; `grep -c '^|' checklists/security-audit.md` reflects added rows.

- [ ] **T020** Obtaining human signoff on tranche 1 security-audit rows (GATE)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T019
  - Done when: every tranche-1 row has reviewer initials AND a disposition of `OK` or `SKIP` (skipped lines added to `--skip-lines`). **No T021 work begins until this is checked off.**

- [ ] **T021** Executing codemod on tranche 1 line range
  - File: `MistHelper.py`
  - Depends on: T018, T020
  - Done when: `python tools/codemod_logging_lazy.py --start-line 315 --end-line 6970 --skip-lines <audit-skips> MistHelper.py` exits 0; codemod report logs ~171 G004 + 1 G003 + 0 G201 conversions.

- [ ] **T022** Formatting after tranche 1
  - File: `MistHelper.py`
  - Depends on: T021
  - Done when: `python -m black MistHelper.py && python -m ruff format MistHelper.py` both exit 0 with no further changes on a re-run.

- [ ] **T023** Running full quality-gate suite for tranche 1
  - File: (verification only)
  - Depends on: T022
  - Done when: all 14 gates in `plan.md` §Quality Gates pass; `python -m ruff check --select G003,G004,G201 MistHelper.py --statistics` shows G004 count ≈ 510 (down from 681).

- [ ] **T024** Manually reviewing `git diff MistHelper.py` for tranche 1
  - File: (review only)
  - Depends on: T023
  - Done when: human walks the diff and confirms (a) inline comments preserved on every refactored line, (b) no multi-line argument wrap broken, (c) no behavior-changing edit outside G003/G004/G201 sites.

- [ ] **T025** Running parity test against fixture entries in tranche 1 range
  - File: (verification only)
  - Depends on: T024
  - Done when: `pytest tests/test_issue_429_log_parity.py -v -k "site_id in tranche1_range"` exits 0 for every fixture entry whose source line falls within 315–6970.

- [ ] **T026** Committing tranche 1
  - File: (git operation)
  - Depends on: T025
  - Done when: `git log -1 --format=%s` matches `^version 26\.06\.\d{2}\.\d{2}\.\d{2} - refactor\(#429\): convert logging f-strings tranche 1/4 \(lines 315-6970, ~171 sites\)$`; tree clean.

---

## Phase 2 — Tranche 2 (lines 6988–10282, ~171 G004 + L8316 G003 + L8684/L9286 G201)

**Goal**: Second tranche lands; transformers reused unchanged; CONV-LOG-FSTRING count drops ~510 → ~339.

- [ ] **T027** Running security-audit grep for tranche 2 (lines 6988–10282)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T026
  - Done when: tranche-2 rows added per same format as T019.

- [ ] **T028** Obtaining human signoff on tranche 2 security-audit rows (GATE)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T027
  - Done when: every tranche-2 row has reviewer initials + disposition.

- [ ] **T029** Executing codemod on tranche 2 line range
  - File: `MistHelper.py`
  - Depends on: T028
  - Done when: `python tools/codemod_logging_lazy.py --start-line 6988 --end-line 10282 --skip-lines <audit-skips> MistHelper.py` exits 0; report shows ~171 G004 + 1 G003 + 2 G201 conversions.

- [ ] **T030** Formatting after tranche 2
  - File: `MistHelper.py`
  - Depends on: T029
  - Done when: black + ruff format exit 0.

- [ ] **T031** Running full quality-gate suite for tranche 2
  - File: (verification only)
  - Depends on: T030
  - Done when: 14 gates pass; G004 count ≈ 339.

- [ ] **T032** Manually reviewing `git diff` + running parity test for tranche 2 range
  - File: (review + verification)
  - Depends on: T031
  - Done when: diff approved; `pytest tests/test_issue_429_log_parity.py -k tranche2_range` exits 0.

- [ ] **T033** Committing tranche 2
  - File: (git operation)
  - Depends on: T032
  - Done when: commit subject matches `^version 26\.06\..* - refactor\(#429\): convert logging f-strings tranche 2/4 \(lines 6988-10282, ~171 sites\)$`.

---

## Phase 3 — Tranche 3 (lines 10298–15076, ~171 G004 + L10898/L10991/L13421 G003 + L12303 G201)

**Goal**: Third tranche lands; CONV-LOG-FSTRING count drops ~339 → ~168.

- [ ] **T034** Running security-audit grep for tranche 3 (lines 10298–15076)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T033
  - Done when: tranche-3 rows added.

- [ ] **T035** Obtaining human signoff on tranche 3 security-audit rows (GATE)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T034
  - Done when: every tranche-3 row has reviewer initials + disposition.

- [ ] **T036** Executing codemod on tranche 3 line range
  - File: `MistHelper.py`
  - Depends on: T035
  - Done when: `python tools/codemod_logging_lazy.py --start-line 10298 --end-line 15076 --skip-lines <audit-skips> MistHelper.py` exits 0; report shows ~171 G004 + 3 G003 + 1 G201.

- [ ] **T037** Formatting after tranche 3
  - File: `MistHelper.py`
  - Depends on: T036
  - Done when: black + ruff format exit 0.

- [ ] **T038** Running full quality-gate suite for tranche 3
  - File: (verification only)
  - Depends on: T037
  - Done when: 14 gates pass; G004 count ≈ 168.

- [ ] **T039** Manually reviewing `git diff` + running parity test for tranche 3 range
  - File: (review + verification)
  - Depends on: T038
  - Done when: diff approved; parity test green for tranche-3 fixture sites.

- [ ] **T040** Committing tranche 3
  - File: (git operation)
  - Depends on: T039
  - Done when: commit subject matches `^version 26\.06\..* - refactor\(#429\): convert logging f-strings tranche 3/4 \(lines 10298-15076, ~171 sites\)$`.

---

## Phase 4 — Tranche 4 (lines 15088–23933, ~168 G004 + remaining G201 sites)

**Goal**: Final conversion tranche; CONV-LOG-FSTRING count drops ~168 → **0**.

- [ ] **T041** Running security-audit grep for tranche 4 (lines 15088–23933)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T040
  - Done when: tranche-4 rows added; checklist now covers entire file.

- [ ] **T042** Obtaining human signoff on tranche 4 security-audit rows (GATE)
  - File: `specs/429-conv-log-fstring-sweep/checklists/security-audit.md`
  - Depends on: T041
  - Done when: every tranche-4 row has reviewer initials + disposition; the checklist is fully signed off end-to-end.

- [ ] **T043** Executing codemod on tranche 4 line range
  - File: `MistHelper.py`
  - Depends on: T042
  - Done when: `python tools/codemod_logging_lazy.py --start-line 15088 --end-line 23933 --skip-lines <audit-skips> MistHelper.py` exits 0; report shows ~168 G004 + remaining G201 conversions.

- [ ] **T044** Formatting after tranche 4
  - File: `MistHelper.py`
  - Depends on: T043
  - Done when: black + ruff format exit 0.

- [ ] **T045** Running full quality-gate suite for tranche 4
  - File: (verification only)
  - Depends on: T044
  - Done when: 14 gates pass; **`python -m ruff check --select G003,G004,G201 MistHelper.py` exits 0 with zero violations**.

- [ ] **T046** Manually reviewing `git diff` + running FULL parity test for tranche 4
  - File: (review + verification)
  - Depends on: T045
  - Done when: diff approved; `pytest tests/test_issue_429_log_parity.py -v` (no filter) exits 0 for every fixture entry.

- [ ] **T047** Committing tranche 4
  - File: (git operation)
  - Depends on: T046
  - Done when: commit subject matches `^version 26\.06\..* - refactor\(#429\): convert logging f-strings tranche 4/4 \(lines 15088-23933, ~168 sites\)$`.

**Checkpoint**: All 695 violations converted. `ruff --select G003,G004,G201 MistHelper.py` is silent. Safe to enable rule family.

---

## Phase 5 — Ruff Config Lock-In (1 commit, MUST be LAST)

**Goal**: Make any future G-rule reintroduction fail CI.

- [ ] **T048** Adding `"G"` to `[tool.ruff.lint] select` in pyproject.toml
  - File: `pyproject.toml`
  - Depends on: T047
  - Done when: `grep -E '^select' pyproject.toml` (under `[tool.ruff.lint]`) contains `"G"`; existing letters preserved.

- [ ] **T049** Running full ruff sweep on entire repo
  - File: (verification only)
  - Depends on: T048
  - Done when: `python -m ruff check .` exits 0 (no G-rule violations elsewhere in repo; if any surface, hand-fix them in this same commit).

- [ ] **T050** Running all 4 new tests + full existing pytest suite
  - File: (verification only)
  - Depends on: T049
  - Done when: `pytest` (no filter) exits 0 with coverage ≥ 70%.

- [ ] **T051** Adding CHANGELOG entry for Phase 5
  - File: `CHANGELOG.md`
  - Depends on: T050
  - Done when: top of CHANGELOG.md has a new entry headed by `## version 26.06.<DD>.<HH>.<MM> - chore(#429)` listing G-rule enablement and the 695-site sweep.

- [ ] **T052** Committing Phase 5 (ruff config lock-in)
  - File: (git operation)
  - Depends on: T051
  - Done when: `git log -1 --format=%s` matches `^version 26\.06\..* - chore\(#429\): enable ruff G rule family \(lock in lazy logging\)$`.

- [ ] **T053** Pushing branch and opening PR
  - File: (git/gh operation)
  - Depends on: T052
  - Done when: `gh pr view --json url -q .url` returns a URL; PR title references `#429`; PR body links to spec.md and lists the 5 tranche commits.

- [ ] **T054** Watching CI (CodeQL ~2–3 min)
  - File: (CI observation)
  - Depends on: T053
  - Done when: `gh pr checks <pr> --watch` exits 0; every required check green.

- [ ] **T055** Adding `auto-merge` label
  - File: (gh operation)
  - Depends on: T054
  - Done when: `gh pr view <pr> --json labels -q '.labels[].name'` includes `auto-merge`.

---

## Dependency Graph

```text
Phase 0:              T001 ──┐
                      T002 ──┤
                             ├─> T003 ─> T004 ─> T005
                             │              │
                             │              └─> T013 (idempotency test, Phase 0.5)
                             │
                      T006 (parallel, no deps)
                      T007 ─> T008
                      T004 + T006 + T008 ─> T009 ─> T010 (Phase 0 commit)

Phase 0.5:            T008 ─> T011
                      T003 ─> T012
                      T004 ─> T013
                      T003 ─> T014
                      T011 + T012 + T013 + T014 ─> T015

Phase 1 entry:        T010 + T015 ─> T016 ─> T017 ─> T018
                                     │
                                     T019 (parallel from T010) ─> T020 (GATE)
                                     T018 + T020 ─> T021 ─> T022 ─> T023 ─> T024 ─> T025 ─> T026

Phase 2:              T026 ─> T027 ─> T028 (GATE) ─> T029 ─> T030 ─> T031 ─> T032 ─> T033
Phase 3:              T033 ─> T034 ─> T035 (GATE) ─> T036 ─> T037 ─> T038 ─> T039 ─> T040
Phase 4:              T040 ─> T041 ─> T042 (GATE) ─> T043 ─> T044 ─> T045 ─> T046 ─> T047

Phase 5:              T047 ─> T048 ─> T049 ─> T050 ─> T051 ─> T052 ─> T053 ─> T054 ─> T055
```

**Critical-path notes**:

- Phase 0.5 (T011–T015) runs in parallel with Phase 0 tasks T004–T009 once their respective `Depends on` is satisfied.
- Each tranche's security-audit signoff (T020 / T028 / T035 / T042) is a **hard gate** — codemod execution MUST NOT begin without it.
- Transformer implementation (T016–T018) is one-time; tranches 2–4 reuse the codemod unchanged.
- Phase 5 commit is the only commit that may modify `pyproject.toml`'s ruff `select` list.

---

## Estimated Effort

| Phase | Tasks | Rough hours | Notes |
|---|---:|---:|---|
| Phase 0 (tooling) | T001–T010 | 3–4 h | Mostly env setup + scaffold; baseline capture script is the wildcard |
| Phase 0.5 (test harness) | T011–T015 | 5–7 h | Hypothesis property test and parity test are the bulk; sentinel + idempotency tests are < 1 h each |
| Phase 1 (tranche 1 + 3 transformers) | T016–T026 | 4–6 h | First tranche includes transformer authoring; later tranches are mechanical |
| Phase 2 (tranche 2) | T027–T033 | 1.5–2 h | Mechanical sweep + audit + review |
| Phase 3 (tranche 3) | T034–T040 | 1.5–2 h | Same as Phase 2 |
| Phase 4 (tranche 4) | T041–T047 | 2–3 h | Final tranche; full-file parity test on T046 takes longer |
| Phase 5 (lock-in) | T048–T055 | 1–1.5 h | Includes PR open + CI watch |
| **Total** |  | **18–25.5 h** | Spread over 2–4 calendar days |

---

## Parallel-Marker Summary `[P]`

| Task | Reason it's parallel |
|---|---|
| T002 | Independent file from T001 (requirements.txt vs pyproject.toml) |
| T005 | Docstring-only edit; independent from T006 / T007 / T008 |
| T006 | Touches only tranche-map.md; no dependency on codemod scaffold |
| T011, T012, T013, T014 | Four independent test modules; can be authored concurrently |
| T019 | Security-audit grep can run concurrently with transformer implementation (T016–T018) — both feed T020 → T021 |

---

## Unresolved Items (NEEDS DECISION surfaced during task breakdown)

1. **Where does `capture_log_baseline.py` live long-term?** Plan.md says "may live in `tools/` or be deleted after baseline is captured — keep in repo under `tools/capture_log_baseline.py` for re-runs." T007 keeps it under `tools/`. Confirm at PR review whether to retain or delete-post-commit.
2. **`--skip-lines` value for each tranche depends on T020/T028/T035/T042 outcomes** — cannot be hard-coded in tasks.md. Each codemod-execute task (T021/T029/T036/T043) accepts `<audit-skips>` as a placeholder that the operator fills in from the audit checklist disposition column.
3. **Test naming**: plan.md alternates between `test_issue_429_log_property.py` (§ Project Structure line 80) and `test_issue_429_log_parity_hypothesis.py` (user prompt). This tasks.md uses `test_issue_429_log_property.py` (matches plan.md). Confirm before T012 lands.
4. **G003/G201 line-number drift in tranches 3–4**: tranche-map.md flags L13421 as both G003 and G201 (line 20: "L13421 (verify)"). T034/T036 acceptance counts assume the verify resolves to G003-only. If both rules fire on the same line, the tranche-3 expected count shifts +1.
