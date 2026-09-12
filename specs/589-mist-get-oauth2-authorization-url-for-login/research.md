# Phase 0 Research: getOauth2AuthorizationUrlForLogin

**Feature**: 589 -- Mist API GET endpoint `getOauth2AuthorizationUrlForLogin`
**Source doc**: `documentation/api/admins/GET_login_oauth_provider.md`
**Spec**: [spec.md](./spec.md)

The five research tasks below resolve every Phase 0 unknown before Phase 1 design.
No "NEEDS CLARIFICATION" markers remain.

---

## Research Task 1: SDK function signature and behavior

**Decision**: Use the SDK call

```python
mistapi.api.v1.admins.login_-_oauth2.getOauth2AuthorizationUrlForLogin(
    apisession,
    provider,           # str, required path parameter
    forward=None,       # str, optional query parameter -- callback URL
)
```

The Python identifier `login_-_oauth2` is the SDK-generated module name shown in
`documentation/api/admins/GET_login_oauth_provider.md` line 79. Because the literal
character `-` is not legal in a Python module path, the implementation imports the
module through `importlib`:

```python
oauth_mod = importlib.import_module("mistapi.api.v1.admins.login_-_oauth2")
response = oauth_mod.getOauth2AuthorizationUrlForLogin(api, provider, forward=forward)
```

The function returns an `mistapi.APIResponse`-shaped object whose `.data` attribute is
the JSON dict `{"authorization_url": "<url>", "client_id": "<id>"}` and whose
`.status_code` is `200` on success.

**Rationale**: The enriched per-endpoint doc is authoritative for the SDK call shape;
both the operationId and the SDK module string come directly from the OpenAPI spec used
to generate `mistapi`. The `forward` parameter is documented as optional with no enum
restriction, so the menu passes `None` when the user supplies an empty string. The
endpoint is not paginated, so no `mistapi_pagination` helper is needed -- a single call
is sufficient.

**Alternatives Considered**:

- *Direct `requests.get()` call*: rejected. The constitution mandates `mistapi` as the
  only Mist API interface.
- *`getattr(mistapi.api.v1.admins, "login_-_oauth2")` instead of `importlib`*: rejected.
  `getattr` on a submodule that has not yet been imported can fail; `importlib` is the
  documented, deterministic approach.
- *Hard-coded provider allow-list passed as an enum*: rejected. The OpenAPI doc declares
  `provider` as a free-form string with no enum, so the menu validates only basic shape
  (alphanumeric plus dash, 1-32 chars) and lets the Mist API surface unknown providers
  as a 404.

