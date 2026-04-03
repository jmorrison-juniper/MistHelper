# Research: Export SLE metrics insights (Menu #53)

Goal: Resolve ambiguities in the spec so implementation is deterministic.

Decisions made (resolved NEEDS CLARIFICATION):

1) Language and environment
- Decision: Python 3.13 (project constitution mandates >=3.13).
- Rationale: Consistency with repository constitution and available dependencies.
- Alternatives considered: Older Python versions (rejected).

2) Primary key strategy for listSiteSlesMetrics
- Decision: Use composite primary key: [site_id, metric, duration, timestamp].
- Rationale: Metrics lack stable UUIDs; the tuple uniquely identifies a metric datapoint for deduplication.
- Alternatives: Use a single timestamp field (rejected because multiple metrics/aggregation windows may collide) or generate synthetic UUIDs (rejected; natural keys preferred per constitution).

3) Flattening strategy for nested objects/arrays
- Decision: Flatten nested dicts into dotted column names (existing behavior). Arrays will be JSON-encoded into a single cell (string) to preserve order and structure.
- Rationale: JSON encoding preserves fidelity and is stable across rows. Expanding arrays into positional columns creates schema instability.
- Alternatives: Join with separator (rejected for loss of fidelity), expand into columns (rejected for schema instability).

4) SQLite upsert semantics
- Decision: Use INSERT ... ON CONFLICT(primary_key) DO UPDATE to perform idempotent upserts.
- Rationale: Native SQLite upsert is efficient and ensures deduplication.
- Alternatives: DELETE+INSERT (higher write amplification), MERGE-like logic in Python (more complex).

5) Pagination handling
- Decision: Treat listSiteSlesMetrics as paginated; implement streaming fetch using limit/page (or next_token) until no more pages.
- Rationale: Ensures complete exports for large datasets.
- Alternatives: Single large request with increased limit (may fail or be rate-limited).

6) Libraries and compatibility
- Decision: Use stdlib sqlite3, csv, json; rely on mistapi client for API calls. Use pytest for tests.
- Rationale: Stability and minimal new dependencies.

7) Performance and memory
- Decision: Stream rows to CSV and batch upserts in transactions (batch_size default 1000). Use WAL mode in SQLite for better concurrency.
- Rationale: Minimizes memory usage and improves write throughput.

Research conclusion: Implement composite PK strategy, JSON-encode arrays, stream/paginate, and use sqlite upserts. All remaining questions for product are recorded in plan.md under clarifications.


