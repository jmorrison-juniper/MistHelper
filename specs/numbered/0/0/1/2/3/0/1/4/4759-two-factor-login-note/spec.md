# Feature Specification: Correct interactive two-factor login notes

**Feature Branch**: `docs/4759-two-factor-login-note`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4759 "Docs: correct interactive two-factor login notes". The API page for `POST /api/v1/login/two_factor` states that MistHelper does not use interactive two-factor authentication. Merged pull request #4757 shows that the interactive login uses it. Correct the MistHelper-specific note. Do not change `README.md` in this issue.

## Terms

- **Two-factor code**: The code that Mist asks for after the password step.
- **Two-factor step**: The part of the interactive login that asks for the two-factor code.
- **Interactive login**: The email, password, and two-factor login that `--login` and menu 143 start.
- **API-token run**: A MistHelper run that authenticates with an API token from the environment or `.env`.
- **Upgrade capture portal**: The browser sign-in on port 8056.
- **Operations portal**: The web user interface on port 8055.
- **MistHelper Notes**: The final section of an API page in `documentation/api/`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a correct two-factor login note (Priority: P1)

An operator or engineer reads the MistHelper Notes section of `documentation/api/admins/POST_login_two_factor.md`. The note states where MistHelper asks for the two-factor code and where it sends the code. The note also states which runs never send the code.

**Why this priority**: The old note told readers that interactive two-factor login does not exist. That statement is false for the current code.

**Independent Test**: Read the note on `main`. Check each named prompt, call, and page against the remote checks in `design/research.md`.

**Acceptance Scenarios**:

1. **Given** the note on `main`, **When** a reader follows each named prompt, call, and page, **Then** each item matches a cited line.
2. **Given** the note on `main`, **When** a reader searches for the old statement, **Then** the search finds no match.

---

### User Story 2 - Find the release note for the correction (Priority: P1)

A release coordinator finds one release-note fragment for issue #4759 in `changelog.d/`. The fragment names the change type and the issue.

**Why this priority**: The repository requires one fragment for each change that a user sees.

**Independent Test**: Run the changelog guard test. It passes with the new fragment present.

**Acceptance Scenarios**:

1. **Given** the new fragment, **When** the changelog guard runs, **Then** no test fails.
2. **Given** the pull request, **When** a reviewer lists its files, **Then** the list holds the fragment and the record folder only.

---

### User Story 3 - Keep both login notes consistent (Priority: P2)

A reader of `documentation/api/admins/POST_login.md` sees the same verified paths as a reader of the two-factor page.

**Why this priority**: Pull request #4924 changed both notes. A mismatch between the notes misleads the reader.

**Independent Test**: Compare both MistHelper Notes with the remote checks for the prompts, the upgrade capture portal, and the operations portal.

**Acceptance Scenarios**:

1. **Given** both notes on `main`, **When** a reader compares the ports and the prompts, **Then** both notes agree.

---

### Edge Cases

- Caution: a branch cut from an old `main` restores the old note. Rebase the branch onto `main` before the commit.
- A fragment with the same name exists on `main`. Stop and report. Do not overwrite the file.
- The pull request opens after the fragment exists. Keep the fragment name. A rename creates a delete and an add.
- A gate fails. Repair the Markdown text and run the gate again. Do not lower the threshold.
- The owner hold stays active. Stop after T-LOCAL-GATES and report the state.
- A later pull request edits the same note line. Rebase and keep the verified text.
- The preserved candidate fragment cannot be found. Write the fragment from this specification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The two-factor note MUST name the interactive login, the SDK call that sends the code, and the upgrade capture portal page.
- **FR-002**: The two-factor note MUST state that an API-token run never sends the two-factor code.
- **FR-003**: The two-factor note MUST state that the operations portal has no page for the code.
- **FR-004**: No page in `documentation/` MUST state that MistHelper lacks interactive two-factor support.
- **FR-005**: The change MUST add `changelog.d/issue-4759-two-factor-login-note.md`, which follows `changelog.d/README.md`.
- **FR-006**: The branch MUST NOT change `README.md`, `CHANGELOG.md`, or any file outside the change manifest.
- **FR-007**: The `POST_login.md` note MUST name the same verified paths as the two-factor note.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: the change edits documentation and adds one fragment. It adds no REST request. The note documents `POST /api/v1/login/two_factor`, which the installed `mistapi` 0.64.1 sends from `login_with_return`.

### Key Entities *(include if feature involves data)*

Not applicable: the change edits prose and adds one file. It defines no data entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each named path in both notes matches one remote check marked present in `design/research.md`.
- **SC-002**: The changelog guard test file reports zero failures.
- **SC-003**: The STE gate scores each changed Markdown file at 80 or above.
- **SC-004**: The pull request lists only the change manifest, and each required check reports success.

## Out of Scope

- `README.md`. The issue names separate owners in #4208 and #4619.
- The SDK path on the two-factor page, `mistapi.api.v1.admins.login.twoFactor()`. It is a separate defect. See `analysis.md`.
- Reverting pull request #4924. The owner decides that question. See `analysis.md`.
- Browser sign-in for the operations portal. Issue #4936 tracks it.
- The 335 entries in `changelog.d/`. The constitution records that debt.

## Assumptions

- The owner hold in issue comment IC_kwDOQltU8c8AAAABm4cmpA stays active. No later owner comment lifts it.
- Main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` is the baseline. The local `HEAD` equals that commit.
- The installed `mistapi` 0.64.1 matches the pin `mistapi>=0.64.0,<0.65`.
- The change type is Fixed, because the earlier note stated a false fact.

## Clarifications

### Session 2026-11-26

- Q: Does `main` hold the corrected note? A: Yes. Blob `98aeb3e81b08c956dc1137f04a833f33220a7bb2` holds it at line 91. Commit `4e81b2a4a724e29476270564be927f797def82be` (pull request #4924) added it.
- Q: Does `main` hold a fragment for issue #4759? A: No. The repository tree holds no `changelog.d` path with 4759 in its name.
- Q: Is a pull request open for issue #4759? A: No. A search for 4759 returns no pull request.
- Q: Does any owner comment lift the hold? A: No. The last owner comment is IC_kwDOQltU8c8AAAABm4cmpA, dated 2026-11-16.
