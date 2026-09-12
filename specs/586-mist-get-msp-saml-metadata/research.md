# Phase 0 Research: getMspSamlMetadata

**Feature**: `586-mist-get-msp-saml-metadata`
**Date**: 2026-06-29
**Source doc**: `documentation/api/msps/GET_msps_msp_id_ssos_sso_id_metadata.md`

This document captures the five Phase 0 research decisions required by the SpecKit
`/speckit.plan` workflow. Each task uses the Decision / Rationale / Alternatives
Considered format.

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke the endpoint via
`mistapi.api.v1.msps.ssos.metadata.getMspSamlMetadata(apisession, msp_id, sso_id)`,
positional arguments only. The call returns a `mistapi.APIResponse` whose `.data`
attribute is a single JSON object (not a list) with up to five optional string fields:
`acs_url`, `entity_id`, `logout_url`, `metadata` (raw XML blob), and `scim_base_url`.
The endpoint is **not paginated**. The doc shows the SDK module path as
`mistapi.api.v1.msps.sso.getMspSamlMetadata()`; the implementer must resolve the actual
import path at task generation time by inspecting `mistapi` 0.59+ installed in the venv
(the openapi-derived path `mistapi.api.v1.msps.ssos.metadata` is the authoritative
fall-back when the doc and SDK disagree).

**Rationale**: The enriched per-endpoint doc at
`documentation/api/msps/GET_msps_msp_id_ssos_sso_id_metadata.md` declares HTTP `GET
/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata`, lists both `msp_id` and `sso_id` as
required path parameters, has no query parameters, and shows a flat object schema. No
pagination cursor is present. The mistapi 0.59+ SDK convention is one Python function
per OpenAPI operationId, with the apisession as the first parameter and path parameters
following in OpenAPI order; this matches every other GET method in the codebase
(`listOrgSites`, `getOrgLicensesSummary`, `getOrgLicenseAsyncClaimStatus`, etc.).

**Alternatives Considered**:

- Direct `requests.get()` call -- rejected. Bypasses the project's sole-SDK rule, breaks
  `mistapi.APISession` rate-limit handling, and forfeits the adaptive delay metrics that
  every other menu item benefits from.
- Use the `.xml` variant
  (`GET /api/v1/msps/{msp_id}/ssos/{sso_id}/metadata.xml`) -- rejected for this spec.
  The spec scope is the JSON endpoint only; the XML variant is a separate operationId
  and would be added under its own future spec if needed. The JSON variant already
  embeds the full XML string in the `metadata` field, so downstream IdP administrators
  can extract it without a second call.

## Research Task 2: Primary Key Strategy

**Decision**: Use `composite_pk` keyed on `(msp_id, sso_id)`. Both columns are populated
from the path parameters supplied by the user (the response body itself does not echo
them). The DataExporter row must therefore inject `msp_id` and `sso_id` into the
flattened dict before write.

**Rationale**: The response is a single object per `(msp_id, sso_id)` pair and contains
no stable identifier of its own (`entity_id` is a URL that may rotate when SAML keys
roll). A composite of the two path parameters is the natural, stable, business-meaningful
key: each (MSP, SSO config) tuple has exactly one current SAML metadata document. This
satisfies the constitution's "natural business keys" rule and enables clean
`INSERT OR REPLACE` upserts in SQLite when the user re-runs the menu item after an IdP
trust refresh.

**Alternatives Considered**:

- `natural_pk` on `entity_id` alone -- rejected. `entity_id` is described in the OpenAPI
  schema as read-only and conditional (`If idp_type==saml`), so it can be absent when
  the SSO is OAuth-only, leaving the row without a usable PK.
- `auto_increment_with_unique` -- rejected. This is the documented fallback for
  aggregated rollups without stable keys; here we have two perfectly stable keys from
  the URL path, so the cheaper composite_pk path is correct.

