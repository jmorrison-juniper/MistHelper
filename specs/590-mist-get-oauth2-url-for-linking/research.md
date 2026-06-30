# Phase 0 Research: GetOauth2UrlForLinking

**Feature**: 590-mist-get-oauth2-url-for-linking
**Date**: 2026-06-29
**Source doc**: `documentation/api/self/GET_self_oauth_provider.md`

---

## Research Task 1: SDK Function Signature & Behavior

### Decision

Invoke `mistapi.api.v1.self.oauth2.getOauth2UrlForLinking(apisession, provider, forward=None)`.

The function signature reads:

- `apisession` -- the `mistapi.APISession` instance already constructed at MistHelper
  startup (carries `MIST_HOST`, `MIST_API_TOKEN`).
- `provider` -- required path parameter, string, OAuth2 provider slug
  (e.g. `google`, `microsoft`, `azure`, `okta`).
- `forward` -- optional query parameter, string, post-link redirect URL.

Return: an `mistapi.APIResponse` object whose `.data` attribute holds the parsed JSON
object with two fields:

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `authorization_url` | string | yes | URL the operator must paste into a browser to authorize the provider link. Contains a one-time CSRF / state token. |
| `linked` | boolean | yes | `true` when the provider is already linked to the current admin; `false` otherwise. |

HTTP semantics: pure GET, idempotent, non-paginated, returns a single object (not a
list). Mist applies standard 5000-calls-per-hour rate limiting.

### Rationale

The enriched per-endpoint doc at
`documentation/api/self/GET_self_oauth_provider.md` lists the SDK path as
`mistapi.api.v1.self.oauth2.getOauth2UrlForLinking()` and confirms the two-field
response shape. The spec.md upstream input shows `mistapi.api.v1.self.oauth` as the
module hint, but the authoritative per-endpoint doc uses the `oauth2` submodule
naming -- which matches the OpenAPI tag `Self OAuth2`. The implementation MUST follow
the per-endpoint doc; the spec field is a hint, not the canonical SDK path.

### Alternatives Considered

- **Raw `requests.get(...)`** -- rejected. The constitution mandates `mistapi` as the
  sole permitted Mist Cloud interface. A direct `requests` call would bypass session
  reuse, rate-limit handling, and 429 back-off built into `mistapi`.
- **Use `mistapi.api.v1.self.oauth` (no trailing `2`)** -- rejected. The
  per-endpoint doc emitted from the enriched OpenAPI run explicitly names the
  submodule `oauth2`. If the SDK module path differs at implementation time, the
  task agent re-verifies against the installed `mistapi` package and updates the
  call site; this research note records the doc-authoritative path.
- **Pre-cache the URL in Redis only** -- rejected. The constitution mandates
  multi-backend output via `DataExporter`; caching alone would skip CSV / SQLite
  consumers.

---

## Research Task 2: Primary Key Strategy

### Decision

Strategy: **`natural_pk`** with `primary_key=['provider']`.

```python
'getOauth2UrlForLinking': {
    'type': 'natural_pk',
    'primary_key': ['provider'],
    'indexes': ['linked', 'fetched_at_utc']
}
```

The `provider` slug is the only stable identifier in the response; the
`authorization_url` carries an embedded one-time state token and changes on every
call, so it cannot be a key. The `fetched_at_utc` column is added by MistHelper at
flatten time (not by the API) so re-runs upsert cleanly on the same provider row,
keeping only the most recent URL.

### Rationale

- The endpoint is scoped to the authenticated admin (no `org_id` is part of the
  request), and only one URL exists per `provider` for that admin at any given
  moment. `provider` is therefore the natural business key.
- A composite key with `(provider, fetched_at_utc)` would accumulate history rows
  (one per fetch) which is undesirable -- the URL is one-shot and the older row is
  immediately stale.
- `INSERT OR REPLACE` semantics on the single-column key give the operator a clean
  "latest URL per provider" table without manual cleanup.

### Alternatives Considered

- **`composite_pk` with `(provider, fetched_at_utc)`** -- rejected. Creates
  permanent history of stale, single-use URLs that cannot be replayed.
- **`auto_increment_with_unique` with unique on `provider`** -- rejected. Adds a
  synthetic `misthelper_internal_id` for no benefit; natural key is already stable
  and small.
- **No PK / append-only CSV** -- rejected. Violates the documented hybrid-PK
  contract in `ENDPOINT_PRIMARY_KEY_STRATEGIES` and breaks SQLite upsert behavior.

---

## Research Task 3: Output Filename and SQLite Table

### Decision

- **CSV filename**: `data/self_oauth_link_url.csv`
- **SQLite table name**: `self_oauth_link_url`
- **ArangoDB collection name**: `self_oauth_link_url`
- **Redis key prefix**: `mist:self:oauth:link_url:<provider>`

### Rationale

