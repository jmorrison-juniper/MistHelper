# Implementation Plan: Bounded live timestamp records

**Branch**: `jmorrison-juniper-spec-live-root-capacity` | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/1/4/0/2/3/4263-spec-live-root-capacity/spec.md`.

## Summary

Use fixed-width base-5 groups for timestamp records below `specs/live/`.
Preserve record names, content, and ownership.
Prepare discovery and guard changes before any approved relocation.
The initial phase delivers planning.
Subsequent authorization permits safe process implementation and the single #4202 move.
The shared-tool release and Redis owner action remain separate prerequisites.
Issue #4263 remains open.

## Technical Context

**Language/Version**: PowerShell process scripts, Python 3.13 tests, and Markdown records.

**Primary Dependencies**: Existing Spec Kit scripts and pinned `misthelper-devtools`.
No new runtime dependency is proposed.

**Storage**: Tracked planning files and command-scoped feature selection.

**Testing**: Process-folder tests, route tests, isolated command fixtures, task-audit fixtures, link checks, and STE checks.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Repository process change, not a product feature.

**Performance Goals**: Visit each structural directory once.
Stop record discovery at the feature boundary.

**Constraints**: Five children per new directory, no feature nesting, no guard suppression, and no owner changes.

**Scale/Scope**: Five current live records and one pending Redis record.
The numeric root and grandfathered flat entries retain their present routing.

## Constitution Check

| Gate | Before research | After design |
| --- | --- | --- |
| Managed numeric intake | Pass: prescribed eight-level route for 4263 | Pass: `0/0/1/1/4/0/2/3` |
| New directory capacity | Pass: bounded record layout | Pass: five root children and five design children |
| Existing record ownership | Pass: read-only investigation | Pass: future moves require owner handover |
| Guard integrity | Pass: no edits | Pass: recursive structural checks retain threshold five |
| Feature selection | Pass: explicit command scope | Pass: tracked `.specify/feature.json` remains unchanged |
| Safety and product scope | Pass: no production action | Pass: no product, container, or Mist API change |
| Commit and PR form | Required at publication | `fix(spec): bound live timestamp record groups` |

The current `specs/` root has 792 grandfathered legacy children.
At intake, the live root had five direct records and no spare child.
Some established feature directories exceed five artifact children.
This issue does not increase that historical debt or use it to permit new excess.
Future inventory must record those exact counts and separate their remediation from structural grouping.

The guard currently checks only managed-root children.
Its future extension must examine every structural group, including numbered levels, without treating feature artifacts as child features.
Existing feature artifacts remain unchanged during relocation.
New feature artifact layouts must satisfy five children at every level.
This distinction preserves existing records without hiding structural violations.

## Project Structure

### Documentation (this feature)

```text
4263-spec-live-root-capacity/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      feature-paths.md
      migration.md
    checklists/
      requirements.md
```

**Structure Decision**: Keep primary command inputs at the root.
Place supporting design records below `design/` to avoid a sixth child.
The plan links all supporting records explicitly because current helpers expect optional design files at the root.
Future helpers must discover both established and bounded layouts, without duplicating files.

### Implementation Surfaces

| Surface | Planned responsibility |
| --- | --- |
| `.specify/scripts/powershell/spec-route.ps1` | Validate timestamp names and calculate the bounded route |
| `.specify/scripts/powershell/create-new-feature.ps1` | Allocate only a validated destination |
| `.specify/scripts/powershell/common.ps1` | Select explicit feature directories and bounded design artifacts |
| `.specify/scripts/powershell/check-prerequisites.ps1` | Report grouped feature inputs and missing records |
| `.specify/scripts/powershell/setup-plan.ps1` and `setup-tasks.ps1` | Use selected inputs without changing another worktree's pointer |
| `.specify/scripts/powershell/update-agent-context.ps1` | Read design context from the selected feature |
| `tests/guardrails/test_process_folder_structure.py` | Validate every structural group and report counts |
| `tests/guardrails/test_spec_route_contract.py` | Pin timestamp routes and unchanged numeric routes |
| `tests/guardrails/test_spec_route_contract.py` | Isolated selection, setup, context, and persistence fixtures |
| Shared `misthelper-devtools` task audit | Discover actual feature records recursively |

Plan and task templates now describe the bounded artifact layout.
The specify skill and agent require grouped timestamp routes.
The plan and tasks skill-agent pairs require the actual returned design paths.
The repository instructions describe the same routing and selection contract.
These paired changes prevent generated artifacts from using obsolete root-only examples.

Shared tool implementation belongs in its canonical repository.
Do not edit installed packages or add a local replacement.
Its reviewed release and pin update must precede reliance on recursive audit coverage.

## Delivery Sequence

1. Inventory records, references, artifact counts, and owners without moving files.
2. Add failing route, structural, discovery, and preservation tests in isolated trees.
3. Implement routing, read-only discovery, and the stronger guard. Publish the canonical task-audit update.
4. Obtain owner handovers, then relocate approved records with preservation evidence and reference updates.
5. Verify the process fix, then let the Redis PR owner rebase and validate its grouped record.

Stop if an affected owner has not approved a handover.
Do not copy another PR's record into this branch.
Do not merge PR #4223 before its rebased checks pass.

## Design Outputs

- [Research](design/research.md) records evidence and route decisions.
- [Data model](design/data-model.md) defines record and manifest fields.
- [Feature paths](design/contracts/feature-paths.md) defines selection and allocation.
- [Migration](design/contracts/migration.md) defines preservation and coordination.
- [Quickstart](design/quickstart.md) gives planning and future implementation checks.
- [Tasks](tasks.md) defines serial execution after separate implementation authorization.

## Complexity Tracking

No new structural exception is requested.
Supporting records use nested directories instead of a larger feature root.
PowerShell was initially absent.
The session later downloaded official PowerShell 7.6.7 and verified its published SHA-256 digest.
Executable route and selection tests now run through its session-local PATH.
The tracked selector remains unchanged.
The default persistence API remains available, while read-only command callers use `-NoPersist`.

## Verified Implementation Boundary

The safe implementation covers timestamp routing, allocation preflight, structural traversal, and explicit selected-feature paths.
Executable numeric vectors exposed a boxed nullable-number defect in the existing resolver.
The resolver now passes the numeric value directly and preserves the prescribed eight-digit route.
Focused tests verify both route kinds and intentional selector persistence.

The public task-audit CLI cannot accept an explicit nested feature path.
Its `--root` option still appends `specs/` and scans direct children.
The verified upstream blocker is [jmorrison-juniper/misthelper-devtools#72](https://github.com/jmorrison-juniper/misthelper-devtools/issues/72).
No installed package was changed.

The coordinator subsequently relayed user authorization for the single merged #4202 record move.
The [migration contract](design/contracts/migration.md) records its verified nine-file map and two reference-only edits.
The live root now has four direct records and one group.
No other record or PR #4223 file changed.
PR #4223 remains blocked pending its owner's separate rebase and path update.
