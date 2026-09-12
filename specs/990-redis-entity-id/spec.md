# Feature Specification: Redis Time-Series Entity Identifier Fallback

**Feature Branch**: `feat/990-redis-entity-id`

**Created**: 2026-07-29

**Status**: Draft

**Input**: GitHub issue #990, part 2 only. Part 1 already landed. See the Non-Goals section.

---

## Problem

`RedisTimeSeriesWriter` builds a time-series key with the shape
`{api_function_name}:{entity_id}:{field_name}`. The writer reads the entity
identifier from one field only. The primary key strategy names that field in
`entity_key_field`.

A composite primary key strategy names fields that appear on some event types
and not on others. When a record does not carry the named field, the writer
buckets that record under the text `unknown`. Many unrelated records therefore
collapse into one time-series key. A downstream query cannot tell those records
apart, and the merged series reports a value that belongs to no single entity.

The same source file already solves the same problem for the webhook path. The
helper `_pick_webhook_entity` walks a candidate list and returns the first field
that the event carries. The batch path does not use that approach. The file
therefore holds two competing ideas for one concept.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A NOC engineer separates composite-key records (Priority: P1)

A NOC engineer exports device event data through an endpoint that uses a
composite primary key strategy. Some of the exported records do not carry the
field that the strategy names. The engineer then queries the time-series store
and expects one series for each device.

**Why this priority**: This story is the defect. Without it, the export loses the
identity of every record that misses the strategy field. The engineer reads a
merged series and draws a wrong conclusion about the network.

**Independent Test**: Write a record set in which the strategy field is absent
and a common identifier is present. Confirm that the writer creates one key for
each distinct identifier and creates no key that carries the text `unknown`.

**Acceptance Scenarios**:

1. **Given** a record that omits the strategy field and carries a common entity
   identifier, **When** the writer extracts the time-series keys, **Then** the
   writer uses the value of that common identifier as the entity identifier.
2. **Given** two records that omit the strategy field and carry two different
   common identifiers, **When** the writer extracts the time-series keys,
   **Then** the writer creates two distinct keys.
3. **Given** a record set in which every record carries a common identifier,
   **When** the writer extracts the time-series keys, **Then** the writer
   creates no key that carries the text `unknown`.

---

### User Story 2 - An existing export keeps its current keys (Priority: P2)

An operator runs an export that already works today. Every record carries the
field that the strategy names. The operator expects the same keys as before, so
that the existing history and the new points join the same series.

**Why this priority**: This story protects the common case. A change of the
entity identifier for an existing record would split one history into two
series and would corrupt every stored trend.

**Independent Test**: Write a record set in which every record carries the
strategy field. Compare the generated keys against the keys that the current
build produces. Confirm that the two sets match.

**Acceptance Scenarios**:

1. **Given** a record that carries the strategy field with a usable value,
   **When** the writer extracts the time-series keys, **Then** the writer uses
   the value of the strategy field and ignores every fallback field.
2. **Given** a record that carries both the strategy field and a common
   identifier, **When** the writer extracts the time-series keys, **Then** the
   strategy field wins.
3. **Given** the full existing unit test suite for the writer, **When** the
   suite runs against the changed code, **Then** every test passes without a
   change to its expected keys.

---

### User Story 3 - A record without any identifier still writes (Priority: P3)

A record carries neither the strategy field nor any common identifier. The
operator still expects the export to complete and to write the numeric fields.

**Why this priority**: This story keeps the sentinel behavior. The export must
not fail and must not drop the record. The sentinel also keeps the key shape
stable for the downstream reader.

**Independent Test**: Write a record that carries only numeric fields. Confirm
that the writer creates a key that carries the text `unknown` and that the write
completes.

**Acceptance Scenarios**:

1. **Given** a record with no strategy field and no common identifier, **When**
   the writer extracts the time-series keys, **Then** the writer uses the text
   `unknown` as the entity identifier.
2. **Given** an empty record, **When** the writer extracts the time-series keys,
   **Then** the writer uses the text `unknown` and raises no error.

---

### Edge Cases

- The record carries the strategy field, and the value is `None`. The writer
  treats the field as absent and continues to the fallback list.
- The record carries the strategy field, and the value is an empty text value.
  The writer treats the field as absent and continues to the fallback list.
