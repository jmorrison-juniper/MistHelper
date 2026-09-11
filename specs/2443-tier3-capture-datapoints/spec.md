# Feature Specification: Expose every Tier 3 capture datapoint to operators

**Feature Branch**: `2443-tier3-capture-datapoints`

**Created**: 2026-09-10

**Status**: Draft

**Input**: User description: "fix(upgrade-portal): expose every Tier 3 capture datapoint to operators (GitHub issue #2443)"

**Linked issue**: jmorrison-juniper/MistHelper#2443

## Live evidence (2026-09-10)

Reproduced on a clean build of `main` (image `misthelper:2443-baseline`, built directly
from the checkout, not the stale/orphaned local `:latest` tag).

- Org: Morrison House, Site: Morrison House Site (9 devices: 1 switch, 1 gateway, 6 APs, 1
  disconnected router).
- Capture `cap-92ee161a3fa24761a4c0b476bdea3412-01`, Tier 3, **Verified**, 40,738 bytes
  stored.
- Capture progress list reports all six sections **done**: Devices, Wired clients,
  Wireless clients, Guest clients, Extra data, Alarms.
- The rendered capture page shows only three tables: **Devices** (9 rows), **Wired
  clients**, and **Wireless clients**. Guest clients and every Tier 3 section are entirely
  absent from the page — no heading, no table, no empty-state message.
- The JSON export (`/api/captures/<id>/export?format=json`) contains **61 rows total**,
  all of kind `device` (9), `client_wired` (35), or `client_wireless` (17). Zero rows of
  kind guest client, switch port, PoE, radio, tunnel, BGP peer, or alarm, even though the
  capture is Verified and reports those sections as done and non-empty.
- Root cause confirmed in code: `capture/extras.py` and the collector already gather all
  Tier 3 data server-side and store it in the capture document. The loss happens entirely
  in the presentation and export layers: `capture/tables.py`'s `page_tables()` only builds
  device/wired/wireless rows, `capture/export.py`'s `build_rows()` only emits
  device/wired/wireless/guest row kinds (and guest is defined but never populated from the
  stored guest list), and `capture.html` never renders a Guest clients heading or any of
  the six Tier 3 headings.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator reviews full Tier 3 capture on the capture page (Priority: P1)

An operator runs a Tier 3 capture before an upgrade and needs to see every datapoint the
portal actually gathered — guest clients, switch ports, PoE budget/draw, radio config,
tunnels, BGP peers, and alarms — directly on the capture results page, not just devices
and non-guest clients.

