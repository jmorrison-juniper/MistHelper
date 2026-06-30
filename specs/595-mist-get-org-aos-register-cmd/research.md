# Phase 0 Research: getOrgAosRegisterCmd

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_aos_register_cmd.md`
(enriched OpenAPI doc) and `spec.md` (authoritative feature contract).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.aos.register_cmd.getOrgAosRegisterCmd(apisession,
org_id)`. The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the
parsed JSON body. The body is a single JSON object (not a list, not paginated) with
exactly one top-level key per the enriched doc:

- `cli_commands` (string) -- AOS-specific CLI command block that can be pasted directly
  into an AOS device to register it with Mist. Includes the registration challenge
  token and the configuration commands.

Required path parameter: `org_id` (UUID string). No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.devices_-_aos.getOrgAosRegisterCmd()`, but the dash + hyphen
characters in `devices_-_aos` are not legal Python module names; that string is the
OpenAPI tag rendered into the doc, not an importable path. The mistapi SDK organizes
modules by URL path, not OpenAPI tag (verified by the convention used across the SDK:
`mistapi.api.v1.orgs.claim.status`, `mistapi.api.v1.orgs.sites`, etc., each mirror the
URL). The spec.md (the authoritative feature contract) names
`mistapi.api.v1.orgs.aos.register_cmd`, which matches the URL one-for-one. Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.aos import register_cmd; help(register_cmd)"`
inside the venv. If the SDK function name is actually capitalized (`GetOrgAosRegisterCmd`)
rather than camelCase (`getOrgAosRegisterCmd`) the implementation step adjusts the
single call site -- no plan change needed.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/aos/register_cmd`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`...orgs.devices_-_aos...`).* Rejected -- the
   string is not a legal Python identifier and the SDK organizes by URL path, not tag.
3. *Wait until SDK introspection at implement time before choosing a path.* Rejected --
   the URL-derived path is deterministic and unambiguous; deferring the decision adds
   no value.

## Research Task 2: Primary Key Strategy

**Decision**:
Use the **`auto_increment_with_unique`** strategy in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`:

- Surrogate PK: `misthelper_internal_id` (auto-increment integer).
- UNIQUE constraint: `(org_id, generated_at_utc)` -- prevents accidental duplicates
  from rapid re-invocations within the same UTC second but otherwise allows every
  invocation to be archived.

`org_id` is injected by MistHelper (the API does not echo it back). `generated_at_utc`
is the MistHelper client-side ISO8601 UTC timestamp of the poll.

