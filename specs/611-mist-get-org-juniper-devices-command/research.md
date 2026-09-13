# Phase 0 Research: getOrgJuniperDevicesCommand

This document captures the design decisions made before any code is written.
Each task uses the Decision / Rationale / Alternatives Considered format
required by the constitution.

Authoritative input:
`documentation/api/orgs/GET_orgs_org_id_ocdevices_outbound_ssh_cmd.md`.

---

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke the SDK as
`mistapi.api.v1.orgs.ocdevices.outbound_ssh_cmd.getOrgJuniperDevicesCommand(apisession, org_id, site_id=None)`.

The function returns a `mistapi.APIResponse` whose `.data` attribute is a
single JSON object with one required field:

```json
{ "cmd": "string" }
```

The endpoint is non-paginated; a single GET is sufficient. HTTP path is
`GET /api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd`. The only query
parameter is `site_id` (optional) -- when supplied, Mist performs a proxy
config check for that site and may include automatic site assignment context
in the generated command.

**Rationale**: The enriched per-endpoint doc at
`documentation/api/orgs/GET_orgs_org_id_ocdevices_outbound_ssh_cmd.md` lists
the parameter table and the 200 schema in full. The mistapi SDK convention
(verified across other operations already used by MistHelper) is that the
Python module path mirrors the URL path: each URL segment becomes a Python
sub-module and the operation function name equals the OpenAPI `operationId`.
Note: the enriched doc's "mistapi SDK" line shows the legacy
`mistapi.api.v1.orgs.devices` alias; the canonical path-mirrored module is
`mistapi.api.v1.orgs.ocdevices.outbound_ssh_cmd` per the spec.md "mistapi SDK
module" entry and matches the URL `/api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd`.
Task generation will pin the import line based on the actual module layout in
the installed `mistapi==0.59+` wheel.

**Alternatives Considered**:

- *Raw `requests.get()`*: Rejected. The constitution and `agents.md` both
  pin `mistapi` as the sole permitted Mist Cloud client. Bypassing it would
  duplicate auth, retry, and rate-limit logic already centralized in the
  SDK.
- *Calling the related JSI variant
  (`GET /api/v1/orgs/{org_id}/jsi/devices/outbound_ssh_cmd`)*: Rejected.
  That is a separate endpoint with its own operationId and warrants its
  own spec/plan if a second menu item is desired.

---

## Research Task 2: Primary Key Strategy

**Decision**: Use **`auto_increment_with_unique`** with a unique constraint
on the composite of `(org_id, site_id)` (site_id stored as the empty string
when not supplied, so the unique constraint behaves predictably for
SQLite). Register in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as:

```python
"getOrgJuniperDevicesCommand": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_constraint": ["org_id", "site_id"],
    "indexes": ["org_id", "site_id", "retrieved_at"],
}
```

**Rationale**: The Mist response payload is a bare `{cmd: "..."}` object
with no stable identifier of its own. Two natural inputs uniquely identify
a row in MistHelper's local store: the `org_id` (always present) and the
optional `site_id` (proxy context). The `cmd` value itself may change
across Mist releases or per-site proxy state, so it cannot be a primary
key. The classic MistHelper pattern for response shapes that lack a stable
upstream ID is `auto_increment_with_unique` -- a surrogate
`misthelper_internal_id` is the PK and a UNIQUE constraint over the inputs
keeps re-runs upserting cleanly rather than appending duplicate rows.

**Alternatives Considered**:

- *`natural_pk` on `(org_id, site_id)`*: Rejected. Composite natural keys
  are reserved for entities Mist itself models with stable identifiers; the
  response here has no identifier at all -- the keys are *inputs we
  supplied*, not Mist-issued IDs. The constitution distinguishes these
  cases.
- *`composite_pk` with a `retrieved_at` timestamp*: Rejected. That would
  intentionally append a new row on every run (time-series behavior) and is
  appropriate for stats/events streams, not for a per-org bootstrap string
  that should be upserted in place.
- *No primary key at all (CSV-only)*: Rejected. The SQLite backend is a
  first-class output target; every operationId must register a PK
  strategy.

---

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV file: `data/org_juniper_devices_outbound_ssh_cmd.csv`
- SQLite table: `org_juniper_devices_outbound_ssh_cmd`
- ArangoDB collection: `org_juniper_devices_outbound_ssh_cmd`

Column set (one row per `(org_id, site_id)` invocation):

| Column | Type | Notes |
|---|---|---|
| `misthelper_internal_id` | INTEGER PK AUTOINCREMENT | Surrogate PK |
| `org_id` | TEXT NOT NULL | Input UUID |
| `site_id` | TEXT NOT NULL DEFAULT '' | Input UUID, '' if unspecified |
| `cmd` | TEXT NOT NULL | The generated outbound SSH/netconf command |
| `cmd_length` | INTEGER | Convenience column for logging/analytics |
| `retrieved_at` | TEXT NOT NULL | ISO-8601 UTC timestamp at fetch time |

