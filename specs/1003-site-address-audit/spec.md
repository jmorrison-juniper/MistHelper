# Feature Specification: Site Address Audit from CSV

**Feature Branch**: `1003-site-address-audit`
**Created**: 2026-06-29
**Status**: Draft
**Input**: User description: "A new read-only menu option that reads a customer-provided CSV, matches rows to Mist sites via serial number, pulls SNMP location vars, geocodes addresses via Mist API, and displays a CLI comparison table."

---

## Problem / Goal *(mandatory)*

### Problem

NOC operators managing large Juniper SSR/gateway deployments receive customer-provided CSV files listing device serial numbers and expected addresses. Today there is no automated way to reconcile that data against Mist Cloud site records. The reconciliation gap causes three classes of operational pain:

1. **E911 inaccuracy** — Mist site addresses may be missing suite/unit numbers, have typos, or be completely wrong; emergency responders could be routed to the wrong location.
2. **SNMP location drift** — Sites often have a richer address in `vars["snmp_location"]` or `snmp_config.location` than in the main Mist site record; there is no tooling to surface that discrepancy.
3. **Manual comparison burden** — Operators currently export site lists and CSV files, then hand-compare rows in a spreadsheet — a slow, error-prone process for organizations with hundreds of sites.

MistHelper already has an `InventoryCSVComparator` class (`src/inventory/csv_comparator.py`) that performs a broader device inventory comparison using Nominatim. The new feature is **complementary, not redundant**: it is narrowly scoped to serial-number-keyed address audit with Mist's own geocoding API as the primary source, SNMP location enrichment, and a pre-classified output table — none of which exist in the current comparator.

### Goal

Deliver a read-only CLI menu option (safe export range 1–59) that:

1. Ingests a tab-delimited customer CSV from `data/` (serial → address)
2. Resolves each row to a Mist site via device serial number lookup, with an address-fuzzy-match fallback
3. Enriches each site record with the `snmp_location` variable and SNMP config location field
4. Geocodes the best available address candidate using Mist's authenticated geocoding API (Google Places via Mist's account), with Nominatim as fallback
5. Classifies each site into one of eight address-state categories
6. Displays a prettytable comparison in the terminal
7. Offers to save the comparison as a CSV to `data/`
8. **Makes zero writes to Mist site records** in this release

### Non-Goals

- Applying geocoded corrections to Mist site records (deferred; `AddressCorrector` stub is wired but inactive)
- Batch geocoding via a paid external API (no new paid dependencies)
- Web portal integration
- Integration with the existing `InventoryCSVComparator` workflow (different CSV schema and scope)
- Handling non-SSR/gateway device types (the CSV schema is SSR-specific; other device types are flagged as SKIPPED)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Full Address Audit: CSV to Comparison Table (Priority: P1)

As a NOC operator, I drop a customer-supplied tab-delimited CSV into `data/` and run the menu option so I can see, in a single terminal table, how each site's Mist address compares to the customer's expected address and the geocoded ground truth.

**Why this priority**: This is the entire value proposition. Without the comparison table, no other story delivers value. It exercises every subsystem end-to-end.

**Independent Test**: Place the four-row sample CSV in `data/`; run the menu option; confirm the table renders with all four rows classified and no unhandled exceptions.

**Acceptance Scenarios**:

1. **Given** a valid CSV at `data/audit_sample.tsv` with four rows matching known device serials, **When** the operator selects the menu option and chooses that file, **Then** the terminal displays a prettytable with columns: Site Name, Current Mist Address, CSV Address, SNMP Location, Suggested Address, Source, Issue Type — one row per CSV entry.
2. **Given** a CSV row whose serial number matches a device assigned to a Mist site, **When** the engine processes that row, **Then** the row's Issue Type is one of the eight defined classification states (not blank, not "ERROR").
3. **Given** a geocoding result from the Mist API that agrees with the Mist site address (normalized), **When** the classifier runs, **Then** the row is classified `ADDRESS_MATCH`.

---

### User Story 2 — Save Comparison Report to CSV (Priority: P2)

As a NOC operator, I want to save the comparison table to a timestamped CSV in `data/` so I can share it with the customer team for review without re-running the tool.

**Why this priority**: The table is ephemeral in the terminal; operators need a persistent artifact for customer-facing review without re-running an API-intensive workflow.

**Independent Test**: After the table renders, select `[1] Save comparison as CSV`; confirm a file matching `data/address_audit_*.csv` is created with a header row and one data row per table entry.

**Acceptance Scenarios**:

