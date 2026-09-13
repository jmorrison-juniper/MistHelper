# Phase 0 Research: getOrg128TRegistrationCommands

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Source**: `documentation/api/orgs/GET_orgs_org_id_128routers_register_cmd.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke the SDK via the dotted module path
`mistapi.api.v1.orgs.128routers.register_cmd.getOrg128TRegistrationCommands(
mist_session, org_id, ttl=None, asset_ids=None)`. The first positional
argument is the active `mistapi.APISession`; the second is the org UUID;
`ttl` and `asset_ids` are passed as keyword arguments only when the user
supplies them, so the SDK falls back to its server-side defaults (1 year
TTL, no asset filter) when the prompts are left blank.

**Rationale**: The enriched per-endpoint doc
(`documentation/api/orgs/GET_orgs_org_id_128routers_register_cmd.md`)
states:

- Path `GET /api/v1/orgs/{org_id}/128routers/register_cmd`
- Path param `org_id` (required, string)
- Query param `ttl` (integer, optional, default 31_536_000 seconds = 1 year)
- Query param `asset_ids` (array, optional; the doc explicitly recommends
  HTTP body over headers for long lists, but the SDK already routes long
  arrays correctly so the caller does not have to think about it)
- 200 response body shape:
  `{ conductor_cmd: string, registration_code: string, router_shell_cmd: string }`
- Error responses: 400 (bad syntax), 401 (unauthorized), 403 (permission
  denied), 404 (not found), 429 (rate limit)
- The endpoint is flagged **DEPRECATED** at the top of the doc; a future
  Mist release may remove it.

The `mistapi` SDK module mirrors the OpenAPI path 1:1 so the function is
located at `mistapi.api.v1.orgs.128routers.register_cmd`. Python module
names cannot start with a digit, so `mistapi` exposes the
`128routers` package via an aliased import internally; callers reach it
through `getattr` or a wildcard `from mistapi.api.v1.orgs import *` style.
The pragmatic call pattern used elsewhere in `MistHelper.py` is:

```python
from mistapi.api.v1.orgs import _128routers as routers_128t_module  # alias the digit-prefixed package
response = routers_128t_module.register_cmd.getOrg128TRegistrationCommands(
    self.mist_session, org_id, ttl=ttl, asset_ids=asset_ids
)
```

**Alternatives Considered**:

1. *Raw `requests` call to `/api/v1/orgs/{org_id}/128routers/register_cmd`*
   -- Rejected because the constitution mandates `mistapi` as the sole
   permitted interface to Mist Cloud. Bypassing the SDK loses adaptive
   retries, rate limiting, and the standard `APIResponse` envelope.
2. *Helper wrapper that builds the URL by hand and uses the SDK only for
   auth* -- Rejected as a hidden wrapper that violates Principle II.
3. *Make `ttl` always send the documented default of 31_536_000 even when
   the user does not specify a value* -- Rejected because it locks future
   server-side default changes out of the user experience; passing `None`
   lets the upstream API choose.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` on `(org_id, registration_code)`. The
