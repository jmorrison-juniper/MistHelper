# Implementation Plan: Export beacon information (Menu #50)

Spec: specs/099-audit-menu-50-export-beacon-information/spec.md
Branch (for context only): ci/triage-fixes-20260403-171203

---

## Technical Context

- Feature: SiteClientExporter.beacons — a menu operation that exports beacon records for a selected site.
- API endpoint: mistapi.api.v1.sites.beacons.listSiteBeacons (site-scoped, paginated).
- Current implementation summary: SiteClientExporter.beacons delegates to SiteExportUtils._export_data(api_call=mistapi...listSiteBeacons, data_type="beacons", sort_key="name"). Data is collected via mistapi.get_all(...), flattened using DataProcessingUtils.flatten_nested_fields(), escaped, and written via DataExporter.save_data_to_output(), which selects CSV or SQLite based on OUTPUT_FORMAT.

Unknowns / NEEDS CLARIFICATION (to be resolved in Phase 0 research):
- presence_and_name_of_stable_beacon_identifier: Whether beacon records always include a stable 'id' field or sometimes use 'uuid' or another name. This affects primary key strategy for SQLite. (NEEDS CLARIFICATION)
- endpoint_primary_key_mapping_for_beacons: Whether ENDPOINT_PRIMARY_KEY_STRATEGIES already contains an explicit entry for listSiteBeacons. (NEEDS CLARIFICATION)
- mistapi_get_all_rate_limit_behavior: Does mistapi.get_all already implement robust retry/backoff for HTTP 429, or should SiteExportUtils._export_data add retries? (NEEDS CLARIFICATION)
- desired_repeat_export_behavior: Product decision: when natural PK absent, should repeated exports clear-and-repopulate (current auto-increment_with_unique behavior) or adopt a consistent upsert behavior? (NEEDS CLARIFICATION)
- default_list_expansion_limit: Preferred default for limiting list-of-dicts expansion (suggested option: 3) and whether to make it configurable. (NEEDS CLARIFICATION)

Other contextual facts (known):
- Data flattening currently indexes list-of-dicts into per-index columns (tags_0_name, tags_1_name, ...), causing variable schema.
- SQLite strategy detection currently prefers explicit ENDPOINT_PRIMARY_KEY_STRATEGIES, else infers from fields and stack inspection. Stack inspection is brittle.
- Outputs are written to data/; default SQLite DB is data/mist_data.db and CSV files under data/.


## Constitution Check

Relevant constitution items:
- Technology & Compatibility Constraints:
  - "mistapi" must be used for Mist API calls.
  - "Database Keys: Natural business keys from the Mist API (not artificial IDs). Primary key strategy MUST be defined in ENDPOINT_PRIMARY_KEY_STRATEGIES before implementing any new operation."
- Observability & Logging: INFO-level logging for schema diffs when columns change is required by plan proposals (not explicitly in constitution but aligns with Observability principle).
- Safety-First: Input validation and safe_input patterns apply to interactive inputs.

Evaluation against constitution:
- Compliance: Use of mistapi is already in place (compliant).
- Gate: Primary-key strategy requirement — current codebase relies on fallback heuristics and stack inspection when explicit mapping is absent. This violates the constitution's requirement that primary key strategy MUST be defined in ENDPOINT_PRIMARY_KEY_STRATEGIES before implementing a new operation unless a documented, justified exception is present.

Gate decision:
- This plan will require adding (or documenting) an explicit ENDPOINT_PRIMARY_KEY_STRATEGIES entry for listSiteBeacons (or ensuring SiteExportUtils passes api_function_name so DatabaseSchemaUtils can deterministically apply an existing mapping). The plan enforces this as a hard gate: implementation work that modifies SQLite behavior must include an explicit strategy mapping or a strong rationale for a temporary exception recorded in the plan's Complexity Tracking table.

If any gate is to be violated, a written justification must be included in "Complexity Tracking" and approved by reviewers. No implementation code will be merged without satisfying the gate.


## Gates & Risks

- Gate 1 (Primary Key Strategy): ERROR if code changes that affect SQLite write behavior are merged without adding a deterministic primary key strategy for listSiteBeacons in ENDPOINT_PRIMARY_KEY_STRATEGIES or without explicitly passing api_function_name through SiteExportUtils._export_data → DataExporter.
- Gate 2 (Testing): Unit tests for flattening and SQLite write strategies MUST be added; otherwise plan cannot advance to final code changes.
- Risk 1: Schema explosion due to list-of-dicts flattening — mitigated by adding configurable max_list_items and an aggregation mode.
- Risk 2: API rate-limits — mitigated by explicit retry/backoff and logging.


## Phase 0 — Outline & Research (deliverable: research.md)

Goals:
- Resolve all NEEDS CLARIFICATION items above.
- Produce decisions with rationale and alternatives.

Research tasks (one per unknown):
- Research presence_and_name_of_stable_beacon_identifier for Mist API listSiteBeacons responses.
- Research whether ENDPOINT_PRIMARY_KEY_STRATEGIES already includes a mapping for listSiteBeacons and, if absent, propose an explicit mapping.
- Research mistapi.get_all behavior regarding 429 retries/backoff and confirm whether SiteExportUtils._export_data must add retries.
- Decide desired_repeat_export_behavior: prefer idempotent upserts when natural key exists; define behavior when it does not.
- Choose default_list_expansion_limit and aggregation mode options; recommend defaults and config knobs.