1. **Given** a rendered comparison table, **When** the operator selects `[1] Save comparison as CSV`, **Then** a file is written to `data/` with a timestamped filename (e.g., `address_audit_20260629_130930.csv`), a header row matching the table columns, and one data row per audited site.
2. **Given** the operator selects `[q] Quit without saving`, **When** the prompt is answered, **Then** no file is written and the tool exits cleanly.
3. **Given** the `data/` directory does not exist, **When** saving is attempted, **Then** the directory is created with `os.makedirs(exist_ok=True)` and the file is written successfully.

---

### User Story 3 — Unmatched and Fallback Rows (Priority: P3)

As a NOC operator, I need every CSV row accounted for in the output — including rows whose serial number cannot be found in Mist, so I can flag them for manual follow-up.

**Why this priority**: Real CSV files always contain edge cases (retired devices, data entry errors, staging serials). The audit is only trustworthy if unmatched rows are surfaced, not silently dropped.

**Independent Test**: Add a row with a non-existent serial `9999999999` and a row with a correctly spelled address matching an existing site (fuzzy fallback) to the CSV; confirm the first row appears as `UNMATCHED` and the second as a classified row with `Source: Fuzzy`.

**Acceptance Scenarios**:

1. **Given** a CSV row with serial `9999999999` that does not match any Mist device, **When** the engine processes it, **Then** the row appears in the table with Issue Type `UNMATCHED` and no geocoding is attempted.
2. **Given** a CSV row where the serial lookup fails but the normalized address fuzzy-matches a Mist site at ≥ 85 % confidence, **When** the engine processes it, **Then** the row is matched to that site with confidence annotated and classified normally.
3. **Given** a CSV row where the address field contains embedded newlines and leading/trailing whitespace, **When** the ingester parses it, **Then** the address is sanitized (whitespace collapsed, newlines removed) before any comparison.

---

### User Story 4 — Geocoding Cache and Rerun Efficiency (Priority: P3)

As a NOC operator running the audit a second time on the same or updated CSV, I want geocoding results to be served from a local SQLite cache so the rerun is fast and does not exhaust Mist API rate limits.

**Why this priority**: Geocoding 200+ sites live every run is slow and puts load on Mist's Google Places proxy. A cache makes reruns near-instant for unchanged addresses.

**Independent Test**: Run the audit once; note wall-clock time. Run again immediately; confirm the second run completes at least 5× faster with "cache hit" log entries visible at DEBUG level.

**Acceptance Scenarios**:

1. **Given** a geocoding result stored in `mist_data.db`, **When** the same normalized query string is requested again, **Then** the cached result is returned and no HTTP request is made to the geocoding endpoint.
2. **Given** an empty or absent cache, **When** the engine geocodes a site, **Then** the result is written to `mist_data.db` under a table `geocoding_cache` keyed by normalized query string.

---

### Edge Cases

- **CSV with zero matchable rows**: All rows flagged `UNMATCHED`; table renders with all `UNMATCHED` entries; no crash.
- **Empty address column in CSV row**: Row is flagged `UNMATCHED` with reason "empty address"; no geocoding attempted.
- **Mist geocoding returns zero results**: Fallback to Nominatim; if Nominatim also returns zero results, row classified `NO_RESULT`.
- **Multiple CSV files in `data/`**: Operator is prompted to select one by index; `safe_input()` used; invalid input loops gracefully.
- **Single CSV file in `data/`**: Auto-selected without prompting.
- **SNMP location variable absent or empty**: Treated as missing; comparison proceeds with remaining candidates; no error.
- **Mist API rate limit (HTTP 429)**: Back-off with configurable `MIST_GEOCODING_DELAY_SECONDS` (default 0.5 s); retry up to 3 times; log warning on each retry.
- **Device serial in Mist but not assigned to any site**: Row flagged `UNMATCHED` with reason "device unassigned"; serial is found but `site_id` is null.
- **Mall/multi-tenant building (ambiguous geocoding result)**: Multiple business results returned by geocoding API → classified `AMBIGUOUS`; first result's address shown in Suggested Address column.
- **`BUSINESS_NAME` env var absent and operator skips the prompt**: Raw address used as geocoding query (no business name prefix); behavior logged.
- **`rapidfuzz` not installed**: Fuzzy-match fallback disabled gracefully; rows that would have matched via fuzzy only are flagged `UNMATCHED`; a one-time WARNING logged at startup.
- **`scourgify` not installed**: Address normalization uses a regex-based fallback; one-time WARNING logged at startup.
- **Tab-delimited file that accidentally has a header row**: First row's `Col 0` will not parse as a numeric serial; flagged as a parse failure with reason "non-numeric serial"; processing continues on remaining rows.

---

## Module Architecture

New subpackage lives entirely within `src/site/address_audit/`. Each module holds **one class** following MistHelper's "one class per module" convention.

