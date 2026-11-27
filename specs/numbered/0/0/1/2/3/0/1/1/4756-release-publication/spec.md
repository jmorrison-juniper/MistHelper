# Feature Specification: Release Publication

**Feature Branch**: `release/4756-release-publication`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4756, "chore(release): publish release v26.11.10.22.38". Publish a release from current `main` after its release-note fragments enter `CHANGELOG.md`.

## Clarifications

### Session 2026-11-26

- Q: Which release tag applies? A: Not `v26.11.10.22.38`. The release tag is `v` plus a release stamp that the release branch sets when it opens. The issue tag equals the issue creation time, and it sorts before `v26.11.21.06.27`. Research D-1 and remote checks RC-02 and RC-59 support this answer.
- Q: Which fragments does the release collect? A: Every fragment on `main` when the release branch opens. At commit `f03c6c9`, that count is 334. Research D-2 and RC-15 support this answer.
- Q: Which branch carries the `CHANGELOG.md` change? A: `release/4756-release-publication`. The changelog guard allows a `CHANGELOG.md` edit only on a `release/` head. Research D-3 and RC-35 support this answer.
- Q: Does the agent tag, publish, or edit the release? A: No. The owner performs those steps. Research D-8 supports this answer.
- Q: Does the release wait for PR 4208? A: Yes. The owner hold stands until PR 4208 merges or closes. The owner makes that decision. Research D-6 records this as HUMAN-DECISION-REQUIRED.
- Q: Which package version applies? A: The package version stays `2.1.0`. Research D-5 and RC-41 support this answer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect the release notes into one section (Priority: P1)

A release maintainer opens a release branch from `main`. The maintainer copies each fragment into one new release section in `CHANGELOG.md`. The maintainer then deletes each collected fragment from `changelog.d/`.

**Why this priority**: The owner acceptance criteria require this result. Without it, `changelog.d/` keeps its fragments, and `CHANGELOG.md` has no record for the release.

**Independent Test**: Run TEST-4. It proves that the section holds one entry for each deleted fragment. It also proves that only `CHANGELOG.md` and `changelog.d/` changed.

**Acceptance Scenarios**:

1. **Given** `main` holds 334 fragments, **When** the maintainer completes T004 to T006, **Then** `CHANGELOG.md` holds one release section with 334 entries.
2. **Given** a fragment with a level-one heading, **When** the maintainer copies it, **Then** its entry uses a level-three heading and unchanged bullets.
3. **Given** the release section, **When** TEST-2 runs, **Then** every relative link in the section names an existing file.

### User Story 2 - Merge the release pull request through the serial slot (Priority: P1)

The maintainer opens the release pull request. The maintainer waits for the 15 required checks. After the orchestrator authorizes the merge, the maintainer adds the `auto-merge` label.

**Why this priority**: `main` enforces strict up-to-date checks and linear history (RC-22). A stale branch or a second merge in flight can break the required checks.

**Independent Test**: TEST-1, TEST-2, and TEST-3 pass locally and in the required checks.

**Acceptance Scenarios**:

1. **Given** the release branch is current, **When** all 15 required checks pass, **Then** the `auto-merge` label squash merges the release pull request as one commit.
2. **Given** `main` advances before the merge, **When** the fragment inventory changes, **Then** the maintainer repeats T004 to T007 before the merge.

### User Story 3 - Publish and verify the release (Priority: P1, owner-only)

The owner creates an annotated tag on the release merge commit. The owner watches the release workflow, verifies the three assets and the container tags, and sets the release title and body.

**Why this priority**: The issue goal is a published release. The agent cannot publish a release, so the owner completes these steps.

**Independent Test**: TEST-5 passes after OWN-001 to OWN-005 complete.

**Acceptance Scenarios**:

1. **Given** the release merge commit, **When** the owner pushes the release tag, **Then** `release.yml` starts, because its trigger matches `v*.*.*` (RC-23).
2. **Given** a successful release workflow, **When** the owner lists the assets, **Then** the release holds the wheel, the source archive, and the standalone ZIP.
3. **Given** the stamp and `latest` container tags, **When** the owner compares digests and the revision label, **Then** both digests match and the revision label equals the release merge commit.

### User Story 4 - Keep the record accurate for the owner (Priority: P2)

The record names each premise in the issue that current evidence contradicts.

**Independent Test**: Research rows RC-02, RC-05, RC-15, RC-17, and RC-60 show the current state.

**Acceptance Scenarios**:

1. **Given** the issue body names `v26.09.28.19.49` as the latest release, **When** the owner reads the record, **Then** the record states that `v26.11.21.06.27` is the latest release.

### Edge Cases

