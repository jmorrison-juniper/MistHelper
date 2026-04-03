# Feature Specification: Export SLE metrics insights (Audit)

**Feature Branch**: `102-audit-menu-53-export-sle-metrics-insights`
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Create a feature specification for MistHelper Menu #53: \"Export SLE metrics insights\"\n\nFunction: SiteExportUtils.insights\nCategory: data_export\nSQL export relevant: Yes\n\nThis is an AUDIT spec — analyze the existing implementation in MistHelper.py, document current state, identify issues, and define acceptance criteria for fixes.\n\nCRITICAL: You MUST write the spec file to disk at this exact path:\n  specs/102-audit-menu-53-export-sle-metrics-insights/spec.md\n\nFocus on: API call flow, data flattening, dual output (CSV/SQLite), primary key strategy, test coverage gaps, any issues found."

## User Scenarios & Testing (mandatory)

### User Story 1 - Export site SLE metrics (Priority: P1)

An auditor or operator wants to export Service Level Experience (SLE) metrics insights for a single site so they can analyze historical and aggregated SLE metrics offline or import into analytics tools.

**Why this priority**: This is the core use-case for menu #53 and is necessary for compliance/audit workflows and troubleshooting.

**Independent Test**: Run menu 53 for a known site that has SLE metrics; verify a CSV and/or SQLite output file is produced in data/; verify rows correspond to the API response and nested fields are flattened into columns.

**Acceptance Scenarios**:

1. Given an authenticated session and a selected site with SLE metrics, When the user runs Menu #53 (SiteExportUtils.insights), Then the tool calls the Mist API endpoint to fetch SLE metrics for that site and writes output to CSV and (when configured) to the hybrid SQLite database.
2. Given API returns nested structures (objects or arrays) in insight records, When saving output, Then the CSV file contains flattened columns and multiline/JSON content is escaped so rows remain valid CSV records.
3. Given multiple runs for the same site+metric+time window, When writing to SQLite, Then duplicate rows are not introduced (primary key strategy enforces uniqueness) and re-running produces idempotent results or overwrites where appropriate.

---

### Edge Cases

- API returns empty or missing data for a requested metric (should be handled gracefully and produce an empty CSV with header or a log message).
- API returns nested arrays (e.g., list of dimensions) — verify how arrays are serialized/flattened.
- Very large number of metric entries (pagination/limits) — ensure the export handles streaming/pagination or logs truncation.

## Extracted current-state summary (audit)

Source: MistHelper.py (SiteExportUtils.insights reference)

- Menu mapping shows: `"53": (SiteExportUtils.insights, "Export SLE (Service Level Experience) metrics insights for a selected site")`.
- The insights implementation invokes the Mist API function: `mistapi.api.v1.sites.sle.listSiteSlesMetrics` (evidence: call site in file) and appears to pass data_type `sle_metrics_insights` to the central export helper.
- Common processing pipeline in MistHelper for similar export flows uses:
  - DataProcessingUtils.flatten_nested_fields(...) to flatten nested JSON before writing
  - DataProcessingUtils.escape_multiline(...) to escape newline/multiline content
  - DataExporter.save_data_to_output(...) to write CSV and (optionally) SQLite
- Global configuration contains a centralized ENDPOINT_PRIMARY_KEY_STRATEGIES mapping for many endpoints. I did not find an explicit entry for `listSiteSlesMetrics` in the mapping; therefore the default fallback strategy (`default`) is likely applied.

Implication: Without an explicit endpoint strategy, the export pipeline may use the fallback primary-key approach (auto-increment with optional unique constraint on API 'id' if present). For metrics/aggregation endpoints that have no stable UUID 'id', this can cause duplicate rows in SQLite or weak uniqueness semantics.

## Key concepts identified

Actors: Auditor/operator (user), Mist API, MistHelper export pipeline

Actions: Select site -> call SLE metrics API -> flatten response -> write CSV -> optionally write to SQLite database

Data involved: SLE/metrics records per site, usually include fields such as site_id, metric name, duration/window, timestamps, aggregated values, and nested details/attributes.

Constraints: Must support nested JSON flattening, preserve CSV validity (escape newlines), and enforce deterministic primary key strategy for SQLite to avoid duplicates. Exports must be robust to empty responses and API pagination.

## Issues observed (high-level)

1. Primary key strategy missing for SLE endpoint
   - The central ENDPOINT_PRIMARY_KEY_STRATEGIES appears comprehensive but does not include `listSiteSlesMetrics` or the `sle` namespace endpoints. As a result, the default fallback strategy (`auto_increment_with_unique`) will be used.
   - Consequence: For time-series/aggregated metrics without stable 'id' fields, the fallback approach can lead to duplicate rows or non-deterministic primary keys in SQLite exports.

