# Copilot handoff record

## Current run

- Pokémon identity: Lapras
- Issue: #2272 (compose rebuild overwrites the published tag)
- Ownership status: released
- Branch: `jmorrison-juniper-fix-2272-compose-rebuild`
- Worktree: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\copilot-worktrees\MistHelper\jmorrison-juniper-probable-guacamole`
- Coordination sub-issue: #2301
- Affected paths: `compose.yml`, `compose.build.yml`, `scripts/compose.ps1`, `documentation/container-deployment.md`, `tests/contract/packaging/test_compose_rebuild_warning.py`

## Completed work

- Moved the build section out of `compose.yml` into `compose.build.yml`, so a plain `up` can never build the image or overwrite the published tag.
- Added `build` and `check-revision` subcommands to `scripts/compose.ps1`.
- Updated the deployment guide with the build and revision-check recipes.
- Added three contract tests that hold the split in place.

## Verification results

- `python -m pytest tests/contract/packaging/test_compose_rebuild_warning.py`: 10 passed.
- `python -m ruff check`: all checks passed.
- `python -m black --check`: no changes needed.
- `python -m podman_compose -f compose.yml config`: parses, no build section.
- `python -m podman_compose -f compose.yml -f compose.build.yml config`: parses, build section present.
- PowerShell parser on `scripts/compose.ps1`: no syntax errors.

## Live API validation

Not required. No Mist API call runs in this change.

## Commit and push status

- Commit: `efa87fd`
- Push: pushed to `origin/jmorrison-juniper-fix-2272-compose-rebuild`.

## Remaining work

- None.

## Blockers

- None.

## Exact next action

A maintainer reviews and merges the branch. PR #2275 also touches `compose.yml`. It rebases cleanly onto this branch, because this change only removes the build section.
