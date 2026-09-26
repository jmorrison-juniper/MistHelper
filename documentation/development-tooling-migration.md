# Development tooling migration

MistHelper carried its own development tooling for a long time. That tooling
served the engineers who build MistHelper. A customer never runs it.

Issue #3404 moves the tooling into a separate repository and stops shipping it
inside the MistHelper wheel and the MistHelper container image.

The new repository is `jmorrison-juniper/misthelper-devtools`.

## What the tooling holds

| Tree | Holds |
| - | - |
| `tools/` | The repository linters, the analyzers, the compliance checkers, and the symbol difference tool. |
| `scripts/` | The maintenance commands, the bootstrap helpers, and the report generators. |
| `tests/` | The MistHelper test suite. |
| `specs/` | The SpecKit records. |

## Phase 1: stop shipping the tooling

Phase 1 is complete. It changed what the build produces. It deleted no file
from this repository, so every local command still works.

| Change | File |
| - | - |
| The wheel no longer packages `tools/`. | `pyproject.toml` |
| The wheel no longer exposes the `test-quality-analyzer` and the `ste-linter` commands. | `pyproject.toml` |
| The container image no longer copies `scripts/`. | `Dockerfile` and `Containerfile` |
| The build context excludes `tools/` and `scripts/`. | `.dockerignore` |
| A guard keeps the tooling out of both artifacts. | `tests/guardrails/test_shipped_artifacts.py` |

Phase 1 also moved one file. `scripts/build_zen_city_metadata.py` held the
hand-curated Zscaler city map, and `src/utils/zscaler_catalogue.py` read that
map at run time. The map is product code, so it moved to
`src/utils/zen_city_metadata.py`. The maintenance command stays in `scripts/`
and it imports the new module. `src/utils/zscaler_probe.py` was promoted the
same way in an earlier change.

Warning: a product module must never import from `scripts/` or from `tools/`.
The container no longer ships either tree, so such an import breaks the image
at start time. The guard test reports that class of defect.

Caution: `Containerfile` and `Dockerfile` must stay byte-identical. Podman reads
`Containerfile` first, so an edit to `Dockerfile` alone leaves the local build
on the old recipe. Edit `Containerfile`, then run
`Copy-Item Containerfile Dockerfile -Force`.
`tests/unit/container/test_build_files_match.py` enforces the rule.

## Phase 2: delete the local copy

Phase 2 is complete. The devtools repository defines an installable Hatch wheel
and MistHelper pins its exact public Git commit in `requirements-dev.txt`, so CI
does not need a package-index credential and a later devtools commit cannot
change a build unexpectedly.

The migration changed the development environment only. Product imports and
runtime commands remain in MistHelper; CI, pre-commit, and development scripts
use the installed devtools package.

1. Make `misthelper-devtools` installable from a pinned commit — complete.
2. Add `misthelper-devtools` to the MistHelper development requirements — complete.
3. Point CI workflow steps at the installed package instead of local tool paths — complete.
4. Point `.pre-commit-config.yaml` at the installed commands — complete.
5. Update the subprocess-timeout tests to use the installed tool package — complete.
6. Delete `tools/` from this repository after verifying its consumers — complete.
7. Move the Juniper skill factory source, scripts, and tests to
   `misthelper-devtools`. Repository searches found no product imports, and
   the development-tooling repository contains the factory — complete.
8. Move the `[tool.ste_linter]` settings out of `pyproject.toml` — complete;
   `.ste-linter.toml` retains the same table and the workflows name it explicitly.

Validation after the move: the focused integration and guard suite passes
(136 tests), Ruff passes for the changed Python files, the citation linter
checks 249 citations with no unresolved references, and a rebuilt wheel has no
`tools/` or `src/juniper_skills/` entries.