## Research Task 3: Output filename and SQLite table

**Decision**: Output base name `msp_saml_metadata`. CSV path
`data/msp_saml_metadata.csv`. SQLite table `msp_saml_metadata` in `data/mist_data.db`.

**Rationale**: The existing MistHelper naming convention is
`<scope>_<resource>[_<sub_resource>]` lowercase with underscores -- matching
`org_sites`, `org_license_summary`, `site_devices`. The MSP scope is uncommon enough in
the current codebase that no `msp_*` prefix collision exists; using `msp_saml_metadata`
keeps the file name short, greppable, and obviously distinct from any future
`org_saml_metadata` (the org-level cousin under a different path).

**Alternatives Considered**:

- `msp_sso_metadata` -- rejected. Less specific; the endpoint is SAML-specific and a
  future OAuth metadata endpoint would collide.
- `getMspSamlMetadata.csv` (operationId verbatim) -- rejected. Mixed case breaks the
  established lowercase-snake convention and is uglier on Linux containers.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place under the **Misc** cluster (operations 56-59). Propose menu number
**58**. If 58 collides with an in-flight feature branch at task generation time, use the
next free integer in the same cluster, or the next contiguous free integer above 50
within the Safe Org Exports / Misc band.

**Rationale**: The MistHelper menu taxonomy documented in `agents.md` and
`.github/copilot-instructions.md` reserves:

- 1-59 for Safe Org Exports (Sites, Inventory, Device stats, Events, Clients, Gateways,
  Templates, Config/Admin, SLE, Misc)
- 60-96 for Interactive Safe operations
- 97-101 / 153 for Resource Intensive
- 102-194 for WebSocket, Interactive, Continuous, and Destructive

MSP SAML metadata is a read-only administrative read with no destructive effect, no
fan-out, no long-running behavior, and no interactive prompt beyond two ID inputs. The
56-59 Misc band is the documented home for read-only administrative endpoints that do
not fit Sites/Inventory/Templates/SLE; menu 58 is the next conventional slot.

**Alternatives Considered**:

- 42-50 Config/Admin band -- rejected. That band is already saturated with org-level
  config exports (Webhooks, Alarm Templates, etc.); inserting an MSP-scope item there
  would force a renumber of adjacent items.
- A new MSP-only cluster (e.g., 195+) -- rejected. Premature. With only one MSP
  endpoint being added, splitting out a dedicated band creates a sparse cluster.
  Revisit when 3+ MSP endpoints have been cataloged.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Prompt the user for **both** `msp_id` and `sso_id` interactively via
`safe_input()`. Neither value is read from `.env`. The Mist API session credentials
(`MIST_HOST`, `MIST_API_TOKEN`) continue to come from `.env` via the existing
`mistapi.APISession` initialization that all other menu items share. In `--test` mode,
fall back to optional env vars `MIST_TEST_MSP_ID` and `MIST_TEST_SSO_ID` so the
non-interactive sweep can exercise the menu item.

**Rationale**: The codebase convention is: tenant credentials (token, host, org default)
in `.env`; per-call selectors (specific UUIDs the user wants to query right now) from
prompts. `msp_id` and `sso_id` are per-call selectors -- a user can manage many MSPs and
each MSP can host many SSO configurations, so caching one in `.env` would mislead. The
`--test` env vars mirror the existing `MIST_TEST_ORG_ID` / `MIST_TEST_SITE_ID` pattern
already used by adjacent menu items.

**Alternatives Considered**:

- Pull both IDs from `.env` always -- rejected. Defeats the purpose of an interactive
  selector and breaks the menu item for users who legitimately query multiple MSP/SSO
  combinations in one session.
- Auto-list all MSPs and SSOs first and let the user pick by index -- rejected for this
  spec. That would require chaining two additional API calls (`listMsps` and
  `listMspSsos`) which are not in scope. A future enhancement spec can layer that on
  top of this base operation.
