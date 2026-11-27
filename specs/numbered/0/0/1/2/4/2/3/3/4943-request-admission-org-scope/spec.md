# Feature Specification: Ship the preserved admission scope work

**Feature Branch**: `fix/4943-request-admission-org-scope` (created in T003)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4943 preserves the unfinished work of 2026-11-24 on the branch `chore/4943-preserve-wip-2026-11-24`. Issue #4921 records the defect that this work repairs. This specification defines how the work ships to `main`.

**Record path**: `specs/numbered/0/0/1/2/4/2/3/3/4943-request-admission-org-scope/`

## Terms

Each term names one concept. Use only these terms in this record.

- **Organization scope**: The block that names the organization of the site requests inside it. Code name: `OrganizationScope.block`.
- **Shared admission**: The Redis-backed `RequestLedger` and `AdmittedAdapter` that count each Mist request.
- **Site request**: A Mist request with `sites` as the fourth path segment.
- **Credential fingerprint**: The SHA-256 hex digest of the authentication header.
- **Frame locals**: The local variables that a traceback frame holds.
- **SDK error line**: A record at ERROR level that the `mistapi` logger writes.
- **MSP organization list**: The result of the `listMspOrgs` call.
- **VC status read**: The call to `getSiteDeviceVirtualChassis`.
- **Preservation branch**: The branch `chore/4943-preserve-wip-2026-11-24`.
- **Ship**: Merge the change to `main` through T-PR, T-REMOTE-CI, and T-MERGE.

Each code citation names a ref. `main` means commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. `branch` means commit `5213149d63be00d4c47c0fe8194d4cbf0eca1f1f`, which holds the five files. The local working copy equals the branch for those five files.

## Clarifications

### Session 2026-11-26

- Q: Which requests does the organization scope change? → A: Only site requests when the ledger holds no organization. Organization paths keep their attribution. Source: `src/interfaces/wan_performance/collection/request_admission.py:102-109` (main).
- Q: Does shared admission run in every session? → A: No. Session setup uses `AdmittedAdapter` only when `RequestLedger.enabled()` returns true. The ledger needs Redis. Sources: `src/foundation/support/refactors/initialize_mist_session.py:72-73` (main) and `request_admission.py:44-53` (main).
- Q: Does the MSP organization list use the site path? → A: No. Its path uses `msps`, so the ledger ignores the organization scope for it. Source: `documentation/mist-api-openapi31yaml.yaml:4081`.
- Q: Does one logger receive every SDK error line? → A: Yes. The SDK creates one logger object named `mistapi`, and its HTTP error lines use that object. Sources: `.venv\Lib\site-packages\mistapi\__logger.py:218` and `.venv\Lib\site-packages\mistapi\__api_request.py:30` and `:242`. A filter on that logger drops those lines.
- Q: Does the default console renderer hide frame locals? → A: No. The structlog default uses `RichTracebackFormatter` with `show_locals` set to true. Sources: `.venv\Lib\site-packages\structlog\dev.py:420` and `:529`.
- Q: Does an explicit color system write escape sequences to a pipe? → A: Yes, unless the `NO_COLOR` variable is set. Rich writes style codes when `_color_system` holds a value. Sources: `.venv\Lib\site-packages\rich\console.py:707-712`, `:725-728`, and `:2136-2144`.
- Q: Does the menu 308 report use more than one thread? → A: No. The report package and the wan_performance collection package hold no thread or async code. Method and results: `design/research.md`, section Method.
- Q: Which mistapi version runs? → A: Version 0.64.1. The pin is `requirements.txt:129`. The lower bound in `pyproject.toml:29` reads 0.64.1. The repository guide, `.github/copilot-instructions.md`, reads 0.64.0.
- Q: What does a transport failure log? → A: The client logs its own error line in `_request_with_retry`. Source: `src/mist/intelligence/reports/subscription_expiry/client.py:40-57` (main). The SDK filter does not apply to that logger.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Count each site request against its organization (Priority: P1)

An operator runs menu 308 with a credential that holds an MSP grant. Shared admission runs during the run. Each VC status read counts against the organization of its chassis, so the report reads each physical member.

**Why this priority**: Without the fix, each VC status read fails closed under shared admission. The report then keeps the logical row and no physical member. Source: `client.py:629-631` (main).

**Independent Test**: Run `test_virtual_chassis_read_is_admitted_under_its_organization` in `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` and `test_site_request_uses_the_scoped_organization` in `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`.

**Acceptance Scenarios**:

1. **Given** an organization scope for `org-one` and a site request, **When** the ledger admits the request, **Then** the request counts against `org-one`.
2. **Given** no organization scope and no ledger organization, **When** the ledger admits a site request, **Then** admission refuses the request with the existing message.
3. **Given** an organization scope that ends with an exception, **When** the next site request runs, **Then** no organization scope is active.

