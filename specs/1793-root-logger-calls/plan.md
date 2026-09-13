# Implementation Plan: Module Logger Migration

**Branch**: `refactor/1793-module-logger` (SpecKit feature directory `1793-root-logger-calls`) | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1793-root-logger-calls/spec.md`

**GitHub Issue**: [#1793](https://github.com/jmorrison-juniper/MistHelper/issues/1793)

## Summary

Ruff reports 4478 root logger calls in 223 files. Ruff repairs none of them. The rewrite is mechanical, but the volume forbids a single pull request.

This plan splits the work into 14 slices. Each slice holds one area or one part of a large area. The slices land from the smallest area to the largest area, so that the pattern proves itself at a low cost.

The gate change lands last, in its own pull request, after the last slice reports zero results.

## Technical Context

**Language/Version**: Python 3.13 (`pyproject.toml` target `py313`)

**Primary Dependencies**: `ruff` 0.16.0 and the standard `logging` module. This work adds no dependency.

**Storage**: Not applicable. The work changes call sites and one configuration line.

**Testing**: `pytest` with `--cov=src/ --cov-fail-under=80`. The suite must keep its pass count for each slice.

**Target Platform**: The CI runner uses Linux. A developer works on Windows. Ruff reports the same count on both.

**Project Type**: Behavior-preserving refactor. The work adds no module and no class. It adds one module-level name to each converted module.

**Performance Goals**: The lint gate must stay inside its current runtime. A named logger costs the same as a root logger call at run time.

**Constraints**:

- The root ruff line length is 120 characters. A rewrite from `logging.` to `logger.` shortens each line by two characters, so no line grows.
- `ruff check .` and `black` read the whole repository. Its `extend-exclude` list drops `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`.
- `mypy` now reads `MistHelper.py` as well as `src/`. Issue #888 widened that scope.
- The action logging rule in `.github/copilot-instructions.md` is NON-NEGOTIABLE. The rewrite must keep every message and every level.

**Scale/Scope**: 4478 calls, 223 files, 14 slices, and one configuration line.

### Measurement contract

Run the command below before each slice. Record the value in the slice pull request.

```powershell
.venv\Scripts\python.exe -m ruff check . --select LOG015 --statistics
```

The expected output holds one line.

```text
4478    LOG015  root-logger-call
```

Ruff reports no repair marker, because `LOG015` has no automatic repair. Every edit is a hand edit or a scripted edit with a hand review.

If the count differs from 4478, stop. Record the new count in this plan and continue with the new value.

### Verified mechanics

A maintainer probed the counts on 2026-08-06 at commit `08a75d2`. Three results shape the tasks.

1. The area counts in the specification match the measured values exactly. No drift exists between the issue and the tree.
2. Four files hold 779 of the 4478 calls. `MistHelper.py` holds 303, `src/firmware/firmware_manager.py` holds 228, `src/firmware/org_ap_upgrader.py` holds 143, and `src/firmware/bulk_ap_upgrader.py` holds 105.
3. The `tests` area holds 134 calls, and 53 of them sit in one file. That file is `tests/unit/refactors/test_fast_mode_small_seams.py`.

### Discovered risk: three files break the 500-line slice limit on their own

`MistHelper.py`, `src/firmware/firmware_manager.py`, and `src/firmware/org_ap_upgrader.py` each hold more than 100 calls. A single file cannot split across two pull requests without a broken intermediate state, because the module logger definition must land with the first converted call.

The control is a per-file slice. Each of those three files becomes its own pull request. The line count then reaches about 300 for the largest file, which stays inside the limit.

### Discovered risk: the logging configuration module can recurse

`src/utils/logger_utils.py` configures the logging system. A record that the configuration path emits can re-enter the same path. Specification `1032-bandit-severity-gate` already records one suppression in that module for the same reason.

The control is a separate read. The implementer reads that module in full before any edit and confirms that the module logger does not sit inside a filter or a handler.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS | The work adds one module-level name to each module. It changes no function body structure. |
| II. Class-Based Architecture (No Wrappers) | PASS | The work adds no class and no wrapper function. |
| III. Safety-First | PASS | The work changes no input handling and no confirmation prompt. |
| IV. Full Deployment Pipeline | ADAPTED | The work follows the branch and pull request workflow. The container needs a rebuild after the last slice, because the runtime code changes. |
| V. Observability and Logging | PASS with a gain | The work improves observability. A record then carries the module name. Every message stays ASCII. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS with a note | The module logger line receives an inline comment that states its purpose. A rewritten call keeps its existing comment. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS with a hard constraint | The rewrite keeps every message and every level. Requirements FR-004 through FR-007 state the constraint. A slice that changes a message fails the review. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS | The work adds no suppression. Non-goal NG-001 states this rule. |

## Project Structure

### Documentation (this feature)

```text
specs/1793-root-logger-calls/
├── spec.md              # The feature specification
├── plan.md              # This file
└── tasks.md             # The task list
```

### Source code (repository root)

The work touches 223 files. The list below names the slice boundary for each area.

```text
pyproject.toml                                        # Slice 14: add LOG015 to the select list

