# Implementation Plan: Unused Noqa Directive Removal

**Branch**: `lint/1792-unused-noqa` (SpecKit feature directory `1792-unused-noqa-directives`) | **Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1792-unused-noqa-directives/spec.md`

**GitHub Issue**: [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792)

## Summary

Ruff reports 286 `# noqa` directives that suppress nothing. Ruff repairs all 286 without help. The whole repair is one command plus a careful read of the difference.

The work then adds `RUF100` to the ruff `select` list, so that the count cannot return.

This plan orders the work in three steps. Measure first. Repair second. Close the gate third. The gate step comes last, because the gate fails while any result remains.

## Technical Context

**Language/Version**: Python 3.13 (`pyproject.toml` target `py313`)

**Primary Dependencies**: `ruff` 0.16.0. This work adds no dependency.

**Storage**: Not applicable. The work changes comment text and one configuration line.

**Testing**: `pytest` with `--cov=src/ --cov-fail-under=80`. The suite must keep its pass count.

**Target Platform**: The CI runner uses Linux. A developer works on Windows. Ruff reports the same count on both, because the `extend-exclude` list uses paths that ruff normalizes.

**Project Type**: Static analysis cleanup. The work adds no module and no class.

**Performance Goals**: The lint gate must stay inside its current runtime. Ruff scans the repository in about two seconds today.

**Constraints**:

- The root ruff line length is 120 characters. The removal shortens lines, so no line grows.
- `ruff check .` reads the whole repository. Its `extend-exclude` list drops `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`.
- `black` formats the whole repository. A removed trailing comment can change the line width that `black` prefers, so `black` must run after the repair.
- The repair touches one test file. The unit suite must run.

**Scale/Scope**: 286 directives, 94 files, and one configuration line.

### Measurement contract

Run the command below to measure the baseline. Record the value before the first edit.

```powershell
.venv\Scripts\python.exe -m ruff check . --extend-select RUF100 --statistics
```

The expected output holds one line.

```text
286     RUF100  [*] unused-noqa
```

The `[*]` marker states that ruff repairs the result without help.

**Warning**: Do not measure with `--select RUF100`. That form turns off every other rule and reports 320 results. The extra 34 results name a code that the project selects, so each of those directives suppresses a real result. A repair with that form breaks the lint gate.

If the count differs from 286, stop. Record the new count in this plan and continue with the new value. Do not change the specification text in silence. A maintainer measured 231 on 2026-08-05 and 286 on 2026-08-06, so the value moves.

### Verified mechanics

A maintainer probed the ruff behavior before this plan. Three results shape the tasks.

1. `ruff check . --extend-select RUF100 --fix` removes each unused code from a directive. It removes the whole comment when no other text remains.
2. A directive that names two codes keeps the code that produces a result. Ruff removes the other code and leaves the line.
3. `--ignore-noqa` reveals the true count for any rule. The difference between the two counts equals the number of lines that a directive hides.

### Discovered risk: 88 lines hide a real blind except block

This risk is the most important finding in the whole plan.

| Command | `BLE001` count |
| - | - |
| `ruff check . --select BLE001 --statistics` | 412 |
| `ruff check . --select BLE001 --ignore-noqa --statistics` | 500 |

The 88-line difference means that 88 lines carry a `# noqa: BLE001` directive and hold a real blind `except` block. Today the directive changes nothing, because the `select` list does not hold `BLE001`.

The day the team selects `BLE001`, those 88 directives start to hide real results. The gate then reports 412 results and never reports the other 88. A team that clears 412 results believes the work is complete.

This plan therefore states a hard order. This work lands first. Issue [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794) starts second.