---

### User Story 2 - Read a traceback without a credential (Priority: P1)

An operator reads a traceback from a failed run. No frame local shows a credential. A pipe or a log file receives plain text with no escape sequence.

**Why this priority**: The default formatter prints frame locals, so a local that holds a credential appears in the output. Source: `.venv\Lib\site-packages\structlog\dev.py:420` and `:529`.

**Independent Test**: Run `test_console_renderer_hides_frame_locals` and `test_console_renderer_output_has_no_ansi_on_non_terminal` in `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`.

**Acceptance Scenarios**:

1. **Given** an exception with a credential in a frame local, **When** the console renders the exception, **Then** the output holds no credential text.
2. **Given** a stream that is not a terminal, **When** the console renders an exception, **Then** the output holds no ESC character.
3. **Given** the `NO_COLOR` variable is set, **When** the console renders an exception, **Then** the output holds no color code.

---

### User Story 3 - Read one outcome line for a failed MSP organization list (Priority: P2)

An operator with an MSP grant that the account cannot list sees one warning line. The line names the HTTP status. The report continues with direct organizations, and the failure stays visible in the output rows.

**Why this priority**: The SDK writes its own error lines for the same failure. The issue reports that a run at 16:15 printed those SDK error lines for the denied list. Source: issue #4943, first paragraph.

**Independent Test**: Run `test_failed_msp_listing_logs_one_outcome_and_no_sdk_error_lines` with the values 403 and 500. Run `test_transport_failure_keeps_the_client_error_line` and `test_msp_listing_logs_info_before_and_debug_after` in `test_client.py`.

**Acceptance Scenarios**:

1. **Given** HTTP 403 for the MSP organization list, **When** menu 308 runs, **Then** one warning names HTTP 403, and no SDK error line appears.
2. **Given** HTTP 500 for the MSP organization list, **When** menu 308 runs, **Then** the terminal shows one warning line that names HTTP 500.
3. **Given** a transport failure during the MSP organization list, **When** menu 308 runs, **Then** the client error line appears.
4. **Given** the MSP organization list call returns or raises, **When** the next SDK call runs, **Then** the SDK error line filter is no longer attached.

---

### Edge Cases

- What happens when one organization scope nests inside another? The inner scope applies. On exit, the outer scope applies again.
- What happens when the body of a scope raises? The scope ends before the error leaves the block.
- What happens when the organization identifier is empty? The scope refuses it before it sets a value.
- What happens when shared admission is off? The scope has no effect, because no ledger checks the request.
- What happens when the ledger holds an organization? The ledger keeps its organization. The scope does not change the attribution.
- What happens in a worker thread? The scope value does not pass to a new thread. A site request in that thread fails closed.
- What happens when Redis fails? The ledger stops admission for the process and continues the request. Source: `request_admission.py:91-97` (main).
- What happens when another thread logs an SDK error during the MSP call? The filter drops that record too. No report path starts a thread. Risk R-5 in `plan.md` records this effect.

## Requirements *(mandatory)*

### Functional Requirements

**Sequencing and preservation**

- **FR-001**: The change MUST start from the current `main` and use the five files of the preservation branch as its source.
- **FR-002**: The change MUST wait until PR #4208 lands or releases `request_admission.py` and its test.
- **FR-003**: The change MUST keep the preservation branch until the merge is verified on `main`.

