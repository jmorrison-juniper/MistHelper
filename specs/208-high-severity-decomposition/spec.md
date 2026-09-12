# Feature Spec: Phase High — MistHelper.py High-Severity STRUCT Decomposition

- **Issue**: #470 (umbrella #433)
- **Branch**: `refactor/470-high-severity-decomposition` (per-wave: `refactor/470-high-waveN`)
- **Severity tier**: High (highest priority — worked first this pass)
- **Source**: `data/compliance_report.md` SpecKit Remediation Plan, Phase: High

## Problem / Goal

`MistHelper.py` carries **50 High-severity structural violations** against the project
5-Item Rule (fresh baseline 2026-06-27; was 94 — prior waves landed):

- `STRUCT-COMPLEXITY` — 28 functions at cyclomatic complexity **11–17** (target <= 5)
- `STRUCT-LENGTH` — 22 functions far over 60 lines (up to 198)
- `STRUCT-PARAMS` — **0** (closed out by #431 dataclass-param extraction)

Top hotspots: `synthetic_tests`, `select_client_mac`, `build_create_table_sql`,
`_run_interactive_mode` (CC 17), `msp`, `anomaly_events` (CC 16). Goal: reduce every
High-severity STRUCT violation in `MistHelper.py` to **zero** through genuine decomposition
— extracting cohesive logic into well-named helper methods on the owning class — with
**no behavior change**.

Non-goals: Medium/Low violations (separate phases #469/#468), `src/` files, feature changes.

## Interfaces & Behavior

Pure internal refactor. CLI flags, `.env` vars, menu numbers, output formats, and public
method behavior are unchanged. The 9 `STRUCT-PARAMS` functions will change their internal
signatures (grouping params into a dataclass/config object); all call sites are updated in
the same change so observable behavior is identical.

## Constraints

- **5-Item Rule**: each new helper <= 5 params, <= 5 logical blocks, <= 25 lines, CC <= 5.
- **No wrappers/delegates/aliases** (Constitution II): helpers do real work, not pass-through.
  (A pure pass-through helper trips ARCH-DELEGATE — the analyzer catches it.)
- Full-word names (no abbreviations).
- **Inline comments on every executable line** (Constitution VI, NON-NEGOTIABLE).
- **Action logging before/after every meaningful action** (Constitution VII, NON-NEGOTIABLE).
- No `# noqa` / `# type: ignore` shortcuts (Constitution: fix-over-suppress).
- **Boolean-operator caution**: each `and`/`or`/comprehension-`if` adds +1 CC. Extracting
  into a helper whose body is boolean-heavy can itself land at CC6 — prefer dict-dispatch,
  guard clauses, and single-loop extraction.

## Test Plan

- `python tools/check_compliance.py MistHelper.py` — High-severity count strictly decreasing
  per wave; new helpers must not introduce any new High/Medium/Low violation.
- `python -m py_compile MistHelper.py`, `ruff check`, `black --check` — clean each wave.
- `mypy MistHelper.py` — no NEW errors vs. baseline.
- Behavior parity harness per wave (assert refactored == reference for representative inputs).
- `python MistHelper.py --test` — periodic full-run check (0 failed operations).

## Acceptance Criteria

- [ ] Analyzer reports **0 STRUCT-COMPLEXITY** at CC >= 11 (High band) for `MistHelper.py`.
- [ ] Analyzer reports **0 High-severity STRUCT-LENGTH** for `MistHelper.py`.
- [ ] Analyzer reports **0 STRUCT-PARAMS** for `MistHelper.py` (absorbs #431).
- [ ] ARCH-DELEGATE / ARCH-NAMING / ARCH-* remain at 0 (no new wrappers).
- [ ] `ruff`, `black`, `py_compile` clean; no new mypy errors.
- [ ] `--test` green (0 failed ops); behavior unchanged.

## Implementation Notes (AI hints)

Worked in **reviewable waves** (one PR per wave; MistHelper.py is a hot file — serialize).
Sequencing to manage risk:
1. **Self-contained complexity** first (pure CC/LENGTH, no signature change) — safest wins.
2. **PARAMS** functions in dedicated waves (dataclass/config object + update all call sites;
   the `emit_progress_*`/`emit_test_summary` group likely shares a progress-event shape).
3. **High-CC hotspots** (CC 18–20) last — they decompose into several helpers each.

The analyzer is the source of truth for "remaining High" — re-run after each wave. Note
that some High functions also carry Medium LENGTH; decomposing once may clear both tiers.
