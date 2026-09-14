# Tasks: Source-grounded Mist API skill

**Input**: Design documents from `specs/2393-mist-api-skill/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Documentation checks and local repository gates are required.

## Phase 1: Setup

**Purpose**: Confirm the worktree, issue, and sources.

- [x] T001 Read GitHub issue #2393 and its comments.
- [x] T002 Inspect `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-mist-api-skill`.
- [x] T003 Verify the branch and preserve existing work by continuing the committed worktree.
- [x] T004 Read the repository instructions and constitution.
- [x] T005 Bootstrap the virtual environment and install `mistapi` version `0.64.0`.

---

## Phase 2: Source Verification

**Purpose**: Build the evidence needed for a source-grounded skill.

- [x] T006 Verify OpenAPI version, path count, operation count, tag count, and schema count.
- [x] T007 Verify `documentation/api/INDEX.md` counts and library-only stub count.
- [x] T008 Verify the installed SDK functions named by the skill.
- [x] T009 Verify the known missing SDK functions from issue #2717.
- [x] T010 Verify the AOSCX SDK module name against the installed SDK.

---

## Phase 3: Skill Documentation

**Purpose**: Improve the existing skill instead of adding a duplicate.

- [x] T011 Update `.github/skills/managing-mist-api/SKILL.md` with the current source hierarchy.
- [x] T012 Update `.github/skills/managing-mist-api/references/source-authority.md` with current counts and conflict rules.
- [x] T013 Update `.github/skills/managing-mist-api/references/endpoint-catalog.md` with current counts and hashes.
- [x] T014 Update `.github/skills/managing-mist-api/references/verification.md` with SDK conflict checks.
- [x] T015 Leave generated vendor files unchanged.

---

## Phase 4: SpecKit Records

**Purpose**: Record the feature contract and execution order.

- [x] T016 Create `specs/2393-mist-api-skill/spec.md`.
- [x] T017 Create `specs/2393-mist-api-skill/plan.md`.
- [x] T018 Create `specs/2393-mist-api-skill/tasks.md`.

---

## Phase 5: Validation and Delivery

**Purpose**: Prove the change and prepare the pull request.

- [x] T019 Run the STE linter on each written Markdown file.
- [x] T020 Run the required local repository gates.
- [x] T021 Add `changelog.d/issue-2393-mist-api-skill.md`.
- [ ] T022 Commit, push, open the pull request, and wait for checks.
- [ ] T023 Merge after all checks pass and verify issue closure.

## Dependencies and Execution Order

1. Complete setup before source verification.
2. Complete source verification before skill documentation.
3. Complete skill documentation before validation.
4. Complete validation before the commit.
5. Complete the pull request checks before merge.