The same trap applies to `DTZ005` at a smaller scale. Ruff reports 56 results by default and 57 with `--ignore-noqa`. One site hides. Issue [#1795](https://github.com/jmorrison-juniper/MistHelper/issues/1795) reads that number.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS | The work adds no function and changes no function body. |
| II. Class-Based Architecture (No Wrappers) | PASS | The work adds no class and no wrapper. |
| III. Safety-First | PASS | The work changes no input handling and no confirmation prompt. |
| IV. Full Deployment Pipeline | ADAPTED | The work follows the branch and pull request workflow. The container needs no rebuild, because no runtime behavior changes. |
| V. Observability and Logging | PASS | The work adds no log call. Every removed directive is ASCII text. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS with a note | The work removes comment text and adds none. Principle VI asks for a comment on each changed line of code. This work changes no line of code. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS | The work adds no action and therefore adds no log call. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS | The work removes suppressions. It adds none. |

## Project Structure

### Documentation (this feature)

```text
specs/1792-unused-noqa-directives/
├── spec.md              # The feature specification
├── plan.md              # This file
└── tasks.md             # The task list
```

### Source code (repository root)

The repair touches 94 files. The list below names the eight files that hold 127 of the 286 directives. The other 86 files hold 1 to 6 directives each.

```text
pyproject.toml                                        # Step 3: add RUF100 to the select list

src/
├── device/ap_profile_migration_manager.py            # 67 directives
├── site/address_audit/ui_geocoder.py                 # 10 directives
├── export/site_export_utils.py                       #  9 directives
├── firmware/firmware_manager.py                      #  9 directives
├── ssid_consolidation/_ssid_template_phase45.py      #  9 directives
├── reports/e911_bssid.py                             #  8 directives
└── ssh/batch/interactive_batch_executor.py           #  7 directives

tests/unit/refactors/test_fast_mode_small_seams.py    #  8 directives
```

**Structure Decision**: The work stays inside the current tree. It creates no file and deletes no file.

## Phased approach

The work runs in three phases. Each phase ends with a measurement.

### Phase A - Measure and record

Record the baseline count. Record the `BLE001` count with and without `--ignore-noqa`. Record the `DTZ005` count with and without `--ignore-noqa`.

These three records prove the latent suppression claim. A later reader needs them.

**Exit measurement**: The three records exist and the `RUF100` count reads 286.

### Phase B - Repair

Run one command. Read the whole difference.

```powershell
.venv\Scripts\python.exe -m ruff check . --extend-select RUF100 --fix
```

**Warning**: Do not add any other rule to the `--extend-select` list in this command. A mixed repair hides the comment change inside a code change, and a reviewer then cannot confirm requirement FR-003. Do not use the `--select` form. That form deletes 34 live suppressions.

Read the difference with `git diff`. Search for any changed line that does not start with a comment marker. The expected count of such lines is zero.

The single file `src/device/ap_profile_migration_manager.py` holds 67 directives. Read that file difference on its own.

**Exit measurement**: `ruff check . --extend-select RUF100` reports zero. The count of changed lines that are not comments reads zero.

### Phase C - Close the gate

Add `RUF100` to the `select` list in `pyproject.toml`.

```toml
select = ["E", "F", "W", "I", "UP", "B", "G", "RUF100"]
```

Add a comment above the list that states why `RUF100` sits there. The comment must state that a directive with no matching result is a false record.

**Warning**: This step must land in the same pull request as Phase B. A separate pull request would let the count grow between the two merges.

**Exit measurement**: `ruff check .` passes with the new list. A test directive with no matching result fails the gate.

## Risk register

| Risk | Likelihood | Effect | Control |
| - | - | - | - |
| Ruff removes a comment that a reader needs | Low | A reader loses context | Task T008 reads the whole difference by hand |
| The repair changes a line of code | Very low | A silent behavior change | Task T008 counts the changed lines that are not comments. The expected value is zero. |
| A concurrent pull request adds a directive | Medium | The count changes | Task T012 measures the count again before the final push |
| `black` wants to reformat a shortened line | Medium | The format gate fails | Task T009 runs `black` after the repair |
| Issue #1794 starts before this work lands | Medium | 88 results disappear | Task T013 writes the warning into the pull request text and comments on issue #1794 |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| Phase B and Phase C land in one pull request | The gate must close at the same moment that the count reaches zero | Two pull requests leave a window in which a contributor adds a new directive with no gate to stop it |
