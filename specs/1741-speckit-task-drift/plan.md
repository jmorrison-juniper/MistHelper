# Implementation Plan: Speckit task record drift

**Branch**: `chore/1741-speckit-task-drift` | **Date**: 2026-09-13 | **Spec**:
[spec.md](./spec.md)

**Input**: Feature specification from
`specs/1741-speckit-task-drift/spec.md`

## Summary

This feature reconciles the four delivered STE task records. It adds file-path
evidence to each checked task. It adds `tools/speckit_task_audit.py` and unit
tests that prove the audit behavior. It wires the tool into the quality workflow
as an advisory report.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard library only, plus pytest for the tests.

**Storage**: Markdown task files under `specs/`.

**Testing**: pytest, ruff, Black, mypy, and the project quality gates.

**Target Platform**: Windows for local work and Linux for continuous
integration.

**Project Type**: A repository tool, task record updates, and a workflow report.

**Performance Goals**: The audit scans the spec tree in less than 5 seconds.

**Constraints**: Do not edit `MistHelper.py`. Do not edit the five reserved task
files. Do not make the first report blocking.

**Scale/Scope**: The audit reads more than 100 spec directories and their task
records.

## Constitution Check

*GATE: This gate passed before implementation. It passed again before the pull
request.*

| Principle | How this plan meets it |
| - | - |
| Five-Item Rule | The audit code uses small classes and short methods. |
| Class-Based Architecture | `AllowList`, `TaskFileScanner`, and `SpecTaskAudit` own the behavior. |
| Safety-First | The tool reads files and writes no repository data. |
| Full Deployment Pipeline | The plan runs the requested quality gates before commit. |
| Observability | The tool logs each meaningful action with lazy formatting. |
| Inline Comments | Each executable line in the new code carries a same-line comment. |
| Action Logging | Each scan and load action logs before and after the action. |

## Project Structure

### Documentation (this feature)

```text
specs/1741-speckit-task-drift/
├── spec.md
├── plan.md
├── tasks.md
└── analysis.md
```

### Source Code (repository root)

```text
tools/
└── speckit_task_audit.py

tests/unit/tools/
└── test_speckit_task_audit.py

.github/workflows/
└── ci.yml

.specify/templates/
└── tasks-template.md
```

**Structure Decision**: The audit tool lives in `tools/`, because the workflow
and local operators run it directly. The tests live under `tests/unit/tools/`,
because the tool has no production package dependency.

## Reconciliation approach

The first pass counts checked and unchecked task boxes for every spec task file.
The edit pass touches only `specs/1026-ste-linter/tasks.md`,
`specs/1027-ste-dict-extractor/tasks.md`,
`specs/1028-ste-compliance-cleanup/tasks.md`, and
`specs/1030-ste-src-cleanup/tasks.md`. Each checked task receives an evidence
note with a delivered file path.

The pass skips the five reserved task files. It also leaves all other open spec
records unchanged unless a file path proves the task.

## Guard approach

The audit tool counts valid task boxes outside fenced code blocks. It prints each
spec with unchecked tasks and its count. It reads the spec status from
`spec.md`. It fails only when a complete spec still holds an unchecked task that
an allow list does not cover.

The workflow job uses `continue-on-error: true`. This makes the day-one report
visible without blocking unrelated pull requests.

## Complexity Tracking

No constitution violation exists.
