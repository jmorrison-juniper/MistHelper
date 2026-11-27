# Tasks: Release Publication

**Input**: Design documents in `specs\numbered\0\0\1\2\3\0\1\1\4756-release-publication\`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`

**Tests**: TEST-1 to TEST-5 are defined in `analysis.md`. TEST-1 to TEST-3 are existing guard tests. TEST-4 and TEST-5 are checks that the implementer and the owner run.

**Ownership**: The agent performs T001 to T-MERGE. The owner performs OWN-001 to OWN-005. The agent creates no tag and no release (FR-018).

**Environment**: Run Python from the `.venv` of the release worktree. Run `gh` only after the two environment lines in `design/quickstart.md`.

## Format

- **[P]**: The task can run in parallel with another task of its phase. No task in this list qualifies.
- **Requirements**: The `FR` IDs from `spec.md` that the task satisfies.
- **Files**: The exact repository paths that the task reads or changes.
- **Verification**: One command from the local gates table, or one read-only command for an owner step. Plan Verification Approach explains the owner exception.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Preflight

**Purpose**: Confirm each gate and record the inventory before the branch opens.

### T001 Confirm the preconditions and the inventory

- **Requirements**: FR-016, FR-017
- **Files**: `changelog.d/` (read), `CHANGELOG.md` (read)
- **Acceptance**: PR 4208 is merged or closed. The main head, the fragment count, and the absent tag and branch are recorded.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: partial. The inventory at `f03c6c9` is in `design/research.md`. The re-check is pending.

### T002 Create the release branch from origin/main

- **Requirements**: FR-005
- **Files**: `CHANGELOG.md`, `changelog.d/`
- **Acceptance**: A worktree holds the branch `release/4756-release-publication` at the current `origin/main` commit. The bootstrap completes.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T003 Set the release stamp

- **Requirements**: FR-004
- **Files**: `CHANGELOG.md` (heading to write)
- **Acceptance**: The stamp is UTC and sorts after `26.11.21.06.27`. No tag matches the release tag. The release date is the UTC date of the stamp.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

## Phase 2: Release Section

**Purpose**: Collect every fragment into one section and delete the collected fragments.

### T004 Write the section text from every fragment

- **Requirements**: FR-001
- **Files**: `changelog.d/*.md` (read), `test-artifacts/release-4756/section.md` (write, not committed)
- **Acceptance**: One entry exists for each fragment, in ordinal name order. Each entry heading uses level three. Bullets and issue links stay unchanged. Each relative link resolves from the root.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T005 Insert the section into CHANGELOG.md

- **Requirements**: FR-001, FR-003, FR-014
- **Files**: `CHANGELOG.md`
- **Acceptance**: The section sits after line 14 and before the `26.09.28.19.49` heading. The Unreleased section is empty. Lines 1 to 14 keep their bytes.
- **Verification**: `python -m pytest tests/guardrails/test_markdown_links.py`
- **Status**: absent

### T006 Delete the collected fragments

- **Requirements**: FR-002
- **Files**: `changelog.d/*.md` except `changelog.d/README.md`
- **Acceptance**: `changelog.d/` holds `README.md` only. The count of deleted files equals the count of entries in the section.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T007 Reconcile the release section

- **Requirements**: FR-001, FR-014, FR-015
- **Files**: `CHANGELOG.md`, `changelog.d/`, `pyproject.toml` (read)
- **Acceptance**: TEST-4 reports zero differences. The changed paths are `CHANGELOG.md` and the deleted fragments only. `pyproject.toml` keeps version `2.1.0`.
- **Verification**: `python -m pytest tests/guardrails/test_markdown_links.py`
- **Status**: absent

## Phase 3: Gates and Pull Request

**Purpose**: Prove the change locally, open the release pull request, and merge it through the serial slot.

### T-LOCAL-GATES Run the local gates

