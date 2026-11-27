# Implementation Plan: Tracked Dependency Lock File

**Branch**: `docs/3400-dependency-lock-file` (this record) | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/spec.md`

**Input**: Numeric record. Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Track `uv.lock`. Keep `pyproject.toml` as the only source of declarations. Generate exports for pip users. Install each managed path from the lock. The lock, both exports, the bootstrap, and the CI lock gate already exist on `main` (RC-01 to RC-06, RC-16 to RC-21, RC-30). The remaining slices change the CI install path, the image install path, the ops lock, Dependabot, the uv pin, and the documentation.

## Technical Context

- **Language/Version**: Python 3.15 (`pyproject.toml` line 23, RC-10).
- **Primary Dependencies**: uv 0.13.9 (`pyproject.toml` line 101, RC-14, and `requirements-dev.txt` line 470, RC-19). mistapi 0.64.1 from the lock (RC-03). misthelper-devtools at commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (RC-04, RC-13).
- **Storage**: N/A. The record changes no data store.
- **Testing**: pytest guard cases in `tests/guardrails/` and `tests/unit/`. Implementers run them per slice. This authoring step runs none.
- **Target Platform**: Windows 11, macOS, and Linux worktrees. A Linux container image. GitHub-hosted `ubuntu-latest` CI (RC-24).
- **Project Type**: Repository tooling, CI workflows, container build files, and dependency metadata.
- **Performance Goals**: N/A. The record sets no runtime target.
- **Constraints**: No package version changes in any slice. Each slice runs its gates before push. Slices 2 to 5 need user approval before publication (U-G).
- **Scale/Scope**: 197 lock packages (RC-05). 108 exact runtime pins (RC-17). One registry source for registry packages (RC-03 shows it).

## Constitution Check

| Rule | Result | Reason |
|---|---|---|
| I. Five-Item Rule | Fail, justified in Complexity Tracking | `mist-ops-platform/uv.lock` adds a direct child to a folder that holds 11 children (RC-52). Other changes add no direct child to a noncompliant parent. The `.github` folder keeps its 14 children (RC-51). Guard cases extend existing files. Changelog fragments are unique records that `changelog.d/` allows. |
| II. Class-Based Architecture | Pass | No production wrapper function is added. Guard cases are pytest functions in existing modules. |
| III. Safety-First | Pass | No destructive operation changes. The image change adds no secret. The default SSH password in the Dockerfile stays unchanged. |
| IV. Full Deployment Pipeline | Pass by plan | Each slice runs local gates, opens a pull request, passes CI, and merges by squash after approval. No slice pushes to `main`. |
| V. Observability and Logging | Pass | New messages and log lines use ASCII only. |
| VI. Inline Comments | Pass, with a condition | Each new code line in the bootstrap and in guard cases carries an inline comment. |
| VII. Action Logging | Pass, with a condition | Each new bootstrap action logs before and after it. Guard cases read files and start no action. |
| Python 3.15 | Pass | RC-10 and RC-46 state the floor. |
| mistapi | Not applicable | This record calls no Mist REST method and no SDK function. |
| uv preferred, requirements.txt for pip | Pass | RC-47 and decision D-1. |
| Podman | Pass | Both `Containerfile` and `Dockerfile` change. RC-27 shows that the build reads `Containerfile`. |
| Test containers | Not applicable | This record starts no test container. A slice that starts one joins the compose group. |
| File paths | Pass | Bootstrap changes use the existing path helpers. |
| Data directory and output backends | Not applicable | No product output changes. |
| Container security | Pass, with a condition | UID 1000 must read `/opt/misthelper-venv` (U-K). Task T016 checks it. |
| Zscaler and proxy | Pass | This record builds no image. Image builds run in GitHub Actions. |
| Security findings | Pass | No suppression comment is added. The audit stays on the runtime export (D-2). |
| SpecKit escalation | Pass | This record is the required spec. The change touches more than three files. |
| Documentation | Pass | Task T022 corrects stale lines (RC-40, RC-42, RC-43, RC-44). |
| Multi-agent git | Pass | Branch names use the `docs` and `chore` types with the issue number. The title uses a Conventional Commits form. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      lock-install-contract.md
    checklists/
      requirements.md
```

### Source Code (repository root)

The file-by-file change map below lists each source path that the slices change.

## Architecture

