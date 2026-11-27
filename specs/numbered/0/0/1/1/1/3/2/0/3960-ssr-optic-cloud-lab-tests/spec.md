# Feature Specification: SSR optic and Mist cloud path lab tests

**Feature Branch**: `docs/3960-ssr-lab-results`

**Created**: 2026-11-26

**Status**: Draft. The record is complete. The six lab tests stay open until the owner returns sanitized outputs.

**Input**: Issue #3960, "Handoff: test the SSR optic and Mist cloud path runbook steps from #3946 on a lab SSR". The agent has no lab device access. Record each lab step as an owner-only human step, and write the rest of the spec.

## Clarifications

### Session 2026-11-26

- Q: Does the agent run the lab tests? → A: No. The owner runs each test on a lab SSR. The orchestrator instruction forbids credential use, and the owner decision of 2026-10-21 requires an identified lab SSR.
- Q: Does the change need a new verification table? → A: No. The section 14 subsection exists on main from pull request #4114, merge commit 400899f4. This change reuses it.
- Q: Which closing keyword does the pull request use? → A: `Refs #3960` until all six outputs exist. The final pull request uses `Closes #3960`.
- Q: Does this change edit the verifier? → A: No. Verifier defects need a separate issue.
- Q: Where does each lab output go? → A: Each output goes in the step that the runbook row names. The H-2 output goes in the section 11 table, as the issue states.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Owner records six lab outputs (Priority: P1)

The owner runs six commands on a lab SSR. The owner records each output in the target that the runbook names. Each recorded output holds no address, serial number, or customer name.

**Why this priority**: Only lab outputs can confirm or correct six unverified runbook statements. An unverified command can mislead an engineer during an outage.

**Independent Test**: The owner runs H-1 on one SSR 7.0.x router. The owner records one sanitized output in the section 11 table. The recorded text holds the exact error text and the release string.

**Acceptance Scenarios**:

1. **Given** a lab SSR on SSR 7.0.x, **When** the owner runs H-1, **Then** the error text appears in section 11 with the release string.
2. **Given** an output that holds a customer name, **When** the owner prepares the record, **Then** the owner removes the name before any commit.
3. **Given** a fiber port on SSR 7.1.0-50r1 or later, **When** the owner runs H-4, **Then** step C2 names the power and threshold fields.

---

### User Story 2 - Agent records the outputs in one pull request (Priority: P2)

After the owner returns the outputs, the agent edits the runbook and adds one changelog fragment. The agent opens one pull request after the local gates pass.

**Why this priority**: One pull request keeps the change reviewable. The closing keyword rule keeps the issue open until all six outputs exist.

**Independent Test**: The agent applies the recorded outputs on a branch cut from main. Each changed Markdown file scores 80 or above with ste-linter. The pull request body holds the correct closing keyword.

**Acceptance Scenarios**:

1. **Given** six recorded outputs, **When** the agent updates the section 14 table, **Then** no cell in rows 360 to 365 reads Not run.
2. **Given** fewer than six recorded outputs, **When** the agent opens the pull request, **Then** the body holds `Refs #3960` and no `Closes #3960`.
3. **Given** a changed Markdown file, **When** ste-linter runs with a minimum score of 80, **Then** the file scores 80 or above.

---

### User Story 3 - Operator reads only verified statements (Priority: P3)

A NOC engineer reads the verification status before an escalation. The engineer sees which statements have a lab result and which statements have none.

**Why this priority**: An unverified statement can send an engineer to the wrong fix during an outage.

**Independent Test**: The reader opens the section 14 subsection. Each row names a source and a lab test cell. Each lab test cell reads Not run or a release string.

**Acceptance Scenarios**:

1. **Given** the merged section 14 subsection, **When** a reader opens it, **Then** each row names a source and a lab test cell.
2. **Given** a row that reads Not run, **When** a reader escalates that statement, **Then** the reader reports the statement as unverified.

---

### Edge Cases

