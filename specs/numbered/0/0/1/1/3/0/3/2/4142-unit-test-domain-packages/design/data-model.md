# Data Model: Unit test domain packages

This feature has no database. Its data is the repository tree and the holds on that tree. The entities below use repository paths and identifiers as natural keys.

## Entities

| Entity | Natural key | Attributes | Relationships |
| - | - | - | - |
| Test package | Repository path, for example `tests/unit/juniper_docs` | Source status on `main`, file count, direct child count, hold ID, batch, destination path | Belongs to one source container or to the root. Moves to one destination grouping directory. |
| Grouping directory | Destination path, for example `tests/unit/marvis/mist/realtime/websocket` | Parent path, direct child count, package marker present (yes or no) | Lies under one container. Holds one or more test packages or modules. |
| Container | One of `config`, `marvis`, `maps`, `prod_readiness` | Child count, domain group names | Lies directly under `tests/unit/`. |
| Hold | Hold ID, for example `H-1` | Type (pull request, exact claim, planned edit, or conservative), owner number, paths, state, release condition | Blocks one or more test packages until its state becomes released. |
| Batch | Batch letter, for example `A` | Task IDs, pull request number, moved paths, verification result | Carries test packages. Runs after its holds clear. |
| Reference | Repository path and line number | Old path, new path, class (active, historical, production comment, or other project), task ID | Points to one test package. |
| Remote check | Check ID, for example `RC-01` | Path, ref, blob or tree SHA, result, line | Supports one claim in `research.md`. |

## Natural Key Rules

- A test package has one source path and one destination path.
- A destination path holds at most one source path for each file name.
- A grouping directory holds five children or fewer, including package markers.
- The final `tests/unit/` directory holds `__init__.py` and the four containers.

## State Transitions

Test package: `source` moves to `held` when a hold applies. `held` moves to `released` when the owner releases the hold. `released` moves to `moved` when a batch moves the path. `moved` moves to `verified` when collection parity passes. A rollback moves `moved` back to `source` by reverting the batch commit.

Hold: `active` moves to `released` when the owner posts a release comment or the pull request merges. A released hold does not return to `active`. A new hold needs a new record.

Batch: `open` moves to `in-progress` when the first move starts. `in-progress` moves to `merged` when the pull request squash-merges. `merged` moves to `verified` when T072 passes on `main`.
