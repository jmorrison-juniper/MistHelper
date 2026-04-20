# Feature Specification: Polyglot Database Migration

**Feature Branch**: `184-polyglot-db-migration`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: User description: "Replace SQL everywhere we can in this project when running as a container, with Redis and ArangoDB containers bundled together. Minimize or eliminate the use of SQLite and other SQL variants. Snapshot frequency: on-change, and periodic when load is lite. Retention policy: as much as storage can hold, then rollover the oldest."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Container Deployment with Multi-DB Backend (Priority: P1)

As a NOC engineer deploying MistHelper in a container, I want the system to automatically use ArangoDB and Redis instead of SQLite so that I get richer data storage with graph relationships and time-series capabilities without any manual database setup.

**Why this priority**: This is the foundational change. Without multi-DB container deployment, no other features in this spec work. Every menu operation that currently writes to SQLite must route to the correct backend database.

**Independent Test**: Deploy using `podman-compose up` and run Menu 11 (org sites export). Verify data is stored in ArangoDB (not SQLite) and CSV output still works identically.

**Acceptance Scenarios**:

1. **Given** a fresh `podman-compose up` deployment, **When** the containers start, **Then** MistHelper, ArangoDB, and Redis containers are all running and connected on the same network.
2. **Given** a running multi-container deployment, **When** a user runs any data extraction menu operation (1-86), **Then** data is persisted to ArangoDB or Redis (based on data type) AND CSV output is produced identically to the current behavior.
3. **Given** a running deployment, **When** the ArangoDB or Redis container is temporarily unavailable, **Then** MistHelper logs a clear error message and continues operating with CSV-only output without crashing.

---

### User Story 2 - Natural Key Entities Stored in ArangoDB (Priority: P1)

As a NOC engineer, I want all configuration and inventory data (sites, devices, templates, WLANs, PSKs, networks) stored in ArangoDB as documents so that I can later query relationships between entities and view historical snapshots.

**Why this priority**: Configuration/inventory data is the largest category of menu operations. This covers all `natural_pk` entities in the current `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary.

**Independent Test**: Run Menu 12 (org inventory), then query ArangoDB to verify device documents exist with correct fields and natural primary keys preserved.

**Acceptance Scenarios**:

1. **Given** a device inventory pull via Menu 12, **When** data is ingested, **Then** each device is stored as a document in an ArangoDB collection with its Mist API UUID as the document key.
2. **Given** an existing device document in ArangoDB, **When** the same device is pulled again with updated fields, **Then** the document is upserted (updated in place, not duplicated).
3. **Given** multiple entity types (sites, devices, templates), **When** they are stored, **Then** graph edges are created representing relationships (site contains device, template assigned to site).

---

### User Story 3 - Time-Series Metrics Stored in Redis TimeSeries (Priority: P1)

As a NOC engineer, I want all statistical and performance data (device stats, port stats, SLE metrics, client counts) stored in Redis TimeSeries so that I get efficient time-range queries and automatic downsampling.

**Why this priority**: Time-series data is the second largest category. Redis TimeSeries is purpose-built for this access pattern and enables future "time voyager" visualizations.

**Independent Test**: Run Menu 13 (org device stats), then query Redis to verify time-series keys exist with correct labels and data points.

**Acceptance Scenarios**:

1. **Given** a device stats pull via Menu 13, **When** data is ingested, **Then** each metric (CPU, memory, throughput, etc.) is stored as a Redis TimeSeries key with appropriate labels (device_id, site_id, metric_name).
2. **Given** existing time-series data, **When** new data points arrive for the same metric, **Then** they are appended to the existing time-series (not overwritten).
3. **Given** a Redis TimeSeries key, **When** storage capacity is reached, **Then** the oldest data points are automatically trimmed per the retention policy.

---

### User Story 4 - Automatic Data Routing by Endpoint Type (Priority: P2)

As a developer maintaining MistHelper, I want data to be automatically routed to the correct backend (ArangoDB vs Redis) based on the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` configuration so that adding new menu operations requires minimal changes.

**Why this priority**: This is the internal architecture that makes the system maintainable. Without automatic routing, every new menu operation requires manual backend selection.