```text
pyproject.toml                  declarations, uv pin (line 101), required-version (new)
        |
        v
uv.lock                         one lock for every platform
        |
        +--> requirements.txt, requirements-dev.txt   exports: uv export --locked --no-hashes --no-emit-project
        |
        +--> bootstrap           uv sync --locked --extra dev
        +--> CI jobs             uv sync --locked --extra dev --no-install-project, then .venv/bin on GITHUB_PATH
        +--> root image          uv sync --locked --no-install-project into /opt/misthelper-venv
        +--> ops containers      uv sync from mist-ops-platform/uv.lock (new lock)
        +--> pip users           requirements.txt, requirements-dev.txt
        +--> Dependabot          uv ecosystem for / and /mist-ops-platform
```

## Slices

| Slice | Tasks | Depends on | Sensitive | Auto-merge |
|---|---|---|---|---|
| R. Record | T001, then the final tasks | none | no | after gates, CI, and the orchestrator's authorization |
| 1. Guards and pins | T009 to T012 | R | no | yes, after gates and CI |
| 2. CI installs | T013, T014 | 1 | yes | no |
| 3. Images | T015 to T017 | 1 | yes | no |
| 4. Ops lock | T018 to T020 | 1 | yes | no |
| 5. Dependabot and documentation | T021 to T023 | 4 | yes | no |

Sensitive slices change how contributors or images install packages. A human reviews each sensitive slice. Slices 1 to 5 change the same guard file, so they merge in order. Slices 2 to 5 need user approval before push, pull request creation, or merge (U-G).

## File-by-file change map

| Path | Action | Task | Notes |
|---|---|---|---|
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/spec.md` | Modify | T001 | Replaces the legacy spec |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/plan.md` | Modify | T001 | Replaces the legacy plan |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/tasks.md` | Modify | T001 | Replaces the legacy tasks |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/analysis.md` | Add | T001 | Consistency review |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/research.md` | Add | T001 | Decisions, remote checks, legacy check |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/data-model.md` | Add | T001 | Entities and transitions |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/quickstart.md` | Add | T001 | Reproduction and commands |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/contracts/lock-install-contract.md` | Add | T001 | Command contract |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/checklists/requirements.md` | Add | T001 | Specification quality checklist |
| `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/lock-comparison.md` | Delete | T001 | Facts move to research.md (D-9) |
| `pyproject.toml` | Modify | T010 | Add `[tool.uv]` with `required-version` |
| `scripts/bootstrap_worktree.py` | Modify | T011 | Pin `uv==0.13.9` in `install_uv` |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Modify | T011 | Case c3 |
| `changelog.d/issue-3400-uv-pin.md` | Add | T011 | One fragment for slice 1 |
| `tests/guardrails/test_dependency_lock_file.py` | Modify | T009, T010, T012, T018, T019, T021, T022 | Cases c1, c2, c4, c11, c12, c14, c15 |
| `tests/guardrails/test_dependency_lock_workflow.py` | Modify | T013, T023 | Cases c5, c6, c16 |
| `tests/guardrails/test_container_build_trigger.py` | Modify | T015, T017 | Cases c7, c8, c9, c10 |
| `tests/guardrails/test_dependency_export.py` | Modify | T020, T023 | Cases c13, c17 |
| `.github/workflows/ci.yml` | Modify | T014, T019 | Locked installs and the ops job lock |
| `changelog.d/issue-3400-ci-locked-sync.md` | Add | T014 | One fragment for slice 2 |
| `.github/workflows/container-build.yml` | Modify | T017 | Freeze comparison step |
| `Dockerfile` | Modify | T016 | Locked venv install |
| `Containerfile` | Modify | T016 | Same change as `Dockerfile` |
| `.dockerignore` | Modify | T016 | Add `!uv.lock` after line 121 |
| `changelog.d/issue-3400-image-locked-sync.md` | Add | T016 | One fragment for slice 3 |
| `mist-ops-platform/uv.lock` | Add | T018 | Ops lock |
| `mist-ops-platform/pyproject.toml` | Modify | T018 | Only if the lock check reports drift |
| `mist-ops-platform/deploy/Containerfile.api` | Modify | T019 | Install from the ops lock |
| `mist-ops-platform/deploy/Containerfile.worker` | Modify | T019 | Install from the ops lock |
| `changelog.d/issue-3400-ops-lock.md` | Add | T019 | One fragment for slice 4 |
| `mist-ops-platform/requirements.txt` | Modify | T020 | Export of the ops lock |
| `documentation/development-setup.md` | Modify | T021, T022 | Locked bootstrap and regeneration command |
| `documentation/quality-gates.md` | Modify | T021 | Audit reads the runtime export |
| `documentation/container-deployment.md` | Modify | T022 | Trigger list |
| `.github/copilot-instructions.md` | Modify | T022 | mistapi floor |
| `.github/dependabot.yml` | Modify | T023 | `uv` entries |
| `changelog.d/issue-3400-dependabot-uv.md` | Add | T023 | One fragment for slice 5 |

## Dependencies

| Dependency | Version or value | Source |
|---|---|---|
| uv | 0.13.9 | `pyproject.toml` line 101 (RC-14), `requirements-dev.txt` line 470 (RC-19) |
| mistapi | 0.64.1 | `uv.lock` line 1419 (RC-03), `requirements.txt` line 129 (RC-17) |
| misthelper-devtools | commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` | `pyproject.toml` line 123 (RC-13), `uv.lock` line 1586 (RC-04) |
| Python | 3.15 | `pyproject.toml` line 23 (RC-10) |
| Base image | `python:3.15-slim` | `Dockerfile` line 22 (RC-33), mutable (D-8) |
| CI runner | `ubuntu-latest` | `.github/workflows/ci.yml` line 636 (RC-24) |

