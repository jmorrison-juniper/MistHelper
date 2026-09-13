# Phase 1 Data Model: getOrgWebhook

**Feature**: 653-mist-get-org-webhook
**Endpoint**: `GET /api/v1/orgs/{org_id}/webhooks/{webhook_id}`
**Source schema**: `documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id.md`
(lines 33-186)

## Entity: OrgWebhookDetail

The endpoint returns exactly one entity per successful call: a single
webhook configuration object. It has no nested collections that require
separate tables -- `topics`, `assetfilter_ids`, `oauth2_scopes`, and
`headers` are stored as serialized JSON strings on the single row (this
is the same flatten pattern used by adjacent MistHelper webhook rows).

### Fields

| Field                        | Type                | Nullable | Notes                                                                                                                                                            |
|------------------------------|---------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| id                           | string (UUID)       | No       | Server-issued unique webhook ID. **Primary key.**                                                                                                                |
| org_id                       | string (UUID)       | No       | Owning organization. Foreign key -> `orgs.id`.                                                                                                                   |
| site_id                      | string (UUID)       | Yes      | Present when `for_site == true`. Foreign key -> `sites.id`.                                                                                                      |
| for_site                     | boolean             | No       | `true` when the webhook is site-scoped. `readOnly`.                                                                                                              |
| name                         | string              | Yes      | Human-readable name.                                                                                                                                             |
| enabled                      | boolean             | No       | Default `true`.                                                                                                                                                  |
| type                         | string              | No       | Enum: `aws-sns`, `google-pubsub`, `http-post`, `oauth2`, `splunk`.                                                                                                |
| url                          | string              | Yes      | Target URL for `http-post`, `oauth2`, `splunk`; unused for `aws-sns` and `google-pubsub`.                                                                        |
| verify_cert                  | boolean             | No       | Default `true`. Only meaningful for HTTPS URLs.                                                                                                                  |
| topics                       | JSON array (string) | Yes      | Serialized JSON of subscribed webhook topic names. Column stored as TEXT.                                                                                        |
| single_event_per_message     | boolean             | No       | Default `false`. Only supported on certain topics.                                                                                                               |
| headers                      | JSON object         | Yes      | Serialized JSON of custom HTTP headers (only when `type == http-post`). Stored as TEXT.                                                                          |
| secret                       | string              | Yes      | HMAC signing secret for `http-post`. **Sensitive** -- persisted but redacted in logs.                                                                            |
| assetfilter_ids              | JSON array (string) | Yes      | Serialized JSON of asset filter UUIDs (only when `type == asset-raw-rssi`). Stored as TEXT.                                                                      |
| splunk_token                 | string              | Yes      | HEC token for `splunk` type. **Sensitive** -- persisted but redacted in logs.                                                                                    |
| oauth2_grant_type            | string              | Yes      | Enum: `client_credentials`, `password`. Required when `type == oauth2`.                                                                                          |
| oauth2_token_url             | string              | Yes      | Required when `type == oauth2`.                                                                                                                                  |
| oauth2_client_id             | string              | Yes      | Required when `oauth2_grant_type == client_credentials`.                                                                                                         |
| oauth2_client_secret         | string              | Yes      | Required when `oauth2_grant_type == client_credentials`. **Sensitive** -- persisted but redacted in logs.                                                        |
| oauth2_username              | string              | Yes      | Required when `oauth2_grant_type == password`.                                                                                                                   |
| oauth2_password              | string              | Yes      | Required when `oauth2_grant_type == password`. **Sensitive** -- persisted but redacted in logs.                                                                  |
| oauth2_scopes                | JSON array (string) | Yes      | Serialized JSON of OAuth2 scope strings.                                                                                                                         |
| created_time                 | number (epoch)      | No       | Server timestamp. `readOnly`.                                                                                                                                    |
| modified_time                | number (epoch)      | No       | Server timestamp. `readOnly`.                                                                                                                                    |
| misthelper_ingest_time       | number (epoch)      | No       | Local column added by MistHelper flattener; recorded at write time for freshness tracking.                                                                       |

### Primary Key

`id` (natural, server-issued UUID). Upsert via `INSERT OR REPLACE` guarantees
that repeated menu invocations for the same `webhook_id` produce one and only
one row.

### Foreign Keys (informational, not enforced by SQLite backend)

- `org_id` -> `orgs.id`
- `site_id` -> `sites.id` (when `for_site == true`)

### State Transitions

**N/A -- read-only endpoint.** The MistHelper row is a point-in-time
snapshot of the server-side webhook configuration; the local table has no
state machine. Freshness is inferred from `modified_time` (server-authored)
and `misthelper_ingest_time` (locally authored).

## SQLite DDL

```sql
-- Auto-created by DataExporter on first invocation of menu 96.
-- Matches the getOrgWebhook response schema documented at
-- documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id.md
CREATE TABLE IF NOT EXISTS org_webhook_detail (
    id                          TEXT PRIMARY KEY,
    org_id                      TEXT NOT NULL,
    site_id                     TEXT,
    for_site                    INTEGER NOT NULL DEFAULT 0,
    name                        TEXT,
    enabled                     INTEGER NOT NULL DEFAULT 1,
    type                        TEXT NOT NULL,
    url                         TEXT,
    verify_cert                 INTEGER NOT NULL DEFAULT 1,
    topics                      TEXT,
    single_event_per_message    INTEGER NOT NULL DEFAULT 0,
    headers                     TEXT,
    secret                      TEXT,
    assetfilter_ids             TEXT,
    splunk_token                TEXT,
    oauth2_grant_type           TEXT,
    oauth2_token_url            TEXT,
    oauth2_client_id            TEXT,
    oauth2_client_secret        TEXT,
    oauth2_username             TEXT,
    oauth2_password             TEXT,
    oauth2_scopes               TEXT,
    created_time                REAL,
    modified_time               REAL,
    misthelper_ingest_time      REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_org_webhook_detail_org_id
    ON org_webhook_detail (org_id);
CREATE INDEX IF NOT EXISTS idx_org_webhook_detail_name
    ON org_webhook_detail (name);
CREATE INDEX IF NOT EXISTS idx_org_webhook_detail_type
    ON org_webhook_detail (type);
CREATE INDEX IF NOT EXISTS idx_org_webhook_detail_enabled
    ON org_webhook_detail (enabled);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following key to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py`
(the dictionary lives near line ~1672 per
`.github/copilot-instructions.md`). Every executable line carries an inline
comment per Constitution Principle VI:

```python
    "getOrgWebhook": {                                          # Register PK strategy for menu 96 getOrgWebhook operation
        "type": "natural_pk",                                   # Webhook has a stable server-issued UUID at .id
        "primary_key": ["id"],                                  # UUID is globally unique across Mist Cloud
        "indexes": ["org_id", "name", "type", "enabled"],       # Support common downstream queries by org, name, protocol, and disabled-set audit
        "table_name": "org_webhook_detail",                     # Distinct from list-endpoint table org_webhooks (menu 47)
        "sensitive_fields": [                                   # Fields that must be redacted from log output but persisted to storage
            "secret",                                           # HMAC secret for http-post webhooks
            "splunk_token",                                     # HEC token for splunk webhooks
            "oauth2_client_secret",                             # OAuth2 client credentials flow secret
            "oauth2_password",                                  # OAuth2 password flow user password
        ],
    },
```
