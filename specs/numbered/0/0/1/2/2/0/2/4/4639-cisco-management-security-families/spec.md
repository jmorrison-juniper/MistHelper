# Feature Specification: Review management and security configuration families

**Feature Branch**: `docs/4639-cisco-management-security-families`

**Created**: 2026-11-26

**Status**: Specified. Implementation and cloud use are not approved.

**Input**: Issue 4639, tasks T015 and T016 of the Cisco converter full-parity map (PR 4596). Review the management and security families. Map only verified fields. Show every other family as display-only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review management and security families safely (Priority: P1)

An engineer loads a Cisco configuration. The review shows each management and security family with one status and one limit. No secret value appears.

**Why this priority**: The parser recognizes these families. Parser presence does not prove a safe Mist mapping. Reviewers need visible limits first.

**Independent Test**: Run the review on a synthetic configuration. The configuration holds all 14 families and each secret form. Check the labels, the statuses, and the absence of values. Block network access.

**Acceptance Scenarios**:

1. **Given** a synthetic configuration with all 14 families, **When** the review runs, **Then** each family returns one fixed label, one status, and one limit.
2. **Given** a line with a password, community, key, or shared secret, **When** the review runs, **Then** the status is secret-omitted and no value appears.
3. **Given** a one-way hash or a reversible type 7 value, **When** the review runs, **Then** the value is omitted and never decoded.
4. **Given** an ACL, class, policy, zone, crypto, redundancy, or flow export line, **When** the review runs, **Then** the status is display-only. No field maps.

### User Story 2 - Map only verified management fields (Priority: P1)

An engineer sees syslog, SNMP location and contact, and the cellular APN as mapped. A field maps only after its evidence row is verified and the selected model supports it.

**Why this priority**: A wrong destination or a wrong scope can change production gateway behavior.

**Independent Test**: Run positive and negative fixtures against a mocked evidence registry. Confirm that each mapped field has a pointer and an SDK signature.

**Acceptance Scenarios**:

1. **Given** a Branch or Standalone role and a logging host line, **When** evidence E-01 is verified, **Then** the host maps to site settings only.
2. **Given** a Hub role and a logging host line, **When** the review runs, **Then** the status is display-only and no mapped field appears.
3. **Given** a logging host line, **When** the review runs, **Then** no host-out policy field appears.
4. **Given** a model without verified LTE support, **When** a cellular APN line appears, **Then** the status is display-only with the family limit.

### User Story 3 - Keep existing DNS behavior and portal contracts (Priority: P2)

The current DNS preview and the portal routes stay unchanged. The management review runs beside the DNS conversion and does not change its output.

**Why this priority**: Engineers already use the DNS preview. A regression stops their work.

**Independent Test**: Run the existing DNS unit tests and route tests. Run the DNS converter on a fixture that holds management lines. Compare its output with the stored baseline.

**Acceptance Scenarios**:

1. **Given** DNS and management lines in one input, **When** the DNS converter runs, **Then** its addresses, unsupported count, and known gaps match the baseline.
2. **Given** this change, **When** the change is reviewed, **Then** no route, template, navigation, or model file changes.

### Edge Cases

- Empty input produces no management observation.
- A banner body that contains a family keyword is not classified.
- An indented line inherits the family of the previous top-level line. A top-level line starts a new context.
- A secret keyword with no value still produces a secret-omitted observation. No value appears.
- A type 5, 7, 8, or 9 value after a secret keyword is omitted in the same way.
- A mapped value that fails validation becomes display-only with a validation limit.
- A syslog option other than the host stays display-only until its enumeration is verified.
- A line that mixes a family keyword and a secret keyword is secret-omitted.
- An unsupported model with a cellular line is display-only with the family limit.
- A community string with spaces or special characters is omitted without escaping.

Warning: a secret value that reaches a log or an export cannot be removed from that copy.