**Shared admission (issue #4921)**

- **FR-004**: A site request MUST count against the organization of the active organization scope when the ledger holds no organization.
- **FR-005**: A site request MUST fail closed when neither the ledger nor the organization scope names an organization.
- **FR-006**: The organization scope MUST end on every exit path, including an exception.
- **FR-007**: The organization scope MUST nest. The inner scope MUST restore the outer scope on exit.
- **FR-008**: The organization scope MUST refuse an empty organization identifier before it sets a value.
- **FR-009**: A request with an organization path segment or a ledger organization MUST keep its current attribution.
- **FR-010**: The ledger MUST store only the credential fingerprint. The ledger MUST NOT store or log the credential.
- **FR-011**: A request without an `Authorization` or `Cookie` header MUST fail closed with the existing message.

**Credential-safe output**

- **FR-012**: Console tracebacks MUST hide frame locals.
- **FR-013**: Console output on a stream that is not a terminal MUST contain no ANSI escape sequence.

**Menu 308 client**

- **FR-014**: The VC status read MUST run inside the organization scope of its organization.
- **FR-015**: A failed MSP organization list MUST log exactly one warning line that names the HTTP status.
- **FR-016**: The MSP organization list call MUST NOT let SDK error lines reach the logging handlers.
- **FR-017**: The SDK error line filter MUST end when the call returns or raises.
- **FR-018**: A transport failure MUST keep the client's own error line.
- **FR-019**: After a failed MSP organization list, the report MUST continue with direct organizations and MUST keep a visible failure row.
- **FR-020**: The MSP organization list call MUST log an info line before the call and a debug line after it.

**Code structure and quality**

- **FR-021**: New behavior MUST live in named classes. Each module MUST hold five top-level names or fewer.
- **FR-022**: The assertion at `test_request_admission.py:141` MUST test the type of the traceback. It MUST NOT test only that a value is not None.
- **FR-023**: Each changed file MUST pass each applicable local gate and each remote check of the pull request.
- **FR-024**: Each new test for a repair MUST fail on the code before the repair. Each regression guard MUST pass before and after the repair.
- **FR-025**: Each Mist REST call MUST use an existing mistapi method. The change MUST NOT add a direct HTTP call.

**Documentation and release**

- **FR-026**: The operator guide MUST state that a denied MSP organization list continues with direct organizations.
- **FR-027**: The change MUST add one changelog fragment named `changelog.d/issue-4943-request-admission-org-scope.md`.
- **FR-028**: The pull request MUST close #4921 and #4943. Its title MUST pass the Conventional Commits check.
- **FR-029**: The first commit of the ship branch MUST add only the specification record.

### Mist Cloud Transport Requirements

- The feature uses two existing mistapi methods. It adds no method, no endpoint, and no transport.
- `mistapi.api.v1.msps.orgs.listMspOrgs(mist_session, msp_id)`. SDK source: `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py:17`. Mist API: `documentation/mist-api-openapi31yaml.yaml:4081-4085`. Reused method: the existing MSP call in `client.py:170` (main).
- `mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(mist_session, site_id, device_id)`. SDK source: `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py:3529`. Mist API: `documentation/mist-api-openapi31yaml.yaml:31433-31464`. Reused method: the existing VC call in `client.py:507` (main).
- The change sends no direct HTTP request and adds no WebSocket transport.
- SDK authentication: the calls use the session that `dependencies.apisession` supplies. The change does not alter that session.
- SDK endpoint parity: the endpoint paths match `documentation/MIST_API_GET_ENDPOINTS.md:331` and `:1223`.
- Failure safety: the 403 test, the 500 test, and the transport test cover the failure paths.
- Secret redaction: the frame-locals test and the fingerprint rule cover the credential path.

### Key Entities

- **Organization scope**: The in-process value that names the organization of the current block. Natural key: the organization identifier. States: unset, active, and ended.
- **Shared admission key**: The Redis key for one credential, `misthelper:api:v1:requests:{fingerprint}`, or for one organization, `misthelper:api:v1:org:{org_id}`. Natural keys: the fingerprint and the organization identifier.
- **Credential fingerprint**: The one-way SHA-256 hex digest of the authentication header. The fingerprint never holds the credential.
- **SDK error line filter**: The process-wide filter on the `mistapi` logger during one MSP call. States: attached and removed.
- **MSP organization list outcome**: The result of one `listMspOrgs` call. Natural key: the MSP identifier. Outcomes: rows (HTTP 200), transport failure (status 0), and HTTP failure (any other status).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every test in `test_request_admission.py` and `test_client.py` passes.
- **SC-002**: A rendered traceback for a credential in a frame local holds zero occurrences of the credential text.
- **SC-003**: Console output on a non-terminal stream holds zero ESC characters.
- **SC-004**: A 403 MSP organization list and a 500 MSP organization list each produce exactly one WARNING record and zero `mistapi` ERROR records.
- **SC-005**: Every applicable local gate reports zero failures. The test quality gate reports `gate: 0 new findings vs baseline`.
- **SC-006**: The diff against `main` changes no file outside the five source files, the operator guide, the changelog fragment, and the specification record.
- **SC-007**: `request_admission.py` holds four top-level names, and `client.py` holds five top-level names.

## Assumptions

- Shared admission runs only when the application store uses Redis. A local run without Redis does not show the defect.
- Menu 308 runs its report work on one thread. The report packages hold no thread or async code.
- The installed mistapi version is 0.64.1, which matches the pin. This record cites the installed source.
- The gate results in the issue comment are reported facts. This record does not reproduce them, because the research task runs no gate.
- A live menu 308 run needs an operator-owned token and a Redis service. The owner runs that check after the merge.
- The five files on the preservation branch hold the same bytes as the local files. The other tracked files equal `main`.

## Out of Scope

- Removing the menu 309 `AdmissionBinding` workaround. A follow-up issue owns that removal (decision D-5).
- Moving the organization scope to the `foundation` package (decision D-3).
- Changing the Redis key names, the hash algorithm, or the attribution of organization requests.
- Changing the parameters of the MSP organization list or the VC status read.
- Changing the output files or the output columns of menu 308.
- Running a live MSP validation as part of this change.
- Editing PR #4208 or its branch.
- Deleting the preservation branch (decision D-11).
