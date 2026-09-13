# Phase 0 Research: countOrgWanClients

All five research tasks resolved. No `NEEDS CLARIFICATION` markers remain.

## Research Task 1 -- SDK function signature & behavior

**Decision.** Use `mistapi.api.v1.orgs.clients_-_wan.countOrgWanClients(mist_session, org_id, distinct=None, start=None, end=None, duration="1d", limit=100)`.

**Rationale.** The enriched per-endpoint doc at
`documentation/api/orgs/GET_orgs_org_id_wan_clients_count.md` lists the
operation as `mistapi.api.v1.orgs.clients_-_wan.countOrgWanClients()` with
path parameter `org_id` (required) and query parameters `distinct`,
`start`, `end`, `duration` (default `1d`), `limit` (default `100`,
integer). The response is an aggregate count envelope with fields
`distinct`, `end`, `limit`, `results[]`, `start`, `total`. Each
`results[]` entry has a required `count` field plus arbitrary string-valued
additional properties whose names depend on the `distinct` value passed in.
Pagination is supported via `limit` and `page` query parameters.

**Alternatives considered.**
1. *Raw HTTPS via `requests`*: rejected -- bypasses the `mistapi` session
   abstraction (token handling, base URL, retry hooks).
2. *Wrap as an async coroutine*: rejected -- the rest of MistHelper is
   synchronous; adding an event loop here would violate consistency.
3. *Iterate pages eagerly into a single list*: accepted -- consistent with
   how adjacent count endpoints already drain their pagination.

## Research Task 2 -- Primary Key Strategy

**Decision.** `auto_increment_with_unique` with surrogate
`misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT` and unique
constraint on `(org_id, distinct_field, distinct_value, start_epoch, end_epoch)`.

**Rationale.** The API does not return a stable identifier per count
bucket. The bucket *is* identified by the combination of the requested
`distinct` field, its value (carried as an additional property), and the
time window. Re-running the menu item with the same parameters must
upsert rather than duplicate; the project-standard pattern for this case
(documented in `.github/copilot-instructions.md` under "Hybrid Primary
Key System") is `auto_increment_with_unique` with a tuple unique index.

**Alternatives considered.**
1. *`natural_pk` on the bucket value alone*: rejected -- bucket values
   collide across time windows and across distinct fields.
2. *`composite_pk` on `(org_id, distinct_field, distinct_value, start_epoch, end_epoch)`*:
   workable but rejected because the `distinct_value` field is dynamic
   (its column name changes with the `distinct` query argument), which
   makes a declarative composite PK harder to express. The
   surrogate-with-unique pattern is cleaner here.

## Research Task 3 -- Output filename and SQLite table

**Decision.**
- CSV filename: `data/count_org_wan_clients.csv`
- SQLite table: `count_org_wan_clients`

**Rationale.** Matches the project convention `data/<operationId_snake>.csv`
and `<operationId_snake>` SQLite table naming, which keeps `DataExporter`
fan-out unambiguous and grep-friendly. The `DataExporter` flatten step
will pivot the dynamic additional-property field name (e.g. `mfg`,
`hostname`, `vendor`) into a single `distinct_value TEXT` column alongside
the count, and capture the original `distinct` request parameter as
`distinct_field TEXT`.

**Alternatives considered.**
1. *Per-distinct CSV files*: rejected -- explodes the file count and
   breaks the `api_function_name` mapping in `DataExporter`.
2. *Embed in `wan_clients` table*: rejected -- search and count
   endpoints persist into distinct tables for clarity.

## Research Task 4 -- Menu category placement and next available menu number

**Decision.** Menu **230**, placed in the "Safe Org Exports" category
alongside other org-level count and search wrappers.

**Rationale.** Current MistHelper occupies menu numbers 1-194; the
OpenAPI cataloging series (specs 500-907) is reserved the contiguous
range 195+ in sequential order. Spec 535 is the 36th entry in the
series (535 - 500 + 1 = 36), and with menu 195 reserved for spec 500,
spec 535 maps cleanly to menu **230** (195 + 35). The category fits
"Safe Org Exports" because the endpoint is read-only, org-scoped, and
returns aggregate counts -- conceptually adjacent to the existing
`searchOrgWanClients` and other count operations.

**Alternatives considered.**
1. *Append at the end (menu 195) regardless of spec order*: rejected --
   creates collisions when multiple agents in the spec-535-and-siblings
   batch all claim "next available."
2. *Place in "Interactive Safe" (60-96 band)*: rejected -- that band is
   for site-scoped/interactive operations, not org-scoped exports.

## Research Task 5 -- Required user prompts (which IDs from the user, which from .env)

**Decision.** Required prompts and their sources:

| Field    | Source                  | Notes                                                    |
|----------|-------------------------|----------------------------------------------------------|
| API token | `.env` (`MIST_API_TOKEN`) | Never prompted; loaded by `mistapi` session.            |
| `org_id` | `.env` (`MIST_ORG_ID`) with `safe_input()` override | Prompt: `"Org ID [<.env value>]: "`. |
| `distinct` | `safe_input()` | Prompt: `"Distinct attribute (optional, blank for default): "`. |
| `start`  | `safe_input()`          | Prompt: `"Start time (epoch or relative like -1d, blank=skip): "`. |
| `end`    | `safe_input()`          | Prompt: `"End time (epoch, relative, or 'now', blank=skip): "`. |
| `duration` | `safe_input()`        | Prompt: `"Duration (default 1d): "`; empty -> default `1d`. |
| `limit`  | `safe_input()`          | Prompt: `"Limit (default 100, max 1000): "`; empty -> default 100. |

All prompts are wrapped in `safe_input(prompt, context="count_org_wan_clients")`
so an EOF (SSH/container disconnect) exits 0 without traceback.

**Rationale.** The org_id is the only universally required identifier
and is the single field most users want pre-populated from `.env`.
The query parameters are all optional and benefit from interactive
override per run (especially `distinct`, which controls the bucket
dimension).

**Alternatives considered.**
1. *Read everything from `.env` (no prompts)*: rejected -- forces the
   user to edit `.env` to switch the `distinct` dimension, defeating
   the interactive use case.
2. *Force every prompt with no defaults*: rejected -- punishes the
   junior NOC engineer audience documented in `agents.md`.
