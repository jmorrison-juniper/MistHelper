# Research: Bounded live timestamp records

## Evidence

The investigation used revision `66a72c877`.
Issue [#4263](https://github.com/jmorrison-juniper/MistHelper/issues/4263) reports the sixth-record failure in PR #4223.

The current live records are:

- `20261013-122636-mistcircuitstats-wan`
- `20261013-125122-mist-org-licensing-comparison`
- `20261013-182828-fix-generated-control-labels`
- `20261014-081459-backup-restoration`
- `20261014-204700-firmware-portal-remediation`

PR [#4223](https://github.com/jmorrison-juniper/MistHelper/pull/4223) owns `20261014-050510-mistcircuitstats-redis`.
PR #4226 owns a different numeric route.
PR #4208 owns WAN product files.
None owns this planning record's paths.
Recheck open paths before publication and before implementation.

## Decision 1: Fixed-width timestamp groups

**Decision**: Encode the timestamp's whole UTC epoch seconds as 17 base-5 digits.
Use those digits as structural directories below `specs/live/`.
Keep the full original timestamp feature name as the terminal record directory.
Interpret an existing timezone-free name as a UTC routing label only.
Do not claim that it identifies the original creation instant.

**Rationale**: Every structural branch has only digit children `0` through `4`.
The range `0 <= seconds < 5^17` includes valid dates from 1970 through 9999.
Validate the calendar date and exact timestamp format before conversion.
Reject earlier dates rather than assign an invented time.
The allocator rejects a sixth record in one second's terminal bucket before writing.
This finite limit is explicit and does not change the guard.

**Alternatives considered**:

- Direct year or month groups eventually exceed five children.
- Arbitrary named groups need a shared mutable index and allocation coordination.
- Feature nesting confuses ownership and is prohibited.
- A larger guard threshold does not solve bounded growth and is prohibited.
- Reusing the numeric route width limits timestamp coverage unnecessarily.

Use the existing `Get-SpecRadixSegments` width parameter instead of a second radix algorithm.
Keep its numeric default at eight.
Pin independent timestamp vectors in tests before implementation.

## Decision 2: Explicit selection, bounded discovery

**Decision**: Keep `SPECIFY_FEATURE_DIRECTORY` as the first selection source.
Use command scope during this planning request.
Do not persist into tracked `.specify/feature.json`.
Read-only commands must retain `-NoPersist` behavior.

**Rationale**: `Get-FeaturePathsEnv` already accepts nested explicit paths.
It currently persists an environment override unless a caller uses `-NoPersist`.
It also fixes optional design paths at the feature root.
The future process change must prevent cross-worktree selection changes and support the bounded design layout.

**Alternatives considered**: Branch-name inference and a committed global pointer can select another owner's feature.
Neither is acceptable.

Discovery identifies a record by its root `spec.md`, not by an arbitrary directory depth.
It must stop at that boundary and reject nested feature records.
Direct and grouped timestamp layouts coexist only during owner-approved migration.
New timestamp allocation uses grouped paths only.

## Decision 3: Preserve existing content and ownership

**Decision**: Move only approved records in a later implementation change.
Record each original file's relative name, byte count, and SHA-256 hash.
Record its owner, destination, and reference-update approval.
Maintain an exact file mapping and compare hashes after relocation.

**Rationale**: The issue requires preservation, not a rewrite of historical plans.
Reference-only edits require a separate before-and-after patch and owner approval.
Keep the original hash evidence even when an approved link update changes a file.
Never treat link normalization as proof that unrelated content stayed unchanged.

**Alternatives considered**: Copies produce duplicate feature identities.
Aliases and compatibility directories create extra children and conceal stale references.
Neither is part of the migration.

## Decision 4: Strengthen structural checks

**Decision**: Retain the existing root baseline and threshold.
Traverse every structural group and validate digit names, capacity, and record boundaries.
Report structural-directory and feature-record counts on success and failure.

**Rationale**: `validate_specs_structure` currently checks only direct managed-root capacity.
It does not prove that deeper groups obey the limit.
Existing feature artifact counts are separate historical debt, not structural-group exemptions.
New feature layouts, including this record, remain fully bounded.

**Alternatives considered**: Baseline growth, exclusions, skipped tests, and a raised threshold hide failures.
Do not use them.

## Decision 5: Update all process consumers

**Decision**: Include the canonical task-audit implementation and its pinned release in the future dependency sequence.

**Rationale**: Installed `misthelper_devtools/speckit_task_audit.py` scans `specs_dir.iterdir()`.
It reads `tasks.md` only from each direct child.
Its current clean result for a nested record would not prove task coverage.
A recursive feature-boundary fixture must prove both valid and failing grouped tasks.

Inspect skill and agent instructions, templates, generators, setup commands, context readers, CI inputs, and path-bearing documentation during implementation.
`AGENTS.md` has a canonical copy in `misthelper-devtools`.
Change that copy first if a generic writing or process rule needs revision.
No such instruction change belongs in this planning PR.

## Planning Workflow Decisions

Core templates apply because no override, preset, or extension template is installed.
The mandatory `before_specify` branch hook ran once with `--json --dry-run`.
It returned `3996-spec-live-root-capacity` as a proposed branch, not an artifact identity.
The app-managed branch remains `jmorrison-juniper-spec-live-root-capacity`.
Issue number 4263 determines this record's numeric route.
This is a deliberate branch-hook exception to avoid a second branch operation.

All enabled hooks after specification and around later phases are optional commit hooks.
Defer them until final validation, then commit explicit feature paths only.
Disabled companion hooks do not run.
No implementation hook runs.

PowerShell was absent during initial artifact generation.
Executable implementation tests later required the missing shell.
The session downloaded official PowerShell 7.6.7 and verified SHA-256 `50dde99bb066adacbb9a748182d09eb9beff25119dc3b12e85c84b6b6b1c5da9`.
The executable remains outside the repository in session artifacts.
Tests require its directory on PATH.

## Resolved Shared-Tool Blocker

The canonical task audit now discovers grouped feature records and stops at feature boundaries.
The owner merged the implementation in [jmorrison-juniper/misthelper-devtools#73](https://github.com/jmorrison-juniper/misthelper-devtools/pull/73).
The owner released v0.6.3 in [jmorrison-juniper/misthelper-devtools#74](https://github.com/jmorrison-juniper/misthelper-devtools/pull/74).
MistHelper pins release commit `e8e093d205428b5503887267b6a9751fa7354be7`.

The canonical task-audit test module passes 24 tests.
Its public-command fixture finds one open task in a grouped record and returns failure.
Its completed grouped fixture verifies the reported feature and task counts.

The repository-wide audit finds a separate tracked duplicate feature identity under `specs/189-quality-gate-remediation/`.
The audit exits 2 before it reports counts.
Issue [#4269](https://github.com/jmorrison-juniper/MistHelper/issues/4269) tracks owner review and the required structure resolution.
Do not move or remove either copy without its owner's approval.