**Independent Test**: Add a new test endpoint to `ENDPOINT_PRIMARY_KEY_STRATEGIES` with type `natural_pk` and verify it automatically routes to ArangoDB without any additional code.

**Acceptance Scenarios**:

1. **Given** an endpoint configured with `type: natural_pk`, **When** data is written, **Then** it is routed to ArangoDB as a document collection.
2. **Given** an endpoint configured with `type: composite_pk`, **When** data is written, **Then** it is routed to Redis TimeSeries with composite labels.
3. **Given** an endpoint configured with `type: auto_increment_with_unique`, **When** data is written, **Then** it is routed to ArangoDB with auto-generated keys.

---

### User Story 5 - Config Snapshot on Change with Periodic Fallback (Priority: P2)

As a NOC engineer, I want MistHelper to capture configuration snapshots whenever a change is detected and periodically during low-load periods so that I have a complete history of my network configuration.

**Why this priority**: Snapshots enable the future "time voyager" feature. On-change capture ensures no configuration change is missed; periodic capture fills gaps when webhooks are unavailable.

**Independent Test**: Modify a WLAN configuration via the Mist dashboard, then verify MistHelper captured a new snapshot document in ArangoDB with a timestamp and diff from the previous version.

**Acceptance Scenarios**:

1. **Given** a running MistHelper with webhook integration, **When** a configuration change event is received from Mist, **Then** a new snapshot document is stored in ArangoDB with the full config and a timestamp.
2. **Given** no configuration changes for a configurable idle period, **When** the periodic timer fires, **Then** MistHelper polls the current config and stores a snapshot if it differs from the last stored version.
3. **Given** a config snapshot, **When** a user requests the history, **Then** the system returns an ordered list of snapshots with timestamps and can produce a diff between any two snapshots.

---

### User Story 6 - Storage-Aware Retention with Oldest-First Rollover (Priority: P3)

As a system administrator, I want MistHelper to automatically manage data retention by using all available storage and rolling over the oldest data first so that I never need to manually clean up databases.

**Why this priority**: Without retention management, storage will eventually fill up and cause failures. This is important but can ship after the core migration.

**Independent Test**: Configure a small storage limit in a test environment, ingest enough data to exceed it, and verify the oldest records are automatically removed while newest data is preserved.

**Acceptance Scenarios**:

1. **Given** a configurable maximum storage threshold per database, **When** storage usage exceeds the threshold, **Then** the oldest data is automatically purged until usage drops below the threshold.
2. **Given** a Redis TimeSeries key, **When** the retention policy triggers, **Then** data older than the calculated cutoff is trimmed while downsampled aggregates are preserved.
3. **Given** ArangoDB document collections, **When** the retention policy triggers, **Then** the oldest snapshot versions are removed while at least one snapshot per entity is always retained.

---

### User Story 7 - Standalone Mode Backward Compatibility (Priority: P3)

As a user running MistHelper directly on a host (not in a container), I want the tool to continue working with CSV output even when ArangoDB and Redis are not available so that standalone mode is not broken by this migration.

**Why this priority**: Standalone mode must not regress. Container mode is the target for polyglot DB, but standalone users should not be forced to install ArangoDB and Redis.

**Independent Test**: Run `python MistHelper.py --menu 11` on a host without ArangoDB or Redis installed. Verify CSV output is produced and no errors are thrown.

**Acceptance Scenarios**:

1. **Given** MistHelper running in standalone mode without ArangoDB/Redis, **When** a menu operation is executed, **Then** data is exported to CSV only and no database connection errors occur.
2. **Given** MistHelper running in standalone mode, **When** ArangoDB and Redis are available on configurable host/port, **Then** MistHelper connects and uses them as backends in addition to CSV.

---

### Edge Cases

