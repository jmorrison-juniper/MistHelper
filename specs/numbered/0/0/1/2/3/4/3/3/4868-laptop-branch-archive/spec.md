# Feature Specification: Laptop Branch Archive Verification

**Feature Branch**: `docs/4868-laptop-branch-archive`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue 4868, "Laptop archive 2026-11-21: 497 local-only branches preserved under archive/laptop-20261121/"

## Clarifications

### Session 2026-11-26

- Q: Which state decides whether an archived name exists? A: The state on origin, read with GitHub GET requests. Local git reads serve as a cross-check only.
- Q: Which names does the issue list? A: 491 archive refs under `archive/laptop-20261121/`, including one stash ref, and 6 rescue branches under `rescue/`. The issue count of 497 covers both sets.
- Q: What is a remote counterpart? A: A branch on origin with exactly the original branch name. An archive ref is never a remote counterpart.
- Q: May this work change any branch or GitHub item? A: No. Every command is a read. No branch is checked out, fetched into, renamed, or deleted.
- Q: Does a legacy record exist? A: No. No path with `4868-` exists on main or in the working tree.
- Q: Is a pull request linked to the issue? A: No. Two search hits match the number in unrelated text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm each archived name on origin (Priority: P1)

A maintainer reads the record before any cleanup. The record shows each archived name and its archive tip on origin.

**Why this priority**: The laptop is retired. Origin must hold each archived name before anyone relies on the archive.

**Independent Test**: Run the GET commands in `design/quickstart.md`. The archive listing must show 491 archive refs, and each one must match a listed name.

**Acceptance Scenarios**:

1. **Given** the issue lists archived names, **When** the archive listing runs, **Then** each archived name has one archive ref on origin with a tip.
2. **Given** a listed name has no archive ref, **When** the listing runs, **Then** the record marks that name absent.

---

### User Story 2 - Find archived names with no remote counterpart (Priority: P1)

A maintainer sees which archived names have no branch with the same name on origin.

**Why this priority**: Such a name exists on origin only as an archive ref. Removing that ref removes the only remote copy of the name.

**Independent Test**: Compare the names in `design/data-model.md` with the branch listing. The result must show 489 `none`, 1 `differs`, 6 `self`, and 1 `not applicable` counterpart state.

**Acceptance Scenarios**:

1. **Given** the branch listing, **When** each archived name is compared, **Then** each name has one counterpart state: none, differs, self, or not applicable.
2. **Given** the name `jmorrison-juniper-4200-migrate-mistwanperformance`, **When** its counterpart is compared, **Then** the record shows a same-name branch at a different tip.

---

### User Story 3 - Correct the issue count and list unverified claims (Priority: P2)

A maintainer sees that the issue count mixes two sets. The maintainer also sees each claim that the record cannot verify.

**Why this priority**: A wrong count sets a wrong cleanup scope. An unverified claim must not appear verified.

**Independent Test**: Read `analysis.md` and the Unverified list in `design/research.md`. Each item must give the count split or the unverified claim with its reason.

**Acceptance Scenarios**:

1. **Given** the issue count of 497, **When** the archive listing is compared with it, **Then** the record states 491 archive refs and 6 rescue branches.
2. **Given** the claim that no secret exists in the archived commits, **When** the record is read, **Then** the claim appears under Unverified with a reason.

---

### User Story 4 - Keep the deletion decision with a human (Priority: P2)

A maintainer sees that this work deletes no archive ref. A later deletion needs a human decision and a fresh verification.

**Why this priority**: Deleting an archive ref removes unique commits that origin may hold nowhere else.

**Independent Test**: Read decision D-8 in `design/research.md`. It must carry the human decision marker and name the rerun.

**Acceptance Scenarios**:

1. **Given** a request to delete an archive ref, **When** the record is read, **Then** the record routes the request to a human decision.

### Edge Cases

