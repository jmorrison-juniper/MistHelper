# Feature Specification: Validate menu 309 with an MSP login

**Feature Branch**: `chore/4925-menu-309-msp-validation`
**Created**: 2026-11-26
**Status**: Draft
**Input**: Issue #4925, "Validate menu 309 live with a credential that can open a shell, and test MSP scope."
**Linked**: Issue #4920 (closed), pull request #4924 (merged on 2026-11-26), issue #4936 (open).

## Summary

Menu 309 collects the hardware inventory of every connected EX switch in scope. The code is on `main`. Tasks 1 through 4 of issue #4925 passed on one test organization with an API token. Task 5 is open. Task 5 needs an MSP login. The owner's account may require two-factor authentication (2FA). Only the owner can run task 5. This record defines that live check. It also defines the checks that the implementer runs before the live check. This change adds no code.

## Terms

- **Live check**: the owner's run of menu 309 with an MSP login. It is a human-only step.
- **MSP login**: an interactive login whose profile holds at least one MSP grant.
- **Step 1 lines**: the credential line, the scope line, and the organizations in scope line of step 1.
- **Step 2 line**: one console line for each organization in scope in step 2.
- **Outcome row**: a CSV row whose `record_type` is `device_outcome`.
- **Master XML file**: the XML file that the run writes next to the CSV report.
- **Run folder**: the folder under `data/websocket-streams/` that holds the saved replies and the manifest of one run.
- **Owner**: the person who runs the live check.
- **Implementer**: the person or agent who runs the implementation tasks.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Count every organization in scope (Priority: P1)

The owner starts menu 309 with an MSP login. The owner reads the step 1 lines. The owner then counts the step 2 lines. Both counts must match.

**Why this priority**: Task 5 of issue #4925 is the only open task. It proves that the MSP scope covers every organization of the login.

**Independent Test**: The owner runs the live check in task T011. The implementer runs no part of it.

**Acceptance Scenarios**:

1. **Given** an MSP login with N organizations, **When** the owner reads step 1, **Then** the console shows `Scope: MSP` and `Organizations in scope: N`.
2. **Given** the same run, **When** the owner counts the step 2 lines, **Then** the count equals N.
3. **Given** the same run, **When** the owner presses Enter at the phrase prompt, **Then** the run cancels and writes no file.

### User Story 2 - Check one unread organization (Priority: P1)

The owner finds an organization that Mist cannot list switches for. The CSV report holds one outcome row for that organization. The master XML file holds one organization element with the status `failed`.

**Why this priority**: Task 5 requires that a failed organization is one outcome row.

**Independent Test**: The owner checks the rows during the live check in task T011. The automated tests in tasks T006, T007, and T008 cover the same rule in code.

**Acceptance Scenarios**:

1. **Given** an organization that fails in step 2, **When** the run ends, **Then** the CSV report holds one outcome row with `collection_status` set to `failed`.
2. **Given** the same organization, **When** the owner reads the master XML file, **Then** one organization element has `status="failed"` and no site.
3. **Given** an organization that fails in step 4, **When** the run ends, **Then** the report holds one row for each confirmed switch of that organization.

### User Story 3 - Check the MSP sign-in prompts and messages (Priority: P1)

The owner starts `python MistHelper.py --login --menu 309` in a terminal. The terminal asks for the email and the password. It asks for `Enter 2FA code:` when Mist requires a second factor. After the sign-in, the console prints `+ Login successful!` and `+ MSP access detected: N MSP(s) available`.

**Why this priority**: Every MSP check starts with this sign-in. Without it, the run has no MSP scope.

**Independent Test**: The owner signs in during the live check in task T011. The automated tests in tasks T003 and T004 cover the prompt text and the messages in code.

**Acceptance Scenarios**:

1. **Given** an account that requires 2FA, **When** the owner types the current code, **Then** the console prints `+ Login successful!`.
2. **Given** an account with an MSP grant, **When** the sign-in ends, **Then** the console prints `+ MSP access detected:` with the number of MSP grants.
3. **Given** a wrong or empty 2FA code, **When** the owner submits it, **Then** the login ends. The owner starts the command again.

### User Story 4 - Check the MSP scope in the portal preview (Priority: P2)

The owner starts `python MistHelper.py --login --web-portal` in a terminal and completes the sign-in there. In the browser, the owner opens WebSockets, then Multi Site. The owner selects `One combined CSV report`. The preview scope line starts with `Scope: MSP,`.