- What happens when ArangoDB is available but Redis is not (or vice versa)? The system should operate in degraded mode, routing data only to the available backend plus CSV.
- What happens when a document exceeds ArangoDB's maximum document size? Large API responses (e.g., full org inventory) should be split into individual documents per entity, not stored as a single blob.
- What happens when Redis TimeSeries runs out of memory? The retention policy should prevent OOM by proactively trimming, and Redis should be configured with a max-memory eviction policy as a safety net.
- What happens when network connectivity between containers is interrupted mid-write? Writes should be atomic per entity with retry logic, and partial writes should not corrupt data.
- What happens when migrating from an existing SQLite deployment to polyglot? A one-time migration tool should export existing SQLite data into ArangoDB/Redis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route data to ArangoDB or Redis TimeSeries based on the endpoint's primary key strategy type when running in container mode.
- **FR-002**: System MUST maintain CSV output for all menu operations regardless of backend database availability.
- **FR-003**: System MUST store `natural_pk` and `auto_increment_with_unique` entities as ArangoDB documents with Mist API UUIDs as document keys where available.
- **FR-004**: System MUST store `composite_pk` time-series data as Redis TimeSeries keys with labels for device_id, site_id, and metric_name.
- **FR-005**: System MUST create ArangoDB graph edges representing relationships between entities (org→site, site→device, template→site, device→port).
- **FR-006**: System MUST capture configuration snapshots on-change (via Mist webhooks) and periodically when the system is idle.
- **FR-007**: System MUST implement storage-aware retention that rolls over the oldest data first when storage thresholds are reached.
- **FR-008**: System MUST support Redis TimeSeries downsampling rules (e.g., 1-minute granularity for 7 days, 1-hour granularity for 90 days, 1-day granularity beyond 90 days).
- **FR-009**: System MUST add ArangoDB and Redis services to `compose.yml` with appropriate volume mounts, network configuration, and health checks.
- **FR-010**: System MUST fall back to CSV-only output when running in standalone mode without ArangoDB/Redis available.
- **FR-011**: System MUST provide a one-time migration utility to export existing SQLite data into ArangoDB and Redis.
- **FR-012**: System MUST support configuring database connection parameters via environment variables in `.env`.
- **FR-013**: System MUST upsert documents in ArangoDB (insert or update based on document key) to prevent duplicates, matching current SQLite `INSERT OR REPLACE` behavior.
- **FR-014**: System MUST operate in degraded mode when only one of the two backends (ArangoDB or Redis) is available, routing data to the available backend plus CSV.

### Key Entities

- **ArangoDB Collections (Documents)**: Sites, Devices, Templates (AP/Switch/Gateway/RF/Network), WLANs, PSKs, Networks, Services, Webhooks, Admins, API Tokens, Licenses, Alarms, Events, Audit Logs, Config Snapshots.
- **ArangoDB Collections (Edges)**: OrgContainsSite, SiteContainsDevice, TemplateAssignedToSite, DeviceHasPort, ClientConnectedToDevice.
- **Redis TimeSeries Keys**: Device stats (CPU, memory, throughput per device), Port stats (traffic, errors per port), SLE metrics (per site/AP), Client metrics (count, signal, throughput), License usage over time.
- **Config Snapshots**: Versioned documents in ArangoDB with timestamp, config hash, full config body, and diff from previous version.
- **Retention Policy Config**: Per-collection/per-key retention rules defining max age, max storage, and downsampling tiers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 160+ menu operations produce identical CSV output compared to the current implementation (zero regression in data content or format).
- **SC-002**: Container deployment via `podman-compose up` starts all three services (MistHelper, ArangoDB, Redis) within 60 seconds on a standard machine.
- **SC-003**: Data ingestion throughput is at least equivalent to current performance (no perceptible slowdown for the user).
- **SC-004**: Time-series queries return results for any time range within retained data in under 1 second for up to 100,000 data points.
- **SC-005**: Configuration snapshots capture 100% of changes detected via webhooks with zero data loss during normal operation.
- **SC-006**: Storage retention rollover operates without manual intervention and maintains at least the most recent snapshot for every entity.
- **SC-007**: Standalone mode (no containers) continues to work with CSV output with zero breaking changes to existing user workflows.
- **SC-008**: The migration from an existing deployment preserves all historical data with field-level accuracy.

## Assumptions

- ArangoDB Community Edition (Apache 2.0 license) is sufficient; Enterprise features are not required.
- Redis Stack (which includes the TimeSeries module) is available as a container image.
- The existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary provides sufficient metadata to automatically route data to the correct backend.
- Mist webhook integration for on-change snapshots uses the existing webhook infrastructure already present in MistHelper.
- Network connectivity between containers on the same compose network is reliable and low-latency.
- The `data/` volume mount pattern continues to be used for ArangoDB and Redis persistent storage.
