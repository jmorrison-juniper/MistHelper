# Phase 0 Research: getGatewayDefaultConfig

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/constants/GET_const_default_gateway_config.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path that mirrors the OpenAPI URL:
`mistapi.api.v1.const.default_gateway_config.getGatewayDefaultConfig(apisession,
model, ha=None)`. The SDK returns a `mistapi.APIResponse` object whose `.data` attribute
is the parsed JSON body. The body is a single JSON object (not a list and not
paginated). Per the enriched doc, the response contains the following top-level keys
(all optional in practice -- presence depends on the model):

- `dhcpd_config` (object: `{lan: {ip_start, ip_end, ...}}`)
- `ip_configs` (object: `{lan: {ip, type, ...}}`)
- `networks` (object: `{lan: {name, subnet, vlan_id, ...}}`)
- `path_preferences` (object: `{wan: {paths: [{name, type}, ...]}}`)
- `port_config` (object keyed by port id, e.g. `ge-0/0/0,ge-0/0/7`, each value
  describes `ip_config`, `name`, `usage`, optional `wan_type`)
- `service_policies` (array of objects: `{action, name, path_preference, services,
  tenants}`)

Required query parameter: `model` (string). Optional query parameter: `ha` (string -- the
upstream API documents the type as `string` even though semantically it is a yes/no
flag). MistHelper normalizes the user answer to either the literal string `"true"` (when
the user answers `y` / `yes`) or `None` (when the user defers).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.constants.models.getGatewayDefaultConfig()`, but the spec.md (the
authoritative feature contract) names `mistapi.api.v1.const.default_gateway_config` and
that path matches the OpenAPI URL one-for-one (`/api/v1/const/default_gateway_config` ->
`mistapi.api.v1.const.default_gateway_config`). The mistapi SDK historically generates
module paths from the URL, not from the OpenAPI tag (verified by inspecting adjacent
const endpoints such as `/api/v1/const/device_models` which resolve to
`mistapi.api.v1.const.device_models`). The doc-suggested
`mistapi.api.v1.constants.models...` path is the human-readable tag, not the SDK module.
Final verification happens at implementation time via
`python -c "from mistapi.api.v1.const import default_gateway_config; help(default_gateway_config)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/const/default_gateway_config`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc's `mistapi SDK` line (`...constants.models...`).*
   Rejected -- the SDK organizes modules by URL path tokens, not OpenAPI tag, and the
   spec.md (the authoritative feature contract) names the URL-based path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table:

- `default_gateway_config`: PK = `(model, ha_flag)` -- one row per
  (gateway hardware model, HA mode) tuple. The `ha_flag` column stores the literal
  string `"true"` when the user requested HA configuration and the literal string
  `"false"` when they did not (never `NULL`, to keep the composite PK total).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` with
`primary_key=['model', 'ha_flag']`. MistHelper injects both columns into every row
before the upsert (the API does not echo `model` or `ha` in the response body, so
MistHelper carries them through from the user inputs).

**Rationale**:
The endpoint returns a *deterministic* default configuration per (model, ha) query --
two runs with the same inputs yield byte-identical responses unless Mist publishes a new
default. Composite PK on `(model, ha_flag)` lets repeated runs `INSERT OR REPLACE` the
single row for that combination, which is the desired behavior: a fresh capture
overwrites the older snapshot for the same combination, and different (model, ha) combos
each retain their own row so a single SQLite file can hold the full reference matrix
across all gateway hardware models the operator queries.

**Alternatives Considered**:

1. *`auto_increment_with_unique` with a uniqueness constraint on `(model, ha_flag)`.*
   Rejected -- adds an artificial `misthelper_internal_id` column that provides no
   business value when the natural key is already total and stable.
2. *`natural_pk` on `model` alone.* Rejected -- the `ha` query parameter materially
   changes the response (HA gateways get a different default port layout), so a single
   `model` value can produce two distinct payloads. Single-column PK would force one
   poll to overwrite the other.
3. *No PK / append-only log.* Rejected -- would let the SQLite table grow unbounded
   on repeated reference lookups and defeats the upsert semantics every other
   MistHelper endpoint observes.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/default_gateway_config_<model>[_ha].csv`
  (the `_ha` suffix appears only when `ha=true` was requested)
- SQLite table: `default_gateway_config`
- ArangoDB collection: `default_gateway_config` (same name; backend selection happens
  inside `DataExporter`, MistHelper does not branch)

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getGatewayDefaultConfig"` (matching the operationId exactly). The DataExporter
uses that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

Both the `model` value used in the filename and the `ha_flag` suffix are sanitized via
`re.sub(r'[^a-z0-9_-]', '_', model.lower())` to remain Windows-path-safe. Model strings
in Mist's documentation are already short alphanumeric tokens (`srx320`, `ssr120`,
`srx345`, `srx380`), so the sanitizer is a defensive no-op for normal inputs.

