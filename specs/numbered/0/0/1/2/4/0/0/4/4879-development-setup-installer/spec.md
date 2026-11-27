# Feature Specification: Development setup installer text

**Feature Branch**: `fix/4879-development-setup-installer`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4879: "Docs: development setup describes a requirement-file install that the bootstrap no longer runs"

**Record path**: `specs\numbered\0\0\1\2\4\0\0\4\4879-development-setup-installer`

## Clarifications

### Session 2026-11-26

- Q: Does `main` still hold the two statements that the issue body quotes? → A: No. Neither quote matches the current guide text (R-04, R-05). The defects that remain are in Step 2, the report text, the settings table, and Package sources (R-03, R-06 to R-11).
- Q: Does the bootstrap install the requirement files? → A: No. It runs `uv sync --locked --extra dev` (`scripts/bootstrap_worktree.py` line 466). It names the pip export files only in its final report (line 694).
- Q: Which settings does the bootstrap set for each child process? → A: The guide table names twelve settings after this change. The contract file gives each name, its condition, and its script line.
- Q: Does CI grade `documentation/development-setup.md` for STE? → A: No. `.github/workflows/ste-lint.yml` line 44 lists five other files (R-35). The issue requires a local score, so the score is checked locally (D-7).
- Q: Does this change need a changelog fragment? → A: Yes. The constitution requires one fragment for each change (line 409), and it takes precedence over practice documents (line 529). The plan adds one fragment (D-8).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the install command that the bootstrap runs (Priority: P1)

A junior engineer creates a worktree and reads the setup guide. The guide names one install command, `uv sync --locked --extra dev`. The guide no longer describes a requirement-file install.

**Why this priority**: A reader who follows a retired install flow gets an environment that differs from the lock. This defect is the reason for the issue.

**Independent Test**: Read Step 2 and the installer section of `documentation/development-setup.md`. Confirm that the locked sync is named and that no retired statement remains.

**Acceptance Scenarios**:

1. **Given** Step 2 of the guide, **When** a reader finishes the step, **Then** the reader knows that the bootstrap runs `uv sync --locked --extra dev`.
2. **Given** the installer section, **When** a reader looks for a requirement-file install, **Then** the section says that the pip export files serve manual installs only.
3. **Given** the report text, **When** a reader compares it with the final console output, **Then** the quoted report line matches the script text exactly.

---

### User Story 2 - Check each installer setting against the script (Priority: P1)

A maintainer compares the setup guide with `scripts/bootstrap_worktree.py`. Each setting name, condition, and report line in the guide appears in the script under the same name and condition.

**Why this priority**: The defect came from drift between the guide and the script. The maintainer needs one list that both files satisfy.

**Independent Test**: Use `design/contracts/bootstrap-installer-flow.md`. Find each setting in the guide and in the script. Both sides match.

**Acceptance Scenarios**:

1. **Given** a setting named in the guide, **When** the maintainer searches the script, **Then** the script sets that name under the stated condition.
2. **Given** a setting that the script sets for a child process, **When** the maintainer searches the guide, **Then** the settings table names it.
3. **Given** the public index case, **When** the maintainer reads the guide, **Then** the guide names the public index, its trigger, and the pip configuration rule.

---

### User Story 3 - Confirm the writing score and the change scope (Priority: P2)

A reviewer runs the local STE gate on the changed guide and on the new fragment. The reviewer also lists the changed files.

**Why this priority**: The repository requires a score of 80 or above for each Markdown file. A wider change adds review work.

**Independent Test**: Run `ste-linter` on the two files. Run `git diff --name-only origin/main`. Both checks pass.

**Acceptance Scenarios**:

1. **Given** the changed guide and the fragment, **When** the reviewer runs `ste-linter`, **Then** each file scores 80 or above.
2. **Given** the finished branch, **When** the reviewer lists the changed files, **Then** the list holds exactly the guide and the fragment.

---

### Edge Cases

