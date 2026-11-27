# Implementation Plan: Check Every Operation Pair in the mistapi Spec Guard

**Branch**: `fix/4935-mistapi-spec-pairs` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification at `specs/numbered/0/0/1/2/4/2/2/0/4935-mistapi-spec-pairs/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The guard in `tests/guardrails/test_mistapi_spec_modules.py` keeps one operation pair for each spec file. The change returns every pair. It reports each operation line that has no module line. It allows two declared absences, and the SDK check verifies each one on every run. The change also corrects spec file 511 and adds a fixture test that fails on the old logic.

## Technical Context

- **Language/Version**: Python 3.15 or newer. The repository instructions name this version.
- **Primary Dependencies**: pytest and the installed `mistapi` package, version 0.64.1, for the SDK source scan. No new dependency.
- **Storage**: Not applicable. The guard reads spec files and SDK source files only.
- **Testing**: pytest in `tests/guardrails/test_mistapi_spec_modules.py`. The guardrails shard runs the same file in CI.
- **Target Platform**: Windows 11, macOS, and Linux. The repository instructions name these platforms.
- **Project Type**: One test module with a real guard test and fixture tests.
- **Performance Goals**: Not measured. The survey parsed 288 SDK files. Task T-LOCAL-GATES records the run time.
- **Constraints**: Output is ASCII only. The guard sends no network request. Paths use `pathlib`.
- **Scale/Scope**: 910 spec files on `main`. 489 operation lines in the non-frozen spec files.

## Constitution Check

The check uses `.specify/memory/constitution.md` version 1.9.0. Each row states the rule, the result, and the reason.

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule | Pass | The record adds one feature folder under the route. Each new directory holds five children or fewer. |
| Principle II, class-based architecture | Pass | The new helpers are static methods of `MistapiSpecModuleIndex`. No wrapper function is added. |
| Principle III, safety-first input | Pass | The guard reads repository files only. It reads no operator input. |
| Principle IV, full deployment pipeline | Pass with conditions | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order. The changelog fragment is part of the change. |
| Principle V, observability and ASCII logging | Pass | FR-013 and the interface contract require ASCII text only. |
| Principle VI, inline comments | Pass | FR-013 requires an inline comment on each changed executable line. |
| Principle VII, action logging | Pass | FR-013 requires an `info` line before the file read and a `debug` line after it. |
| Technology, Python and mistapi | Pass | The Python version does not change. The guard reads SDK source and sends no Mist REST request. |
| Technology, file paths | Pass | The guard uses `pathlib.Path`. The declared absence keys use forward slashes. |
| Technology, test containers | Not applicable | No container starts for this change. |
| Technology, data directory | Not applicable | The guard writes no product output. |
| Security findings | Not applicable | No security tool reports a finding for this change. |
| Development workflow, menu operations | Not applicable | No menu operation changes. |
| Documentation, release notes | Pass | Decision D-10 adds one fragment, as Principle documentation requires. |
| Escalation to SpecKit | Pass | The change touches three files, so the constitution requires a specification. This record is that specification. |
| Multi-agent git | Pass with conditions | Task T-PR checks open pull requests for file overlap. The branch starts from `main`. |

## Architecture

The guard runs four steps.

1. `spec_declarations` lists each `spec.md` under `specs/` in sorted order. It skips the frozen spec files.
2. `_source_fields` reads one spec file. It returns each operation pair in file order. A pair has no module when the next operation line or the end of the file comes first.
3. `failure_messages` checks each pair. It reports orphans, mismatches, contradicted absences, and zero-pair runs.
4. The real test prints the summary line and asserts that no failure exists.

The declared absences live in `ABSENT_SDK_OPERATIONS`. This class attribute of `MistapiSpecModuleIndex` maps POSIX spec paths to operation identifiers. The contract in `design/contracts/guard-interface.md` gives the exact shapes.

## File Change Map

| Path | Action | Purpose |
| - | - | - |
| `tests/guardrails/test_mistapi_spec_modules.py` | Modify | Pair parser, scan change, declared absences, failure helper, summary line, and four new fixture tests. Covers FR-001 to FR-007, FR-009, FR-010, and FR-013 to FR-016. |
| `specs/511-mist-count-org-client-fingerprints/spec.md` | Modify, lines 14 to 16 | Declares the installed SDK module and corrects the stale status line. Covers FR-008. |
| `changelog.d/issue-4935-mistapi-spec-pairs.md` | Add | One `Fixed` fragment for the change. Covers FR-015. |
| `specs/numbered/0/0/1/2/4/2/2/0/4935-mistapi-spec-pairs/` | Add | This record folder. Covers FR-012 and the record layout. |

No other path changes. This meets FR-011.

## Dependencies

No new package is added. The guard depends on the installed `mistapi` package, version 0.64.1, and on pytest. The repository pins mistapi with `mistapi>=0.64.0,<0.65`.

## Project Structure

The record folder holds these children. It moves to the route folder in task T-PR.

```text
4935-mistapi-spec-pairs/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      guard-interface.md
    checklists/
      requirements.md
      test-quality.md
```

The feature root holds five children. The `design` folder holds five children. The `contracts` folder holds one file, because the guard exposes an interface. The `checklists` folder holds two files.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| A non-frozen spec file has a defect that the new guard finds. | The pull request shows a red guard. | Research R4 finds no mismatch in the simulation. Task T-LOCAL-GATES runs the real guard before the pull request. |
| The regular-expression simulation differs from the `ast` scan. | A pair result differs from the simulation. | The gate run is the authority. Research R4 and the Unverified list name the approximation. |
| The absence list grows without review. | A stale declaration hides a gap. | The drift check fails when the SDK defines the operation. The reviewer checks the list in the pull request. |
| A module line without an operation line hides a declaration. | A silent gap in the guard. | Research R3 finds no such line on `main`. The Out of Scope section keeps the policy for a later decision. |
| Spec file 511 changes in parallel with another pull request. | A merge conflict. | Task T-PR checks open pull requests for overlapping files. |
| The record `spec.md` begins a line with the guard prefix. | The guard reads a false pair from the record. | FR-012 and task T010 check the record before the pull request. |
| A reviewer objects to the changelog fragment. | A small review delay. | Decision D-10 cites the constitution precedence. The owner can remove the fragment. |

Caution: a red guard blocks the pull request. Task T003 must land before task T006 runs the real guard.

## Rollback Steps

1. If the pull request is open, close it. Delete its branch by name.
2. If the merge landed, create a branch from `main`. Revert the squash commit with `git revert`. Open a new pull request.
3. Do not force-push a shared branch. Add the revert as a new commit.

The rollback restores the one-pair helper, the previous spec file 511, and the previous guard file. The record folder is removed with the revert.

## Complexity Tracking

Not applicable. The Constitution Check shows no violation that needs a justification row.
