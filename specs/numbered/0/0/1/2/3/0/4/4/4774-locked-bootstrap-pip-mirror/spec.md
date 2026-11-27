# Feature Specification: Locked Bootstrap With a Configured Pip Index

**Feature Branch**: `fix/4774-locked-bootstrap-pip-mirror`

**Created**: 2026-11-26

**Status**: Draft. The repair waits for owner decision D-1.

**Input**: GitHub issue #4774, "Runtime: locked bootstrap fails with a configured pip mirror".

## Clarifications

### Session 2026-11-26

- Q: Does the repair change `uv.lock`? A: No. The issue owner forbids a lock change (comment 6807911629). Comment 6903867178 also forbids transforming the lock to bypass D-1.
- Q: May this work contact the private mirror? A: No. The owner forbids any request to the private mirror (comment 6807911629).
- Q: Which index governs the locked sync when a configured index differs from the lock? A: HUMAN-DECISION-REQUIRED. The owner decides D-1. The plan uses option C until then.
- Q: Does the defect exist in the runtime package? A: No. At main, only `scripts/bootstrap_worktree.py` maps a configured index into uv settings (research.md, section 5).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete the locked sync with a configured index (Priority: P1)

An operator runs the worktree bootstrap on a host with a configured pip index. The locked sync completes. The operator adds no extra option.

**Why this priority**: The defect blocks each new worktree, so no test environment starts.

**Independent Test**: Run TST-01 and TST-07. Each test checks the child environment of the locked sync.

**Acceptance Scenarios**:

1. **Given** a configured index that differs from `uv.lock`, **When** the locked sync runs, **Then** the child receives the lock registry as its primary index.
2. **Given** the same state, **When** the child starts, **Then** no configured index appears in any `UV_` setting.

---

### User Story 2 - Keep the lock and the manifests unchanged (Priority: P1)

A maintainer trusts that the bootstrap never changes `uv.lock`, `pyproject.toml`, or the requirement exports.

**Why this priority**: The lock is the reproducible install record for the whole project.

**Independent Test**: Run TST-05. Review the pull request file list in T-PR.

**Acceptance Scenarios**:

1. **Given** the repair, **When** the pull request lists its files, **Then** no lock or manifest path appears.

---

### User Story 3 - Keep fallback, redaction, and the opt-in option (Priority: P2)

An operator behind a proxy keeps the public-only fallback, the credential redaction, and the `--public-lock-index` option.

**Why this priority**: These controls protect the operator from a dead mirror and from a credential leak.

**Independent Test**: Run KT-02, TST-08, and KT-04. TST-08 receives the edit listed in plan.md.

**Acceptance Scenarios**:

1. **Given** a configured index that does not answer, **When** the bootstrap runs, **Then** the public-only fallback applies.
2. **Given** a configured index with credentials, **When** the bootstrap writes logs, **Then** no credential appears in the logs.

---

### User Story 4 - Read the policy in the setup guide (Priority: P2)

A reviewer reads the source rule, the Caution text, and the changelog fragment.

**Why this priority**: The owner needs a written policy before the next worktree bootstrap.

**Independent Test**: Run TST-06 and KT-06.

**Acceptance Scenarios**:

1. **Given** the change, **When** a reader opens the Package sources section, **Then** the section states that the lock registry governs the locked sync.

### Edge Cases

