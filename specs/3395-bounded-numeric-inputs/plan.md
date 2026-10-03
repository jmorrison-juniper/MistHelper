# Implementation Plan: Bounded numeric inputs

**Branch**: `jmorrison-juniper-bounded-numeric-inputs` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3395-bounded-numeric-inputs/spec.md`.

## Summary

Use one semantic class to validate ASCII whole number text before integer conversion.
Keep request access, field normalization, defaults, and refusal decisions in the existing callers.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing Flask, pytest, Hypothesis, and standard library modules.

**Storage**: None.

**Testing**: Real Flask requests, direct page limit reads, exhaustive cases, and Hypothesis properties.

**Target Platform**: Existing macOS, Windows, and Linux environments.

**Project Type**: Existing Python web application.

**Performance Goals**: Reject oversized text before conversion.
Convert at most the digits of each usable number bound.

**Constraints**: No network, production store, credential, firmware, container, or dependency changes.
No system integer limit changes.
No Unicode normalization.

**Scale/Scope**: Three existing readers, one shared class module, and two focused test modules.

## Constitution Check

The shared class enters `src/interfaces/portals/upgrade_portal/api/`, which currently has three direct children.
Its methods keep the existing parameter, block, and length limits.
The three large caller modules remain existing structural debt.
This repair changes only the affected reader blocks and their imports.
Future structural repairs belong to separate issues.

The existing test directories exceed the five-child limit.
The requested isolated test modules remain within this issue's explicit reservation.
Restructuring unrelated test trees would conflict with the assigned file ownership boundary.

Use standard field diagnostics without raw input or credentials.
Keep explicit capture refusal and existing organization authentication.
Add no pass-through wrapper, compatibility alias, suppression, or exclusion.

The app already owns the branch.
The legacy SpecKit branch hook requires raw checkout.
Use the current templates without running that hook or changing shared `.specify` files.
Keep all specification artifacts inside the reserved issue directory.
Do not create separate specification commits.

## Project Structure

### Documentation (this feature)

```text
specs/3395-bounded-numeric-inputs/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/input-readers.md
  tasks.md
  checklists/requirements.md
  analysis.md
```

### Source Code (repository root)

```text
src/interfaces/portals/upgrade_portal/api/numeric_input.py
src/interfaces/portals/upgrade_portal/app/routes/select.py
src/interfaces/portals/upgrade_portal/app/routes/capture.py
src/interfaces/portals/upgrade_portal/capture/clients.py
tests/unit/upgrade_portal/test_bounded_numeric_inputs.py
tests/contract/upgrade_portal/test_bounded_numeric_routes.py
changelog.d/issue-3395-bounded-numeric-inputs.md
```

**Structure Decision**: Add the class to the existing API package.
Do not edit the option mapper or a file owned by another repair.

## Complexity Tracking

| Existing constraint | Required scope | Separate remediation |
| - | - | - |
| Large route modules | Change only three reader blocks. | Plan a route split under another issue. |
| Large test directories | Keep focused, reserved test modules. | Plan a test package split under another issue. |

## Validation

Run regression cases before the repair.
Run focused tests with branch coverage after the repair.
Measure the changed methods separately from unrelated module code.
Run the current full Ruff and Black scopes, exact CI mypy scope, and Bandit scope.
Run the unchanged test quality baseline, citation checks, link checks, and configured STE heuristics.
Run the existing dependency audit without an ignore list.
Record the unavailable STE dictionary as partial grading, not a full writing pass.
