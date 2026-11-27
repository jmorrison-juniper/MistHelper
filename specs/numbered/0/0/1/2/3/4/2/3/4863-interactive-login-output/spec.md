# Feature Specification: Interactive Login Output

**Feature Branch**: `fix/4863-interactive-login-output`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4863, "fix: keep interactive login prompts outside warning logs". The interactive login writes banners, status lines, and success lines as warning records. The mistapi SDK also prints its own success lines at INFO level.

## Clarifications

### Session 2026-11-26

- Q: Should progress lines print to the terminal? A: No. The issue requires progress to stay in info and debug records. Each progress line writes one info record. Five progress lines duplicate an info record that already exists, so they are removed.
- Q: Which channel do banners, menus, and success lines use? A: Direct output through the `echo` helper. The helper prints the text and writes one info record. The console handler drops that record, so the terminal shows the text once.
- Q: Do failure lines leave the warning channel? A: No. A failure line reports a real problem. It keeps its warning or error record, so the operator still sees a label.
- Q: Which login path shows the MSP picker? A: Only the switch to interactive login, menu 143. The `--login` startup path calls the orchestrator and does not call the MSP picker.
- Q: Which console threshold does an operator use? A: The sample file sets `CONSOLE_LOG_LEVEL=20`. The code default is 20 when the variable is unset. An operator checkout can set 30 in its git-ignored `.env` file. The fix works at each threshold.
- Q: Does the fix change login results or SDK calls? A: No. Only the `console_log_level` argument changes, from 20 to 30.

## Terms

- **Direct output**: Text that the `echo` helper prints to the terminal. The helper also writes one info record.
- **Info record**: A log record at INFO level, written by `logger.info`.
- **Warning record**: A log record at WARNING level, written by `logger.warning` or `logging.warning`.
- **Progress line**: Text that tells the operator that a step started. It writes one info record and no direct output.
- **Success line**: Text that reports a completed step. It uses direct output and carries no warning label.
- **Failure line**: Text that reports a failed step or an invalid input. It keeps its warning or error record.
- **SDK console**: The `console` object of the `mistapi` package. It prints lines with a level label such as INFO.
- **Console level**: The `console_log_level` value of the SDK console. The interactive login sets this value.
- **Interactive login**: The email and password login, with a 2FA code when the account requires one. It starts with `--login` or menu 143.
- **2FA code**: The second factor that the operator types when the account requires it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the cloud menu and login banners as plain text (Priority: P1)

An operator starts `--login`. The cloud menu and the login banners appear as plain text, with no warning label. The operator reads each prompt and types each answer.

**Why this priority**: The operator reads these lines before every login. A warning label makes a normal step look like a problem.

**Independent Test**: Run the cloud picker and the banner code with a fake input function. Capture the terminal output and the log records. Verify that the banner text appears in the output and that no warning record exists.

**Acceptance Scenarios**:

1. **Given** the operator starts the interactive login, **When** the cloud menu appears, **Then** each menu line prints as direct output and no warning record exists.
2. **Given** the account requires a 2FA code, **When** the 2FA banner appears, **Then** the banner prints as direct output before the 2FA prompt.
3. **Given** the operator presses Enter at the cloud prompt, **When** the default cloud is chosen, **Then** the selection line prints as direct output.

---

### User Story 2 - See login and 2FA success without a warning label (Priority: P1)

After Mist accepts the login, the operator sees one login success line. For an account with 2FA, the operator also sees one 2FA success line. The SDK does not print its own success lines.

**Why this priority**: Success lines confirm the login. A warning label or a duplicate SDK line makes the operator doubt the result.

**Independent Test**: Run the login sequence with a fake SDK session that requires a 2FA code. Verify that the output holds one 2FA success line and one login success line. Verify that no SDK success line appears.

**Acceptance Scenarios**:

1. **Given** Mist accepts the password and the 2FA code, **When** the login ends, **Then** both success lines print as direct output.
2. **Given** Mist refuses the 2FA code, **When** the login ends, **Then** no 2FA success line prints, and the failure line keeps its warning record.
3. **Given** the SDK accepts a password login, **When** the SDK would print a success line, **Then** the console level of 30 hides that INFO line.

---

### User Story 3 - Read login progress in the log file (Priority: P2)

An engineer reads `data/script.log` to trace a login. Each progress step appears as an info record. The terminal does not show the same progress text twice.

**Why this priority**: Progress records help an engineer trace a failure. Duplicate lines add noise to the operator terminal.

**Independent Test**: Run the login with caplog at INFO level. Verify that each progress step writes one info record and that no progress step writes a warning record.

**Acceptance Scenarios**:

1. **Given** the login starts authentication, **When** the step begins, **Then** one info record names the host, the account, and the cloud.
2. **Given** the operator cancels the switch to interactive login, **When** the cancel is recorded, **Then** the record is an info record.

---

### User Story 4 - See the MSP picker as plain text (Priority: P2)

After an interactive login with MSP grants, the operator sees the MSP picker banner, the MSP menu, and each selection result as plain text. Invalid input still shows a warning label.

**Why this priority**: The picker is a prompt. The same warning labels that affect the login also affect the picker.

**Independent Test**: Run the picker with fake input. Verify the banner and the menu in the output. Verify that the invalid input path still writes a warning record.

**Acceptance Scenarios**:

1. **Given** the account has MSP grants, **When** the picker opens, **Then** the banner and the numbered menu print as direct output.
2. **Given** the operator chooses an organization, **When** the choice is saved, **Then** the selected organization lines print as direct output.
3. **Given** the operator types an invalid MSP number, **When** the picker reads the input, **Then** the invalid selection line keeps its warning record.

---

### User Story 5 - Keep secrets out of output and logs (Priority: P1)

