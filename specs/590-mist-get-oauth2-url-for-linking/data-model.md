# Phase 1 Data Model: GetOauth2UrlForLinking

**Feature**: 590-mist-get-oauth2-url-for-linking
**Date**: 2026-06-29
**Source**: `documentation/api/self/GET_self_oauth_provider.md` (response schema)

---

## Entities Returned by the Endpoint

The endpoint returns exactly one entity: a `SelfOauthLinkUrl` record describing the
authorization URL for a single OAuth2 provider linked (or available to link) against
the authenticated admin's account. The response is a single JSON object -- not a
list and not paginated.

### Entity: `SelfOauthLinkUrl`

| Field | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `provider` | TEXT (string) | request path param (echoed by MistHelper into the row) | yes | OAuth2 provider slug, e.g. `google`, `microsoft`, `azure`, `okta`. Lowercased before persistence. |
| `authorization_url` | TEXT (string) | response body | yes | Full https URL the operator pastes into a browser to complete provider linkage. Carries a one-time CSRF / state token; do NOT log this value. |
| `linked` | INTEGER (0/1, boolean) | response body | yes | Stored as 0/1 in SQLite (no native BOOLEAN). `1` = provider already linked to current admin; `0` = not yet linked. |
| `forward` | TEXT (string, nullable) | request query param (echoed by MistHelper) | no | Post-link redirect URL the operator requested. `NULL` if not supplied. |
| `fetched_at_utc` | TEXT (ISO-8601 UTC, e.g. `2026-06-29T22:51:22Z`) | MistHelper at flatten time | yes | When the URL was retrieved. Index for staleness checks (URLs are one-shot). |
| `mist_host` | TEXT (string) | MistHelper at flatten time (from `apisession`) | yes | The Mist Cloud regional host (`api.mist.com`, `api.eu.mist.com`, etc.) the URL was fetched from. Disambiguates rows when an operator runs against multiple Mist clouds from the same workstation. |

**Primary key**: `provider` (single-column natural key -- see PK strategy below).

**Foreign keys**: none. The endpoint is account-scoped; there is no `org_id`,
`site_id`, or `device_id` reference in the payload. Cross-table joins are
unnecessary.

**Indexes**:
- `linked` -- filter "all providers already linked" vs "all providers awaiting link".
- `fetched_at_utc` -- spot stale rows (URL is one-shot, anything older than a few
  minutes is unusable).

---

## State Transitions

**N/A -- read-only endpoint.** `getOauth2UrlForLinking` is a pure HTTP GET. The
client (MistHelper) does not transition any server-side state by calling it. The
`linked` field is observed, not mutated. The companion `POST /api/v1/self/oauth/{provider}`
endpoint (see `documentation/api/self/POST_self_oauth_provider.md`) is the one that
mutates the link state, and is out of scope for this spec.

Local row lifecycle inside SQLite:

1. First run for a given `provider` -> `INSERT` new row.
2. Subsequent runs for the same `provider` -> `INSERT OR REPLACE` -- the newer
   `authorization_url` + `fetched_at_utc` overwrite the stale row. `linked` may
   flip from `0` to `1` after the operator completes the browser handshake out of
   band; MistHelper observes the new value on the next fetch.

---

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS self_oauth_link_url (
    provider           TEXT NOT NULL,                -- OAuth2 provider slug (PK)
    authorization_url  TEXT NOT NULL,                -- one-time URL, do not log
    linked             INTEGER NOT NULL DEFAULT 0,   -- 0 = not linked, 1 = linked
    forward            TEXT,                         -- optional post-link redirect
    fetched_at_utc     TEXT NOT NULL,                -- ISO-8601 UTC timestamp
    mist_host          TEXT NOT NULL,                -- regional Mist Cloud host
    PRIMARY KEY (provider)
);

CREATE INDEX IF NOT EXISTS idx_self_oauth_link_url_linked
    ON self_oauth_link_url (linked);

CREATE INDEX IF NOT EXISTS idx_self_oauth_link_url_fetched_at
    ON self_oauth_link_url (fetched_at_utc);
```

`DataExporter.write_with_format_selection()` creates this table on first run if it
does not already exist, using the strategy registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. No manual migration is needed.

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py`
(currently around line 1672):

```python
'getOauth2UrlForLinking': {                          # Mist API operationId (Self OAuth2)
    'type': 'natural_pk',                            # provider is the natural business key
    'primary_key': ['provider'],                     # one row per OAuth2 provider per admin
    'indexes': ['linked', 'fetched_at_utc'],         # filter by link state / detect stale URLs
    'table': 'self_oauth_link_url',                  # explicit table name override
    'description': 'OAuth2 authorization URL for '   # short doc string surfaced in --list-pks
                   'linking an external IdP to the '
                   'currently authenticated Mist admin account.'
}
```

Notes:

- The key in the dict is the camel-case `operationId` exactly as returned by the
  Mist API and used by the `mistapi` SDK. This keeps the dictionary aligned with
  upstream naming and supports operationId-driven lookups in `DataExporter`.
- `INSERT OR REPLACE` semantics are derived automatically by `DataExporter` when
  `type` is `natural_pk` -- no per-endpoint code change required.
- The `description` field is informational only; consumed by the `--list-pks`
  introspection helper if present, harmless if not.

---

## Multi-Backend Mapping

| Backend | Artifact | Key |
|---------|----------|-----|
| CSV | `data/self_oauth_link_url.csv` | `provider` column |
| SQLite | table `self_oauth_link_url` in `data/mist_data.db` | PK `(provider)` |
| ArangoDB | collection `self_oauth_link_url`, `_key` = `provider` | document `_key` |
| Redis | key `mist:self:oauth:link_url:<provider>` -> JSON-encoded row | string key |

All four backends carry the same six-column shape so downstream consumers (Grafana,
ad-hoc scripts, the web UI on port 8055) see a consistent record regardless of which
backend the operator has configured.
