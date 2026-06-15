# Research: Org Marvis Client APIs Menu Set (mistapi 0.63.0)

## Decision 1: Operation set and menu grouping

- **Decision**: Implement a coherent org-level Marvis Client block with five operations: insights export, events count, events search, stats count, stats search.
- **Rationale**: This directly satisfies FR-001 and gives operators full triage flow (summarize first, drill-down second).
- **Alternatives considered**:
  - Implement only search endpoints first: rejected because operators lose fast volume-sizing workflow.
  - Split across unrelated menu ranges: rejected due to poor discoverability.

## Decision 2: Endpoint mapping strategy

- **Decision**: Bind operations to mistapi 0.63.0 Org Marvis Client endpoints as follows:
  - insights export -> org marvis client insights endpoint
  - events count -> org marvis client events count endpoint
  - events search -> org marvis client events search endpoint
  - stats count -> org marvis client stats count endpoint
  - stats search -> org marvis client stats search endpoint
- **Rationale**: Scope explicitly requested by spec and compatibility requirement FR-019.
- **Alternatives considered**:
  - Raw HTTP wrappers: rejected because SDK-first policy is required.
  - Deferred count endpoints: rejected because P2/P3 triage workflows depend on counts.

## Decision 3: Prompt contract for optional filters and duration

- **Decision**: Reuse existing `safe_input()` prompts with optional skip behavior for all filters; validate duration format before dispatch.
- **Rationale**: Aligns with Safety-First principle and FR-003/FR-004.
- **Alternatives considered**:
  - Free-form unvalidated pass-through: rejected due to user error risk and opaque failures.
  - Mandatory all-fields prompting: rejected due to operator friction and lower usability.

## Decision 4: Search-after and pagination behavior

- **Decision**: Search operations will explicitly support search-after token input/output and multi-page traversal with operator visibility of page progress.
- **Rationale**: Required by FR-005/FR-006 and SC-003 (no dropped/duplicate rows).
- **Alternatives considered**:
  - Single-page fetch only: rejected, incompatible with large result sets.
  - Hidden auto-pagination with no operator context: rejected, reduces auditability.

## Decision 5: Primary key strategy and idempotency

- **Decision**: Register explicit `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for each of the five operations:
  - insights dataset -> natural or composite key preserving uniqueness
  - count datasets -> deterministic keys for repeat-run update behavior
  - search datasets -> composite keys including record identity/timestamp for dedupe across pages/retries
- **Rationale**: Required by FR-009 through FR-012 and constitution PK governance.
- **Alternatives considered**:
  - default/fallback key strategy: rejected because it can cause row growth or duplicate storage.

## Decision 6: Export behavior

- **Decision**: All datasets route through existing exporter path for CSV/SQLite compatibility and consistent metadata handling.
- **Rationale**: Required by FR-008 and SC-002.
- **Alternatives considered**:
  - terminal-only output: rejected, no persistence/reporting parity.
  - custom per-operation writers: rejected due to duplication and higher maintenance risk.

## Decision 7: Failure handling and operator messaging

- **Decision**: Standardize actionable messages for invalid duration, malformed/expired search-after token, empty result sets, API errors, and output write failures.
- **Rationale**: FR-014 and SC-004 require first-response corrective guidance.
- **Alternatives considered**:
  - generic exception text: rejected as non-actionable for junior NOC operators.

## Decision 8: Test design

- **Decision**: Add regression tests for:
  - happy-path for all five operations
  - filter/duration validation failures
  - pagination continuation + search-after no-dup/no-drop invariants
  - CSV + SQLite compatibility
  - output failure handling
- **Rationale**: FR-015 through FR-017 and SC-003/SC-002.
- **Alternatives considered**:
  - manual validation only: rejected due to hidden-test and regression risk.

## Open risk log and mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| Endpoint naming mismatch in SDK vs docs | runtime call failure | Confirm callable names during implementation; encapsulate mapping in one handler block per operation. |
| Time-window drift between count and search runs | apparent count/search mismatch | Always print effective execution window and selected filters in summary output. |
| Partial page then transient API failure | duplicate rows on retry | Use idempotent PK strategy + append-safe pagination state handling. |
| SQLite or CSV target unavailable | failed persistence | Return actionable write error and preserve retrieval summary for audit. |
