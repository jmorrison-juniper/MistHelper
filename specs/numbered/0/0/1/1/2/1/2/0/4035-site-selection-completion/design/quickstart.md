# Validation Guide

## Prerequisites

Use the worktree environment created by `python3 scripts/bootstrap_worktree.py`.
Do not provide production credentials.

## Commands

Run the focused terminal and selector tests:

```text
.venv/bin/python -m pytest -q tests/unit/web_portal/test_portal_silent_completion.py tests/unit/ui/test_prompt_utils.py tests/e2e/web_portal/test_operation_terminal_reconciliation.py
```

Expect successful selections to complete without an export file.
Expect invalid selections and silent exports to fail.
Expect explicit empty exports to retain their reason.

The [terminal contract](contracts/terminal-result.md) defines the expected completion message.

## Measured Results

The initial focused run passed 120 tests.
The expanded portal, output-discovery, selector, browser, and structural-guard run passed 1,281 tests and skipped one test.
Repository Ruff passed. Black accepted all three changed Python files.
Compilation and targeted Bandit passed.
The documented CI mypy scope passed for 860 source files.
The direct portal-module mypy check reported 70 errors on both this branch and unchanged main, with no new diagnostic.
The symbol check reported no module-level name change.
Docstring coverage reached 100 percent. The changed method has cyclomatic complexity 7.
All eight feature Markdown files passed the STE threshold.

## Specification Analysis

The read-only review found no blocking inconsistency, ambiguity, duplication, or uncovered requirement.
FR-001 and FR-002 map to T003, T004, and T005.
FR-003 maps to T003 and T006.
FR-004 and FR-005 map to T002, T006, and T008.
FR-006 maps to T003, T005, T006, and T008.
SC-001, SC-002, and SC-003 map to the corresponding selection and terminal-state regression tasks.
All nine requirements and success criteria have task coverage. All nine tasks have a requirement or validation purpose.
The existing structural debt remains unchanged, as documented in the plan.
