# Phase 0 Research: getOrgEvpnTopology

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke
`mistapi.api.v1.orgs.evpn_topologies.getOrgEvpnTopology(session, org_id,
evpn_topology_id)` exactly once per menu run. The call returns a
`mistapi.APIResponse` whose `.data` is a single JSON object (not a list and not
paginated). Treat HTTP 200 with a non-empty `.data` as success; treat 404 as
"topology not found" and log a warning.

**Rationale**: The enriched endpoint reference at
`documentation/api/orgs/GET_orgs_org_id_evpn_topologies_evpn_topology_id.md`
states explicitly under "Pagination" -- "Not paginated" -- and under "mistapi SDK"
gives the fully qualified call
`mistapi.api.v1.orgs.evpn_topologies.getOrgEvpnTopology()`. The response schema
shows a single object with `id`, `org_id`, `site_id`, `name`, `created_time`,
`modified_time`, `evpn_options`, `overwrite`, `pod_names`, `switch_configs`, and
the required `switches` array. The `switches` array carries per-device records
(role, pod, evpn_id, mac, etc.) -- this is where the bulk of operational data
lives and is the reason a second flattened output file is needed.

**Alternatives Considered**:

- *Use the list endpoint `listOrgEvpnTopologies` only* -- rejected. The list call
  returns a summary collection and omits the per-switch detail block. Operators
  troubleshooting a specific fabric need the single-topology detail call.
- *Call the SDK twice (once for list, once for detail)* -- rejected. The spec is
  scoped to one endpoint; chaining belongs in a separate spec if requested.
- *Use raw `requests.get(...)`* -- rejected. Constitution Principle II and the
  Technology & Compatibility Constraints mandate `mistapi` as the sole Mist
  Cloud interface.

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with `primary_key=["id"]` and
`indexes=["org_id", "site_id", "name"]`. The header row inherits this PK; the
per-switch detail rows use a composite primary key `["evpn_topology_id", "mac"]`
registered under a dedicated synthetic operationId
`getOrgEvpnTopology_switches` (mirroring how spec 500 introduces a sibling
operationId for its details rollup). No surrogate `misthelper_internal_id` is
required because every row has a stable Mist-supplied identifier.

**Rationale**: The 200-response schema shows `id` as a UUID (`contentEncoding:
uuid`) that uniquely identifies an EVPN topology within Mist. The existing
`listOrgEvpnTopologies` entry already uses `natural_pk` with `["id"]` (see
`MistHelper.py` line ~3938-3944) -- using the same shape for the detail call
keeps the two operations consistent and lets the header row from the detail call
upsert into the same logical table as the list call if the operator chooses to
unify them. For per-switch rows, the `mac` field is required by the underlying
`evpn_topology_switch_config` schema and is unique within a topology, so the
composite `["evpn_topology_id", "mac"]` is stable across repeated runs.

**Alternatives Considered**:

- *`composite_pk` on `["id", "modified_time"]`* -- rejected. `modified_time`
  changes on every config edit; that would store an unbounded history rather
  than upserting the current state.
- *`auto_increment_with_unique` with a synthetic surrogate* -- rejected. The
  Mist-supplied `id` UUID is already perfectly stable; introducing a surrogate
  would break joinability with the existing `listOrgEvpnTopologies` table.
- *Single flattened table with `(id, switch_mac)` PK and nullable header columns*
  -- rejected. That denormalises the data, repeats overlay/underlay fields on
  every switch row, and makes ArangoDB graph edge creation harder.

## Research Task 3: Output filename and SQLite table

**Decision**: Two physical outputs per run:

- `data/OrgEvpnTopology.csv` -- header row (`id`, `name`, `org_id`, `site_id`,
  `created_time`, `modified_time`, `overwrite`, flattened `evpn_options.*`,
  flattened `pod_names.*`). SQLite table: `org_evpn_topology`.
- `data/OrgEvpnTopologySwitches.csv` -- one row per `switches[]` element
  (`evpn_topology_id`, `mac`, `role`, `pod`, `pods`, `evpn_id`, and the
  flattened `switch_configs[mac].*` overrides when present). SQLite table:
  `org_evpn_topology_switches`.

Both filenames use the existing PascalCase convention enforced by `DataExporter`
adjacent to `OrgWlans.csv`, `OrgPsks.csv`, `OrgMxEdges.csv`.

