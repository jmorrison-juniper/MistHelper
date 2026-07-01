# Phase 0 Research: getOrgWebhook

**Feature**: 653-mist-get-org-webhook
**Endpoint**: `GET /api/v1/orgs/{org_id}/webhooks/{webhook_id}`
**Reference doc**: `documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke `mistapi.api.v1.orgs.webhooks.getOrgWebhook(mist_session,
org_id, webhook_id)`. The SDK returns a `mistapi.APIResponse` whose `.data`
attribute is a single JSON object (not a list), matching the OpenAPI schema
documented in the enriched per-endpoint markdown. There is no pagination and
no query parameters -- one call yields the complete webhook configuration
including sensitive fields (`secret`, `oauth2_client_secret`,
`oauth2_password`, `splunk_token`) that the list endpoint (menu 47) does not
expose in full.

**Rationale**: The enriched documentation at
`documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id.md` explicitly
names this SDK entry point at line 208 (`mistapi.api.v1.orgs.webhooks.getOrgWebhook()`).
The pagination section at line 199-200 confirms "Not paginated." The 200
response schema (lines 33-186) is a single `type: object` with roughly 22
properties including `id`, `org_id`, `type`, `url`, `topics` (array), and the
sensitive credential fields. The Gotchas section at line 214-216 confirms
that webhook secrets are included in the response for HMAC verification --
which is precisely why the per-item GET exists as a distinct operation from
the list.

**Alternatives Considered**:

1. Direct `requests.get()` call bypassing `mistapi` -- rejected. Constitution
   Principle II mandates `mistapi` as the sole permitted Mist Cloud interface,
   and rewriting authentication, retry, and adaptive-delay logic in this menu
   item would duplicate work already handled centrally.
2. Reusing the menu 47 `listOrgWebhooks` output and filtering client-side --
   rejected. The list endpoint does not return `secret`,
   `oauth2_client_secret`, `oauth2_password`, or `splunk_token` in full form.
   Only the per-item GET returns the material needed for HMAC verification and
   webhook debugging.

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with `primary_key = ['id']`. Indexes on
`org_id`, `name`, `type`, and `enabled`.

**Rationale**: The response includes a stable server-issued UUID at the `id`
field (documented lines 78-86: `"description": "Unique ID of the object
instance in the Mist Organization"`, `contentEncoding: uuid`, `readOnly:
true`). This is the same key structure used by other webhook-related tables
and matches the pattern for entities with stable UUIDs described in
`.github/copilot-instructions.md` under the "Database Strategy" section
(`sites`, `devices`, `templates` all use natural_pk). Upsert via
`INSERT OR REPLACE` on the natural key gives clean idempotent re-runs. The
secondary indexes on `org_id`, `name`, `type`, and `enabled` support the two
most common downstream queries: "show me all webhooks for org X" and "show me
disabled Splunk webhooks I can safely delete."

**Alternatives Considered**:

1. `composite_pk` on `(org_id, id)` -- rejected. The Mist `id` field is
   already globally unique across the Mist Cloud; scoping the PK to
   `(org_id, id)` adds no protection and makes joins slightly noisier.
2. `auto_increment_with_unique` -- rejected. This strategy is reserved for
   endpoints without a stable server-issued key (e.g. license summaries).
   Webhooks have a canonical UUID from the API, so a synthetic surrogate is
   unnecessary and would break clean cross-run upserts.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV / JSON output filename: `data/org_webhook_detail_<webhook_id>.csv`
  (short-form: the org context is captured in the row's `org_id` column;
  filename is keyed by the webhook UUID because that is what the user
  supplied).
- SQLite table name: `org_webhook_detail`.
- ArangoDB collection name: `org_webhook_detail`; graph edge
  `webhook_detail_of_org` from the row to the parent org vertex per the spec
  188 polyglot pattern.

**Rationale**: The `org_webhook_detail` name reads naturally next to the
existing `org_webhooks` collection produced by menu 47 (`listOrgWebhooks`).
Suffixing the CSV filename with the webhook UUID prevents overwrite when the
user drills into multiple webhooks in one session. The table name is
singular-per-record (matches the endpoint returning a single object) but
retains the `org_webhook_detail` plural-ish form so the two operations
`listOrgWebhooks` (menu 47, table `org_webhooks`) and `getOrgWebhook`
(menu 96, table `org_webhook_detail`) remain visually distinct at
`ls data/` and `SELECT name FROM sqlite_master` time.

**Alternatives Considered**:

1. `webhooks_by_id` -- rejected. Ambiguous when other org/site scoped webhook
   tables land later.
2. Overwriting `data/org_webhook_detail.csv` on every run -- rejected. Users
   who inspect two webhooks in one session would lose the first record.
3. Embedding both `org_id` and `webhook_id` in the filename
   (`org_webhook_detail_<org_id>_<webhook_id>.csv`) -- rejected as too long;
   the SQLite row already carries `org_id`.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Menu number **96**, placed in the interactive-safe cluster
(60-96) immediately adjacent to the existing menu 47 (`listOrgWebhooks`) in
functional intent but numerically at the end of the interactive-safe range.

**Rationale**: `.github/copilot-instructions.md` documents the menu ranges:
1-59 safe org exports, 60-96 interactive safe, 97-101 and 153 resource
intensive, 102-123 WebSocket, 124-150 interactive, 151-152 continuous,
154-194 destructive. Menu 47 (`listOrgWebhooks`) sits in the org config /
admin sub-cluster (42-50). The new `getOrgWebhook` operation cannot fit
alongside 47 because it requires an interactive per-record prompt for
`webhook_id`, which places it in the interactive-safe cluster. Menu 96 is
the last documented interactive-safe slot (viewers 92-96) and it is the next
free integer per the review of adjacent spec branches (spec 500 already
reserved menu 95). If 96 is subsequently taken by an in-flight branch at
task-generation time, the fallback is the next free integer in the same
cluster (97 is out because 97-101 are resource-intensive) -- so the
practical fallback is coordinated at merge time by the sequential-merge
protocol in the git workflow.

**Alternatives Considered**:

1. Insert as menu 48 (immediately after `listOrgWebhooks` at menu 47) --
   rejected. That would push the entire 48+ range up by one, breaking every
   downstream operation number, README, CHANGELOG, and user muscle memory.
   MistHelper never re-numbers existing menu items.
2. Place in the 124-150 "Interactive" cluster -- rejected. Those slots are
   reserved for diagnostics, management, and tools that can mutate device
   state, not simple read-only lookups.
3. Place in the destructive cluster -- rejected outright. The operation is
   HTTP GET only with no mutation.

## Research Task 5: Required User Prompts

**Decision**: Two prompts, both via `safe_input()`:

1. `org_id` -- prompt reads
   `"Enter org_id (default: MIST_ORG_ID from .env)"`. The method reads the
   optional `MIST_ORG_ID` variable from `.env` via the existing
   `os.getenv("MIST_ORG_ID")` pattern used elsewhere in `MistHelper.py`; if
   present, an empty user reply accepts the default. If the environment
   variable is absent and the user supplies no value, the method logs a
   WARNING and returns early.
2. `webhook_id` -- prompt reads
   `"Enter webhook_id (UUID from menu 47 output)"`. There is no default; an
   empty reply logs a WARNING and returns early.

**Rationale**: The API path template has two required path parameters and no
query parameters (per
`documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id.md` lines 20-24
and 26-27). The `MIST_ORG_ID` optional default matches the pattern used by
the license-async claim status menu (spec 500) and other adjacent
interactive-safe items, reducing keystrokes for engineers who work in a
single org for a whole session. The user is expected to have run menu 47
first to obtain the desired `webhook_id`; the prompt string points them
there. No credential-shaped prompts (token, secret, password) are needed --
authentication is entirely `.env` -> `mistapi.APISession`.

**Alternatives Considered**:

1. Prompt for `site_id` -- rejected. The endpoint path is `orgs`, not
   `sites`. Site scope is derived server-side and returned as a `readOnly`
   field in the response (`site_id`, lines 150-157 of the enriched doc).
2. Prompt for `type` filter -- rejected. There is no query parameter for
   filtering; the endpoint is a single-record GET keyed by
   `webhook_id`.
3. Silent default of `webhook_id` from the most recent menu 47 output --
   rejected as too magical. The user must explicitly name which webhook they
   want to inspect, because inspecting the wrong webhook reveals the wrong
   secret material.
