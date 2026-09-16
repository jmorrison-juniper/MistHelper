<!-- site-read-handoff:01-specification -->
# Artifact 01: spec.md

## Feature Specification: Export twenty site-read endpoint datasets

**Status:** Planning complete. Implementation has not started.
**Source:** The twenty issue packets in this thread define the exact endpoint set.
**Feature directory:** `specs/2339-site-read-exports/`.
**Scope owner:** This handoff issue. The existing endpoint issues remain open.

## Problem and goal

Twenty open endpoint issues describe site datasets without a callable export path in the current application. Existing storage declarations do not provide that path. A NOC engineer needs to select one dataset, select one site, and export complete, sanitized records.

Provide one family menu entry, not twenty top-level entries. This is a bounded application of the design in #1807. Do not implement all of #1807 or close it with this work.

## User Scenarios and Testing

### US1: Select and export a site dataset (P1)

The operator selects one of twenty datasets and one site. The application reads the selected dataset and exports its records.

1. Given a supported dataset and a valid site, the application calls the exact SDK function in its packet.
2. Given multiple pages, the export contains every valid row in page order.
3. Given an empty successful response, the application reports no data and writes no file or database record.
4. Given an unknown dataset, the application makes no endpoint request.

Independent test: A fake SDK session supplies two successful pages. Assert the exact selected function, parameters, row sequence, and writer call.

### US2: Cancel or encounter a failed request safely (P1)

The operator can cancel at any prompt. A failed request must never appear as a successful empty dataset.

1. Blank input, `q`, `0`, EOF, and Ctrl+C cancel before the endpoint request.
2. Invalid choices and invalid site identifiers cause a clear message and no endpoint request.
3. HTTP 401, 403, 404, 429, 5xx, missing status, malformed rows, or a failed later page prevent export.
4. A repeated continuation or an exhausted page bound prevents export. Earlier pages must not become a complete-looking file.

Independent test: Supply one good page followed by a 403 response. Assert zero writer calls and an error outcome.

### US3: Store a repeatable, safe result (P1)

The operator can repeat the export without losing records or exposing credentials.

1. Keep the API identifier unchanged. Do not manufacture an `id`.
2. Repeated writes update the same business record in the selected backend.
3. The same inherited identifier at two sites has two endpoint-document storage keys.
4. Sanitize credentials before flattening, logging record content, or passing raw records to a database mirror.
5. A primary writer failure produces an error outcome. A database mirror failure remains visible through the canonical writer warnings.

Independent test: Write a two-row fixture twice into a temporary SQLite database. Verify two rows and updated non-key values. Verify separate scoped keys in fake ArangoDB and Redis writers.

### US4: Discover and maintain the feature (P2)

The main menu exposes the family once. The generated menu reference, README, changelog, source specs, and tests agree.

1. Existing menu numbers and public exports remain unchanged.
2. The new menu belongs to `interactive_safe`. Normal `--test` must skip its prompts.
3. A callable exporter without menu wiring is not complete.
4. A source issue closes only after its endpoint packet and the shared acceptance tests pass.

Independent test: The registry coverage guard and a mocked menu invocation verify dispatch without authenticating to Mist.

## Functional Requirements

- **FR-001:** Provide exactly one top-level family menu and exactly the twenty endpoint choices named in this handoff.
- **FR-002:** Obtain organization and site context through existing selection services. Validate UUIDs before the selected endpoint request.
- **FR-003:** Use the installed `mistapi` SDK and its configured session. Never derive a Python module from a URL suffix.
- **FR-004:** Follow every continuation through the SDK transport. Validate the status and array shape of every page before accepting records.
- **FR-005:** Apply the existing adaptive pacer and session retry policy. Do not create another retry loop or a new session.
- **FR-006:** Distinguish cancelled, empty, saved, and error outcomes. Never save a partial fetch as a successful full export.
- **FR-007:** Keep complete noncredential fields, nested values, API order, and business keys. Preserve the caller's original records.
- **FR-008:** Redact credential fields before every output boundary. Do not print raw responses, raw exception messages, or pagination tokens.
- **FR-009:** Call `DataExporter.write_with_format_selection` with the exact operationId. Pass only sanitized raw records in `ExportBackendOptions.raw_data`.
- **FR-010:** Use a fixed operationId and canonical site UUID for the output basename. All generated output must remain under `data/`.
- **FR-011:** Preserve repeated-write identity and site isolation. Reject missing business-key components before invoking any writer.
- **FR-012:** Restrict storage-key changes to an explicit opt-in on these twenty strategies. Keep other endpoint keys and routing unchanged.
- **FR-013:** Preserve canonical backend warnings. A primary output success does not prove that every database mirror succeeded.
- **FR-014:** Use class-owned behavior, meaningful inline comments, action logging, typed dependencies, and bounded functions. Add no new `src` import of `MistHelper`.
- **FR-015:** Add offline unit, property, storage, menu, and regression tests. Do not use real Mist credentials to run them.
- **FR-016:** Update the twenty source specs, README, changelog, and both generated menu-reference copies. Do not renumber existing entries.

## Measurable Success Criteria

- **SC-001:** All twenty packet cases reach their exact SDK GET callable through one family menu.
- **SC-002:** A two-page fixture exports both pages. Every failed-page fixture exports zero rows.
- **SC-003:** Cancellation at every prompt causes zero selected-endpoint calls.
- **SC-004:** Known credential sentinels appear in neither exported payloads nor captured logs.
- **SC-005:** Repeat writes preserve row counts. Different sites and different composite-key values remain distinct.
- **SC-006:** Focused tests pass. The new package reaches at least 90 percent branch coverage. Repository gates meet their current configured thresholds.
- **SC-007:** Exactly one menu entry is added. The original public API snapshot and existing menu numbers do not change.

## Non-Functional Requirements

Use Python 3.13 or newer on Windows and Linux. Use existing runtime dependencies. Process requests sequentially. Limit a fetch to 1,000 pages and 1,000,000 records. Crossing either limit is a visible error with no export, not truncation. These are safety limits, not a latency promise about Mist Cloud.

## Clarifications and scope decisions

The packet fixes the SDK module and argument set. Optional filters remain at SDK defaults unless a packet explicitly sets one. Derived endpoints that accept `resolve` use `resolve=True`. The two zone-stat endpoints without `limit` must not receive it. Stats exports represent the current returned snapshot, not a newly invented time series.

The twenty old specs requested twenty menu rows. This handoff replaces that choice with one family menu. Preserve their read-only and output requirements. Amend their stale module paths and menu wording during implementation.

## Out of Scope

Do not change Mist configuration, run upgrades, invoke device commands, add web routes, implement every endpoint in #1807, repair the full backlog, or alter dependency pins. Do not add parallel requests, raw export mode, arbitrary endpoint dispatch, production database migrations, or new environment variables. Do not repair unrelated existing `src` back-references as part of this feature.
