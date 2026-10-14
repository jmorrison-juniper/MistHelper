# Implementation Plan: SSR lab runbook validation

**Branch**: `jmorrison-juniper-spec-3960-ssr-lab-handoff` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: `specs/numbered/0/0/1/1/1/3/2/0/3960-ssr-lab-handoff/spec.md`

## Summary

Prepare a human-executed validation plan for the six observations in issue #3960.
Do not collect physical results during this assignment.
Use the existing runbook as the future publication destination, not as measured evidence.

The design separates evidence collection, human review, and later runbook publication.
The [observation contract](design/contracts/lab-evidence.md) defines all six observations and their destinations.

## Technical Context

**Language/Version**: Markdown artifacts. Python 3.13 or later runs repository checks. PowerShell runs installed Spec Kit setup scripts.

**Primary Dependencies**: Existing Spec Kit templates, `misthelper-devtools`, and the source issue. No new runtime dependency.

**Storage**: Tracked artifact files only. Future raw lab evidence belongs in ignored `test-artifacts/issue-3960/`.
Only reviewed, sanitized excerpts may enter the runbook.

**Testing**: STE, local Markdown links, route guards, task-format checks, and requirement coverage.
Future human validation supplies the unit-level command observations, the portal integration observation, and the edge-case review.

**Target Platform**: Artifact tools support the repository development platforms.
Future lab targets need SSR 7.0.x and SSR 7.1.0-50r1 or later with a fiber port.

**Project Type**: Documentation validation handoff. No service, CLI feature, export, or transport implementation.

**Performance Goals**: No runtime performance change. Account for six observations and twelve functional requirements.

**Constraints**: No lab execution, cloud blocking, runbook edits, verifier edits, implementation, or pull request creation during this assignment.
Future cloud blocking requires explicit human approval and a verified independent recovery path.

**Scale/Scope**: Three user stories, six physical observations, one future runbook, and one future release fragment.

## Constitution Check

*Gate checked before research and after design.*

| Principle | Decision and evidence |
| --- | --- |
| I. Structure | Use the fixed eight-digit base-5 route for 3960: `0/0/1/1/1/3/2/0`. |
| I. Five children | Keep five feature-root children. Group four supporting records under `design/`. |
| I. Existing debt | Do not add a direct child under the existing noncompliant `specs/` root. Leave the baseline unchanged. |
| I. Incremental remediation | Maintain compliant feature directories and leave root migration to its separate owner. No unrelated restructuring belongs here. |
| II. Architecture | No executable code, class, wrapper, or compatibility path changes. |
| III. Safety | The human owns the cloud-loss experiment. Approval, console access, stop conditions, and recovery evidence precede acceptance. |
| IV. Deployment | Artifact preparation stops before implementation. No product code or release fragment changes in this assignment. |
| V-VII. Logging and comments | No executable code or operational logging changes. Future evidence excludes credentials and customer identifiers. |
| Mist transport | No REST or WebSocket client. A human observes the existing portal. No transport exception or SDK change. |
| Outputs | Future raw evidence stays in ignored `test-artifacts/issue-3960/`. No product output moves. |
| Ownership | The parent recorded the claim in #3959. Check overlap again before future runbook edits. |
| Publication | A future human-authorized change needs a unique fragment, a Conventional Commit, and the applicable repository pipeline. |

Pre-design result: pass for artifact-only scope.
Post-design result: pass. Hardware dependencies remain explicit and incomplete.
The plan does not authorize later implementation or suspend any deployment gate.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/1/3/2/0/3960-ssr-lab-handoff/
|-- spec.md
|-- plan.md
|-- tasks.md
|-- checklists/
|   `-- requirements.md
`-- design/
    |-- research.md
    |-- data-model.md
    |-- quickstart.md
    `-- contracts/
        `-- lab-evidence.md
```

**Structure Decision**: The feature root contains five children.
The design directory groups planning outputs to satisfy the constitution.
Setup scripts discover the three core artifacts normally.
Read supporting documents through the links below because setup scripts only discover conventional root-level design paths.
No script changes or compatibility copies are required.

### Source Code (repository root)

No source code changes.
Future publication targets are `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md`
and `changelog.d/issue-3960-ssr-lab-results.md`.
The protected file `scripts/verify_ssr_commands.py` remains excluded.

## Phase 0: Research

The [research record](design/research.md) resolves document ownership, current verification status, evidence authority, and safety boundaries.
No technical uncertainty permits a guessed console field or error string.
Unknown physical values remain evidence dependencies, not specification placeholders.

## Phase 1: Design and Contracts

The [data model](design/data-model.md) defines observation status and evidence acceptance.
The [observation contract](design/contracts/lab-evidence.md) maps the six issue tasks to exact commands and runbook destinations.
The [validation guide](design/quickstart.md) separates local artifact checks from the prohibited lab execution phase.

## Delivery Boundaries

The current deliverable is a specified, planned, task-listed, and analyzed feature.
All implementation tasks remain unchecked.
Lab access, approved releases, a fiber port, and human experiment authorization block physical validation.

A later owner must review all evidence before changing the runbook.
If an observation contradicts the source, preserve the measured difference and request review.
Do not broaden the change to the other runbooks from #3951 without a new ownership check.

## Complexity Tracking

No constitution exception is required.
The grouped design directory avoids new hierarchy violations.
No code, concurrency, schema, runtime dependency, or performance change is planned.
