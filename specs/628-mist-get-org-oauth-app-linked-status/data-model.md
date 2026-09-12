# Phase 1 Data Model: getOrgOauthAppLinkedStatus

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_setting_app_name_link_accounts.md` (200 OK
body).

## Entities

The endpoint returns a single JSON object describing the OAuth linking state of a
third-party integration for one organization. MistHelper splits this into two
logical entities for clean multi-backend persistence.

### Entity 1: `OauthAppLinkSummary`

One row per (org, app_name) pairing. Captures the top-level linking flag and the
authorization endpoint.

| Field                | Type    | Source                | PK? | FK?           | Notes |
|----------------------|---------|-----------------------|-----|---------------|-------|
| `org_id`             | TEXT    | MistHelper context    | YES | sites.org_id  | UUID supplied by prompt / `.env`. |
| `app_name`           | TEXT    | MistHelper context    | YES | --            | Lowercase, `^[a-z0-9_-]{2,32}$`. |
| `linked`             | INTEGER | API `linked`          | --  | --            | Boolean stored as 0/1 for cross-backend portability. |
| `authorization_url`  | TEXT    | API `authorization_url` | -- | --           | Contains a redirect nonce -- written to SQLite/Arango only, omitted from CSV. |
| `accounts_count`     | INTEGER | len(API `accounts`)   | --  | --            | Convenience count for quick filtering. |
| `polled_at_utc`      | TEXT    | MistHelper clock      | --  | --            | ISO8601 UTC timestamp of the poll, audit trail. |

### Entity 2: `OauthAppLinkAccount`

Zero-or-more rows per (org, app_name). Source: each element of the API `accounts`
array. Fields are the union of the schema properties across all supported
integrations (Prisma, Zoom, ZDX, JAMF, Crowdstrike, SentinelOne, VMWare, Zscaler);
any absent field for a given integration is stored as `NULL`.

| Field                    | Type    | Source                              | PK? | FK?                                             | Notes |
|--------------------------|---------|-------------------------------------|-----|-------------------------------------------------|-------|
| `org_id`                 | TEXT    | MistHelper context                  | YES | org_oauth_app_link_summary.org_id               | UUID. |
| `app_name`               | TEXT    | MistHelper context                  | YES | org_oauth_app_link_summary.app_name             | Joins to summary. |
| `account_id`             | TEXT    | API `accounts[].account_id`         | YES | --                                              | Per-account unique id. |
| `name`                   | TEXT    | API `accounts[].name`               | --  | --                                              | Display name. |
| `company`                | TEXT    | API `accounts[].company`            | --  | --                                              | Subscribed company name. |
| `cloud_name`             | TEXT    | API `accounts[].cloud_name`         | --  | --                                              | e.g. `Tapi.sase.paloaltonetworks.com`. |
| `client_id`              | TEXT    | API `accounts[].client_id`          | --  | --                                              | OAuth client id (identifier, not secret). |
| `instance_url`           | TEXT    | API `accounts[].instance_url`       | --  | --                                              | Customer instance URL. |
| `username`               | TEXT    | API `accounts[].username`           | --  | --                                              | Customer account username. |
| `last_status`            | TEXT    | API `accounts[].last_status`        | --  | --                                              | e.g. `failed`, `success`. |
| `last_sync`              | INTEGER | API `accounts[].last_sync`          | --  | --                                              | Epoch millis. |
| `linked_by`              | TEXT    | API `accounts[].linked_by`          | --  | --                                              | First name of the user who linked. |
| `linked_timestamp`       | REAL    | API `accounts[].linked_timestamp`   | --  | --                                              | Epoch millis. |
| `error`                  | TEXT    | API `accounts[].error`              | --  | --                                              | Last-error string. |
| `errors_joined`          | TEXT    | join(API `accounts[].errors`, `\|`) | --  | --                                              | Pipe-joined error list for flat storage. |
| `enable_probe`           | INTEGER | API `accounts[].enable_probe`       | --  | --                                              | Prisma only. Bool 0/1. |
| `auto_probe_subnet`      | TEXT    | API `accounts[].auto_probe_subnet`  | --  | --                                              | Prisma only. |
| `region`                 | TEXT    | API `accounts[].region`             | --  | --                                              | Prisma only. |
| `regions_json`           | TEXT    | json(API `accounts[].regions`)      | --  | --                                              | Prisma only. Full nested regions object as JSON text. |
| `service_account_name`   | TEXT    | API `accounts[].service_account_name` | -- | --                                             | Prisma only. |
| `service_connections_json` | TEXT  | json(API `accounts[].service_connections`) | -- | --                                        | Prisma only. Nested map as JSON text. |
| `tsg_id`                 | TEXT    | API `accounts[].tsg_id`             | --  | --                                              | Prisma only. Tenant Service Group id. |
| `smartgroup_name`        | TEXT    | API `accounts[].smartgroup_name`    | --  | --                                              | Compliance smart group. |
| `key_id`                 | TEXT    | API `accounts[].key_id`             | --  | --                                              | ZDX only. |
| `zdx_org_id`             | TEXT    | API `accounts[].zdx_org_id`         | --  | --                                              | ZDX only. |
| `max_daily_api_requests` | INTEGER | API `accounts[].max_daily_api_requests` | -- | --                                          | Zoom only. Daily API quota. |
| `webhook_enabled`        | INTEGER | API `accounts[].webhook_enabled`    | --  | --                                              | Crowdstrike/JAMF/SentinelOne/VMWare. Bool 0/1. |
| `webhook_auth_type`      | TEXT    | API `accounts[].webhook_auth_type`  | --  | --                                              | e.g. `Basic`, `Bearer`. |
| `webhook_url`            | TEXT    | API `accounts[].webhook_url`        | --  | --                                              | Webhook receiver URL. |
| `webhook_username`       | TEXT    | API `accounts[].webhook_username`   | --  | --                                              | VMWare only. |
| `has_password`           | INTEGER | derived: `password` present         | --  | --                                              | Bool 0/1. Raw `password` is redacted, never stored. |
| `has_webhook_password`   | INTEGER | derived: `webhook_password` present | --  | --                                              | Bool 0/1. Raw value redacted. |
| `has_webhook_secret`     | INTEGER | derived: `webhook_secret` present   | --  | --                                              | Bool 0/1. Raw value redacted. |
| `has_webhook_token`      | INTEGER | derived: `webhook_token` present    | --  | --                                              | Bool 0/1. Raw value redacted. |
| `polled_at_utc`          | TEXT    | MistHelper clock                    | --  | --                                              | ISO8601 UTC timestamp of the poll. |

**Security note**: The `password`, `webhook_password`, `webhook_secret`, and
`webhook_token` fields are secret material returned by the Mist API. MistHelper
persists a boolean `has_*` marker only and never stores the raw value on disk or in
any log line. This complies with the constitution's "no secrets in logs / no secrets
in disk artifacts you did not generate" pattern.

## State Transitions

N/A -- this is a read-only endpoint. The underlying OAuth link on the Mist side
transitions between `linked=false` (no active OAuth grant) and `linked=true` (active
grant with one-or-more accounts), and individual accounts move through
`last_status` values (`success`, `failed`, ...). MistHelper does not drive these
transitions; each poll overwrites the prior snapshot for the same (org, app_name)
tuple via SQLite `INSERT OR REPLACE`, and each account row is upserted by
(org, app_name, account_id).

## SQLite DDL

```sql
-- Summary table: one row per (org, integration).
CREATE TABLE IF NOT EXISTS org_oauth_app_link_summary (
    org_id             TEXT    NOT NULL,
    app_name           TEXT    NOT NULL,
    linked             INTEGER,
    authorization_url  TEXT,
    accounts_count     INTEGER,
    polled_at_utc      TEXT,
    PRIMARY KEY (org_id, app_name)
);

