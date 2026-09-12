# Phase 0 Research: getOrgMxEdge

**Feature**: 615-mist-get-org-mx-edge | **Date**: 2026-06-30
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document records the five research tasks required by `/speckit.plan` for this
endpoint. Each task uses the Decision / Rationale / Alternatives Considered format.

---

## Research Task 1: SDK Function Signature & Behavior

**Source**: `documentation/api/orgs/GET_orgs_org_id_mxedges_mxedge_id.md` (enriched
per-endpoint reference produced from the Mist OpenAPI 3 spec).

### Decision

Call the SDK exactly as:

```python
response = mistapi.api.v1.orgs.mxedges.getOrgMxEdge(
    apisession,                          # existing global mistapi.APISession
    org_id=org_id,                       # validated UUID from safe_input()
    mxedge_id=mxedge_id,                 # validated UUID from safe_input()
)
mxedge_record = response.data            # mistapi wraps payload in .data
```

The endpoint is `GET /api/v1/orgs/{org_id}/mxedges/{mxedge_id}`. It accepts two
required path parameters and zero query parameters. The 200 response is a single JSON
object describing one MxEdge appliance, with fields including `id`, `mac`, `model`,
`mxcluster_id`, `name`, `org_id`, `site_id`, `for_site`, `mxagent_registered`,
`tunterm_registered`, `created_time`, `modified_time`, plus nested configuration
objects `mxedge_mgmt`, `oob_ip_config`, `proxy`, `tunterm_ip_config`,
`tunterm_dhcpd_config`, `tunterm_igmp_snooping_config`, `tunterm_multicast_config`,
`tunterm_other_ip_configs`, `tunterm_port_config`, `tunterm_switch_config`,
`tunterm_monitoring`, `tunterm_extra_routes`, `versions`, and arrays `ntp_servers` and
`services`. Errors: 400, 401, 403, 404, 429. The endpoint is not paginated.

### Rationale

- The enriched doc explicitly lists the SDK call as
  `mistapi.api.v1.orgs.mxedges.getOrgMxEdge()` with both required path params.
- `response.data` is the canonical access pattern used throughout MistHelper for every
  mistapi GET (see `OrgConfigExporter.mx_edges()` and `OrgExportUtils.export_data()`).
- No query parameters means no flags or filter prompts -- the call is a pure path-only
  fetch.
- The 5-second performance budget set in `spec.md` is comfortable: a single JSON object
  on the order of a few KB.

### Alternatives Considered

- **Raw `requests` call** -- Rejected. Constitution requires `mistapi` as the sole
  Mist API interface; raw HTTP would bypass adaptive delay metrics and shared retry
  logic.
- **Bulk fetch via `listOrgMxEdges` then filter client-side** -- Rejected. The user
  may want a specific MxEdge's full detail including nested configs that `list` may
  return in summarized form; using the dedicated GET-by-id is the documented pattern
  and avoids over-fetching.
- **Mxedge_id auto-selection from a previous `listOrgMxEdges` call** -- Considered for
  UX. Deferred: the spec scope is a single read endpoint; auto-selection is a
  separate UX feature that can be added without changing this plan.

---

## Research Task 2: Primary Key Strategy

### Decision

Register `getOrgMxEdge` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as `natural_pk` on `id`:

```python
"getOrgMxEdge": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["org_id", "mxcluster_id", "site_id", "mac", "name"],
    "description": "Single MxEdge appliance detail record",
},
```

### Rationale

- The response carries a stable `id` field documented as a UUID (`contentEncoding:
  uuid`, `readOnly: true`) and described as "Unique ID of the object instance in the
  Mist Organization."
- This matches the `natural_pk` recipe from the canonical instructions document:
  "Entities with stable UUIDs (sites, devices, templates)."
- Sibling endpoints already follow this pattern: `listOrgMxEdges` is registered with
  natural primary key on `id` (`MistHelper.py` line ~4685). Using the same shape keeps
  cross-table joins clean.
- Indexes on `org_id`, `mxcluster_id`, `site_id`, `mac`, and `name` cover the common
  filter columns surfaced by adjacent menu items and by Marvis-style search flows.

### Alternatives Considered

- **`composite_pk` on `(id, modified_time)`** -- Rejected. The spec describes a read
  endpoint that overwrites the latest state on every fetch. There is no time series
  semantic; composite PK would create duplicates instead of upserting.
- **`auto_increment_with_unique`** -- Rejected. The API provides a stable UUID, so
  there is no need to synthesize a surrogate key.

---

## Research Task 3: Output Filename and SQLite Table

### Decision

- **CSV filename**: `data/OrgMxEdgeDetail.csv`
- **SQLite table**: `org_mxedge_detail`
- **ArangoDB collection**: `org_mxedge_detail` (same name, default polyglot mapping)

