# Feature Specification: History Organization Isolation

**Feature Branch**: `jmorrison-juniper-history-organization-isolation`

**Created**: 2026-09-30

**Status**: Ready for planning

**Feature Directory**: `specs/3484-history-org-isolation`

**Issue**: [MistHelper #3484](https://github.com/jmorrison-juniper/MistHelper/issues/3484)

**Scope Extension**: [Audit log comment](https://github.com/jmorrison-juniper/MistHelper/issues/3484#issuecomment-5854527294)

**Input**: User description: "Keep ALL history reads within the selected organization authorized for the current sign-in."

## User Scenarios & Testing *(mandatory)*

The selected organization is the operator's explicit choice in the current signed session.
The current sign-in rules determine whether that choice is authorized.
A foreign record belongs to any organization other than the selected organization.
This includes another organization that the operator can access.

**Existing request forms**:

| Request form | Required scope |
| --- | --- |
| `/history` | The selected organization and all its sites. |
| `/history?site_id=...` | The selected organization and the requested site. |
| `/api/sites/<site_id>/history` | Capture history for the selected organization and the requested site. |
| `/api/sites/<site_id>/runs/history` | Run history for the selected organization and the requested site. |

These paths identify existing entry points.
This feature does not create a new interface.

**Test data**:

Use at least two synthetic organizations, Organization A and Organization B.
Organization A has Site A1 and Site A2.
Organization B has Site B1.
Give both organizations distinct capture, run, operation, and audit records.
Use distinct identifiers, site labels, counts, operator labels, account labels, moments, and operator digests.
Include a session that permits both organizations and a session that permits only Organization A.

### User Story 1 - Read the selected organization's history (Priority: P1)

An operator selects an organization and opens its history without a site restriction.
Every history card describes that organization only.
The operator can read history across its sites without receiving another customer's records.

**Why this priority**: The shared history exposes customer records and operator information.
Organization isolation protects that information and makes history counts correct.

**Independent Test**: Select Organization A and open `/history` against the synthetic shared history.
Inspect the complete rendered HTML, including links, attributes, and embedded values.
Verify the Captures, Runs, Multi-site upgrades, and Audit log cards independently.

**Acceptance Scenarios**:

1. **Given** an operator can access both organizations and selects Organization A.
   **When** the operator opens `/history`.
   **Then** every card contains only Organization A records.
   No stored identifier, label, count, account content, or audit content from Organization B appears.
2. **Given** Organization A has history for Site A1 and Site A2.
   **When** the operator opens history without a site restriction.
   **Then** eligible records from both sites appear within the current page limits.
   Site B1 contributes no rows or totals.
3. **Given** Organization A has no history and Organization B has populated history.
   **When** the operator opens Organization A history.
   **Then** the page shows the existing empty states.
   Capture and run totals are zero.
   The operation and audit cards contain no foreign records.
4. **Given** both organizations have more capture and run records than one page holds.
   **When** the operator reads successive pages for Organization A.
   **Then** rows, totals, and available page links describe Organization A only.
   Adding newer Organization B records does not change those results.
5. **Given** both organizations have multi-site operations.
   **When** the operator opens Organization A history.
   **Then** the Multi-site upgrades card lists only Organization A operations.
   Existing session-ownership rules still control its progress links.

---

### User Story 2 - Refuse an invalid organization selection (Priority: P1)

An operator receives the existing selection or authorization refusal when the selected organization is missing or outside known privileges.
The portal reads no history source before this decision.
The portal does not choose another organization for the operator.

**Why this priority**: Filtering cannot protect history if an invalid selection starts an unrestricted read.
The authorization decision must precede every history read.

**Independent Test**: Exercise all four request forms with controlled sign-in privileges and selection values.
Record calls to capture, run, operation, and audit readers.
Every refused case must record zero calls.

**Acceptance Scenarios**:

1. **Given** the session has no organization selection, an empty selection, or an invalid selection value.
   **When** the operator requests any history form.
   **Then** the portal returns the existing missing-organization refusal before any history read.
   It does not select the first available organization.
2. **Given** known privileges permit Organization A only.
   **When** a saved selection names Organization B or an unknown organization.
   **Then** the portal returns the existing unauthorized-organization refusal before any history read.
   An empty store does not alter this decision.
3. **Given** the sign-in has a known empty privilege list.
   **When** the operator requests history with a saved organization selection.
   **Then** the portal refuses the selection before any history read.
4. **Given** an environment-token session has no available privilege list and explicitly selects Organization A.
   **When** the current identity policy permits the request.
   **Then** history contains Organization A records only.
   The repair does not introduce a new global sign-in policy.
5. **Given** a valid selection becomes unauthorized between page requests.
   **When** the operator requests the next history page.
   **Then** the portal checks the current privileges and refuses before any history read.
6. **Given** the operator has no active sign-in.
   **When** the operator requests any history form.
   **Then** the existing sign-in refusal applies before selection checks or history reads.

---

### User Story 3 - Preserve history for one authorized site (Priority: P1)

An operator reads a site's history within the selected organization.
The site restriction narrows the organization restriction.
It never replaces that restriction.

**Why this priority**: A site identifier must not provide another path to foreign customer records.
Legitimate site history must remain available.

**Independent Test**: Select Organization A and exercise all three site-specific request forms.
Compare Site A1 results with the synthetic expected records.
Repeat the requests for Site B1 and an unknown site.
Inspect complete HTML and JSON responses.

**Acceptance Scenarios**:

1. **Given** Organization A contains populated history for Site A1 and Site A2.
   **When** the operator requests Site A1 history through each applicable request form.
   **Then** capture and run rows include only Site A1 records from Organization A.
   Their totals, ordering, and page limits remain correct.
   The page's audit rows and multi-site operations obey the same site restriction.
2. **Given** the operator can access both organizations but selects Organization A.
   **When** the operator requests Site B1 history.
   **Then** the portal returns the existing successful empty result for the organization-and-site intersection.
   No foreign history content or foreign history totals appear.
   The request does not select Organization B.
3. **Given** the operator selects Organization A.
   **When** the operator requests an unknown site.
   **Then** the empty result does not distinguish that site from a site with no matching history.
   The response does not disclose another organization's records or existence.
4. **Given** Site A1 history spans multiple pages.
   **When** the operator requests a later page.
   **Then** the site restriction remains Site A1.
   Every read still uses the selected, authorized Organization A.
5. **Given** another operator holds the lock for Site A1.
   **When** the signed-in operator reads authorized Site A1 history.
   **Then** history remains available without lock ownership or a typed confirmation.

---

### User Story 4 - Read correctly scoped audit events (Priority: P1)

An operator reads lock actions and inferred expiry events for the selected organization.
An optional site restriction narrows those events.
Audit limits must not remove matching events because foreign events consume the available rows.

**Why this priority**: The Audit log card exposes site identifiers, actions, moments, and operator digests.
Incorrect filtering or expiry inference can expose foreign activity or misstate a site's lock history.

**Independent Test**: Read a synthetic audit trail through bounded and unbounded reads.
Interleave actions across both organizations and both Organization A sites.
Compare the ordered results with explicit expected events.
Include older actions needed to infer an expiry inside a bounded result.

**Acceptance Scenarios**:

1. **Given** the audit trail interleaves Organization A and Organization B events.
   **When** the operator opens Organization A history without a site restriction.
   **Then** the Audit log card contains only Organization A events.
   It retains the current operator digest representation.
2. **Given** Organization A has audit events for Site A1 and Site A2.
   **When** the operator opens Site A1 history.
   **Then** every audit event belongs to Organization A and Site A1.
3. **Given** newer foreign events outnumber a bounded audit limit.
   **When** the operator reads Organization A audit history.
   **Then** the result contains the newest matching events up to that limit.
   Foreign events consume no result positions.
4. **Given** one organization-and-site sequence contains a take after an unreleased take or takeover.
   **When** the reader produces that site's audit history.
   **Then** it infers one expiry before the later take.
   The expiry retains the earlier hold's organization, site, and operator digest.
   Its moment comes from the later take.
5. **Given** one sequence contains a release before its next take and another sequence contains a takeover.
   **When** the reader produces audit history.
   **Then** the release prevents the corresponding inferred expiry.
   A takeover does not itself create an inferred expiry.
   Actions for another site or organization do not alter this sequence.
6. **Given** the same synthetic trail feeds bounded and unbounded reads.
   **When** both reads use the same organization and optional site restriction.
   **Then** the bounded result equals the newest matching events from the unbounded result.
   Earlier events still support correct inference when they fall outside the result limit.

### Edge Cases

- A missing, blank, whitespace-only, or incorrectly typed selection must not become an unrestricted history read.
- A stale selection must fail even when the history store contains no records.
- A known empty privilege list differs from an unavailable privilege list in environment-token mode.
- Permission for another organization does not make that organization part of the current history selection.
- A caller-supplied organization value must not replace the signed selection during a history request.
- Foreign records must not change a selected organization's counts, page boundaries, or empty states.
- An offset beyond the matching records returns the existing empty page with the correct scoped total.
- A record without a matching organization attribution must not appear because its site identifier matches.
- Interleaved audit actions must preserve independent state for each organization-and-site sequence.
- Reused site text across synthetic organizations must not connect their audit sequences.
- An older audit take outside the visible limit can support an inferred expiry inside that limit.
- Missing audit files, damaged audit lines, and legacy action handling retain their current behavior without widening scope.
- An unavailable history source must not trigger an unrestricted retry or foreign-data fallback.

**Verification requirements**:

Use direct no-network contracts with synthetic records from at least two organizations.
Prove the defect with a failing contract before the repair.
Prove the repaired behavior with the same contract after the repair.
Inspect complete HTML and JSON, not only visible table cells.
Check foreign identifiers, labels, counts, page totals, operator content, account content, audit actions, and operator digests.
Include records with missing or mismatched organization attribution.

Exercise the real capture and run store-adapter paths with controlled local test data.
Verify that both receive the selected organization and optional site before counting or pagination.
An injected approximation alone does not satisfy this requirement.
Compatibility with older injected readers must not conceal an unrestricted real-store read.

Prove early refusal with zero calls to all four history sources.
Exercise both bounded and unbounded audit paths.
Test expiry inference, interleaved sites, foreign events, and organization-and-site attribution.
Test expiry inference after both opening actions.
Add a browser journey only if later design changes require separate browser behavior evidence.
Do not repeat these server contracts merely to add browser coverage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every history request MUST require the current active sign-in before any history read.
  Existing sign-in refusal behavior MUST remain unchanged.
- **FR-002**: Every history request MUST require an explicit, valid organization selection from the signed session.
  Missing or invalid selections MUST receive the existing missing-organization refusal before any history read.
  The portal MUST NOT guess or select the first organization.
- **FR-003**: If privileges are known, the selected organization MUST belong to those privileges before any history read.
  Stale, unknown, or excluded selections MUST receive the existing unauthorized-organization refusal.
  A known empty privilege list MUST refuse every organization.
- **FR-004**: Existing selection and identity services MUST remain the authority for organization access.
  The repair MUST preserve current environment-token behavior when the privilege list is unavailable.
  It MUST NOT change global authentication policy or introduce duplicate authorization rules.
- **FR-005**: Every history source MUST restrict records to the selected organization.
  Permission for multiple organizations MUST NOT widen that restriction.
  A requested site or caller-supplied organization MUST NOT replace the signed selection.
- **FR-006**: The organization restriction MUST cover the Captures, Runs, Multi-site upgrades, and Audit log cards.
  It MUST cover stored identifiers, site labels, operator labels, account content, audit content, links, attributes, and embedded response values.
- **FR-007**: Capture and run counts, rows, and page totals MUST apply the organization restriction before pagination.
  An optional site restriction MUST also apply before counting or pagination.
  Foreign records MUST NOT consume page positions or create additional page links.
- **FR-008**: Each site-specific request MUST use the intersection of the selected organization and requested site.
  This rule MUST apply to the history page and both site-history responses.
- **FR-009**: A foreign or unknown site with no matching scoped history MUST return the existing successful empty result.
  Capture and run totals MUST be zero.
  The response MUST NOT confirm foreign stored history or identify the foreign organization.
- **FR-010**: An authorized organization with no matching history MUST retain the existing empty states and zero capture and run totals.
  Populated foreign history MUST NOT cause a fallback to another organization.
- **FR-011**: The organization restriction MUST reach each real history source before rows or totals reach a response.
  Test-reader compatibility MUST NOT silently discard that restriction from a real history read.
- **FR-012**: Every audit result MUST match the selected organization and the optional requested site.
  This requirement MUST apply to bounded and unbounded reads.
  Records without matching organization attribution MUST NOT appear.
- **FR-013**: Audit expiry inference MUST preserve independent state for each organization-and-site sequence.
  Foreign events and other sites MUST NOT open, close, or replace that sequence's hold.
  Result limits MUST NOT remove earlier context needed for correct inference.
- **FR-014**: After an unreleased take or takeover, a new take MUST infer one expiry for the same organization and site.
  A release MUST prevent that corresponding expiry.
  A takeover MUST NOT itself create an inferred expiry.
  The inferred row MUST retain the earlier hold's attribution and the later take's moment.
- **FR-015**: Audit output MUST retain the current one-way operator digest representation, including inferred rows.
  Audit output MUST NOT contain stored operator addresses.
  History responses MUST NOT expose credentials.
- **FR-016**: Multi-site operation history MUST obey the same pre-read selection authorization and selected-organization restriction.
  A site restriction MUST retain only operations that include that site.
  Existing session-ownership rules for progress links MUST remain unchanged.
- **FR-017**: An unavailable history source MUST retain its current failure or availability behavior.
  It MUST NOT trigger an unrestricted read or a fallback to foreign records.
- **FR-018**: Successful history responses MUST preserve their current fields, ordering, limit rules, and unrelated controls.
  Firmware choices, upgrade confirmations, menus, and unrelated page text or style MUST remain unchanged.
- **FR-019**: History access MUST remain read-only and independent of site-lock ownership.
  The repair MUST NOT add a lock check or a typed confirmation.

### Key Entities *(include if feature involves data)*

- **Operator session**: The current sign-in, its organization privileges, and its explicit organization selection.
  An unavailable privilege list differs from a known empty list.
- **Organization**: The customer boundary for every history read.
  One history request uses one selected organization.
- **Site**: The optional restriction within the selected organization.
  A site restriction cannot authorize or select another organization.
- **History record**: A capture, run, or multi-site operation with organization attribution and existing identifiers, counts, operator content, and account content.
  A multi-site operation can reference several sites.
- **Audit event**: A lock action with an organization, site, moment, and operator digest.
  An inferred expiry describes the earlier hold within the same organization-and-site sequence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four request forms expose zero foreign history records or associated content across the complete acceptance matrix.
  The matrix includes at least two organizations and two sites in the selected organization.
- **SC-002**: All missing or unauthorized selection cases refuse before history access.
  Each case records zero capture, run, operation, and audit reads.
- **SC-003**: In every pagination case, displayed capture and run totals exactly match the selected organization and optional site.
  Adding, removing, or reordering foreign records changes zero matching rows, totals, or page boundaries.
- **SC-004**: Operators complete 100% of valid organization-history and site-history journeys on the first request.
  Empty and populated histories retain their existing behavior.
  Operators need no lock ownership or new confirmation.
- **SC-005**: All bounded and unbounded audit cases match the expected ordered events for the selected organization and optional site.
  Every expiry scenario preserves the correct attribution.
  Foreign events create zero false expiries, lost matching events, or foreign result positions.

## Assumptions

- **Refusal default**: All four request forms use the existing missing-organization and unauthorized-organization refusals.
  This scope-only repair does not require a new browser redirect or new refusal wording.
- **Privilege availability**: The existing identity policy permits some environment-token sessions without a privilege list.
  This repair preserves that policy.
  It still requires an explicit organization selection and exact organization restriction.
  An unavailable privilege list does not make an excluded selection valid when privileges are known.
- **Foreign sites**: A foreign or unknown site returns the existing empty result for the organization-and-site intersection.
  The repair does not need a new site-discovery operation.
  It must not disclose foreign stored content or confirm foreign history.
- **Record attribution**: Existing records already identify their organization.
  Records without matching attribution remain excluded.
  The repair does not infer organization ownership from a site value alone or migrate old records.
- **Existing authorities**: Current selection services own the signed organization choice.
  Current identity services own sign-in privileges and authorization refusals.
  Existing capture, run, and multi-site history readers already support organization restrictions.
  Existing audit records already contain organization attribution.
- **Read-only scope**: The repair introduces no persistent writes, schema changes, key changes, or new external dependencies.
  Current retention, backup, recovery, and persistence rules remain unchanged.
  The project constitution remains binding for later planning and implementation.
- **Verification safety**: Acceptance tests use synthetic records and controlled local history sources only.
  They use no network calls, production databases, credentials, or production containers.
  Existing firmware and menu behavior remain outside the repair.
- **Specification boundary**: This step creates only the specification and its separate quality checklist.
  Planning artifacts, implementation, commits, pushes, pull requests, merges, and deployment remain outside this step.
  The app-managed branch and explicit feature directory remain unchanged.
- **Uncertainty**: No blocking uncertainty remains.
  The refusal, foreign-site, privilege-availability, and record-attribution defaults above define the unspecified choices.
