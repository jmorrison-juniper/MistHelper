# Feature Specification: Admin Token Hygiene

**Feature Branch**: `feat/3554-admin-token-hygiene`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 273 admin and API token hygiene report. Menus 47 and 48 export API tokens and administrators, but no operation scores them. A Super User with no two-factor authentication, a stale invite, a token that no one used for 90 days, and a token with org-wide write and no source IP limit are each a finding that an operator must compute by hand. AdminHygiene.csv: one row per admin with email, role summary, site scope, two-factor state, SSO state, password age in days, invite expiry, and a findings column. TokenHygiene.csv: one row per org token with name, created by, created time, last used, idle days, privilege summary, source IP restriction present, and a findings column. A console summary counts Super Users, admins with no two-factor and no SSO, idle tokens, and unrestricted write tokens."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate hygiene reports without prompts (Priority: P1)

An operator runs menu 273 to get an admin hygiene report and a token hygiene report. The operation completes without prompts in test mode. It writes both files under `data/`.

**Why this priority**: This is the main value. Operators need one action that replaces manual checks across the existing admin and token exports.

**Independent Test**: Run the operation in `--test`. Confirm that it returns without any prompt and writes `data/AdminHygiene.csv` and `data/TokenHygiene.csv`.

**Acceptance Scenarios**:

1. **Given** test mode is active, **When** the operator runs menu 273, **Then** the operation writes both hygiene files under `data/` and does not ask for input.
2. **Given** admin and token source data exists, **When** the operation completes, **Then** each admin appears in `AdminHygiene.csv` and each org token appears in `TokenHygiene.csv`.
3. **Given** the operation completes, **When** the operator reads the console output, **Then** it includes counts for Super Users, admins with no two-factor authentication and no SSO, idle tokens, and unrestricted write tokens.

---

### User Story 2 - Review admin risk findings (Priority: P2)

An operator opens `AdminHygiene.csv` and sees one row per admin. The row includes identity, role, scope, sign-in security, password age, invite state, and findings.

**Why this priority**: Admin accounts can control the organization. Operators must see weak or stale admin access without hand checks.

**Independent Test**: Use source data with admins that include a Super User, an admin without two-factor authentication, an admin without SSO, and a stale invite. Confirm that the report lists the expected fields and findings.

**Acceptance Scenarios**:

1. **Given** an admin has privileges with role `superuser` at org scope, **When** the operation scores admins, **Then** that admin counts as a Super User in the console summary.
2. **Given** an admin has no two-factor authentication and no SSO, **When** the operation scores admins, **Then** that admin is counted in the console summary for admins with no two-factor authentication and no SSO.
3. **Given** an admin invite has expired or is stale, **When** the operation scores admins, **Then** the admin row includes a finding for the invite risk.

---

### User Story 3 - Review token risk findings (Priority: P3)

An operator opens `TokenHygiene.csv` and sees one row per org token. The row includes token metadata, use age, privilege summary, source IP restriction state, and findings.

**Why this priority**: Long-lived and broad tokens are a common access risk. Operators need clear findings without exposing token secrets.

**Independent Test**: Use source data with a never-used token, an idle token, and an org-wide write token without a source IP limit. Confirm that the report computes idle days, findings, and summary counts.

**Acceptance Scenarios**:

1. **Given** a token was never used, **When** the operation scores token idle time, **Then** idle days equals the token age and the findings column includes `never_used`.
2. **Given** a token has not been used for the idle threshold, **When** the operation scores tokens, **Then** the token is counted as idle in the console summary.
3. **Given** a token has org-wide write privilege and no source IP limit, **When** the operation scores tokens, **Then** the token is counted as an unrestricted write token in the console summary.
4. **Given** any token is present in source data, **When** reports and logs are produced, **Then** the token key value never appears in any log line or output file.

---

### User Story 4 - Track delivery artifacts (Priority: P4)

A planner can find the wiring manifest and release note fragment for this issue.

**Why this priority**: The implementation needs a clear integration contract and release note before it is ready for review.

**Independent Test**: Confirm that `specs/3554-admin-token-hygiene/wiring.md` exists with every section of the wiring contract, and `changelog.d/issue-3554-admin-token-hygiene.md` exists before release.

**Acceptance Scenarios**:

1. **Given** planning starts for this feature, **When** the planner checks the feature directory, **Then** `specs/3554-admin-token-hygiene/wiring.md` exists with every section of the contract.
2. **Given** the feature is ready for release review, **When** the reviewer checks release notes, **Then** `changelog.d/issue-3554-admin-token-hygiene.md` exists.

### Edge Cases