- The record carries the strategy field, and the value is a text value that
  holds only blank space. The writer treats the field as absent and continues
  to the fallback list.
- The record carries the strategy field, and the value is the number `0`. The
  writer treats the value as usable and returns the text `0`.
- The record carries two different fallback fields. The order of the fallback
  list decides which field wins.
- The record carries a fallback field whose value is empty. The writer skips
  that field and tries the next field in the list.
- The strategy field name matches one of the fallback names. The writer returns
  the same value and does not read the field twice.

---

## Requirements *(mandatory)*

A field holds a **usable value** when all three conditions are true. The record
carries the field. The value is not `None`. The text form of the value is not
empty after the removal of the surrounding blank space. The specification uses
the term "usable value" for this rule in every requirement below.

### Functional Requirements

- **FR-001**: The writer MUST read the entity identifier from the field that the
  primary key strategy names, when that field holds a usable value.
- **FR-002**: When the strategy field does not hold a usable value, the writer
  MUST walk an ordered list of common entity identifier field names. The writer
  MUST take the first field that holds a usable value.
- **FR-003**: The writer MUST return the text `unknown` only when neither the
  strategy field nor any field in the fallback list holds a usable value.
- **FR-004**: The writer MUST keep the time-series key shape
  `{api_function_name}:{entity_id}:{field_name}`.
- **FR-005**: The writer MUST produce a byte-identical key for every record that
  carries a usable value in the strategy field. The current build and the
  changed build MUST agree on that key.
- **FR-006**: The fallback list MUST use the order `device_id`, `site_id`,
  `org_id`, `mac`, `id`. The source file already declares this order for the
  choice of the strategy field. The Assumptions section records the reason.
- **FR-007**: The writer MUST emit one debug summary for each extraction call.
  The summary MUST report three counts. The first count covers the records that
  used the strategy field. The second count covers the records that used a
  fallback field. The third count covers the records that used the `unknown`
  sentinel.
- **FR-008**: The writer MUST NOT emit a log line for each record. A per-record
  log line would flood the output for a large export.
- **FR-009**: The unit test suite MUST cover three branches. The first branch
  covers a present strategy field. The second branch covers an absent strategy
  field with a present fallback field. The third branch covers a record with no
  usable field.
- **FR-010**: The change MUST add an entry under the `## [Unreleased]` heading in
  `CHANGELOG.md`.
- **FR-011**: Every changed line MUST carry an inline comment that states the
  reason for the line.
- **FR-012**: Every comment and every prose line MUST follow the Simplified
  Technical English guide at `documentation/ASD-STE100_writing-guide.md`.
- **FR-013**: The resolution logic MUST live in one place. The file MUST NOT hold
  two different rules for the choice of an entity identifier in the batch path.

### Key Entities

- **Record**: One row of exported data from a Mist API endpoint. The record holds
  identifier fields and numeric fields.
- **Primary key strategy**: The table entry that names the primary key fields for
  an endpoint. The strategy supplies the name of the entity identifier field.
- **Entity identifier**: The text value that names the subject of a time series.
  The value sits in the middle part of the time-series key.
- **Time-series key**: The three-part key that the store uses for one metric of
  one entity.
- **Fallback list**: The ordered list of common entity identifier field names
  that the writer tries when the strategy field fails.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Build a test set of records that omit the strategy field and carry
  a common identifier. 100 percent of those records resolve to a distinct entity
  identifier. 0 percent land in the `unknown` bucket.
- **SC-002**: For a test set of records that carry the strategy field, 100
  percent of the generated keys match the keys that the current build produces.
- **SC-003**: The unit test suite covers all three resolution branches, and the
  full suite passes.
- **SC-004**: 100 percent of the generated keys hold three parts that a colon
  separates.
- **SC-005**: An operator who queries a mixed record set receives one series for
  each distinct entity. Before the change, the same query returns one merged
  series for every record that missed the strategy field.
- **SC-006**: Every quality gate passes with no new violation. The gates are the
  lint gate, the format gate, the type gate, the complexity gate, the security
  gate, and the coverage gate.
- **SC-007**: An extraction of 10000 records emits one summary log line for the
  resolution counts and emits no per-record log line.
- **SC-008**: The Simplified Technical English linter reports a score of 80 or
  above for every changed file.

---

