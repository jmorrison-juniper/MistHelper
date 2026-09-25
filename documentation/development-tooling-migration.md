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
| The container image no longer copies `scripts/`. | `Dockerfile` |
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

## Phase 2: delete the local copy

Phase 2 is not started. Do not start it until the devtools repository
publishes a package that MistHelper CI can install.

Complete these steps in order.

1. Publish `misthelper-devtools` to a package index that CI can reach.
2. Add `misthelper-devtools` to the MistHelper development requirements.
3. Point every workflow step at the installed commands instead of the local
   paths. Read `.github/workflows/ci.yml` for the current set.
4. Point `.pre-commit-config.yaml` at the installed commands.
5. Update `tests/unit/prod_readiness/test_subprocess_timeouts.py`. That test
   imports `tools.symbol_diff` and `tools.compliance_analyzer`.
6. Delete `tools/` from this repository.
7. Decide where `src/juniper_skills/`, `scripts/juniper_skills/`, and
   `tests/unit/juniper_skills/` belong. Phase 1 left all three in place.
8. Move the `[tool.ste_linter]` table out of `pyproject.toml`. The linter that
   reads it now lives in the devtools repository. The table names
   `data/ste_dictionary.json`, and git does not track that file today.

Caution: step 6 removes the local copy of every tool. If CI still names a
local path at that point, every gate that reads the path fails at once. Verify
step 3 and step 4 on a branch before you delete the tree.
