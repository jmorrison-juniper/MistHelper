# Phase 0 Research: getOauth2UrlForLinking

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/self/GET_self_oauth_provider.md` (enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK using the URL-derived module path:
`mistapi.api.v1.self.oauth.getOauth2UrlForLinking(apisession, provider, forward=None)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single two-field object (not a list and not paginated), with:

- `authorization_url` (string, required) -- HTTPS URL the operator's browser must
  visit to authorize the link. Contains a short-lived state nonce that rotates on
  every call.
- `linked` (boolean, required) -- `true` when the provider is already linked to the
  authenticated admin account, `false` otherwise.

Required path parameter: `provider` (string -- e.g., `google`, `azure`, `okta`).
Optional query parameter: `forward` (string -- URL the provider should redirect to
after authorization completes). When omitted, the SDK does not add the query parameter
to the URL.

**Rationale**:
The enriched per-endpoint doc lists the SDK module path as
`mistapi.api.v1.self.oauth2.getOauth2UrlForLinking()`, but the OpenAPI URL is
`/api/v1/self/oauth/{provider}` (path segment `oauth`, not `oauth2`). The mistapi SDK
historically generates module paths from the URL, not the OpenAPI tag, which is
verified by inspecting the sibling endpoint `POST /api/v1/self/oauth/{provider}` whose
SDK path is `mistapi.api.v1.self.oauth` (no trailing `2`). The spec.md explicitly
names `mistapi.api.v1.self.oauth` and that matches the URL one-for-one, so we follow
the spec. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.self import oauth; help(oauth)"` inside the venv;
if the installed SDK ships the module as `oauth2`, the import is adjusted in a single
line and the constant in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (keyed by operationId, not
module path) remains correct.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/self/oauth/{provider}`.* Rejected -- the constitution
   forbids direct HTTP when a mistapi method exists.
2. *Trust the doc's `oauth2` module name verbatim.* Rejected -- the URL path token is
   `oauth` (no `2`), and adjacent endpoints under the same path use the URL-based
   module name. Following the spec is safer; we still verify with `help()` at
   implementation time.
3. *Auto-discover the provider name via `getSelf` first.* Rejected -- adds a second
   round trip and a hidden dependency. The user explicitly knows which provider they
   want to link.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy on the single output table:

- `self_oauth_link_urls`: PK = `(account_email, provider)` -- one row per
  (authenticated account, OAuth2 provider). `account_email` is fetched once at
  startup from the existing `getSelf` cache that MistHelper already maintains;
  `provider` is the path parameter the user supplied.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk`.

**Rationale**:
This endpoint is account-scoped, not org-scoped, so `org_id` is not part of the key.
The natural identity of a row is "which provider's linking URL did we fetch for which
admin account". The `authorization_url` field changes on every call (state nonce
rotation), so re-running the menu item must overwrite the previous URL rather than
append a duplicate row. Pairing `account_email` with `provider` gives one stable row
per pair, and `INSERT OR REPLACE` keeps the freshest URL on each poll. `linked` is a
state flag that flips when the user completes the link in their browser; storing it
alongside the URL lets `getSelf`-style follow-up checks reuse the same row.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on `provider` alone.* Rejected -- a developer running
   MistHelper as several admin accounts (dev / staging / prod tokens) would silently
   overwrite another account's row. Pairing with `account_email` keeps multi-tenant
   safety.
2. *`composite_pk` on `(account_email, provider, polled_at_utc)`.* Rejected --
   appending a row per poll defeats the point of upsert and bloats the table because
   the URL changes every call. Operators want the latest URL, not a history.