## Non-Goals

The items below stay out of scope. A change to any of them makes this feature
larger than the defect that it fixes.

- **`compose.yml`**: Do not edit this file. Part 1 of issue #990 already landed
  on the main branch.
- **The `arangodb` service**: This service already exists in `compose.yml` at
  line 66. It declares the image, the port `8529`, the `arangodb-data` volume,
  the `ARANGO_ROOT_PASSWORD` variable, and the health check. Do not add it again.
- **The `redis-stack` service**: This service already exists in `compose.yml` at
  line 91. It declares the image, the ports `6379` and `8001`, the `redis-data`
  volume, the `REDIS_PASSWORD` variable, and the health check. Do not add it
  again.
- **The `arangodb-data` volume**: This volume already exists in `compose.yml` at
  line 153. Do not add it again.
- **The `redis-data` volume**: This volume already exists in `compose.yml` at
  line 155. Do not add it again.
- **The `unknown` sentinel**: Keep the sentinel as the final fallback. The
  companion key builder in the JSON writer depends on a stable key length. A
  removal of the sentinel would break the key format.
- **The JSON writer key builder**: Do not change `RedisJSONWriter._build_key`.
  That method serves a different key shape and a different reader.
- **The webhook path**: Do not change `_pick_webhook_entity`. That helper already
  behaves as this feature requires, and it serves a different record shape.
- **The primary key strategy table**: Do not add or change any strategy entry.
  The defect sits in the reader of the strategy, not in the strategy itself.
- **The key shape**: Do not change the three-part key shape. A change would
  orphan every stored series.
- **The ArangoDB writer**: Do not change any ArangoDB code path.

---

## Assumptions

- **The fallback order follows the existing preference order.** The source file
  already declares the order `device_id`, `site_id`, `org_id`, `mac`, `id` for
  the choice of the strategy field in the batch path. The new fallback serves the
  same batch path. A shared order keeps one rule in the file. The webhook path
  uses a different order, because a webhook event carries a different field set.
  This feature does not align the two orders.
- **The value `0` is a usable value.** The rule tests for absence, for `None`,
  and for an empty text value. The rule does not test for a false value. An
  entity identifier of `0` is rare and remains valid.
- **The strategy field keeps its priority.** The strategy names the correct field
  for the endpoint. The fallback list only serves the records that the strategy
  field does not cover.
- **The existing tests define the current behavior.** The file
  `tests/unit/test_redis_writer.py` already exercises the writer with the
  strategy fields `id` and `entity_id`. Those tests act as the guard for
  Success Criterion SC-002.
- **No migration runs.** Keys that the store already holds under the text
  `unknown` stay as they are. This feature fixes the future writes only. A
  cleanup of the stored history sits outside this scope.
- **The change carries no new dependency.** The fix uses the standard library
  only.

---

## Implementation Notes (AI hints)

The repository convention places implementation hints in a separate section. See
the Feature Spec definition in `.github/copilot-instructions.md`. The main body
above stays behavior-focused.

- **Target file**: `src/db/redis_writer.py`.
- **Target line**: The direct lookup at line 190 inside `_extract_chunk`. The
  line reads
  `entity_id = str(record.get(ctx.entity_key_field, "unknown"))`.
- **New method**: Add a static method `_resolve_entity_id(record, entity_key_field)`
  to `RedisTimeSeriesWriter`. Replace the line 190 lookup with a call to it.
- **Pattern to copy**: The helper `_pick_webhook_entity` near line 431 walks a
  candidate list and returns the first field that the event carries. Reuse its
  shape, its naming style, and its module-level candidate constant. The webhook
  candidate constant is `WEBHOOK_ENTITY_KEYS` near line 45.
- **Existing order source**: The helper `_pick_entity_field` near line 444
  declares the order `device_id`, `site_id`, `org_id`, `mac`, `id`.
- **Sentinel dependency**: The method `RedisJSONWriter._build_key` near line 592
  uses the same `unknown` sentinel for key length stability. Keep the sentinel.
- **Thread safety**: `_extract_chunk` runs inside a thread pool for a large
  input. Keep the new method pure and free of shared state. Plan the counter for
  Functional Requirement FR-007 so that it does not add a shared mutable
  variable across threads.
- **Test file**: `tests/unit/test_redis_writer.py`.
