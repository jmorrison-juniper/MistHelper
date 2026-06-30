# Phase 1 Data Model: getOauth2UrlForLinking

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from `documentation/api/self/GET_self_oauth_provider.md`
(200 OK body).

## Entities

The endpoint returns a single two-field JSON object describing the OAuth2 linking
URL for a specific provider against the currently authenticated admin account.
MistHelper persists this as one logical entity in one output table.

### Entity 1: `SelfOauthLinkUrl`

One row per (authenticated account, OAuth2 provider).

| Field               | Type    | Source                  | PK? | FK? | Notes |
|---------------------|---------|-------------------------|-----|-----|-------|
| `account_email`     | TEXT    | MistHelper getSelf cache | YES | --  | Email of the authenticated admin account. Stable per `.env` token. |
| `provider`          | TEXT    | User prompt / path param | YES | --  | OAuth2 provider name (e.g. `google`, `azure`). Lower-cased, regex-validated `^[a-z0-9_-]{1,32}$`. |
| `authorization_url` | TEXT    | API `authorization_url`  | --  | --  | HTTPS URL the operator's browser must visit. Contains a short-lived state nonce; never logged at INFO. |
| `linked`            | INTEGER | API `linked`             | --  | --  | `1` when the provider is already linked, `0` otherwise. Stored as INTEGER for SQLite portability. |
| `forward`           | TEXT    | User prompt (optional)   | --  | --  | Forward URL passed as the `forward` query parameter, or empty string when omitted. |
| `polled_at_utc`     | TEXT    | MistHelper clock         | --  | --  | ISO8601 UTC timestamp of the poll, for audit. Not part of the PK so repeated polls upsert in place. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *link* on the Mist side transitions
through `not linked -> link initiated -> linked` once the operator visits the URL in a
browser and completes the OAuth2 dance, but MistHelper does not drive or model those
transitions; it merely captures snapshots. Each poll overwrites the prior snapshot for
the same `(account_email, provider)` tuple via SQLite `INSERT OR REPLACE`. The
`linked` column reflects whichever value the API returned at the last poll; the
`authorization_url` likewise rotates on every poll because the state nonce changes.

## SQLite DDL

```sql
-- One row per (authenticated account, OAuth2 provider).
CREATE TABLE IF NOT EXISTS self_oauth_link_urls (
    account_email      TEXT     NOT NULL,
    provider           TEXT     NOT NULL,
    authorization_url  TEXT,
    linked             INTEGER,
    forward            TEXT,
    polled_at_utc      TEXT,
    PRIMARY KEY (account_email, provider)
);

CREATE INDEX IF NOT EXISTS idx_self_oauth_link_provider
    ON self_oauth_link_urls (provider);

CREATE INDEX IF NOT EXISTS idx_self_oauth_link_linked
    ON self_oauth_link_urls (linked);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (around line 3019, single insert in the dict literal,
no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per (authenticated account, OAuth2 provider).
    # The authorization_url rotates on every call (state nonce), so re-running
    # the menu item upserts the freshest URL in place rather than appending.
    'getOauth2UrlForLinking': {                                                     # operationId from OpenAPI
        'type': 'natural_pk',                                                       # PK is the natural business key
        'primary_key': ['account_email', 'provider'],                               # one row per account+provider
        'indexes': ['provider', 'linked'],                                          # fast filter by provider / linked-state
        'table': 'self_oauth_link_urls',                                            # target SQLite/ArangoDB table
    },
}
```

`account_email` is injected by MistHelper before the upsert by reading the cached
`getSelf` payload that is already loaded at startup -- the Mist API does not return
`account_email` in this endpoint's body but MistHelper always knows which admin token
it is using.