3. *`natural_pk` on `provider` alone.* Rejected for the multi-account reason above.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/self_oauth_link_<provider>.csv`
  (e.g., `data/self_oauth_link_google.csv`, `data/self_oauth_link_azure.csv`)
- SQLite table: `self_oauth_link_urls`
- ArangoDB collection (when active): `self_oauth_link_urls` (same name as SQLite)
- The `api_function_name` argument passed to
  `DataExporter.write_with_format_selection()` is `"getOauth2UrlForLinking"` (matches
  the operationId). The DataExporter uses that string as the lookup key into
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Embedding the provider into the CSV filename keeps human-readable separation per
provider when an operator links multiple identity sources sequentially. The provider
token is already validated to ASCII `[a-z0-9_-]{1,32}` (Principle III), so no path
sanitization is needed beyond the existing `pathlib.Path` join. The SQLite / Arango
table is single because rows are differentiated by the `provider` column inside the
table -- splitting tables per provider would explode the schema unnecessarily.

**Alternatives Considered**:

1. *One global file `data/self_oauth_link_urls.csv`.* Rejected -- mixes providers in
   one CSV, which is harder to eyeball in `data/` directory listings. SQLite already
   gives a unified table, so per-provider CSV is a usability win without losing
   queryability.
2. *Stash the URL in `data/.cache/` instead of `data/`.* Rejected -- the constitution
   requires all outputs under `data/`. Operators may want to copy the URL to a browser
   from `data/` listings.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org Exports
/ Safe Self-Account cluster (1-59), adjacent to the existing
`SelfExportUtils.audit_logs()` entry. The category label is
"Safe Self-Account -- OAuth2 Link URL".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. Self-account exports
historically live inside the safe block; 58 is the next contiguous integer below the
final safe-block slot at 59 and is far from the destructive block at 154-194,
correctly signaling read-only safety to a junior NOC engineer scrolling the menu.
The number is provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for
the latest allocated menu integer and 58 is shifted forward if a conflict exists with
another in-flight feature branch.

**Alternatives Considered**:

1. *Append to the very end (e.g., 195).* Rejected -- the destructive cluster ends at
   194 and placing a read-only OAuth check above the destructive block visually
   mis-signals the risk level. Operators learn the cluster boundaries; placing this
   item inside 1-59 follows the existing convention.
2. *Slot inside the Interactive Safe range (60-96).* Rejected -- this endpoint
   requires only two simple prompts and produces a single-row output. It is no more
   "interactive" than the existing self audit-logs export at the same complexity
   tier.
3. *Slot inside the Resource Intensive range (97-101).* Rejected -- one GET, one
   small response, no pagination, no long-running work. It belongs in the safe block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `provider` -- prompt: `"OAuth2 provider name (e.g., google, azure): "`, context:
   `"self_oauth_link:provider"`. Default: the value of `MIST_OAUTH_PROVIDER` in
   `.env` if present (pressing Enter accepts the default; the variable is optional
   and not added to `.env.example` because the value is operator-specific). Normalized
   to lower-case and validated against `^[a-z0-9_-]{1,32}$` before the API call; on
   failure, log `WARNING` and return early.
2. `forward` -- prompt: `"Forward URL after authorization (optional, press Enter to
   skip): "`, context: `"self_oauth_link:forward"`. Default: empty string (no
   forward). When non-empty, must start with `https://`; otherwise log `WARNING` and
   send the request without the `forward` query parameter.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_OAUTH_PROVIDER` -- optional default for prompt 1.

The authenticated account's `email` (used as the `account_email` PK column) is
sourced from the existing in-process `getSelf` cache; no extra prompt is needed.

**Rationale**:
The endpoint is account-scoped, so `org_id` / `site_id` / `device_id` are not
involved. The optional `forward` parameter materially changes the OAuth2 redirect
flow but is only useful when the operator already has a callback URL ready -- making
it optional with an empty default keeps the common "just give me the link" path to
two keystrokes. Validating both inputs client-side keeps Mist from returning HTTP 400
when the operator typos a provider name.

**Alternatives Considered**:

1. *Single prompt: provider only; never expose `forward`.* Rejected -- the OpenAPI
   doc lists `forward` as a real query parameter and operators integrating with a
   custom portal will need it.
2. *Auto-fill `provider` by listing supported providers via a discovery endpoint.*
   Rejected -- Mist has no documented discovery endpoint for OAuth2 providers, and
   the constitution forbids guessing API shapes.
3. *Validate `forward` more strictly (must match the org's configured callback
   domain).* Rejected -- MistHelper does not own that allow-list; Mist itself
   rejects bad forwards at the OAuth2 redirect stage. Client-side `https://` check
   is sufficient defensive validation.