Phase 0 outcome (this plan includes the research conclusions below in research.md).


## Phase 1 — Design & Contracts (deliverables: data-model.md, /contracts/*, quickstart.md)

Prerequisites: research.md complete

Planned deliverables and brief content summary:

1) data-model.md
- Entity: Beacon
  - Fields (flattened): id (uuid), uuid, mac, name, type, power, major, minor, x, y, map_id, site_id, created_at, plus any flattened nested fields (location_lat, location_lon, tags_0_name, ...)
  - Validation: id/uuid presence preferred; mac format validation (hex, colon/dash-free normalization); timestamps normalized to ISO-8601 UTC; numeric bounds for x/y if maps use coordinates.
  - Relationships: Beacon.site_id -> Site.id
  - State transitions: N/A (export-only read model)

2) contracts/
- contract: DataExporter.save_data_to_output(data, filename, api_function_name=None, output_format=None, max_list_items=None)
  - Description: data is list[dict] flattened; filename base without extension; api_function_name explicitly informs schema strategy; output_format overrides global OUTPUT_FORMAT; max_list_items controls list expansion.
  - Examples: CLI usage and internal call examples.

3) quickstart.md
- How to run Menu #50 locally:
  - From interactive menu: choose Menu 50 → select site → choose format (csv/sqlite) → verify data/<file> or data/mist_data.db table.
  - Programmatic invocation example: SiteClientExporter.beacons(apisession, site_id, output_format='sqlite')

4) Agent context update
- Run .specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot to add new tech/context (SQLite schema strategy, list flattening options) to the copilot agent context. This will be executed as part of this plan.


## Phase 2 — Implementation Plan (high-level tasks)

Note: Actual code changes are out-of-scope for this planning artifact. This phase lists the tasks to be executed by engineers.

1. Code changes
  - Update SiteExportUtils._export_data to pass api_function_name=api_call.__name__ (mandatory).
  - Modify DataExporter.save_data_to_output signature to accept api_function_name and pass it to SQLiteDatabaseWriter.write(). Ensure default behavior unchanged if None.
  - Add/extend ENDPOINT_PRIMARY_KEY_STRATEGIES with entry for listSiteBeacons: prefer natural_pk on 'id' (or 'uuid' if 'id' absent). Example mapping: 'listSiteBeacons': {"type":"natural_pk","fields":["id","uuid"]} (implementation should pick first present field).
  - Add optional parameters to DataProcessingUtils.flatten_nested_fields: max_list_items (default=3), list_mode in {'expand','aggregate'} (default='expand' for backward compatibility). Implement aggregation as JSON-encoded string when chosen.
  - Implement explicit retry/backoff wrapper around api_call invocation inside SiteExportUtils._export_data (exponential backoff, up to 3 attempts on 429/5xx). Log retries and final status.
  - Add schema fingerprinting: after flattening, compute sorted list of columns, compare against file data/<name>.schema.json (if exists), log INFO with added/removed columns, and overwrite schema file for next run.
  - For CSV writing of large exports, ensure streaming write (writerow) to avoid large memory usage (refactor if currently materializing all rows). Add tests to validate memory usage on simulated large lists.

2. Tests
  - Unit tests for flatten_nested_fields with: nested dicts, lists-of-dicts with varying lengths, stringified JSON/list fields, and max_list_items modes.
  - Unit tests for DatabaseSchemaUtils.get_endpoint_strategy using explicit api_function_name and fallbacks.
  - Unit/integration tests for SQLiteDatabaseWriter for natural_pk (upsert), composite_pk, and auto_increment_with_unique (clear-and-insert) behaviors.
  - Integration tests: site export end-to-end with mocked mistapi responses including pagination and simulated 429 responses to verify retry/backoff and partial saves.

3. Docs & Observability
  - Update README and menu table to document Menu #50 and the new configuration flags (max_list_items, list_mode).
  - Add INFO-level logs for schema diffs and retry attempts.
  - Add code comment/docstring in SiteExportUtils._export_data explaining forwarding of api_function_name.

4. Release & Deployment
  - Run the full deployment pipeline per Constitution IV: syntax validation, commit using version YY.MM.DD.HH.MM format, push and wait for CI.


## Complexity Tracking

- Complexity item: Adding max_list_items and list_mode increases function parameter count; to comply with Five-Item Rule (max 5 params), bundle export options into a dataclass ExportOptions if needed. This will be implemented if any function exceeds parameter limits.
- Justification for any temporary gate relaxation must be recorded here.


## Milestones & Deliverables

- M0 (this plan): plan.md, research.md, data-model.md, contracts/, quickstart.md — delivered here.
- M1 (design complete): PR with code changes for api_function_name propagation, tests skeletons — target 1 week.
- M2 (implementation): Full implementation and unit tests — target 2 weeks.
- M3 (integration & release): CI green and container/podman image pushed — target 3 weeks.


## Artifacts generated by this plan

- specs/099-audit-menu-50-export-beacon-information/plan.md (this file)
- specs/099-audit-menu-50-export-beacon-information/research.md
- specs/099-audit-menu-50-export-beacon-information/data-model.md
- specs/099-audit-menu-50-export-beacon-information/contracts/site-beacons-contract.md
- specs/099-audit-menu-50-export-beacon-information/quickstart.md


---

Plan author: Spec auditing workflow
Date: 2026-04-03
