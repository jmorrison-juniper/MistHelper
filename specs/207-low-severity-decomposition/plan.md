# Implementation Plan: Phase Low — Low-Severity STRUCT Decomposition

- **Spec**: `spec.md` | **Issue**: #468 | **Branch**: `refactor/468-low-severity-decomposition`

## Technical Context

- **Language**: Python 3.13+ | **File**: `MistHelper.py` (~23,499 lines, hot file)
- **Analyzer**: `tools/check_compliance.py` (5-Item Rule grader) — source of truth
- **Gates**: py_compile, ruff, black, mypy (no new errors), `--test` (0 failed ops)

## Constitution Check

| Principle | Compliance |
| - | - |
| I. Five-Item Rule | Goal of this work; every helper <= 5 params/blocks/25 lines/CC5 |
| II. Class-Based (No Wrappers) | Helpers do real work on the owning class; no delegates |
| III. Safety-First | `safe_input()` preserved; no input paths altered |
| IV. Deployment Pipeline | Each wave: gates -> commit -> push -> PR -> CI -> merge |
| V. Observability | ASCII-only; existing logging preserved/relocated |
| VI. Inline Comments | Every touched line commented (why) |
| VII. Action Logging | info before / debug after on touched blocks |

No deviations. Pure structural refactor.

## Approach

Two violation kinds, one technique each:

1. **STRUCT-COMPLEXITY (CC 6–9)** — reduce branching: extract decision sub-trees into
   predicate/handler helpers; replace nested `if` with guard clauses; collapse boolean
   accumulation with `any()`/`all()`/`sum(map(bool, ...))`.
2. **STRUCT-BLOCKS (6–11 blocks)** — extract each cohesive block (a loop, a try/except, a
   distinct setup step) into a single-responsibility helper, leaving the original as a short
   orchestrator (still <= 5 blocks).

**Gotcha** (from prior waves): an extracted helper whose body is a comprehension-with-`if`
often lands at CC6 itself — use `sum(map(bool, ...))` or extract the predicate to stay <= 5.

## Wave Batching

Each wave = a cohesive cluster of functions (same class/region) → one PR. Re-run the analyzer
after every wave; Low count must strictly decrease. Stop the phase when Low = 0.

- **Wave 1**: dependency/bootstrap helpers (`GlobalImportManager` version + requirements parsing).
- **Wave 2+**: session/auth, connection-pool, runtime-init clusters, then the long tail.

The analyzer enumerates remaining Low offenders each run; `tasks.md` seeds the known set.

## Risk & Mitigation

- **Behavior drift**: mitigated by `--test` after each wave + unchanged public signatures.
- **OneDrive git locks**: retry; never `git checkout` with editor holding files.
- **Hot-file contention**: only one open PR touches MistHelper.py at a time.
