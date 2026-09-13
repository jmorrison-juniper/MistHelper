# Implementation Plan: STE Compliance for src/ Comments and Docstrings

**Branch**: `1030-ste-src-cleanup` | **Date**: 2026-07-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1030-ste-src-cleanup/spec.md`

## Summary

Apply the STE linter to the `src/` tree. Remove genuine STE violations in
comments and docstrings. Do not change code behavior. Split the work into
phases. Phase 1 fixes mechanical rules. Later phases fix judgment rules, grouped
by module cluster, one pull request per phase.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution binding minimum)

**Primary Dependencies**: None new. Uses the existing STE linter in
`tools/ste_linter/` and the dictionary at `data/ste_dictionary.json`.

**Storage**: N/A. This feature edits source comments and docstrings only.

**Testing**: Existing pytest suite under `tests/`. The STE linter itself
provides the pass or fail signal for each rule.

**Target Platform**: Developer workstation and CI (Windows and Linux).

**Project Type**: Single project. Source lives in `src/`.

**Performance Goals**: N/A. This is a documentation cleanup.

**Constraints**:

- Edit comments and docstrings only. No code behavior change.
- `src/` has CI gates that MistHelper.py comments did not: coverage at 80
  percent, mypy on `src/`, and radon at CC 10 or less.
- Keep code examples inside docstrings unchanged, including semicolons.
- Every touched code line keeps its inline comment.

**Scale/Scope**: 359 files, 108,543 lines. In scope: about 4,313 fixes (309
mechanical plus about 4,004 judgment). Out of scope: about 62,877 false
positives on code words and noun clusters.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | No new functions. Comment and docstring edits only. |
| II. Class-Based Architecture | PASS | No code structure change. |
| III. Safety-First | PASS | No input handling change. No destructive path. |
| IV. Full Deployment Pipeline | PASS | Standard PR flow. No container change needed. |
| V. Observability & Logging | PASS | No log strings edited. Linter skips log strings. |
| VI. Inline Comments | PASS | Every touched code line keeps its inline comment. |
| VII. Action Logging | PASS | No action code touched. |

Result: PASS. No violations. No complexity deviations.

## Project Structure

### Documentation (this feature)

```text
specs/1030-ste-src-cleanup/
├── spec.md          # Feature specification
├── plan.md          # This file
├── research.md      # Scan findings and rule decisions
└── tasks.md         # Phased task list
```

No `data-model.md` and no `contracts/`. This feature adds no data model and no
new CLI. The linter CLI already exists on `main`.

### Source Code (repository root)

```text
src/
├── firmware/        # Worst cluster by structural count
├── org/             # org_synthetic_probes_manager.py is the top file
├── maps/
├── site/address_audit/
├── analytics/
├── export/
├── refactors/
└── ... (359 files total)
```

**Structure Decision**: The feature touches files across many `src/`
subpackages. It adds no new files to `src/`. It groups edits by subpackage for
the judgment phases.

## Complexity Tracking

No constitution violations. This table is empty by design.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| None | N/A | N/A |

## Phasing

- **Phase 1 — Mechanical (P1)**: Fix the six mechanical rules across all of
  `src/`. Target zero violations. One pull request. Safe and CI-verifiable.
- **Phase 2 — Semicolons (P2)**: Fix prose semicolons. Verify each file to keep
  code examples in docstrings. Group by module cluster. One pull request per
  cluster or a small set of clusters.
- **Phase 3 — Passive, length, tense (P3)**: Fix judgment rules by module
  cluster. One pull request per cluster.

Each phase links to issue #1687 and closes only when its rules meet the target.
