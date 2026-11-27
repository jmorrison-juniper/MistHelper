# Feature Specification: Ruff (lint) check failure from the mando 0.8.2 pin

**Feature Branch**: `fix/4891-dependabot-mando-ignore`

**Created**: 2026-11-26

**Status**: Draft

**Input**: CI quality-gate failure report for issue #4891, "CI: quality-gate `ruff` failed (PR #4888)".

**Record path**: `specs\numbered\0\0\1\2\4\0\3\1\4891-ruff-gate-mando-conflict`

## Clarifications

### Session 2026-11-26

- Q: Which check failed? A: The Ruff (lint) check, job ID `ruff`, job 137336719229 in run 45064243269. Its pip install step failed. No ruff rule ran (research.md, section 2).
- Q: Does `main` fail the same way? A: No. `main` pins mando 0.7.1 (RV-01). The Ruff (lint) check succeeded on `main` at f03c6c9 (RV-29).
- Q: Should PR #4888 close? A: No. The repository says not to close update pull requests (RV-22). See decision D-3.
- Q: Where does the guard test go? A: In `tests/guardrails/test_dependency_export.py`. The folder holds 79 direct children (RV-43). See decision D-4.
- Q: Does the change need a changelog fragment? A: Yes. The constitution requires one fragment for each change (RV-20). See decision D-5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the Ruff (lint) check able to run `ruff check .` (Priority: P1)

A maintainer changes a dependency pin. The Ruff (lint) check must install the pins, then run `ruff check .`. A resolver conflict must stop the job before the lint step. The job log must show the conflict.

**Why this priority**: The Ruff (lint) check reports lint results for each pull request. A failed install hides every lint result.

**Independent Test**: Run the Ruff (lint) check on the fix pull request. Step 5 and step 6 both succeed (SC-001).

**Acceptance Scenarios**:

1. **Given** `requirements-dev.txt` pins mando 0.7.1 and radon 6.0.1, **When** the Ruff (lint) check runs, **Then** the pip install step succeeds and `ruff check .` runs.
2. **Given** a pull request pins mando 0.8.2, **When** the Ruff (lint) check runs, **Then** the pip install step fails with the resolver conflict. The lint step is skipped.

---

### User Story 2 - Stop Dependabot from reopening the mando 0.8 bump (Priority: P1)

The weekly pip update stream must not propose mando minor updates while radon 6.0.1 blocks them. Patch updates of mando must stay allowed.

**Why this priority**: The same bump reopens the failure in every job that installs the dev requirements after the next weekly run.

**Independent Test**: Run the three guard cases in `tests/guardrails/test_dependency_export.py` (SC-003).

**Acceptance Scenarios**:

1. **Given** `.github/dependabot.yml` holds the mando ignore entry, **When** the minor-update guard case runs, **Then** the case passes. It prints the count of pip ignore entries that it examined.
2. **Given** the mando entry blocks patch updates, **When** the patch-update guard case runs, **Then** the case fails.
3. **Given** the mando ignore entry is missing, **When** the gap check runs, **Then** it returns a message that names mando, and the failing-path case passes.

---

### User Story 3 - Record the true failing check and cause (Priority: P2)

A triage engineer sees the issue title "quality-gate `ruff` failed". The record must name the check, the step, the conflict text, and the fact that no ruff rule ran.

**Why this priority**: The title names the gate, not the step. A reader can expect a lint finding that does not exist.

**Independent Test**: Follow quickstart.md steps QS-02 and QS-03. The output names job 137336719229, step 5, and the conflict text (FR-006).

**Acceptance Scenarios**:

1. **Given** the record, **When** a reader opens `design\research.md`, **Then** the reader finds the job ID, the step name, and the conflict text.

---

### Edge Cases

- A mando 0.7.x patch release appears. The ignore entry must allow it (FR-003).
- A radon release accepts mando 0.8. The ignore entry must go in a separate change. The YAML comment names this condition.
- Dependabot does not honor the `update-types` filter for pip. The next weekly run shows it (U-01).
- PR #4888 stays open after the fix merges. The record names its state. No manual close occurs (U-02, D-3).
- The Ruff (lint) check finds rule violations after the pip install step passes. Each violation follows the repository error pipeline. This change does not fix lint rules (U-03).
- A maintainer edits `requirements-dev.txt` by hand. The existing export guard fails (RV-23).

