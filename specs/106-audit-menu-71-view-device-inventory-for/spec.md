# Feature Specification: View device inventory for a site (Audit: Menu 71)

**Feature Branch**: audit-site-inventory
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Create a feature specification for MistHelper Menu #71: \"View device inventory for a site\"\n\nFunction: InteractiveDisplayUtils.site_inventory\nCategory: interactive\nSQL export relevant: No\n\nThis is an AUDIT spec — analyze the existing implementation in MistHelper.py, document current state, identify issues, and define acceptance criteria for fixes.\n\nCRITICAL: You MUST write the spec file to disk at this exact path:\n  specs/106-audit-menu-71-view-device-inventory-for/spec.md\n\nFocus on: performance for large sites, pagination, caching, UI formatting, and test coverage."  


## Summary (one-line)

Audit of Menu #71 (InteractiveDisplayUtils.site_inventory / SiteDeviceExporter.device_inventory): document current behavior, identify defects and risks (performance, pagination, caching, UI formatting, test coverage), and define clear, testable acceptance criteria for fixes.


## Background & Scope (mandatory)

This is an audit-style specification for the MistHelper interactive menu option that displays a site's device inventory (Menu #71). The existing code path invoked by the menu is InteractiveDisplayUtils.site_inventory(), which delegates to SiteDeviceExporter.device_inventory(site_id). The current implementation fetches all devices for a site in one API call, writes the inventory CSV, constructs a full PrettyTable, and logs the table string. The audit scope is limited to:

- Performance and memory behavior when a site contains large numbers of devices (hundreds to tens of thousands)
- Correct handling of paginated API responses and robust fetching for large result sets
- Caching strategies and freshness controls to avoid repeated expensive fetches
- Interactive UI formatting and pagination for terminal display (page size, navigation, truncation)
- Test coverage: unit tests, integration tests, and performance/soak tests

Excluded: changes to data model or permanent storage layout outside of CSV/cache files, and unrelated menus.


## User Scenarios & Testing (mandatory)

### User Story 1 - View site inventory (Priority: P1)

A network operator wants to quickly view devices for a single site, including APs, switches and gateways, and export the inventory to CSV.

Why this priority: Primary value of Menu #71 — daily operational task for support engineers.

Independent Test: Run the menu for a small site (<= 200 devices), confirm a CSV is written, verify a paginated interactive display shows the first page and allows navigation.

Acceptance Scenarios:
1. Given a site with 50 devices, when the operator selects Menu #71 and confirms the site, then the tool writes a CSV and displays page 1 (default 20 rows) within 2 seconds.
2. Given a site with devices of mixed types, when the operator filters by device type (AP/switch/gateway), then only matching rows appear both in the CSV and interactive display.

---

### User Story 2 - View very large site inventory (Priority: P1)

An engineer needs to inspect a site that contains a very large inventory (>= 5,000 devices). The tool must fetch and export the data without exhausting memory and must present an interactive, responsive paginated view.

Why this priority: Large-site performance is a reliability and usability risk affecting production.

Independent Test: Execute Menu #71 against a test org/site simulated with 10,000 devices (mock API). Verify CSV is produced and interactive page loads (page render) complete under the performance target.

Acceptance Scenarios:
1. Given a site with 10,000 devices, when the operator runs the inventory export, then the fetch+CSV-write completes within 120 seconds and peak memory usage remains below 500 MB (CI measurable).  
2. Given a large CSV, when the operator navigates pages, then each page displays within 2 seconds and pagination commands (next/prev/jump) work correctly and deterministically.

---

### User Story 3 - Cached inventory with manual refresh (Priority: P2)

A support engineer wants to avoid repeated full fetches during repeated investigations. The tool should cache the last inventory per site and allow a forced refresh.

Why this priority: Reduces API load and improves responsiveness for repeated usage.

Independent Test: Run Menu #71 twice in short succession; second run should use cached results unless a "refresh" option is chosen. Validate cache TTL is respected.

Acceptance Scenarios:
1. Given a cached inventory younger than TTL (default 4 hours), when the operator runs Menu #71, then the display is served from the cache and no API calls are made.  
2. Given the operator chooses "Force refresh", when the command runs, then a fresh API fetch happens and cache is updated.

---

### Edge Cases

- Empty site (0 devices): show clear message "No devices found" and create an empty CSV with header only.  
- Deeply nested device fields produce many columns (>100): UI should fall back to a curated default column set and give an option to export full CSV.  
- API returns partial pages or non-200: retry with exponential backoff (configurable limits), and report a clear error to the user with actionable guidance.  
- Devices with extremely long field values (multi-kB strings): columns truncated in interactive view, full values preserved in CSV.  
- Cache file corrupted or unparsable: ignore cache, fetch fresh data and overwrite cache; log a warning.


