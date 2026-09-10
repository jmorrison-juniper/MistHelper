# Implementation Plan: Compliance analyzer parallel jobs

**Branch**: `feat/2428-parallel-compliance-analyzer` | **Date**: 2026-09-09 | **Spec**: `specs/2428-parallel-compliance-analyzer/spec.md`

**Input**: Feature specification from `specs/2428-parallel-compliance-analyzer/spec.md`

## Summary

Add an opt-in spawned process pool to `tools.compliance_analyzer`. Keep the default sequential path. Use the measured 8-worker automatic cap and 16-file batch size.

## Technical Context

**Language/Version**: Python 3.13.3.

**Primary Dependencies**: Standard library only. Use `concurrent.futures` and `multiprocessing`.

**Storage**: Markdown report files only.

**Testing**: pytest, ruff, black, py_compile, and report byte comparison.

**Target Platform**: Windows and Linux developer workstations, plus GitHub Actions.

**Project Type**: Python CLI tool.

**Performance Goals**: At least 1.5 times faster on the repository-wide scan.

**Constraints**: Preserve report values, report order, and exception behavior.

**Scale/Scope**: 1,383 Python files measured in the current repository.

## Constitution Check

- The work starts from a measured bottleneck.
- The default behavior stays sequential.
- The process start method is explicit.
- Worker count and task batching are bounded.
- Tests prove parity and failure behavior.

## Project Structure

### Documentation

```text
specs/2428-parallel-compliance-analyzer/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
tools/compliance_analyzer/
├── __main__.py
└── engine.py

tests/unit/
└── test_compliance_analyzer.py
```

**Structure Decision**: Update the existing analyzer package and its existing unit test file.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Worker helper function | Spawn requires an importable module-level callable | A bound method or closure does not pickle on Windows |
