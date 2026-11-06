# Feature Specification: Stable SLE summary window keys

**Feature Branch**: `jmorrison-juniper-sle-window-summary-key-assessment`

**Created**: 2026-11-06

**Status**: Specified

**Issues**: #4347 and #4348

**Input**: User description:
> "Fix stable-window primary keys for getSiteSleImpactSummary and getSiteSleHistogram, preserve all existing data, use no live Mist or production database operations, and do not invent identity fields."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repeat an export without new duplicates (Priority: P1)

The network operator exports the same histogram or impact summary window again. The export updates its new keyed record and preserves other windows.

**Why this priority**: Repeated exports must not create new duplicates or overwrite a different measurement window.

**Independent Test**: Export local sample responses twice with changed measurements. Compare the resulting records without any live service.

**Acceptance Scenarios**:

1. **Given** an empty store, **When** each endpoint exports one identity twice, **Then** each endpoint has one keyed record with the latest measurements.
2. **Given** a stored window, **When** only its returned `start` or `end` changes, **Then** both windows remain separate.
3. **Given** equal boundaries, **When** one source dimension changes, **Then** each identity retains its own record.
4. **Given** one identity, **When** only measurements, labels, or grouping arrays change, **Then** the same keyed record receives the new content.

### User Story 2 - Retain all legacy data (Priority: P1)

The network operator keeps every existing record when the export starts to use complete window identities.

**Why this priority**: A key repair must not destroy historical data or silently merge records.

**Independent Test**: Seed isolated stores with legacy duplicates and unrelated records. Export a matching identity twice and compare all original content and identifiers.

**Acceptance Scenarios**:

1. **Given** legacy rows or documents, **When** the first matching export runs, **Then** all original records remain unchanged beside one new keyed record.
2. **Given** that first keyed record, **When** a later matching export runs, **Then** only that keyed record receives updated content.
3. **Given** several legacy duplicates, **When** exports repeat, **Then** every duplicate retains its original identity and values.
4. **Given** unrelated endpoint records, **When** either repaired endpoint exports data, **Then** those unrelated records remain unchanged.

### User Story 3 - Preserve valid values and reject incomplete identity (Priority: P1)

The maintainer can distinguish a documented empty string from a missing impact-summary identity field.

**Why this priority**: Invented values or an incorrect rejection can silently lose valid summaries or combine different results.

**Independent Test**: Use local sample responses with empty strings, absent fields, invalid types, and conflicting returned source dimensions.

**Acceptance Scenarios**:

1. **Given** string `classifier` and `failure` fields, **When** either or both equal `""`, **Then** the export preserves those values and accepts the identity.
2. **Given** a missing or non-string `classifier` or `failure`, **When** validation runs, **Then** the export reports an invalid identity without writing records.
3. **Given** a missing or invalid required source dimension or boundary, **When** validation runs, **Then** the export reports the invalid identity without changing stored data.
4. **Given** response fields that conflict with selected source dimensions, **When** the export identifies the window, **Then** the selected source dimensions remain authoritative.
5. **Given** an invalid record beside a valid record, **When** the export validates the response, **Then** it rejects the invalid response before persistence.

### Edge Cases

