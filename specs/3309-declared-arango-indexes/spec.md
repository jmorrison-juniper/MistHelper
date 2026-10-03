# Feature Specification: Declared ArangoDB indexes

**Feature Branch**: `jmorrison-juniper-declared-arangodb-indexes`

**Created**: 2026-10-01

**Status**: Implementation verified locally. Remote delivery awaits the coordinator grant.

**Input**: Repair [issue #3309](https://github.com/jmorrison-juniper/MistHelper/issues/3309).
The exporter ignores the secondary indexes in its endpoint strategies.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use the declared indexes (Priority: P1)

An operator exports records through the configured ArangoDB backend.
The collection receives each declared secondary index before the writer imports records.
An equal existing index remains unchanged.

**Why this priority**: A query can use its declared field index instead of reading every document.

**Independent Test**: Use the real writer with fake database handles and an unchanged endpoint strategy.
Compare the exact index requests and imported documents.

**Acceptance Scenarios**:

1. **Given** a new collection, **When** the first write starts, **Then** the writer creates each declared field index before import.
2. **Given** an existing collection, **When** the first write starts, **Then** the writer ensures the same declared indexes.
3. **Given** a completed index check, **When** the same strategy writes again, **Then** the writer sends no additional index request.
4. **Given** an empty record list, **When** the writer opens the collection, **Then** it ensures the declared indexes without importing records.

### User Story 2 - Report a failure and retry (Priority: P2)

An operator receives an explicit failure when the database cannot create a required index.
The writer does not import records after that failure.
The next write retries the incomplete index check.

**Why this priority**: A success result must not conceal an incomplete index plan.

**Independent Test**: Fail the second index request.
Verify the exception, diagnostics, unchanged documents, and exact requests on the next write.

**Acceptance Scenarios**:

1. **Given** an index creation error, **When** a write starts, **Then** the writer reports the original error and imports no records.
2. **Given** an incomplete first check, **When** the next write succeeds, **Then** it retries all unconfirmed fields.
3. **Given** a completed strategy, **When** an added field fails, **Then** the next write retains earlier confirmed fields and retries the extension.
4. **Given** a driver error, **When** the router handles it, **Then** its existing failure result remains explicit.

### User Story 3 - Coordinate concurrent writers (Priority: P3)

Concurrent writes share one collection check within the configured database scope.
Independent database scopes do not suppress each other's required indexes.

**Why this priority**: Duplicate initial work adds avoidable database requests and can race with collection creation.

**Independent Test**: Start concurrent real writer calls with controlled fake index requests.
Compare request counts across the same scope and separate scopes.

**Acceptance Scenarios**:

1. **Given** concurrent first writes, **When** one index request waits, **Then** the other writes cannot bypass the incomplete check.
2. **Given** two writer instances for the same database account, **When** both write, **Then** each declared field receives one process-local request.
3. **Given** separate servers, databases, or accounts, **When** each writer starts, **Then** each scope checks its own declared indexes.
4. **Given** a changed field list, **When** another write starts, **Then** it checks only the unconfirmed fields without removing existing indexes.

### Edge Cases

- A missing or empty index list creates no secondary index.
- Duplicate fields receive one request, in their first declared order.
- Reordered or reduced field lists create no duplicate and remove no index.
- Invalid field lists fail before collection creation or document import.
- A new collection clears any earlier confirmation for its name.
- A successful partial server action does not confirm an incomplete field list.
- A transport failure remains visible and permits a later retry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The writer MUST consume the existing strategy's `indexes` without changing the strategy catalog.
- **FR-002**: The writer MUST ensure one non-unique persistent index for each distinct declared field.
- **FR-003**: The writer MUST preserve the declared field text and the first occurrence order.
- **FR-004**: The writer MUST ensure indexes for new and existing collections, including empty writes.
- **FR-005**: The process MUST scope confirmed fields by configured server, database, account, and collection.
- **FR-006**: Concurrent writers MUST share a guard for collection creation and index confirmation within that scope.
- **FR-007**: The process MUST confirm new fields only after every required creation succeeds.
- **FR-008**: A failed check MUST preserve earlier confirmed fields and retry all unconfirmed fields on the next write.
- **FR-009**: The writer MUST log the collection and field before each index request and after each successful request.
- **FR-010**: A failed index request MUST report its exception and checked count without importing records or reporting success.
- **FR-011**: Invalid index declarations MUST fail explicitly before database mutations.
- **FR-012**: The repair MUST preserve business keys, `_key` formation, replacement imports, batching, row counts, and record values.
- **FR-013**: Tests MUST prove the real writer path, failure, retry, concurrency, scope separation, and unchanged documents.
- **FR-014**: A live integration test MUST use only an explicitly owned isolated store and report an unavailable capability as unmeasured.

### Key Entities

- **Endpoint strategy**: The existing declaration of primary keys and secondary index fields.
- **Database scope**: The configured server URL, database name, and account name.
- **Collection confirmation**: The set of fields from index checks that completed in the current process.
- **Write outcome**: The existing record counts or explicit exception from the writer and router.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each tested strategy produces exactly one request per distinct field on its first write and zero on its second write.
- **SC-002**: An incomplete check produces zero document imports and retries its unconfirmed fields on the next write.
- **SC-003**: Concurrent writes and independent same-scope writers produce the same index request count as one first write.
- **SC-004**: Separate database scopes each produce their complete declared request count.
- **SC-005**: Before and after document comparisons show no changed key, record value, import option, or batch boundary.
- **SC-006**: Tests cover every new index coordination branch and every changed writer path.
- **SC-007**: An available isolated database proves equal-index reuse and an index-based query plan.

## Assumptions

- The normal configured ArangoDB path owns index creation.
- The declared indexes improve query access and impose no uniqueness constraint.
- No production store access, migration, index deletion, or data rewrite is authorized.
- Existing router diagnostics determine how an ArangoDB driver error becomes a failed export result.
- Process-local confirmation ends when the process ends. A later process relies on the database's equal-index response.
- A remote push and protected merge require a separate coordinator grant after the preceding repair.