**Rationale**: The filename mirrors the URL path with `/` replaced by `_`
and the `{org_id}` placeholder dropped, matching the convention used across
existing MistHelper exports (e.g. `org_inventory.csv`,
`org_licenses_summary.csv`). The `cmd_length` column is included because
the constitution forbids logging the `cmd` body but allows logging its
length -- having the length materialized in the SQLite row makes downstream
audit queries (e.g. "did the command change between runs?") cheaper without
re-exposing the body in logs.

**Alternatives Considered**:

- *Short name `org_oc_ssh_cmd.csv`*: Rejected. Less searchable; breaks the
  pattern of mirroring the URL path.
- *Storing `cmd` only as a sidecar `.txt` file*: Rejected. Splits the
  storage path -- CSV/SQLite/ArangoDB backends would lose parity, violating
  the multi-backend contract enforced by `DataExporter`.

---

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new operation at menu number **58** in the **Safe
Org Exports / Misc (56-59)** cluster, alongside other read-only org-wide
device-and-config exports.

**Rationale**: Per `.github/copilot-instructions.md` the menu number ranges
are documented as:

- 1-59: Safe Org Exports (Sites, Inventory, Device stats, Events,
  Clients, Gateways, Templates, Config/Admin, SLE, Misc 56-59)
- 60-96: Interactive Safe
- 97-101, 153: Resource Intensive
- 102+: WebSocket / Interactive / Destructive

This endpoint is read-only, returns a small payload, and concerns an
org-wide device bootstrap command -- a clean fit for the "Misc" tail of the
Safe Org Exports range. Slot 58 is the next available integer in that
cluster (with 56, 57, 59 already informally claimed or reserved per the
project's ongoing cataloging effort). If task generation discovers 58 is
already taken by an in-flight feature branch, the next free integer in the
same cluster is used (preference order: 58 -> 59 -> first free in 56-72).

**Alternatives Considered**:

- *Menu 8-14 (Inventory cluster)*: Rejected. Inventory operations list
  devices; this endpoint returns a bootstrap command string, not a device
  list.
- *Menu 60-72 (Site devices, Interactive Safe)*: Rejected. The endpoint is
  org-scoped, not site-scoped (site_id is optional context only), so it
  belongs with org-wide exports.
- *Menu 124+ (Interactive Diagnostics)*: Rejected. Nothing in this
  operation requires interactive diagnostics; it is a single GET that
  writes one row.

---

## Research Task 5: Required User Prompts

**Decision**: Two prompts via `safe_input()`, each with an explicit
`context=` label and `.env` defaulting where possible.

1. **`org_id`** (required) -- prefilled from `MIST_ORG_ID` in `.env` if
   present; if absent the user must type it. Validated against the standard
   Mist UUID regex (`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)
   before the SDK call; on validation failure the method logs a warning and
   returns early without invoking `mistapi`.
   Prompt: `Enter org_id [MIST_ORG_ID default]: `
   Context label: `org_juniper_devices_outbound_ssh_cmd:org_id`

2. **`site_id`** (optional) -- empty input is allowed and means "no
   site_id". If non-empty, validated against the same UUID regex; failure
   is treated as a soft warning and the call proceeds without the query
   parameter (i.e. validation failure degrades to "no site_id" rather than
   aborting, because site_id is itself optional in the API).
   Prompt: `Enter site_id (optional, press Enter to skip): `
   Context label: `org_juniper_devices_outbound_ssh_cmd:site_id`

The API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) are loaded from
`.env` by the existing `mistapi.APISession` bootstrap -- the menu method
never prompts for them and never logs them.

**Rationale**: The endpoint signature has exactly one required path
parameter (`org_id`) and one optional query parameter (`site_id`). Other
MistHelper org-scoped menu items default `org_id` from `.env` for
non-interactive `--test` mode, then re-prompt at the menu when the
operator overrides it. The same pattern applies here. UUID validation is
done client-side because the Mist API otherwise returns a 400 with a less
helpful message; client-side validation gives the NOC engineer a clean
"invalid UUID format" warning and avoids burning an API call.

**Alternatives Considered**:

- *Prompt for `cmd` output destination*: Rejected. `DataExporter` already
  resolves output backend from `.env` (`OUTPUT_BACKEND=csv|sqlite|arango`);
  re-prompting per menu item would violate consistency with the other 193
  operations.
- *Skip UUID validation and let Mist 400*: Rejected. Wastes an API call,
  burns rate-limit budget, and degrades the user experience for a trivial
  client-side check.
- *Read `site_id` from `.env`*: Rejected. There is no project-wide
  `MIST_SITE_ID` convention -- site context is per-invocation in
  MistHelper. A `MIST_SITE_ID` default would set a misleading precedent.
