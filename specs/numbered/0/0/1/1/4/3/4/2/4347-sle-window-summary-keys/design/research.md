# Research: Stable SLE summary window keys

## Scope and Research Status

This design covers only `getSiteSleHistogram` and
`getSiteSleImpactSummary`, and only their required window identity and
SQLite/ArangoDB persistence behavior. The user-provided specification and the
repository's merged PR #4350 behavior resolve the relevant choices. No
clarification remains.

All verification is offline. No Mist credentials, live endpoint calls, or
production database operations are part of this design.

## Evidence

### OpenAPI response contract

Source: `documentation/mist-api-openapi31json.json`, OpenAPI 3.1.0,
version 2609.1.0, operation paths:

- `GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/histogram`
  (`getSiteSleHistogram`)
- `GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impact-summary`
  (`getSiteSleImpactSummary`)

The histogram response schema `sle_histogram` requires `metric`, `start`,
`end`, `data`, `x_label`, and `y_label`. It describes `start` and `end` as the
first and last timestamps in the histogram window and types them as numbers.
`data`, `x_label`, and `y_label` are summary content, not identity fields.

The impact response schema `sle_impact_summary` requires `start`, `end`,
`metric`, `classifier`, `failure`, `ap`, `wlan`, `device_os`, `device_type`,
and `band`. `classifier` and `failure` are strings and have no minimum-length
constraint, so an empty string is valid. The five grouping arrays are content,
not identity dimensions.

The path requires `site_id`, `scope`, `scope_id`, and `metric`. The existing
endpoint-family exporter supplies these required identifiers and does not send
the optional time/filter query parameters. The request's selected identifiers
therefore remain the authoritative source for those four identity values.

### Time-range evidence

Source: the official Mist API time-range guidance cited in the feature
specification's “Source contract and time boundaries” assumptions. It states
that the returned `start` and `end` are the actual range boundaries and that
the default request covers the last 24 hours. The specification records this
source but does not contain a canonical deep-link.

Design consequence: identity uses the response boundaries, not a reconstructed
last-24-hour range, the requested relative range, or export time. Two default
requests with different returned boundaries are distinct windows.

### Existing implementation pattern

- `src/operations/exporting/export/endpoint_family_exporter.py` resolves the
  existing Mist SDK method, sends the required operation arguments, normalizes
  the result, and prepares SLE identities before persistence.
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py`
  declares endpoint-specific keys and contains `SleWindowIdentity`, which
  validates windows and hashes ordered identity values.
- `src/foundation/support/refactors/sqlite_database_writer.py` prepares new
  keyed SLE rows, adds an identity marker/index through the existing writer
  path, and uses keyed replacement instead of the legacy auto-increment clear
  behavior.
- `src/foundation/persistence/db/writers/arango_writer.py` derives deterministic
  keys for the existing composite SLE identities and imports with replacement.
- `src/foundation/persistence/db/router.py` routes
  `auto_increment_with_unique` strategies to ArangoDB only, while
  `composite_pk` fans out to RedisJSON and ArangoDB.
- Merged PR #4350 establishes the non-destructive precedent: legacy SQLite
  rows and Arango UUID documents remain, the first keyed row is added beside
  them, and subsequent matching exports replace that keyed row only.

## Decisions

### 1. Exact identity fields

**Decision**: Declare only these ordered identity tuples:

- Histogram: `site_id`, `scope`, `scope_id`, `metric`, `start`, `end`.
- Impact summary: `site_id`, `scope`, `scope_id`, `metric`, `classifier`,
  `failure`, `start`, `end`.

**Rationale**: These tuples are the complete identity required by the
specification. Measurements, labels, grouping arrays, export timestamps,
generated values, and undocumented response fields can change without changing
the source window.

**Alternatives considered**: Adding `data`, `x_label`, `y_label`, grouping
arrays, or export time to the identity was rejected because those describe
content or execution, not the measurement window. Adding other response
dimensions was rejected because it would invent identity fields.

### 2. Source of identity values

**Decision**: Use request path arguments for `site_id`, `scope`, `scope_id`,
and `metric`; use response `start` and `end` for both endpoints; use response
`classifier` and `failure` for impact summaries.

**Rationale**: The exporter sends only the required path identifiers.
Response-provided `start` and `end` are the actual boundaries. The impact
classifier and failure values are required response identity fields, not
request parameters in this exporter flow.

**Alternatives considered**: Trusting conflicting response path dimensions,
using requested/default time values, mapping nonexistent classifier/failure
request arguments, or synthesizing missing fields was rejected.

### 3. Validation and canonical window identity

**Decision**: Validate that every required value is present and correctly
typed before persistence. Accept empty strings only for `classifier` and
`failure`; retain their exact values. Validate finite, nonnegative,
non-reversed numeric boundaries and canonicalize equivalent supported numeric
representations as the current SLE identity path does.

**Rationale**: Complete preflight prevents a partially written response and
avoids collisions from ambiguous separators or numeric formatting. Reusing the
existing deterministic key encoding preserves the established trend behavior.

**Alternatives considered**: Truthiness validation for classifier/failure,
silently coercing invalid types, substituting defaults, or using ad hoc
delimiter concatenation were rejected.

### 4. Backend coexistence and repeated exports

**Decision**: Reuse the merged PR #4350 keyed-row/document pattern. New
SQLite rows receive a deterministic identity marker derived only from the
declared key fields; ArangoDB derives a deterministic document key from that
same identity. Use the existing replacement behavior for later exports.
Retain all existing SQLite rows and Arango UUID documents unchanged. Keep both
new endpoint strategies at their existing `auto_increment_with_unique`
routing type, and recognize their exact identity tuples in the SLE-specific
SQLite and Arango key paths.

**Rationale**: This directly meets the required no-data-loss policy while
providing idempotent replacement for new records. Existing rows/documents do
not share the newly derived keyed identity and therefore are not rewritten.
Keeping the existing routing type avoids introducing a RedisJSON write:
`composite_pk` is routed to RedisJSON plus ArangoDB, while the specification
requires the two existing backends, SQLite and ArangoDB.

**Alternatives considered**: Backfill or migration, deletion, deduplication,
re-keying legacy rows, replacing all table/document contents, or keeping random
UUIDs for new records were rejected. Switching to `composite_pk` was rejected
because it would broaden backend behavior by adding RedisJSON. No migration
interface is added.

### 5. Scope and verification

**Decision**: Keep the existing Mist SDK methods and exporter call arguments.
Add offline tests under `tests/unit/db/sle_window_summary/` using fake API
responses, temporary SQLite, and an Arango fake. Do not add public contracts.
Assert that the existing strategy routing does not introduce RedisJSON writes.

**Rationale**: The feature changes stored identity, not the API or transport.
The planned test directory is distinct from the test paths under
`tests/unit/config/...` owned by open PR #4358 and fits the five-item rule:
adding it makes `tests/unit/db/` five direct children, with two files inside
the new directory.

**Alternatives considered**: Live Mist probes, production database checks,
optional query parameters, public API changes, or a new migration contract
were rejected.

## Remaining Research

None. The official time-range guidance is referenced by the specification,
whose evidence note does not supply a canonical URL. Implementation must retain
the documented actual-boundary rule and must not compensate with live service
verification.
