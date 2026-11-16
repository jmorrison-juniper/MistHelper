# Implementation Plan: Native Windows Timeout Acceptance

**Branch**: `4777-windows-timeout-acceptance` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/3/1/0/2/4777-windows-timeout-acceptance/spec.md`.

## Summary

Add a bounded, optional Windows acceptance run that executes the existing seven-test timeout-budget module unchanged. A workflow contract will protect its trigger, permissions, native runtime check, test selection, result count, and cancellation behavior.

## Technical Context

**Language/Version**: Python 3.15 and GitHub Actions YAML.

**Primary Dependencies**: Existing `requirements.txt` and `requirements-dev.txt`.

**Storage**: None.

**Testing**: Pytest. The current timeout-budget module collects seven tests and has no parametrized cases.

**Target Platform**: Native Windows hosted runner.

**Project Type**: Optional continuous integration check and its contract test.

**Performance Goals**: End the job within 20 minutes. The test module already bounds each child process.

**Constraints**: Start only on filtered non-main pushes. Use read-only repository permission and checkout without persisted credentials. Cancel an older run for the same branch. Do not edit the existing timeout test, required CI workflow, dependencies, or repository settings.

**Scale/Scope**: One workflow, one contract test module in the existing timeout-budget test package, and the #4777 specification records.

## Constitution Check

- **Safety**: Pass. The run uses no Mist credentials, production data, live operations, services, or browser.
- **Permissions**: Pass. The workflow needs only `contents: read`, and checkout does not persist credentials.
- **Test integrity**: Pass. The workflow runs the existing full module with real subprocess behavior. It fails for missing count fields, zero tests, an unexpected count, skips, errors, or failures.
- **Change boundary**: Pass. The existing timeout test and its thresholds remain unchanged. No required check or repository setting changes.
- **Structure**: Pass. The feature uses the required eight-segment route for issue 4777. Each route parent has fewer than five children after allocation.
- **Existing folder debt**: `specs/` has 795 direct children. This record uses the required managed route and adds no direct child. Track any migration of existing direct records as separate work.
- **New code structure**: Pass. The contract test goes in the existing `tests/guardrails/e2e_timeout_budget/` package. No existing module or class changes.

## Design Decisions

- Use the action versions already used by `.github/workflows/windows-audit-report.yml`.
- Trigger only on non-main pushes that change the workflow, its contract test, the timeout-budget module, its shared E2E configuration, or dependency manifests.
- Store the test result as JUnit XML. Require recorded total, skipped, failed, and errored counts.
- Keep the acceptance run optional. A successful native push run, not a local test, is the acceptance evidence.
- Do not add a separate contract directory because this workflow has no public interface.

## Project Structure

```text
.github/workflows/windows-timeout-budget.yml
tests/guardrails/e2e_timeout_budget/
├── test_timeout_budget.py
└── test_windows_timeout_budget_workflow.py
specs/numbered/0/0/1/2/3/1/0/2/4777-windows-timeout-acceptance/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── checklists/requirements.md
    ├── data-model.md
    ├── quickstart.md
    └── research.md
changelog.d/issue-4777-windows-timeout-acceptance.md
```

**Structure Decision**: Reuse the existing guardrail test package and add one workflow. Keep supporting records under `design/`. The feature root has five children or fewer.

## Phase 0: Research

Review the native Windows audit workflow for action versions, checkout permissions, Python setup, platform checks, and JUnit parsing. Count the tests in the existing timeout-budget module. Confirm the managed route and preserve the current feature selector.

## Phase 1: Design

The workflow run records its branch, operating system, Python runtime, and test counts. It succeeds only when it confirms native Windows and Python 3.15, runs all seven tests, and reports zero skips, failures, or errors.

The workflow has no external application interface. The focused contract test reads the YAML workflow and proves that an invalid trigger or result policy fails the same contract decision.

## Validation Plan

- Run the workflow contract test on the development host.
- Run the full existing timeout-budget module on the development host.
- Run relevant lint and YAML validation gates.
- Keep native Windows acceptance unchecked until the coordinator authorizes a push and the workflow succeeds on Windows.
