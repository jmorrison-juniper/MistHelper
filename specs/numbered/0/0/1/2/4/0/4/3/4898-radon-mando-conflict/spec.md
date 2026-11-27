# Feature Specification: Radon Job Mando Pin Conflict

## Clarifications

### Session 2026-11-26

- **Question**: Does the complexity rule need a change? **Answer**: No. The radon job passed on main in run 45774119357, including the complexity step (R-08).
- **Question**: Does a newer radon release accept mando 0.8? **Answer**: No. PyPI lists radon 6.0.1 as the latest release. It requires mando below 0.8 (R-51).
- **Question**: Does main need a lock or requirements change? **Answer**: No. Main already pins mando 0.7.1 in `requirements-dev.txt` (R-09) and in `uv.lock` (R-16).
- **Question**: Where do the guard tests go? **Answer**: In the existing file `tests/guardrails/test_dependency_lock_file.py`. The folder `tests/guardrails` has 79 direct children (R-23). Principle I forbids a new direct child there.
- **Question**: Does the change need a changelog fragment? **Answer**: Yes. The constitution Documentation section requires one fragment for each change (R-29). The changelog README exempts internal-only changes (R-34). This record follows the constitution. See D-6 in `design/research.md`.

## Terms

- **Radon job**: The job `radon` in `.github/workflows/ci.yml`. GitHub shows its check as `Radon (complexity)`.
- **Install step**: The step `Run pip install -r requirements-dev.txt` in the radon job.
- **Complexity step**: The step `Check cyclomatic complexity` in the radon job.
- **Complexity rule**: The limit of cyclomatic complexity 10, enforced by `complexity-gate --max 10`.
- **Pin**: A line that sets one package to one version, such as `mando==0.7.1`.
- **Resolution conflict**: A pip error. No version set satisfies every pin.
- **Ignore rule**: An entry under `ignore` in `.github/dependabot.yml`.
- **PR #4888**: The Dependabot pull request that raises mando to 0.8.2.
- **Fix PR**: The pull request that delivers this change and this record.
- **Guard test**: A test in `tests/guardrails/`.
- **Remote check**: A check of a path, a ref, and a blob SHA on GitHub, or of an upstream source.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the radon job able to install (Priority: P1)

Run 45064243269 stopped 26 jobs at an install step. The radon job stopped before its complexity step. Each pull request must let the radon job install and run its complexity step.

**Why this priority**: A resolution conflict stops the install step of each affected job. Those jobs produce no gate result.

**Independent Test**: Run the radon job on the fix PR. The install step and the complexity step both succeed.

**Acceptance Scenarios**:

1. **Given** the fix PR, **When** CI runs the radon job, **Then** the install step and the complexity step succeed.
2. **Given** main at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, **When** the radon job runs, **Then** it succeeds, as run 45774119357 shows (R-08).

### User Story 2 - Stop Dependabot from raising a release that radon rejects (Priority: P1)

Dependabot checks pip packages each week (R-18). Without an ignore rule, it proposes mando 0.8 releases. Radon 6.0.1 rejects each mando release from 0.8.0 on. The ignore rule stops those proposals.

**Why this priority**: Each proposal fails the same way and opens new quality-gate issues.

**Independent Test**: The guard test reads the ignore rule. It finds that mando 0.8.2 is ignored and mando 0.7.2 is allowed.

**Acceptance Scenarios**:

1. **Given** the fix branch, **When** the guard test reads `.github/dependabot.yml`, **Then** mando 0.8.2 is ignored and mando 0.7.2 is allowed.
2. **Given** a policy file without the ignore rule, **When** the guard test reads it, **Then** mando 0.8.2 is allowed.

### User Story 3 - Catch a rejected pin before CI (Priority: P2)

A developer sets `mando==0.8.2` while radon stays at 6.0.1. The guard test reports the defect on the developer machine. CI reports the same conflict later, at the install step.

**Why this priority**: The local signal comes earlier than the CI signal.

**Independent Test**: The radon pin test fails and names mando 0.8.2 and the accepted range.

**Acceptance Scenarios**:

1. **Given** `mando==0.8.2` and `radon==6.0.1` in a requirements file, **When** the radon pin test runs, **Then** it reports one defect that names the range `<0.8,>=0.6`.

### Edge Cases

- A later radon release accepts mando 0.8. The radon pin test fails. A maintainer then updates the test constants from the new radon metadata.
- A security advisory affects only mando releases below 0.8. The ignore rule covers 0.8 and later releases, so a maintainer reviews the advisory by hand.
- Someone reopens PR #4888. The ignore rule blocks new Dependabot proposals. The reopened pull request keeps its own pin, and that pin fails the install step.
- A mando pin appears in `requirements.txt`. The radon pin test reads only `requirements-dev.txt`, so a maintainer reviews that case by hand.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The pip ignore rule MUST stop Dependabot from proposing mando 0.8.0 or later.
- **FR-002**: A guard test MUST fail when the pinned mando is outside the range that radon 6.0.1 accepts.
- **FR-003**: A guard test MUST fail when the ignore rule does not block mando 0.8.2.
- **FR-004**: PR #4888 MUST close without a merge after the fix PR merges, with a note that cites the main pin.
- **FR-005**: The fix PR MUST use the branch `fix/4898-radon-mando-conflict` and a Conventional Commits title.
- **FR-006**: The fix PR MUST contain `Closes #4898` in its body and carry the labels bug, ci, and tests.
- **FR-007**: The fix PR MUST add exactly one changelog fragment for this change.
- **FR-008**: The Radon (complexity) check MUST pass on the fix PR run, and its complexity step MUST run.
- **FR-009**: The change MUST keep the radon command and the complexity rule unchanged.
- **FR-010**: The change MUST NOT edit `requirements-dev.txt`, `requirements.txt`, `pyproject.toml`, or `uv.lock`.

### Key Entities *(include if feature involves data)*

Not applicable: this change adds no data entity. See `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the fix PR run, every job that installs `requirements-dev.txt` completes its install step.
- **SC-002**: On the fix PR run, the Radon (complexity) check passes, and its complexity step runs.
- **SC-003**: Each guard test fails when its rule is removed or changed. The mutation runs in T-LOCAL-GATES record this.
- **SC-004**: After the fix PR merges, the next weekly Dependabot run opens no pip pull request for mando 0.8.0 or later.

## Out of Scope

- Changing the complexity rule, the radon command, or the radon version.
- Replacing the radon tool or the `complexity-gate` tool.
- Changing how the Quality Gates workflow orders or skips jobs.
- Examining or fixing the native Windows checks on PR #4888.
- Closing the sibling issues #4891 through #4905. The orchestrator decides this (D-8).
- Resolving the conflict between the constitution and the changelog README (`analysis.md`, A-06).
- Pull requests #4886, #4889, and #4890.

## Assumptions

- PyPI keeps mando 0.7.1 available for installation.
- Dependabot applies `versions` ranges in `ignore` to pip updates. The github/docs source documents this syntax (R-53).
- The `ci.yml` workflow keeps the radon job and its command (R-01, R-02, R-03).
- Mando is a development-only package. `requirements.txt` holds no mando pin (R-15).