**Rationale**:
Matches the naming pattern used by `device_models` and other constants/reference
endpoints already in MistHelper -- a flat filename embedding the discriminating query
parameter(s). The single-table design is justified because the response is exactly one
config blob per (model, ha) and there is no nested array that needs its own table
(unlike, for example, `getOrgLicenseAsyncClaimStatus` which has a separate per-device
`details` array).

**Alternatives Considered**:

1. *One table per top-level response key (`dhcpd_config`, `networks`,
   `service_policies`, etc).* Rejected -- the nested structure is irregular per model;
   keeping the raw JSON in a single `config_json` column preserves fidelity and lets
   downstream consumers parse what they need without a five-table join.
2. *One row per `port_config` entry (i.e., explode the port_config dict into rows).*
   Rejected -- port identifiers are model-specific and rarely useful as primary search
   keys; flattening blows the row count up without operational benefit. Operators who
   want per-port detail can `json_extract` from the `config_json` column.
3. *Include `ha` in the table name (`default_gateway_config_ha`).* Rejected --
   doubles the schema for no benefit; the `ha_flag` column already discriminates.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org Exports
cluster, specifically in the Misc subrange (56-59). The category label is "Safe Org
Exports -- Constants / Gateway".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports (with sub-clusters: Sites 1-7, Inventory 8-14, Device stats
15-19, Events 20-26, Clients 27-30, Gateways 31-36, Templates 37-41, Config/Admin
42-50, SLE 51-55, Misc 56-59), 60-96 Interactive Safe, 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. This endpoint
returns *constants* -- it has no org_id and no destructive effect -- so it belongs in
the safe block. The Misc 56-59 subrange is the natural home for read-only
constants/reference lookups that do not fit a more specific theme. 58 is the next
contiguous integer in that subrange (assuming 56-57 are taken; the actual collision
check runs at `/speckit.tasks` time and the number shifts to 57 or 59 if needed). The
number is far away from the destructive cluster, so a junior NOC engineer scrolling
the menu is given the correct risk signal.

**Alternatives Considered**:

1. *Slot inside the Gateway 31-36 cluster (e.g., 36).* Rejected -- 31-36 is for
   org-scoped gateway operations that consume an `org_id`. This endpoint is global and
   has no org context, so grouping it with org-scoped gateway exports is misleading.
2. *Append to the end of the menu (e.g., 195).* Rejected -- the destructive cluster
   ends at 194; placing a constants lookup above the destructive block visually
   mis-signals the risk level.
3. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns a few KB of JSON, with no pagination and no long-running work.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `model` -- prompt: `"Gateway model (e.g. srx320, ssr120): "`, context:
   `"default_gateway_config:model"`. Default: the value of `MIST_DEFAULT_GATEWAY_MODEL`
   in `.env` if present (pressing Enter accepts the default; if no default is set,
   pressing Enter logs a `WARNING` and returns early). The value is lowercased before
   the API call.
2. `ha` -- prompt: `"HA configuration variant? (y/N): "`, context:
   `"default_gateway_config:ha"`. Default: `N` (no HA). On `y` or `yes`
   (case-insensitive), the SDK is called with `ha="true"`; otherwise `ha=None` is
   passed so the query string omits the parameter.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_DEFAULT_GATEWAY_MODEL` -- optional default for prompt 1. When unset, the
  `--test` sweep uses the hard-coded fallback `srx320` so the smoke run does not block
  on an interactive prompt.

**Rationale**:
The Mist `default_gateway_config` endpoint is global, not org-scoped, so no `org_id`,
`site_id`, or `device_id` is collected. The `model` query parameter is required by the
upstream API, and the `ha` parameter materially changes the response (HA gateways have
different port assignments), so both must be exposed. Allowing a `.env` default for
`model` keeps non-interactive runs (`python MistHelper.py --menu 58 < /dev/null`)
deterministic and lets the `--test` sweep complete without operator input.

**Alternatives Considered**:

1. *Single prompt that asks the user to pick a model from an enumerated list fetched
   from `/api/v1/const/device_models` first.* Rejected -- adds a second API call and
   couples this menu item to a second endpoint contract. The user already knows what
   model they own; a free-text prompt is faster.
2. *Always request `ha=true` to keep the prompt count to one.* Rejected -- the HA
   default is a different payload, and operators querying non-HA gateways would get
   misleading reference data.
3. *Prompt for an output filename override.* Rejected -- adds keystrokes without
   operational value. The deterministic filename scheme in Research Task 3 makes
   results easy to find under `data/`.
