# Feature Specification: Rogue client exports use the client endpoint name

**Feature Branch**: `fix/4732-rogue-client-endpoint`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4732, "[Bug]: Rogue-client exports use the rogue-AP database identity". Menu 29 fetches rogue clients with `listSiteRogueClients`. Its export writer call sends `listSiteRogueAPs`. The endpoint name selects the SQLite primary key, so client rows collapse under the AP key.

## Clarifications

### Session 2026-11-26

- Q: Does Phase 1 repair existing SQLite tables? A: No. Issue comments 2 and 3 keep the shared-writer and publication holds. A repair needs an approved conflict policy first.
- Q: Which endpoint name must menu 29 send? A: `listSiteRogueClients`. The issue body states it. Menu 29 calls `OrgClientSecurityExporter.rogue_clients`.
- Q: May this change edit the reserved test file? A: Yes, for this issue only. Issue comment 2 releases the narrow reservation. The preserved branch and other #2746 paths stay held.
- Q: Does a route change repair existing data? A: No. Issue comment 3 states that a route change alone is not a recovery plan.
- Q: Do the tests call the live Mist API or a live database? A: No. The issue evidence used mocks and synthetic rows. This record keeps that rule.
- Q: Does this change close issue #4732? A: Decision D-10 decides it. The default keeps `Closes #4732` and tracks Phase 2 in a new issue.

## User Scenarios & Testing *(mandatory)*

Story 1 and Story 2 form the minimum viable change. Story 3 is held. Story 4 documents the fix.

### User Story 1 - Client rows use the client endpoint name (Priority: P1)

An operator runs menu 29. The export writer receives the endpoint name `listSiteRogueClients`. A new SQLite table then uses the primary key `client_mac, bssid`.

**Why this priority**: This story fixes the reported defect. Client rows collapse under the AP key until this story ships.

**Independent Test**: Run the unit tests for `rogue_clients` with a mocked collector and a mocked export writer. No live API, file, or database is used.

**Acceptance Scenarios**:

1. **Given** two synthetic client rows with the same `bssid` and `ap_mac` and different `client_mac`, **When** menu 29 runs, **Then** the export writer receives `api_function_name="listSiteRogueClients"`.
2. **Given** menu 29 in normal mode, **When** the collector starts, **Then** the collector receives `mistapi.api.v1.sites.insights.listSiteRogueClients`.
3. **Given** the endpoint name `listSiteRogueClients`, **When** the DDL builder creates a new table, **Then** the DDL contains `PRIMARY KEY (client_mac, bssid)`.

---

### User Story 2 - Rogue AP export and fast-mode cache hits keep their behavior (Priority: P1)

Menu 30 keeps the endpoint name `listSiteRogueAPs`. A fast-mode cache hit in menu 29 or menu 30 returns before any fetch and before any export writer call.

**Why this priority**: The fix must not change the AP export. The cache checks stop a silent second write, as issue comment 1 describes.

**Independent Test**: Run the unit tests for `rogue_aps`, `rogue_clients`, and `_export_rogues` with mocks.

**Acceptance Scenarios**:

1. **Given** one synthetic AP row, **When** `_export_rogues` runs for the AP label, **Then** the export writer receives `api_function_name="listSiteRogueAPs"`.
2. **Given** a fresh CSV file in fast mode, **When** menu 29 or menu 30 runs, **Then** the collector and the export writer receive no call.
3. **Given** an empty collector result, **When** `_export_rogues` runs, **Then** the export writer receives no call and the log names the label.

---

### User Story 3 - Existing SQLite tables stay unchanged until a repair is approved (Priority: P2) - HOLD

A table created by an earlier run keeps its primary key. A later repair stops the write when a table has a different key. The repair reports the conflicts before it changes any row.

**Why this priority**: This story protects operator data that already exists. It needs a human conflict policy and coordination with the shared-writer owners.

**Independent Test**: The Phase 2 test uses a temporary SQLite file. Phase 1 does not run it.

**Acceptance Scenarios**:

1. **Given** a table with another primary key, **When** the later SQLite writer runs, **Then** it stops before insert and reports both keys.
2. **Given** candidate keys with duplicates, **When** the read-only report runs, **Then** it lists the duplicate keys and changes no row.

---

### User Story 4 - SDK documentation names the module that MistHelper uses (Priority: P3)

A developer reads the SDK documentation page for `listSiteRogueClients`. The page names `mistapi.api.v1.sites.insights`. It names menu 29 as the caller.

**Why this priority**: The current page names a module that the installed mistapi SDK does not define. A developer who follows it reaches the wrong code.

**Independent Test**: Read the page. Run `ste-linter` and `markdown-link-check` on the page.

**Acceptance Scenarios**:

1. **Given** the page, **When** a developer reads the SDK section, **Then** the page names `mistapi.api.v1.sites.insights.listSiteRogueClients()`.
2. **Given** the page, **When** a developer reads the MistHelper note, **Then** the note names menu 29 and `OrgClientSecurityExporter.rogue_clients`.

### Edge Cases

