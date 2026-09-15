# Implementation Plan: Analyzer Skip Reporting

**Branch**: `1768-analyzer-skips` | **Date**: 2026-09-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/1768-analyzer-skips/spec.md`

## Summary

Add explicit coverage reporting to each analyzer under `tools`. The change records read files, skipped files, and skip reasons. It also fails when a caller names a target that the analyzer cannot measure.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard library only. No new dependency is added.

**Storage**: Markdown, JSON, and console analyzer output only.

**Testing**: pytest tests for compliance, refactor, STE, and test quality analyzer coverage reporting.

**Target Platform**: Windows developer workstations and GitHub Actions Linux runners.

**Project Type**: Repository-internal command-line tools.

**Performance Goals**: Coverage reporting adds only list operations and does not change analyzer complexity.

**Constraints**: No change to `MistHelper.py`. No one-off container. No new external service. Use `pathlib.Path` for paths.

**Scale/Scope**: Four analyzer packages under `tools`, one helper module, one workflow configuration entry, one script, tests, and one release note.

## Constitution Check

| Principle | Status | Notes |
| - | - | - |
| Five-Item Rule | PASS | New helper code uses small classes and short methods. |
| Class-Based Architecture | PASS | New behavior lives in named classes. No wrapper-only function is added. |
| Safety-First | PASS | The tools do not read secrets and do not run destructive operations. |
| Full Deployment Pipeline | PASS | Local gates, commit, push, pull request, and checks are part of the task. |
| Observability & Logging | PASS | New actions log before and after meaningful work. |
| Inline Comments | PASS | New executable lines include inline comments. |
| Action Logging | PASS | New classes use `logging.info` before actions and `logging.debug` after actions. |

No constitutional violation exists.

## Project Structure

### Documentation (this feature)

```text
specs/1768-analyzer-skips/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
tools/
├── analyzer_coverage.py
├── check_compliance.py
├── compliance_analyzer/
├── refactor_analyzer/
├── ste_linter/
└── test_quality_analyzer/

tests/tools/
├── test_analyzer_coverage.py
├── test_compliance_analyzer_coverage.py
├── test_refactor_analyzer_coverage.py
├── test_ste_linter_coverage.py
└── test_quality_analyzer/
```

**Structure Decision**: Add one shared helper module under `tools` to keep the reporting vocabulary consistent.

## Files Changed

- `tools/analyzer_coverage.py`: shared coverage record, summary, and renderer classes.
- `tools/compliance_analyzer/engine.py`: collect skipped targets and git-ignore skips.
- `tools/compliance_analyzer/__main__.py`: fail explicit skipped targets and print coverage.
- `tools/compliance_analyzer/reporting.py`: write coverage into Markdown.
- `tools/refactor_analyzer/analysis.py`: collect module graph parse and resolve skips.
- `tools/refactor_analyzer/graph.py`: expose skipped import records.
- `tools/refactor_analyzer/reporting.py`: write coverage into Markdown.
- `tools/refactor_analyzer/__main__.py`: print coverage summary.
- `tools/ste_linter/cli.py`: collect graded and skipped paths.
- `tools/ste_linter/report.py`: write coverage into text and JSON output.
- `tools/test_quality_analyzer/discovery.py`: report omitted test roots and missing roots.
- `tools/test_quality_analyzer/__main__.py`: fail unexpected skips and include analyzed files.
- `tools/test_quality_analyzer/reporting.py`: write coverage into JSON and Markdown.
- `pyproject.toml`: include `tools` in Bandit targets.
- `scripts/run_repository_analyzers.py`: document and run the full repository analyzer set.
- `tests/tools/...`: prove the new reporting and failure behavior.
- `changelog.d/issue-1768-analyzer-skips.md`: release note fragment.

## Complexity Tracking

No new violation exists. Existing `tools` contains more than five children. The constitution permits a narrow edit to an existing noncompliant parent. This change does not increase the root child count in `tools` beyond one required helper and one required script for the issue.