**Why this priority**: Step 8 of the owner steps in issue #4925 asks for this check. The CLI check proves the scope first, so this check has a lower priority.

**Independent Test**: The owner runs the portal check in task T012. The integration test in task T008 covers the MSP run in code.

**Acceptance Scenarios**:

1. **Given** an MSP login, **When** the owner opens the Multi Site preview, **Then** the scope line starts with `Scope: MSP,`.
2. **Given** the Multi Site action, **When** the owner opens the output choices, **Then** the choice `One combined CSV report (.csv)` exists.

### User Story 5 - Keep the evidence free of secrets and names (Priority: P1)

The owner searches the report, the master XML file, the run folder, and the log for each secret. The secrets are the API token, the password, and the 2FA code. Each search must find nothing. The owner then posts aggregate counts on issue #4925.

**Why this priority**: The repository is public. A posted name, identifier, or secret stays in the issue history.

**Independent Test**: The owner performs the searches. The owner checks the posted comment against the evidence contract.

**Acceptance Scenarios**:

1. **Given** the run files, **When** the owner searches for each secret, **Then** no search finds a match.
2. **Given** the posted comment, **When** a reader compares it with the evidence contract, **Then** the comment holds counts only.

### User Story 6 - Verify the code on main before the live check (Priority: P1)

The implementer checks each remote row on `main` at the commit that the owner uses. The implementer runs the automated tests named in the tasks. The implementer records the commit SHA of the checkout.

**Why this priority**: The live check tests the code on `main`. A changed file can invalidate this record.

**Independent Test**: The implementer repeats the remote checks and the automated tests. Each row and each result is recorded.

**Acceptance Scenarios**:

1. **Given** this record, **When** the implementer repeats the remote checks, **Then** each row keeps its blob SHA and its line.
2. **Given** the checkout, **When** the implementer runs the MSP scope test, **Then** the test passes.

### Edge Cases

- The MSP login has no MSP grant. Step 1 prints `Scope: organization`. The owner records the setup cause and uses an account with an MSP grant.
- The MSP list returns HTTP 403. Step 1 prints a note. The scope becomes one organization. The owner records the cause on issue #4925 and opens a new issue.
- The MSP has no organization. The scope becomes one organization, as in the previous case.
- An organization has no connected EX switch. Step 2 prints `0 connected EX switches`. The organization has no outcome row and no step 4 line.
- Mist limits the requests while step 2 reads an organization. The console prints that the organization was not read, because Mist limited the requests. The report holds one outcome row for it.
- Mist limits the requests in step 4. Each confirmed switch of that organization gets a skipped row with the reason.
- The operator presses Ctrl+C during step 4. The active batch stops. The remaining organizations are skipped. The run status is `partial`.
- A login session ends during the run. Mist behavior at expiry is not verified. The owner records the cause and starts a new login.
- The 2FA code expires before the owner submits it. The login fails. The owner starts the command again.

Warning: a posted secret cannot be removed from the issue history. Do not post a token, a password, or a 2FA code.

Caution: the run opens a read-only shell on each switch of every organization in scope. Read the step 1 lines before you type the phrase.

## Requirements *(mandatory)*

### Functional Requirements

Live check (human-only):

- **FR-001**: The record MUST list the live check as a human-only step. The implementer MUST NOT use or request a live credential.
- **FR-002**: The owner MUST run the CLI check first. The command is `python MistHelper.py --login --menu 309`.
- **FR-003**: The owner MUST read the step 1 lines before typing the phrase. The lines are the credential, the scope, and the organizations in scope.
- **FR-004**: The owner MUST count the step 2 lines. The count MUST equal the number in `Organizations in scope`.
- **FR-005**: The owner MUST check each organization that fails in step 2. The report MUST hold one outcome row for it. The master XML file MUST hold one organization element with `status="failed"`.
- **FR-006**: The owner MUST type the phrase only after FR-003 and FR-004 pass.
- **FR-007**: Before the run, the owner MUST compare the expected request count with the threshold of 5000 API calls per hour.
- **FR-008**: After the run, the owner MUST search four locations for each secret. Each search MUST find nothing.
- **FR-009**: The owner MUST post aggregate counts only, in the form of `design/contracts/live-msp-evidence.md`.
- **FR-010**: If the live check fails, the owner MUST open a new issue that names the cause.
- **FR-011**: The owner MUST run the portal check with `python MistHelper.py --login --web-portal`. The owner MUST read the preview scope line.

Implementer checks (before the live check):

