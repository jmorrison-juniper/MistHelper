# Feature Specification: Redis device event identity

**Feature Branch**: `fix/4724-redis-device-event-identity`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4724, "Runtime: Redis device events overwrite records with the same timestamp"

## Clarifications

### Session 2026-11-26

- Q: Which values identify one device event in Redis? A: A SHA-256 digest of the full row, named `record_id`. The key also holds `org_id` and `timestamp`. The documented schema has no `id` or `device_id` (RC-24). See research D-1.
- Q: Should a missing key field use a sentinel value? A: No. The Redis writer rejects the row and reports a failed write. See research D-3.
- Q: Should the change migrate or purge existing data? A: No migration. Old Redis documents expire by their TTL. A purge needs human approval. See research D-7.
- Q: Does this fix depend on issue #4725? A: No. `record_id` is the first key field, so the ArangoDB key rule works unchanged. See research D-2.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep every device event that shares a timestamp (Priority: P1)

An operator runs a device event export. Two events have the same timestamp and different content. Redis keeps both events.

**Why this priority**: Redis documents serve fast recent-event queries. A silent replacement hides an event from the operator.

**Independent Test**: Run the Redis writer regression test with two events that share one timestamp. Two Redis documents remain.

**Acceptance Scenarios**:

1. **Given** two device events with equal timestamps and different content, **When** the router writes them, **Then** Redis holds two documents under two keys.
2. **Given** one device event without `org_id`, **When** the router writes it, **Then** the write reports one failed record and no key contains `unknown`.

---

### User Story 2 - Separate organizations that share a timestamp (Priority: P1)

Two organizations report device events at the same time. The router keeps both events.

**Why this priority**: The current key omits `org_id`. One organization can replace another organization's event.

**Independent Test**: Write two rows with equal timestamps and different `org_id` values. Two records result.

**Acceptance Scenarios**:

1. **Given** two rows with equal timestamps and different `org_id` values, **When** the router stamps them, **Then** each row gets a different `record_id`.

---

### User Story 3 - Keep the archive and the graph complete (Priority: P2)

An operator queries the ArangoDB archive and the graph. Each distinct device event has its own document and vertex.

**Why this priority**: The graph map reads `id`. A device event without `id` creates no vertex and no site edge.

**Independent Test**: Write one device event with `record_id`, `site_id`, and `mac`. One vertex and one site edge result.

**Acceptance Scenarios**:

1. **Given** two distinct device events, **When** the ArangoDB writer prepares them, **Then** each `_key` equals its `record_id`.
2. **Given** one device event with `site_id`, **When** the graph writer builds edges, **Then** the event links to its site.

---

### User Story 4 - Leave existing data unchanged (Priority: P3)

An operator upgrades the tool. Existing Redis and ArangoDB documents stay in place.

**Why this priority**: Deleted production data cannot be restored. The fix must not delete data.

**Independent Test**: Review the diff. No code path deletes, purges, or rewrites an existing document.

**Acceptance Scenarios**:

1. **Given** an existing Redis key that contains `unknown`, **When** the fix deploys, **Then** the key stays until its TTL ends.

### Edge Cases

- Equal timestamps and different content produce two `record_id` values.
- A repeated identical row produces the same `record_id`. The second write replaces the same document.
- A row without `org_id` or `timestamp` fails the Redis write. Caution: the ArangoDB writer still stores that row under its `record_id`.
- The same event with a changed payload creates a second document. Caution: both documents remain until the Redis TTL ends. ArangoDB keeps both documents.
- A datetime value in a row uses string conversion in the digest.
- A row without `mac` keeps its key and its vertex. Only the device edge to the device is skipped.
- Caution: Old ArangoDB documents keep their old `_key` values. This change does not remove them.

### Out of Scope

- Migration, purge, or rewrite of existing Redis or ArangoDB data. Decision D-7 requires human approval for any purge.
- The same key pattern in `searchOrgTunnelsStats`. A follow-up issue must confirm its schema first.
- The SQLite device event collision (issue #4723), exporter recovery (issues #4721 and #4722), and OSPF identity (issue #4726).
- ArangoDB `_key` fallback to a UUID for other endpoints. Issue #4725 tracks that defect.
- The `unknown` sentinel in the timeseries writer (RC-08). Timeseries keys use a separate path.
- The suggestion generator in `scripts/pk_strategy_suggestions.py` (RC-34, RC-35). It stays unchanged.

### Functional Requirements

- **FR-001**: The router MUST add `record_id` to each `searchOrgDeviceEvents` row before any database write.
- **FR-002**: `record_id` MUST be the SHA-256 hex digest of the canonical JSON of the received row.
- **FR-003**: The router MUST copy each row before it adds `record_id`. CSV and SQLite output MUST NOT change.
- **FR-004**: The device event primary key MUST be `record_id`, `org_id`, and `timestamp`, in that order. The indexes MUST replace `device_id` with `mac`.
- **FR-005**: The Redis key builder MUST NOT substitute `unknown`. It MUST reject a row with a missing or null key field.
- **FR-006**: A Redis write MUST report failure when it rejects a row or when a SET fails.
- **FR-007**: The ArangoDB graph map for device events MUST use `record_id` for vertex keys and edge sources.
- **FR-008**: The change MUST NOT delete, rewrite, or migrate existing Redis or ArangoDB documents.
- **FR-009**: Each changed line MUST carry an inline comment. Each changed action MUST log `info` before it and `debug` after it.
- **FR-010**: The design guide, the contributor guide, and the changelog MUST describe the new key.

### Mist Cloud Transport Requirements

- The feature reads rows through `mistapi.api.v1.orgs.devices.searchOrgDeviceEvents` (RC-62). It adds no direct HTTP request.
- No owned WebSocket transport is required or proposed.
- SDK insufficiency is not claimed. The SDK call, its authentication, and its endpoint stay unchanged.
- Contract tests keep the mocked SDK call. Failure safety is covered by FR-006.
- Secret redaction: the change logs field names and counts only. It logs no row values.

### Key Entities

- **DeviceEvent**: One row from `searchOrgDeviceEvents`. The schema requires `org_id`, `timestamp`, and `type` (RC-25).
- **DeviceEventRecord**: A copy of a DeviceEvent with one added `record_id` field.
- **RedisDocument**: A Redis JSON document at the key `searchOrgDeviceEvents:<record_id>:<org_id>:<timestamp>`.
- **ArangoDocument**: An ArangoDB document whose `_key` equals `record_id`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A regression test keeps two Redis documents for two events with equal timestamps.
- **SC-002**: Two organizations with equal timestamps produce two different `record_id` values.
- **SC-003**: A repeat write of one identical row keeps the same Redis key and the same ArangoDB `_key`.
- **SC-004**: No device event Redis key contains `unknown` after the change.
- **SC-005**: The persistence structure guard passes without a change to its child counts.
- **SC-006**: Every applicable local gate passes, and remote CI passes before the merge.

## Assumptions

- Each live row includes `org_id`, `timestamp`, and `type`, as the schema requires. This is unverified (research U-1).
- Most device events include `mac`. This is unverified (research U-1).
- The Redis TTL default is seven days. The `REDIS_JSON_TTL_DAYS` variable sets it (RC-07).
- One payload produces one digest in every run. This is unverified (research U-2).
- No reader in this repository depends on the old key format. The local search found no reader (research U-5).
