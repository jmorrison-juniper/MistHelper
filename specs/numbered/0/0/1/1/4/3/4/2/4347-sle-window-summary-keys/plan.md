# Implementation Plan: Stable SLE summary window keys

**Branch**: `jmorrison-juniper-sle-window-summary-key-assessment` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/spec.md`.

## Summary

Repair the persistence identity for `getSiteSleHistogram` and
`getSiteSleImpactSummary` so repeated exports replace only the same actual
response window. Extend the existing SLE identity and writer behavior used by
merged PR #4350; preserve every legacy SQLite row and ArangoDB UUID document
without historical migration, deletion, or deduplication. Use only the selected
path identifiers and returned `start`/`end`; impact summaries additionally
require the returned `classifier` and `failure` strings, including empty
strings.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi` SDK methods and MistHelper
`DataExporter`; no new dependency or transport.

**Storage**: SQLite and ArangoDB persistence paths. CSV output representation
and unrelated backend behavior remain unchanged.

**Testing**: `pytest`, fake SDK/API responses, temporary SQLite files, and the
existing Arango writer fake. No live Mist calls or production database access.

**Target Platform**: Existing MistHelper local and container-supported runtime;
no platform change.

**Project Type**: Python application with an endpoint exporter and selectable
data-persistence backends.

**Performance Goals**: No new latency target. Identity validation and hashing
remain proportional to the response row count and follow the existing SLE
window path.

**Constraints**:

- Histogram identity is exactly `site_id`, `scope`, `scope_id`, `metric`,
  `start`, `end`.
- Impact-summary identity is exactly `site_id`, `scope`, `scope_id`, `metric`,
  `classifier`, `failure`, `start`, `end`.
- `classifier` and `failure` must exist as strings; `""` is valid.
- The four selected source dimensions come from request path identifiers;
  actual `start` and `end` come from each response.
- Validate the complete response batch before either backend writes.
- Keep legacy SQLite rows and Arango UUID documents unchanged. Do not migrate,
  delete, deduplicate, re-key, or rewrite legacy data.
- The exporter continues to send only the four required path identifiers.
  Do not add optional query parameters.
- Document matching-window replacement and legacy-record preservation in the
  contributor guide and in one scoped README paragraph.
- Keep menu titles, operation counts, and existing WAN content unchanged.
- Add one issue-specific release fragment that names both #4347 and #4348.
- Do not change existing trend identities or behavior, unrelated endpoint
  strategies, public APIs, database migration interfaces, or issue records.
- Do not rebase, push, or create a pull request before local validation and a
  report of the exact patch scope and remaining blockers.

**Scale/Scope**: Only the two SLE endpoints named above, their exact identities,
and their SQLite/ArangoDB persistence behavior.

## Constitution Check

### Pre-Design Gate

- **Five-item rule**: The selected feature is already below the managed
  `specs/numbered/` route. `specs/` has 795 existing direct children, which is
  pre-existing process-folder debt; this feature adds no direct child there.
  The feature root has four direct children: `spec.md`, `plan.md`, `tasks.md`,
  and `design/`. The `design/` directory has four direct children. This feature
  adds no structural child under either directory. `changelog.d/` has 272
  direct fragment files. This is existing process-folder debt; do not
  restructure the shared release-note directory in this feature.
  `tests/unit/db/sle_window_summary/` is the fifth direct child of
  `tests/unit/db/` and holds two test modules. No `contracts/` directory is
  needed. **Separate incremental remediation action**: track independent
  cleanup of the existing `specs/` and `changelog.d/` folder debt. Do not
  restructure either directory in this feature.
- **Natural keys**: The exact endpoint-specific key lists are declared in the
  existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` catalog. The opaque backend key is
  derived only from those declared values; it is not an additional identity
  dimension.
- **Mist transport**: Retain the existing `mistapi` SDK call path and its
  required path arguments. No direct HTTP transport, WebSocket, authentication
  change, or optional query parameter is proposed. Offline contract tests will
  pin method selection, path arguments, failure safety, and credential
  redaction.
- **Output and data safety**: Keep the shared `DataExporter` boundary and
  preserve measurement, label, and grouping content. All acceptance tests use
  local fixtures and isolated stores.
- **Deployment pipeline**: This feature changes local code, tests, and
  documentation. Run the focused local gates before reporting. Do not rebase,
  push, or create a pull request before that report.
- **Existing-code quality constraints**: Later implementation must keep
  touched functions within the constitution's parameter, block, operation, and
  line limits; comply with its inline-comment and action-logging requirements;
  and avoid unrelated refactors.

**Gate result**: Pass. The specification provides exact identity fields,
validation behavior, legacy-data policy, endpoint scope, and offline
verification constraints. No clarification is required before design.

## Design Decisions

1. Rename the trend-only helper to `SleWindowIdentity`, then extend it to
   recognize the two summary endpoints. Keep all four endpoint field tuples
   exact and preserve the existing trend identities and outputs.
2. Keep the selected request's `site_id`, `scope`, `scope_id`, and `metric`
   authoritative when response values disagree. Use each response's actual
   `start` and `end`; do not derive them from request parameters or export time.
3. Use response `classifier` and `failure` as impact-summary identity values.
   Validate presence and string type separately from truthiness so both empty
   strings remain valid and unchanged.
4. Validate every identity before persistence. Reject missing, invalid,
   non-finite, or reversed window boundaries before any row is written. Keep
   the existing no-data short circuit.
5. Reuse the keyed-row pattern established by PR #4350: key new SQLite rows by
   a deterministic identity derived from the exact declared fields, and use
   the same complete identity for ArangoDB document keys. Keep these endpoints'
   existing `auto_increment_with_unique` routing type so the router remains
   Arango-only; do not switch them to `composite_pk`, which would add a
   RedisJSON write. Set each strategy's `primary_key` to its exact window
   identity while keeping the SQLite surrogate column as an internal storage
   detail. A repeat export replaces the keyed record only; legacy records
   remain alongside it and unchanged.
6. Add a scoped README paragraph that says matching site SLE summary windows
   replace the new keyed record and preserve legacy SQLite rows and ArangoDB
   documents. Do not alter the existing WAN links, response-refusal paragraph,
   menu titles, or operation counts.
7. Add the detailed persistence rule to `documentation/CONTRIBUTING-MistHelper.md`.
8. Add one release fragment that names both issues. Do not add external
   contract files. The work introduces no public API, transport, or database
   migration interface.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys/
  spec.md
  plan.md
  tasks.md                         # Produced by the later tasks phase.
  design/
    checklists/
      requirements.md
    research.md
    data-model.md
    quickstart.md
```

