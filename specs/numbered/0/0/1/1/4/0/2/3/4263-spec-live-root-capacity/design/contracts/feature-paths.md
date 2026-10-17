# Contract: Feature paths and command selection

## Allocation

New timestamp paths use `specs/live/<17-base-5-segments>/<timestamp-feature-name>`.
Numeric paths retain eight base-5 segments under `specs/numbered/`.
The timestamp conversion and supported range are defined in the [data model](../data-model.md).

Validate input, parent shape, destination absence, and terminal capacity before creating directories.
Reject a sixth terminal record and any feature parent.
Reject a malformed date or unsafe path.
Report the proposed destination and cause on failure.
Do not create a partial feature after failed validation.

## Selection

Use the explicit `SPECIFY_FEATURE_DIRECTORY` first.
Read-only prerequisite inspection must not persist that value.
The worktree selection must never change a second worktree's selection.

Return `FEATURE_DIR`, `FEATURE_SPEC`, `IMPL_PLAN`, and `TASKS` for exactly one feature.
Discover supporting artifacts at the established root or bounded `design/` location.
Return the actual paths, not assumed names or duplicated compatibility files.
Fail when both locations claim one artifact role.

## Consumers

Apply the same feature-boundary rule to prerequisite checks, plan setup, task setup, context readers, and task audit.
The task audit must discover numbered, direct timestamp, grouped timestamp, and grandfathered flat records.
It must not audit a structural group as a feature.
It must not descend into a feature looking for another feature.

Missing tasks for a task-ready record must remain an error.
Planning records with open implementation tasks remain open, not shipped.
Report examined records and task counts so zero coverage cannot appear successful.

## Required Contract Cases

| Case | Required result |
| --- | --- |
| Existing numeric route | Same directory and task identity |
| Direct timestamp record during migration | Same selected record |
| Grouped timestamp record | Correct root and supporting artifacts |
| Two worktrees with different explicit paths | Independent selection, no tracked pointer change |
| Invalid or absent record | Failure with cause and examined count |
| Duplicate identity or artifact role | Failure, no arbitrary first match |
| Feature nested beneath a feature | Failure |
| Sixth child at any structural depth | Failure with offending path and count |
| Sixth artifact child in a newly generated record | Failure before publication |
