# Feature Spec: Phase Low — MistHelper.py Low-Severity STRUCT Decomposition

- **Issue**: #468 (umbrella #433)
- **Branch**: `refactor/468-low-severity-decomposition`
- **Severity tier**: Low (lowest priority — worked first per the remediation plan)
- **Source**: `data/compliance_report.md` SpecKit Remediation Plan, Phase: Low

## Problem / Goal

`MistHelper.py` carries **184 Low-severity structural violations** against the project
5-Item Rule:

- `STRUCT-COMPLEXITY` — 116 functions at cyclomatic complexity **6–9** (target <= 5)
- `STRUCT-BLOCKS` — 68 functions with **6–11 logical blocks** (limit 5)

These are the least-severe tier (no Critical, High/Medium tracked in #470/#469). Goal:
reduce every Low-severity STRUCT violation in `MistHelper.py` to **zero** through genuine
decomposition — extracting cohesive logic into well-named helper methods on the owning
class — with **no behavior change**.

Non-goals: High/Medium violations (separate phases), `src/` files (#457), feature changes.

## Interfaces & Behavior

Pure internal refactor. No CLI flags, `.env` vars, menu numbers, output formats, or public
method signatures change. Every menu operation behaves identically before and after.

## Constraints

- **5-Item Rule**: each new helper <= 5 params, <= 5 logical blocks, <= 25 lines, CC <= 5.
- **No wrappers/delegates/aliases** (Constitution II): helpers do real work, not pass-through.
- Full-word names (no abbreviations).
- **Inline comments on every executable line** (Constitution VI, NON-NEGOTIABLE).
- **Action logging before/after every meaningful action** (Constitution VII, NON-NEGOTIABLE) —
  preserve existing logging when relocating code; add where the touched block lacks it.
- No `# noqa` / `# type: ignore` shortcuts (Constitution: fix-over-suppress).

## Test Plan

- `python tools/check_compliance.py MistHelper.py` — Low-severity count strictly decreasing
  per wave, target 0.
- `python -m py_compile MistHelper.py`, `ruff check`, `black --check` — clean each wave.
- `mypy MistHelper.py` — no NEW errors vs. baseline.
- `python MistHelper.py --test` — 0 failed operations (behavior unchanged).
- Existing unit tests for touched code paths stay green.

## Acceptance Criteria

- [ ] Analyzer reports **0 STRUCT-COMPLEXITY** in the 6–9 (Low) band for `MistHelper.py`.
- [ ] Analyzer reports **0 STRUCT-BLOCKS** for `MistHelper.py`.
- [ ] ARCH-DELEGATE / ARCH-NAMING / ARCH-* remain at 0 (no new wrappers).
- [ ] `ruff`, `black`, `py_compile` clean; no new mypy errors.
- [ ] `--test` green (0 failed ops); behavior unchanged.

## Implementation Notes (AI hints)

Worked in **reviewable waves** (one PR per wave; MistHelper.py is a hot file — serialize).
The analyzer is the source of truth for "remaining Low" — re-run after each wave. Many Low
functions also carry High/Medium violations (length); decomposing once may clear multiple
tiers, which is acceptable and beneficial.