- Separate sites, scopes, scope identifiers, and metrics can return identical boundaries.
- Impact summaries can differ only in `classifier` or `failure`. Each different string value identifies a separate summary.
- Empty strings are valid only where the documented contract permits them. Missing values and non-string values are not equivalent to empty strings.
- Strings with separators or non-ASCII characters must not cause identity collisions or value changes.
- Missing, nonnumeric, nonfinite, or reversed boundaries must stop persistence. Zero-length windows with equal valid boundaries remain valid.
- Numerically equal boundaries must identify the same window, regardless of an equivalent supported numeric representation.
- Default last-24-hour requests can return different actual boundaries on successive exports. Such windows remain separate.
- Empty measurement or grouping arrays do not justify invented identity fields.
- An empty response retains existing no-data behavior and does not change stored data.
- Legacy duplicates remain visible. This repair does not correct historical totals.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both endpoints MUST identify each exported record by its complete source dimensions and actual returned window boundaries.
- **FR-002**: Histogram identity MUST contain exactly `site_id`, `scope`, `scope_id`, `metric`, `start`, and `end`.
- **FR-003**: Impact-summary identity MUST contain exactly `site_id`, `scope`, `scope_id`, `metric`, `classifier`, `failure`, `start`, and `end`.
- **FR-004**: The selected request MUST supply `site_id`, `scope`, `scope_id`, and `metric`. Conflicting response fields MUST NOT replace those source dimensions.
- **FR-005**: The response MUST supply `start` and `end`. Impact summaries MUST also supply string `classifier` and `failure` values.
- **FR-006**: Empty `classifier` and `failure` strings MUST remain valid identity values, unchanged. Missing, null, numeric, boolean, array, and object values MUST fail validation.
- **FR-007**: Identity MUST NOT depend on measurements, labels, grouping arrays, export time, generated identifiers, or undocumented fields.
- **FR-008**: Repeated exports with the same complete identity MUST update only the same new keyed record in SQLite and ArangoDB.
- **FR-009**: A change to any identity field MUST retain a separate keyed record. A change only to non-identity content MUST update the existing keyed record.
- **FR-010**: Every legacy row and document MUST retain its original identifier and values. The repair MUST NOT delete, migrate, deduplicate, re-key, or rewrite legacy data.
- **FR-011**: The first export MAY add one keyed record beside matching legacy duplicates. Later exports MUST reuse only that new keyed record.
- **FR-012**: The export MUST validate complete identities before persistence. Invalid identities MUST produce a visible error without partial writes or fabricated values.
- **FR-013**: Returned boundaries MUST remain authoritative. The exporter MUST NOT substitute requested times, export time, or a reconstructed default window.
- **FR-014**: The repair MUST preserve all returned measurement, label, and grouping content through the existing export representation.
- **FR-015**: Existing trend-endpoint behavior and unrelated endpoint identities, output choices, and no-data behavior MUST remain unchanged.
- **FR-016**: Verification MUST use only local sample responses, isolated temporary stores, or store doubles. It MUST NOT call live Mist or access production databases.
- **FR-017**: The exporter MUST retain its existing required-path-only calls. This repair MUST NOT add optional query parameters or identity requirements for parameters it does not send.
- **FR-018**: Product documentation MUST state that matching exports replace only the new window record and preserve existing SQLite rows and ArangoDB documents.

### Mist Cloud Transport Requirements

The existing methods are `mistapi.api.v1.sites.sle.getSiteSleHistogram` and `mistapi.api.v1.sites.sle.getSiteSleImpactSummary`.
Both endpoint paths require `site_id`, `scope`, `scope_id`, and `metric`.
The endpoint-family exporter passes only those required path arguments and sends no optional query parameters.

This repair introduces no new transport, authentication behavior, or direct HTTP call.
Offline contract checks must confirm unchanged method selection, source arguments, failure safety, and credential redaction.
No live authentication or endpoint probe forms part of verification.

### Key Entities

- **Histogram window**: One measurement distribution for a site, scope, scope identifier, metric, and actual returned `start` and `end`.
- **Impact-summary window**: One impact summary with those dimensions plus the returned `classifier` and `failure` strings.
- **New keyed record**: The record that receives later exports with the same complete identity.
- **Legacy record**: Any preexisting row or document, including a duplicate, whose identifier and values must remain unchanged.
- **Summary content**: Measurements, axis labels, and grouping arrays that describe a window but do not identify it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each endpoint, three exports of one identity produce exactly one new keyed record containing the third export's content.
- **SC-002**: Every single-field identity variation in the offline acceptance set retains a separate record, with zero collisions.
- **SC-003**: After a first matching export and two repeat exports, 100 percent of seeded legacy and unrelated records retain their original identifiers and values.
- **SC-004**: All four empty/nonempty combinations of `classifier` and `failure` succeed and retain their exact strings.
- **SC-005**: Every missing-field and invalid-type acceptance case reports failure and changes zero stored records.
- **SC-006**: Every accepted response retains its measurements, labels, and grouping content. Reviewers can distinguish preserved legacy records from the new keyed record.
- **SC-007**: All acceptance checks complete with zero live Mist calls, zero production database operations, and zero regressions in the two existing trend exports.