```
src/site/address_audit/
  __init__.py                # Package init; exports AddressAuditEngine for menu registration
  csv_ingester.py            # CSVAddressIngester  — parse & sanitize tab-delimited input
  site_matcher.py            # SiteMatchingEngine  — serial → site_id; fuzzy fallback
  snmp_enricher.py           # SNMPLocationEnricher — pull snmp_location and snmp_config.location
  mist_geocoder.py           # MistGeocodingClient — Mist API + Nominatim geocoding with cache
  audit_engine.py            # AddressAuditEngine  — orchestrator; menu entry point
  comparison_display.py      # ComparisonTableRenderer — prettytable build and print
  audit_reporter.py          # AddressAuditReporter — CSV save to data/
  address_corrector.py       # AddressCorrector    — stub; all methods raise NotImplementedError
```

Two lines added to `MistHelper.py` only:
1. Import of `AddressAuditEngine` (with existing import block for `src.site.*`)
2. Menu entry in the safe export dict (range 1–59, number TBD by developer at implementation time)

No changes to any other existing file except where required by the import.

### Class Responsibility Summary

| Class | Responsibility | Key Methods |
|---|---|---|
| `CSVAddressIngester` | Read & sanitize tab-delimited CSV; yield `AddressRow` dataclass per valid row | `load(path)`, `sanitize_address(raw)` |
| `SiteMatchingEngine` | Resolve serial → `site_id` via Mist inventory; fuzzy fallback on normalized address | `match_serial(serial)`, `match_fuzzy(address, sites)` |
| `SNMPLocationEnricher` | Fetch `vars["snmp_location"]` and `snmp_config.location` for a site | `enrich(site_id)` |
| `MistGeocodingClient` | Query Mist geocoding API; fall back to Nominatim; read/write SQLite cache | `geocode(query)`, `_from_cache(key)`, `_to_cache(key, result)` |
| `AddressAuditEngine` | Orchestrate full audit pipeline; entry point for menu registration | `run(apisession, org_id)` |
| `ComparisonTableRenderer` | Build and print prettytable from list of `AuditResult` dataclasses | `render(results)` |
| `AddressAuditReporter` | Write comparison CSV to `data/` with timestamp filename | `save(results, output_dir)` |
| `AddressCorrector` | Stub for future write-back feature; raises `NotImplementedError` on all methods | `apply_correction(site_id, address)` |

---

## CSV Format & Data Contract

**Encoding**: UTF-8  
**Delimiter**: Tab (`\t`)  
**Headers**: None (zero-indexed columns, no header row)  
**Quoting**: No quoting assumed; embedded quotes treated as literals

| Col | Field | Type | Notes |
|-----|-------|------|-------|
| 0 | Serial | string | Juniper device serial (numeric string, e.g. `2012233588`) |
| 1 | Model | string | Device model (e.g. `SSR130`); stored for display only |
| 2 | Address | string | Street address; may contain embedded whitespace/newlines |
| 3 | City | string | City name |
| 4 | State | string | Two-letter state code (e.g. `FL`) |
| 5 | Zip | string | 5-digit ZIP code |

**Sanitization rules applied by `CSVAddressIngester`**:
- Strip leading/trailing whitespace on all fields
- Replace internal newlines (`\n`, `\r\n`, `\r`) with a single space
- Collapse multiple consecutive spaces to one
- Skip row and log parse failure if `Col 0` (serial) is empty after strip

**Sample rows** (tab-delimited):
```
2012233588	SSR130	5550 N Military Traill Unit 200	Boca Raton	FL	33431
2012234081	SSR130	6000 Glades Rd Suite 1019A	Boca Raton	FL	33431
2017233102	SSR130	4103 14th St W Suite 101	Bradenton	FL	34205
2012233133	SSR130	459 Brandon Town Center Mall Suite 330	Brandon	FL	33511
```

---

## Address Classification States

After geocoding, each audited site is assigned exactly one of eight mutually exclusive states:

| State | Meaning | Action needed |
|---|---|---|
| `ADDRESS_MATCH` | Mist address and geocoded result agree (normalized) | None |
| `MISSING_SUITE` | Geocoded result includes suite/unit; Mist address does not | Operator review |
| `WRONG_STREET` | Mismatch beyond suite level (different street number or name) | Operator review |
| `CSV_BETTER` | CSV or SNMP address is more specific than the current Mist address | Operator review |
| `MIST_BETTER` | Mist address is already the most specific source | None |
| `AMBIGUOUS` | Geocoding returned multiple plausible results (e.g. mall scenario) | Manual lookup |
| `NO_RESULT` | Both Mist geocoding and Nominatim returned no usable result | Manual lookup |
| `UNMATCHED` | No CSV row could be paired to a Mist site via serial or fuzzy match | Manual follow-up |