- **Requirements**: FR-007
- **Files**: `CHANGELOG.md`, `changelog.d/`
- **Acceptance**: TEST-1, TEST-2, and TEST-3 pass on the worktree. The results go into the pull request body.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T-PR Open the release pull request

- **Requirements**: FR-005, FR-006, FR-017, FR-018
- **Files**: `CHANGELOG.md`, `changelog.d/`
- **Acceptance**: The branch pushes without force. The title uses the release scope. The labels are `chore` and `docs`. The body holds `Closes #4756`, the fragment count, the gate results, and the template answers.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T-REMOTE-CI Watch the required checks

- **Requirements**: FR-008
- **Files**: `.github/workflows/ci.yml` (read)
- **Acceptance**: All 15 required checks report success on the head commit. A failed check stops T-MERGE until its cause is repaired.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T-MERGE Merge through the serial slot

- **Requirements**: FR-009, FR-018
- **Files**: `CHANGELOG.md`, `changelog.d/`
- **Acceptance**: The orchestrator authorizes the merge. No other merge is in flight. The inventory matches the collected set. The `auto-merge` label squash merges the pull request.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

## Phase 4: Owner-Only Release Steps

**Purpose**: Publish and verify the release. The agent does not run these steps.

### OWN-001 Tag the release merge commit

- **Requirements**: FR-010
- **Files**: `CHANGELOG.md` (the tagged tree holds the release section). The step creates a Git tag on the release merge commit.
- **Acceptance**: The remote tag peels to the release merge commit SHA. The owner uses that SHA, not the current `main` head.
- **Verification**: `git ls-remote --tags origin $TAG`
- **Status**: absent

### OWN-002 Confirm the release workflow

- **Requirements**: FR-011
- **Files**: `.github/workflows/release.yml`
- **Acceptance**: The workflow for the release tag ends with success. A failed job is rerun only after its cause is known.
- **Verification**: `gh run watch $RUN_ID --repo jmorrison-juniper/MistHelper --exit-status`
- **Status**: absent

### OWN-003 Confirm the three assets

- **Requirements**: FR-011
- **Files**: `.github/workflows/release.yml` (lines 151 to 154 select the assets)
- **Acceptance**: The release lists one wheel, one source archive, and one ZIP named with the stamp.
- **Verification**: `gh release view $TAG --repo jmorrison-juniper/MistHelper --json assets --jq '.assets[].name'`
- **Status**: absent

### OWN-004 Confirm the container tags, digests, and revision label

- **Requirements**: FR-012
- **Files**: `.github/workflows/release.yml` (line 90 sets the `latest` tag), `Containerfile` (line 27 sets the version label)
- **Acceptance**: The stamp tag and the `latest` tag share one digest. The revision label equals the release merge commit. The observed version label is recorded.
- **Verification**: `podman image inspect ghcr.io/jmorrison-juniper/misthelper:$STAMP --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'`
- **Status**: absent

### OWN-005 Set the release title and body

- **Requirements**: FR-013
- **Files**: `CHANGELOG.md` (the release body links to this file at the tag). The step edits the GitHub release text.
- **Acceptance**: The title starts with the release tag, a space, a hyphen, and a space. The body keeps the compare link and the CHANGELOG link.
- **Verification**: `gh release view $TAG --repo jmorrison-juniper/MistHelper --json name --jq .name`
- **Status**: absent

## Dependencies and Execution Order

- T001 must finish before T002. T002 must finish before T003, and T003 before T004.
- T004 feeds T005. T005 and T006 must finish before T007.
- T007 and T-LOCAL-GATES must pass before T-PR. T-PR must finish before T-REMOTE-CI.
- T-REMOTE-CI must pass before T-MERGE. The orchestrator authorizes T-MERGE.
- OWN-001 starts after T-MERGE. OWN-002 waits for OWN-001. OWN-003 to OWN-005 wait for OWN-002.

## Counts

- Agent tasks: 11 (T001 to T007 and four final tasks).
- Owner-only tasks: 5 (OWN-001 to OWN-005).
- Total tasks: 16.
