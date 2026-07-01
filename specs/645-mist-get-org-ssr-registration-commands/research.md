# Phase 0 Research: getOrgSsrRegistrationCommands

**Feature**: `645-mist-get-org-ssr-registration-commands`
**Source docs**: `documentation/api/orgs/GET_orgs_org_id_ssr_register_cmd.md`
**Spec**: [spec.md](./spec.md)

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke the endpoint through the `mistapi` Python SDK as
`mistapi.api.v1.orgs.ssr.register_cmd.getOrgSsrRegistrationCommands(apisession, org_id,
ttl=<int|None>, asset_ids=<list[str]|None>)`. The SDK returns a `mistapi.APIResponse`
whose `.data` attribute is the JSON body -- for this endpoint a single dict with three
string keys: `conductor_cmd`, `registration_code`, `router_shell_cmd`.

**Rationale**: The enriched per-endpoint doc `documentation/api/orgs/GET_orgs_org_id_ssr_register_cmd.md`
specifies:
- Path: `GET /api/v1/orgs/{org_id}/ssr/register_cmd`
- Path params: `org_id` (required string)
- Query params: `ttl` (optional int, default 31536000 seconds = 1 year) and `asset_ids`
  (optional array; the doc notes "Prefer HTTP body over headers ... to avoid header size
  limits" but the `mistapi` SDK layer handles the correct transport)
- Response 200: `{conductor_cmd, registration_code, router_shell_cmd}` -- all strings
- Not paginated, standard Mist rate limits, no request body

The `mistapi.api.v1.orgs.ssr.register_cmd` module is the canonical location per the spec.
The SDK doc lists the tag as `Orgs Devices - SSR` and MistHelper already imports the
`mistapi` package globally; no new import path is needed.

**Alternatives Considered**:
- **Direct `requests.get()` call**: Rejected. Constitution Principle II requires all
  Mist Cloud interaction to go through the `mistapi` SDK to inherit retry, back-off,
  logging, and authentication uniformly.
- **Async batch retrieval across many orgs**: Rejected. The current UX is
  one-org-per-invocation, matching every sibling menu item. Multi-org batching would
  double the surface area and violate the 5-Item Rule budget on the new method.

## Research Task 2: Primary Key Strategy

**Decision**: `auto_increment_with_unique`. The primary key is the internal auto-increment
column `misthelper_internal_id` with a UNIQUE constraint on
`(org_id, registration_code, fetched_at)`. The natural row-level identity is a
combination of the org and the registration secret at the moment of retrieval, but that
secret is a short-lived generated value not previously stored anywhere in the Mist system,
so it is not truly a "natural" business key in the database-normalization sense.

**Rationale**:
- The endpoint returns a single object with no `id` field. It is not an entity in the
  Mist data model; it is a *rendered command* generated at request time.
- Each invocation produces a fresh `registration_code` when `ttl` is supplied, so back-to-
  back calls yield different rows even for the same `org_id`. Using `org_id` alone as the
  key would collapse history and defeat the audit-trail benefit of persisting the row.
- Using a composite of `(org_id, registration_code)` alone would still allow duplicate
  rows across TTL renewals with different `fetched_at` timestamps; adding `fetched_at`
  disambiguates and preserves audit history.
- `auto_increment_with_unique` is already the documented default for endpoints that lack
  a stable server-side identifier (constitution "Adding New Menu Operations" section and
  MistHelper `ENDPOINT_PRIMARY_KEY_STRATEGIES` conventions).

**Alternatives Considered**:
- **`natural_pk` on `org_id`**: Rejected. Overwrites prior fetch on every rerun, losing
  the ability to correlate an old registration secret with the device that consumed it.
- **`natural_pk` on `registration_code`**: Rejected. Not a business key; it is a
  short-lived credential and using it as PK would leave orphaned rows when TTL expires
  and it recycles.
- **`composite_pk` on `(org_id, registration_code, fetched_at)`**: Rejected only because
  MistHelper's composite_pk convention is reserved for API responses that carry the
  timestamp field themselves (e.g., events, stats). Since `fetched_at` is a client-side
  insertion, `auto_increment_with_unique` is the more honest classification.

## Research Task 3: Output filename and SQLite table

**Decision**:
- CSV filename: `data/org_ssr_registration_commands_<org_id>_<YYYYMMDD_HHMMSS>.csv`
- SQLite table: `org_ssr_registration_commands`
- ArangoDB collection: `org_ssr_registration_commands`
- Redis key prefix: `org:{org_id}:ssr:register_cmd:<epoch>`

**Rationale**: The naming mirrors adjacent SSR / device-utility operations
(`org_128routers_registration_commands`, `org_devices_ssh_command_history`) and keeps the
operationId shape (`getOrgSsrRegistrationCommands` -> `org_ssr_registration_commands`).
Filename embeds the `org_id` and a UTC timestamp so repeated runs never overwrite each
other on disk, while SQLite/ArangoDB de-duplicate via the PK strategy above. The Redis
key includes an epoch suffix so an operator can inspect the exact fetch cheaply.

**Alternatives Considered**:
- **`ssr_register_cmd` short form**: Rejected. Loses the `org_` prefix that all other org-
  scoped exports use, breaking sort order in `data/`.
- **Omitting `<org_id>` from the CSV name**: Rejected. Would collide when the operator
  runs the menu against multiple orgs in a single day.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **95**, placed inside the Safe Org Exports / Config / Admin
cluster (menu 42-59 per the copilot instructions "Menu Categories" table, extended by
recent additions through the low 90s). This is a strictly read-only operation with no
destructive side effect, so it does NOT belong in the 154-194 destructive block.

**Rationale**:
- The menu is a GET call that returns short-lived credential material for adopting an SSR
  into an org. It behaves exactly like every other "safe org export" -- a read that
  writes a row to `data/`.
- Menu 95 is the next unused slot below the resource-intensive band at 96-101 and
  adjacent to the recently-planned menu 95 for `GetOrgLicenseAsyncClaimStatus` (spec
  500). At `/speckit.tasks` time, `list_free_menu_numbers()` must be re-run to detect any
  cross-branch collision; if 95 is claimed, the implementation moves to the next free
  integer in the 51-95 Safe Exports cluster.
- The label reads "Get SSR Registration Command (for router adoption)" in the menu so
  the audience (junior NOC engineers) knows what problem it solves without needing to
  read the OpenAPI spec.

**Alternatives Considered**:
- **Menu in the 128T / 155-160 range**: Rejected. That range is the destructive firmware
  / reboot cluster; a safe GET does not belong there.
- **Menu 102-115 (WebSocket show commands)**: Rejected. Those slots are for streaming
  device output, not one-shot org config reads.

## Research Task 5: Required user prompts

**Decision**: Prompt for exactly three inputs via `safe_input()`, in this order:

1. `org_id` -- required. Default suggested from `.env` var `MIST_ORG_ID` when present.
   Context tag: `"ssr_register_cmd:org_id"`. UUID-validated before the SDK call.
2. `ttl` -- optional. Blank input = SDK default (1 year). Numeric input is bounds-checked
   (1 <= ttl <= 31536000). Context tag: `"ssr_register_cmd:ttl"`.
3. `asset_ids` -- optional. Blank input = fetch a general (non-asset-restricted) token.
   Comma-separated UUID list otherwise; each token is UUID-validated. Context tag:
   `"ssr_register_cmd:asset_ids"`.

**Rationale**:
- `.env` supplies the API token (`MIST_API_TOKEN`) and the Mist host (`MIST_HOST`) --
  the operator never types these. `MIST_ORG_ID` is optional in `.env`; when present it
  seeds the prompt default so the operator can press Enter to accept.
- `ttl` and `asset_ids` are true UX choices, not credentials, so they belong at the
  prompt. Defaulting `ttl` to blank keeps the common "1-year adoption token" path
  effortless.
- `safe_input()` is mandated by spec.md FR-002 and by constitution Principle III for SSH
  / container EOF safety.

**Alternatives Considered**:
- **Pull `org_id` silently from `.env`**: Rejected. Operators frequently work across
  multiple orgs; a silent org selection would generate the wrong registration secret
  and could ship it to the wrong tenant.
- **Prompt for `apisession` credentials interactively**: Rejected. `.env` + `mistapi`
  session bootstrap is the documented and enforced pattern; interactive credential
  entry would break `--test` and container automation.
