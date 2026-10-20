# Implementation Plan: Tracked Dependency Lock File

## Scope

Move the dependency declaration into `pyproject.toml`, track `uv.lock`, and make
each install path use the lock. Keep every resolved version unchanged. Slice S0 adds
only this record. No manifest, workflow, image, Dependabot, or bootstrap file
changes before S0 merges.

## Ordering rule

Each slice depends on the one before it. A later slice MUST NOT start until the
earlier slice is on `main` with fresh required checks and CodeQL green. One pull
request is open at a time. Each pull request targets current `main`.

| Slice | Content | Sensitive | Auto-merge |
| - | - | - | - |
| S0 | This specification, plan, and tasks | No | Yes, after fresh checks and CodeQL |
| S1 | Reconcile `pyproject.toml` with the requirements files, and add the declaration parity guard | No | Yes, after fresh checks and CodeQL |
| S2 | Capture the baseline freeze, generate `uv.lock`, remove the ignore line, add the lock check guard | No | Yes, after fresh checks and CodeQL |
| S3 | Switch the bootstrap to `uv sync --locked`, with a pip fallback message only for a missing UV | Yes | No. A human examines it |
| S4 | Make `requirements*.txt` generated exports and add the export guard | No | Yes, after fresh checks and CodeQL |
| S5 | Switch `ci.yml` and `container-build.yml` to the lock, and add the `uv lock --check` job | Yes | No |
| S6 | Switch `Dockerfile` and `Containerfile` to a locked runtime-only sync | Yes | No |
| S7 | Switch Dependabot to `uv`, add the sync guidance, and cover the ops platform | Yes | No |

S4 comes before S5 so the CI install and the audit read generated files that
already match the lock.

## Design

### S1 Declaration reconciliation

1. List each package in `requirements.txt`, `requirements-dev.txt`, `dependencies`,
   and the `dev` extra.
2. For each shared package, keep the higher floor and the existing upper bound.
   Add each missing package to the correct table.
3. Move the devtools Git pin into the `dev` extra. Enable Hatch direct references.
4. Keep `container`, `ste-linter`, and the `waitress` marker unchanged.
5. Add `tests/guardrails/test_dependency_declaration_parity.py`. It parses the files
   with `packaging` and `tomllib`, prints the package count that it examined, and
   fails on a missing or looser entry. A fixture proves that it can fail.

Because the requirements files stay as they are in S1, no environment changes.

### S2 First lock

1. Install the current requirements into a clean environment and save
   `test-artifacts/dependency-freeze-before.txt`.
2. Run `uv lock` with `--exclude-newer` set to the commit time of the baseline so
   the lock cannot pick a newer release. Remove the flag from the stored command.
3. Run `uv export` and compare each version with the freeze. Each difference needs
   a written reason. An upgrade blocks the slice (B-003).
4. Replace the `uv.lock` ignore lines with nothing, and add the lock.
5. Add a guard that runs `uv lock --check` when UV exists and reports the lock
   package count. It fails when the lock is missing.

Warning: a lock made from an incomplete manifest locks the wrong set and hides the
drift. The S1 parity guard MUST pass first.

### S3 Bootstrap

Replace the two `pip install` steps with `uv sync --locked --extra dev`. The script
installs UV first when it is missing. Keep the Chromium and credential steps as they
are. Update the bootstrap tests and the contract test.

### S4 Exports

Generate the two files with `uv export --locked --no-hashes --no-emit-project`. Add
a header line that names the command. Add the export guard.

### S5 CI

Replace each `pip install -r requirements*.txt` line with a locked UV sync. Add a
`dependency_lock` job that runs `uv lock --check` and the export guard. Replace
`pip-audit -r requirements.txt` with `pip-audit --locked .`. Add `uv.lock` to the
`container-build.yml` path trigger. Keep the quality gate names unchanged. Update
the contract tests that read the workflow text.

### S6 Images

Copy a pinned UV binary from its official image by digest. Copy `pyproject.toml`
and `uv.lock`. Run `uv sync --locked --no-dev --no-install-project`. Keep the layer
order so the dependency layer caches. Compare `pip freeze` in each image with the
runtime export.

### S7 Dependabot and ops platform

Change the root entry from `pip` to `uv`. Keep the weekly schedule, the limit of 5,
the label, and the `chore` prefix. Document the regeneration command for the
exports. Open a follow-up task for a lock refresh workflow if Dependabot leaves a
stale export. Add a lock for `mist-ops-platform` and its two containers.

## Guardrails

- Parity guard (S1), lock guard (S2), export guard (S4), and workflow contract
  tests (S5). Each prints its examined count and fails on unreadable input.
- Symbol check on each changed Python file.
- No slice changes a version. The baseline comparison is the evidence.

## Verification

Per slice: compile, ruff, black, mypy, targeted tests, test quality ratchet,
bandit, STE lint on changed Markdown, and the guardrail tests. S3 and later also
run the bootstrap test group and a clean worktree bootstrap. S6 builds both
images with Podman. S5 and S7 observe a green run on the pull request.

## Safety

Caution: S3 and S5 through S7 change how every contributor and image installs.
A human examines each one. Do not enable auto-merge for them. A wrong lock can ship
the wrong package set. Do not close issue #3400 until every install path, CI, the
images, Dependabot, the exports, and the validation pass.

## Overlap check (2026-10-19)

Open pull request #4208 changes `.github/workflows/ci.yml`. It blocks S5 until it
merges. No open pull request changes a manifest, an image file, `dependabot.yml`,
or the bootstrap. Check again before each slice.
