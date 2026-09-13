# Phase 1 Data Model: Site Address Audit from CSV

All entities are Python `@dataclass` types in `src/site/address_audit/models.py`
(one module, one cohesive "models" responsibility). Plus one SQLite table.

Conventions: full-word field names; type hints required; ASCII-only; no logic in
dataclasses beyond trivial defaults (logic lives in the owning classes).

---

## Entity: `AddressRow`

One parsed, sanitized CSV row.

| Field | Type | Notes |
|-------|------|-------|
| `serial` | `str` | CSV col 0; Juniper device serial (numeric string). Required & non-empty (else row skipped at ingest). |
| `model` | `str` | CSV col 1; display only. |
| `address` | `str` | CSV col 2; sanitized (whitespace collapsed, newlines removed). |
| `city` | `str` | CSV col 3. |
| `state` | `str` | CSV col 4; 2-letter code. |
| `zip_code` | `str` | CSV col 5; 5-digit. |

**Validation**: produced only for rows whose `serial` is non-empty after strip.
Malformed rows (empty/non-numeric serial) are skipped and counted, not emitted.

**Produced by**: `CSVAddressIngester.load()`.

---

## Entity: `MatchedSite`

A CSV row resolved (or not) to a Mist site.

| Field | Type | Notes |
|-------|------|-------|
| `site_id` | `str \| None` | Mist site UUID; `None` when unmatched. |
| `site_name` | `str \| None` | Display name; `None` when unmatched. |
| `mist_address` | `dict[str, Any]` | `{"address","city","state","zip"}` from the Mist site record. |
| `snmp_location` | `str \| None` | Populated later by `SNMPLocationEnricher`; `None`/`(none)` when absent. |
| `match_strategy` | `str` | One of `"serial"`, `"fuzzy"`, `"unmatched"`. |
| `match_confidence` | `float` | 1.0 for serial; rapidfuzz score/100 for fuzzy; 0.0 for unmatched. |

**State transitions** (`match_strategy`):
`serial` (inventory hit, site_id present) | `fuzzy` (>=85% address) | `unmatched`
(both miss, OR device found but `site_id` null, OR empty address).

**Produced by**: `SiteMatchingEngine.match_serial()` / `match_fuzzy()`; enriched by
`SNMPLocationEnricher.enrich()`.

---

## Entity: `ResolverResult`

Output of the tiered resolver for one site's best-candidate query.

| Field | Type | Notes |
|-------|------|-------|
| `query` | `str` | The query string built from best candidate (+ optional business name). |
| `canonical_address` | `str \| None` | Resolved/validated address; `None` => `NO_RESULT`. |
| `source` | `str` | One of `"internal"`, `"nominatim"`, `"mist_ui"`, `"cache"`. |
| `confidence` | `float` | 0.0-1.0. |
| `raw_response` | `dict[str, Any]` | Raw tier payload (Nominatim JSON / UI capture); persisted to cache as `raw_json`. |
| `ambiguous` | `bool` | `True` when multiple plausible results (mall scenario) -> drives `AMBIGUOUS`. |

**Produced by**: `AddressResolver.resolve()` (Tiers 1-2 + cache) and optionally
`MistUIGeocoder.geocode_via_ui()` (Tier 3).

---

## Entity: `AuditResult`

The per-row result that drives BOTH the table and the saved CSV. Composes the above.

| Field | Type | Notes |
|-------|------|-------|
| `address_row` | `AddressRow` | Original CSV input. |
| `matched_site` | `MatchedSite` | Match outcome (+ SNMP). |
| `resolver_result` | `ResolverResult \| None` | `None` for `UNMATCHED` rows (no resolution attempted). |
| `issue_type` | `str` | Exactly one of the eight classification states. |
| `suggested_address` | `str` | Best correction to display (full value; truncated only in terminal). |
| `source` | `str` | Display label for the Source column (`Internal` / `Nominatim` / `Mist UI` / `Cache` / `-`). |

**One per CSV row** -- 100% row accountability (SC-002). No row silently dropped.

**Produced by**: `AddressAuditEngine._classify_and_render()`.

---

## Entity: `AuditCounters` (lightweight, inline)

Run summary counters (fresh per run; NOT the existing `AddressComparisonCounters`,
to avoid coupling the two workflows -- see spec AI-hint 10).

| Field | Type | Notes |
|-------|------|-------|
| `total_rows` | `int` | CSV rows emitted by ingester. |
| `parse_failures` | `int` | Rows skipped (empty/non-numeric serial). |
| `by_state` | `dict[str, int]` | Count per classification state (all 8 keys). |
| `cache_hits` | `int` | Resolver cache hits (DEBUG-visible). |
| `external_calls` | `int` | Nominatim + UI calls actually made. |

**Used by**: post-table one-line summary; not persisted.

---

## Classification States (eight, mutually exclusive)

`issue_type` is exactly one of:

| State | Trigger summary |
|-------|-----------------|
| `ADDRESS_MATCH` | Mist address == resolved/validated result (normalized). |
| `MISSING_SUITE` | Resolved candidate (CSV/SNMP/UI) has suite/unit; Mist lacks it. |
| `WRONG_STREET` | Mismatch beyond suite (street number/name differs); Nominatim-driven. |
| `CSV_BETTER` | CSV/SNMP more specific than current Mist address. |
| `MIST_BETTER` | Mist already the most specific source. |
| `AMBIGUOUS` | Resolver returned multiple plausible results (mall). |
| `NO_RESULT` | Internal inconclusive AND Nominatim (and UI if enabled) returned nothing. |
| `UNMATCHED` | No site paired via serial or fuzzy (or empty address / unassigned device). |

---

## SQLite Table: `geocoding_cache`

Additive table in `data/mist_data.db` (`CREATE TABLE IF NOT EXISTS`; `INSERT OR REPLACE`).

```sql
CREATE TABLE IF NOT EXISTS geocoding_cache (
    query_key      TEXT PRIMARY KEY,   -- normalized (lowercased, ws-collapsed) query string
    canonical_addr TEXT,               -- resolved canonical address (nullable => NO_RESULT cached)
    source         TEXT,               -- internal | nominatim | mist_ui
    confidence     REAL,               -- 0.0 - 1.0
    raw_json       TEXT,               -- raw tier payload for audit/debug
    cached_at      TEXT                -- ISO-8601 UTC timestamp
);
```

**Key**: `query_key` = `normalize(query)` -- lowercase + collapse whitespace.
**Lifecycle**: read before any Tier 2/3 call (cache hit -> `source="cache"`, zero
external calls); write/upsert after a successful resolve. Negative results (no
canonical address) MAY be cached to avoid re-querying dead addresses on rerun.

**Migration safety**: purely additive; no changes to existing tables; DB created if
absent. No primary-key-strategy registration needed (this is a local cache, not a
`DataExporter` multi-backend export).

---

## Entity Relationships

```text
AddressRow (1) ---ingested---> CSVAddressIngester
   |
   v  (serial / fuzzy)
MatchedSite (1) <---enriched--- SNMPLocationEnricher (snmp_location)
   |
   v  (best-candidate query)
ResolverResult (0..1) <--- AddressResolver (Tier1 internal / Tier2 Nominatim / cache)
   |                   \--- MistUIGeocoder (Tier3, optional)
   v
AuditResult (1 per AddressRow) ---> ComparisonTableRenderer (terminal, truncated)
                               \---> AddressAuditReporter (CSV, full values)

AuditCounters (1 per run) ---> post-table summary line
geocoding_cache (SQLite) <--> AddressResolver (read-before / upsert-after)
```