---

## Interfaces & Behavior

### Menu Registration

Two registrations in `MistHelper.py`:

```python
# Safe export entry (number TBD, must be in range 1-59 and not already occupied):
"<N>": (AddressAuditEngine.run, "Audit site addresses from CSV -- compare Mist vs. customer data vs. web"),

# Destructive/write-back entry -- DEFERRED, do NOT wire; stub only:
# "<M>": (AddressAuditEngine.apply_corrections, "Apply geocoded address corrections to Mist sites"),
```

> **Rule**: The write-back menu entry must NOT appear in this release. The `AddressCorrector` class exists as a stub with `NotImplementedError` methods; it is not registered.

### Geocoding Priority

1. **Mist geocoding API** — `GET /api/v1/utils/geocoding?q=<query>` using the existing authenticated `apisession`; same endpoint as the Mist UI address autocomplete.  
2. **Nominatim** — `https://nominatim.openstreetmap.org/search?q=<query>&format=json&limit=3`; rate-limited to ≤ 1 request/second per ToS.  
3. **Cache** — SQLite table `geocoding_cache` in `mist_data.db`; checked before either live API call.

**Query construction**:
- Best candidate = `snmp_location` → `csv_address` → `mist_address` (first non-empty, in that priority order)
- Full query = `"{BUSINESS_NAME} {best_candidate}"` if `BUSINESS_NAME` is set; otherwise raw best candidate
- Query is normalized (lowercased, whitespace collapsed) before cache lookup

**Business name resolution**:
1. Read `BUSINESS_NAME` from `.env`
2. If absent/empty: prompt operator with `safe_input("Enter business name (or press Enter to skip): ")`
3. If operator presses Enter: geocode with address only (no business name prefix)

### SNMP Location Pull

For each matched Mist site, pull two fields via the existing `apisession`:

```
site["vars"]["snmp_location"]        -- custom variable key
site_settings["snmp_config"]["location"]  -- standard SNMP location OID
```

Use whichever is non-empty; if both are non-empty, prefer `snmp_config.location` as it is more authoritative (set by NOC, not provisioning). If neither is set, SNMP Location column shows `(none)`.

### CLI Post-Table Prompt

```
[1] Save comparison as CSV to data/ for review
[q] Quit without saving
```

Implemented in `ComparisonTableRenderer`; input via `safe_input()`. Invalid input loops with a one-line error message. No other options in this release.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST be reachable as a numbered menu option in the safe export range (1–59) in `MistHelper.py` via `AddressAuditEngine.run`.
- **FR-002**: `CSVAddressIngester` MUST accept tab-delimited files with zero header rows; MUST sanitize address fields (strip whitespace, collapse newlines); MUST skip and log rows where `Col 0` (serial) is empty after sanitization.
- **FR-003**: When multiple CSV files exist in `data/`, the operator MUST be prompted to select one by index using `safe_input()`; when exactly one CSV exists, it MUST be auto-selected.
- **FR-004**: `SiteMatchingEngine` MUST first attempt a serial number lookup via the Mist device inventory API; on miss, MUST attempt a rapidfuzz address fuzzy-match at threshold ≥ 85 % against all org sites; on miss of both strategies, the row MUST be classified `UNMATCHED`.
- **FR-005**: `SNMPLocationEnricher` MUST read both `vars["snmp_location"]` and `snmp_config.location` from the site record; MUST return the more authoritative non-empty value; MUST not raise an exception if either field is absent.
- **FR-006**: `MistGeocodingClient` MUST query `GET /api/v1/utils/geocoding?q=...` using the authenticated `apisession`; MUST fall back to Nominatim if the Mist API returns no results or raises an exception; MUST apply a configurable per-request delay (`MIST_GEOCODING_DELAY_SECONDS`, default 0.5 s) between Mist API calls.
- **FR-007**: Geocoding results MUST be cached in an SQLite table `geocoding_cache` within `mist_data.db`; a cache-hit MUST skip all live API calls for that query string.
- **FR-008**: `AddressAuditEngine` MUST classify each audited row into exactly one of the eight defined states (see Address Classification States section).
- **FR-009**: `ComparisonTableRenderer` MUST render a prettytable with columns: Site Name, Current Mist Address, CSV Address, SNMP Location, Suggested Address, Source, Issue Type.
- **FR-010**: After rendering, the operator MUST be offered `[1] Save CSV` and `[q] Quit`; selecting `[1]` MUST write a timestamped CSV to `data/` via `AddressAuditReporter`; no other choices exist in this release.
- **FR-011**: `AddressCorrector` MUST exist as a stub class whose methods raise `NotImplementedError`; it MUST NOT be registered in the menu.
- **FR-012**: The feature MUST make zero writes to any Mist site record.
- **FR-013**: All geocoding operations MUST be guarded by a `try/except` block; any single-row geocoding failure MUST be logged and the row classified `NO_RESULT`; the audit MUST continue for remaining rows.
- **FR-014**: Nominatim requests MUST be rate-limited to ≤ 1 request/second.

