# Feature Specification: MSP organization list skipped without the listing right

**Feature Branch**: `fix/4919-msp-listing-right` (proposed)

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4919, "Chore: skip the MSP organization list when this account lacks listing rights"

**Related**: #4713 (MSP detection treats refused profile responses as no access)

**Input**: GitHub issue #4919, read on 2026-11-26. Remote `main` commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Glossary

- **Profile grant**: One entry of the `privileges` list in the `GET /api/v1/self` response.
- **MSP grant**: A profile grant with a non-empty `msp_id` string.
- **Listing right**: The right to list the organizations of one MSP. A grant holds it when its `scope` is `msp`.
- **Listing call**: A `listMspOrgs` request for one MSP id.
- **Skipped source**: An MSP id with no grant that holds the listing right. The report sends no listing call for it.
- **Status row**: One `OrganizationScope` record. The report writes it to `CrossOrgOrganizationStatus.csv`.

## Clarifications

### Session 2026-11-26

- Q: Which profile privilege controls the MSP organization listing right? A: The grant `scope` value `msp`. Evidence E1 to E6 in `design/research.md` gives the evidence.
- Q: Does the grant `role` decide the listing right? A: No. No local source names a role that the listing call needs. Unverified item U1 records the gap.
- Q: What happens when a grant has no `scope` key? A: The grant counts as scope `msp`. This rule matches the menu 309 profile reader at `ex_hardware_inventory/scope/profile.py` line 136.
- Q: Does the pending warning change belong to this work? A: No. The change exists only in the local working copy. It stays out of this pull request. Decision D6.
- Q: Does a skipped source appear when another grant holds the listing right for the same MSP id? A: No. The listing call runs for that MSP id, and no skipped row is written. Decision D5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Do not request an MSP list that the account cannot read (Priority: P1)

An operator runs menu 308 with an account. One profile grant names an MSP, but its scope is not `msp`. The report does not send a listing call for that MSP. The status file and the console show the MSP source as skipped, with the reason.

**Why this priority**: For such an account, the listing call fails with HTTP 403 on each run. Removing the call stops the failed requests.

**Independent Test**: A unit test with a fake session records zero listing calls and one skipped status row.

**Acceptance Scenarios**:

1. **Given** a grant with `msp_id` and scope `org`, **When** discovery runs, **Then** no `listMspOrgs` call occurs and one row has `request_status` `skipped`.
2. **Given** the same grant, **When** the console summary prints, **Then** it prints the skipped source count and the reason.

### User Story 2 - Keep the listing call for an MSP-scope grant (Priority: P1)

An operator runs menu 308 with an account that holds a grant with `scope` `msp`. The report calls `listMspOrgs` once for that MSP and adds its organizations, as before.

**Why this priority**: Existing MSP reports must keep the same organizations.

**Independent Test**: A unit test with a fake session records one listing call and adds the organizations from its response.

**Acceptance Scenarios**:

1. **Given** a profile grant with `msp_id` and `scope` `msp`, **When** the report discovers organizations, **Then** one `listMspOrgs` call occurs, and its organizations are added.
2. **Given** that call returns HTTP 403, **When** discovery completes, **Then** the existing failure row remains.

### User Story 3 - Read the skipped status in the report reference (Priority: P2)

A maintainer reads the cross-org report reference. The reference names the `skipped` status, the listing right rule, and the effect on MSP license evidence.

**Why this priority**: Operators must know why an MSP is missing from a run.

**Independent Test**: The reference file has a section that names `skipped` and `scope`.

**Acceptance Scenarios**:

1. **Given** the reference file, **When** a reader searches for `skipped`, **Then** the reader finds the rule and the reason text.

## Edge Cases