**Why this priority**: This is the core defect. Operators currently believe Tier 3 data
was not collected at all (it's silently dropped), which can lead to unsafe upgrade
decisions (e.g., missing a critical alarm or a BGP peer that will drop during the
upgrade).

**Independent Test**: Start a Tier 3 capture against a site with guest clients, switch
ports, PoE devices, radios, tunnels, BGP peers, and alarms; open the completed capture
page; confirm all eight tables (devices, wired clients, wireless clients, guest clients,
switch ports, PoE, radios, tunnels, BGP peers, alarms) are present and populated with the
correct row counts.

**Acceptance Scenarios**:

1. **Given** a Verified Tier 3 capture with non-zero rows in every section, **When** the
   operator opens the capture page, **Then** every section (guest clients, switch ports,
   PoE, radios, tunnels, BGP peers, alarms) renders as a labeled table with the expected
   rows, matching the counts stored in the capture document.
2. **Given** a Verified Tier 3 capture where one or more Tier 3 sources returned no data or
   failed to read (e.g., no BGP peers configured, or the alarms call failed), **When** the
   operator opens the capture page, **Then** the section still renders with a clear
   empty-state message (e.g., "No rows." or the stored reason such as "This site has no
   BGP peers") instead of disappearing silently.

---

### User Story 2 - Operator downloads Tier 3 data as CSV/JSON for offline review (Priority: P1)

An operator exports a capture for a change-management ticket or offline diff and expects
the export to contain every datapoint that was collected, not just devices and non-guest
clients.

**Why this priority**: Exports are the audit trail attached to change tickets; a partial
export is a compliance and safety gap equal in severity to a partial page render.

**Independent Test**: Start a Tier 3 capture, download both CSV and JSON exports, and
verify row counts/kinds for guest clients and all six Tier 3 sections match the page and
the underlying stored capture document.

**Acceptance Scenarios**:

1. **Given** a Verified Tier 3 capture, **When** the operator downloads the JSON export,
   **Then** the `rows` array contains rows with `kind` values for guest client and each of
   the six Tier 3 sections, with counts matching the page tables.
2. **Given** the same capture, **When** the operator downloads the CSV export, **Then**
   the CSV contains the same rows (by kind and count) as the JSON export, with
   section-appropriate columns and no credential-like fields.

---

### User Story 3 - Tier 2 captures are unaffected (Priority: P2)

An operator who intentionally runs a Tier 2 (lighter) capture should not see broken pages,
spurious Tier 3 tables, or export regressions — only an explicit "Tier 3 not requested"
style message where Tier 3 content would otherwise appear.

**Why this priority**: Regression protection — Tier 2 is the higher-volume, faster capture
path and must not be destabilized by this fix.

**Independent Test**: Start a Tier 2 capture and confirm the capture page and both exports
behave exactly as before (devices/wired/wireless only) plus a clear "Tier 3 not requested"
note, with no empty Tier 3 tables or errors.

**Acceptance Scenarios**:

1. **Given** a Verified Tier 2 capture, **When** the operator opens the capture page,
   **Then** guest clients and the six Tier 3 sections show a "not requested" message (not
   an empty table, not an error), and devices/wired/wireless render exactly as before.
2. **Given** the same Tier 2 capture, **When** the operator downloads CSV/JSON, **Then**
   the export contains only device/wired/wireless/guest-absent rows, unchanged from
   current behavior.

### Edge Cases

- A Tier 3 section's cloud call fails (e.g., alarms endpoint errors) → section renders
  with the stored failure reason, not a blank gap or a 500 error.
- A Tier 3 section legitimately has zero items (e.g., no guest clients configured) →
  section renders with an explicit "No rows" state, distinguishable from "not requested"
  and from "call failed".
- Row count for any Tier 3 section exceeds the existing `TABLE_ROW_CAP` (500) → table
  shows the capped rows plus a "N additional rows not shown" note, consistent with the
  existing device/client tables.
- A field in a Tier 3 row matches `CREDENTIAL_WORDS` → the field is filtered out of both
  the page table and the export, consistent with existing device/client filtering.
- Guest client list is empty but Tier 3 was requested → "No rows" state, not "not
  requested".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The capture page MUST render a labeled table for guest clients whenever a
  capture includes client data, showing the same row cap and empty-state conventions as
  the existing wired/wireless tables.
- **FR-002**: The capture page MUST render a labeled table for each of the six Tier 3
  sections (switch ports, PoE, radios, tunnels, BGP peers, alarms) whenever a Tier 3
  capture is Verified, using the field lists already defined in `capture/extras.py`.
- **FR-003**: Each Tier 3 section MUST distinguish three states: "not requested" (Tier 2
  capture), "no rows" (requested, zero items), and "unavailable" (requested, call failed —
  showing the stored reason string).
- **FR-004**: The CSV and JSON exports MUST include rows for guest clients and all six
  Tier 3 sections with stable `kind` values, matching the counts shown on the page.
- **FR-005**: Tier 3 export rows MUST pass through the existing credential-field filter
  (`CREDENTIAL_WORDS` / `is_credential_field()`) before being written to any table or
  export.
- **FR-006**: Tier 3 table rows MUST use the existing `TABLE_ROW_CAP` / `capped()` pattern,
  reporting a held-row count rather than silently truncating.
- **FR-007**: Tier 2 captures MUST continue to render/export exactly as before for
  devices/wired/wireless, with an explicit "Tier 3 not requested" message in place of each
  Tier 3 section (not an empty table, not an error).
- **FR-008**: Automated browser tests MUST fail (not skip) when Tier 3 data exists in a
  capture but is not rendered or not exported, so this defect class cannot silently
  reappear.

### Key Entities

- **Guest client row**: A client record from the guest client list, following the same
  shape as wired/wireless client rows (host name, MAC, IP, parent device, etc., where
  present).
- **Switch port row**: Per-port data from `SOURCE_PORTS` (`_SWITCH_PORT_FIELDS`).
- **PoE row**: Per-port PoE budget/draw data from the same `SOURCE_PORTS` read
  (`_POE_FIELDS`).
- **Radio row**: Per-radio config/stat data carried in Tier 2's `radio_stat` device field
  (`_RADIO_FIELDS`).
- **Tunnel row**: One row per tunnel from the dedicated tunnels cloud call.
- **BGP peer row**: One row per BGP peer from the dedicated BGP-peers cloud call.
- **Alarm row**: One row per alarm from the dedicated alarms cloud call.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Tier 3 capture against the Morrison House Site re-run after the fix shows
  non-zero rows on the page for guest clients (if any exist) and all six Tier 3 sections
  that have data, with zero silently-dropped sections.
- **SC-002**: The JSON/CSV exports for the same capture contain row counts for each Tier 3
  `kind` equal to the counts shown on the page (zero discrepancy).
- **SC-003**: A Tier 2 capture run before and after the fix produces byte-identical
  device/wired/wireless table and export content (no regression).
- **SC-004**: New/updated Playwright E2E coverage fails when run against the pre-fix code
  path and passes against the fixed code path, demonstrating the test actually detects
  this defect class.

## Assumptions

- The Tier 3 data collector (`capture/extras.py`) already gathers correct data and does
  not need modification; this fix is presentation (`tables.py`, `capture.html`) and export
  (`export.py`) only, plus route wiring (`capture.py`).
- Field lists and section names already defined in `extras.py`
  (`_SWITCH_PORT_FIELDS`, `_POE_FIELDS`, `_RADIO_FIELDS`, `SECTION_NAMES`, reason
  constants) are the source of truth for what each new table/export section must show.
- The existing row-cap (`TABLE_ROW_CAP = 500`) and credential-filtering conventions in
  `tables.py`/`export.py` apply unchanged to the new sections.
- No database schema change is required; the capture document already stores all Tier 3
  data (confirmed by the 40,738-byte Verified capture used for live evidence).