## Requirements (mandatory)

### Functional Requirements

- FR-001: The tool MUST fetch the full site device inventory reliably for any site size (including >10k devices) while avoiding unbounded memory growth.
- FR-002: The tool MUST handle API pagination (or streaming) and ensure all devices are retrieved even when the API returns paged responses.
- FR-003: The tool MUST write a CSV export of the full inventory (all records) without holding all rows in RAM simultaneously for very large sites.
- FR-004: The interactive display MUST provide paginated viewing in the terminal (default page size 20, configurable), with next/previous/jump controls and a clear header summary.
- FR-005: The interactive display MUST limit column width and number of columns by default (curated view), with an option to view/export the full set of fields.
- FR-006: The tool MUST provide caching of per-site inventory on disk (data/SiteInventory_{site_id}.json or similar) with a configurable TTL (default 4 hours) and a "force refresh" option.
- FR-007: The tool MUST log meaningful progress and errors and surface user-facing messages for common failures (timeouts, rate limits, permission denied).
- FR-008: The tool MUST include deterministic sorting of rows for reproducible paging and CSV output (e.g., sort by device type then model then name) unless user overrides.
- FR-009: The tool MUST include unit tests and integration tests (mocked API) covering small, medium, and large inventories, caching behavior, pagination UI, and error handling.
- FR-010: The tool MUST include a performance test (CI or manual) demonstrating reasonable time and memory for 10k devices (see Success Criteria).

*Assumptions documented in the Assumptions section below.*


### Key Entities

- Site: Selected site ID and human-friendly name.  
- Device Record: Inventory row for a single device. Key attributes include id, name, type (ap/switch/gateway), model, mac, ip, serial, status, last_seen, and site_id.  
- Inventory Cache Entry: {site_id, timestamp_utc, device_count, file_path_or_blob, hash}  
- PaginationConfig: {page_size, current_page, sort_key}


## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: For a site with 10,000 synthetic devices (mocked API), a full fetch + CSV write completes within 120 seconds on a 4-core, 8GB test runner.  
- SC-002: Peak process memory usage during the operation remains under 500 MB for 10k devices.  
- SC-003: Interactive page render time (per-page display) is under 2 seconds for page size 20 for inventories up to 10k rows.  
- SC-004: 100% of devices present in the API are exported to the CSV; pagination correctness measured by comparing CSV row count to API total reported value.  
- SC-005: At least one unit test covers the following areas: pagination logic, cache TTL and force-refresh, display truncation, and API error handling.  
- SC-006: The feature provides clear user-facing messages for empty sites, permission errors, and API timeouts.

Verification notes: Success criteria must be validated in CI using mocked large datasets and measurement tooling (time/memory). Exact thresholds may be adjusted after initial implementation, but remain technology-agnostic.


## Current Implementation (analysis)

Summary of current code path (observed in MistHelper.py):

- InteractiveDisplayUtils.site_inventory(): prompts the user to select a site and calls SiteDeviceExporter.device_inventory(site_id).
- SiteDeviceExporter.device_inventory(site_id, device_type="all", csv_filename="SiteInventory.csv"):
  - Calls mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="all").data
  - If device_type filter provided, filters the returned list in memory
  - Sorts the inventory by model and flattens nested fields
  - Calls DataExporter.save_data_to_output(inventory, csv_filename)
  - Builds a PrettyTable with all discovered fields and adds all rows
  - Logs table.get_string() via logging.debug (does not print the table to stdout)

Observed strengths:
- Uses flattened fields and sanitization utilities (DataProcessingUtils) and writes a CSV export.
- Sorts results for reproducibility.

Observed issues and risks (detailed):
1. No pagination or streaming: a single API call used with .data may return only the first API page (depending on mistapi behavior) or may load large result sets into memory, causing high memory usage and slow operations for large sites.
2. No use of mistapi.get_all or explicit paged iteration; behavior is inconsistent across other functions where mistapi.get_all is used (see SiteDeviceExporter.device_stats uses mistapi.get_all).  
3. Full in-memory table build: the implementation constructs a PrettyTable with all columns and rows and retains the entire inventory list in memory; for large sites this risks OOM and slow rendering.
4. Display gap: the PrettyTable is logged in debug but not printed to the interactive terminal, so interactive behavior is limited or inconsistent with user expectations.
5. No caching: every invocation fetches fresh data even if a recent inventory is available; repeated use causes unnecessary API load.
6. No interactive pagination: the code lacks CLI paging/navigation, forcing operators to rely on CSV export or log output for large inventories.
7. Columns explosion: flattening arbitrary nested fields can produce dozens-to-hundreds of columns which break the terminal display; no curated default column set is provided.
8. Insufficient test coverage: no specific unit tests or integration tests for the device inventory code path were found in the repository scan; no performance tests exist.
9. Error handling: simple checks do exist for empty rawdata, but there's no robust retry/backoff for intermittent API failures or rate limits.


