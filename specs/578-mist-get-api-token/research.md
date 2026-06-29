# Phase 0 Research: getApiToken

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/self/apitokens/{apitoken_id}` | **Tag**: Self API Token

This document captures the five research tasks required to ground the Phase 1 design.
Each task uses the Decision / Rationale / Alternatives Considered format mandated by the
constitution's Pre-Phase 0 Gate.

## Research Task 1: SDK function signature & behavior

**Source**: `documentation/api/self/GET_self_apitokens_apitoken_id.md` (enriched OpenAPI
extract).

**Decision**: Invoke
`mistapi.api.v1.self.api_token.getApiToken(apisession, apitoken_id)` and consume the
returned `mistapi.APIResponse` object's `.data` attribute as a single dict (not a list).
The SDK module path published in the enriched doc is `mistapi.api.v1.self.api_token`
(singular `api_token`), distinct from the directory naming `apitokens` used in the
documentation tree. Both function name and module are case-sensitive.

**Rationale**:

- The enriched doc explicitly lists the SDK call as `mistapi.api.v1.self.api_token.getApiToken()`.
- The HTTP contract has exactly one required path parameter (`apitoken_id`) and no query
  parameters, request body, or pagination cursor -- the SDK signature must therefore be
  `(apisession, apitoken_id)`.
- The 200 response is a single JSON object (not an array), so the SDK returns
  `APIResponse.data` as a `dict`. No `mistapi.get_all()` pagination helper is needed.
- The response carries five fields: `id` (uuid), `name` (string), `key` (redacted
  fingerprint string), `created_time` (number, epoch seconds), `last_used` (nullable
  int32 epoch seconds).

**Alternatives Considered**:

- *Direct HTTP via `requests`*: Rejected -- the constitution mandates `mistapi` as the
  sole interface to Mist Cloud (Principle: Technology & Compatibility).
- *Use the list variant `listApiTokens` and filter client-side*: Rejected -- wasteful
  bandwidth, and the spec is explicit about the single-token endpoint. The list endpoint
  remains a related operation captured in the contract's "Related Endpoints" section.
- *Call `getApiToken()` per id in a batch loop*: Out of scope -- the spec describes a
  single-id read. Bulk fetch belongs in a future spec.

## Research Task 2: Primary Key Strategy

**Decision**: Register `getApiToken` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with
`type='natural_pk'` and `primary_key=['id']`. Add secondary indexes on `name` and
`last_used` for common viewer queries.

```python
'getApiToken': {
    'type': 'natural_pk',
    'primary_key': ['id'],
    'indexes': ['name', 'last_used'],
},
```

**Rationale**:

- The response includes `id` as a stable Mist-issued UUID (`"contentEncoding": "uuid"`,
  `"readOnly": true`) -- the textbook definition of a natural PK.
- The token id never changes across the token's lifetime; rotations create a *new* id, so
  `INSERT OR REPLACE ... ON CONFLICT(id)` is the correct upsert behavior.
- Time-series fields (`created_time`, `last_used`) are *attributes* of the same logical
  record, not partitioning dimensions -- the row is rewritten in place when `last_used`
  advances. Composite PK is therefore unnecessary.

**Alternatives Considered**:

- *composite_pk on `(id, last_used)`*: Rejected -- would create a new SQLite row every
  time the token is used, exploding the table without preserving useful history. If a
  history view is wanted later, it belongs in a separate `self_api_token_usage_log`
  table populated by a different endpoint.
- *auto_increment_with_unique*: Rejected -- the API does provide a stable identifier; the
  fallback strategy is only for endpoints that return aggregates without natural keys.

## Research Task 3: Output filename and SQLite table

**Decision**:

- **CSV filename**: `data/self_api_token_<apitoken_id>.csv` (one file per inspected
  token, parameterised by the prompted id so repeated lookups of different tokens do not
  overwrite each other).
- **SQLite table**: `self_api_tokens` (plural -- the table aggregates every token the
  user has ever inspected).
- **ArangoDB collection**: `self_api_tokens` (matches the SQLite table name for
  cross-backend grep-ability).

**Rationale**:

- The `data/` prefix matches the constitution's enforced output directory.
- Using the `apitoken_id` in the filename mirrors the per-device CSV pattern used by
  other single-object viewers and prevents accidental overwrite when a user inspects
  several tokens in succession.
- The SQLite table is shared across runs so the user can query "which tokens have I
  inspected and when were they last used" in a single SELECT. The natural PK guarantees
  no duplicate rows.

**Alternatives Considered**:

- *Single CSV `self_api_tokens.csv` rewritten each run*: Rejected -- destroys the
  diff-friendly per-run artifact and forces the user to rely on SQLite for history.
- *Nested directory `data/self/api_tokens/<id>.csv`*: Rejected -- the existing
  `DataExporter` writes flat into `data/` and creating sub-directories would require a
  cross-cutting change out of scope here.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **96**, placed in the Interactive Safe / Viewers cluster
(60-96), with the label `View single API token (self)`.

**Rationale**:

- The MistHelper menu map (per `.github/copilot-instructions.md`) groups operations as
  follows: 60-72 site devices, 73-79 insights, 80-91 stats, **92-96 viewers**, 97-101
  resource-intensive. A single-record read of metadata for an account-owned object is
  exactly a viewer.
- 96 is the highest unused slot in the viewers cluster as documented; placing the new
  item there keeps the resource-intensive boundary at 97 intact.
- Sibling self-* endpoints (`getSelf`, `listApiTokens`, `getSelfLogs`) currently lack a
  dedicated cluster; clustering them in the viewers range under a shared
  `SelfAccountUtils` class is a natural starting point.

**Alternatives Considered**:

- *Misc Safe Org Exports 56-59*: Rejected -- those slots are reserved for *org-scoped*
  exports. The self/apitokens endpoint is account-scoped (no `org_id` parameter).
- *Resource-Intensive 97-101*: Rejected -- a single GET of one record has no
  long-running characteristic.
- *Defer numbering to tasks.md*: Rejected -- the plan must propose a concrete number per
  the instructions; tasks.md may shift it if a parallel branch collides, but the plan
  records the intent.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**:

| Value           | Source           | Prompt? | Notes                                       |
|-----------------|------------------|---------|---------------------------------------------|
| `MIST_HOST`     | `.env`           | No      | Already consumed by `mistapi.APISession`    |
| `MIST_API_TOKEN`| `.env`           | No      | Bearer auth -- never logged                 |
| `apitoken_id`   | User (interactive) or `--menu 96 --apitoken-id <uuid>` (non-interactive) | Yes -- via `safe_input()` with `context="self_api_token:apitoken_id"` | Validated against UUID regex before SDK call |

A `--test` mode helper resolves a default `apitoken_id` by calling the sibling
`listApiTokens` endpoint once and reading the first returned id; this keeps
`python MistHelper.py --test` non-interactive without baking a real id into the repo.

**Rationale**:

- Only one runtime value is unknown until the user supplies it -- the token id.
- `safe_input()` is the constitution-mandated prompt path for SSH/container EOF safety.
- The `.env` values are the existing global session config; reusing them avoids a
  second prompt and prevents the user from accidentally typing the secret into the
  terminal.
- Auto-discovery via `listApiTokens` is preferred over a fixed `MIST_API_TOKEN_ID`
  `.env` variable because the test admin's token ids differ per environment and we do
  not want to persist a token id in `.env.example`.

**Alternatives Considered**:

- *Prompt for `MIST_HOST` and `MIST_API_TOKEN` interactively*: Rejected -- duplicates
  the `.env` mechanism and risks logging the secret if the user types it at a prompt
  that may be echoed.
- *Take `apitoken_id` as a positional argv only (no interactive prompt)*: Rejected --
  breaks the menu-driven UX for junior NOC engineers, which is the target audience.
- *Persist a default `MIST_API_TOKEN_ID` in `.env.example`*: Rejected -- pollutes the
  example file with an identifier that will not exist in any other admin's account.
