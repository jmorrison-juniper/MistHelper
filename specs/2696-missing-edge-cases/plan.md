# Implementation Plan: Missing Edge Case Triage

**Branch**: `chore/2696-missing-edge-cases` | **Date**: 2026-09-16 | **Spec**: `specs\2696-missing-edge-cases\spec.md`

**Input**: Feature specification from `specs\2696-missing-edge-cases\spec.md`

## Summary

Repair the missing edge-case detector so it reports only marked input domains. The old detector treated any positive integer call argument as proof that empty, zero, negative, and `None` inputs all mattered.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Standard library `ast`, `dataclasses`, `logging`, and `pathlib`. No new package dependency.

**Storage**: No storage change. `tools\test_quality_analyzer\baseline.json` remains unchanged.

**Testing**: pytest, Ruff, Black, mypy, radon, `tools.test_quality_analyzer`, and `tools.guard_proof_audit`.

**Target Platform**: Windows development and GitHub Actions runners.

**Project Type**: Python command-line tooling in the MistHelper repository.

**Performance Goals**: Keep analyzer runtime in the same order as the existing scan.

**Constraints**: Do not edit generated Mist API documentation. Do not add broad test sweeps. Keep the change below 20 production or test files.

**Scale/Scope**: The current scan covers 670 analyzed files and about 16,611 collected tests.

## Constitution Check

- Five-Item Rule: The change edits one existing detector module and one existing test module. It does not add a new package child.
- Class-Based Architecture: New behavior stays inside `MissingEdgeCaseDetector` and a semantic `EdgeCaseCoverage` value object.
- Safety-First: The change does not touch operator input, destructive operations, or external API calls.
- Full Deployment Pipeline: Local gates and pull request CI prove the repair.
- Observability: New detector decisions use existing logger calls.

## Project Structure

### Documentation (this feature)

```text
specs\2696-missing-edge-cases\
├── spec.md
├── plan.md
├── tasks.md
└── triage.md

specs\2448-misthelper-performance-monitoring\artifacts\
└── hook-catalog.csv
```

### Source Code (repository root)

```text
tools\test_quality_analyzer\
├── detection\missing_edge_case.py
└── fixtures\
    ├── bad\test_missing_edge_case_bad.py
    └── good\test_missing_edge_case_good.py

tests\tools\test_quality_analyzer\
└── test_meta_fixtures.py

changelog.d\
└── issue-2696-missing-edge-cases.md
```

**Structure Decision**: Edit the existing analyzer and its fixtures. Add no new source package.

## Changed Files

| File | Reason |
| - | - |
| `tools\test_quality_analyzer\detection\missing_edge_case.py` | Require explicit edge-case domains and ignore test support calls. |
| `tools\test_quality_analyzer\fixtures\bad\test_missing_edge_case_bad.py` | Update the fixture contract for numeric-only opt-in behavior. |
| `tools\test_quality_analyzer\fixtures\good\test_missing_edge_case_good.py` | Update the fixture contract for numeric-only opt-in behavior. |
| `tests\tools\test_quality_analyzer\test_meta_fixtures.py` | Add regression tests for support-call false positives and valid collection gaps. |
| `specs\2448-misthelper-performance-monitoring\artifacts\hook-catalog.csv` | Update the hook row after the detector helper name changed. |
| `specs\2696-missing-edge-cases\spec.md` | Record the SpecKit requirement contract. |
| `specs\2696-missing-edge-cases\plan.md` | Record the implementation plan and file set. |
| `specs\2696-missing-edge-cases\tasks.md` | Record the ordered tasks. |
| `specs\2696-missing-edge-cases\triage.md` | Record the full triage table. |
| `changelog.d\issue-2696-missing-edge-cases.md` | Add the release-note fragment. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Existing detector method length | The file already exceeds the new function limit in places. | A broad module split would enlarge this risk-focused repair. |
