# Feature Specification: CodeQL register check fails on pull request 4888

**Feature Branch**: `fix/4904-codeql-register-check`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4904, titled "CI: quality-gate `codeql_register_check` failed (PR #4888)". Pull request #4888 raises the transitive pin `mando` from 0.7.1 to 0.8.2 in `requirements-dev.txt`. Radon 6.0.1 requires `mando` below 0.8, so the gate install step fails.

## Failure Record

- **Failing check**: "CodeQL verdict register check". It runs gate `codeql_register_check` as job `codeql_register_check` in `.github/workflows/ci.yml` lines 385-411.
- **Failing run**: Workflow run 45064243269, job 137336719141, event `pull_request`, head branch `dependabot/pip/mando-0.8.2`, conclusion failure.
- **Failing step**: `Run python -m pip install -r requirements-dev.txt`. The next step, which runs `codeql-verdict-register check`, was skipped.
- **Failing rule**: Pip dependency resolution. Pip prints `ResolutionImpossible` and "radon 6.0.1 depends on mando<0.8 and >=0.6".

## Clarifications

### Session 2026-11-26

- Q: Is commit `5bb4b385` the head of pull request #4888? A: No. It is the GitHub merge commit of base `00d9a16e` and head `e86098cd`. The issue names the merge commit.
- Q: Does the failure affect `main`? A: No. The latest Quality Gates run on `main`, run 45774119357, succeeded at commit `f03c6c9b`.
- Q: Do the other failed jobs have a separate cause? A: No. 26 of 28 failed jobs print the same resolver conflict. The other two jobs verify the failed upstream jobs.
- Q: Is radon 6.0.1 the current radon release? A: Yes. The PyPI JSON reports version 6.0.1 on 2026-11-26. Its requirements list `mando (<0.8,>=0.6)`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the register gate installable (Priority: P1)

A maintainer opens a pull request that changes a development pin. The install step resolves every pin. The register check then runs and reports its result.

**Why this priority**: A failed install hides the register result. Maintainers then cannot judge the pull request.

**Independent Test**: Run the resolver check in `design/quickstart.md`, step 6. The pinned set passes with `mando` 0.7.1 and radon 6.0.1.

**Acceptance Scenarios**:

1. **Given** `requirements-dev.txt` pins `mando==0.7.1`, **When** the install step runs, **Then** pip resolves the file and the register check runs.
2. **Given** a pin of `mando==0.8.2`, **When** the local guard runs, **Then** the guard reports a defect before CI starts.

---

### User Story 2 - Stop Dependabot from reopening the rejected bump (Priority: P2)

Dependabot checks pip updates each week. The repository has no rule for `mando`. Dependabot can propose a minor or major `mando` update that radon rejects.

**Why this priority**: Each proposal fails the same gate and adds review work for maintainers.

**Independent Test**: Read the pip stream of `.github/dependabot.yml`. Confirm the `mando` ignore entry. Run the policy guard test.

**Acceptance Scenarios**:

1. **Given** the pip stream, **When** Dependabot evaluates a `mando` 0.8.x update, **Then** the update type `version-update:semver-minor` is ignored.
2. **Given** the pip stream, **When** Dependabot evaluates a `mando` 0.7.2 update, **Then** the ignore entry does not block the patch update.

---

### User Story 3 - Find a rejected pin before CI (Priority: P3)

A developer changes a pin in `requirements-dev.txt`. A local guard test reads the installed radon requirement. It reports a rejected `mando` pin within seconds.

**Why this priority**: Local feedback shortens the cycle. The message names the cause in plain words.

**Independent Test**: Run `python -m pytest tests/guardrails/test_dependency_lock_file.py`. The pinned case passes. The negative case reports one defect.

**Acceptance Scenarios**:

1. **Given** the pin `mando==0.7.1`, **When** the guard runs, **Then** it prints the examined counts and reports zero defects.
2. **Given** the pin `mando==0.8.2`, **When** the guard runs, **Then** it reports one defect that names `mando` and the radon requirement.

### Edge Cases

- Radon releases a version that accepts `mando` 0.8. The owner removes the ignore entry and updates the pin and the lock in one change.
- Radon is missing from the test environment. The guard fails and names the missing package. It does not skip.
- A later `mando` 0.7.x patch release appears. The ignore entry allows it. The lock still needs its own `uv lock` change.
- Pull request #4888 stays open after this change merges. Its check keeps failing, so the owner must close it.
- A developer edits `requirements-dev.txt` by hand. The export guard fails when the file differs from the lock export.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The install step of the `codeql_register_check` job MUST resolve every pin in `requirements-dev.txt` without a resolver conflict.
- **FR-002**: The `mando` pin MUST stay at `mando==0.7.1`. The lock export MUST match `requirements-dev.txt`.
- **FR-003**: The pip stream of `.github/dependabot.yml` MUST ignore `mando` updates of the types `version-update:semver-minor` and `version-update:semver-major`.
- **FR-004**: The `codeql_register_check` job, its install command, and its check command MUST stay unchanged.
- **FR-005**: The local guard MUST fail when a `mando` pin falls outside the ceiling that radon declares.
- **FR-006**: The change MUST add one release-note fragment that names issue 4904.
- **FR-007**: Each changed Markdown file MUST score 80 or above in `ste-linter`.

### Mist Cloud Transport Requirements

Not applicable. This change makes no Mist REST or WebSocket call.

### Key Entities

- **Gate**: A quality rule that one job enforces. Example: the rule `codeql_register_check`.
- **Job**: A GitHub Actions unit in `.github/workflows/ci.yml` that runs one gate.
- **Check**: The status name that a job reports on a pull request. Example: CodeQL verdict register check.
- **Pin**: One `name==version` line in `requirements-dev.txt`.
- **Export**: A requirements file that uv generates from `uv.lock`.
- **Ceiling**: The upper bound of a requirement. Example: `<0.8` in the radon requirement on `mando`.
- **Ignore entry**: One item of the `ignore` list in `.github/dependabot.yml`.
- **Resolver conflict**: A pip failure that reports `ResolutionImpossible` when pins cannot satisfy every requirement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The check CodeQL verdict register check reports success on the head commit of the fix pull request.
- **SC-002**: The workflow run of the fix pull request has zero `ResolutionImpossible` lines in its failed-job logs.
- **SC-003**: The local guard prints its examined counts and reports zero defects on `main`.
- **SC-004**: Pull request #4888 reaches the closed state, and its `mergedAt` value is null.
- **SC-005**: No Dependabot pull request for a `mando` minor or major update opens within seven days after the merge.

## Out of Scope

- Replacing radon, or changing the `Radon (complexity)` gate.
- Changing the register tool, its pin, or its check command.
- Changing branch protection, required checks, or the merge queue.
- Regenerating `requirements-dev.txt` or `uv.lock` for a newer `mando` release.
- Reducing the child counts of `tests/guardrails/` and `changelog.d/`. Both exceed five children today. A separate remediation issue tracks them.

## Assumptions

- Radon 6.0.1 remains the newest radon release when the fix merges. The implementer rereads the PyPI JSON before opening the pull request.
- The repository owner authorizes the label changes, the merge, and the close of pull request #4888.
- Dependabot applies an `update-types` ignore entry to a transitive pin in `requirements-dev.txt`. This assumption is unverified. See the Unverified list in `design/research.md`.
- The CI runner uses the same package index as the failed run.
