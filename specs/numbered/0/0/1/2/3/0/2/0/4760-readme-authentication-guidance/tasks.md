# Tasks: README Authentication Guidance

**Input**: `specs/numbered/0/0/1/2/3/0/2/0/4760-readme-authentication-guidance/`

**Prerequisites**: `spec.md`, `plan.md`, `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

**Tests**: No new runtime tests are needed for this documentation-only change. Existing guards check links, fragment format, and managed spec routes.

**Organization**: Tasks follow the independent user stories. The README tasks run in order because both edit the same file.

## Phase 1: Setup

**Purpose**: Confirm the source evidence and feature scope.

- [x] T001 Confirm current authentication evidence in `specs/numbered/0/0/1/2/3/0/2/0/4760-readme-authentication-guidance/design/research.md` (delivered: `specs/numbered/0/0/1/2/3/0/2/0/4760-readme-authentication-guidance/design/research.md`).

## Phase 2: Foundational

**Purpose**: No shared runtime prerequisite applies to this documentation-only change.

## Phase 3: User Story 1 - Choose an authentication method (Priority: P1)

**Goal**: Help an operator choose token authentication or interactive email and password sign-in.

**Independent Test**: Review the README Who section and confirm it describes both methods and the conditional two-factor prompt.

### Implementation

- [x] T002 [US1] Update only the `README.md` Who authentication paragraph to name API-token use, interactive `--login`, email and password, the conditional verification-code prompt, and the command-line reference link (delivered: `README.md`).

## Phase 4: User Story 2 - Understand token handling (Priority: P2)

**Goal**: Explain local token storage and HTTPS transmission to Mist.

**Independent Test**: Review the README Where section and confirm it describes the authorization header without claiming that the token stays on the host.

### Implementation

- [x] T003 [US2] Update only the `README.md` Where authentication paragraph and Step 2 credential setup to state that token requests send the token to Mist over HTTPS and that an API token is optional for `--login`, while preserving unrelated README text (delivered: `README.md`).
- [x] T004 [P] [US2] Add `changelog.d/issue-4760-readme-authentication-guidance.md` with one `Changed` bullet that names issue #4760 (delivered: `changelog.d/issue-4760-readme-authentication-guidance.md`).

## Phase 5: Polish and Validation

**Purpose**: Verify the exact text scope and run the applicable documentation guards.

- [x] T005 Compare `README.md` with the base revision and confirm that only the Who, Where, and Step 2 authentication guidance changed (delivered: `README.md`).
- [x] T006 Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py` and `ste-linter --config .ste-linter.toml --min-score 80 README.md` (delivered: `README.md`).

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 is complete and records the source evidence.
- **Foundational**: No tasks apply.
- **User Story 1**: T002 can start after setup.
- **User Story 2**: T003 follows T002 because both edit `README.md`. T004 can run in parallel with T003 because it edits another file.
- **Polish**: T005 and T006 follow all implementation tasks.

### Parallel Opportunities

- T003 and T004 can run in parallel after T002.
- No other tasks can run in parallel without touching the same file.

## Implementation Strategy

Complete User Story 1 first. Then update the token-handling paragraph and the issue release fragment. Run the exact-scope review and the documentation guards before commit.
