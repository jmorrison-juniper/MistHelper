# Feature Specification: Site Request Admission by Organization

**Feature Branch**: `fix/4921-site-request-admission`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Issue 4921. Runtime: shared request admission rejects a site request when the ledger holds no organization."

## Summary

When shared request admission is on, the request ledger refuses each site request that has no organization. The CLI never gives the ledger an organization, so `listSiteDevices`, `listSiteDevicesStats`, and the shell trigger fail. Menu 309 works around the defect with a per-run binding. This change makes the ledger find the organization of each site by itself. The binding is then removed.

## Clarifications

### Session 2026-11-26

- Q: Which source attributes a site request when no organization listing ran in this process?
  A: The session organization from `ConfigUtils.get_cached_org_id`. When no session organization exists, the request is refused.
- Q: Does the change add a Mist request to find a site organization?
  A: No. The ledger learns from the listing responses that the batch already reads.
- Q: Does the change keep `AdmissionBinding` as a compatibility path?
  A: No. The class, its import, and its call sites are removed, because `AGENTS.md` forbids compatibility shims.
- Q: Does the change include the uncommitted local edits in the working copy?
  A: No. The implementation starts from `main`. See `research.md` section 4.
- Q: Does the subscription-expiry virtual-chassis read change?
  A: Its code does not change. Its site request follows the same attribution rule, so it succeeds when the rule resolves an organization.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a site from the CLI with the cached organization (Priority: P1)

An operator runs a CLI report. The report reads a site that no organization listing returned in this process. The request uses the organization that the session cached.

**Why this priority**: This case is the failure in the issue. It blocks each site read when the CLI has an organization but no listing.

**Independent Test**: A unit test caches a session organization, sends a site request for an unlisted site, and checks the organization that the quota key uses.

**Acceptance Scenarios**:

1. **Given** the session organization is `org-one` and no listing ran, **When** a site request for `site-one` runs, **Then** the request counts against the organization key for `org-one`.
2. **Given** the session organization is not set, **When** a site request for `site-one` runs, **Then** the request is refused with the existing message.

---

### User Story 2 - Run a batch whose worker threads read sites (Priority: P1)

An operator runs menu 309 for one organization. The preview lists the organization sites. Worker threads then read device status and open shells on those sites. The threads use no scope and no binding.

**Why this priority**: This case is the batch path that the issue names. The binding exists only because of this path.

**Independent Test**: A unit test lists sites in one thread, then sends site requests from a worker thread. The requests must be admitted under the listing organization.

**Acceptance Scenarios**:

1. **Given** a listing of `org-two` returned `site-two`, **When** a worker thread sends a site request for `site-two`, **Then** the request counts against the organization key for `org-two`.
2. **Given** menu 309 runs with the change, **When** the batch preview and the batch run finish, **Then** no code path binds the ledger, and each site request succeeds.

---

### User Story 3 - Refuse an unknown site when no organization is known (Priority: P2)

A caller reads a site that no listing returned, and the session holds no organization. The request must fail closed. It must not count against a guessed organization.

**Why this priority**: The fail-closed rule protects the quota accounting. A guess would count the request against the wrong organization.

**Independent Test**: A unit test lists other sites, then sends a request for an unlisted site with no session organization. The request must be refused.

**Acceptance Scenarios**:

1. **Given** a listing of `org-one` returned `site-one`, and no session organization, **When** a site request for `site-two` runs, **Then** the request is refused with the existing message.

---

### Edge Cases