2. Data flattening risks with arrays and nested dicts
   - Code uses DataProcessingUtils.flatten_nested_fields(...) shared across many exporters. That helper is appropriate for shallow nested objects, but historically such flatteners vary in how they handle arrays (e.g., join with `;`, index suffixes, JSON-encode).
   - Consequence: If arrays are JSON-encoded into a single cell, downstream analytics may misinterpret fields. If arrays are expanded into multiple columns with positional suffixes, schema can be unstable across exports.

3. Dual output behavior (CSV vs SQLite) not endpoint-specific
   - The DataExporter.save_data_to_output(...) is used to save both CSV and SQLite; however, because the endpoint is not registered in primary key strategies, the SQLite schema selection may be generic and not well-suited for metric data.
   - Consequence: Potential schema mismatch, missing indexes, and poor deduplication when importing/reconciling metric records.

4. Test coverage gaps
   - I found widespread calls to export helpers but few (or no) unit tests exercising: the insights export code path, flattening behavior for nested metrics payloads, and SQLite write/deduplication for metrics endpoints.
   - Consequence: Bugs in real-world nested payloads or primary key handling will go undetected until manual use.

5. Error handling and pagination
   - The audit observed calls to listSiteSlesMetrics but it's unclear whether the implementation handles pagination or limit/next semantics from the Mist API (list endpoints often return paged data). If unhandled, exports may miss data silently.

## Functional Requirements (testable)

- FR-001: The insights exporter MUST call mistapi.api.v1.sites.sle.listSiteSlesMetrics with the correct site_id and parameters (duration, limit) and log the API request and response status.
- FR-002: The exporter MUST flatten nested JSON objects into stable, deterministic CSV columns using a documented flattening strategy (see Assumptions) so that the same logical field always appears in the same column name.
- FR-003: The exporter MUST serialize nested arrays deterministically (e.g., JSON-encode arrays or join with a documented separator) and document the chosen approach in the spec.
- FR-004: The exporter MUST escape multiline strings so the resulting CSV has exactly one header row and each record is a single CSV row.
- FR-005: When SQLite output is enabled, the exporter MUST use a deterministic primary key strategy for SLE metrics that prevents duplicate rows on repeated exports for the same metric/time combination.
- FR-006: The exporter MUST create appropriate indexes for common query patterns (e.g., site_id, metric, timestamp) in SQLite to support fast queries.
- FR-007: The exporter MUST handle paginated API responses and export the complete result set; if the API supports pagination/limit, all pages must be fetched unless a user-specified limit is applied with a clear log message.
- FR-008: Errors from API calls or write operations MUST be logged and surfaced to the user; in case of partial failure, the exporter MUST either roll back the SQLite transaction or mark the output as partial and provide details.
- FR-009: Unit tests MUST exist to validate: (a) flattening behavior for nested dicts and arrays; (b) CSV validity (header + consistent columns); (c) SQLite write semantics and deduplication with the chosen primary key strategy.
- FR-010: The exporter MUST run in test mode (reduced lookback) and produce predictable results; tests should exercise both CSV-only and SQLite output paths.

## Success Criteria (mandatory)

- SC-001: Running Menu #53 for a sample site with SLE metrics produces a CSV file with header and at least one data row (or an empty CSV with header if no data) within 60 seconds in normal conditions and <10s in test mode (when using small lookback).
- SC-002: Flattened CSV contains no nested objects serialized as plain Python dict text; arrays must be consistently serialized (JSON array string or documented separator) in 100% of exported rows.
- SC-003: When SQLite output is enabled, re-running the export for the same site+metric+duration must NOT create duplicate rows. Idempotency test: run export twice; row count for canonical key(s) must be unchanged.
- SC-004: A targeted unit/integration test suite exists and passes for the insights exporter verifying API call stub handling, flattening, CSV write, SQLite write, and deduplication (see Test Coverage below).
- SC-005: Endpoint-level primary key strategy is added to ENDPOINT_PRIMARY_KEY_STRATEGIES for `listSiteSlesMetrics` and verified by tests.

## Key Entities

- SLEMetricInsight
  - site_id (string)
  - site_name (string)
  - metric (string) — e.g., availability, latency, throughput
  - duration (string) — e.g., "7d", "24h"
  - timestamp or window_start/window_end (ISO8601) — depends on API payload
  - value(s) (numeric or dict of quantiles)
  - details (nested object) — flattened into columns
  - raw_payload (optional) — full JSON string for auditability if kept

## Assumptions

1. Default flattening behavior: DataProcessingUtils.flatten_nested_fields currently converts nested dict keys into dotted column names (e.g., details.region -> details.region). If arrays are present, they will be JSON-encoded into a single cell. If this assumption is inaccurate, update the code or spec accordingly.
2. SQLite EXPORT is controlled by global OUTPUT_FORMAT or a CLI flag; DataExporter.save_data_to_output handles whether to write to CSV, SQLite, or both.
3. listSiteSlesMetrics returns per-site metric rows with at least the following fields: metric name, duration, timestamp/window and aggregated values. If the API returns a stable unique 'id' per metric row, prefer using it; otherwise use a composite primary key.