---

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` keyed on `provider` (the path parameter, normalized to lower
case before persistence).

```python
"getOauth2AuthorizationUrlForLogin": {
    "type": "natural_pk",
    "primary_key": ["provider"],
    "indexes": ["client_id"],
}
```

**Rationale**: The endpoint returns exactly one record per `provider` value, and that
value is supplied by the user as a path parameter -- it is the natural business key for
this row. Re-running the menu against the same provider must upsert (the authorization
URL contains a fresh `state` token each call, so the row content changes but the key
stays stable). The `client_id` is indexed because operators may want to query "which
provider uses this client_id?" in incident response. No composite key is needed because
the response is not time-series and there is no list returned. An auto-increment fallback
is unnecessary because `provider` is always present and stable.

**Alternatives Considered**:

- *`composite_pk` on `(provider, client_id)`*: rejected. The `client_id` rarely changes
  per provider; treating it as part of the primary key would create a duplicate row
  every time the Mist back end rotated the OAuth2 client, defeating the upsert.
- *`auto_increment_with_unique`*: rejected. A natural key exists (`provider`), so the
  constitution's preference for natural keys applies.
- *Composite on `(provider, fetched_at_timestamp)`*: rejected. The constitution treats
  audit timestamps as ordinary columns, not key components, unless the endpoint is
  time-series (this one is not).

---

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV filename: `data/login_oauth_authorization_url.csv`
- SQLite table: `login_oauth_authorization_url`
- ArangoDB collection: `login_oauth_authorization_url` (consistent with the other two
  backends; `DataExporter.write_with_format_selection()` derives the collection name
  from the same filename token)

**Rationale**: The convention in MistHelper is `<resource_family>_<operation>`. The
endpoint sits under `/api/v1/login/oauth/{provider}` and returns an authorization URL,
so `login_oauth_authorization_url` reads cleanly and groups naturally next to any future
`login_oauth_complete` (POST) or `login_oauth_unlink` (DELETE) tables. Lower-snake-case
matches the existing tables (`org_sites`, `org_devices_stats`, etc.). The filename token
is what `DataExporter` uses to derive the SQLite table name and the ArangoDB collection
name, so a single string change keeps all three backends in sync.

**Alternatives Considered**:

- *`oauth_auth_url`*: rejected -- too terse, loses the `login` family prefix that groups
  the related POST and DELETE endpoints.
- *`admin_oauth_url`*: rejected -- the OpenAPI tag is `Admins Login - OAuth2` but the
  path token is `login`, not `admins`; matching the path token avoids confusion when
  the operator searches the OpenAPI doc.
- *Per-provider sub-files (`data/login_oauth_authorization_url_google.csv`)*: rejected.
  Splitting by `provider` would multiply files unnecessarily; SQLite already lets the
  operator filter by `provider` in one statement.

---

## Research Task 4: Menu category placement and next available menu number

**Decision**: Propose menu number **195**, with **50** held as a fallback if 195
collides with another in-flight branch.

**Rationale**: The current menu range is 1-194 (per `.github/copilot-instructions.md`).
The OAuth authorization URL fetch does not belong in the destructive 154-194 cluster,
nor in the resource-intensive 97-101 or 153 slots, nor in the SSH / packet-capture
clusters (102-150). The two natural anchors are:

1. **Tail of Config / Admin (42-50)** -- this cluster already covers org-level admin
   exports, and OAuth2 provider auth URL fetch is a one-shot admin / auth utility. Slot
   50 is the last documented integer in this cluster and is plausibly free.
2. **Append at 195** -- a fresh integer beyond the current 1-194 range, signalling that
   this is a freshly catalogued endpoint with no obvious home in the existing clusters.

The primary proposal is **195** because (a) it is guaranteed not to collide with any
already-documented operation, (b) it preserves the current cluster boundaries until a
broader re-clustering is done, and (c) it matches the "next sequential operation number"
language in the spec's acceptance checklist. The fallback **50** is held in reserve in
case another in-flight feature branch claims 195 first; the implementation pass
re-verifies the next free integer at task generation time.

**Alternatives Considered**:

- *Slot inside 60-96 (Interactive Safe)*: rejected. That range is reserved for
  per-site interactive viewers, and this endpoint has no site context.
- *Slot inside 124-150 (Interactive / Tools)*: rejected. Same reason -- those slots are
  per-device or per-site interactive tools.
- *Slot inside 154-194 (Destructive)*: rejected. The endpoint is HTTP GET and read-only;
  placing it in the destructive cluster would mislead the operator.

---

## Research Task 5: Required user prompts

**Decision**: Two prompts only, both gathered through `safe_input()`:

1. **`provider`** (required path parameter)
   - Prompt: `"OAuth2 provider name (e.g. google, azure): "`
   - `context="oauth_auth_url:provider"`
   - Validation: regex `^[a-zA-Z0-9_-]{1,32}$`; on failure log a warning and return.
   - Normalization: `.strip().lower()` before the SDK call (consistent with other
     menu items that pass user-supplied tokens to the Mist API).

2. **`forward`** (optional query parameter -- OAuth2 callback URL)
   - Prompt: `"Callback URL (press Enter to skip): "`
   - `context="oauth_auth_url:forward"`
   - Validation: if non-empty, must start with `http://` or `https://`. On failure log a
     warning and treat as empty (no early return -- the call still works without
     `forward`).
   - Empty input -> `forward=None` passed to the SDK so the query parameter is omitted.

Nothing is read from `.env` beyond the standard Mist API credentials
(`MIST_HOST`, `MIST_API_TOKEN`) that `mistapi.APISession` already consumes. No org / site
/ device IDs are required because the endpoint is account-scoped, not org-scoped.

**Rationale**: The OpenAPI doc lists exactly one required path parameter (`provider`)
and one optional query parameter (`forward`). No headers beyond the standard
`Authorization: Token <token>` are required. Restricting prompts to just these two
parameters minimizes operator friction and satisfies the 5-Item Rule (the implementation
function takes <=3 arguments including `self`).

**Alternatives Considered**:

- *Prompt for the API base URL*: rejected. `MIST_HOST` already controls this through
  `mistapi.APISession`; prompting would risk leaking the host into logs or audit trails
  inconsistently with the rest of the tool.
- *Single combined prompt `"provider [callback_url]"`*: rejected. Parsing a single
  free-form line increases the chance of validation errors and complicates the
  `safe_input()` EOF handling.
- *Hard-code `provider=google`*: rejected. The endpoint supports multiple providers; a
  fixed value would defeat the purpose of cataloguing it.
