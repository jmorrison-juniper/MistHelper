# Implementation Plan: Prevent Unsafe Stale Builds

**Branch**: `fix/4164-compose-stale-build` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4164 and the feature specification in this directory.

## Summary

The compose helper will fetch `origin/main` before a build and count commits that the checkout lacks. It will stop by default when the count is positive. An explicit `--allow-stale` option will permit the build and set its image name to `misthelper:local`. The normal build path will keep the published image name.

## Technical Context

**Language/Version**: PowerShell 5.1+ and Python 3.13+ for contract tests.

**Primary Dependencies**: Git, `podman-compose`, and pytest. The plan changes no dependencies.

**Storage**: Git references and a local container image tag. No application data changes.

**Testing**: `tests/contract/packaging/test_compose_rebuild_warning.py`, pytest, Ruff, and Black.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Operator command-line tooling for a Python application.

**Performance Goals**: Add only one remote fetch before a requested local image build.

**Constraints**: Preserve `$args` handling. Do not add a PowerShell `param` block. Do not start a container or publish an image during tests.

**Scale/Scope**: One PowerShell helper, one Compose build overlay, one contract test module, and operator documentation.

## Constitution Check

- **Safety**: A stale build stops before the provider starts unless the operator gives an explicit option.
- **Structure**: The new specification uses the fixed eight-level managed route. It adds no source package or module.
- **Process-folder debt**: Existing baseline entries remain governed by `tests/guardrails/process_folder_baseline.json`. This change adds only its managed specification record. Track baseline cleanup as a separate incremental task and do not change unrelated entries here.
- **Five-item rule**: This change adds no source hierarchy level or class. The existing process-folder baseline remains unchanged.
- **Comments and logging**: Add inline comments to each changed executable line. Report the fetch, stale decision, and build result to the operator.
- **Mist Cloud**: Not applicable. This change makes no Mist API request.
- **Deployment safety**: Do not build or publish a container during local validation. GitHub CI remains the publisher.
- **Git flow**: Keep the assigned `fix/4164-compose-stale-build` branch. Do not create or switch branches.
- **Plan setup limitation**: `pwsh` is not installed in this worktree environment. The PowerShell plan setup script cannot run here, so this plan uses the resolved feature path and checked-in template directly.

**Gate result**: Pass, with the local plan setup limitation recorded above.

## Design

1. In `scripts/compose.ps1`, recognize `--allow-stale` only for `build`.
2. Fetch `origin/main` with an explicit refspec, then read `HEAD..origin/main`.
3. Stop before the provider call when fetch fails or the checkout is behind without the override.
4. Set `MISTHELPER_BUILD_IMAGE` to the published name for a current checkout or `misthelper:local` for an allowed stale checkout. Restore the prior process value after the provider exits.
5. Give `compose.build.yml` a default published image name. Replace direct build examples with the helper command and explain the stale override.
6. Extend the contract tests to guard failure order, behind-count direction, flag handling, image selection, and documentation.

## Project Structure

### Documentation for this feature

```text
specs/numbered/0/0/1/1/3/1/2/4/4164-compose-stale-build/
├── checklists/requirements.md
├── design/
│   ├── contracts/compose-build.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── research.md
├── plan.md
├── spec.md
└── tasks.md
```

### Source and tests

```text
scripts/compose.ps1
compose.build.yml
tests/contract/packaging/test_compose_rebuild_warning.py
documentation/container-deployment.md
documentation/wiki/Container-Setup.md
changelog.d/issue-4164-compose-stale-build.md
```

**Structure Decision**: Keep the guard in the existing compose helper. Keep the image-name default in the existing build overlay. Extend the existing contract test module.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | The change adds no hierarchy, class, or compatibility layer. | Not applicable. |

## Existing Debt

The process-folder baseline contains existing entries that this change does not alter. Track baseline cleanup as a separate maintenance action after each route review.

The existing contract test module contains 12 test functions. This change updates existing tests and adds no module-level declaration. Track test grouping as a separate maintenance action.