- A planned release differs from the release that the router reports. The owner records the reported release. The agent changes the step text only when the output differs.
- An output holds a customer name. Warning: a committed name stays in the public repository history after a revert. The owner removes the name first.
- H-6 stops Mist management of the lab router. Caution: the router loses Mist management until the owner removes the block rule. The owner then repeats H-5.
- The Testing Tools run while the cloud link is blocked. The owner records the result. The agent corrects the last sentence of the cloud path section.
- The 2026-10-05 sentence has no source. The owner adds a source or removes the sentence before the final pull request.
- Main changes before the merge. The agent rebases onto main and repeats TEST-01 and TEST-02.
- The verifier still reports `show route` after the edit. The finding stays in a separate issue. It does not block this change.
- An output contradicts a statement. The owner records the output. The agent changes the statement and keeps the release string.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The process MUST keep the six lab tests as owner-only human steps. The agent MUST NOT run a lab test.
- **FR-002**: The process MUST NOT request, store, print, or use a lab credential or a console credential.
- **FR-003**: Each lab output MUST go in the target that contracts/lab-output-record.md names.
- **FR-004**: Each recorded output MUST NOT hold an address, a serial number, or a customer name.
- **FR-005**: Each changed lab test cell MUST name the release that produced the output.
- **FR-006**: The change MUST reuse the section 14 subsection that pull request #4114 merged. The change MUST NOT add a second verification table.
- **FR-007**: The pull request body MUST hold `Closes #3960` only after all six outputs are recorded. Before that, the body MUST hold `Refs #3960`.
- **FR-008**: The change MUST NOT modify scripts/verify_ssr_commands.py or tests/unit/scripts/test_verify_ssr_commands.py.
- **FR-009**: The change MUST modify only documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md and add one changelog fragment.
- **FR-010**: Each changed Markdown file MUST score 80 or above with ste-linter.
- **FR-011**: Each hyperlink in each changed Markdown file MUST resolve to a file or an anchor.
- **FR-012**: The owner MUST give a typed confirmation before H-6 starts. The agent MUST NOT start H-6.
- **FR-013**: Before the first edit, the implementer MUST add the in-progress label and a claim comment to #3960. The implementer MUST check open pull requests for file overlap.
- **FR-014**: The changelog fragment MUST follow the name rule in changelog.d/README.md. The fragment MUST keep its name after the pull request opens.
- **FR-015**: The research record MUST list each statement without a source check under Unverified, with its reason.
- **FR-016**: The agent MUST NOT report a lab result without a sanitized recorded output.
- **FR-017**: The final pull request MUST keep the 2026-10-05 sentence only when a source supports it.
- **FR-018**: Before the local branch of pull request #3951 is removed, the owner MUST confirm a clean status and compare the branch with main.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- Not applicable. This feature makes no REST request and names no mistapi method. The runbook names device commands and portal tools only.
- The Mist OpenAPI file names ep-terminator in one field description (documentation/mist-api-openapi31yaml.yaml, line 109123). That text does not describe the lab tests.

### Key Entities *(include if feature involves data)*

- **Lab step**: One owner-only test. It has an identifier from H-1 to H-8, a command, a target, and a release string. H-0 names the lab SSR before any test.
- **Statement**: One row of the section 14 verification table. It has a statement, a source, and a lab test cell.
- **Sanitized output**: Text from a lab run. The owner removes each address, serial number, and customer name first.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Six sanitized outputs exist, one for each lab step from H-1 to H-6, before the final pull request opens.
- **SC-002**: No cell in rows 360 to 365 of the section 14 table reads Not run when the final pull request opens.
- **SC-003**: Each changed Markdown file scores 80 or above with the ste-linter gate.
- **SC-004**: The pull request diff changes no line in the verifier file or its test file.
- **SC-005**: The pull request body holds `Closes #3960` only when SC-001 and SC-002 both hold.
- **SC-006**: No required check fails on the pull request before the auto-merge label is added.

## Assumptions

- The owner identifies a lab SSR for each release line that the six steps name.
- The owner reaches each lab console by the owner's own method. The agent holds no console access.
- The runbook on main keeps blob 4fe23574f2f66792139b4c84132a85a21f3dda03 until the implementer starts. A later change needs a new read.
- The Mist portal Testing Tools are available for the owner's lab tenant. This assumption is unverified.
- The implementer runs ste-linter and markdown-link-check from the development environment. This record did not run them.

## Out of Scope

- Any agent access to a lab SSR, a lab console, or a lab credential.
- Any change to scripts/verify_ssr_commands.py or tests/unit/scripts/test_verify_ssr_commands.py.
- Any change to another runbook in documentation/noc-runbooks/.
- Any change to CHANGELOG.md.
- Any fetch of vendor documentation into documentation/references/. Git ignores that folder.
- Any new owner decision on lab credential policy. A future issue must handle that decision.
- Any extension of the verification table beyond the six statements (D-6).
