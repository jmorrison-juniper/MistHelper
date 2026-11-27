# Data Model: Early dependency check without half-removed packages

The early check keeps no database record. The entities below exist only during one start. The natural key of each entity comes from the source data.

## Package

- **Natural key**: The normalized package name. Lowercase the name, and replace each run of hyphens, underscores, and periods with one hyphen. The key matches the pin name in `requirements.txt`.
- **Attributes**: four values. The installed version comes from metadata, and it is empty when the package is missing. The pinned version comes from the lock reference. The RECORD state is complete or incomplete. The loaded state is true when a top-level name is in `sys.modules`.
- **Derived classification**: exactly one of missing, broken, loaded, off pin, latest only, or current. A broken package is classified before the loaded check. A missing package has no version, so it is never loaded.

### Package states

| From | Event | To | Record |
| - | - | - | - |
| Current | The pin changes on disk | Off pin | None |
| Missing | Install succeeds | Current | M-12 |
| Missing | Install fails | Missing | Existing error record, `Failed to install %s` (not changed) |
| Off pin | Loaded module found | Loaded (skipped) | M-03 |
| Off pin | RECORD incomplete | Broken (skipped) | M-04 |
| Off pin | Snapshot captured, upgrade succeeds | Current | M-05, M-08, M-09, existing success record |
| Off pin | Snapshot captured, upgrade fails, restore succeeds | Off pin | M-05, M-08, M-09, M-10 |
| Off pin | Snapshot captured, upgrade fails, restore fails | Broken | M-05, M-08, M-09, M-11 |
| Off pin | Snapshot cannot be captured | Off pin (skipped) | M-06 |
| Any drifted state | Drift count above five | Unchanged | M-02 |

## Drift set

- **Natural key**: none. The set exists only during one run.
- **Attributes**: the packages that are missing, broken, or off pin. A loaded package counts toward the set when it is off pin.
- **Rule**: a set with more than five packages refuses the run (FR-005).

## Snapshot

- **Natural key**: the normalized package name, and the start time of the run in UTC ISO 8601 form (for example `2026-11-26T17:00:00Z`).
- **Attributes**: the temporary folder path, the list of RECORD files captured, and the state.
- **States**: captured, then one of restored, discarded, or kept. A snapshot is discarded after a successful upgrade. A snapshot is kept when a restore fails, so the operator can repair the files.

## Lock reference entry

- **Natural key**: the normalized package name.
- **Attributes**: the pinned version from `requirements.txt`, and the locked version from `uv.lock` (checked by TC-13 at test time).
- **Relationship**: each Package has one lock reference entry.

## Relationships

- One Package has zero or one Snapshot for each in-process upgrade.
- One Drift set holds zero or more Packages. Each Package appears at most once in one set.
- One Lock reference entry matches one Package by natural key.