canonical entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` is:

```python
"getOrg128TRegistrationCommands": {                                 # operation id keyed for upsert
    "type": "composite_pk",                                          # multiple natural cols form the key
    "primary_key": ["org_id", "registration_code"],                  # unique per org per minted token
    "indexes": ["org_id", "registration_code"],                       # accelerate per-org lookups
},
```

**Rationale**: The response carries no server-provided UUID, but
`registration_code` is server-minted and unique per call (the doc gotcha
says the command is time-sensitive and may expire, which implies a fresh
code per request). Pairing it with `org_id` keeps the key safe even in
the unlikely event Mist reuses a code across tenants. A composite key
with `INSERT OR REPLACE` semantics means each new call from the same org
either inserts a new row (new code) or replaces the prior row if Mist
ever returns the same code for the same TTL window. `org_id` is also a
natural foreign key to the `org_sites` summary table populated by
existing menu items, enabling JOIN-based reporting in SQLite.

**Alternatives Considered**:

1. *`natural_pk` on `registration_code` alone* -- Rejected because it
   relies on global uniqueness across orgs, which the API contract
   neither promises nor refutes; composite is safer.
2. *`auto_increment_with_unique` with a `misthelper_internal_id`* --
   Rejected because the response has a perfectly good natural key
   (`registration_code`); using auto-increment would produce duplicate
   rows on every re-run, defeating the upsert goal.
3. *Adding `requested_at` (a MistHelper-side timestamp) to the PK* --
   Rejected because the SQLite history of registration commands is
   intentionally point-in-time; if historical retention is needed later,
   a separate `org_128t_registration_commands_history` table can be
   layered on top without changing this PK strategy.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV / JSON output filename: `org_128t_registration_commands.csv`
  (and `.json` from `DataExporter` automatically). Written to `data/`.
- SQLite table name: `org_128t_registration_commands`.
- `api_function_name` passed to
  `DataExporter.write_with_format_selection()`:
  `"getOrg128TRegistrationCommands"`.

**Rationale**: MistHelper's naming convention for read-only org exports
is `<scope>_<noun_phrase>.csv` and the matching SQLite table is the same
string. `128t` (lowercase, no separator between the digit and the `t`)
mirrors the path token `128routers` and matches how Mist itself spells
the product family in user-facing docs. `registration_commands` is
plural because the response carries multiple distinct command strings
(`conductor_cmd`, `router_shell_cmd`) even though a single row is
returned per call.

**Alternatives Considered**:

1. *`org_ssr_register_cmd.csv`* -- Rejected because spec 645
   (`getOrgSsrRegistrationCommands`) owns the `org_ssr_*` namespace and
   the two endpoints, while sibling, are not the same shape.
2. *Splitting into two files (one per command string)* -- Rejected
   because the three fields are semantically a single bundle keyed by
   `registration_code`; splitting them would force JOINs for every
   downstream consumer.

## Research Task 4: Menu Category Placement and Next Available Number

**Decision**: Place the new item at menu number **96** in the Safe Org
Exports / Org-Device-SSR sub-cluster of `MistHelper.py`. Label the menu
entry `Export 128T/SSR registration commands (DEPRECATED upstream)` so
operators see the deprecation flag at selection time.

**Rationale**: The category guidance in
`.github/copilot-instructions.md` puts 1-59 in Safe Org Exports and
60-96 in Interactive Safe (Site / Insights / Viewers), with 97-101
flagged Resource Intensive. 96 is the last slot in the Interactive Safe
range and currently sits at the viewer boundary. Spec 500
(`getOrgLicenseAsyncClaimStatus`) already proposed 95, and specs 595
(`getOrgAosRegisterCmd`) and 645 (`getOrgSsrRegistrationCommands`) will
need adjacent slots. Using 96 keeps the three SSR-family read endpoints
contiguous (95-97 once 595 and 645 are placed) and stops just short of
the resource-intensive boundary. If a parallel feature branch lands at
96 first, the next free integer in the same cluster is used and the
shift is recorded in `tasks.md`. The exact assignment is not load-bearing
for any other artifact in this plan -- only the menu registration line
in `MistHelper.py` reads it.

**Alternatives Considered**:

1. *Slot 56-59 (Misc safe org exports)* -- Rejected because those slots
   are reserved for non-device-adoption miscellany; putting a 128T
   adoption read there fragments the device-onboarding cluster.
2. *Slot in 154-194 (Destructive cluster)* -- Rejected because the
   endpoint is strictly read-only. Destructive numbering would mislead
   operators about safety.
3. *Append at the next free integer above 194* -- Rejected because the
   menu remains coherent only while numbers stay within the documented
   cluster ranges; sprawling beyond 194 forces a global menu reflow.

## Research Task 5: Required User Prompts

**Decision**: Prompt for three inputs, in this order, each through
`safe_input()`:

1. `org_id` -- required. Resolved either from a typed prompt or from
   `os.environ.get("MIST_ORG_ID")` if the env var is set and the user
   accepts the default. The prompt context label is
   `"org_128t_register_cmd:org_id"`.
2. `ttl` -- optional. Accept a blank line to send `None` to the SDK
   (server default = 1 year). If provided, coerce to `int`, then bound
   to `60 <= ttl <= 31_536_000`. The prompt context label is
   `"org_128t_register_cmd:ttl"`.
3. `asset_ids` -- optional. Accept a blank line for "no filter". If
   provided, split on commas, strip whitespace, drop empty entries, and
   pass the resulting list to the SDK. The prompt context label is
   `"org_128t_register_cmd:asset_ids"`.

Credentials (`MIST_HOST`, `MIST_API_TOKEN`) are loaded from `.env` by
the existing `mistapi.APISession` bootstrap -- they are **never**
prompted for and **never** logged.

**Rationale**: The endpoint declares one required path parameter
(`org_id`) and two optional query parameters (`ttl`, `asset_ids`).
Prompting for all three matches the read-only menu pattern documented
in `.github/copilot-instructions.md` and the reference plan
(spec 500). Sourcing `org_id` from `.env` as the default keeps
non-interactive `--test` runs working without changing the prompt
contract.

**Alternatives Considered**:

1. *Prompt only for `org_id` and always omit `ttl` / `asset_ids`* --
   Rejected because it removes documented user agency over the TTL,
   which is the entire point of the query parameter for short-lived
   registration windows.
2. *Accept a JSON blob for `asset_ids`* -- Rejected as user-hostile;
   comma-separated values are easier to paste in an SSH session and
   match how `MistHelper.py` already handles multi-value inputs in
   adjacent menu items.
3. *Default `ttl` client-side to 3600 (1 hour)* -- Rejected because
   it overrides the documented server default; the SDK's `None` path
   is the only way to honour future server-side changes.
