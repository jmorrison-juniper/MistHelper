# Phase 0 Research: getOrgLicensesSummary

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_licenses.md`

## Research Task 1: SDK function signature & behavior

- **Decision**: Use `mistapi.api.v1.orgs.licenses.getOrgLicensesSummary(apisession, org_id)`
  as the sole interface to the Mist Cloud endpoint
  `GET /api/v1/orgs/{org_id}/licenses`. The call is synchronous, non-paginated,
  and returns one JSON object whose top-level keys are `amendments[]` (array of
  `license_amendment`), `licenses[]` (array of `license_sub`), `entitled` (map
  `license_type -> int`), `fully_loaded` (map `license_type -> int`), `summary`
  (map `license_type -> int`), and `usages` (map `license_type -> int`). All
  fields are read-only per the OpenAPI schema; the method never mutates server
  state.
- **Rationale**: Constitution mandates that the Thomas Munzer `mistapi` SDK is
  the sole permitted Mist API interface; the documented module path
  (`mistapi.api.v1.orgs.licenses`) matches the SDK convention of mirroring the
  REST path. The enriched per-endpoint doc confirms a single required path
  parameter (`org_id`) and no query parameters, so the Python call collapses to
  a two-positional-argument invocation. The endpoint already appears in the
  documentation's "MistHelper Notes" line as being referenced by op 52, but the
  spec treats it as a new sequential menu addition with the full flatten /
  multi-backend treatment that the older invocation did not have.
- **Alternatives Considered**:
  - *Direct `requests.get(...)`* -- rejected: violates Principle II
    (class-based, mistapi-only) and bypasses the SDK's auth / pagination /
    retry hooks.
  - *Calling the related `getOrgLicensesBySite` instead* -- rejected: that is
    a different endpoint (`/orgs/{org_id}/licenses/sites`) and does not return
    the org-wide `entitled` / `summary` / `usages` maps that this spec covers.
  - *Lazy-load the response and stream rows* -- rejected: response is small
    and already fully materialized by the SDK; streaming would add complexity
    with no observed gain.

## Research Task 2: Primary Key Strategy

- **Decision**: Use **mixed strategy** -- one PK strategy per logical row set,
  all four registered under the single operationId `getOrgLicensesSummary`
  with a `child_tables` mapping (consistent with other multi-table operations
  in `ENDPOINT_PRIMARY_KEY_STRATEGIES`):
  - `org_licenses_subscriptions` -> **natural_pk** on `['id']` (the
    subscription UUID, stable across runs).
  - `org_licenses_amendments` -> **natural_pk** on `['id']` (the amendment
    UUID, stable across runs).
  - `org_licenses_summary_counts` -> **composite_pk** on `['org_id',
    'license_type']` (one row per license type per org, upsertable each run).
  - `org_licenses_usage_counts` -> **composite_pk** on `['org_id',
    'license_type', 'metric']` where `metric` discriminates between the
    `entitled`, `fully_loaded`, and `usages` maps (the four maps share a flat
    schema and are stacked into one table with the `metric` column).
- **Rationale**: `licenses[]` and `amendments[]` items already carry stable
  UUIDs (`id`, `contentEncoding: uuid` in the schema), so natural_pk is the
  cheapest correct choice and lets repeated runs upsert cleanly via `INSERT
  OR REPLACE`. The four count maps have no per-row UUID, so a composite_pk on
  the business identity (`org_id` + `license_type` [+ `metric`]) avoids
  duplicate row accumulation across nightly runs while still allowing the
  current snapshot to be updated. Auto-increment with unique constraints was
  rejected for the maps because the natural identity is unambiguous and
  composite keys give a more semantically meaningful upsert behaviour.
- **Alternatives Considered**:
  - *Single auto-increment table per row set* -- rejected: would accumulate
    duplicate rows on every run (violates the "no duplicates on re-run"
    acceptance criterion).
  - *Flatten everything into one wide table* -- rejected: lossy because
    `amendments[]` and `licenses[]` carry distinct fields, and the count maps
    have no per-row UUID.
  - *Skip the count maps entirely* -- rejected: they are the primary value of
    this endpoint (this is what the user opens menu 96 to see).

## Research Task 3: Output filename and SQLite table

- **Decision**: Use four parallel output names derived from the operationId,
  produced by four sequential `DataExporter.write_with_format_selection`
  calls. Each name doubles as the SQLite table name and the CSV basename:
  - `org_licenses_subscriptions` -> `data/org_licenses_subscriptions.csv` /
    table `org_licenses_subscriptions`
  - `org_licenses_amendments` -> `data/org_licenses_amendments.csv` / table
    `org_licenses_amendments`
  - `org_licenses_summary_counts` -> `data/org_licenses_summary_counts.csv` /
    table `org_licenses_summary_counts`
  - `org_licenses_usage_counts` -> `data/org_licenses_usage_counts.csv` /
    table `org_licenses_usage_counts`
  Each call passes `api_function_name="getOrgLicensesSummary"` so the
  DataExporter routes through the registered PK strategy and emits the same
  shape across CSV, SQLite, and ArangoDB+Redis backends.
- **Rationale**: Four names mirror the four logical entities in the response
  schema and align with the existing naming convention
  (`org_<resource>_<subresource>`) used by adjacent license-cluster
  operations. Splitting the maps from the arrays prevents schema collisions
  in SQLite (different column sets) and gives the NOC user one CSV per
  question they are actually asking ("what subscriptions do I own?", "what
  amendments have been applied?", "how many of each license type am I
  consuming?", "what is my total entitlement / fully-loaded ceiling /
  available headroom?").
- **Alternatives Considered**:
  - *One CSV with a `row_type` column* -- rejected: forces nullable columns
    across heterogeneous shapes and makes downstream SQL queries awkward.
  - *Hand-roll JSON dump to a single `.json` file* -- rejected: bypasses
    DataExporter and breaks the multi-backend contract (CSV / SQLite /
    ArangoDB consistency).

## Research Task 4: Menu category placement and next available menu number

- **Decision**: Place the new menu item in the **Safe Org Exports** category
  at menu number **96**. The label is
  `Export Org Licenses Summary (subscriptions, amendments, counts)`. Menu 96
  sits at the boundary between the Safe Org Exports cluster (1-95) and the
  Resource Intensive cluster (97-101), which is appropriate because the
  endpoint is light (single GET, non-paginated, small payload) but produces
  four output files in one invocation.
- **Rationale**: The constitution / project conventions map ops 51-95 to the
  Safe Org Exports / License / SLE cluster. The pre-validated reference plan
  (`specs/500-mist-get-org-license-async-claim-status/plan.md`) reserves 95
  for the async claim-status export, so 96 is the next available integer in
  the same cluster. If a later merge claims 96 first, task generation will
  walk forward to the next free integer in the same cluster (97 falls into
  Resource Intensive, so practically the fallback is to expand the cluster by
  one and document the boundary shift in CHANGELOG.md).
- **Alternatives Considered**:
  - *Slot into Misc 56-59* -- rejected: that range is for org-level
    miscellany unrelated to licensing.
  - *Pick a high number (e.g. 155)* -- rejected: 150+ is the destructive
    block; placing a safe GET there mis-signals the intent.
  - *Replace the existing op-52 invocation in-place* -- rejected: spec
    explicitly treats this as a new addition with the full flatten /
    multi-backend treatment, and replacing op-52 would change a
    user-visible menu number for no benefit.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

- **Decision**: One prompt only -- the org UUID -- collected via
  `safe_input("Org ID (blank to use MIST_ORG_ID): ",
  context="org_licenses_summary:org_id")`. If the user enters blank, fall
  back to `os.environ.get("MIST_ORG_ID")`. Validate the resulting string
  against the Mist UUID regex (`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`,
  case-insensitive) before the SDK call; on validation failure log a
  WARNING and return early. The API token (`MIST_API_TOKEN`) and host
  (`MIST_HOST`) are loaded by the existing `mistapi.APISession`
  initialization in `MistHelper.py`; the new method never sees or logs
  them.
- **Rationale**: The endpoint takes exactly one path parameter (`org_id`)
  and zero query parameters. The `.env`-first pattern matches every other
  org-scoped menu method in MistHelper and keeps the `--test` /
  non-interactive path working without prompting. `safe_input()` is
  mandated by Principle III for SSH and container EOF safety. UUID
  validation before the SDK call prevents wasted API quota on malformed
  input.
- **Alternatives Considered**:
  - *Read `org_id` from a CLI flag only* -- rejected: breaks the
    menu-driven UX for the junior NOC audience.
  - *Loop over every org the token can see* -- rejected: violates the
    Five-Item Rule (additional logical block) and exceeds the
    single-responsibility scope of this menu item.
  - *Prompt for both `org_id` and an output-format flag* -- rejected:
    output format is already controlled by `DataExporter` configuration
    (backend selection lives in `.env` / global runtime state), so
    re-prompting per menu item would duplicate state.
