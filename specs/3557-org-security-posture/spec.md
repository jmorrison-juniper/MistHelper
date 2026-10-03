# Feature Specification: Organization Security Posture Checklist

**Feature Branch**: `3557-org-security-posture`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 276 organization security posture checklist. The organization settings page holds the password policy, the session policy, the API policy, the remote shell switch, the packet capture switch, and the stale configuration cleanup switch. No operation reads them as one checklist with a pass or fail verdict, so a security review reads each setting by hand. OrgSecurityPosture.csv: one row per check with check id, area, setting path, current value, recommended value, verdict (pass, fail, review), and a one-sentence reason. A console summary prints the pass, fail, and review counts. Acceptance criteria: runs in --test with no prompt and writes OrgSecurityPosture.csv under data/; each check lives in one small class with stable check id; absent API setting gives verdict review with reason absent; non-https webhook url fails; checklist has at least twelve checks and spec lists each recommended value and source page; wiring manifest exists; changelog fragment exists."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate an organization security checklist (Priority: P1)

A MistHelper operator running the menu 276 handler can review the organization's security posture from one command instead of manually opening each organization settings area. This branch delivers the importable handler and the wiring manifest. The integration pull request registers the handler as menu 276. The operation evaluates the password policy, session policy, API policy, remote shell switch, packet capture switch, and stale configuration cleanup switch and produces a checklist with a pass, fail, or review verdict for each check.

**Why this priority**: This delivers the core security-review value: one repeatable checklist replaces manual inspection of multiple organization settings.

**Independent Test**: Run the menu 276 handler in test mode with representative organization settings and confirm the operation completes without prompts, writes `data/OrgSecurityPosture.csv`, and includes at least twelve check rows with stable check IDs and verdicts.

**Acceptance Scenarios**:

1. **Given** representative organization settings are available in test mode, **When** the operator runs the menu 276 handler with `--test`, **Then** the run completes without prompting and writes `data/OrgSecurityPosture.csv`.
2. **Given** the CSV is opened after the run, **When** the reviewer inspects the rows, **Then** each row contains check id, area, setting path, current value, recommended value, verdict, and a one-sentence reason.
3. **Given** the checklist evaluates all configured security areas, **When** the reviewer counts the rows, **Then** at least twelve checks are present and every check id remains stable across repeated runs.

---

### User Story 2 - Understand security posture at a glance (Priority: P2)

A security reviewer can see a console summary of how many checks passed, failed, or require manual review before opening the CSV details. This allows quick triage of whether the organization is broadly compliant or needs immediate attention.

**Why this priority**: Security reviews need a fast verdict summary before detailed evidence is reviewed or attached to an audit packet.

**Independent Test**: Run the menu 276 handler against test data containing known pass, fail, and review outcomes and confirm the console summary prints the correct count for each verdict category.

**Acceptance Scenarios**:

1. **Given** the checklist contains passing, failing, and review rows, **When** the menu 276 handler completes, **Then** the console summary prints the pass, fail, and review counts that match the CSV.
2. **Given** all checks pass, **When** the operation completes, **Then** the console summary clearly shows zero failures and zero review items.

---

### User Story 3 - Flag uncertain or unsafe API posture (Priority: P3)

A reviewer can distinguish missing API-policy information from confirmed failures. Absent API settings require review with a clear reason, while webhook URLs that are not HTTPS fail because they create an insecure integration path.

**Why this priority**: API posture has both security and evidence-quality risks; missing data must not be treated as passing, and insecure webhook transport must be clearly actionable.

**Independent Test**: Run menu 276 with test data where the API policy is absent and with test data containing a non-HTTPS webhook URL; confirm the absent setting is `review` with reason `absent`, and the non-HTTPS webhook is `fail`.

**Acceptance Scenarios**:

1. **Given** the API policy setting is absent from the organization settings response, **When** the checklist evaluates API posture, **Then** the relevant API check verdict is `review` and the one-sentence reason contains `absent`.
2. **Given** a webhook URL starts with any scheme other than `https://`, **When** the checklist evaluates API posture, **Then** the webhook transport check verdict is `fail` with a reason that identifies non-HTTPS transport.

---

### Edge Cases

- If an expected organization settings area is missing entirely, each affected check uses verdict `review` rather than `pass`, and the reason states that the setting is absent.
- If a setting has an unexpected type or unrecognized value, the affected check uses verdict `review` and explains that the value could not be interpreted.
- If no webhook URLs are configured, the webhook transport check uses verdict `review` with a reason that no webhook value was present to verify.
- If the CSV already exists from a previous run, the operation replaces it with the current organization's checklist so reviewers do not use stale evidence.
- If the run has no authenticated organization context in normal mode, the operation fails safely before writing a misleading checklist; this does not apply to `--test` mode.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide the importable menu 276 handler and the wiring manifest for the organization security posture checklist operation.
- **FR-002**: System MUST evaluate the organization settings page areas for password policy, session policy, API policy, remote shell, packet capture, and stale configuration cleanup as one checklist.
- **FR-003**: System MUST write `OrgSecurityPosture.csv` under `data/` for every successful run.
- **FR-004**: System MUST write one CSV row per check with columns `check id`, `area`, `setting path`, `current value`, `recommended value`, `verdict`, and `reason`.
- **FR-005**: System MUST use only the verdict values `pass`, `fail`, and `review`.
- **FR-006**: System MUST provide a one-sentence reason for every check verdict.
- **FR-007**: System MUST print a console summary containing the pass, fail, and review counts after checklist generation.
- **FR-008**: System MUST support `--test` execution with no interactive prompt and produce the same CSV structure as a normal run.
- **FR-009**: System MUST include at least twelve security checks in the checklist.
- **FR-010**: System MUST keep each check id stable across releases unless the check is deliberately replaced and documented.
- **FR-011**: System MUST ensure each check has a single, small, independently reviewable owner so reviewers can trace one check to one decision rule.
- **FR-012**: System MUST give absent API settings a `review` verdict with a reason containing `absent`.
- **FR-013**: System MUST give any non-HTTPS webhook URL a `fail` verdict.
- **FR-014**: System MUST list each check's recommended value and source page in this specification.
- **FR-015**: System MUST include a feature-owned wiring manifest so implementation and review can confirm the deferred menu, operation, export, and test wiring.
- **FR-016**: System MUST include a changelog fragment describing the new menu 276 organization security posture checklist.
- **FR-017**: System MUST not mark a check as passing when the required setting is absent, unreadable, or ambiguous.
- **FR-018**: System MUST make the CSV sufficient for a reviewer to identify which setting needs remediation without re-running the operation.

