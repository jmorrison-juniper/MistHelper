# Feature Specification: Gitignore Source Leak Repair

**Feature Branch**: `docs/1778-1780-specs` (specification only. The implementation needs its own branch.)

**GitHub Issue**: [#1778](https://github.com/jmorrison-juniper/MistHelper/issues/1778) - "security: a MEDIUM bandit finding hides in a source file that gitignore excludes by accident"

**Created**: 2026-08-05

**Status**: Specification. No code change exists yet.

**Input**: A `config/` pattern in `.gitignore` excludes source directories by accident. One excluded module holds a MEDIUM bandit finding that CI never sees. Narrow the pattern, track the source, and clear every gate that the new files then meet.

---

## Background

Line 244 of `.gitignore` holds the pattern `config/`. The pattern carries no anchor, so git applies it to a directory named `config` at any depth. The pattern was written for a local settings directory. It also matches source directories inside two tracked projects.

The `mist-ops-platform` project holds 110 tracked files. The `config` directory under `src/shared/` is the only source directory that drops out. That imbalance shows that the exclusion is an accident, not a decision.

One excluded module holds a security defect. The module is `mist-ops-platform/src/shared/config/settings.py`. Line 41 reads as follows.

```python
    api_host: str = "0.0.0.0"  # noqa: S104
```

Bandit reports the line as a MEDIUM `B104` finding, which is `hardcoded_bind_all_interfaces`. Issue [#889](https://github.com/jmorrison-juniper/MistHelper/issues/889) removed the `-ll` severity flag from the bandit gate. The gate now stops the build on a result at any severity. The gate therefore stops the build on the first run after the module enters git.

The `# noqa: S104` annotation hides nothing today. Issue [#1719](https://github.com/jmorrison-juniper/MistHelper/issues/1719) states the reason. The root ruff configuration does not select the `S` family, and bandit reads `# nosec` only. A reader sees the annotation and believes that a person reviewed the line. No person reviewed the line.

### Measured baseline

A maintainer measured every claim on 2026-08-05 with bandit 1.9.4 and ruff 0.16.0.

| Measurement | Command | Result |
| - | - | - |
| The rule that excludes the module | `git check-ignore -v mist-ops-platform/src/shared/config/settings.py` | `.gitignore:244:config/` |
| Tracked files in the project | `git ls-files mist-ops-platform` | 110 |
| The module in git | `git ls-files mist-ops-platform/src/shared/config/settings.py` | no output |
| Raw bandit results | `bandit -c pyproject.toml -r .` | 43 |
| Results under the analyzer fixtures | the same run | 42 |
| Results that remain | the same run | 1 |
| Results in tracked files | the same run | 0 |

The one remaining result is the `B104` MEDIUM at line 41 of the settings module. Every claim in issue #1778 holds.

### Three findings that issue #1778 does not state

The measurement produced three facts that the issue text omits. Each fact widens the work.

**Finding 1: the pattern hides three directories, not one.**

```text
.gitignore:244:config/  mist-ops-platform/src/shared/config/
.gitignore:244:config/  ops-portal/src/features/config/
.gitignore:244:config/  ops-portal/src/pages/config/
```

The three directories hold 20 source files in total.

| Directory | Files | Type |
| - | - | - |
| `mist-ops-platform/src/shared/config/` | 3 | Python |
| `ops-portal/src/features/config/` | 7 | TypeScript React |
| `ops-portal/src/pages/config/` | 10 | TypeScript React |

**Finding 2: the black gate also stops the build.**

Black reads `.gitignore` and skips an ignored file. The settings module therefore never met the formatter. The module carries the 99 character line length of the `mist-ops-platform` subtree. The root black configuration sets 120 characters. A forced run reports that black would rewrite the module. CI runs `black --check --diff .`, so the gate stops the build the moment the module enters git.

**Finding 3: the annotation is latent, not inert.**

The `# noqa: S104` annotation activates the moment anybody selects the `S` family in ruff. A run of `ruff check --select S` on the module reports one result at line 27 and no result at line 41. The same run with `--ignore-noqa` reports both. The annotation therefore hides the MEDIUM defect from ruff already. Issue [#1780](https://github.com/jmorrison-juniper/MistHelper/issues/1780) asks whether to select the `S` family. If issue #1780 lands first, the annotation hides the defect for good.

Warning: If a person selects the ruff `S` family before this work deletes the annotation, the `S104` defect becomes invisible to both tools. Delete the annotation first.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track every source file that the project needs (Priority: P1)

A maintainer clones the repository on a clean machine. The maintainer starts the `mist-ops-platform` service. The service imports its settings module and starts, because git holds every module that the service needs.

**Why this priority**: The missing module is a correctness defect on its own. A clean clone cannot start the service today. The security defect in User Story 2 is a consequence, not the root cause.

**Independent Test**: A reviewer runs `git ls-files mist-ops-platform/src/shared/config/settings.py` on the branch. The command prints the path.

**Acceptance Scenarios**:

1. **Given** the corrected ignore rule, **When** a reviewer runs `git check-ignore -v mist-ops-platform/src/shared/config/settings.py`, **Then** the command prints no rule and exits with code 1.
2. **Given** the corrected ignore rule, **When** a reviewer runs `git ls-files mist-ops-platform/src/shared/config/`, **Then** the command lists `__init__.py`, `constants.py`, and `settings.py`.
3. **Given** the corrected ignore rule, **When** a reviewer runs `git status --porcelain`, **Then** the output holds no compiled Python file from a `__pycache__` directory.
4. **Given** the corrected ignore rule, **When** a reviewer runs `git check-ignore -v` against the local settings path that the original rule protected, **Then** the command still prints a rule.

---

### User Story 2 - Clear the security defect before the module enters git (Priority: P1)

A security reviewer wants the tracked code to hold zero bandit results. The reviewer reads the corrected settings module. The module binds to a named interface or reads the host from the environment. No hidden defect enters the history.

**Why this priority**: The gate stops the build on the first push that holds the module. This story and User Story 1 must land in one pull request, because either one alone breaks CI.

**Independent Test**: A reviewer runs `bandit -c pyproject.toml -r .` on a Linux checkout of the branch. The command reports zero results and exits with code 0.

**Acceptance Scenarios**:

1. **Given** the corrected module, **When** CI runs `bandit -c pyproject.toml -r .`, **Then** the job reports zero results and succeeds.
2. **Given** the corrected module, **When** a reviewer reads line 41, **Then** the line holds no `# noqa: S104` annotation.
3. **Given** a bind to every interface that the team keeps, **When** a reviewer reads the line, **Then** the line holds a `# nosec B104` comment that states the reason.
4. **Given** the corrected module, **When** a reviewer runs `ruff check --select S --ignore-noqa` against the module, **Then** the run reports no `S104` result.

---

### User Story 3 - Keep every other gate green (Priority: P2)

A maintainer pushes the branch. Every CI job succeeds. No new file breaks the formatter, the linter, or the type checker.

**Why this priority**: The formatter failure is certain and measured. The story protects the pull request from a second review cycle.

**Independent Test**: A reviewer runs the full local gate set on the branch. Ruff, black, and mypy each exit with code 0.

**Acceptance Scenarios**:

1. **Given** the new tracked files, **When** CI runs `black --check --diff .`, **Then** the job reports zero files to rewrite.
2. **Given** the new tracked files, **When** CI runs `ruff check .`, **Then** the job reports zero results.
3. **Given** the new tracked files, **When** CI runs `mypy src/ --config-file pyproject.toml`, **Then** the job reports no new error.
4. **Given** the 17 TypeScript files that the corrected rule adds, **When** CI runs the full workflow, **Then** every job keeps the status that it held before the change.

---

### Edge Cases

- A person narrows the rule but forgets the directory negation. Git cannot re-include a file below an excluded directory. The rule needs two lines, as lines 246 to 249 already show. A single glob line fails without a visible error.
- A person adds the module without the black correction. The formatter job stops the build. The person must run `black` on the module before the first commit.
- A person adds the module without the bandit correction. The security job stops the build, because issue #889 removed the severity filter.
- A person narrows the rule and stages a `__pycache__` directory by accident. Line 80 of `.gitignore` holds the `__pycache__/` rule, so git catches the compiled files once it descends into the directory. The person must still read `git status` before the first commit.
- The original `config/` rule protects a real local directory. A person must find that directory before the change. If no such directory exists, the rule needs deletion, not narrowing.
- A person tracks the 17 TypeScript files and starts a lint job that the repository does not run today. The files then need their own cleanup. This specification keeps that work outside its scope.
- A person selects the ruff `S` family under issue #1780 before this work lands. The latent annotation then hides the MEDIUM defect. The two efforts need an order.

---

## Requirements *(mandatory)*

### Ignore rule requirements

- **FR-001**: The `config/` pattern at line 244 of `.gitignore` MUST stop matching a directory inside a tracked project.
- **FR-002**: The corrected rule MUST keep the exclusion that the original rule protects. The team MUST name that directory before the change.
- **FR-003**: The corrected rule MUST follow the two line form that lines 246 to 249 already use. The first line re-includes the directory. The second line re-includes the files inside it.
- **FR-004**: The corrected rule MUST NOT re-include a compiled Python file, a build output, or a local secret.
- **FR-005**: The team MUST record a decision for each of the three matched directories. The decision is track or keep out.

### Source tracking requirements

- **FR-006**: Git MUST track `mist-ops-platform/src/shared/config/__init__.py`, `constants.py`, and `settings.py`, or the pull request MUST state why each file stays out.
- **FR-007**: The team MUST record a decision for the 17 TypeScript files under `ops-portal/`. The decision MUST state the reason.
- **FR-008**: The change MUST NOT add a file that holds a credential, a token, or a private key.

### Security requirements

- **FR-009**: The bandit gate MUST report zero results after the new files enter git.
- **FR-010**: The `B104` result at line 41 of the settings module MUST receive one recorded decision. The decision MUST be a bind to a named interface, a read from the environment, or a `# nosec B104` comment that states the reason.
- **FR-011**: The team MUST select the decision in this order. First, correct the root cause. Second, restructure to remove the pattern. Third, add a suppression comment for a result that a person verified as safe.
- **FR-012**: The `# noqa: S104` annotation at line 41 MUST go, because the annotation hides the defect the moment anybody selects the `S` family.
- **FR-013**: The team MUST search every new tracked file for a further security result before the first commit. The search MUST cover bandit and MUST cover `ruff check --select S --ignore-noqa`.

### Quality requirements

- **FR-014**: Every CI gate MUST hold its current status after the change.
- **FR-015**: Black MUST report zero files to rewrite across the whole repository.
- **FR-016**: Every changed Python line MUST carry an inline comment that states why the line exists.
- **FR-017**: All prose, all code comments, and all commit text MUST follow the writing guide at `documentation/ASD-STE100_writing-guide.md`.
- **FR-018**: The pull request MUST land the ignore rule change and the security correction together, because either change alone stops the build.

### Coordination requirements

- **FR-019**: This work MUST land before issue #1780 selects the ruff `S` family. The pull request MUST state that order.
- **FR-020**: The pull request MUST reference issue #1719, which removed every other latent annotation of this kind.

### Key Entities

- **Ignore rule**: One line in `.gitignore`. It holds a pattern, and git applies it to a path.
- **Matched directory**: One directory that the pattern excludes. It holds a track decision or a keep out decision.
- **Bandit result**: One report entry. It holds a rule identifier, a severity, a file path, and a line number.
- **Latent annotation**: A `# noqa` comment for a rule that no tool selects today. It starts to hide a result the moment a person selects that rule.

---

## Non-Goals

- **NG-001**: This work does not select the ruff `S` family. Issue #1780 owns that decision.
- **NG-002**: This work does not remove the `mist-ops-platform` entry from the root ruff `extend-exclude` list.
- **NG-003**: This work does not add a TypeScript lint job or a TypeScript build job.
- **NG-004**: This work does not audit the other patterns in `.gitignore`. It corrects the `config/` pattern only.
- **NG-005**: This work does not restructure the settings module beyond the one line that holds the security defect.
- **NG-006**: This work does not rotate a credential, because the measurement found no real credential in the new files.

---

## Success Criteria *(mandatory)*

- **SC-001**: `git check-ignore -v mist-ops-platform/src/shared/config/settings.py` prints no rule and exits with code 1.
- **SC-002**: `git ls-files mist-ops-platform` reports 113 files or more, against the baseline of 110.
- **SC-003**: `bandit -c pyproject.toml -r .` reports zero results outside the analyzer fixtures.
- **SC-004**: `black --check --diff .` reports zero files to rewrite.
- **SC-005**: `ruff check .` reports zero results.
- **SC-006**: No line in the repository holds a `# noqa: S104` annotation.
- **SC-007**: `ruff check --select S --ignore-noqa` reports no `S104` result in the new tracked files.
- **SC-008**: The pull request records a track decision or a keep out decision for each of the three matched directories.
- **SC-009**: `git status --porcelain` reports no compiled Python file.
- **SC-010**: Every CI job that succeeded before the change succeeds after the change.

---

## Assumptions

- The `mist-ops-platform` project stays in the repository. A plan to delete the project would cancel this work.
- The original `config/` rule protects a local directory that a developer creates. The team confirms that directory during the research phase.
- The bandit version stays at 1.9.4, which `requirements-dev.txt` pins.
- The root ruff `extend-exclude` list keeps the `mist-ops-platform` entry, so ruff stays quiet on the new Python files.
- The repository runs no lint job and no build job for TypeScript, so the 17 new TypeScript files add no gate risk.
