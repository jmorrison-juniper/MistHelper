# Contract: `geocoding_cache` SQLite Table

Additive cache table in the canonical `data/mist_data.db`. Read before any Tier 2/3
external call; upserted after a resolve. No existing tables touched.

## DDL (idempotent)

```sql
CREATE TABLE IF NOT EXISTS geocoding_cache (
    query_key      TEXT PRIMARY KEY,   -- normalize(query): lowercase + whitespace-collapsed
    canonical_addr TEXT,               -- resolved address; NULL allowed (negative cache => NO_RESULT)
    source         TEXT,               -- internal | nominatim | mist_ui
    confidence     REAL,               -- 0.0 .. 1.0
    raw_json       TEXT,               -- raw tier payload (JSON string) for debug/audit
    cached_at      TEXT                -- ISO-8601 UTC timestamp
);
```

## Operations

| Op | SQL shape | When |
|----|-----------|------|
| Ensure | `CREATE TABLE IF NOT EXISTS ...` | once per run, before first lookup |
| Read | `SELECT canonical_addr, source, confidence, raw_json FROM geocoding_cache WHERE query_key = ?` | before Tier 2/3 |
| Upsert | `INSERT OR REPLACE INTO geocoding_cache (query_key, canonical_addr, source, confidence, raw_json, cached_at) VALUES (?,?,?,?,?,?)` | after resolve |

## Rules

- **Key** = `query_key` = lowercase + collapse-whitespace of the constructed query
  (`"{BUSINESS_NAME} {best_candidate}"` or raw best candidate).
- **Cache hit** -> return `ResolverResult(source="cache")`; make ZERO external
  calls (FR-007, SC-003); log `debug "cache hit for %s"`.
- **Upsert** (`INSERT OR REPLACE`) -> no duplicate-key errors on rerun.
- **Negative caching**: a `NULL canonical_addr` row MAY be stored to skip re-querying
  dead addresses; treated as a hit that yields `NO_RESULT`.
- **DB path**: resolve to `data/mist_data.db` (constitution-fixed location), built
  with `os.path.join`. Single path constant in `AddressResolver`.
- **Security**: stores only public addresses + query strings; no credentials/PII
  beyond what `mist_data.db` already holds; local-only, never transmitted.
- **Migration**: purely additive; `mist_data.db` created if absent. No
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry needed (local cache, not a multi-backend export).
