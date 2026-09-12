# Implementation Plan: Gitignore Source Leak Repair

**Branch**: The implementation needs its own branch. This document sits on `docs/1778-1780-specs`. | **Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1778-gitignore-source-leak/spec.md`

**GitHub Issue**: [#1778](https://github.com/jmorrison-juniper/MistHelper/issues/1778)

## Summary

Line 244 of `.gitignore` holds an unanchored `config/` pattern. The pattern excludes three source directories inside two tracked projects. One excluded module holds a MEDIUM bandit result that CI never sees.

This work narrows the pattern, clears the security result, and formats the new files. The three parts must land together. The ignore change alone stops the build on the bandit gate and on the black gate.

The plan orders the work so that each gate risk closes before the files enter git. The commit that adds the files comes last.

## Technical Context

**Language/Version**: Python 3.13 for the three new Python files. TypeScript for the 17 new React files.

**Primary Dependencies**: None. The change adds no package.

**Storage**: N/A. The change adds no schema and no data file.

**Testing**: The existing suite must keep its pass count. The new files hold no test.

**Target Platform**: CI runs on Linux. Developers work on Windows. Git applies the same ignore rules on both platforms.

**Project Type**: repository hygiene and static analysis repair.

**Performance Goals**: Every CI job must stay inside its current timeout. The bandit job holds a 5 minute timeout and finishes in about 10 seconds.

**Constraints**:

- The root `[tool.black]` table sets a line length of 120. The `mist-ops-platform/pyproject.toml` file sets 99. Black reads the root table for a whole repository run, so the new module needs the 120 character form.
- The root ruff `extend-exclude` list holds `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`. Ruff therefore stays quiet on the new Python files.
- The bandit `targets` list holds `mist-ops-platform`, so bandit reads the new Python files.
- Mypy reads `src/` only, so the new files face no type check.
- Git cannot re-include a file below an excluded directory. A negation needs two lines.

**Scale/Scope**: 1 ignore rule, 3 matched directories, 20 source files, and 1 security result.

### Measurement contract

Run each command from the repository root. Use `.venv\Scripts\python.exe` on Windows, because the global interpreter cannot import the project.

```powershell
git check-ignore -v mist-ops-platform/src/shared/config/settings.py
git ls-files mist-ops-platform | Measure-Object
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1778.json" -q
.venv\Scripts\python.exe -m black --check --diff .
.venv\Scripts\python.exe -m ruff check .
```

A Windows bandit run reports 43 results. It reports 42 of them under `tools/test_quality_analyzer/fixtures/`. The `[tool.bandit]` table lists that path in `exclude_dirs`, but a Windows scan does not apply the entry, because the configured path uses a forward slash and a Windows scan reports a backslash. Subtract those 42 by hand.

| Filter step | Baseline count | Target count |
| - | - | - |
| Raw bandit results on Windows | 43 | 42 |
| Minus the analyzer fixtures | 1 | 0 |
| Results in tracked files | 0 | 0 |
| Files that black would rewrite | 0 | 0 |

The baseline reads 0 tracked results only because git hides the module. The target reads 0 with the module tracked.

### Verified mechanics

The implementer probed four behaviors before this plan. Each result shapes a task.

1. **Git needs two negation lines.** Lines 246 to 249 of `.gitignore` already hold the pattern. A directory line comes first, and a file glob line comes second. A single glob line cannot escape an excluded parent directory.
2. **Black reads `.gitignore`.** A run against the excluded directory reports "No Python files are present to be formatted". A forced run reports that black would rewrite `settings.py`. The formatter therefore stops the build after the file enters git.
3. **The `# noqa: S104` annotation is latent.** A run of `ruff check --select S` on the module reports one result at line 27. The same run with `--ignore-noqa` reports a second result at line 41. The annotation already hides the `S104` result from ruff.
4. **Ruff reads the subtree configuration for an explicit path.** The `mist-ops-platform/pyproject.toml` file selects the `RUF` family, so an explicit run reports `RUF100` on the latent annotation. A repository wide run never reaches the file, because the root `extend-exclude` list holds the subtree.

### Discovered risk: the settings module holds a second security result

Ruff reports `S105` at line 27 of the module.

```python
    vault_token: str = "dev-root-token"
```

Bandit does not report that line. The two tools disagree, because bandit handles an annotated assignment differently. The value is a documented local development token, not a production secret. The implementer must record that judgment in the pull request. The implementer must not add a `# noqa: S105` annotation, because a latent annotation is the exact defect that this work removes.

### Discovered risk: the original rule may protect nothing

The team wrote the `config/` rule for a local settings directory. No such directory exists in the working tree today. If the research phase finds no protected directory, the rule needs deletion, not narrowing. Deletion is simpler and removes the whole class of accident.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS | The change touches one line of a class body. It adds no function and no class. |
| II. Class-Based Architecture (No Wrappers) | PASS | The change adds no wrapper. |
| III. Safety-First | PASS with a gate | The implementer must read every new file for a credential before the first commit. Task T006 holds that gate. |
| IV. Full Deployment Pipeline | ADAPTED | The work follows the branch and pull request flow. The container needs no rebuild, because no runtime behavior changes inside the container image. |
| V. Observability and Logging | PASS | The change adds no log call. The one changed line is a settings default. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | The changed line and each new ignore line carry a comment that states the reason. |
| VII. Action Logging (NON-NEGOTIABLE) | NOT APPLICABLE | The change adds no action. A settings default runs no operation. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS with a gate | The plan prefers a named interface or an environment read. A `# nosec B104` comment stays available only with a stated reason. |