- What happens when GitHub returns HTTP 403 or 429? Wait 60 seconds and retry up to three times. Then mark the check unverified.
- What happens when origin lacks a listed name? Mark the name absent and list it in `analysis.md`.
- What happens when origin holds an archive ref that the issue does not list? Record it as an extra ref. This run found none.
- What happens when a same-name branch has another tip? Compare the tips and record the compare status.
- What happens when a stash source branch has no remote counterpart? Record the absence. The base commit of the stash stays unverified.
- What happens when a local branch tip differs from its archive tip? Record both tips. The archive tip is the record value.
- What happens when two archive refs share one tip? Record each shared tip group in `analysis.md`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST verify each archive ref on origin with a GET request.
- **FR-002**: The record MUST verify each rescue branch named in the issue on origin with a GET request.
- **FR-003**: The record MUST list the tip of each verified archive ref in `design/data-model.md`, with at least seven characters of its SHA.
- **FR-004**: The record MUST state the counterpart state of each archived name.
- **FR-005**: The record MUST count archive refs and rescue branches in separate totals.
- **FR-006**: The record MUST state the difference between the issue count of 497 and the verified count.
- **FR-007**: The record MUST cross-check local branch names with read-only git commands only.
- **FR-008**: The record MUST NOT check out, fetch into, rename, reset, or delete any branch or ref.
- **FR-009**: The record MUST NOT comment on, label, edit, close, or create any GitHub item.
- **FR-010**: The record MUST list each claim that it cannot verify, with the reason.
- **FR-011**: The record MUST route any deletion of an archive ref to a human decision.
- **FR-012**: The record MUST use the managed route under `specs/numbered/` and keep each directory at five children or fewer.
- **FR-013**: Each Markdown file of the change MUST score 80 or above in the STE gate.
- **FR-014**: The change MUST add one changelog fragment under `changelog.d/`.
- **FR-015**: The record MUST contain no placeholder text.

### Key Entities

- **Listed name**: One entry of the 497-entry list in the issue body. It is an original branch name, or a full rescue branch name.
- **Archived name**: The listed name without the prefix `archive/laptop-20261121/`. This record counts 491 archived names. One of them is `stash-0`.
- **Archive ref**: The full ref `refs/heads/archive/laptop-20261121/` followed by the archived name.
- **Rescue branch**: A listed name that starts with `rescue/uncommitted-20261121-`. It is a branch on origin, not an archive ref.
- **Remote counterpart**: A branch on origin with exactly the original branch name. An archive ref is never a remote counterpart.
- **Counterpart state**: One of four values. `none` means no remote counterpart. `differs` means a remote counterpart at another tip. `self` means a rescue branch. `not applicable` means the stash ref.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The archive listing shows 491 of 491 archive refs named in the issue.
- **SC-002**: The branch listing shows 6 of 6 rescue branches named in the issue.
- **SC-003**: The record gives a counterpart state for all 497 listed names. The states total 489 none, 1 differs, 6 self, and 1 not applicable.
- **SC-004**: The remote check count in the status file equals the row count of the remote table in `design/research.md`.
- **SC-005**: The local branch count and the origin archive count match before and after the verification.
- **SC-006**: Each Markdown file of the change scores 80 or above in the STE gate.

## Assumptions

- The issue body reflects the laptop state on 2026-11-21.
- Origin is `jmorrison-juniper/MistHelper` on github.com.
- The configured GitHub account has read access to the repository.
- Archive refs do not change after the verification date. A later change needs a rerun of the quickstart checks.
- The local checkout serves as a cross-check. It does not prove the laptop state.

## Out of Scope

- No deletion, rename, force push, or restore of any archive ref or rescue branch.
- No review of archived commit content and no secret scan.
- No reading of the notes in other repositories that the issue names.
- No change to code, CI workflows, branch protection, or repository settings.
- No retention decision. A human makes that decision (D-8).

Warning: deleting an archive ref can remove the only remote copy of its unique commits. Keep every archive ref until a human approves its removal.

Caution: a local branch can hold different commits than its archive ref. Use the archive tip as the record value.