- A grant has no `scope` key. The report treats the grant as scope `msp` and sends the listing call.
- Two grants with scope `org` name the same MSP id. The report writes one skipped row for that MSP id.
- One grant with scope `msp` and one grant with scope `org` name the same MSP id. The report sends one listing call and writes no skipped row.
- Scope values `orggroup`, `site`, and `sitegroup` with an `msp_id` are skipped like scope `org`.
- A grant has an `msp_id` that is not a string. The report ignores the grant, as before.
- Every MSP grant is skipped and no direct organization exists. The report writes the skipped row and no "No accessible organization" row.
- The profile read fails. The existing profile failure row remains, and no MSP row is written.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The report MUST check the listing right of each MSP grant before any listing call.
- **FR-002**: The listing right MUST exist when the grant `scope` is `msp` or absent.
- **FR-003**: The report MUST NOT send a `listMspOrgs` request for a grant without the listing right.
- **FR-004**: The report MUST write one status row for each MSP id without a listing right.
- **FR-005**: Each skipped row MUST set `source` to `msp`, `request_status` to `skipped`, and `msp_id` to the MSP id. It MUST set `org_id` and `org_name` to the missing value.
- **FR-006**: Each skipped row MUST set `error` to a reason that names the missing listing right and scope.
- **FR-007**: The console summary MUST print the skipped source count. It MUST print one line for each skipped source, with its reason.
- **FR-008**: The "Organizations discovered" count MUST exclude skipped rows.
- **FR-009**: A grant with the listing right MUST keep the existing listing behavior and failure rows.
- **FR-010**: The change MUST keep the output file names, the CSV column names, and the `discover_organizations` return shape.
- **FR-011**: Each new action MUST log an `info` line before it and a `debug` line after it. Log text MUST use ASCII only.
- **FR-012**: The cross-org report reference MUST describe the listing right, the `skipped` status, and the MSP license effect.
- **FR-013**: The change MUST add one release-note fragment under `changelog.d/`.
- **FR-014**: The unit tests MUST cover the right present, the right absent, a missing scope key, and the console summary.

### Mist Cloud Transport Requirements

- The feature keeps the mistapi method `mistapi.api.v1.msps.orgs.listMspOrgs` with its current arguments. Installed source: `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py` lines 17 and 36 to 38.
- The feature keeps the profile read `mistapi.api.v1.self.self.getSelf`. Installed source: `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` line 17.
- The feature adds no direct HTTP request and no WebSocket transport.

### Key Entities

- **Profile grant**: One privilege entry. Attributes: `msp_id`, `scope`, `role`, and `org_id`. For an MSP grant, the natural key is the pair of `msp_id` and `scope`.
- **MSP source**: One MSP id that the report reads. Natural key: `msp_id`.
- **Status row**: One `OrganizationScope` record. Natural key: `org_id` for an organization row, and `msp_id` with `source` `msp` for an MSP row.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A unit test with only organization-scope MSP grants records zero `listMspOrgs` calls.
- **SC-002**: A unit test with one MSP-scope grant records exactly one `listMspOrgs` call.
- **SC-003**: A unit test captures console output that contains the skipped source line and its reason.
- **SC-004**: Every applicable gate in T-LOCAL-GATES passes for the changed files.
- **SC-005**: Every required remote check passes on the pull request before T-MERGE starts.
- **SC-006**: The pull request does not change `model.py`, so the status row fields stay the same.

## Assumptions

- The pending warning change stays in its own pull request (D6).
- This specification does not check live Mist behavior. The role threshold stays unverified (U1 and U2).
- The installed mistapi version 0.64.1 satisfies the pin in `pyproject.toml` line 29.
- The change adds no menu entry and no primary key strategy.
- The implementation starts only after the human decision D8 approves scheduling. HUMAN-DECISION-REQUIRED.

## Non-Goals

- No role-based gating.
- No change to the other `listMspOrgs` callers in `src`. Analysis item A3 lists them.
- No change to `src/foundation/support/refactors/msp_privilege_detection.py`.
- No change to `mist-ops-platform`.
- No edit to `documentation/api/msps/GET_msps_msp_id_orgs.md`. Analysis item A2 records its stale note.
- No split of the long methods. The plan records that debt as remediation R-1.

Caution: A skipped MSP source adds no organizations to the run. Read the skipped rows before you trust the totals.