### The bind address question

The module sets `api_host` to `0.0.0.0`, which binds the service to every interface. Three answers exist.

1. **Read the host from the environment.** The class already extends `BaseSettings`, so the field already reads an environment variable. Change the default to `127.0.0.1`. A container deployment then sets `API_HOST=0.0.0.0` on purpose. This answer removes the result and keeps the container working.
2. **Bind to a named interface.** This answer breaks a container deployment, because the container needs a bind to every interface to accept outside traffic.
3. **Keep the bind and add `# nosec B104` with a reason.** The repository already holds this pattern at `src/network/_routing_utils_display.py` line 454.

The plan prefers answer 1. It removes the result at the root instead of hiding it. The implementer must confirm that no deployment file relies on the current default before the change.

## Project Structure

### Documentation (this feature)

```text
specs/1778-gitignore-source-leak/
├── spec.md              # The feature specification
├── plan.md              # This file
└── tasks.md             # The task list
```

### Source code (repository root)

```text
.gitignore                                          # Phase 2: narrow the config/ pattern at line 244

mist-ops-platform/src/shared/config/
├── __init__.py                                     # Phase 4: track. The file is empty.
├── constants.py                                    # Phase 4: track. 127 lines, no security result.
└── settings.py                                     # Phase 3: correct line 41, then format, then track.

ops-portal/src/features/config/                     # Phase 5: 7 TypeScript files. Record a decision.
ops-portal/src/pages/config/                        # Phase 5: 10 TypeScript files. Record a decision.
```

**Structure Decision**: The work adds no directory and no module. It corrects one ignore rule and one source line, then adds existing files to git.

## Phased approach

Each phase ends with a measurement. A phase that does not reach its target blocks the next phase.

### Phase 0 - Research (no file change)

- Find the local directory that the `config/` rule protects. Search the working tree and the deployment documents.
- Read every one of the 20 files for a credential, a token, and a private key.
- Read the deployment files of `mist-ops-platform` and record how each one sets the API host.
- Decide the answer to the bind address question.
- Decide whether the 17 TypeScript files belong in git.

**Exit measurement**: The team records five decisions. No decision stays open.

### Phase 1 - Correct the security result (no git change)

- Change the `api_host` default in `settings.py` per the Phase 0 decision.
- Delete the `# noqa: S104` annotation.
- Add an inline comment that states why the default binds where it binds.

**Exit measurement**: A forced ruff run with `--ignore-noqa` reports no `S104` result in the module.

### Phase 2 - Correct the formatting (no git change)

- Run black on the three Python files with the root configuration.
- Confirm that the result matches the 120 character line length.

**Exit measurement**: A forced black check reports zero files to rewrite.

### Phase 3 - Narrow the ignore rule

- Replace or narrow the `config/` pattern at line 244.
- Add the two line negation for each directory that the team decided to track.
- Add a comment above the rule that states which directory it protects.

**Exit measurement**: `git check-ignore -v` prints no rule for the settings module. It still prints a rule for the protected local directory.

### Phase 4 - Track the files and run every gate

- Stage the new files. Read `git status` and confirm that no compiled file appears.
- Run bandit, black, ruff, and mypy across the whole repository.

**Exit measurement**: Every gate exits with code 0.

### Phase 5 - Record the TypeScript decision

- Track the 17 TypeScript files, or record why they stay out.
- State the decision in the pull request body.

**Exit measurement**: The pull request holds a decision for all three matched directories.

## Complexity Tracking

| Item | Why it is needed | Simpler option that the plan rejected |
| - | - | - |
| A two line negation per directory | Git cannot re-include a file below an excluded directory. Lines 246 to 249 already prove the need. | One glob line. It fails without a visible error. |
| A forced black run before the commit | Black reads `.gitignore`, so a normal run skips the file and hides the failure. | A normal run. It reports success and the gate then stops the build. |
| A separate pull request for issue #1780 | The two efforts touch different files and need different reviewers. | One combined pull request. It mixes a defect repair with a design decision. |

## Risks

| Risk | Effect | Control |
| - | - | - |
| The team narrows the rule and a local secret enters git. | A credential enters the history and needs a rotation. | Task T006 reads every new file before the first commit. |
| The bind change breaks a container deployment. | The service stops accepting outside traffic. | Phase 0 reads every deployment file first. |
| Issue #1780 selects the ruff `S` family first. | The latent annotation hides the MEDIUM result for good. | Requirement FR-019 states the order. The pull request repeats it. |
| The 17 TypeScript files hold lint errors. | A future TypeScript job starts with a failure. | Non-goal NG-003 keeps that job outside this scope. The decision record names the debt. |