## Recommended Fixes (what to change, not implementation-level how)

- Fetching & pagination: Replace the single-call approach with a robust paginated fetch that guarantees all devices are retrieved for the site. Ensure the fetch approach is resilient to API page boundaries and rate limits.

- Streaming CSV write: When exporting, stream rows directly to CSV to avoid building the full inventory list in memory for very large sites.

- Interactive paging & formatting: Implement an interactive terminal pager for inventory viewing with a default curated column set, truncation of long values, and next/prev/jump controls. Provide an option to view/export the full set of fields.

- Caching: Add a per-site cache with configurable TTL and a force-refresh option. Cache metadata must include timestamp and device_count and allow invalidation.

- Logging & error handling: Improve logging for progress and errors, add retry/backoff for API calls (configurable), and surface friendly messages for common failures.

- Tests: Add unit tests (pagination logic, caching, UI truncation), integration tests with mocked API responses for small/large datasets, and a performance test/benchmark for a 10k-device scenario.


## Acceptance Criteria (testable)

- AC-001: The inventory fetch MUST correctly retrieve the full device set for a site where the API returns paged responses. Validation: compare the CSV row count with the API-reported total and assert equality.

- AC-002: The export mechanism MUST write the full CSV without retaining all device records in RAM simultaneously. Validation: run a synthetic 10k-device test and measure peak memory usage remains below the threshold (see SC-002).

- AC-003: The interactive display MUST show a summary header (total devices, counts by type, top 5 models) and present results in paginated pages. Validation: automated UI test that simulates user navigation through pages and asserts page content consistency.

- AC-004: Cached inventory MUST be used when younger than TTL and force-refresh MUST fetch fresh data. Validation: mock API to detect whether network calls occur on cached read and assert behavior.

- AC-005: The default interactive view MUST present a curated set of columns (id, name, type, model, mac, ip, status, last_seen). The user MUST be able to request full field export.

- AC-006: Add tests covering: (a) pagination boundary conditions (page sizes that do not evenly divide total), (b) cache corruption handling, (c) API error/retry handling, and (d) display truncation logic.


## Assumptions

- The Mist API and mistapi client provide a way to iterate or page through listSiteDevices results (either via a `get_all` helper or explicit page/limit params).  
- The environment has a writable data/ directory for CSV and cache files.  
- Interactive terminal supports basic ANSI control sequences but the implementation will provide non-ANSI fallback.  
- Performance targets (SC-001, SC-002, SC-003) are reasonable starting points and can be tuned after the first implementation/benchmark run.


## Test Coverage Requirements

- Unit tests:
  - pagination logic (page boundaries, sorting stability)
  - cache TTL and force-refresh behavior
  - display truncation and curated column selection
  - handling of empty and malformed API responses

- Integration tests (mocked API):
  - small dataset (50 devices) - verify CSV contents and interactive page display
  - medium dataset (2,000 devices) - verify streaming CSV and paging responsiveness
  - large dataset (10,000 devices) - performance measurement (time, peak memory) under CI runner constraints

- Manual/Benchmark tests:
  - run a measured scenario for 10k devices, capture time/memory logs for review and acceptance against success criteria.


## Implementation Tasks (suggested order)

1. Add paginated fetch utility for listSiteDevices (shared helper with clear API and unit tests).
2. Implement streaming CSV writer that accepts an iterator/generator of device records.
3. Add per-site cache with TTL and force-refresh flag; integrate cache into fetch flow.
4. Implement interactive pager UI with curated column set, truncation, and navigation controls.
5. Integrate summary header (counts by type, top models) and deterministic sort key.
6. Add logging and retry/backoff wrapper for API calls.
7. Add unit and integration tests and performance benchmark harness for 10k-device scenario.
8. Document usage notes in the README and add example commands for force-refresh and changing page size.


## Risks & Mitigations

- Risk: Mist API rate limits during large fetches. Mitigation: implement configurable backoff and sequential page throttling; use cache to reduce frequency of full fetches.
- Risk: Terminal UI may be slow for large columns or Unicode. Mitigation: default to curated columns and provide CSV for full data; implement truncation and column wrapping.
- Risk: CI environment differs from production and may not meet performance thresholds. Mitigation: run performance checks in representative environment and document environment used for benchmarks.


## Next Steps / Recommendations

- Implement the fixes in the order above, starting with a minimal safe change (paginated fetch + streaming CSV) and iterating to add caching and paging UI.  
- Add tests and a performance harness to validate SC targets.  
- After implementation, re-run this audit with real org data and adjust performance thresholds as necessary.


---

RETURN: SUCCESS (spec ready for planning)