A security reviewer confirms that a password and a 2FA code never appear in direct output or in any log record.

**Why this priority**: The constitution requires redaction at the logging boundary. A leaked password or 2FA code is a security incident.

**Independent Test**: Run the login with a sentinel password and a sentinel 2FA code. Search the captured output and the captured log records for both sentinel values.

**Acceptance Scenarios**:

1. **Given** a sentinel password and a sentinel 2FA code, **When** the login completes, **Then** neither value appears in direct output or in a log record.
2. **Given** the 2FA prompt receives an empty code, **When** the validation line prints, **Then** no value appears in direct output or in a log record.

---

### Edge Cases

- The operator ends input at the cloud prompt. The login returns no result and prints no success line.
- The operator ends input at the email, password, or 2FA prompt. The login stops and prints no success line.
- The 2FA code is empty. The validation line keeps its warning record, and no login request follows.
- Mist refuses the password. The SDK prints its error line, and the failure line keeps its warning record.
- Mist refuses the 2FA code. The SDK prints its 2FA error line, and no 2FA success line appears.
- The account has no MSP grant. The no-MSP line prints as direct output. The organization picker follows the switch flow.
- The account has one MSP grant. The picker prints the auto-selection line as direct output.
- The MSP organization list is empty. The no-organization line prints as direct output.
- The console threshold is 20. The info records of the login appear on the terminal with an INFO label. The direct output does not change.
- The SDK console level stays at 30 after the login. SDK info lines stay hidden until another SDK session sets the level.
- An MSP or organization name holds non-ASCII text. The name prints as received. This feature does not change that behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The cloud menu prints each line as direct output and writes no warning record.
- **FR-002**: The cloud selection line and its blank line print as direct output.
- **FR-003**: The email, password, and 2FA prompts keep their wording and their input path.
- **FR-004**: The 2FA banner prints as direct output before the 2FA prompt.
- **FR-005**: Each login progress line writes one info record and no direct output. Each duplicate progress line is removed.
- **FR-006**: The login success line prints as direct output and carries no warning label.
- **FR-007**: After Mist accepts a 2FA code, the tool prints `  + 2FA verification successful` as direct output.
- **FR-008**: When Mist refuses a 2FA code, the tool prints no 2FA success line.
- **FR-009**: The SDK console level for the interactive login is 30.
- **FR-010**: At SDK console level 30, SDK warning and error lines still print.
- **FR-011**: Each failure line and validation line keeps its warning or error record.
- **FR-012**: The MSP picker banner, the MSP menu, the organization menu, and each selection result print as direct output.
- **FR-013**: The organization list progress line writes one info record and no direct output.
- **FR-014**: The MSP summary lines after a login print as direct output.
- **FR-015**: The cancel of the switch to interactive login writes one info record.
- **FR-016**: A password value and a 2FA code value never appear in direct output or in any log record.
- **FR-017**: Each changed line carries an inline comment that states its channel and its reason.
- **FR-018**: Each new printed line uses ASCII text.
- **FR-019**: The operator guide lists the 2FA success line, and one changelog fragment names issue 4863.
- **FR-020**: Login results, SDK calls, prompt wording, and exit codes stay unchanged, except for the console level in FR-009.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature uses these mistapi members without change: the `APISession` constructor, `APISession.login_with_return`, and the `console` object of the logger module.
- The feature adds no direct HTTP request to a Mist REST endpoint.
- The feature adds no owned WebSocket transport. The output problem is local to MistHelper and to the SDK console level.
- Contract evidence: the constructor test pins `console_log_level=30`. A real-SDK test proves that the SDK success line stays off the terminal. The existing 2FA replay test and HTTP 503 test keep the SDK login path.
- Redaction evidence: the sentinel test for FR-016 searches all captured output and log records.

### Key Entities *(include if feature involves data)*

- **Operator line**: One fixed text line that the tool prints. Its key is the module, the function, and the wording. It has one channel: direct output, info record, warning record, or error record.
- **Login state**: The stage of one interactive login. The stages are cloud chosen, credentials read, login sent, 2FA sent, session finalized, and MSP announced. A stage can end as canceled or failed.
- **Console level**: The SDK console threshold. The interactive login sets it to 30.

Caution: the SDK console level is process-wide. SDK info lines stay hidden after a login until another SDK session sets the level.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the updated and new tests, no warning record exists for a banner, menu, success, or progress text.
- **SC-002**: A successful 2FA login prints one 2FA success line and one login success line, and no SDK success line.
- **SC-003**: Every failure test still finds its warning or error record.
- **SC-004**: The redaction tests find zero matches of the sentinel password and the sentinel 2FA code in direct output and log records.
- **SC-005**: Each applicable local gate passes. A failing gate is reported with its exact result. No gate is suppressed.

## Out of Scope

- The upgrade capture portal sign-in in `src/interfaces/portals/upgrade_portal/app/routes/auth.py`. It keeps its own console level of 20.
- The browser sign-in and the 2FA page of the operations portal. Issue #4936 tracks them.
- Filtering of SDK logger info records on the terminal. These records follow `CONSOLE_LOG_LEVEL` like every other module.
- The override warning in `scripts/bootstrap_worktree.py`.
- The token session path in `MistSessionInitializer`.
- Changes to prompt wording, the SDK version, and the Mist API calls.
- Non-ASCII text in names from Mist.

## Assumptions

- The MSP picker runs only in the switch flow, through `handle_interactive_login_success`. Remote check RC-31 confirms that call.
- The `--login` startup path calls `LoginOrchestrator.execute` and does not call the MSP picker. Remote check RC-32 confirms that call.
- The SDK version stays at 0.64.1, the version pinned in `requirements.txt`.
- The SDK console level is set on each SDK session construction. Remote check RC-68 confirms this behavior.
