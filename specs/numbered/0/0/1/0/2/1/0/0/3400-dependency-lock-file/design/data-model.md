# Data Model: Tracked Dependency Lock File

This model names the entities that the install paths share. Each entity has one source, a natural key, and validation rules.

## Entities

| Entity | Source | Fields | Natural key | Validation rules |
|---|---|---|---|---|
| Declaration | `pyproject.toml` dependency tables | Normalized name, table, specifier, marker | Normalized name and table | Each runtime declaration keeps its floor and its upper bound. The declaration guard checks both. |
| Lock package | `uv.lock` `[[package]]` tables | Name, version, source, dependency list, sha256 values | Name, version, and source | The lock holds 197 tables on `main` (RC-05). The mistapi entry is version 0.64.1 (RC-03). |
| Export line | `requirements.txt` and `requirements-dev.txt` | Normalized name, pinned version, marker | Normalized name and marker | Each export line equals the lock output. Each header names the command (RC-16, RC-18). |
| uv pin | Four locations: `pyproject.toml`, `requirements-dev.txt`, the container build, and the bootstrap | Tool name, exact version, location | Tool name and location | All four locations hold `0.13.9`. The `required-version` range includes the pin. |
| Install path | Bootstrap, CI jobs, root images, ops containers, and Dependabot | Identifier, command, state | Identifier | The state is `pip-from-export`, `pip-from-declaration`, `locked-sync`, or `dependabot-export`. |
| Build context rule | `.dockerignore` | Pattern, action | Pattern | `uv.lock` must stay admitted after the exclusion at line 121. |

## Install path states

| Install path | Today | Target | Task |
|---|---|---|---|
| Worktree bootstrap | `locked-sync` (RC-30) | `locked-sync` with a pinned uv install | T011 |
| CI jobs | `pip-from-export` (RC-22) | `locked-sync` | T014 |
| Root image, `Dockerfile` | `pip-from-export` (RC-31) | `locked-sync` | T016 |
| Root image, `Containerfile` | `pip-from-export` (RC-32) | `locked-sync` | T016 |
| Ops container, `Containerfile.api` | `pip-from-declaration` (RC-37) | `locked-sync` | T019 |
| Ops container, `Containerfile.worker` | `pip-from-declaration` (RC-38) | `locked-sync` | T019 |
| Dependabot, root entry | Edits the export directly (RC-35, RC-59) | Edits the lock and declarations together | T023 |
| Dependabot, ops entry | Absent (RC-36) | Edits the ops lock and declarations together | T023 |

## State transitions

1. A declaration changes. The lock becomes stale, and `uv lock --check` fails.
2. A maintainer refreshes the lock with `uv lock`. The lock matches the declarations.
3. The exports become stale, and the export guard fails.
4. A maintainer regenerates the exports with the `uv export` commands in the contract. Both guards pass.
5. A Dependabot update changes the declaration and the lock together. The exports become stale.
6. A maintainer regenerates the exports. The guards pass again.
7. An install path moves from `pip-from-export` or `pip-from-declaration` to `locked-sync`, one slice at a time.

## Validation rules

- R1: `uv lock --check` exits with status 0.
- R2: Each export equals the output of its `uv export` command.
- R3: Each uv pin equals `0.13.9`.
- R4: `.dockerignore` admits `uv.lock`.
- R5: `pip-audit -r requirements.txt` reads the runtime export.
