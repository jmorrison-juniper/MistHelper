# Tasks: Tracked Dependency Lock File

## S0 Specification

- [x] T001 Write spec.md with the adopted decision and the assumptions.
- [x] T002 Write plan.md with the staged slices and guardrails.
- [x] T003 Write tasks.md and review the slice order for safe ordering.
- [ ] T004 Open the S0 pull request and post the assumption on issue #3400.

## S1 Declarations

- [ ] T005 Reconcile `pyproject.toml` runtime and `dev` declarations with both requirements files.
- [ ] T006 Enable Hatch direct references for the devtools pin.
- [ ] T007 Add the declaration parity guard and its failing fixture.

## S2 Lock

- [ ] T008 Capture `dependency-freeze-before.txt` from a clean install.
- [ ] T009 Generate `uv.lock` with a baseline `--exclude-newer` date.
- [ ] T010 Compare the lock with the freeze and explain each difference.
- [ ] T011 Remove the `uv.lock` ignore lines and add the lock guard.

## S3 Bootstrap

- [ ] T012 Switch `scripts/bootstrap_worktree.py` to `uv sync --locked`.
- [ ] T013 Update the bootstrap unit and contract tests.

## S4 Exports

- [ ] T014 Generate `requirements.txt` and `requirements-dev.txt` from the lock.
- [ ] T015 Add the export drift guard.

## S5 CI

- [ ] T016 Switch each `ci.yml` and `container-build.yml` install to the lock.
- [ ] T017 Add the `dependency_lock` job and switch the audit to `--locked`.
- [ ] T018 Update the workflow contract tests.

## S6 Images

- [ ] T019 Switch `Dockerfile` and `Containerfile` to a locked runtime-only sync.
- [ ] T020 Compare image package lists with the runtime export.

## S7 Dependabot and ops platform

- [ ] T021 Change the Dependabot root entry to `uv`.
- [ ] T022 Document the export regeneration command.
- [ ] T023 Add a lock for `mist-ops-platform` and its two containers.

## Close

- [ ] T024 Run the full validation and close issue #3400 only when T005 through T023 pass.