MistHelper.py                                         # Slice 11: 303 calls, its own pull request

src/
├── export/                                           # Slices 12 and 13: 678 calls, split by file
├── firmware/
│   ├── firmware_manager.py                           # Slice 9: 228 calls, its own pull request
│   ├── org_ap_upgrader.py                            # Slice 8: 143 calls, its own pull request
│   └── (the rest of the area)                        # Slice 10: 130 calls
├── refactors/                                        # Slice 7: 423 calls, split by file if needed
├── gateway/                                          # Slice 6: 261 calls
├── capture/                                          # Slice 5: 220 calls
├── org/                                              # Slice 4: 191 calls
├── device/                                           # Slice 3: 182 calls
├── site/                                             # Slice 3: 156 calls
├── troubleshooting/                                  # Slice 3: 150 calls
├── auth/                                             # Slice 2: 131 calls
├── inventory/                                        # Slice 2: 131 calls
└── ui/                                               # Slice 2: 131 calls

tests/                                                # Slice 1: 134 calls, the lowest risk
```

**Structure Decision**: The work stays inside the current tree. It creates no file and deletes no file. Each converted module gains one module-level line.

## Phased approach

The work runs in three stages. Every slice inside a stage follows the same steps.

### Stage 1 - Prove the pattern on the lowest risk area

Slice 1 converts the `tests` area. A test module carries no operator value in its log records, so a mistake there costs the least.

The slice proves three facts. The `caplog` fixture still captures the records. The unit suite keeps its pass count. The difference holds only a logger object change.

**Exit measurement**: The `LOG015` count drops by 134. The unit suite keeps its pass count.

### Stage 2 - Convert the production areas from the smallest to the largest

Slices 2 through 13 convert the production code. Each slice follows the same five steps.

1. Search the area for an existing name `logger`. Record any collision.
2. Add the module logger line to each file in the slice.
3. Rewrite each root logger call in those files.
4. Read the whole difference and confirm that only the logger object changed.
5. Run the full gate set and the full unit suite.

**Warning**: Do not change a message text and do not change a level. The action logging rule depends on both. A reviewer who finds one changed message must reject the slice.

**Exit measurement**: The `LOG015` count reaches zero after slice 13.

### Stage 3 - Close the gate

Add `LOG015` to the `select` list in `pyproject.toml`.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G", "LOG015"]
```

**Warning**: This step must follow the last slice. The gate fails on every push while any call remains.

**Exit measurement**: `ruff check .` passes with the new list. A test call to `logging.info` fails the gate.

## Slice ledger

| Slice | Scope | Calls | Files |
| - | - | - | - |
| 1 | tests | 134 | about 20 |
| 2 | src/auth, src/inventory, src/ui | 393 | about 25 |
| 3 | src/device, src/site, src/troubleshooting | 488 | about 30 |
| 4 | src/org | 191 | about 10 |
| 5 | src/capture | 220 | about 10 |
| 6 | src/gateway | 261 | about 12 |
| 7 | src/refactors | 423 | about 25 |
| 8 | src/firmware/org_ap_upgrader.py | 143 | 1 |
| 9 | src/firmware/firmware_manager.py | 228 | 1 |
| 10 | src/firmware, the rest | 130 | about 10 |
| 11 | MistHelper.py | 303 | 1 |
| 12 | src/export, part one | about 340 | about 15 |
| 13 | src/export, part two, and every remaining area | about 1624 | about 60 |
| 14 | pyproject.toml | 0 | 1 |

**Caution**: Slice 13 holds every area that the table above does not name. The implementer must split that slice further once the earlier slices land and the exact remainder is clear. No pull request may exceed 500 changed lines.

## Risk register

| Risk | Likelihood | Effect | Control |
| - | - | - | - |
| A slice changes a message text | Medium | An operator playbook breaks | The slice review reads every changed line. Task T012 states the check. |
| A module already binds the name `logger` | Low | A name collision hides the real object | Each slice starts with a search. Task T008 states the search. |
| A test asserts on the root logger | Medium | A test fails after the slice | Each slice runs the whole unit suite, not the area tests alone |
| The logging configuration module recurses | Low | The process hangs or overflows the stack | Task T034 reads `src/utils/logger_utils.py` before any edit |
| A slice exceeds 500 changed lines | Medium | A reviewer cannot read the difference | The slice ledger caps each slice. Task T009 counts the lines before the push. |
| Issue #886 edits the same lines | Medium | A merge conflict | Task T005 checks the open pull requests for each area before the slice starts |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| The work spans 14 pull requests | 4478 call sites cannot receive a real review in one difference | A single pull request would merge without a review, and the action logging rule needs a human check on every message |
| Three files each take a whole pull request | The module logger line must land with the first converted call in that file | A split inside one file leaves an intermediate state in which the module holds both call forms |
| The gate change lands in its own pull request | The gate fails while any call remains | A gate change inside the last slice would block every push during the slice review |
