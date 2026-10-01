# Feature Specification: Bounded database discovery

**Feature Branch**: `jmorrison-juniper-bounded-database-discovery`

**Created**: 2026-10-01

**Status**: Ready for implementation

**Input**: Repair [issue #3318](https://github.com/jmorrison-juniper/MistHelper/issues/3318) in the isolated app worktree.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Limit the discovery wait (Priority: P1)

An operator opens the portal on a host that cannot resolve the configured database names.
Each name lookup returns within about one second.
Repeated configuration reads reuse the recent failed result.

**Why this priority**: An operating system lookup currently holds each configuration read for more than 20 seconds.

**Independent Test**: Block a controlled resolver and measure the real caller wait without a network connection.

**Acceptance Scenarios**:

1. **Given** a blocked resolver, **When** the application checks one name, **Then** the caller returns within 1.3 seconds.
2. **Given** two failed names, **When** the application reads its configuration twice, **Then** it performs one lookup per name.
3. **Given** explicit standalone mode, **When** the application reads its configuration, **Then** it performs no name lookup.

### User Story 2 - Detect a later database (Priority: P2)

An operator starts a database after an earlier lookup failed.
The application checks the name again after the 30-second cache period.
The application also refreshes successful results after that period.

**Why this priority**: A permanent failed result would prevent database recovery.

**Independent Test**: Advance a controlled monotonic clock and change the controlled resolver result.

**Acceptance Scenarios**:

1. **Given** a recent failed result, **When** the cache period expires, **Then** a new successful result becomes visible.
2. **Given** a recent successful result, **When** the cache period expires, **Then** the application checks the name again.
3. **Given** a changed configured name, **When** the application reads its configuration, **Then** it checks the new name immediately.
4. **Given** one resolved backend, **When** configuration requires credentials, **Then** the existing credential validation remains active.

### User Story 3 - Keep work and readiness distinct (Priority: P3)

Concurrent portal reads share one lookup for the same name.
A blocked operating system resolver cannot create unlimited worker threads or pending work.
A resolved name alone does not establish database readiness.

**Why this priority**: A caller deadline must not replace one delay with unlimited background work or a false readiness result.

**Independent Test**: Block controlled lookups, submit concurrent requests, and inspect worker and cache counts.

**Acceptance Scenarios**:

1. **Given** concurrent requests for one name, **When** resolution starts, **Then** one worker performs that lookup.
2. **Given** two blocked workers, **When** additional names arrive, **Then** no additional workers or queued jobs appear.
3. **Given** released controlled workers, **When** their lookups finish, **Then** new names can resolve.
4. **Given** resolved addresses without a listening service, **When** the TCP probe runs, **Then** it reports unavailable.
5. **Given** a cached address, **When** the TCP probe runs, **Then** it uses that address without another name lookup.

### Edge Cases

- Cache keys distinguish the name, address family, and socket type of the actual query.
- DNS failure, caller timeout, unavailable worker capacity, and resolver errors have explicit diagnostics.
- Late worker completion does not extend an existing negative cache period.
- A wall-clock change does not change cache expiry or the caller deadline.
- Cache storage holds no more than 128 entries.
- Worker shutdown has a deadline and never waits indefinitely for the operating system resolver.
- A finite handoff queue admits no additional job when both worker slots are occupied.
- Configured external names remain usable outside a container.
- IPv4 and IPv6 TCP probes retain the resolved address family.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Bound each central database name lookup to a one-second caller budget.
- **FR-002**: Cache successful and failed results for 30 seconds with a monotonic clock.
- **FR-003**: Share one active lookup for each complete query identity.
- **FR-004**: Limit active resolver workers and outstanding queries to two, with no extra work behind blocked workers.
- **FR-005**: Limit cached query results to 128 entries.
- **FR-006**: Release worker capacity when the controlled or operating system lookup finishes.
- **FR-007**: Keep blocked workers from preventing process shutdown.
- **FR-008**: Reuse resolved numeric addresses for central TCP probes.
- **FR-009**: Keep the TCP availability check separate from DNS success.
- **FR-010**: Preserve explicit standalone mode, partial-backend behavior, required credentials, and file output.
- **FR-011**: Preserve configured names instead of substituting local addresses or using container location as a decision.
- **FR-012**: Document the actual DNS budget, cache period, worker limit, and driver boundary.
- **FR-013**: Prove the existing defect and the repair with controlled tests that require no network.
- **FR-014**: Emit safe diagnostics for DNS failure, timeout, capacity, and worker capability errors.
- **FR-015**: Share DNS results with the released Redis and capture-store preflights without changing driver hostnames or URLs.
- **FR-016**: Migrate the inherited ArangoDB preflight only after the coordinator releases its verified main revision.

### Key Entities

- **Lookup identity**: The configured name, address family, and socket type.
- **Cached result**: Resolved addresses or a failed result with an expiry time.
- **Active lookup**: One finite worker and the result shared by its waiting callers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A blocked single-name lookup returns within 1.3 real seconds with the default one-second budget.
- **SC-002**: Two blocked names complete one configuration read within 2.6 real seconds.
- **SC-003**: A repeated configuration read performs zero additional lookups during the cache period.
- **SC-004**: A controlled failed result changes to a successful result after exactly 30 monotonic seconds.
- **SC-005**: Concurrent requests perform one controlled lookup for the same identity.
- **SC-006**: Resource tests observe at most two workers and outstanding queries, no extra queued work, and 128 cache entries.
- **SC-007**: All controlled helper jobs finish after their release, and worker capacity recovers.
- **SC-008**: TCP tests perform no additional name lookup and reject a resolved but unavailable service.

## Assumptions

- Operating system name resolution has no interruptible deadline in the Python socket interface.
- The caller can stop waiting while a finite daemon worker finishes the operating system lookup.
- A permanently blocked operating system lookup holds its worker slot until that lookup finishes.
- Driver network handshakes remain separate from the bounded DNS preflight.
- The coordinator releases Redis and capture-store preflight files after fresh exact ownership checks.
- The ArangoDB writer belongs to issue #3309 and remains read-only until the verified position-25 release.
- Its inherited DNS preflight migration remains an incomplete implementation prerequisite before publication.
- No production DNS, Mist API, service, store, container, or firmware operation is authorized.
- The coordinator must grant a verified main SHA before any push or pull request.
