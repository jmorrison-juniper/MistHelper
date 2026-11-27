# Feature Specification: Organization Config Export Refusal

**Feature Branch**: `fix/4707-organization-config-export-refusal`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4707, "Runtime: organization export treats refused endpoints as empty configuration". Six refused responses produced a saved bundle with six empty lists. The export reported completion, and the structural check accepted the bundle.

## Preconditions and Constraints

- **P-1**: Before you edit `src/mist/resources/org/org_config_migration_manager.py`, issue #4707 needs an explicit handover comment. Authoring found no handover comment.
- **C-1**: The `needs-human-review` label stays on issue #4707 and on its pull request.
- **C-2**: Automatic merge stays off. A human reviews and approves the merge.

## Clarifications

### Session 2026-11-26

- Q: Does an export save a partial bundle when one configuration type is not verified? A: No. The export saves no file. A partial file in `data/` can be chosen by menu 187 and looks complete.
- Q: Can menu 187 import a bundle that was saved before this change? A: No. The bundle must use schema 1.1 and show a verified fetch status for every type. Run menu 58 again.
- Q: Does a dry-run import continue when the destination inventory is not verified? A: No. A preview without conflict data hides conflicts.
- Q: Does the manager retry a refused fetch? A: No. The SDK already retries HTTP 429. A second retry layer adds requests.
- Q: Does the fix add a module beside the manager? A: No. The directory already holds five tracked children, so a new child breaks the five-item rule.
- Q: Does the change enable automatic merge? A: No. Constraint C-2 applies.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export only a verified bundle (Priority: P1)

The operator runs menu 58 for one organization. The export saves a bundle only when all six configuration types are verified. Otherwise, it saves no bundle and names each type that is not verified.

**Why this priority**: A bundle that hides a failed fetch looks complete. An operator can then migrate an incomplete configuration.

**Independent Test**: Mock six refused responses, then six verified empty responses. Inspect the files in a temporary directory and the captured logs.

**Acceptance Scenarios**:

1. **Given** six HTTP 503 responses, **When** menu 58 runs, **Then** no bundle is saved, and one error names the six types.
2. **Given** six HTTP 200 responses with empty lists, **When** menu 58 runs, **Then** one bundle is saved with zero counts and a verified fetch status for each type.
3. **Given** a second page that returns HTTP 503, **When** menu 58 runs, **Then** no bundle is saved, and the completion message is not logged.

---

### User Story 2 - Import only a verified bundle into a verified destination (Priority: P1)

The operator runs menu 187. The import refuses a bundle that does not use schema 1.1 or lacks a verified fetch status for every type. The import also stops when the destination inventory is not verified. In both cases, no object is created.

**Why this priority**: The import creates configuration objects. The tool cannot undo those objects automatically.

**Independent Test**: Use a legacy bundle, a bundle with one type that is not verified, and a destination response of HTTP 403. Count the create calls.

**Acceptance Scenarios**:

1. **Given** a bundle with schema 1.0, **When** menu 187 loads it, **Then** the import stops before the preview and before the prompts.
2. **Given** a bundle whose fetch status for one type is not verified, **When** menu 187 loads it, **Then** the import stops before the prompts.
3. **Given** a verified bundle and a destination response of HTTP 403 for one type, **When** the operator runs a dry run or a live import, **Then** no create call occurs.
4. **Given** a verified bundle and a verified destination, **When** the operator types `IMPORT`, **Then** the import runs as it did before this change.

---

### User Story 3 - Diagnose a stopped run with private logs (Priority: P2)

The operator reads the log of a stopped run. Each error names the organization identifier, the configuration type, and the failure category. The HTTP status appears when the server returns one. The log holds no response body, token, or exception text.

**Why this priority**: The operator needs the cause to repair access. The log must not expose private configuration data.

**Independent Test**: Place a synthetic marker in a response body and in an exception message. Inspect every captured manager log record.

**Acceptance Scenarios**:

1. **Given** a refused type with HTTP 503, **When** the export stops, **Then** the error line names the type and the text `refused, HTTP 503`.
2. **Given** an exception that carries a marker, **When** the fetch fails, **Then** no captured record contains the marker.

---

### Edge Cases

