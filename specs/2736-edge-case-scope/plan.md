# Implementation Plan: Edge-Case Detector Scope

**Branch**: `fix/2736-edge-case-scope` | **Date**: 2026-09-16 |
**Spec**: `specs/2736-edge-case-scope/spec.md`

**Input**: Feature specification from
`specs/2736-edge-case-scope/spec.md`

## Summary

Replace the manual `edge-case-required` marker with inferred applicability.
Add detector metrics to the analyzer report. Extend the guard proof audit so a
detector with zero real scope fails.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Standard library only for the changed analyzer and
audit code.

**Storage**: JSON report files under `tools/test_quality_analyzer/output/`.

**Testing**: pytest, ruff, black, mypy, radon, the analyzer CLI, and the guard
proof audit.

**Target Platform**: Windows development hosts and Linux CI runners.

**Project Type**: Python command-line tooling.

**Performance Goals**: Keep one analyzer run within the existing local runtime.

**Constraints**: Do not edit the generated Mist API documentation. Keep helper
and status-code exclusions from pull request #2734.

**Scale/Scope**: Repository test discovery reports about 16600 collected tests.

## Constitution Check

- The change uses class-based detector and audit code.
- The change keeps path handling in `pathlib.Path`.
- The change adds logging before and after meaningful analyzer actions.
- The change adds tests that prove the new guard fails on a zero-scope report.
- Existing analyzer modules exceed some size limits. This change edits them
  surgically and does not increase the module count at their hierarchy level.

## Project Structure

### Documentation (this feature)

```text
specs/2736-edge-case-scope/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
tools/test_quality_analyzer/detection/missing_edge_case.py
tools/test_quality_analyzer/detection/types.py
tools/test_quality_analyzer/reporting.py
tools/test_quality_analyzer/report.schema.json
tools/test_quality_analyzer/__main__.py
tools/guard_proof_audit.py
tests/tools/test_quality_analyzer/test_meta_fixtures.py
tests/guardrails/test_guard_proof_audit.py
tools/test_quality_analyzer/fixtures/bad/test_missing_edge_case_bad.py
tools/test_quality_analyzer/fixtures/good/test_missing_edge_case_good.py
changelog.d/issue-2736-edge-case-scope.md
```

**Structure Decision**: Keep the detector in the existing analyzer package.
Keep the audit extension in the existing guard proof audit module.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Existing analyzer modules exceed size targets. | The issue needs a surgical repair in existing analyzer files. | Moving the analyzer package would increase risk and change unrelated code. |
