# Implementation Plan: Code Defaults First Batch

**Branch**: `jmorrison-juniper-code-defaults-specification` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: `specs/numbered/0/0/0/4/2/0/0/3/2753-code-defaults-first-batch/spec.md`

## Summary

Validate confirmed required inputs in the five-file batch without changing permitted empty results or optional display values.
Deliver a committed candidate scanner and a baseline guard with observable failure behavior.
Reconcile the historical 59 candidates before accepting a current baseline.
Preserve the organization-migration repair from #4310.

This document authorizes no implementation or live operation.
The larger inventory, sibling scopes, and #2862 ownership remain excluded.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing mistapi and pytest dependencies. The scanner uses the Python standard library and Git only.

**Storage**: A tracked baseline document beside the scanner. Existing migration backups remain unchanged.

**Testing**: Existing eight unit modules, plus scanner unit, guardrail, and local workflow tests using controlled responses.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Existing command-line tool with internal audit tooling.

**Performance Goals**: One deterministic parse per selected tracked source file. No new concurrency, timing target, or live dependency.

**Constraints**: Five source files only, except the scanner/guard package and directly related tests.
No cloud request, device action, dependency change, transport change, menu change, or ownership reassignment.

**Scale/Scope**: Historical first-batch counts are 18, 17, 10, 9, and 5.
They are review targets, not accepted current baseline values.

## Constitution Check

*Before research and after design: the bounded design passes the applicable checks below. Implementation gates remain unexecuted.*

| Check | Decision and evidence |
| --- | --- |
| Managed process records | Use the existing numeric route. Feature root has four planned children, including `design/`. That directory has five. |
| New package capacity | Add `code_defaults/` under `src/foundation/support/`, which currently has three children. Add tests under `tests/integration/helpers/`, which has one. |
| Existing structural debt | Edit existing modules only. Do not add children to their overfull parents or add module-level helpers to overfull modules. |
| Functions and classes | New code uses typed classes, at most five parameters and logical blocks, and functions no longer than 25 lines. |
| Safety | Use controlled responses. Preserve typed migration confirmations, backup verification, and the existing failed-row contract. |
| Observability | Log meaningful actions before and after them. Report errors explicitly. Do not include secrets or private payloads. |
| Input contracts | Validate before dependent use. Preserve valid optional absence and explicit empty collections. |
| Cloud transport | No new transport or endpoint. Existing SDK calls remain unchanged. Verification replaces external calls. |
| Output locations | Runtime product outputs remain under `data/`. Tests use `tmp_path`. Audit output goes to standard output, not a new product store. |
| Tests and gates | Use [design/quickstart.md](design/quickstart.md). Prove that the guard fails. Do not modify quality baselines to conceal findings. |
| Git lifecycle | A later implementation requires a Conventional Commit and applicable repository review rules. This planning task creates no commit or pull request. |

### Existing Debt and Incremental Action

Measured direct children: device package 15, analytics 7, inventory 8, support utils 19, and organization resources 5.
The shared `scripts/` and `tests/guardrails/` folders have 51 and 65 children.
Do not add the scanner or its tests to those overfull folders.

The five modules have 24, 85, 9, 33, and 2 top-level declarations respectively.
The AP migration module has 24 functions above 25 lines. Address utilities have two.
These are raw source measurements, not a claim that the repository structural gate failed.

For each touched block, record its limits before editing and reduce its local excess where extraction is required.
Keep extraction inside existing classes or the new compliant package. Do not move unrelated modules or change public names.
Record remaining unrelated debt for a separate future change without assigning another issue's ownership.

## Project Structure

### Documentation (this feature)

```text
2753-code-defaults-first-batch/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/requirements.md
    research.md
    data-model.md
    quickstart.md
    contracts/audit.md
```

### Source Code (repository root)

Keep the five existing source paths and eight existing test paths listed in [spec.md](spec.md).
Add only the following bounded scanner and verification package:

```text
src/foundation/support/code_defaults/
  __init__.py
  __main__.py
  inventory.py
  policy.py
  baseline.json
tests/integration/helpers/code_defaults/
  __init__.py
  test_inventory.py
  test_guardrail.py
  test_workflows.py
```

**Structure Decision**: Keep repairs in their current classes and modules.
Place the independent scanner in the compliant support parent instead of adding another script.
The regression test is a guardrail by behavior. Its collection path avoids increasing the overfull `tests/guardrails/` folder.
No compatibility module or alias is introduced.

## Execution Boundaries

1. Establish scanner fixtures and reconcile the historical manifest against the current revision.
2. Repair AP profile migration first, then zone analysis, CSV comparison, address validation, and organization migration.
3. Complete each file's missing-input, valid-input, and optional-input evidence before proceeding to the next file.
4. Verify cross-file workflows and scan/guard evidence, then accept only the reduced or unchanged reviewed baseline.
5. Run the documented gates and produce a bounded completion report. Do not claim that issue #2753 is complete.

The accepted baseline records stable candidate identities, not just an aggregate count.
A removed candidate cannot offset a new high-severity candidate.
Excluded ownership and display-only candidates cannot increase or decrease the accepted first-batch total.

## Complexity Tracking

No new exception is requested.
Existing debt is recorded above. New modules and directories must satisfy the structural limits.
If a repair cannot meet those limits without expanding scope, stop that repair and report the exact conflict.