### Coding-Standard Requirements (NON-NEGOTIABLE — from `agents.md` / `copilot-instructions.md`)

- **CR-001 Inline comments**: Every executable line in every new module MUST carry an inline comment explaining *why*, not just *what*.
- **CR-002 Action logging**: `logging.info()` MUST appear before each meaningful operation (e.g., "Starting CSV ingestion", "Querying Mist geocoding API for site {name}"); `logging.debug()` MUST appear after with a result summary; ASCII-only (no Unicode/emoji in log strings).
- **CR-003 safe_input**: Every `input()` call MUST be replaced with `InputUtils.safe_input(prompt, context=<tag>)`; no bare `input()` calls in any new file.
- **CR-004 Class-based**: No standalone functions outside a class body in any new module; all logic lives inside the class defined in that module.
- **CR-005 5-Item Rule**: No new method exceeds 5 parameters / 25 lines / 5 nested blocks; orchestration that needs more state MUST be split into smaller private methods.
- **CR-006 Paths**: All file paths constructed with `os.path.join()` or `pathlib.Path`; no hardcoded separators.
- **CR-007 Import guard**: `rapidfuzz` and `scourgify` MUST be imported via `GlobalImportManager`'s existing optional-import pattern; code MUST degrade gracefully if either is absent.

### Key Entities

- **`AddressRow`** — Dataclass representing one parsed CSV row: `serial`, `model`, `address`, `city`, `state`, `zip_code`.
- **`MatchedSite`** — Dataclass representing a resolved Mist site: `site_id`, `site_name`, `mist_address` (dict), `snmp_location` (str or None), `match_strategy` (serial | fuzzy | unmatched), `match_confidence` (float).
- **`GeocodingResult`** — Dataclass: `query`, `canonical_address`, `source` (mist_geo | nominatim | cache), `raw_response` (dict).
- **`AuditResult`** — Dataclass combining all above plus `issue_type` (str), `suggested_address` (str), and `source` (str); one per CSV row; drives both table and CSV output.
- **`geocoding_cache` table** — SQLite: `query_key TEXT PRIMARY KEY, canonical_address TEXT, source TEXT, cached_at TEXT`.

---

## Security & Secrets

- **Mist API session**: Passed through the existing `apisession` parameter already established by the menu framework; no new credential storage.
- **`BUSINESS_NAME` in `.env`**: Read via `python-dotenv`; treated as non-secret configuration (it is a public business name). No logging of `.env` file contents.
- **Nominatim ToS compliance**: The User-Agent header MUST identify MistHelper (e.g., `User-Agent: MistHelper/1.0 (address-audit)`); per Nominatim policy, no more than 1 request/second; no scraping.
- **No new API keys**: The Mist geocoding endpoint uses the existing authenticated session; no additional tokens or secrets required.
- **SQLite cache (`mist_data.db`)**: Cache stores geocoded addresses (public data) and query strings (addresses); no credentials or PII beyond what is already present in the DB. Cache is local to the deployment environment and not transmitted.
- **Operator-entered business name**: Not stored persistently (runtime-only); not logged at INFO level.
- **SSL verification**: Follows the existing `skip_ssl_verify` flag pattern already present in `InventoryCSVComparator`; not bypassed by default.

---

## Constraints / Performance

- **No new required dependencies**: All production dependencies (`requests`, `prettytable`, `python-dotenv`, `mistapi`) are already in `requirements.txt`. `rapidfuzz` and `scourgify` are optional with graceful fallbacks.
- **Geocoding throughput**: Mist API default delay of 0.5 s/request gives ≈ 120 sites/minute live; with a warm cache, a 500-site audit should complete in < 30 seconds.
- **SQLite cache write**: Must use `INSERT OR REPLACE` (upsert) to avoid duplicate-key errors on reruns.
- **Memory**: `AddressRow`, `MatchedSite`, `GeocodingResult`, `AuditResult` dataclasses are all allocated in memory for the duration of the run; for typical deployments (< 2000 rows), peak memory is negligible.
- **Rate limiting (Nominatim)**: `time.sleep(1.0)` between each Nominatim call; configurable via `NOMINATIM_DELAY_SECONDS` in `.env` (default 1.0; minimum 1.0 enforced).
- **Mist geocoding delay**: Configurable via `MIST_GEOCODING_DELAY_SECONDS` in `.env` (default 0.5; minimum 0.0).
- **Retry on HTTP 429**: Back-off up to 3 retries with 2× delay multiplier; log WARNING on each retry; after 3 retries, classify the row `NO_RESULT` and continue.
- **prettytable max width**: Truncate the Suggested Address and SNMP Location columns to 40 characters for terminal readability; full values written to CSV output.