CREATE INDEX IF NOT EXISTS idx_oauth_link_summary_linked
    ON org_oauth_app_link_summary (linked);

-- Accounts table: zero-or-more rows per (org, integration, account).
CREATE TABLE IF NOT EXISTS org_oauth_app_link_accounts (
    org_id                    TEXT    NOT NULL,
    app_name                  TEXT    NOT NULL,
    account_id                TEXT    NOT NULL,
    name                      TEXT,
    company                   TEXT,
    cloud_name                TEXT,
    client_id                 TEXT,
    instance_url              TEXT,
    username                  TEXT,
    last_status               TEXT,
    last_sync                 INTEGER,
    linked_by                 TEXT,
    linked_timestamp          REAL,
    error                     TEXT,
    errors_joined             TEXT,
    enable_probe              INTEGER,
    auto_probe_subnet         TEXT,
    region                    TEXT,
    regions_json              TEXT,
    service_account_name      TEXT,
    service_connections_json  TEXT,
    tsg_id                    TEXT,
    smartgroup_name           TEXT,
    key_id                    TEXT,
    zdx_org_id                TEXT,
    max_daily_api_requests    INTEGER,
    webhook_enabled           INTEGER,
    webhook_auth_type         TEXT,
    webhook_url               TEXT,
    webhook_username          TEXT,
    has_password              INTEGER,
    has_webhook_password      INTEGER,
    has_webhook_secret        INTEGER,
    has_webhook_token         INTEGER,
    polled_at_utc             TEXT,
    PRIMARY KEY (org_id, app_name, account_id),
    FOREIGN KEY (org_id, app_name)
        REFERENCES org_oauth_app_link_summary(org_id, app_name)
);

CREATE INDEX IF NOT EXISTS idx_oauth_link_accounts_last_status
    ON org_oauth_app_link_accounts (last_status);

CREATE INDEX IF NOT EXISTS idx_oauth_link_accounts_company
    ON org_oauth_app_link_accounts (company);
```

`DataExporter.write_with_format_selection()` is responsible for emitting equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB
via collection upsert, Redis via key namespacing). MistHelper does not run the DDL
directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single dict-literal insert, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (org, integration), keyed by (org_id, app_name).
    'getOrgOauthAppLinkedStatus': {                                                 # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['org_id', 'app_name'],                                      # stable identity of the integration
        'indexes': ['linked'],                                                      # fast filter: which integrations are linked
        'table': 'org_oauth_app_link_summary',                                      # target SQLite table for summary rows
    },

    # Per-account detail rows produced from the accounts[] array.
    'getOrgOauthAppLinkedStatusAccounts': {                                         # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of summary FK + account id
        'primary_key': ['org_id', 'app_name', 'account_id'],                        # uniquely identifies a linked account
        'indexes': ['last_status', 'company'],                                      # common query filters
        'table': 'org_oauth_app_link_accounts',                                     # target SQLite table for account rows
    },
}
```

The `getOrgOauthAppLinkedStatusAccounts` key is a MistHelper-internal identifier
(the Mist API has no operationId for it -- it is the flattened `accounts` sub-array
of the parent response). This pattern matches how MistHelper already splits other
endpoints whose response contains nested arrays.
