# Tasks: Junos hardening skill

**Input**: Design documents from `specs/2754-junos-hardening-skill/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Documentation validation only. No application test changes are needed.

**Organization**: Tasks are grouped by user story so each story can be verified
separately.

## Phase 1: Setup

**Purpose**: Establish the source base and the worktree.

- [x] T001 Read issue #2754 and add the `in-progress` label. (delivered: GitHub issue #2754)
- [x] T002 Read issues #2393 and #2394 for the sibling skill standard. (delivered: issue review)
- [x] T003 Read repository instructions, coding standards, git workflow, STE guide, and constitution. (delivered: repository instructions)
- [x] T004 Create the `docs/2754-junos-hardening-skill` worktree from `origin/main`. (delivered: local worktree)

---

## Phase 2: Foundational source review

**Purpose**: Verify sources before writing the skill.

- [x] T005 Search for an existing Junos hardening skill in `.github/skills/`, the session skill list, and documentation. (delivered: `.github/skills/hardening-junos/references/source-index.md`)
- [x] T006 Verify repository security rules with file and line citations. (delivered: `.github/skills/hardening-junos/references/repository-decisions.md`)
- [x] T007 Verify Junos root authentication and zeroize claims against Juniper documentation. (delivered: `.github/skills/hardening-junos/references/junos-verified-rules.md`)
- [x] T008 Record unavailable external corpus details as unverified gaps. (delivered: `.github/skills/hardening-junos/references/validation-and-gaps.md`)

---

## Phase 3: User Story 1 - Answer a MistHelper Junos hardening question

**Goal**: Give a safe answer for ZTP, SSH, zeroize, and other MistHelper contact
points.

**Independent Test**: Read `SKILL.md` and confirm that it routes ZTP and zeroize
questions to cited references.

- [x] T009 Create `.github/skills/hardening-junos/SKILL.md`. (delivered: `.github/skills/hardening-junos/SKILL.md`)
- [x] T010 Add repository hardening decisions. (delivered: `.github/skills/hardening-junos/references/repository-decisions.md`)
- [x] T011 Add Junos verified rules. (delivered: `.github/skills/hardening-junos/references/junos-verified-rules.md`)

---

## Phase 4: User Story 2 - Select the correct source

**Goal**: Let a maintainer verify the source for each answer.

**Independent Test**: Read the source index and confirm each row has a title,
train or version, and path or URL.

- [x] T012 Add the source index. (delivered: `.github/skills/hardening-junos/references/source-index.md`)

---

## Phase 5: User Story 3 - Preserve known gaps

**Goal**: Keep missing corpus details visible.

**Independent Test**: Read the gap register and confirm it marks six PDF gaps as
unverified.

- [x] T013 Add validation and gap records. (delivered: `.github/skills/hardening-junos/references/validation-and-gaps.md`)

---

## Phase 6: Polish and validation

**Purpose**: Validate and deliver the documentation change.

- [x] T014 Add the release-note fragment. (delivered: `changelog.d/issue-2754-junos-hardening-skill.md`)
- [x] T015 Run the local gates from issue #2754.
- [x] T016 Run the STE linter on each Markdown file added by this feature.
- [ ] T017 Commit, push, open the pull request, wait for checks, merge, and verify issue closure.

## Dependencies and execution order

Setup tasks block source review. Source review blocks skill writing. Skill writing
blocks validation. Validation blocks the pull request.
