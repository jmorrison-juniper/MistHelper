# Data Model: Feature structure and migration evidence

## Feature Record

| Field | Meaning and validation |
| --- | --- |
| Identity | Original feature directory basename, unique across discovery |
| Owner | Issue and active PR owner, confirmed before relocation |
| Directory | Explicit repository-relative directory below an approved managed root |
| Kind | Numeric or timestamp |
| Artifacts | Exact inventory of original files, with no invented replacement |

The feature root contains `spec.md`, `plan.md`, and `tasks.md` when those phases exist.
Optional design artifacts can use established root paths or the bounded `design/` layout.
If both layouts contain the same artifact role, selection fails rather than choosing silently.
A feature cannot contain another feature.

## Timestamp Group Route

| Field | Meaning and validation |
| --- | --- |
| Timestamp label | Exact `YYYYMMDD-HHMMSS` prefix with a valid calendar date |
| Routing instant | Label interpreted as UTC for deterministic allocation only |
| Epoch seconds | Integer from zero through `5^17 - 1`, subject to supported calendar limits |
| Segments | Exactly 17 digits, each between zero and four |
| Destination | `specs/live/<segments>/<original-feature-name>` |

A terminal bucket contains at most five feature directories.
Intermediate groups contain only digit groups.
Do not mix records and groups in a new route.
Reject symlinks, traversal, duplicate names, and occupied destinations.

## Migration Manifest

| Field | Meaning and validation |
| --- | --- |
| Source and destination | Unique normalized relative paths within this repository |
| Owner approval | Issue or PR handover reference and approved scope |
| Original file inventory | Relative name, byte count, and SHA-256 hash for every file |
| Reference inventory | Each selector, link, command, or document affected by the move |
| Approved reference patch | Exact permitted content changes, separate from relocation |
| Verification | File mapping, hashes, reference results, and structural counts |
| State | Proposed, approved, moved, verified, or blocked |

State advances only after its evidence exists.
An error sets the affected entry to blocked and stops further moves.
The manifest must preserve the original source evidence.
Do not remove the source until the destination verification succeeds.
Use a checked temporary destination during the move.
Do not publish both source and destination as feature records.

## Feature Selection

Selection belongs to a command or isolated worktree.
An explicit directory overrides persisted state.
Read-only commands do not write selection state.
Missing inputs, conflicting layouts, and multiple identity matches are errors.
Errors name the selected path and examined counts without printing credentials.
