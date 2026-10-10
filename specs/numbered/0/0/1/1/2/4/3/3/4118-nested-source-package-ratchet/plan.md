# Implementation Plan: Nested Source Package Ratchet

## Technical Context

The existing source structure guard checks only two levels below `src`.
Issue #4118 requires a tracked-path measurement for every nested Python directory.
The new guard will remain in `tests/guardrails` and will read a checked-in JSON baseline.

## Design

1. Read `src/**/*.py` from Git with a NUL-delimited `git ls-files` call.
2. Build every directory prefix without checking for `__init__.py`.
3. Count direct Python modules except `__init__.py`.
4. Count immediate child directories that contain a tracked Python descendant.
5. Exclude the `src` prefix from the directory count.
6. Load and validate the JSON baseline.
7. Compare the active path set, each child count, and total excess.
8. Print the examined directory count, violation count, and total excess.

## Ratchet Decisions

- A new measured violation fails the guard.
- An increased count for an existing path fails the guard.
- A greater total excess fails the guard.
- An entry at five or fewer children is stale and fails the guard.
- A missing or malformed baseline fails with the examined count.
- The guard validates issue number shape locally and does not call GitHub.

## File Plan

| File | Purpose |
| - | - |
| `tests/guardrails/nested_package_baseline.json` | Record the current violations |
| `tests/guardrails/test_nested_package_structure.py` | Measure and enforce the ratchet |
| `spec.md` | Record behavior and constraints |
| `plan.md` | Record implementation decisions |
| `tasks.md` | Record ordered delivery tasks |

The owner of `.github/copilot-instructions.md` must add the guidance after PR #4124 releases or transfers ownership.

## Validation Plan

Run the focused guard tests, Ruff, Black, and the test-quality gate.
Defer CPU-heavy validation until the fleet coordinator reports lower load.