- A token with no `last used` value is treated as never used. Its idle days equals its age.
- A token with missing created time cannot have a reliable age. The report still keeps the row and adds a finding that the age is unknown.
- A token with read-only privilege and no source IP limit is not counted as an unrestricted write token.
- A token with org-wide write privilege and a source IP limit is not counted as an unrestricted write token.
- An admin with SSO enabled and no two-factor state is not counted in the "no two-factor and no SSO" summary count.
- An admin with site-only scope is not counted as a Super User unless privileges also show role `superuser` at org scope.
- Empty source data still produces both CSV files with headers and a console summary with zero counts.
- Missing optional metadata leaves the related cell blank or marked unknown. It does not stop the full report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide menu 273 as an admin and API token hygiene report operation.
- **FR-002**: The operation MUST run in `--test` with no prompt.
- **FR-003**: The operation MUST write both `AdminHygiene.csv` and `TokenHygiene.csv` under `data/`.
- **FR-004**: `AdminHygiene.csv` MUST include one row per admin.
- **FR-005**: Each admin row MUST include email, role summary, site scope, two-factor state, SSO state, password age in days, invite expiry, and findings.
- **FR-006**: The admin findings MUST identify at least Super User access, missing two-factor authentication when SSO is also absent, and stale invites.
- **FR-007**: An admin whose privileges hold role `superuser` at org scope MUST count as a Super User in the console summary.
- **FR-008**: `TokenHygiene.csv` MUST include one row per org token.
- **FR-009**: Each token row MUST include id, name, created by, created time, last used, idle days, privilege summary, source IP restriction present, and findings.
- **FR-010**: The token key value MUST NOT appear in any log line or output file.
- **FR-011**: The token report MUST keep token id, name, and metadata only.
- **FR-012**: A token that was never used MUST carry idle days equal to its age.
- **FR-013**: A token that was never used MUST include the finding `never_used`.
- **FR-014**: The idle token threshold MUST default to 90 days.
- **FR-015**: The idle token threshold MUST read `TOKEN_IDLE_DAYS` from the environment when it is set.
- **FR-016**: The token findings MUST identify at least never-used tokens, idle tokens, and tokens with org-wide write privilege and no source IP limit.
- **FR-017**: The console summary MUST count Super Users, admins with no two-factor authentication and no SSO, idle tokens, and unrestricted write tokens.
- **FR-018**: The operation MUST complete when no admins or no tokens exist, and it MUST still write both files with headers.
- **FR-019**: The wiring manifest `specs/3554-admin-token-hygiene/wiring.md` MUST exist with every section of the contract before implementation is marked ready.
- **FR-020**: The release note fragment `changelog.d/issue-3554-admin-token-hygiene.md` MUST exist before release review.

### Key Entities

- **Admin Hygiene Row**: A scored admin account. Key data includes email, role summary, site scope, two-factor state, SSO state, password age in days, invite expiry, and findings.
- **Token Hygiene Row**: A scored org token. Key data includes id, name, created by, created time, last used, idle days, privilege summary, source IP restriction present, and findings. It excludes the token key value.
- **Finding**: A short label that explains a hygiene risk. Examples include missing two-factor authentication with no SSO, stale invite, `never_used`, idle token, and unrestricted write token.
- **Console Summary**: A short result summary for the operator. It counts Super Users, admins with no two-factor authentication and no SSO, idle tokens, and unrestricted write tokens.
- **Idle Threshold**: The number of days used to classify a token as idle. The default is 90 days unless `TOKEN_IDLE_DAYS` is set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In test mode, 100% of runs complete without a prompt and write both expected files under `data/`.
- **SC-002**: For seeded source data, 100% of admins and 100% of org tokens appear once in the matching hygiene file.
- **SC-003**: For seeded source data, 100% of never-used tokens show idle days equal to token age and include `never_used`.
- **SC-004**: For seeded source data, 0 token key values appear in logs, console output, or report files.
- **SC-005**: For seeded source data, the console summary counts Super Users, admins with no two-factor authentication and no SSO, idle tokens, and unrestricted write tokens with 100% accuracy.
- **SC-006**: Operators can identify all listed admin and token findings from the two report files and console summary in under 5 minutes for a normal organization export.
- **SC-007**: The idle threshold is 90 days by default and matches `TOKEN_IDLE_DAYS` in 100% of runs where the value is set.

## Assumptions

- Existing menu 47 and menu 48 exports or their source data contain enough metadata to score admins and org tokens.
- The report is read by operators who can access existing exported data under normal MistHelper permissions.
- "Stale invite" means an invite that is expired or no longer usable at the time of the report.
- "Unrestricted write token" means an org token with org-wide write privilege and no source IP restriction.
- Password age is calculated in whole days from the best available password age or password change timestamp.
- Missing optional metadata is reported as unknown rather than causing the operation to fail.