## Risks and mitigations

| Risk | Effect | Mitigation |
|---|---|---|
| A PATH step in CI fails | Caution: each affected job fails, and the aggregator reports a failure. | One slice. Cases c5 and c6. Pull request CI before merge. Revert with a new pull request. |
| uv version drift | A lock format or resolution changes on one machine. | `required-version` (T010). Pin guard (T012). |
| `.dockerignore` excludes the lock | The image build fails at `COPY`. | T016 adds `!uv.lock` after line 121. Case c9. |
| The venv is unreadable by UID 1000 | The container fails to start. | T016 acceptance. Unverified item U-K. |
| Warning: a wrong image package set reaches users. | Users run the wrong versions. A pushed tag can reach users before a check. | Freeze comparison (T017). Dispatch only after user approval. |
| Dependabot edits an export | The export guard fails, as pull request #4888 shows (RC-59). | T023 `uv` entries. The guard names the regeneration command (c17). |
| The ops lock adds a child to a noncompliant folder | A Principle I exception. | Complexity Tracking. Follow-up F-2. |
| Overlap with open Dependabot ops pull requests | A merge conflict in `mist-ops-platform/requirements.txt`. | T020 waits for pull requests #4889 and #4890 (R2). |
| The publication hold applies | A slice ships without approval. | Slices 2 to 5 need user approval before publication (U-G). |
| Unrelated local edits | A commit includes changes outside the slice. | Each slice starts from `main`. Stage named files only. The six files in research R6 differ only in line endings. |
| The base image tag is mutable | Packages differ on rebuild. | Out of scope (D-8). Follow-up F-3. |
| Exports carry no hashes | pip installs do not check artifact hashes. | Images use the lock (D-4). Follow-up F-4. |

## Rollback

1. Revert a slice with a new pull request that restores the previous files. Never force push to `main`.
2. Slice R: restore the legacy record files from `main`, including `design/lock-comparison.md`.
3. Slice 1: remove the `[tool.uv]` table from `pyproject.toml`. Restore the bootstrap install line and the guard cases.
4. Slice 2: restore the `pip install -r` lines in `.github/workflows/ci.yml`. Restore the CI guard cases.
5. Slice 3: restore `Dockerfile`, `Containerfile`, and `.dockerignore`. Rebuild from the previous image tag.
6. Slice 4: remove `mist-ops-platform/uv.lock`. Restore the two Containerfiles and the ops requirements file.
7. Slice 5: restore the `pip` entry in `.github/dependabot.yml`.
8. After each revert, run `uv lock --check` and the export guard. Both must pass.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Principle I: `mist-ops-platform/uv.lock` adds a direct child to `mist-ops-platform/`, which holds 11 children (RC-52). | The ops containers need one lock for every platform. Each ops container installs unlocked ranges today (RC-37, RC-38). | A uv workspace couples the root and ops releases and changes the root exports. The ops `requirements.txt` header names one Windows interpreter (RC-39). Deferring leaves the ops containers unlocked. |

The debt in `mist-ops-platform/` existed before this change (RC-52). The new child does not permit any other new child. Owner review of this exception is requested at T-PR.

## Verification

Each slice runs its tasks' verification commands. It also runs the Local gates rows that apply to its changed files, and then T-REMOTE-CI. The image freeze check runs only after user approval. This authoring step runs no test, build, or install.

## Skill and source use

- Skill `docker-build`, file `01-containerfiles-and-input-contexts/07-base-images-and-input-pinning.md`. It supports D-8.
- `astral-sh/uv` at commit `9bf01bef71c76643290ca17635970076fab1bd0d`, file `crates/uv-settings/src/lib.rs`, lines 247 to 261. It supports D-6.

## Mist API and SDK

Not applicable. This plan calls no Mist endpoint and no mistapi function.
