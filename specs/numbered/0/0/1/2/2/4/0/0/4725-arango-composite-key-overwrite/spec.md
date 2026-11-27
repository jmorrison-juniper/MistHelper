# Feature Specification: ArangoDB Identity Keys for Declared Multi-Field Primary Keys

**Feature Branch**: `fix/4725-arango-composite-key-overwrite`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4725, "Runtime: ArangoDB composite keys overwrite distinct BGP records." The ArangoDB writer derives each document key from the first declared key field only. Two BGP peer records from one router, with one timestamp and two neighbors, receive one document key. The second record replaces the first, and the writer reports two successful writes.

## Clarifications

### Session 2026-11-26

- Q: Which document key does the writer store for a strategy with several key fields? → A: One identity key. It is `identity_` followed by the SHA-256 hex digest of the typed JSON of every declared key value, in declared order. Raw joins are rejected, because ArangoDB keys do not allow `/`, spaces, or `|`, and they advise against `:`.
- Q: Which strategy entries change? → A: Each entry on the ArangoDB write path that declares two or more key fields. The SLE identities and audited exemptions are excluded. At main f03c6c9b this is 121 entries.
- Q: What happens to existing ArangoDB documents? → A: The change deletes, renames, and rewrites nothing. Legacy documents stay in place. Any later migration needs a backup and an approved plan (decision D-7).
- Q: What happens when a declared key field is missing, empty, or not a scalar? → A: The writer stores that record under a UUID key, as the current code does, and logs a count. It does not reject the record.
- Q: Does this change edit the strategy table? → A: No. The table is a shared file with its own owner. The writer reads the table and does not change it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep every distinct BGP peer record (Priority: P1)

An operator runs menu 217 for one site. The Mist response lists several BGP peer records from one router. Each record has a different neighbor, or a different timestamp. The ArangoDB collection keeps every record.

**Why this priority**: A replaced record hides a BGP session change from the operator. The writer reports the replacement as a success, so the operator does not see the loss.

**Independent Test**: Import two BGP records with equal `mac` and `timestamp` and different `neighbor` values into the in-memory collection. Expect two documents.

**Acceptance Scenarios**:

1. **Given** two records with equal `mac` and `timestamp` and different `neighbor`, **When** the writer imports both, **Then** the collection holds two documents.
2. **Given** two records with equal `mac` and `neighbor` and different `timestamp`, **When** the writer imports both, **Then** the collection holds two documents.
3. **Given** two records from two routers with equal `neighbor` and `timestamp`, **When** the writer imports both, **Then** the collection holds two documents.

### User Story 2 - Replace an identical record once (Priority: P1)

An operator repeats the same export. The same BGP record returns. The collection still holds one document for that record.

**Why this priority**: Repeated runs must stay idempotent. The import contract `on_duplicate="replace"` depends on it.

**Independent Test**: Import the same record twice. Expect one document and one update on the second write.

**Acceptance Scenarios**:

1. **Given** one record, **When** the writer imports it twice, **Then** the collection holds one document, and both writes use the same document key.

### User Story 3 - Keep SLE and single-field keys unchanged (Priority: P1)

The SLE trend and window endpoints and every single-field strategy entry keep their current document keys.

