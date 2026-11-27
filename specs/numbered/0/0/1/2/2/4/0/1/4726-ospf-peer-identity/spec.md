# Feature Specification: OSPF Peer Identity Keys

**Feature Branch**: `fix/4726-ospf-peer-identity` (proposed)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4726, "Runtime: OSPF exports overwrite distinct router or neighbor records." Menus 55, 70, and 225 export OSPF peer statistics. Their storage keys drop or reuse identity fields. Warning: Distinct records replace each other, and each writer reports success.

## Clarifications

### Session 2026-11-26

- Q: Which endpoints and menus are in scope? A: `searchSiteOspfStats` (menus 70 and 225) and `searchOrgOspfStats` (menu 55). The count endpoints, `searchOrgBgpStats` (#4725), and the device-event keys (#4723 and #4724) are out of scope.
- Q: Which fields identify one OSPF peer record? A: `mac`, `vrf_name`, `port_id`, `neighbor`, and `timestamp`. `mac`, `neighbor`, and `timestamp` are required. `vrf_name` and `port_id` are scope fields and may be absent.
- Q: What happens when a required field is missing? A: Caution: The whole batch fails before any write, and no row, document, or key is written for it.
- Q: How are absent scope fields stored? A: An absent or empty scope field becomes JSON null in the identity payload. It never becomes the text `unknown`.
- Q: How do existing tables, keys, and documents change? A: They do not change. New SQLite rows go to a `_v2` table. New Redis and ArangoDB values use the identity key.
- Q: Does the CSV output change? A: No. The CSV files keep the same names, columns, and rows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep distinct neighbors in SQLite (Priority: P1)

An operator runs menu 225 or menu 70 for a site. Two OSPF records share a router MAC and a sampling time. Each record names a different neighbor. The SQLite export keeps both records.

**Why this priority**: SQLite is the default durable store. Warning: A silent replacement removes operator data and reports success.

**Independent Test**: Write two site records with the same `mac` and `timestamp`, different `neighbor` values, and no `peer_ip`. Read the `_v2` table. It must hold two rows.

**Acceptance Scenarios**:

1. **Given** two site records with the same MAC and time and different neighbors, **When** the SQLite writer stores them, **Then** the `_v2` table holds two rows.
2. **Given** the same two records in a second run, **When** the writer runs again, **Then** the table still holds two rows and no row is duplicated.
3. **Given** two records that differ only by `vrf_name`, **When** the writer stores them, **Then** the table holds two rows.

---

### User Story 2 - Keep distinct neighbors in Redis and ArangoDB (Priority: P1)

An operator runs menu 55 for an organization. The router sends the same records to the Redis JSON writer and the ArangoDB writer. Each distinct adjacency keeps its own Redis document and its own ArangoDB document.

**Why this priority**: Both backends feed dashboards and queries. Warning: A replaced document looks like a successful write.

**Independent Test**: Route two colliding records through the router with fake Redis and fake ArangoDB backends. Two Redis keys and two ArangoDB keys must exist.

**Acceptance Scenarios**:

1. **Given** two org records differ only by neighbor, **When** the router writes them, **Then** Redis holds two documents.
2. **Given** the same two records, **When** ArangoDB stores them, **Then** the collection holds two documents whose `_key` values differ.
3. **Given** a batch with one record that has neither `neighbor` nor `peer_ip`, **When** the router writes the batch, **Then** the write result reports a failure and no backend receives a write.

---

### User Story 3 - Keep legacy data unchanged (Priority: P2)

An operator upgrades the tool and already holds OSPF data. The legacy SQLite tables, Redis keys, and ArangoDB documents stay in place. The operator guide names the new `_v2` tables.

**Why this priority**: Legacy rows can be the only copy of past samples. Warning: A rewrite removes that copy without notice.

**Independent Test**: Create a legacy table with the old primary key and rows. Run the writer. Compare the schema and row count before and after. Both must match.

**Acceptance Scenarios**:

1. **Given** a legacy table with primary key `mac` and `timestamp`, **When** the writer runs, **Then** the legacy schema and row count do not change.
2. **Given** an existing `_v2` table whose primary key is not `misthelper_ospf_peer_key`, **When** the writer runs, **Then** the write fails and the error names the table.
3. **Given** the operator guide, **When** an operator searches for OSPF tables, **Then** the guide names each `_v2` table and the legacy rule.

---

### Edge Cases

- What happens when `neighbor` is absent and `peer_ip` holds a value? The identity uses `peer_ip` as the neighbor component.
- What happens when `neighbor` and `peer_ip` both exist and differ? The identity uses `neighbor`.
- What happens when `timestamp` arrives as `1700000000` and as `1700000000.0`? Both forms produce one identity key.
- What happens when `timestamp` is negative, text, a boolean, or not finite? Caution: The batch fails before any write.
- What happens when `vrf_name` is absent and another record holds the text `unknown`? The two records keep distinct keys.
- What happens when one batch mixes records with and without `vrf_name`? Each record keeps its own key. A later run can store the same adjacency twice. A duplicate never replaces another record.
- What happens when the CSV write succeeds and the database write fails? The CSV file remains. The failed leg reports its own failure.
- What happens when a `_v2` table exists with another primary key? The SQLite writer fails closed and names the table.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST derive one identity key from mac, vrf_name, port_id, neighbor, and timestamp.
- **FR-002**: The system MUST use neighbor as the neighbor component and peer_ip only when neighbor is absent or empty.
- **FR-003**: The system MUST reject the whole batch before any write when a required component is missing or invalid.
- **FR-004**: The system MUST encode an absent or empty vrf_name or port_id as JSON null in the identity payload.
- **FR-005**: The system MUST write timestamp as decimal text without an exponent, so 1700000000 and 1700000000.0 match.
- **FR-006**: The SQLite writer MUST store OSPF rows in the legacy table name plus `_v2`, keyed by misthelper_ospf_peer_key.
- **FR-007**: The SQLite writer MUST NOT alter, drop, rename, or delete any legacy table.
- **FR-008**: The SQLite writer MUST fail the write when an existing `_v2` table has another primary key.
- **FR-009**: The Redis JSON writer MUST store each OSPF document under the identity key that the router attaches.
- **FR-010**: The ArangoDB writer MUST store each OSPF document with the identity key as its `_key`.
- **FR-011**: The router MUST attach identity keys to OSPF records before the Redis JSON and ArangoDB legs run.
- **FR-012**: The CSV output for menus 55, 70, and 225 MUST keep the same file names, columns, and rows.
- **FR-013**: The strategy entries for searchSiteOspfStats and searchOrgOspfStats MUST name misthelper_ospf_peer_key as primary key.
- **FR-014**: The system MUST keep the primary key of every other endpoint, including searchOrgBgpStats, unchanged.
- **FR-015**: The identity class MUST log an info line before attaching keys and a debug line with the count after.
- **FR-016**: The operator guide MUST name the `_v2` tables and state that legacy tables stay unchanged.
- **FR-017**: The changelog fragment MUST name issue #4726 in one Fixed bullet.
- **FR-018**: The system MUST NOT purge or migrate legacy SQLite tables, Redis keys, or ArangoDB documents.

### Mist Cloud Transport Requirements

- This feature uses existing mistapi methods only. They are `mistapi.api.v1.sites.stats.searchSiteOspfStats` and `mistapi.api.v1.orgs.stats.searchOrgOspfStats`.
- This feature changes no API request, parameter, or response handling.
- No owned WebSocket transport is added or changed. The SDK insufficiency and owned-transport contract tests do not apply.
- Contract evidence for the SDK calls comes from the existing export tests named in tasks T008.

### Key Entities *(include if feature involves data)*

- **OSPF peer record**: One statistic item from `searchSiteOspfStats` or `searchOrgOspfStats`. It holds the router MAC, neighbor address, VRF, interface, timestamp, and state.
- **Required components**: mac, the neighbor component (neighbor, or peer_ip when neighbor is absent), and timestamp.
- **Scope components**: vrf_name and port_id. Each one may be absent, and an absent value encodes as JSON null.
- **Identity key**: The text `ospf_` followed by 64 lowercase hexadecimal characters. It is a SHA-256 digest of the canonical identity payload.
- **Legacy table**: The SQLite table that the earlier writer created. It stays unchanged.
- **v2 table**: The SQLite table named with the legacy name plus `_v2`. Its primary key is misthelper_ospf_peer_key.
- **Legacy key or document**: A Redis key or ArangoDB document that the earlier writer created. It stays unchanged until its own expiry or an operator action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two colliding site records produce two rows in the `_v2` table in one run.
- **SC-002**: Two colliding org records produce two Redis documents and two ArangoDB documents.
- **SC-003**: A batch with one record that lacks neighbor and peer_ip writes zero rows, documents, and keys.
- **SC-004**: The legacy table schema and row count are identical before and after a write.
- **SC-005**: The CSV bytes for a fixed fixture are identical before and after the change.
- **SC-006**: Each new test fails before implementation and passes after it. Each applicable local gate passes.

## Assumptions

- Live Mist records include `neighbor` for each OSPF neighbor. This assumption is unverified. See `design/research.md`, item U-01.
- The installed mistapi is version 0.64.1. This version matches the pin `mistapi>=0.64.0,<0.65`.
- The Redis JSON writer keeps its default TTL of 7 days through `REDIS_JSON_TTL_DAYS`.
- No live Mist request runs for this change. Tests use fake backends and synthetic records.
- Operators read `data/mist_data.db` with a SQLite client. The table name change is documented.

## Non-Goals

- The count endpoints `countSiteOspfStats` and `countOrgOspfStats` write no rows. They stay unchanged.
- The `searchOrgBgpStats` key defect belongs to #4725. The device-event key defects belong to #4723 and #4724.
- The OSPF graph mapping uses `id` as its key field. That defect needs a separate issue. This record does not fix it.
- The generic functions `_build_composite_pk_sql`, `_build_key`, and `_compute_key` keep their current behavior for other endpoints.
- Warning: Purging legacy OSPF data cannot be undone by this tool. The purge decision is recorded as D-9 for a human.