- Caution: An existing `OrgRogueClients` SQLite table created before this change keeps the AP primary key. New client rows still collapse in that table until Phase 2 ships.
- ArangoDB receives client rows in the `rogue_clients` collection after Phase 1. The ArangoDB key uses `client_mac` only, so one client on two BSSIDs keeps one document (FR-016).
- Documents that earlier runs replaced in ArangoDB or Redis stay in place. Their cleanup needs an approved plan (FR-017).
- Two client rows with the same `bssid` and `ap_mac` and different `client_mac` both stay in a new SQLite table with the client key.
- A site that returns HTTP 403 or 503 contributes no rows. The other sites continue, as the current code does.
- A stop signal during collection exports the partial list. The current code behaves the same way.
- An empty collector result writes nothing and logs the empty result. The export writer receives no call.
- A row without `client_mac` or `bssid` can fail the SQLite insert, because the schema builder marks key columns `NOT NULL`. Phase 1 does not change this behavior.

## Requirements *(mandatory)*

### Functional Requirements

Phase 1 is ready after the orchestrator authorizes it.

- **FR-001**: The rogue client export MUST send `listSiteRogueClients` as the endpoint name to the export writer.
- **FR-002**: The rogue AP export MUST keep `listSiteRogueAPs` as the endpoint name.
- **FR-003**: The helper `_export_rogues` MUST receive the endpoint name from its caller and MUST NOT hardcode it.
- **FR-004**: The rogue client export MUST fetch rows with `mistapi.api.v1.sites.insights.listSiteRogueClients`.
- **FR-005**: A new SQLite table for rogue clients MUST use the primary key `PRIMARY KEY (client_mac, bssid)`.
- **FR-006**: This change MUST NOT drop, rename, rebuild, or reset any SQLite table, ArangoDB collection, or Redis key.
- **FR-007**: Each rogue export MUST write an info log before the export writer call and a debug log after it.
- **FR-008**: A fast-mode cache hit MUST NOT call the export writer in either rogue export.
- **FR-009**: The reserved test file MUST keep its import lines and the list-type assertion in `TestLoadSiteList`.
- **FR-010**: The SDK documentation page MUST name `mistapi.api.v1.sites.insights` and the menu 29 caller.
- **FR-011**: The change MUST add the changelog fragment `changelog.d/issue-4732-rogue-client-endpoint.md`.
- **FR-012**: The change MUST edit only the Phase 1 files that `plan.md` lists.
- **FR-013**: The pull request body MUST state that existing SQLite tables keep their primary key. It MUST link the Phase 2 issue.

Phase 2 is on hold. Each item below needs the decisions and coordination in `tasks.md`.

- **FR-014**: When an existing table has a different primary key, the SQLite writer MUST stop before inserting and report both keys.
- **FR-015**: Before any migration, a read-only report MUST list missing and duplicate candidate keys, and a verified backup MUST exist.
- **FR-016**: The ArangoDB rogue client vertex key MUST include `bssid` in addition to `client_mac`.
- **FR-017**: Stale AP-keyed rows in ArangoDB and Redis MUST NOT be deleted or rewritten without an approved plan.

### Key Entities

- **Rogue client observation**: One client seen on one rogue BSSID by one reporting AP. Natural key: `client_mac` and `bssid`. Source endpoint: `listSiteRogueClients`.
- **Rogue AP observation**: One rogue BSSID seen by one reporting AP. Natural key: `bssid` and `ap_mac`. Source endpoint: `listSiteRogueAPs`.
- **Existing SQLite table**: A table that an earlier run created. It keeps its primary key in Phase 1.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tests TST-03 and TST-04 pass. Each test fails on the code before the fix.
- **SC-002**: Tests TST-05 and TST-07 pass. The AP endpoint name and the AP behavior do not change.
- **SC-003**: Tests TST-02 and TST-06 prove zero export writer calls on a fast-mode cache hit.
- **SC-004**: Tests TST-09 and TST-10 show the client primary key and the AP primary key.
- **SC-005**: Every applicable local gate in `T-LOCAL-GATES` passes with zero new findings.
- **SC-006**: All required pull request checks pass on the latest commit (`T-REMOTE-CI`).
- **SC-007**: The pull request changes only the Phase 1 files (check CHK-01).
- **SC-008**: No Phase 2 code starts before decisions D-3, D-4, and D-10 and the coordination in T-HOLD-COORD finish.

## Assumptions

- The local checkout matches `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The blob SHA of every cited file matches on `main`.
- The installed mistapi SDK is version 0.64.1. That version satisfies the pin `mistapi>=0.64.0,<0.65`.
- The Mist API accepts `limit=1000` for `listSiteRogueClients`. The OpenAPI `limit` parameter sets no maximum. The live behavior is not verified.
- The operator selects the SQLite output for some runs. The polyglot router writes ArangoDB and Redis for each run when the database layer is available.

## Out of Scope

- The Phase 2 repair of existing SQLite tables. It is on hold (FR-014, FR-015).
- Any change to the ArangoDB key or the Redis namespace in Phase 1 (FR-016).
- Deletion or rewrite of stale AP-keyed rows (FR-017).
- The combined rogue export of menu 24 in `src/foundation/support/refactors/serial_cc/security_events.py`, lines 287 and 293. It needs its own issue (D-9).
- Changes to menu titles, menu categories, CSV file names, or CSV columns.
- Changes to `MistHelper.py`, `README.md`, or the generated menu reference. `README.md` holds no rogue export text.
