# Contract: SpecKit Task Audit Report

**Date**: 2026-11-26

This contract describes the text that the SpecKit task audit prints and the exit code that it returns. The CI step and the guard tests read this text.

## Identity

- **Command**: `speckit-task-audit`. The CI step runs it from the repository root, with `|| true` (RC-01).
- **Implementation**: module `misthelper_devtools.speckit_task_audit` at the pinned commit `2239e7bd` (RC-11, RC-23).
- **Readers**: maintainers read the CI log. `tests/guardrails/test_spec_route_contract.py` asserts parts of the text (RC-37, RC-38). `tests/guardrails/test_process_folder_structure.py` reads the counts through `TaskFileScanner` (RC-34).

## Output lines

The command prints these lines in this order. Source lines refer to `src/misthelper_devtools/speckit_task_audit.py` at `2239e7bd`.

| Order | Line form | Source line | Meaning |
|-------|-----------|-------------|---------|
| 1 | `SpecKit task audit` | 391 | The heading that starts the report. |
| 2 | `Examined <records> feature record(s), <files> task file(s), and <markers> task marker(s): <checked> checked, <unchecked> unchecked, <malformed> malformed.` | 405 to 408 | The summary of the whole scan. |
| 3 | `specs/<path>/tasks.md:<line>: malformed task marker` | 428 | One line for each real malformed marker. |
| 4 | `specs/<path>: <count> unchecked tasks (open)` | Not separately numbered | One line for each record with open tasks. The CI log at run 45774119357 shows this form. |
| 5 | `specs/<path>: missing tasks.md` | 423 | One line for each record without a task file. |
| 6 | `specs/<path>: line <line>: <citation> (<marker>)` | 435 | One line for each checked task with a missing citation. |
| 7 | `No unchecked task boxes found.` | 413 | The result when no record has open tasks. |

Input errors print `Error: <message>` to standard error (line 456).

## Exit code

- The command returns `1` when a complete record has open tasks or a missing citation (lines 162 to 170 and 355).
- The command returns `0` in every other case.
- The CI step ignores the value, because the step ends with `|| true` (RC-01).

## Consumer strings

These strings appear in the consumer tests at main (RC-37, RC-38). A change to any of them breaks those tests.

- `Examined 1 feature record(s), 1 task file(s)`
- `1 task marker(s)`
- `specs/<route>: 1 unchecked tasks`
- `No unchecked task boxes found.`

Caution: Changing a line form in this contract breaks the consumer tests. Update the tests and this contract in the same change.