- The MistHelper naming convention for read-only export operations is
  `<scope>_<resource>.csv` with snake_case tokens. `self_oauth_link_url` clearly
  identifies the scope (`self` -- authenticated admin), the namespace (`oauth`),
  and the artifact (`link_url`).
- Keeping table and CSV names identical simplifies the existing `DataExporter`
  routing logic, which derives the SQLite table from the filename stem.
- The Redis key prefix is keyed on `provider` (the natural PK) so cache lookups are
  O(1) per provider.

### Alternatives Considered

- **`oauth_authorization_url.csv`** -- rejected. Drops the `self_` scope prefix
  and loses parity with the other `self_*` artifacts that will appear when the
  sibling POST endpoint is cataloged.
- **`getOauth2UrlForLinking.csv`** -- rejected. Camel-case operationId names are
  reserved for the `ENDPOINT_PRIMARY_KEY_STRATEGIES` key; on-disk filenames stay
  snake_case for cross-platform / case-insensitive filesystem safety.

---

## Research Task 4: Menu Category Placement and Next Available Menu Number

### Decision

Place the new operation at **menu number 149**, within the Interactive Config cluster
(menu range 148-150), under a category label such as "Self / OAuth2 -- Get link URL".

If 149 collides with an in-flight feature branch at task-generation time, fall back
to the next free integer in the Interactive cluster (124-150) in this priority order:
148, 150, then highest-free-integer below 148.

### Rationale

- The Mist API tag `Self OAuth2` is account-configuration in nature -- the operator
  fetches a URL to wire up an external identity provider. That is configuration,
  not org-scoped export, so it belongs in the Interactive Config band (148-150),
  not the Safe Org Exports band (1-59).
- The op is read-only (HTTP GET, returns a URL string) so it does NOT belong in
  the destructive range (154-194).
- Numbers 124-147 host other interactive diagnostics and management items;
  148-150 is the documented Config sub-cluster and currently has open slots. The
  reference plan (spec 500) demonstrates the same "pick next free integer in the
  natural cluster" pattern.

### Alternatives Considered

- **Menu 59 (Misc, Safe Org Exports)** -- rejected. The op is not org-scoped;
  placing it in the org-export band confuses the operator.
- **Menu 96 (end of Interactive Safe Viewers)** -- rejected. Viewers are
  inspection tools for site/org telemetry; OAuth link URL is account config.
- **A brand-new top-level category** -- rejected. The existing Config sub-cluster
  is exactly the right home; introducing a new category for a two-endpoint tag
  inflates the menu hierarchy without benefit.

---

## Research Task 5: Required User Prompts

### Decision

The menu method collects **two prompts** via `safe_input()`:

1. `provider` (required, string) --
   Prompt text: `"OAuth2 provider slug (e.g. google, microsoft, azure, okta): "`
   Context tag: `"self_oauth_link_url:provider"`
   Validation: non-empty, lowercased, restricted to a small allow-list seeded by
   the constant `SUPPORTED_OAUTH_PROVIDERS = {"google", "microsoft", "azure", "okta"}`
   defined at module level. Unknown values log a `WARNING` and the method returns
   early without an API call.
2. `forward` (optional, string) --
   Prompt text: `"Optional post-link redirect URL (press Enter to skip): "`
   Context tag: `"self_oauth_link_url:forward"`
   Validation: if empty, set `forward=None` so `mistapi` omits the query string.
   If non-empty, basic shape check (must start with `http://` or `https://`); on
   failure log a `WARNING` and treat as `None`.

No identifier is sourced from `.env` -- the endpoint is account-scoped, and the
authenticated admin is already determined by `MIST_API_TOKEN` (loaded into the
`mistapi.APISession` at startup). The optional `MISTHELPER_TEST_OAUTH_PROVIDER`
environment variable is read only by the `--test` harness to supply a default
provider value in non-interactive mode (defaulting to `google`).

### Rationale

- The OpenAPI doc lists `provider` as the only required parameter, and `forward`
  as the only optional one. There are no org / site / device identifiers in this
  call.
- Provider validation against an allow-list prevents the operator from sending
  arbitrary strings to Mist (which would return 404 and waste a rate-limit slot).
- The optional `forward` follows the existing MistHelper pattern of empty-string
  -> skip-parameter, established in adjacent menu items.

### Alternatives Considered

- **Prompt for `provider` from a numbered sub-menu** -- rejected for now. With
  only four common providers the typed string is simpler; if Mist adds many more
  providers, a future refactor can promote the allow-list to a sub-menu.
- **Pull `provider` from `.env`** -- rejected for interactive use. The whole
  point is the operator chooses which provider to link in this run; baking it
  into `.env` would defeat that. The `--test` harness uses `.env` only as a
  default for non-interactive sweeps.
- **Make `forward` required** -- rejected. OpenAPI marks it optional; forcing it
  on the operator would deviate from the upstream contract.
