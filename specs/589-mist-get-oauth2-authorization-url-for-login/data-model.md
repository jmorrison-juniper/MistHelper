# Phase 1 Data Model: getOauth2AuthorizationUrlForLogin

**Feature**: 589 -- Mist API GET endpoint `getOauth2AuthorizationUrlForLogin`
**Source doc**: `documentation/api/admins/GET_login_oauth_provider.md`
**Spec**: [spec.md](./spec.md)

## Entities Returned by the Endpoint

The HTTP 200 response is a single JSON object (not an array). There is exactly **one
logical entity**: the OAuth2 authorization handshake row for a given identity provider.
No nested or referenced sub-entities are returned.

### Entity: `LoginOauthAuthorizationUrl`

| Field             | Type    | Required (API) | Source                                | Description                                                                                  |
|-------------------|---------|----------------|---------------------------------------|----------------------------------------------------------------------------------------------|
| `provider`        | TEXT    | Yes (synthesized) | Path parameter, normalized lower-case | Identity provider name (for example `google`, `azure`). Synthesized into the row by MistHelper because the API response does not echo the path. **Primary key**. |
| `authorization_url` | TEXT  | Yes            | Response body `authorization_url`     | Full OAuth2 authorization endpoint URL (carries a fresh `state` token on every call).        |
| `client_id`       | TEXT    | Yes            | Response body `client_id`             | OAuth2 client identifier registered with the provider for this Mist tenant.                  |
| `forward`         | TEXT    | No             | Query parameter, echoed by MistHelper | Callback URL supplied by the operator at run time. Stored as `NULL` when not supplied.       |
| `fetched_at`      | TEXT    | No (synthesized) | ISO-8601 UTC timestamp set by MistHelper | Wall-clock time of the API call. Useful when correlating against rotated `state` tokens.  |

**Primary key**: (`provider`)
**Foreign keys**: None. The endpoint is account-scoped, not org / site / device scoped.

### State Transitions

N/A -- read-only endpoint. The Mist back end rotates `authorization_url`'s embedded
`state` token on every call, but from MistHelper's perspective each invocation is an
independent upsert into the same row keyed on `provider`. The previous `authorization_url`
is overwritten; that is the intended behavior (the previous URL would be invalid by then
anyway).

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS login_oauth_authorization_url (
    provider          TEXT    NOT NULL,                 -- normalized lower-case path param; primary key
    authorization_url TEXT    NOT NULL,                 -- full OAuth2 authorization endpoint URL (includes state)
    client_id         TEXT    NOT NULL,                 -- OAuth2 client identifier for this tenant
    forward           TEXT,                             -- optional callback URL (NULL when not supplied)
    fetched_at        TEXT    NOT NULL,                 -- ISO-8601 UTC timestamp of the API call
    PRIMARY KEY (provider)
);

CREATE INDEX IF NOT EXISTS idx_login_oauth_authorization_url_client_id
    ON login_oauth_authorization_url (client_id);       -- supports "which provider uses this client_id" lookups
```

`DataExporter.write_with_format_selection()` creates the table on first run from the
flattened dict it receives; the DDL above documents the intended target shape so a
manual `CREATE TABLE` is also possible during database recovery.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (the dictionary is currently anchored around line 1672). The key is the
operationId exactly as it appears in the OpenAPI spec, and the value is the strategy
descriptor.

```python
"getOauth2AuthorizationUrlForLogin": {                  # operationId from documentation/api/admins/GET_login_oauth_provider.md
    "type": "natural_pk",                               # provider is supplied by the user and is stable across calls
    "primary_key": ["provider"],                        # one row per OAuth2 provider name
    "indexes": ["client_id"],                           # support reverse lookups by registered OAuth2 client id
    "table_name": "login_oauth_authorization_url",      # explicit table override matches DataExporter filename
},
```

Notes:

- The `table_name` override is provided because the operationId
  (`getOauth2AuthorizationUrlForLogin`) does not transliterate cleanly to the desired
  table name; the explicit field keeps the SQLite, CSV, and ArangoDB names aligned.
- `type` is `natural_pk` per Phase 0 Research Task 2.
- Indexes list `client_id` only -- `authorization_url` is high-cardinality and changes
  every call, so indexing it would add cost without benefit.

## Row-Construction Pseudocode

The implementation flattens the response into one dict per call:

```python
row = {                                                  # single row -- the endpoint returns one object
    "provider": provider.strip().lower(),                # normalized path param; primary key
    "authorization_url": response.data["authorization_url"],  # raw URL from the API
    "client_id": response.data["client_id"],             # OAuth2 client id from the API
    "forward": forward or None,                          # echo the operator-supplied callback or None
    "fetched_at": datetime.now(timezone.utc).isoformat(),  # audit timestamp for incident response
}
```

The dict is passed to
`DataExporter.write_with_format_selection([row], filename="login_oauth_authorization_url", api_function_name="getOauth2AuthorizationUrlForLogin")`
which dispatches to the active backend (CSV, SQLite with `INSERT OR REPLACE`, or
ArangoDB+Redis).