### Source Code (repository root)

```text
README.md
documentation/CONTRIBUTING-MistHelper.md
changelog.d/issue-4347-sle-window-summary-keys.md
src/
  operations/exporting/export/
    endpoint_family_exporter.py
  foundation/support/refactors/
    endpoint_primary_key_strategies.py
    sqlite_database_writer.py
  foundation/persistence/db/writers/
    arango_writer.py

tests/
  guardrails/
    test_endpoint_catalog.py
  unit/
    test_router.py
    arango_indexes/
      test_preservation.py
    refactors/
      test_sqlite_database_writer.py
  unit/db/
    sle_window_summary/
      test_export_identity.py
      test_backend_preservation.py
```

**Structure Decision**: Extend the existing endpoint-family export,
SLE-identity, SQLite writer, and Arango writer paths. Place focused new tests
in the fifth direct child under `tests/unit/db/`, and extend existing router,
SQLite, Arango, and endpoint-catalog tests. The current open PR #4358 changes
test files under `tests/unit/config/` and owns none of these paths.
The user granted a scoped handover for the README paragraph. Preserve existing
WAN content and the response-refusal paragraph from open PR #4619 when the
branch is later reconciled. PR #4208 and PR #4619 also list `README.md`.
The #4208 handover covers only the approved SLE paragraph. PR #4619 owns the
WAN paragraph, and this work does not edit it. No other open PR owns a planned
path. No new source package, public API, migration interface, or contracts
directory is needed.

## Phase 0: Research

See [design/research.md](design/research.md). It records the OpenAPI and
time-range evidence, current persistence patterns, decisions, rationale, and
alternatives.

## Phase 1: Design

- [Data model](design/data-model.md): exact identities, content, validation,
  and legacy/new-record lifecycle.
- [Quickstart](design/quickstart.md): offline validation using fake API
  responses and isolated stores.
- **Contracts**: omitted because no external interface or migration contract is
  added.

### Post-Design Constitution Gate

- The exact identity lists remain limited to the six histogram fields and
  eight impact-summary fields.
- Existing endpoint routing remains Arango-only for the polyglot backend; do
  not introduce RedisJSON writes as a side effect of the new key strategy.
- The README receives only the approved SLE window-summary paragraph.
  Existing WAN content, the #4619 response-refusal paragraph, menu titles, and
  operation counts remain unchanged.
- The new document/test hierarchy remains at or below five children per new
  level. Existing `specs/` and `changelog.d/` debt remains unchanged and is
  listed as separate remediation work above.
- The design preserves SDK transport behavior and uses no live service or
  production database.
- No migration, deletion, deduplication, or legacy-record rewrite is part of
  the design.
- Test coverage exercises output preservation, invalid-input failure safety,
  repeat replacement, backend preservation, and transport redaction without
  expanding endpoint scope.

**Post-design gate result**: Pass. The selected data identity is grounded in
the bundled schema and existing request path. The current branch is behind
`origin/main`, but this task does not authorize a rebase. No unresolved
identity or legacy-data question remains.

## Complexity Tracking

| Existing constraint or debt | Plan treatment | Separate action |
|---|---|---|
| `specs/` has 795 direct children, and `changelog.d/` has 272 direct children. | Keep artifacts under the existing managed route and use one unique issue-specific release fragment. Do not add a direct child to `specs/` or restructure the release-fragment directory. | Track separate incremental cleanup of both existing folder debts; do not broaden this feature. |
| Existing identity/export/writer code predates the current inline-comment rule in some touched blocks. | Apply the required inline comments to any whole function/block changed and add before/after action logging for meaningful validation and write actions. | None beyond implementation acceptance; do not refactor unrelated code. |