- The configured index equals the lock registry. The bootstrap logs no Caution line.
- The configured index does not answer. The public-only fallback applies, as before.
- The caller sets `UV_INDEX_URL`. The child value becomes the lock registry. The parent value stays unchanged.
- `uv.lock` names no registry. The bootstrap stops before the locked sync and names the lock file.
- `uv.lock` names a second registry. TST-05 fails. The runtime reads only the first registry line (research.md, U-4).
- Public PyPI is blocked and the configured index answers. The locked sync fails with a network error. The bootstrap does not name a lock cause.
- The configured index value is empty. The bootstrap treats the value as absent.
- The repository path contains spaces (OneDrive). This change does not alter path handling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bootstrap MUST run `uv sync --locked --extra dev` from the worktree root.
- **FR-002**: The locked sync child MUST NOT receive a configured index as its primary index.
- **FR-003**: The locked sync child MUST use the registry recorded in `uv.lock` as its primary index. It MUST stop when no registry exists.
- **FR-004**: The bootstrap MUST log one Caution line, without any URL, when the configured index differs from the lock registry.
- **FR-005**: The change MUST NOT modify `uv.lock`, `pyproject.toml`, `requirements.txt`, or `requirements-dev.txt`.
- **FR-006**: The bootstrap MUST NOT add `--frozen`, skip the locked sync, or weaken `--locked`.
- **FR-007**: The bootstrap MUST NOT write any pip or uv configuration file.
- **FR-008**: The bootstrap MUST keep the caller environment unchanged in the parent process.
- **FR-009**: The public-only fallback MUST apply when the configured index does not answer.
- **FR-010**: The `--public-lock-index` option MUST keep its name and its arguments.
- **FR-011**: The bootstrap MUST report the original failure when the lock check reports no stale lock.
- **FR-012**: The stale-lock diagnosis MUST name lock drift only.
- **FR-013**: The development setup guide MUST describe the lock registry rule and the Caution text.
- **FR-014**: The change MUST add one changelog fragment named `issue-4774-locked-bootstrap-pip-mirror.md`.
- **FR-015**: Each behavior test that this change adds or rewrites MUST fail before the code change. A repository guard may pass before the change.
- **FR-016**: The new tests MUST NOT open a connection to any host other than the loopback address.
- **FR-017**: Logs, messages, and reports MUST NOT show a configured index URL, a host name, or a credential.
- **FR-018**: Each local gate that applies to the changed files MUST pass. Otherwise, the pull request MUST state its cause.
- **FR-019**: The pull request body MUST contain `Closes #4774`, the local gate results, and the removed-line count.

### Key Entities

- **Configured index**: the pip index from the caller environment or a pip file. It is never printed.
- **Lock registry**: the registry URL that `uv.lock` records.
- **Source decision**: the child-only source choice for one bootstrap run.

Details appear in `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The behavior tests fail on main at commit f03c6c9b and pass after the change.
- **SC-002**: On the owner Windows host, the default bootstrap exits with code 0 when a configured index is set. The owner records the uv version and the setting names on issue #4774.
- **SC-003**: The CI dependency lock step and the container guard pass without edits to their files.
- **SC-004**: The pull request file list matches the change map in `plan.md`.
- **SC-005**: Each applicable row of the local gates table reports its expected result.
- **SC-006**: The pull request closes issue #4774 and passes the Conventional Commits title check.

## Out of Scope

- Changing `uv.lock`, regenerating a lock for a private registry, or adopting `--frozen`.
- Adopting the uv proxy-index preview feature (option P).
- Removing the `--public-lock-index` option.
- Fixing the mistapi version wording drift (separate issue, D-11).
- Splitting `scripts/bootstrap_worktree.py` (separate issue, D-11).
- A Windows CI runner (D-10).
- The work of issues #4591, #4773, and #2746. Each keeps its own scope.

## Assumptions

- The lock registry stays `https://pypi.org/simple` for each package (research.md, R43 and R44).
- The owner selects option C, or the plan adapts to the option the owner selects.
- PyPI answers from the owner host for the locked sync. This is not verified (research.md, U-7).
- The owner uses uv 0.13.x. The owner reports versions 0.13.7 and 0.13.8. This is not verified (research.md, U-1).
- The bootstrap calls no Mist API. The mistapi pin does not affect this change (research.md, R41).
- The bootstrap keeps Python 3.15.2 selected through uv.

## Dependencies

- Owner decision D-1 must precede tasks T011 through T015.
