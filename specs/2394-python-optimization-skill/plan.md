# Implementation Plan: Python optimization skill

**Branch**: `docs/2394-python-optimization-skill` | **Date**: 2026-09-16 | **Spec**: `specs/2394-python-optimization-skill/spec.md`

**Input**: Feature specification from `specs/2394-python-optimization-skill/spec.md`

## Summary

Continue the existing worktree for issue #2394.
Improve the repository `optimizing-python` skill instead of adding a duplicate.
Ground the skill in MistHelper measurements, quality gates, and safety rules.

## Technical Context

**Language/Version**: Markdown documentation with Python 3.13 used only for verification commands.

**Primary Dependencies**: Installed `mistapi` version `0.64.0`, the STE linter, GitHub Actions run history, and repository benchmarks.

**Storage**: Git-tracked Markdown files only. Measurement artifacts stay under `data/performance/` and do not enter the commit.

**Testing**: STE linter, repository quality gates, benchmark execution, and workflow run inspection.

**Target Platform**: Windows development worktree.

**Project Type**: Documentation and skill guidance.

**Performance Goals**: The skill must require a reproducible before number and after number for each retained optimization.

**Constraints**: Do not edit application code, OpenAPI source files, generated API pages, or workflow files.

**Scale/Scope**: One skill entry point, four reference guides, three SpecKit files, and one release-note fragment.

## Constitution Check

The change is documentation-only.
No Python implementation change is planned.
The plan obeys the issue-first rule because issue #2394 owns the branch.
The plan obeys the one-term rule because it improves one `optimizing-python` skill.
The plan avoids duplicate skills for the same concept.

## Project Structure

### Documentation for this feature

```text
specs/2394-python-optimization-skill/
├── spec.md
├── plan.md
└── tasks.md
```

### Source files for this feature

```text
.github/skills/optimizing-python/
├── SKILL.md
└── references/
    ├── benchmarking.md
    ├── optimization-checklist.md
    ├── report-template.md
    └── installation-and-sources.md

changelog.d/
└── issue-2394-python-optimization-skill.md
```

**Structure Decision**: Improve the existing `optimizing-python` skill because the repository must use one skill per concept.

## Files added or changed

| File | Action | Reason |
| - | - | - |
| `.github/skills/optimizing-python/SKILL.md` | Update | Add MistHelper measurement sources and repository quality gates. |
| `.github/skills/optimizing-python/references/benchmarking.md` | Update | Add reproducible repository measurement commands and run evidence. |
| `.github/skills/optimizing-python/references/optimization-checklist.md` | Update | Add the 5-Item Rule, gate list, and broad-exception warning. |
| `.github/skills/optimizing-python/references/report-template.md` | Update | Add MistHelper validation evidence fields. |
| `.github/skills/optimizing-python/references/installation-and-sources.md` | Update | Add repository source references and verification rules. |
| `specs/2394-python-optimization-skill/spec.md` | Add | Record the user need and acceptance criteria. |
| `specs/2394-python-optimization-skill/plan.md` | Add | Record the implementation plan. |
| `specs/2394-python-optimization-skill/tasks.md` | Add | Record dependency-ordered work. |
| `changelog.d/issue-2394-python-optimization-skill.md` | Add | Record the user-visible documentation change. |

## Verified claims

| Claim | Evidence command | Result |
| - | - | - |
| The installed SDK version is `0.64.0`. | `.\.venv\Scripts\python.exe -c "import mistapi; print(mistapi.__version__)"` | `0.64.0` |
| The performance package overhead can be reproduced locally. | `.\.venv\Scripts\python.exe tools\bench_performance_overhead.py --calls 20000 --repeats 9 --out data\performance\issue2394-performance-overhead.json` | Disabled 193 ns, base 8,322 ns, targeted 7,998 ns on this workstation. |
| Pull request #2690 recorded the before duration. | `gh pr view 2690 --json body` and `gh run view 34983706229 --json jobs` | The PR body reports 11 minutes 47 seconds. Run timestamps show 11 minutes 50 seconds. |
| Pull request #2690 recorded the after duration. | `gh run view 35020159627 --json jobs` | The longest main shard was `root-units` at 4 minutes 48 seconds. |
| The repository contains the flattening benchmark. | `Get-ChildItem scripts\benchmarks` and file read | `scripts/benchmarks/bench_flatten_dict.py` measures 500 synthetic Mist records. |

## Complexity Tracking

No constitution violation is required.
