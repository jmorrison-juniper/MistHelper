# Feature Specification: Keep mando inside the radon requirement

**Feature Branch**: `fix/4894-mando-radon-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4894, "CI: quality-gate `pytest` failed (PR #4888)". Dependabot raised the pinned mando version from 0.7.1 to 0.8.2. The pip resolver cannot install requirements-dev.txt with that pin, because radon 6.0.1 requires mando below 0.8.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the quality gates installable (Priority: P1)

The CI runner installs requirements-dev.txt before each quality gate. The install must resolve. The mando pin stays at 0.7.1.

**Why this priority**: The install failure stopped 28 jobs in run 45064243269. It also stopped two Windows jobs. No gate reported a result for pull request #4888.

**Independent Test**: On the fix pull request, the `Dependency lock and exports` check and the four `pytest coverage shard` checks report success.

**Acceptance Scenarios**:

1. **Given** the fix pull request head, **When** CI runs the install step, **Then** pip resolves requirements-dev.txt without a ResolutionImpossible error.
2. **Given** the fix pull request head, **When** the export guard runs, **Then** the guard reports zero defects.

---

### User Story 2 - Stop Dependabot from proposing the blocked bump (Priority: P2)

Dependabot does not open a mando update pull request from the pip update block.

**Why this priority**: Dependabot already proposed the blocked bump. Without an ignore entry, it proposes the same bump on each weekly run.

**Independent Test**: The two guard tests in `TestDependabotPipIgnore` pass on the fix pull request head. Removing the ignore entry makes them fail.

**Acceptance Scenarios**:

1. **Given** the pip update block, **When** Dependabot reads it, **Then** Dependabot ignores every mando version update.
2. **Given** an ignore entry that names only some versions, **When** the guard tests run, **Then** `test_mando_ignore_blocks_every_version` fails.

---

### User Story 3 - Close the blocked pull request with a record (Priority: P3)

Pull request #4888 closes without a merge. The closing comment names the radon requirement and the fix pull request.

**Why this priority**: An open pull request keeps its failing checks visible. The closing comment explains why the bump cannot merge.

**Independent Test**: The GitHub read of pull request #4888 reports the state CLOSED and an empty merge time.

**Acceptance Scenarios**:

1. **Given** pull request #4888 is open, **When** the implementer closes it with the comment, **Then** its state is CLOSED and its merge time is empty.

---

### Edge Cases

- What happens when radon releases a version that accepts mando 0.8? The owner moves radon and mando through uv. The same pull request removes the ignore entry.
- What happens when Dependabot opens a mando pull request anyway? The `Dependency lock and exports` check fails. Close that pull request with the same comment used for pull request #4888.
- Caution: the ignore entry also blocks a mando 0.7.x update. Check mando advisories by hand until a release closes the gap.
- What happens when a developer edits requirements-dev.txt by hand? The export guard fails when the file differs from the uv output. Use uv to change a pin.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST keep mando at 0.7.1 in requirements-dev.txt, requirements.txt, and uv.lock.
- **FR-002**: The requirements-dev.txt install MUST resolve on the fix pull request head.
- **FR-003**: The pip update block in `.github/dependabot.yml` MUST ignore every mando version update.
- **FR-004**: The guard tests MUST fail when the mando ignore entry is missing or narrowed.
- **FR-005**: Pull request #4888 MUST close without a merge. The closing comment MUST name the radon requirement and the fix pull request.
- **FR-006**: The change MUST add one changelog fragment for issue #4894.
- **FR-007**: The change MUST NOT edit `.github/workflows/ci.yml`, `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, or `uv.lock`.
- **FR-008**: The record MUST name the failing check, the failing step, and the failing pip rule.
- **FR-009**: The fix pull request title MUST pass the Conventional Commits check. Its body MUST contain `Closes #4894`.
- **FR-010**: Each other defect from this review MUST have its own issue. The two defects are the fragment policy conflict and the changelog.d folder debt.

### Key Entities *(include if feature involves data)*

- **Pinned package**: A line in requirements-dev.txt that holds one version. Natural key: the package name.
- **Check**: A named status on a pull request. Natural key: the check name, such as `pytest (coverage gate)`.
- **Ignore entry**: An item under `ignore` in the pip update block. Natural key: the dependency name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The fix pull request shows success for `Dependency lock and exports`, `pytest (coverage gate)`, and the four `pytest coverage shard` checks.
- **SC-002**: The two new guard tests pass on the fix pull request head.
- **SC-003**: The fix pull request changes only the paths in the change map of plan.md.
- **SC-004**: Pull request #4888 has state CLOSED and an empty merge time.
- **SC-005**: Dependabot opens no mando update pull request in the first weekly pip run after the merge.

## Assumptions

- Dependabot reads requirements-dev.txt. The commit that opened pull request #4888 changed that file.
- Radon 6.0.1 is the latest radon release on PyPI. The PyPI record was read on 2026-11-26.
- A pinned mando version can lag radon until radon accepts a newer mando.

## Out of Scope

- Upgrading radon or mando.
- Changing the failing jobs or the CI workflow.
- Changing the changelog policy text. The separate issue under FR-010 owns that text.
- Changing the npm or GitHub Actions update blocks in dependabot.yml.
- Deploying the image after the merge. The owner runs the deployment.

## Clarifications

### Session 2026-11-26

- Q: Should the fix upgrade mando or keep it at 0.7.1? A: Keep 0.7.1. PyPI lists radon 6.0.1 as the latest release, and radon 6.0.1 requires mando below 0.8. See research D-1.
- Q: Should the change add a changelog fragment? A: Yes. The constitution requires one fragment for each change, and it supersedes practice documents. See research D-5.
- Q: Which pull request carries the fix? A: A new pull request from `fix/4894-mando-radon-pin`. Pull request #4888 closes without a merge. See research D-2.
- Q: Does a human decision block the work? A: No. The work involves no licensing, production data, credential, or product priority decision. See research.
