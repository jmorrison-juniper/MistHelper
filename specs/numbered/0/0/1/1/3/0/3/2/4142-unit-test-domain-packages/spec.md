# Feature Specification: Split tests/unit into domain packages

**Feature Branch**: `chore/4142-unit-test-domain-packages`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4142, "R-1: split tests/unit/ into domain packages (Juniper RMA debt C-1)".

**Baseline**: `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read on 2026-11-26.

## User Scenarios & Testing

### User Story 1 - Find tests by domain (Priority: P1)

An engineer finds a unit test by the product area that the test checks. Each grouping directory under `tests/unit/` holds five children or fewer.

**Why this priority**: A predictable tree helps engineers find and maintain tests. Debt C-1 blocks any new direct child under the root.

**Independent Test**: Count the direct children of `tests/unit/` and of each new grouping directory. Each count is five or fewer.

**Acceptance Scenarios**:

1. **Given** the final tree, **When** an engineer lists `tests/unit/`, **Then** the listing shows `__init__.py` and the containers `config`, `marvis`, `maps`, and `prod_readiness`.
2. **Given** any new grouping directory, **When** an engineer counts its direct children, **Then** the count is five or fewer.

### User Story 2 - Run the same unit tests after the moves (Priority: P1)

An engineer runs the same unit tests after the files move. No test disappears, and no test changes its result.

**Why this priority**: A reorganization that drops a test hides a defect.

**Independent Test**: Collect `tests/unit` before the first move and after each batch. Map each old node ID to its new path. The two sets match.

**Acceptance Scenarios**:

1. **Given** the baseline node IDs, **When** collection runs after a batch, **Then** each baseline node ID maps to exactly one collected node ID.
2. **Given** a CI selector, guard, or current document that names a moved path, **When** the batch completes, **Then** the reference names the new path.

### User Story 3 - Move only unowned paths (Priority: P1)

A maintainer moves a path only when no open pull request, exact claim, or planned edit holds it.

**Why this priority**: A move during active work causes conflicts and lost edits.

**Independent Test**: Compare each source path with the open pull request file lists and the issue comments on the day of the batch. Each held path stays in place.

**Acceptance Scenarios**:

1. **Given** an open pull request lists a test path, **When** a batch runs, **Then** the path remains at its current location.
2. **Given** an owner releases a held path, **When** the next batch runs, **Then** the path moves in that batch.

### Edge Cases

- A moved package contains a relative import. The import resolves only when the package moves as one unit.
- Two packages contain a test with the same file name. Package markers keep each module path unique.
- An open pull request adds a direct child to `tests/unit/`. The pull request must place its files inside a grouping directory.
- The local working tree holds untracked directories under `tests/unit/`. These directories are not on `main`, so no batch moves them.
- An open issue edits a file during a batch. The batch rebases onto the current file before it moves the file.
- A package marker exists in both the source and the destination. The source marker moves only when the destination has no marker.

## Requirements

### Functional Requirements

- **FR-001**: `tests/unit/` MUST contain no more than five direct children after the final batch.
- **FR-002**: Each new grouping directory MUST contain no more than five direct children, including package markers.
- **FR-003**: Test collection under `tests/` MUST yield every baseline node ID after path normalization.
- **FR-004**: Each active import, selector, lint rule, workflow, test-quality baseline entry, and current document MUST use the new path. Historical records MUST remain unchanged.
- **FR-005**: A moved test MUST keep its file content. A batch MAY change only a root path, a repository-root depth, or an import that a move requires.
- **FR-006**: A batch MUST NOT move a path that an open pull request owns, an exact claim names, or a planned edit names, until the owner releases the path.
- **FR-007**: A batch MUST NOT change executable code in `src/`, `web_portal/`, `Dockerfile`, or `Containerfile`. A batch MUST NOT change Mist API behavior.

### Key Entities

- **Test package**: A direct child of `tests/unit/` or of a grouping directory. It has a repository path, a child count, and a hold state.
- **Grouping directory**: A destination directory under a container. It has a parent and a child count.
- **Hold**: A reservation on a path. It has a type, an owner, and a release condition.
- **Batch**: A set of moves that one pull request carries.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `tests/unit/` has five or fewer direct children on the final `main` revision.
- **SC-002**: Each new grouping directory has five or fewer direct children on the final `main` revision.
- **SC-003**: Collection after the final batch yields every baseline node ID after path normalization.
- **SC-004**: Each moved test passes in the batch that moves it.
- **SC-005**: No open pull request loses or conflicts with a path that it owns.
- **SC-006**: A search of active files finds no old `tests/unit` path that a moved test replaced.

## Assumptions

- Test discovery stays recursive under `tests`. `pyproject.toml` lines 514 through 520 configure this behavior.
- The four containers on `main` keep their names. Each container gains one grouping directory for each source package.
- A path with a planned or claimed edit stays in place until its owner releases it.
- The local working tree differs from `main`. Only `main` counts as evidence.

## Clarifications

### Session 2026-11-26

- Q: Does a legacy record at the same route change this work? A: Yes. The legacy record is stale. This record reuses its folder name and replaces its claims.
- Q: Does an inventory mention in an open issue hold a path? A: No. Only an exact claim or a planned edit holds a path (D-2).
- Q: Does the historical link to `tests/unit/analytics/test_insight_metrics_utils.py` block its move? A: No. FR-004 keeps historical text unchanged, so the link becomes stale (D-3).
- Q: Does this change need a human decision? A: No. The change has no licensing, data destruction, credential, or product priority decision.