**Rationale**:
The endpoint returns a registration *challenge* that is **time-sensitive** (per the
enriched doc's Gotchas section: "The registration command is time-sensitive"). Each
invocation produces a fresh, distinct command intended to be used once. Treating each
call as a new historical record (rather than upserting an evergreen row) is the
correct semantic: an operator who polls today and again tomorrow gets two valid
commands and may want both archived for audit. The unique constraint on
`(org_id, generated_at_utc)` is purely defensive against accidental rapid re-invocation
inside the same second; in practice every meaningful poll produces a new row.

The natural body has no stable identifier -- `cli_commands` itself is a long opaque
string that changes every call and is not suitable as a key. There is no
`scheduled_at` or `id` field in the response.

**Alternatives Considered**:

1. *`natural_pk` on `cli_commands`.* Rejected -- the string is long, opaque, and
   contains the registration token; using it as a key would index the entire token
   into SQLite and ArangoDB. Bad signal-to-noise and unnecessary token exposure in
   index storage.
2. *`composite_pk` on `(org_id, generated_at_utc)` with no surrogate.* Rejected -- two
   calls inside the same second on different threads (unlikely but possible) would
   collide. The auto-increment PK preserves both rows; the UNIQUE constraint becomes a
   soft de-dup guard rather than a hard PK.
3. *`auto_increment` with no unique constraint.* Rejected -- a user who fat-fingers
   the menu twice in rapid succession should see one row, not two near-identical rows
   one second apart.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_aos_register_cmd.csv`
- SQLite table: `org_aos_register_cmd`
- `org_id_short` is the first 8 hex characters of the org UUID -- the standard
  MistHelper convention for human-readable filenames without leaking full UUIDs into
  shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgAosRegisterCmd"` (matching the operationId). The DataExporter uses that
string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern already used by adjacent device-onboarding exports in
MistHelper (org-prefixed, snake_case operation name, `data/` root). The dedicated
SQLite table name `org_aos_register_cmd` keeps AOS registration history queryable
without joining against unrelated device tables, and aligns with the existing
`org_ssr_register_cmd` / `org_128routers_register_cmd` naming pattern used by the
sibling endpoints listed in the enriched doc's Related Endpoints section.

**Alternatives Considered**:

1. *Single combined `org_register_cmd` table covering AOS + SSR + 128T.* Rejected --
   the three endpoints have distinct response shapes today (and may diverge further);
   one table per operationId keeps schema migrations local.
2. *Full org UUID in the filename.* Rejected -- leaks the UUID into shell history and
   `ls` output. The 8-char short form disambiguates locally without leakage.
3. *Append a timestamp to the filename per invocation.* Rejected -- MistHelper's CSV
   writer already supports SQLite-style upserts; the timestamp lives inside the row
   (`generated_at_utc`), not the filename.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org Exports
cluster, in the Misc sub-range (56-59). The category label is "Safe Org Exports --
Misc / Device Registration Helpers".

**Rationale**:
`.github/copilot-instructions.md` describes the menu ranges as:

| Range | Category |
|-------|----------|
| 1-59 | Safe Org Exports (Misc at 56-59) |
| 60-96 | Interactive Safe |
| 97-101, 153 | Resource Intensive |
| 102-123 | WebSocket |
| 124-150 | Interactive |
| 151-152 | Continuous monitoring |
| 154-194 | Destructive |

This endpoint is a single read-only GET that produces a small JSON object -- the
textbook Safe Org Export. The Misc sub-cluster at 56-59 is the natural home for
device-onboarding helpers (sibling endpoints for SSR and 128T register-cmd are
expected to share this cluster). 58 is the next available integer below the boundary
to the Interactive Safe cluster at 60. The number is provisional -- at
`/speckit.tasks` time MistHelper.py is grep'd for the latest allocated menu integer and
58 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside Interactive Safe (60-96).* Rejected -- there is no genuine interactive
   element beyond a single org-id prompt; the operation is a plain read.
2. *Slot inside Destructive (154-194).* Rejected -- the call is HTTP GET and has zero
   side effect on the Mist Cloud. Mis-signalling risk to junior NOC engineers.
3. *Append at 195 (end of menu).* Rejected -- placing a safe read above the
   destructive cluster visually misleads operators scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_aos_register_cmd:org_id"`. Default: the value of `MIST_ORG_ID` in `.env` if
   present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and return
   early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the org_id prompt.

**Rationale**:
The endpoint has exactly one path parameter (`org_id`) and zero query parameters per
the enriched doc, so a single prompt is sufficient. Site, device, and template IDs
are not involved. Defaulting from `MIST_ORG_ID` keeps the operation one keystroke
("Enter") for an operator who works on a single org.

**Alternatives Considered**:

1. *Add a second prompt to override the output filename.* Rejected -- adds keystrokes
   without operational value; the deterministic filename scheme from Research Task 3
   makes results easy to find under `data/`.
2. *Add a confirmation prompt because the output contains a registration token.*
   Rejected -- the constitution reserves typed confirmations for *destructive*
   operations only. This is a read; safety comes from never logging the token, not
   from gating the read.
3. *Pull `org_id` silently from `.env` without prompting.* Rejected -- breaks the
   contract that interactive mode always shows the user which org is being queried,
   and prevents one-shot use against a non-default org.