- uv is absent and the Python is externally managed: the bootstrap stops with the uv install message and returns status 1 (lines 132, 455, 901). The guide states that the bootstrap does not retry through pip.
- The configured index does not match `uv.lock`: the final message names the index mismatch, and the guide names `--public-lock-index`.
- `uv.lock` does not match `pyproject.toml`: the final message tells the operator to run `uv lock` on a branch and commit the lockfile (line 141).
- The configured index does not answer: the run uses the public index, and the guide names the child settings that change.
- The caller sets `PIP_EXTRA_INDEX_URL` and the public index applies: the child removes the extra index (line 428). The guide names this removal.
- The browser download fails: the bootstrap prints the repair command and returns status 0 (lines 903, 909). The existing browser section stays.
- pip configuration holds several extra index lines: the parser keeps one value (line 206). The guide does not describe this limit. `analysis.md` records it as a follow-up.

### Out of scope

- Changes to `scripts/bootstrap_worktree.py`, `scripts/bootstrap_worktree.ps1`, tests, and workflows.
- A description of `StaleSourceSweeper` (class at line 706, run at line 895). A separate issue covers it (D-5).
- The manual install commands that use `pip install -r` and `uv pip install` (D-2).
- Podman, Mist API, and Juniper device behavior.
- The deprecated uv names that the script sets, `UV_INDEX_URL` and `UV_EXTRA_INDEX_URL`. A separate issue covers the rename.
- The multi-value extra index limit at line 206.
- Edits to `CHANGELOG.md`, which a feature branch never edits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Step 2 text and the installer section MUST name `uv sync --locked --extra dev` as the install command.
- **FR-002**: The guide MUST remove each retired statement about requirement files, per-file attempts, and total time.
- **FR-003**: The installer section MUST name the uv discovery order, the install condition, and both lock messages.
- **FR-004**: The installer section MUST name `--public-lock-index`, which applies to one run and changes no pip configuration.
- **FR-005**: The settings table MUST name each setting that the script sets, with its condition.
- **FR-006**: The report text MUST quote the report line `Installed dependencies with uv sync --locked --extra dev.` exactly.
- **FR-007**: The guide MUST state that the pip export files serve manual pip installs and that the bootstrap installs neither file.
- **FR-008**: The guide and the new fragment MUST each score 80 or above with the local `ste-linter` gate.
- **FR-009**: The change MUST touch exactly two files: the guide and the new changelog fragment.

### Key Entities

Not applicable: the change edits documentation prose and stores no entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The guide names `uv sync --locked --extra dev` at least two times, in Step 2 and in the installer section.
- **SC-002**: No retired statement from FR-002 remains. The search returns no line.
- **SC-003**: The settings table names every setting in the contract that applies to a child process.
- **SC-004**: `ste-linter` scores both changed files at 80 or above.
- **SC-005**: The branch changes exactly the two files that FR-009 names.

## Assumptions

- Commit `f03c6c9b` on `main` is the source of truth. The local blobs of the cited files equal the remote blobs (R-02, R-14).
- The local `ste-linter` runs with the ASD-STE100 dictionary. The CI job runs without the dictionary (`.github/workflows/ste-lint.yml` lines 6 and 7).
- uv and pip behavior follows the upstream pages that `design/research.md` cites.
- The reader is a junior engineer, as the constitution requires. The guide keeps plain words.

### Terms

- **Locked sync**: the command `uv sync --locked --extra dev`.
- **Installer child process**: a child process that runs uv or pip.
- **Browser child process**: the child process that downloads Chromium.
- **Public index**: the URL `https://pypi.org/simple`.
- **Configured index**: the index that a `PIP_` variable or pip configuration names.
- **Pip export file**: `requirements.txt` or `requirements-dev.txt`.
- **Uv executable**: the uv program file.
- **Report line**: a line that the bootstrap prints at the end of a run.
- **Retired statement**: a sentence that the bootstrap no longer matches.