Caution: a stale evidence row can map a field that the schema no longer supports. Repeat the evidence checks before each release.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Requirement |
| --- | --- |
| FR-001 | The review must classify each in-scope line into one of 14 families with a fixed label. |
| FR-002 | A field must map only when its evidence row is verified, and its pointer and SDK signature are recorded. |
| FR-003 | Parser-only families must show display-only status and the fixed family limit. |
| FR-004 | Each unsupported family must show its limit. No value may be inferred for it. |
| FR-005 | The review must generate no device command and must never write a raw command field. |
| FR-006 | Secret values must not appear in review output, logs, or test output. |
| FR-007 | One-way hashes and reversible encoded values must never be decoded, reconstructed, or displayed. |
| FR-008 | Each omitted value must show a fixed label. The review must not echo the source line. |
| FR-009 | Syslog must map only to site settings for Branch and Standalone roles after evidence E-01. Hub syslog must stay display-only. |
| FR-010 | The existing DNS addresses, unsupported items, and known gaps must stay unchanged. |
| FR-011 | Existing portal routes, templates, navigation, and models must stay unchanged. |
| FR-012 | No test or code path in this issue may send a Mist request or write to Mist. |
| FR-013 | A field must map only for a model that the selected model table lists as supported. |
| FR-014 | Each test must exist and must fail before its implementation. |
| FR-015 | Each conflicting source claim must have a recorded resolution before its field is implemented. |

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- This issue calls no mistapi method. Future writes use `updateSiteSettings` for site settings and `updateOrgGatewayTemplate` for port configuration (R68, R70).
- This issue proposes no direct HTTP request and no owned WebSocket transport.
- The evidence rows in `design/contracts/mist-management-evidence.md` must pass before any write. Issue 4644 owns writes.

### Key Entities *(include if feature involves data)*

- **Management family**: One of 14 families. Each family has a fixed ID, label, disposition, and limit.
- **Management observation**: One classified source line. It holds a status and a limit. It holds no source text.
- **Secret keyword**: A token that marks the value after it as secret. The review omits that value.
- **Evidence row**: One checked Mist field or absence. It holds a pointer, an SDK signature, and a status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 14 families have one disposition row in `design/research.md` with evidence or a limit.
- **SC-002**: Zero secret values or hash strings appear in review output, logs, or test output.
- **SC-003**: Zero device command strings appear in any observation.
- **SC-004**: All existing DNS unit tests and route tests pass without edits to their assertions.
- **SC-005**: Each mapped field has one positive test and one negative test.
- **SC-006**: Zero network sockets open during the review tests.

## Assumptions

- Issues 4634, 4636, 4637, 4638, and 4640 finish before implementation starts.
- The OpenAPI YAML file in the repository matches the fields cited in this record. Task T001 checks each pointer.
- Cisco command forms in fixtures follow standard IOS syntax. Task T003 confirms each form.
- The source mapping document serves only as an observation source. Issue 4635 decides any reuse.
- Issue 4644 uses this contract only after its own approval gates pass.

## Out of Scope

- Routing, network, and hardware conversion. Issues 4638 and 4640 own them.
- Proposal display, proposal export, and review screens. Issues 4637 and 4641 own them.
- Discovery, apply, backup, administration, restore, and recovery. Issues 4642 to 4646 own them.
- Visual journeys and shared portal integration. Issues 4647 and 4648 own them.
- Parity closure and the converter guide. Issue 4649 owns them.
- Licensing and authorship decisions. Issue 4635 owns them.

## Clarifications

### Session 2026-11-26

- Q: Where do the management tests go? A: Under `tests/integration/web_portal/cisco_config_converter/management/`. The `tests/contract/` parent already has 17 children (R35). Decision D-1.
- Q: Where does the review code go? A: In `conversion.py`. No new module joins the converter package root. Decision D-2.
- Q: Does this issue change the portal display? A: No. The data contract ships now. The display ships with issue 4637. Decision D-3.
- Q: Is Hub syslog mapped? A: No. The gateway device profile has no syslog property (R45). Decision D-7.
- Q: Does this record reuse source text? A: No. Source lines serve observation only (R72 to R81). Decision D-16 covers the related serialization.
