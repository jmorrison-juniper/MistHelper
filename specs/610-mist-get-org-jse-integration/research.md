# Phase 0 Research: getOrgJseIntegration

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and
implementation. Each task follows the Decision / Rationale / Alternatives
Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_setting_jse_setup.md` (enriched
OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the path documented in the
enriched per-endpoint file:
`mistapi.api.v1.orgs.setting.jse.setup.getOrgJseIntegration(apisession,
org_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object
titled `account_jse_info` with three top-level keys per the schema:

- `cloud_name` (string -- the JSE cloud the org is bound to,
  e.g. `devcentral.juniperclouds.net`)
- `org_names` (array of unique strings -- names of JSE orgs the
  authenticated user can see)
- `username` (string -- the JSE account email,
  e.g. `john@abc.com`)

Required path parameter: `org_id` (UUID string). No query parameters. No
request body. Not paginated.

**Rationale**:
The enriched documentation file lists the SDK module as
`mistapi.api.v1.orgs.integration_jse.getOrgJseIntegration()`, but
spec.md and the OpenAPI URL path (`/api/v1/orgs/{org_id}/setting/jse/setup`)
both indicate the URL-derived module path
`mistapi.api.v1.orgs.setting.jse.setup`. The mistapi SDK historically
generates module paths from the URL, not the OpenAPI tag (verified for
adjacent operations like `getOrgLicensesSummary` which lives under
`mistapi.api.v1.orgs.licenses` matching `/orgs/{org_id}/licenses`). We
follow spec.md as the authoritative feature contract. Final verification
happens at implementation time via
`python -c "from mistapi.api.v1.orgs.setting.jse import setup; help(setup)"`
inside the venv; if the SDK actually exposes the function at the
tag-derived `integration_jse` path the implementation switches to that
import line and the rest of the design is unchanged.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/setting/jse/setup`.* Rejected --
   the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the tag-derived path
   (`mistapi.api.v1.orgs.integration_jse`).* Held in reserve as the
   implementation-time fallback if the URL-derived path is not present
   in the installed mistapi version; the spec.md path is preferred.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy on a single output table:

- `org_jse_integration_setup`: PK = `org_id` -- one row per org. The
  endpoint reports the *current* JSE binding for the org, and re-running
  the menu item against the same org must overwrite the previous row,
  not append a duplicate.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type
`natural_pk` with `primary_key=['org_id']`. The `org_id` value is
injected by MistHelper before the upsert because the Mist API response
does not echo it back. Secondary index on `cloud_name` lets a user
quickly see which orgs are bound to which JSE cloud.

**Rationale**:
The response contains no stable Mist-supplied UUID (`getOrgJseInfo`
returns a configuration snapshot, not a versioned record). The natural
identity of a row in this table is "the JSE setup currently bound to
this org" -- exactly one such record exists per org at any moment. Using
`org_id` as the PK guarantees clean `INSERT OR REPLACE` upsert behavior
on repeated polls. `composite_pk` is overkill (no time dimension is
modelled because the API does not provide a stable timestamp on the
binding itself), and `auto_increment_with_unique` would let duplicate
snapshots accumulate across polls.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, username)`.* Rejected -- the username
   is the JSE account, and if the JSE account changes the row should
   still be overwritten in place (the meaningful identity is "the JSE
   integration for org X", regardless of which JSE user signed it).
2. *`auto_increment_with_unique` on a `misthelper_internal_id`.*
   Rejected -- would let repeated runs accumulate duplicate snapshots,
   defeating the upsert behavior the spec requires.
3. *`composite_pk` on `(org_id, polled_at_utc)`.* Rejected -- creates
   one row per poll instead of one row per org, which is the wrong
   semantic and bloats the table without value (the endpoint state
   changes rarely).

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_jse_integration_setup.csv`
- SQLite table: `org_jse_integration_setup`
- `org_id_short` is the first 8 hex characters of the org UUID --
  already the convention used by adjacent org-scoped exports for
  human-readable filenames without leaking full UUIDs into shell
  history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgJseIntegration"`
(matching the operationId from the OpenAPI spec). The DataExporter uses
that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Single-table design matches the single-object response shape. The
filename pattern is consistent with the `org_<short>_*` convention used
by license exports and other org-scoped Safe Org Exports operations.
Using the operationId verbatim as the `api_function_name` keeps the PK
strategy lookup deterministic.

**Alternatives Considered**:

1. *Two output files (one for `org_names` array, one for the rest).*
   Rejected -- the `org_names` array is small and best collapsed into a
   single comma-joined string column on the parent row. Splitting would
   force a join for trivial questions.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into
   shell history and ls output unnecessarily. The 8-character short
   form is enough to disambiguate locally.
3. *Generic filename `jse_integration_setup.csv` (no org segment).*
   Rejected -- multi-org operators routinely poll several orgs and a
   shared filename would clobber prior output.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 59**, sitting at the tail
of the Safe Org Exports cluster (1-59) and immediately before the
Interactive Safe block starting at 60. The category label is "Safe Org
Exports -- Integrations / JSE".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the
menu ranges as: 1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101
+ 153 Resource Intensive, 102-123 WebSocket, 124-152 Interactive,
154-194 Destructive. This endpoint is a single non-paginated GET that
returns a small fixed-shape JSON object -- it is the canonical example
of a Safe Org Export. Slot 59 is the next contiguous integer at the
top of that block. The number is provisional -- at `/speckit.tasks`
time, MistHelper.py is grep'd for the latest allocated menu integer
and 59 is shifted to the next free integer inside the same cluster if
a conflict exists (search order: 59, 58, 57 ... toward the start of
the safe-export range).

**Alternatives Considered**:

1. *Slot inside Interactive Safe (60-96).* Rejected -- this menu item
   is not interactive beyond a single org prompt and does not warrant
   a slot in the interactive block.
2. *Slot inside Resource Intensive (96-101).* Rejected -- the
   endpoint is a single small GET, not resource intensive.
3. *Append to the end (e.g., 195).* Rejected -- the destructive
   cluster ends at 194, and placing a read-only safe export above the
   destructive block visually mis-signals the risk level to a junior
   NOC engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_jse_integration:org_id"`. Default: the value of
   `MIST_ORG_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on validation failure, log `WARNING` and
   return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap,
never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by
  `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the prompt.

**Rationale**:
The Mist JSE setup endpoint is strictly org-scoped: no site, device,
or template identifiers are involved, and there are no query
parameters. A single prompt keeps the menu item friction-free for the
common case where the operator polls their default org.

**Alternatives Considered**:

1. *Zero prompts: always use `MIST_ORG_ID` from `.env`.* Rejected --
   would prevent ad-hoc polling of non-default orgs in a multi-tenant
   shop, and would silently skip the call when `MIST_ORG_ID` is not
   set rather than asking the user.
2. *Add a second prompt for an output filename override.* Rejected --
   adds keystrokes without operational value. The deterministic
   filename scheme in Research Task 3 makes results easy to find under
   `data/`.
3. *Add a prompt to refresh the JSE binding via the sibling POST
   endpoint.* Rejected -- mixing a destructive operation into a
   read-only menu item violates the safety-first principle. The
   POST/DELETE siblings get their own future specs.