### Recommended Values and Source Pages

| Check ID | Area | Setting Path | Recommended Value | Source Page |
|----------|------|--------------|-------------------|-------------|
| ORGSEC-PASSWORD-001 | Password policy | `organization settings > password policy > enabled` | Enabled | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-002 | Password policy | `organization settings > password policy > minimum length` | At least 12 characters | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-003 | Password policy | `organization settings > password policy > uppercase required` | Required | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-004 | Password policy | `organization settings > password policy > lowercase required` | Required | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-005 | Password policy | `organization settings > password policy > number required` | Required | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-006 | Password policy | `organization settings > password policy > special character required` | Required | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-007 | Password policy | `organization settings > password policy > password reuse history` | Reuse blocked for at least the last 5 passwords | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-008 | Password policy | `organization settings > password policy > maximum password age` | 90 days or less, or review if the tenant uses federated identity with stronger policy evidence | Mist Organization Settings > Password Policy |
| ORGSEC-PASSWORD-009 | Password policy | `organization settings > password policy > two-factor required` | Required | Mist Organization Settings > Password Policy |
| ORGSEC-SESSION-001 | Session policy | `organization settings > session policy > idle timeout` | 30 minutes or less | Mist Organization Settings > Session Policy |
| ORGSEC-SESSION-002 | Session policy | `organization settings > session policy > maximum session lifetime` | 12 hours or less | Mist Organization Settings > Session Policy |
| ORGSEC-API-001 | API policy | `organization settings > API policy > API access` | `disabled`, `restricted`, or `admins_only` | Mist Organization Settings > API Policy |
| ORGSEC-API-002 | API policy | `organization settings > API policy > token expiration` | API tokens expire within 365 days or less | Mist Organization Settings > API Policy |
| ORGSEC-API-003 | API policy | `organization settings > API policy > webhook URLs` | Every configured webhook URL uses `https://` | Mist Organization Settings > API Policy |
| ORGSEC-REMOTE-001 | Remote shell | `organization settings > remote shell` | Disabled unless there is a documented break-glass exception | Mist Organization Settings > Remote Shell |
| ORGSEC-REMOTE-002 | Remote shell | `organization settings > Junos shell role access` | Every role is set to none | Mist Organization Settings > Remote Shell |
| ORGSEC-CAPTURE-001 | Packet capture | `organization settings > packet capture` | Disabled unless there is an active troubleshooting exception | Mist Organization Settings > Packet Capture |
| ORGSEC-CAPTURE-002 | Packet capture | `organization settings > packet capture bucket verified` | Verified | Mist Organization Settings > Packet Capture |
| ORGSEC-CLEANUP-001 | Stale configuration cleanup | `organization settings > stale configuration cleanup` | Enabled | Mist Organization Settings > Stale Configuration Cleanup |

### Key Entities *(include if feature involves data)*

- **Security Posture Check**: A single checklist rule with a stable check id, area, setting path, recommended value, source page, verdict, and one-sentence reason.
- **Organization Setting Value**: The current value read from the organization's settings for a specific security-relevant path.
- **Checklist Export**: The `OrgSecurityPosture.csv` evidence file containing one row per security posture check.
- **Console Summary**: The operator-facing count of pass, fail, and review verdicts from the generated checklist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can generate the organization security posture CSV through the importable menu 276 handler without manually checking more than one settings page.
- **SC-002**: In `--test` mode, the operation completes without prompts and produces `data/OrgSecurityPosture.csv` in 100% of successful test runs.
- **SC-003**: The CSV contains at least twelve checklist rows and 100% of rows include all required columns with non-empty check id, area, recommended value, verdict, and reason fields.
- **SC-004**: The console summary's pass, fail, and review counts match the CSV verdict counts in 100% of validation runs.
- **SC-005**: Test data with absent API settings produces a `review` verdict and a reason containing `absent` in 100% of validation runs.
- **SC-006**: Test data with a non-HTTPS webhook URL produces a `fail` verdict in 100% of validation runs.
- **SC-007**: A security reviewer can identify each failing or review item's setting path and recommended value from the CSV without rerunning menu 276.

## Assumptions

- The source of truth for these checks is the Mist Organization Settings page and its Password Policy, Session Policy, API Policy, Remote Shell, Packet Capture, and Stale Configuration Cleanup sections.
- The first release focuses on organization-level settings only; site-level, WLAN-level, device-level, and identity-provider posture checks are out of scope.
- Recommended values reflect conservative enterprise security defaults suitable for a security review; documented compensating controls may justify a `review` outcome rather than an automatic pass.
- `--test` mode uses representative fixture data and must not require network access, operator prompts, or live organization credentials.
- Existing CSV export behavior may be reused as long as the exported evidence file has the required name, location, rows, and columns.
- The integration pull request registers menu 276 in `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, generated menu references, and user-facing menu documentation.