**Why this priority**: The SLE behavior has tests and a closed issue (#4003). Single-field keys already identify one stored value.

**Independent Test**: Derive keys for sample records before and after the change. Expect equal values.

**Acceptance Scenarios**:

1. **Given** a sample record for `getSiteSleSummaryTrend`, **When** the writer derives the key, **Then** the key equals the value that `SleTrendIdentity.key` returns.
2. **Given** a record for `listSiteAnomalyEvents` with a timestamp field, **When** the writer derives the key, **Then** the key equals the current single-field value.

### User Story 4 - Keep existing documents (Priority: P2)

An operator runs the updated tool against a collection with legacy documents. The legacy documents keep their keys and content. New writes add identity-key documents.

**Why this priority**: The issue requires preservation before any key migration. Warning: A deletion cannot be undone without a backup.

**Independent Test**: Seed a legacy document in the fake collection. Import a matching record. Expect the legacy document unchanged and one new document.

**Acceptance Scenarios**:

1. **Given** a legacy document under the first-field key, **When** the writer imports a matching record, **Then** the legacy document keeps its key and content. The collection gains one identity-key document.

### User Story 5 - Verify each affected identity contract (Priority: P2)

A maintainer reviews the identity audit before the change merges. The audit lists each affected strategy entry with its declared key fields, its OpenAPI evidence, and one verdict. A guard test fails when an affected entry has no verdict.

**Why this priority**: A wrong key changes stored data for each affected endpoint. The issue requires an endpoint-level contract.

**Independent Test**: Run the audit guard against the strategy table. Expect the examined count and zero unclassified entries.

**Acceptance Scenarios**:

1. **Given** the strategy table at main f03c6c9b, **When** the guard runs, **Then** it prints the examined count of 121 and zero unclassified entries.

### Edge Cases

- A record lacks a declared key field. The writer stores the record under a UUID key and logs the count (FR-006).
- A declared key field is an empty string. The writer treats the value as missing (FR-006).
- A declared key field is `None`, a list, or an object. The writer treats the value as missing (FR-006).
- A declared key field is NaN or infinity. The writer treats the value as missing (FR-006).
- The timestamp is an integer in one response and a float in another. Both values produce one identity key (FR-004).
- The neighbor is an IPv6 address with colons. The identity key stays ASCII and shorter than 254 bytes (FR-005).
- Two records in one batch share every declared key field. One document results, and the import counts both writes, as before (D-12).
- `searchOrgDeviceEvents` receives records with an `id` value. The key changes to an identity key (D-10). The OpenAPI `device_event` schema documents no `id` property.
- A collection is in the exemption table. The writer keeps the legacy key for that collection (FR-009).

### Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The writer MUST derive `_key` from every declared key field. This applies to each ArangoDB strategy entry with two or more key fields. SLE identities and exempt collections are excluded.
- **FR-002**: Two records with different declared key values MUST receive different `_key` values.
- **FR-003**: Two records with equal declared key values MUST receive the same `_key` value.
- **FR-004**: The writer MUST normalize each key value by type. Numbers MUST compare by value. Strings MUST compare exactly. Booleans MUST stay distinct from numbers and strings.
- **FR-005**: Each identity key MUST contain only ASCII letters, digits, and the underscore, and MUST be at most 254 bytes long.
- **FR-006**: The writer MUST treat a missing, empty, null, non-finite, or non-scalar key value as missing. It MUST store that record under a UUID key and count each missing record.
- **FR-007**: Single-field strategy entries MUST keep their current `_key` values.
- **FR-008**: The SLE trend and window identities MUST keep their current `_key` values. The SLE checks MUST run before the new rule.
- **FR-009**: The writer MUST keep the legacy first-field key for each collection in the exemption table. The table MUST list only collections with an audited unique-record contract.
- **FR-010**: The change MUST NOT delete, rename, rewrite, or re-index any existing ArangoDB document, collection, or index.
- **FR-011**: Each import MUST keep `on_duplicate="replace"`.
- **FR-012**: A legacy-document migration MUST NOT run before a backup exists and the operator approves the plan (decision D-7).
- **FR-013**: The change MUST NOT edit `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, the SQLite writers, or the Redis writers.
- **FR-014**: The writer MUST log an info line before each key derivation batch and a debug line after it. Log lines MUST use ASCII text and report counts only.
- **FR-015**: The identity audit MUST cover every effective strategy entry on the ArangoDB write path that declares two or more key fields. Each verdict MUST cite OpenAPI evidence.
- **FR-016**: The change MUST update `documentation/diagrams/core/database-strategy.md` and MUST add one changelog fragment.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature uses the mistapi method `mistapi.api.v1.sites.stats.searchSiteBgpStats`, called by `SiteSearchExporter.bgp_stats`. The change adds no HTTP request and no direct REST call.
- The installed SDK signature is in `.venv\Lib\site-packages\mistapi\api\v1\sites\stats.py`, line 532 (mistapi 0.64.1).
- SDK authentication and endpoint contracts stay unchanged. The change handles no credential.
- Contract-test evidence: the existing parametrized test at `tests/unit/export/test_site_search_exporter.py` line 26 keeps the operation name pair unchanged.

### Key Entities *(include if feature involves data)*

- **BGP peer statistic record**: One Mist `bgp_stats` item. Its declared identity is `mac`, `neighbor`, and `timestamp`. The OpenAPI schema declares all three fields.
- **Strategy entry**: One effective value in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. It holds a type, a primary key field list, and index fields.
- **Identity key**: The `_key` value that the writer derives from all declared key fields of one record.
- **Legacy document**: An ArangoDB document whose `_key` equals the first declared key field value.
- **Identity verdict**: One audit row for one strategy entry. It names the declared fields, the evidence, and the verdict.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The issue fixture keeps two documents for two BGP records with different neighbors. The distinct-router control keeps two documents.
- **SC-002**: Two writes of one BGP record leave one document. The second write reports one update.
- **SC-003**: Key values for each SLE endpoint and each single-field sample match the values from before the change.
- **SC-004**: The fixture run deletes or rewrites zero legacy documents.
- **SC-005**: The identity audit reports 121 examined entries at main f03c6c9b and zero unclassified entries.
- **SC-006**: Each applicable local gate in `design/quickstart.md` reports its expected result.

## Assumptions

- A-1: The Mist response for `searchSiteBgpStats` contains `mac`, `neighbor`, and `timestamp`. The OpenAPI `bgp_stats` schema declares those fields (RC-45, RC-46, RC-47).
- A-2: The strategy table is the declared identity contract. The identity audit confirms or rejects each entry.
- A-3: `import_bulk` with `on_duplicate="replace"` replaces a document that has the same `_key` (RC-120).
- A-4: This change includes no live ArangoDB or live Mist test. Unit tests use the fake collection.
- A-5: Operators accept duplicate documents for legacy records until a separate migration runs.

## Out of Scope

- SQLite device events (#4723) and Redis device events (#4724).
- OSPF identity and the deprecated `peer_ip` key (#4726).
- Rogue-client identity (#4732).
- Duplicate strategy names in the table. Eleven composite definitions are shadowed at main (RC-70). A new issue is recommended (T018).
- The BGP graph mapping that keys vertices by `id`, which the BGP schema does not declare (RC-48, RC-59). A new issue is recommended (T018).
- Timestamp-only strategy identities (RC-74). A new issue is recommended (T018).
- Migration of legacy documents (gated by D-7).
- Live ArangoDB and live Mist tests.