**Rationale**: Splitting header from switch detail (a) keeps the CSV row width
manageable for spreadsheet review, (b) lets SQLite enforce the two distinct PK
strategies cleanly, and (c) lines up with how `OrgConfigExporter.psks` and
peers already pair their outputs (one file per logical entity). The
`api_function_name` argument to `DataExporter.write_with_format_selection()` is
set to `"getOrgEvpnTopology"` for the header file and the synthetic
`"getOrgEvpnTopology_switches"` for the detail file so the dispatch picks up
each PK strategy from `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Alternatives Considered**:

- *One wide CSV with `switches_json` column* -- rejected. Operators consuming
  the CSV in Excel cannot pivot on JSON-encoded strings; SQLite cannot upsert
  individual switches; ArangoDB cannot build per-switch graph edges.
- *Three files (header + switches + switch_configs)* -- rejected. The
  `switch_configs[mac]` block is naturally an extension of each switch row;
  collapsing those overrides into the detail row keeps the model simple and
  matches how the schema indexes both by MAC.
- *Use lowercase / snake_case filenames* -- rejected. Adjacent existing outputs
  (`OrgWlans.csv`, `OrgPsks.csv`) all use PascalCase and operators have muscle
  memory for that convention.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **195**, registered in the dispatch dict at
`MistHelper.py` line ~21947 directly after the existing `"194"` entry. The label
text is `"Export single Org EVPN topology detail (header + per-switch)"`.

**Rationale**: The current dispatch dict tops out at 194
(`DeviceConfigTemplateClonerManager.clone` -- a destructive operation). Read-only
operations historically have been added immediately after the current ceiling
when no slot exists in the cluster-of-origin (the Safe Org Exports range 1-59
and Interactive Safe 60-96 are both saturated). Choosing 195 keeps the new safe,
read-only fetch visually separated from the destructive block 154-194 and avoids
renumbering any existing menu items (which would break user automation scripts
that invoke `--menu <num>` directly). The placement is documented in the
README menu table update.

**Alternatives Considered**:

- *Slot it inside the safe-org-exports range (1-59)* -- rejected. The range is
  fully assigned; renumbering would break operator scripts.
- *Slot 92-96 (Interactive Safe viewers)* -- rejected. Those slots are
  contiguous with viewers, not config exports; 195 keeps it beside the related
  `listOrgEvpnTopologies` machinery and the other read-only org-config
  operations.
- *Use 100-series gaps* -- rejected. Those map to WebSocket / Interactive
  operations; placing a non-interactive config export there would mislead
  operators when they scan the menu.

## Research Task 5: Required user prompts

**Decision**: Two prompts via `safe_input()`, both with `.env` defaults:

1. `org_id` -- prompt text: `"Org UUID [default from MIST_ORG_ID]: "`; context:
   `"org_evpn_topology:org_id"`. If the operator presses Enter, fall back to
   `os.environ.get("MIST_ORG_ID")`. If neither is set, log a warning and exit.
2. `evpn_topology_id` -- prompt text: `"EVPN topology UUID [default from
   MIST_EVPN_TOPOLOGY_ID]: "`; context:
   `"org_evpn_topology:evpn_topology_id"`. Falls back to
   `os.environ.get("MIST_EVPN_TOPOLOGY_ID")`. If neither is set, the method
   offers to call `listOrgEvpnTopologies` first and pick from the results
   (this is the existing pattern used by `SiteDeviceExporter` for site_id
   resolution).

Both inputs are validated against the Mist UUID shape (lowercase hex with
hyphens, 36 chars total) before the SDK call. The API token itself is never
prompted -- it is loaded by `mistapi.APISession` from `.env`
(`MIST_API_TOKEN` + `MIST_HOST`) at process start.

**Rationale**: The path parameters `org_id` and `evpn_topology_id` are both
required by the OpenAPI spec, and neither has a sensible global default beyond
what `.env` already provides for `MIST_ORG_ID`. Allowing an `.env` override on
both keeps `python MistHelper.py --test` non-interactive while preserving the
interactive path for ad-hoc operator use. `safe_input()` handles SSH/container
EOF cleanly per Constitution Principle III. UUID shape validation up-front
prevents wasted API quota on operator typos and surfaces a clear error message
instead of a 404 traceback.

**Alternatives Considered**:

- *Single prompt that accepts `"org_id:topology_id"`* -- rejected. Harder to
  validate and inconsistent with the rest of the codebase.
- *Skip `.env` defaults and always prompt* -- rejected. Breaks `--test` mode
  and the Quadlet / SSH automation scenarios.
- *Auto-iterate every topology in the org (no second prompt)* -- rejected. That
  changes the endpoint contract from "get one" to "get all" and belongs in a
  separate spec adjacent to `listOrgEvpnTopologies`.
