# Implementation Plan: C0103 naming exceptions in MistHelper.py

**Branch**: `chore/4130-c0103-invalid-names` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/1/3/0/1/0/4130-c0103-invalid-names/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/1/3/0/1/0/4130-c0103-invalid-names/spec.md`. The route is the base-5 encoding of issue 4130 from `Get-SpecRadixSegments` in `.specify/scripts/powershell/spec-route.ps1`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`.

## Summary

Pylint 4.1.4 reports 25 predicted C0103 messages in `MistHelper.py` on current `main`. `web_portal/services/operation.py` has none, because PR #4662 fixed it on 2026-11-09. This change keeps every flagged name. It adds 24 reviewed `invalid-name` pragmas and one module-name rule in `pyproject.toml`. It changes no executable line.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.

**Primary Dependencies**: pylint 4.1.4 (`pyproject.toml` line 117), ruff, black, mypy, pytest, and `misthelper-devtools` 0.6.4 for `symbol-diff`. No dependency changes.

**Storage**: Not applicable.

**Testing**: Three guard test cases in the existing `tests/guardrails/test_src_public_symbol_preservation.py`. Two existing targeted test modules run unchanged.

**Target Platform**: Windows 11 workstation, macOS, Linux, and the Podman container.

**Project Type**: Command-line tool with a single entry-point module and a source package.

**Performance Goals**: Not applicable. The change alters no runtime path.

**Constraints**: No module-level name may change, because the symbol gate fails on any lost or added name. No executable line may change.

**Scale/Scope**: Two tracked files change (`MistHelper.py` comments, `pyproject.toml` one key). One guardrail file gains three test cases. One changelog fragment and one record folder are added.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record adds one folder under the route. The feature root holds five children, `design` holds four, and `design/checklists` holds one. The change adds no direct child to `tests/guardrails`, which already holds 79 children. |
| II. Class-Based Architecture | Pass | The change adds no function and no class. |
| III. Safety-First | Pass | The change adds no input handling and no destructive operation. |
| IV. Full Deployment Pipeline | Pass with plan | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. Steps 10 to 12 (main build, revision check, and deployment) run after the merge under orchestrator control. |
| V. Observability and Logging | Pass | The change adds no log statement. Each pragma reason uses ASCII text. |
| VI. Inline Comments | Pass | Each kept name carries a reason on its line. The pragmas are comments, and no executable line is new. |
| VII. Action Logging | Pass | The change adds no executable action. |
| Mist Cloud Transport | Not applicable | The change sends no request to Mist Cloud. |
| File Paths | Pass | The change adds no path construction. |
| Data Directory | Pass | The change writes no product output. |
| Container Runtime | Not applicable | The change adds no container. The container build runs after the merge. |
| Security Findings: Fix Over Suppress | Pass with recorded exception | The findings are naming-convention findings, not security findings. Renames are blocked by the symbol gate and by string-keyed bindings. Decisions D-2 and D-3 record the exception. Decision D-8 tracks the root-cause work in a follow-up issue. |
| Documentation | Pass | The change adds one changelog fragment (FR-009). No operator-facing behavior changes, so no README update is needed. |
| Hot File Coordination | Pass | No open pull request changes `MistHelper.py`, `pyproject.toml`, or the guardrail host file. The check ran on 2026-11-26 (decision D-9). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/0/1/0/4130-c0103-invalid-names/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

The folder `design/contracts/` is omitted. This change adds no CLI option, no menu operation, no output column, and no API shape.

### File Change Map

| Path | Action | Purpose | Lines |
| - | - | - | - |
| `MistHelper.py` | Modify | Add one `invalid-name` pragma with a reason to each kept name | 182, 183, 184, 1082, 1096, 1114, 1117, 1123, 1125, 1126, 1135, 1136, 1137, 1150, 1172, 1174, 2345, 2458, 2460, 2461, 2463, 2474, 2475, 2479 |
| `pyproject.toml` | Modify | Add `module-rgx` under `[tool.pylint.basic]` with a comment | Near line 596 |
| `tests/guardrails/test_src_public_symbol_preservation.py` | Modify | Add three guard test cases at the end of the file | End of file |
| `changelog.d/issue-4130-c0103-invalid-names.md` | Add | One release-note fragment | New file |
| `specs/numbered/0/0/1/1/3/0/1/0/4130-c0103-invalid-names/` | Add | Copy of the record from the draft folder | New folder |
| `web_portal/services/operation.py` | No change | Already fixed by PR #4662 at line 915 | Not applicable |

The line numbers refer to the current `main` blob `98d7828479ded6bc4c83d15e0c1847171cfbfd49`. Each insertion shifts later lines, so the implementation adds pragmas from the bottom of the file upward.

### Dependencies

No new package. The change uses the pinned pylint 4.1.4 and the `symbol-diff` tool already in `.venv\Scripts`.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A pragma hides a future finding on the same line. | Each pragma carries a reason. The guard fixes the pragma count at 24. |
| The `module-rgx` option does not take effect. | Task T009 reruns pylint on `MistHelper.py`. Rollback removes the key. |
| A predicted finding does not occur in pylint. | Task T009 runs with `useless-suppression` enabled. The pragma for that line is removed. |
| A pragma pushes a code line past 120 characters. | Ruff exempts a pragma comment when the code before it fits the limit. Task T-LOCAL-GATES runs `ruff check .` to confirm. |
| `main` moves before the pull request opens. | Rebase the branch, then rerun task T009 and the local gates. |
| Another pull request changes `MistHelper.py` during the work. | Stop and wait. `MistHelper.py` is a hot file. |

## Rollback

Warning: do not force-push a branch that another agent shares. Caution: rollback before merge uses a new commit on the feature branch. After the squash merge, open a new issue and branch from `main`.

Before merge, revert the commit on the feature branch. Alternatively, remove the 24 pragma comments and the `module-rgx` line. After merge, follow the post-merge fix rule in `AGENTS.md`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| 24 `invalid-name` pragmas in `MistHelper.py` | The symbol gate and the string-keyed bootstrap require the current module-level names. | A rename fails the symbol gate. A repository-wide `const-naming-style = "any"` removes checks for every module. |
| One module-name rule in `pyproject.toml` | The entry-point file name is fixed by the gates, the container, and the operators. | A rename changes every import, every gate command, and every operator command. |