---

## Test Plan *(mandatory)*

Local workaround (corrupted venv — dash plugin autoload only):
```
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; & ".venv\Scripts\python.exe" -m pytest <files> -o addopts="" -q
```

### Unit Tests (new, in `tests/unit/site/address_audit/`)

1. **`test_csv_ingester.py`**
   - Valid 4-row tab CSV parses to 4 `AddressRow` dataclasses
   - Row with embedded newline in address field is sanitized correctly
   - Row with empty serial is skipped; parse failure count = 1
   - Row with trailing/leading whitespace is trimmed on all fields
   - File-not-found raises a controlled exception (logged, not crash)

2. **`test_site_matcher.py`**
   - Serial found in mock Mist inventory → returns `MatchedSite` with `match_strategy = "serial"`
   - Serial not found → fuzzy fallback called with site list
   - Fuzzy match at ≥ 85 % → returns `MatchedSite` with `match_strategy = "fuzzy"`
   - Fuzzy match at < 85 % → returns `MatchedSite` with `match_strategy = "unmatched"`
   - `rapidfuzz` absent → fuzzy fallback returns unmatched; one WARNING logged

3. **`test_snmp_enricher.py`**
   - Site with both `vars["snmp_location"]` and `snmp_config.location` → returns `snmp_config.location`
   - Site with only `vars["snmp_location"]` → returns that value
   - Site with neither → returns `None`; no exception

4. **`test_mist_geocoder.py`**
   - Query with cache hit → returns cached result; zero HTTP calls made
   - Query with cache miss → calls Mist API; result written to cache
   - Mist API returns empty → Nominatim called; result returned and cached
   - Both APIs return empty → returns `GeocodingResult` with `canonical_address = None`
   - HTTP 429 from Mist API → retried up to 3×; classified `NO_RESULT` after 3 failures
   - Nominatim delay of 1 s enforced (monkeypatched `time.sleep` call count ≥ 1)

5. **`test_audit_engine.py`** (integration-style with mocked dependencies)
   - All 8 classification states reachable via distinct input combinations
   - Zero-row CSV → empty `AuditResult` list; no exception
   - All-unmatched CSV → table rendered with all `UNMATCHED` rows

6. **`test_comparison_display.py`**
   - `render()` returns a non-empty string (prettytable output)
   - SNMP Location column truncated at 40 characters when > 40 chars long
   - `[1]` and `[q]` options presented after table

7. **`test_audit_reporter.py`**
   - `save()` writes CSV to a temp dir with expected header row
   - Filename contains a timestamp in `YYYYMMDD_HHMMSS` format
   - All 8 classification states appear in written CSV when present in results

### Quality Gates

```
python -m py_compile MistHelper.py          # Must pass
ruff check src/site/address_audit/          # Must pass clean
black --check src/site/address_audit/       # Must pass clean
```

---

## Migration / Compatibility

- **No database schema changes to existing tables**: The new `geocoding_cache` table is additive; `mist_data.db` is created if absent; `CREATE TABLE IF NOT EXISTS` used.
- **No changes to existing `InventoryCSVComparator`**: The new feature does not touch `src/inventory/csv_comparator.py` or `AddressComparisonCounters`.
- **No menu number conflicts**: The developer assigns an unoccupied number in range 1–59 at implementation time; the menu framework enforces uniqueness via a dict key collision that would cause an immediate startup error if a conflict existed.
- **`MistHelper.py` changes are additive only**: One import line; one menu entry; no modifications to existing code paths.
- **Backward compatibility**: Operators who never use the new menu option are unaffected.
- **Python 3.13+ required**: Follows the project minimum; no 3.12-or-below workarounds needed.

---

## Acceptance Criteria *(mandatory)*