### Rationale

- CamelCase CSV filenames match the existing pattern (e.g. `OrgMxEdges.csv` from
  `OrgConfigExporter.mx_edges()`, line ~12009).
- Snake_case SQLite table names match the existing pattern (e.g. `org_mxedges` from
  `listOrgMxEdges`, line ~4685).
- The `_detail` suffix differentiates this single-record-per-MxEdge GET-by-id table
  from the bulk `org_mxedges` listing table -- the two are complementary and the
  suffix makes that explicit in `SELECT` queries.

### Alternatives Considered

- **`OrgMxEdge.csv` (singular, no suffix)** -- Rejected. Tables with the same root
  name as a listing table would confuse junior NOC engineers and risk accidental
  schema collisions in SQLite when both are persisted.
- **`MxEdgeConfig.csv`** -- Rejected. The Mist convention prefixes
  organization-scoped resources with `Org`; deviating breaks the lookup mnemonic.

---

## Research Task 4: Menu Category Placement & Next Available Number

### Decision

Place the new operation in the **Safe Org Exports** cluster as menu number **235**,
adjacent to the existing org-scope MxEdge cluster.

### Rationale

- The endpoint is read-only (GET), so it belongs in the safe range, not the
  destructive range (which `copilot-instructions.md` documents as 154-194).
- The in-flight batch of catalog-the-endpoint specs is landing operations in the
  220-250 range (spec 535 proposes 230, spec 543 proposes 95, etc.). 235 is a clean
  free integer that avoids collisions with neighboring open PRs at the time of
  writing.
- Adjacent MxEdge operations already live in the safe cluster:
  - `listOrgMxEdges` -> `OrgConfigExporter.mx_edges()` (existing op).
  - `listSiteMxEdges`, `listOrgMxEdgesStats`, `listOrgMxEdgeClusters` -- all safe org
    reads.
  Placing the single-record detail next to them keeps the menu mentally cohesive.
- Number is provisional: the final task-generation step (`/speckit.tasks`) re-verifies
  the integer against the menu registry and bumps it if needed.

### Alternatives Considered

- **Place in op 60-72 (site-device cluster)** -- Rejected. The endpoint is
  org-scoped, not site-scoped; the path is `/orgs/.../mxedges/...`, not `/sites/...`.
- **Place in op 153 (resource-intensive)** -- Rejected. A single-record GET is not
  resource-intensive.
- **Pick 96** -- Rejected. The 96 slot is reserved for the heavier interactive viewer
  cluster (see `copilot-instructions.md` menu category table).

---

## Research Task 5: Required User Prompts

### Decision

Two prompts collected via `safe_input()`, both with explicit context strings:

1. **`org_id`** -- prompt: `"Enter org_id (UUID): "`, context:
   `"org_mxedge_detail:org_id"`. Default: read from `.env` `MIST_ORG_ID` when set, so
   `--test` mode runs non-interactively.
2. **`mxedge_id`** -- prompt: `"Enter mxedge_id (UUID): "`, context:
   `"org_mxedge_detail:mxedge_id"`. No `.env` default for the general case; in
   `--test` mode the value is taken from a new optional `MIST_TEST_MXEDGE_ID`
   environment variable (documented in `quickstart.md`), and if that variable is
   absent the test invocation logs `WARNING` and skips the menu cleanly with exit
   code 0.

Both inputs are validated against the Mist UUID regex (`^[0-9a-fA-F-]{36}$`) before
the SDK call. Validation failure logs `WARNING` and returns early.

### Rationale

- The endpoint requires both path parameters; the SDK rejects calls without them.
- `MIST_ORG_ID` already exists in `.env` and is read by sibling menu items, so
  re-using it preserves consistency.
- A separate `MIST_TEST_MXEDGE_ID` keeps the test fixture explicit without polluting
  the normal-run prompt path. It is optional so production deployments without test
  fixtures do not gain a spurious required env variable.
- `safe_input()` handles SSH / container EOF cleanly, satisfying
  Principle III (Safety-First) and acceptance scenario 2 in `spec.md`.

### Alternatives Considered

- **Auto-list MxEdges and let the user pick by index** -- Considered for UX
  ergonomics. Deferred: introduces a second API call (`listOrgMxEdges`) and a numeric
  selection prompt that pushes the method past the 25-line / 5-block budget. Can be
  added later as a separate UX-only spec.
- **Accept the MxEdge MAC instead of the UUID** -- Rejected. The SDK call's required
  path param is the UUID, and translating MAC -> UUID would again require a second
  API call.
- **Skip validation and rely on the API to 404** -- Rejected. Local UUID validation
  catches typos before consuming an API call against the rate limit, which matters
  when the user is exploring interactively.