- A site request path has no site segment (`/api/v1/sites`). The rule uses the ledger organization or the session organization. The request fails closed when neither exists.
- A listing returns HTTP 429, HTTP 500, invalid JSON, or a JSON object instead of a list. The ledger learns nothing from that response. The Mist read still returns its normal result.
- The map holds 50,000 entries and a new site arrives. The oldest entry leaves. A later request for the evicted site uses the session organization or fails closed.
- Redis is unavailable. The ledger stops admission for the process, as before. This change does not change that behavior.
- Shared admission is off, because the standalone flag is set or `WAN_SHARED_ADMISSION` is `false`. No ledger exists, and no behavior changes.
- An MSP session caches its home organization. A site that no listing returned belongs to another organization. The fallback counts the request against the home organization.
- Caution: a wrong fallback changes the quota count of one organization. It grants no access and runs no command. The learned map runs first, which limits this case to unlisted sites.
- A site moves to another organization during a process. The map keeps the first value until eviction or restart. This risk is recorded in `plan.md` and in `research.md` item U-2.
- Two threads learn and read at the same time. The map lock keeps each entry whole.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The request ledger MUST learn the organization of each site from each successful GET listing of `/api/v1/orgs/{org_id}/sites`.
- **FR-002**: The site organization map MUST hold at most 50,000 entries. It MUST evict the oldest entry first.
- **FR-003**: A site request MUST resolve its organization in this order: the site organization map, the ledger organization, and the session organization. When no source applies, the request MUST fail closed with the existing message.
- **FR-004**: The session organization MUST come from `ConfigUtils.get_cached_org_id`, supplied when the ledger connects. The read MUST NOT prompt the operator.
- **FR-005**: The learning step MUST NOT raise an error. It MUST skip a response that is not HTTP 200, not JSON, or not a list. It MUST log counts only.
- **FR-006**: The site organization map MUST support concurrent reads and writes from worker threads. A caller MUST NOT register a site, set a context variable, or bind the ledger.
- **FR-007**: The change MUST remove `AdmissionBinding`, its import, its two call sites in `batch.py`, and its test class. It MUST keep `SdkErrorMute`.
- **FR-008**: The change MUST add no Mist request and no direct HTTP call. The learning step MUST use only the responses of existing mistapi calls.
- **FR-009**: A request to an organization path, or to a path with no organization or site segment, MUST keep its current attribution.
- **FR-010**: The change MUST add one changelog fragment under `changelog.d/`. It MUST update the module docstrings and the inline comments of each changed line.

### Mist Cloud Transport Requirements

- The feature observes the responses of these mistapi methods. The change does not call them:
  - `mistapi.api.v1.orgs.sites.listOrgSites` (`.venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py` line 17).
  - `mistapi.api.v1.sites.devices.listSiteDevices` (`sites\devices.py` line 17).
  - `mistapi.api.v1.sites.stats.listSiteDevicesStats` (`sites\stats.py` line 1051).
  - `mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis` (`sites\devices.py` line 3529).
- The shell trigger posts a path built in `src\mist\realtime\websocket_streams\live\runners\utility\triggers\table.py` line 103. It uses the session method `mist_post`. This change keeps that path.
- The feature owns no WebSocket transport. No SDK insufficiency contract is required.
- The feature adds no REST endpoint.

### Key Entities

- **Site organization map**: The in-memory map from site identifier to organization identifier. It holds at most 50,000 entries.
- **Ledger organization**: The organization that the ledger receives when it is built. Production code passes no value.
- **Session organization**: The organization that the session cached. The admission path reads it and never writes it.
- **Organization listing record**: One site record in a successful listing. The rule reads its `id` field.
- **Site request**: One HTTP attempt to a path under `/api/v1/sites/{site_id}`.
- **Quota key**: A Redis key that counts attempts for a credential and for an organization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The eight new unit tests pass. The batch-thread test fails on `main` before the fix.
- **SC-002**: The existing fail-closed test at `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` line 95 passes without change.
- **SC-003**: The listing test records one transport call for each request. The change adds no transport call.
- **SC-004**: A search of `src` and `tests` for `AdmissionBinding` finds no match after the change.
- **SC-005**: The eviction test shows that the map never holds more than 50,000 entries.
- **SC-006**: Each applicable local gate in `design/quickstart.md` passes for the changed files. The symbol gate reports only the intended removal.

## Assumptions

- A1: Mist lists each site under one organization. Moves between organizations are not verified (`research.md` U-2).
- A2: Menu 309 lists the organization sites before it reads any site. The preview reads the organization sites first (`research.md` R72 and R43), and each site-scoped resource read checks the listing first (R41).
- A3: The cached session organization is the organization that the operator selected for the session (`research.md` U-3).
- A4: Shared admission exists only when Redis is configured. The adapter is built only when `RequestLedger.enabled()` is true (`initialize_mist_session.py` line 72).
- A5: The unit tests use a fake Redis client and invented identifiers. They need no Mist token.

## Non-Goals

- NG1: Learning from other endpoints, such as `searchOrgSites` or `listOrgSiteStats`.
- NG2: An exact lookup of each unknown site with `getSiteInfo`.
- NG3: A change to the quota limit (`LIMIT = 5000`), the Redis script, or the credential key format.
- NG4: A change to the MSP detection of issue #4713. That path reads `/api/v1/self`, which has no site segment.
- NG5: A change to the uncommitted working-copy edits, including the context-variable scope and `logger_utils.py`.
- NG6: A correction of the mistapi version text in `.github/copilot-instructions.md` line 21 and the constitution line 279. `analysis.md` records this defect for a separate issue.
- NG7: A change to the shell trigger path, to the batch confirmation, or to any destructive operation.