- [ ] Drop a tab-delimited CSV (no headers) into `data/` and run the menu option; if multiple CSV files exist, operator is prompted to select one using `safe_input()`.
- [ ] Script looks up each serial number in Mist device inventory; rows with matching serials show `match_strategy = serial` in logs.
- [ ] Script pulls `snmp_location` and `snmp_config.location` for each matched site; non-empty values appear in the SNMP Location column.
- [ ] Script calls Mist geocoding API (`/api/v1/utils/geocoding`) with business name + best address candidate; falls back to Nominatim if Mist returns no result.
- [ ] Script displays comparison table in terminal using prettytable; all seven columns present; every CSV row has an entry with exactly one of the eight Issue Type classifications.
- [ ] Operator can save results as CSV to `data/` with a timestamped filename; file contains a header row matching the table columns.
- [ ] No writes to any Mist site record occur in any code path of this release.
- [ ] Geocoding results are cached in `mist_data.db`; a second run on the same CSV retrieves from cache (zero new geocoding API calls for unchanged addresses, visible in DEBUG logs).
- [ ] Graceful fallback when SNMP var is missing (row processes normally), geocoding fails (row classified `NO_RESULT`), or CSV row is malformed (row skipped with logged parse failure).
- [ ] `python -m py_compile MistHelper.py`, `ruff check`, and `black --check` all pass after the feature is added.
- [ ] Every executable line in every new file carries an inline comment; `logging.info()` before every meaningful operation; `logging.debug()` after with a result summary; ASCII-only log strings.
- [ ] No method in any new class exceeds 5 parameters, 25 lines, or 5 nested blocks.
- [ ] All new `input()` calls use `InputUtils.safe_input()`; no bare `input()` calls.

---

## Implementation Notes (AI Hints)

> These notes are for the AI/developer implementing the feature. They do not define requirements — they describe the expected implementation path.

1. **Start with dataclasses first** (`AddressRow`, `MatchedSite`, `GeocodingResult`, `AuditResult` in a new `src/site/address_audit/models.py`). Every class that produces or consumes these types can then be written with clear type hints.

2. **Reuse `InputUtils.safe_input()`** from `src/utils/input_utils.py`; do not create new input wrappers.

3. **`MistGeocodingClient` cache table DDL** (place in `_ensure_cache_table(conn)`):
   ```sql
   CREATE TABLE IF NOT EXISTS geocoding_cache (
       query_key     TEXT PRIMARY KEY,
       canonical_addr TEXT,
       source        TEXT,
       raw_json      TEXT,
       cached_at     TEXT
   );
   ```
   Use `os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "mist_data.db")` resolved via `os.path.realpath()` to locate the DB regardless of CWD.

4. **Mist geocoding API call** (existing `apisession` already has auth headers):
   ```python
   response = apisession.get("/api/v1/utils/geocoding", params={"q": query})
   # response is a requests.Response; parse response.json()
   ```
   Inspect `mistapi` source (`mistapi/_api/v1/utils/geocoding.py`) for the exact call signature — it may be `mistapi.api.v1.utils.geocoding.getGeocode(apisession, q=query)`.

5. **Fuzzy match pattern**: Load all site names + concatenated addresses into a list; use `rapidfuzz.process.extractOne(query, choices, score_cutoff=85)`. The match threshold of 85 % is a constant in `SiteMatchingEngine`, overridable via `.env` key `FUZZY_MATCH_THRESHOLD`.

6. **Classification logic** should live in a private `_classify(mist_addr, csv_addr, snmp_loc, geo_result)` method on `AddressAuditEngine`. Keep it ≤ 25 lines by delegating to helpers (`_addresses_agree()`, `_has_suite_discrepancy()`, etc.).

7. **prettytable column widths**: Use `table.max_width = 40` per column for SNMP Location and Suggested Address. Full values should still be in the underlying `AuditResult` passed to `AddressAuditReporter`.

8. **`AddressCorrector` stub pattern** — follow the same pattern as other deferred features in the codebase:
   ```python
   class AddressCorrector:
       """Future: apply geocoded address corrections to Mist site records. Not wired in v1."""
       def apply_correction(self, site_id: str, address: dict) -> None:
           """Stub — raises NotImplementedError until feature flag is enabled."""
           raise NotImplementedError("Address write-back is not enabled in this release.")
   ```

9. **5-Item Rule split points** to watch for:
   - `AddressAuditEngine.run()` will naturally want > 25 lines — split into `_load_csv()`, `_match_sites()`, `_enrich_and_geocode()`, `_classify_and_render()` private methods, each called from `run()`.
   - `MistGeocodingClient.geocode()` — split into `_query_mist()`, `_query_nominatim()`, `_build_query_key()`.

10. **Existing `AddressComparisonCounters`** at `src/inventory/csv_comparator.py` should NOT be reused for this feature; create fresh counters inline in `AddressAuditEngine` or a lightweight dataclass to avoid coupling the two workflows.

---

## UI Behavior

### File Selection Prompt (multiple CSVs in `data/`)