Caution: a broad ignore entry hides future security updates for mando. Keep the entry narrow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST keep mando at 0.7.1 in `requirements-dev.txt` while radon 6.0.1 is pinned.
- **FR-002**: The pip update stream in `.github/dependabot.yml` MUST NOT propose mando semver-minor updates.
- **FR-003**: The pip ignore entry for mando MUST allow mando semver-patch updates.
- **FR-004**: A guard case MUST fail when the mando ignore entry is missing. The guard cases MUST print the count of pip ignore entries that they examined.
- **FR-005**: The change MUST add one changelog fragment named `issue-4891-dependabot-mando-ignore.md`.
- **FR-006**: The record MUST name the failing check, the failing step, the conflict text, and the fact that no ruff rule ran.
- **FR-007**: The change MUST NOT close PR #4888, comment on it, edit its branch, or push to its branch.
- **FR-008**: The change MUST pass each applicable local gate and each required remote check before merge.
- **FR-009**: Each new executable line MUST carry an inline comment. Each file read MUST log a message before and after the read.

### Key Entities

Not applicable: this change adds no data entity. It changes one policy file and one guard module, and it adds one fragment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the fix pull request, the Ruff (lint) check reports success for step 5 and step 6.
- **SC-002**: On the fix pull request, the Dependency lock and exports check reports success.
- **SC-003**: The three guard cases pass, and the test output prints the count of examined entries.
- **SC-004**: `.github/dependabot.yml` parses as YAML. Its pip update block holds exactly one mando ignore entry.
- **SC-005**: Issue #4891 closes after the fix merges. The pull request body contains `Closes #4891`.
- **SC-006**: The counts of remote checks, decisions, tasks, and requirements match in the STATUS file, `research.md`, and the summary.

## Assumptions

- `main` reflects the current tree. The Ruff (lint) check and the Dependency lock and exports check passed on `main` at f03c6c9 (RV-29, RV-51).
- The PyPI radon page shows the latest release on 2026-11-26 (RV-25).
- The local `.venv` radon 6.0.1 metadata matches the pin that CI installs (RV-24, RV-02).
- Dependabot applies `update-types` to the pip stream. Repository precedent exists only for npm (RV-16, U-01).

### Terms used in this record

- **Ruff (lint) check**: The GitHub check for job ID `ruff` in the Quality Gates workflow.
- **Pip install step**: Step 5 of the Ruff (lint) check, named `Run pip install -r requirements-dev.txt`.
- **Resolver conflict**: The pip error `ResolutionImpossible`, with the text quoted in `research.md`, section 2.
- **Fix pull request**: The pull request that carries this record and the fix.
- **PR #4888**: The Dependabot pull request that moves mando to 0.8.2.
- **Local gate**: A command in the local gates table of `.github/copilot-instructions.md`.
- **Remote check**: A row in the remote verification table of `research.md`, section 7. Each row has an ID of the form RV-nn.
- **Decision**: An entry in `research.md`, section 6, with an ID of the form D-n.
- **Unverified item**: An entry in `research.md`, section 10, with an ID of the form U-nn.
- **Finding**: An entry in `analysis.md`, with an ID of the form DEF-nn.

## Out of Scope

- Changes to `requirements-dev.txt`, `requirements.txt`, `pyproject.toml`, or `uv.lock`. `main` already holds the required pins.
- Upgrades of radon or mando.
- Closing PR #4888, or any change to its branch.
- The missing job IDs in `documentation/quality-gates.md`. Track them in a separate issue (analysis DEF-03).
- The conflict between the changelog README rule and the constitution. Track it in a separate issue (analysis DEF-04).
- Constitution Principle IV steps 10 to 12 for CI-only changes. Track them in a separate issue (analysis DEF-05).
- Splitting the 79 direct children of `tests/guardrails`. Track the split in a separate issue (analysis DEF-07).
- Moving the Dependabot pip stream to the uv ecosystem.