## Assumptions

### Source contract and time boundaries

- The bundled Mist OpenAPI 3.1 specification is version `2609.1.0`.
- Histogram responses require `metric`, `start`, `end`, `data`, `x_label`, and `y_label`.
- Impact-summary responses require `metric`, `start`, `end`, `classifier`, `failure`, `ap`, `wlan`, `device_os`, `device_type`, and `band`.
- The impact-summary grouping arrays are `ap`, `wlan`, `device_os`, `device_type`, and `band`. They are content, not identity dimensions.
- `classifier` and `failure` have type string without a minimum-length constraint. Empty strings therefore remain valid.
- The official time-range guide states that returned `start` and `end` are actual boundaries. The default range is the last 24 hours.
- The guide's default range does not imply a stable identity across repeated requests. Actual returned boundaries control identity.

### Existing behavior and dependencies

- Merged PR #4350 implements `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend`. This combined fix covers only the two remaining endpoints.
- PR #4350 preserves old rows and documents, permits one first keyed record beside legacy duplicates, and replaces only that keyed record afterward.
- The same non-destructive legacy behavior is required here. No historical cleanup is authorized.
- PR #4208 and PR #4619 both list `README.md`. The #4208 owner granted this work a scoped handover for the approved SLE paragraph.
- PR #4619 owns a WAN response-refusal paragraph in `README.md`. Do not edit that paragraph, and preserve it when the branch is reconciled.
- PR #4358 owns no planned path. Its related test files are under `tests/unit/config/...`; its full file list also includes other files.
- The open-PR file lists were checked before implementation. No other open PR owns the planned paths.

### Phase and scope limits

- This feature changes only the two SLE summary identities, their SQLite and ArangoDB persistence, focused tests, and related documentation.
- Add one bounded README paragraph about window replacement and legacy-record preservation. Do not change menu titles, operation counts, or WAN content.
- Add the detailed persistence behavior to `documentation/CONTRIBUTING-MistHelper.md`.
- Add one release-note fragment that names both issues #4347 and #4348.
- Keep every existing SQLite row and ArangoDB document unchanged. Do not migrate, delete, deduplicate, re-key, or rewrite legacy data.
- Verify with local responses, temporary SQLite stores, and ArangoDB test doubles only. Do not call live Mist or access production databases.
- The current feature branch is five commits behind `origin/main` at `2758fe4ee87de047bb66003a1e76d7657aae6f1b`. Do not rebase, push, or create a pull request before local validation and a scope report.
- The branch pointer and issue records remain unchanged during local implementation.
- `pwsh` is unavailable. The destination uses the exact `Resolve-SpecFeaturePath` base-5 algorithm, checked against existing parent child counts.
- The managed destination is `specs/numbered/0/0/1/1/4/3/4/2/4347-sle-window-summary-keys`.
- Downstream commands must select this directory explicitly without replacing another feature's shared selector.
- Future optional-query support, broad identity audits, historical data cleanup, and trend-endpoint redesign are outside scope.

### Evidence references

These references support the supplied research facts and local contract checks. They do not form an implementation plan.

- Bundled contract: `documentation/mist-api-openapi31json.json`, response schemas `SleHistogram` and `SleImpactSummary`.
- Existing export call behavior: `src/operations/exporting/export/endpoint_family_exporter.py`.
- Existing identity behavior: `src/foundation/support/refactors/endpoint_primary_key_strategies.py`.
- Numeric route and destination checks: `.specify/scripts/powershell/spec-route.ps1`.
- Related change: [merged PR #4350](https://github.com/jmorrison-juniper/MistHelper/pull/4350).
- Related ownership check: [open PR #4358](https://github.com/jmorrison-juniper/MistHelper/pull/4358).
- Scoped README handover: [open PR #4208](https://github.com/jmorrison-juniper/MistHelper/pull/4208).
- WAN paragraph to preserve: [open PR #4619](https://github.com/jmorrison-juniper/MistHelper/pull/4619).
- The official time-range statements come from the request's research context. This phase performs no live Mist verification.
