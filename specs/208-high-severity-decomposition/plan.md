# Implementation Plan: Phase High — High-Severity STRUCT Decomposition

- **Spec**: `spec.md` | **Issue**: #470 | **Branch**: `refactor/470-high-waveN`

## Technical Context

- **Language**: Python 3.13+ | **File**: `MistHelper.py` (~23.5K lines, hot file)
- **Analyzer**: `tools/check_compliance.py` (5-Item Rule grader) — source of truth
- **Gates**: py_compile, ruff, black, mypy (no new errors), `--test` (0 failed ops)
- **Scope**: 84 High violations / 57 functions (41 COMPLEXITY, 34 LENGTH, 9 PARAMS)

## Constitution Check

| Principle | Compliance |
| - | - |
| I. Five-Item Rule | Goal of this work; every helper <= 5 params/blocks/25 lines/CC5 |
| II. Class-Based (No Wrappers) | Helpers do real work on the owning class; no delegates |
| III. Safety-First | `safe_input()` preserved; no input paths altered |
| IV. Deployment Pipeline | Each wave: gates -> commit -> push -> PR -> CI -> auto-merge |
| V. Observability | ASCII-only; existing logging preserved/relocated |
| VI. Inline Comments | Every touched line commented (why) |
| VII. Action Logging | info before / debug after on touched blocks |

No deviations. Pure structural refactor.

## Approach by violation kind

1. **STRUCT-COMPLEXITY (CC 11-20)** — extract decision sub-trees into predicate/handler
   helpers; replace if/elif chains with dict dispatch; collapse boolean accumulation with
   `any()`/`all()`/`sum(map(bool, ...))`; hoist nested loops into helpers.
2. **STRUCT-LENGTH (40-77 lines)** — extract each cohesive section into a single-responsibility
   helper, leaving a short orchestrator.
3. **STRUCT-PARAMS (6-8 params)** — group cohesive params into a frozen dataclass / config
   object; update every call site in the same change. Verify call-site behavior is identical.

**Gotcha** (carried from Low phase): an extracted helper whose body is boolean-heavy
(comprehension-`if`, chained `and`/`or`) often lands at CC6 — split the predicate out or use
dict-dispatch. Always re-run the analyzer BEFORE commit; it catches interim ARCH-DELEGATE
pass-throughs and CC/LENGTH overflow in new helpers.

## Wave Sequencing (risk-managed)

- **Waves H1-H4 (self-contained complexity/length)**: functions with no signature change and
  no/few call sites — exporters, parsers, report builders, time-series extractors. Safest.
- **Waves H5-H6 (PARAMS via dataclass)**: the `emit_progress_*` + `emit_test_summary` group
  (shared progress-event shape), then `_enrich_device_context`, `_listen_for_output`,
  `_systematic_test_run_option`, `write_with_format_selection`, `__init__`. Absorbs #431.
- **Waves H7+ (CC 18-20 hotspots)**: `import_module_safely`, `insight_metrics`,
  `gateway_device_configs`, `detect_msp_privileges`, `devices_with_site_info` — each splits
  into several helpers; one hotspot (or a small pair) per PR.

Re-run the analyzer after every wave; High count must strictly decrease. Phase done when
High = 0.

## Risk & Mitigation

- **Signature changes (PARAMS)**: update all call sites atomically; behavior-parity harness +
  `--test` run before merge.
- **Behavior drift**: parity assertions per wave + unchanged public behavior.
- **OneDrive git locks**: retry / `git reset --hard origin/main` after merge.
- **Hot-file contention**: only one open PR touches MistHelper.py at a time.