- **FR-012**: The implementer MUST verify each row of the remote table in `design/research.md` on `main`. A changed row MUST update the record.
- **FR-013**: The implementer MUST run each automated test named in `tasks.md`. Each test MUST pass before the owner starts.
- **FR-014**: The implementer MUST record the commit SHA of the checkout. The SHA MUST equal the SHA of `main`.

Record and documentation:

- **FR-015**: The record MUST hold no token, password, 2FA code, organization name, site name, or identifier from a live run.
- **FR-016**: Each quoted console string in the record MUST match the code. The implementer MUST verify each string with a row in the remote table.
- **FR-017**: The operator guide MUST NOT state a Mist behavior that no source verifies.
- **FR-018**: The change MUST add one changelog fragment that names issue #4925.
- **FR-019**: The record MUST sit at `specs\numbered\0\0\1\2\4\2\0\0\4925-menu-309-msp-validation`. The pull request MUST refer to issue #4925 without closing it.

### Mist Cloud Transport Requirements

This record adds no Mist REST call and no owned WebSocket transport. The run uses the mistapi calls that the code already makes:

- `mistapi.api.v1.self.self.getSelf` reads the profile (`scope/profile.py`, line 97).
- `mistapi.api.v1.msps.orgs.listMspOrgs` lists the organizations of each MSP (`scope/resolver.py`, line 118).
- `mistapi.get_next` reads the next page of that list (`scope/resolver.py`, line 127).
- `login_with_return` runs the login and the 2FA replay (`login_orchestrator.py`, lines 171, 199, and 202).

### Key Entities

- **Live check run**: one run of menu 309 by the owner. It holds counts only. Section 2 of `design/data-model.md` defines it.
- **Organization in scope**: one organization that the run reads. Its identifier is never recorded.
- **Outcome row**: one CSV row with `record_type` set to `device_outcome`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the live check, the count of step 2 lines equals the count in `Organizations in scope`.
- **SC-002**: Each organization that fails in step 2 has one outcome row and one organization element with `status="failed"`.
- **SC-003**: Each secret search finds no match in the four locations of FR-008.
- **SC-004**: Issue #4925 holds a counts-only comment. Or a new issue names the cause of the failure.
- **SC-005**: Each remote row matches on `main` at the commit that the owner uses.
- **SC-006**: Each automated test in `tasks.md` passes before the owner starts the live check.

## Clarifications

### Session 2026-11-26

- Q: Who runs the live check? → A: The owner. The implementer uses no credential and makes no live request. (Source: issue #4925 body, task 5.)
- Q: Which front end runs first? → A: The CLI. The portal check follows. (Source: owner steps in the comment of 2026-11-26T00:08:35Z.)
- Q: Does merging this record close issue #4925? → A: No. The issue stays open until task 5 passes, or until a new issue records the failure. (Source: issue #4925 body, acceptance.)
- Q: What does "covers every organization" mean? → A: Each organization in scope has one step 2 line. The count equals `Organizations in scope`. (Derived from the console contract. See decision D-2.)
- Q: What does "a failed organization is one outcome row" mean? → A: A failure in step 2 gives one outcome row. A failure in step 4 gives one row for each confirmed switch. (Derived from the code. See decision D-6.)
- Q: May the record name a person, an identifier, or a secret? → A: No. The record holds aggregate counts only. (Source: issue #4925 acceptance. The repository is public.)

## Out of Scope

- Changes to the code of menu 309, the scope code, the sign-in code, or the portal code.
- The browser sign-in form for the operations portal on port 8055. Issue #4936 tracks it.
- The sign-in of the upgrade capture portal on port 8056.
- Support for the `orggroup`, `site`, and `sitegroup` grants (4920 research R17).
- Automation of the live check, and any container run of it.
- A fix for a defect that the live check finds. A defect gets its own issue.
- A correction to the 4920 contract wording for the 403 note. A follow-up issue tracks it (decision D-5).

## Assumptions

- The owner has an MSP login with at least one MSP grant. The owner also has a device for the 2FA code.
- The owner runs the checkout at the commit of `main` that this record names.
- Menu 309 is read-only. It opens a read-only shell on each switch and runs one fixed command (R-20).
- The API token threshold of 5000 calls per hour applies to the API token (R-89, R-90). Login sessions are unverified (U-03).
- The owner estimates the request count from the site count. The three-requests-per-site estimate is unverified (U-01).

## Dependencies

- Issue #4920 and pull request #4924 deliver the feature code. Both are complete on `main`.