- What happens when a fragment merges after the inventory? The maintainer repeats T004 to T007 on a rebased branch before T-MERGE.
- What happens when PR 4208 merges before T-PR? Its fragment `pr-4208.md` enters the collection. The count changes, so the maintainer recounts.
- What happens when a copied entry holds a relative link? The link breaks at the repository root. The maintainer rewrites it to resolve from the root. TEST-2 fails until the rewrite is complete.
- What happens when the release stamp equals an existing tag? The maintainer chooses a later stamp. Quickstart Scenario 2 must show no matching tag first.
- What happens when the generated release body exceeds 125,000 code points? `scripts/release_body.py` uses the summary form (RC-39). The owner keeps that form.
- What happens when the merge starts a container build? `auto-merge.yml` dispatches `container-build.yml` after a merge (RC-31). That build pushes an image with an automatic stamp and moves `latest` (RC-30). The release workflow moves `latest` again. The owner records both builds.
- What happens when the release workflow fails? The owner reruns the workflow after the cause is known. The owner does not delete the tag first.
- What happens when `main` advances between the merge and the tag? The owner tags the release merge commit by its SHA, not the current `main` head.
- What happens when `Closes #4756` closes the issue before the owner steps finish? The summary comment lists OWN-001 to OWN-005 as open. The owner tracks them there.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The release MUST collect every fragment on `main` at branch time into one release section in `CHANGELOG.md`.
- **FR-002**: The release MUST delete each collected fragment and keep `changelog.d/README.md`.
- **FR-003**: The release MUST keep the `## [Unreleased]` heading and leave its section empty.
- **FR-004**: The release MUST use a release stamp in UTC form `YY.MM.DD.HH.MM`. The stamp MUST sort after `26.11.21.06.27` and match no existing tag.
- **FR-005**: Every `CHANGELOG.md` edit MUST happen on the branch `release/4756-release-publication`, created from `origin/main`.
- **FR-006**: The release pull request MUST use a Conventional Commits title, MUST contain `Closes #4756`, and MUST state the fragment count and the gate results.
- **FR-007**: The implementer MUST run each local gate that applies before the push.
- **FR-008**: The release pull request MUST pass all 15 required checks before the `auto-merge` label is added.
- **FR-009**: The release pull request MUST merge only after the orchestrator authorizes the merge and no other merge is in flight.
- **FR-010**: The owner MUST create an annotated release tag on the release merge commit and push it.
- **FR-011**: The release workflow MUST publish the wheel, the source archive, the standalone ZIP, and the container image.
- **FR-012**: The owner MUST confirm that the stamp and `latest` container tags share one digest and that the revision label equals the release merge commit.
- **FR-013**: The owner MUST set a release title and body. The body MUST keep the compare link and the CHANGELOG link.
- **FR-014**: The `CHANGELOG.md` change MUST add the release section only. No other existing line may change.
- **FR-015**: The package version in `pyproject.toml` MUST stay `2.1.0`.
- **FR-016**: The record MUST state each premise in the issue that current evidence contradicts.
- **FR-017**: The agent MUST NOT open the release pull request until PR 4208 merges or closes and the orchestrator authorizes the work.
- **FR-018**: The agent MUST NOT create a tag, a release, or a comment on GitHub. The agent performs only the pull request creation in T-PR and the label change in T-MERGE.

### Mist Cloud Transport Requirements

Not applicable: this release changes no Mist Cloud request, no WebSocket transport, and no mistapi call. The release uses GitHub and container registry operations only.

### Key Entities

- **Release stamp**: The text `YY.MM.DD.HH.MM` in UTC. It names the release and sorts as text.
- **Release tag**: The text `v` plus the release stamp. It names one annotated Git tag.
- **Fragment**: One Markdown file in `changelog.d/`. It holds the release note for one change. Its name uses an issue number and a slug, a pull request number, or a date and a slug.
- **Release section**: The new block in `CHANGELOG.md` below the `## [Unreleased]` heading. It holds one entry for each collected fragment.
- **Entry**: One level-three block in the release section. The maintainer copies it from one fragment.
- **Release pull request**: The pull request from `release/4756-release-publication` to `main`.
- **Release merge commit**: The single squash commit that the release pull request creates on `main`.
- **Owner hold**: The owner comment that blocks release preparation until 14 listed pull requests merge or close. Thirteen merged. PR 4208 is open.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the release merge, `changelog.d/` holds only `README.md`. The count of deleted fragments equals the count recorded at branch time.
- **SC-002**: The release section holds one entry for each deleted fragment. Each fragment body line appears in the section, in the same order.
- **SC-003**: TEST-1, TEST-2, and TEST-3 pass locally and in the 15 required checks.
- **SC-004**: The release tag names the release merge commit, and the release workflow ends with success.
- **SC-005**: The release holds three assets. The stamp and `latest` tags share one digest. The revision label equals the release merge commit.
- **SC-006**: The release title starts with the release tag, a space, a hyphen, and a space. The release body keeps the compare link and the CHANGELOG link.

## Assumptions

- The owner keeps write access to push tags and edit releases.
- The orchestrator authorizes T-PR and T-MERGE in separate steps.
- The public image pulls work without a credential, as the documented pull command shows (RC-66). Unverified: U-1.
- `main` stays at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` until the branch opens. If it moves, the inventory repeats.

## Out of Scope

- Product code, tests, and workflow files.
- The package version in `pyproject.toml`.
- Branch protection, required checks, and queue settings.
- Deployment of the release image. Constitution Principle IV step 12 is outside this issue (RC-63).
- Deletion of any tag, release, or image version.
- Content changes in PR 4208, PR 4813, or the dependency pull requests.
- The merge-triggered container build (research D-11). A separate issue must track that change.