- An HTTP 200 response with an error object and no list payload is invalid.
- An HTTP 200 response with an empty `results` list is verified with zero objects.
- A response without an integer status is unavailable. A transport failure produces this result.
- Statuses 199 and 300 are refused. Statuses 200 and 299 are verified.
- A follow-up page that the SDK does not return is unavailable.
- A bundle with five verified types and one missing type is refused.
- An organization with zero objects in every type exports a complete bundle.
- A destination that refuses one type stops a dry run as well as a live import.
- A source organization that equals the destination organization keeps the existing warning.
- The device profile fetch keeps the gateway filter.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The export MUST record one fetch outcome for each of the six configuration types.
- **FR-002**: A fetch outcome MUST be verified only when every response has an integer HTTP status from 200 through 299.
- **FR-003**: A fetch outcome that is not verified MUST record one category: refused, unavailable, invalid, or exception.
- **FR-004**: A verified empty list MUST stay distinct from a fetch outcome that is not verified, in every log, summary, and bundle.
- **FR-005**: One failed follow-up page MUST make its whole configuration type not verified. The type MUST keep no objects.
- **FR-006**: The export MUST write a bundle only when all six configuration types are verified. Otherwise, it MUST write no file.
- **FR-007**: The export MUST log one error for each type that is not verified. The error MUST name the organization, the type, and the category.
- **FR-008**: The export MUST log the completion message only after it saves a verified bundle.
- **FR-009**: Each saved bundle MUST record schema version 1.1 and the fetch status verified for each configuration type.
- **FR-010**: The import MUST reject a bundle before the preview when its schema is not 1.1 or a fetch status is not verified.
- **FR-011**: The import MUST log the reason for a rejected bundle. It MUST tell the operator to run menu 58 again from the source organization.
- **FR-012**: The import MUST verify the destination inventory before any create call, in dry-run and live modes. An unverified destination MUST stop the import.
- **FR-013**: For verified inputs, the import MUST keep the IMPORT confirmation, the dry-run default, the dependency order, the conflict checks, and the report.
- **FR-014**: Every Mist REST call MUST use a mistapi function. The change MUST NOT add a direct HTTP call or a dynamic SDK call site.
- **FR-015**: The manager MUST read each follow-up page with `mistapi.get_next`. It MUST NOT call `mistapi.get_all`.
- **FR-016**: Logs MUST use ASCII text and `%s` values. Logs MUST NOT contain a secret, a response body, or exception text.
- **FR-017**: The organization name lookup and the create path MUST keep their current behavior.
- **FR-018**: The tests MUST cover each category, status boundaries, empty results, follow-up pages, export outcomes, bundle rejection, destination failure, and log privacy.
- **FR-019**: The module docstring, the inline comments, and the changelog fragment MUST describe the verification rules.

### Mist Cloud Transport Requirements

The feature uses these mistapi methods:

- `mistapi.api.v1.orgs.orgs.getOrg` reads the organization name. This call does not change.
- `mistapi.api.v1.orgs.networks.listOrgNetworks`, `mistapi.api.v1.orgs.services.listOrgServices`, `mistapi.api.v1.orgs.vpns.listOrgVpns`, `mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates`, `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles` with `type` set to `gateway`, and `mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies` read the six configuration types.
- `mistapi.get_next` reads each follow-up page. The six create functions do not change.

No owned WebSocket transport enters this change. Contract-test evidence:

- SDK insufficiency: `test_the_sdk_paging_helper_hides_a_refused_body` and `test_status_boundaries_decide_verification` show that the SDK returns a response for an HTTP refusal and does not raise.
- SDK authentication: `test_each_list_call_uses_the_documented_path` checks that the manager session is the first argument.
- SDK endpoint parity: `test_each_list_call_uses_the_documented_path` checks each documented path.
- Failure safety: the export and import tests in tasks T002 and T004.
- Secret redaction: `test_an_exception_is_not_verified_and_logs_the_type_only` and the export log privacy test.

### Key Entities

- **ConfigFetchOutcome**: The result of one configuration type fetch. It holds the type key, the verified flag, the objects, the failure category, and the HTTP status when the server returns one.
- **Bundle**: The JSON file in `data/` that holds six configuration lists and metadata.
- **Fetch status**: The map in bundle metadata. It holds the verification state for each configuration type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Six refused responses produce zero saved files and one error line that names six types.
- **SC-002**: Six verified empty responses produce one bundle with zero counts and six verified fetch statuses.
- **SC-003**: A legacy bundle, an unverified bundle, and an unverified destination each produce zero create calls.
- **SC-004**: One boundary matrix refuses statuses 199 and 300 and verifies statuses 200 and 299.
- **SC-005**: No captured manager record contains the response marker or the exception marker.
- **SC-006**: The local gates report zero failures, and the SDK guard baselines do not grow.

## Assumptions

- The SDK returns a response object for an HTTP refusal and does not raise for it. Research R1 cites the SDK lines.
- The tests use native SDK response objects and mocked sessions. No live Mist request runs in this change.
- Operators keep bundles in `data/` on the host that runs menu 187.
- The migration manager stays in `src/mist/resources/org/`.

## Out of Scope

- The organization name lookup and the create path. PR #4404 and PR #4310 fixed them.
- The retry policy, the page size, and cycle detection for pages. The SDK limits remain.
- Changes to the configuration types, menu numbers, categories, prompts, and file names.
- A bundle format beyond schema 1.1 and the fetch status map.
- Deployment and live validation.

Warning: a partial import can create duplicate or overlapping objects. The tool cannot undo those objects automatically.