```
Available CSV files in data/:
  [1] audit_sites_june.tsv
  [2] addresses_boca_raton.tsv
  [3] customer_export_20260628.tsv

Select file number: _
```

- Invalid input (non-integer, out-of-range) re-prompts with: `"Invalid selection. Please enter a number between 1 and {n}: "`
- Implemented with `safe_input()` in a loop

### Business Name Prompt (if `BUSINESS_NAME` not in `.env`)

```
Enter business name for geocoding queries (e.g. "Starbucks"), or press Enter to skip: _
```

- Shows once per run; result held in memory only
- If skipped, address is geocoded without a business name prefix

### Progress Indicator

- `tqdm` progress bar (`tqdm` already present in requirements) for the geocoding loop: `"Geocoding sites: 45/200 [00:22, 2.1 site/s]"`
- Suppress bar when running in non-interactive mode (piped stdout)

### Comparison Table (prettytable)

```
+----------------------+------------------------+------------------------+----------------+---------------------------+----------+--------------+
| Site Name            | Current Mist Address   | CSV Address            | SNMP Location  | Suggested Address          | Source   | Issue Type   |
+----------------------+------------------------+------------------------+----------------+---------------------------+----------+--------------+
| Boca Raton - Unit 20 | 5550 N Military Trl    | 5550 N Military Traill | Suite 200 (... | 5550 N Military Trail U... | Mist Geo | MISSING_SUIT |
| Boca Raton - Glades  | 6000 Glades Rd         | 6000 Glades Rd Ste 101 | (none)         | 6000 Glades Rd Suite 101... | Mist Geo | CSV_BETTER   |
| Bradenton - 14th St  | 4103 14th St W         | 4103 14th St W Ste 101 | (none)         | 4103 14th St W Suite 101... | Mist Geo | MISSING_SUIT |
| Brandon - Town Ctr   | 459 Brandon Town Center| 459 Brandon Town Ctr M | Suite 330 (... | 459 Brandon Town Center M.. | Nominatim| ADDRESS_MATC |
+----------------------+------------------------+------------------------+----------------+---------------------------+----------+--------------+
```

- Address columns truncated to 40 chars in terminal; full value in saved CSV
- Classification abbreviations in terminal acceptable (e.g. `MISSING_SUIT`); full value in saved CSV

### Post-Table Prompt

```
Audit complete. 4 sites processed: 0 ADDRESS_MATCH, 2 MISSING_SUITE, 1 CSV_BETTER, 1 ADDRESS_MATCH, 0 UNMATCHED.

[1] Save comparison as CSV to data/ for review
[q] Quit without saving

Choice: _
```

- One-line summary precedes the prompt
- Save confirmation: `"Saved to data/address_audit_20260629_130930.csv"`
- Exit confirmation: `"No file saved. Exiting address audit."`

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators complete an address audit of up to 500 sites in under 15 minutes on a warm geocoding cache (from running the audit once to producing a saved CSV).
- **SC-002**: 100 % of CSV rows appear in the output table — no rows silently dropped; every row has exactly one non-blank Issue Type.
- **SC-003**: On a second identical run, geocoding API calls are zero (all cache hits); rerun completes in under 30 seconds for a 200-row CSV.
- **SC-004**: Zero Mist site records are modified during any run of this feature.
- **SC-005**: All quality gates (`py_compile`, `ruff`, `black`) pass after the feature is merged.
- **SC-006**: Graceful degradation confirmed: if `rapidfuzz` is absent, the tool completes the audit (with unmatched fuzzy rows) rather than crashing.

---

## Assumptions

- The Mist API endpoint `GET /api/v1/utils/geocoding?q=...` is available in the authenticated session with the same organization scope as other mistapi calls; no additional OAuth scope is required.
- `mist_data.db` may already exist with other tables from prior MistHelper operations; `CREATE TABLE IF NOT EXISTS` handles this safely.
- The customer CSV contains only SSR/gateway device serials; non-gateway serials are not an expected input but will be processed through the same pipeline (serial lookup will either match or miss).
- Tab-delimited files use `.tsv` or `.csv` extension; the file-picker in `data/` filters for both.
- The `data/` directory is always present or can be created; no elevated permissions are required on the deployment host.
- The operator runs the tool in a terminal wide enough to display prettytable output (minimum 120 columns); no fallback table format is required for v1.
- `python-dotenv` `load_dotenv()` is already called at MistHelper startup; no duplicate call needed in the new module.
- The Mist geocoding API response JSON follows the same schema as the Mist UI autocomplete: `{ "results": [{ "formatted_address": "...", ... }] }` — to be confirmed against `mistapi` source before implementation.