## Test Coverage & Gaps

Observed gaps:

- No dedicated unit tests found that exercise SiteExportUtils.insights end-to-end with stubbed API responses including nested arrays/dicts.
- No tests validating the SQLite schema generation for metrics endpoints and the deduplication behavior when endpoint is not present in ENDPOINT_PRIMARY_KEY_STRATEGIES.
- No explicit tests asserting flattening strategy (column names and serialization for arrays) nor CSV validity for nested payloads.

Required tests to add:

- TC-001: Unit test for DataProcessingUtils.flatten_nested_fields using sample SLE payloads that include nested dicts and arrays; assert deterministic column names and cell representations.
- TC-002: Integration-style test for SiteExportUtils.insights that stubs mistapi.api.v1.sites.sle.listSiteSlesMetrics to return paginated responses; assert full dataset exported and CSV/SQLite output present.
- TC-003: Idempotency test that runs insights exporter twice against same dataset and asserts SQLite row counts for canonical keys do not increase.
- TC-004: Error handling test: simulate API errors/timeouts and verify exporter logs error and does not leave a partially corrupted SQLite state (transaction rollback or a "partial" marker).

## Recommended fixes / Implementation notes

1. Add explicit endpoint strategy for SLE metrics in ENDPOINT_PRIMARY_KEY_STRATEGIES. Suggested entry:

   "listSiteSlesMetrics": {
     "type": "composite_pk",
     "primary_key": ["site_id", "metric", "duration", "timestamp"],
     "indexes": ["site_id", "metric", "duration", "timestamp"],
     "unique_constraints": [],
     "description": "Site SLE metrics with composite key to ensure deduplication by site/metric/duration/timestamp",
   },

   Rationale: metrics typically lack a stable UUID and are uniquely identified by the site+metric+time window.

2. Clarify and stabilize flattening strategy:
   - Decide on array handling: either JSON-encode arrays (recommended for fidelity) or join with a stable separator and document it.
   - Ensure flattening produces deterministic column names and does not vary per row (use union of keys across rows or pre-defined schema for known metric fields).

3. Enhance DataExporter.save_data_to_output to:
   - Use endpoint_name/api_function_name to pick primary key strategy from ENDPOINT_PRIMARY_KEY_STRATEGIES; if missing, raise a warning and default to a safe composite key rather than auto-increment.
   - When writing to SQLite, create tables with explicit primary keys and indexes before inserting and use upsert semantics (INSERT OR REPLACE or equivalent) to ensure idempotency.
   - Wrap SQLite writes in transactions and roll back on failure.

4. Pagination and API robustness:
   - Ensure the insights implementation iterates over paginated responses (if applicable) and collects all results before saving.
   - Log page counts and total rows exported.

5. Tests and CI:
   - Add unit tests above (TC-001..TC-004).
   - Add a small fixture JSON sample of typical listSiteSlesMetrics payloads (including nested arrays) for test assertions.

## Acceptance Criteria (for this audit to be considered resolved)

- AC-001: A new ENDPOINT_PRIMARY_KEY_STRATEGIES entry for `listSiteSlesMetrics` is added to MistHelper.py with a composite primary key strategy as suggested or approved.
- AC-002: DataProcessingUtils.flatten_nested_fields behavior for dicts and arrays is documented in code comments and covered by unit tests (TC-001).
- AC-003: DataExporter.save_data_to_output uses endpoint-aware primary key selection and writes SQLite rows idempotently (TC-003 passes).
- AC-004: The insights exporter correctly handles paginated API responses and exports the complete dataset to CSV (TC-002 passes).
- AC-005: Error handling for API failures and partial writes is implemented such that SQLite is not left in a corrupted or partially committed state (TC-004 passes).

## Implementation tasks (high level)

- T1: Add endpoint strategy entry for listSiteSlesMetrics (code change + unit test)
- T2: Add/adjust flattening behavior and tests (TC-001)
- T3: Update DataExporter.save_data_to_output to perform endpoint-aware SQLite schema creation and upserts (TC-003)
- T4: Add pagination handling and integration test for insights exporter (TC-002)
- T5: Add error handling tests and rollback logic (TC-004)

## SPEC STATUS

SUCCESS (spec ready for planning)


---

Appendix: Files referenced in audit

- MistHelper.py: Function reference - SiteExportUtils.insights (menu 53)
- Suggested new endpoint entry: `listSiteSlesMetrics` in ENDPOINT_PRIMARY_KEY_STRATEGIES

[NEEDS CLARIFICATION: Primary key choice]

- Context: The choice of primary key for SLE metrics affects deduplication and schema design. The suggested composite key is site_id + metric + duration + timestamp.
- Question: Do you want the composite primary key suggested above (site_id, metric, duration, timestamp) or prefer using a single canonical timestamp field or an API-provided id if present?



