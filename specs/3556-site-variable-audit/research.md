# Research: Site Variable Audit

## Decision: Use installed `mistapi` functions for all Mist reads

The implementation must call the installed SDK functions:

- `mistapi.api.v1.orgs.sites.listOrgSites`
- `mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates`
- `mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates`
- `mistapi.api.v1.orgs.templates.listOrgTemplates`
- `mistapi.api.v1.orgs.wlans.listOrgWlans`
- `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles`
- `mistapi.api.v1.orgs.vars.searchOrgVars`

**Rationale**: The project constitution prohibits direct HTTP calls when a
`mistapi` method exists. The installed `mistapi` package includes all required
functions.

**Alternatives considered**: Direct REST calls were rejected because matching
SDK methods exist. Per-site settings calls were rejected because the feature
must not call them for each site.

## Decision: Use organization-scoped list and search operations

The implementation uses these OpenAPI operations:

| Operation ID | Method and path | Required input | Optional query | Responses |
| - | - | - | - | - |
| `listOrgSites` | `GET /api/v1/orgs/{org_id}/sites` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgGatewayTemplates` | `GET /api/v1/orgs/{org_id}/gatewaytemplates` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgNetworkTemplates` | `GET /api/v1/orgs/{org_id}/networktemplates` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgTemplates` | `GET /api/v1/orgs/{org_id}/templates` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgWlans` | `GET /api/v1/orgs/{org_id}/wlans` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgDeviceProfiles` | `GET /api/v1/orgs/{org_id}/deviceprofiles` | `org_id` | `type`, `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `searchOrgVars` | `GET /api/v1/orgs/{org_id}/vars/search` | `org_id` | `site_id`, `var`, `src`, `limit`, `page` | `200`, `400`, `401`, `403`, `404` |

**Rationale**: These endpoints provide the organization-wide inputs needed for
the audit. They also support pagination through `limit` and `page`.

**Alternatives considered**: Site-scoped settings retrieval was rejected because
it violates the performance requirement. A narrow `searchOrgVars` call for one
variable was rejected because Menu 149 already covers only `wan2_interface`.

## Decision: Search all site variables with `searchOrgVars`

The client must call `searchOrgVars` with `var=*`. It can add `site_id` when an
implementation task proves a per-site search is needed for a bounded fixture or
fallback path.

**Rationale**: The Juniper Mist WAN guidance says site variables can be searched
with `GET /api/v1/orgs/:org_id/vars/search?var=*`. This supports an audit that
does not know variable names before scanning templates.

**Alternatives considered**: Searching one variable at a time was rejected
because the audit must find missing and unused variables across all assigned
templates.

## Decision: Use double curly brace token syntax

The scanner must find `{{name}}` tokens in strings at any depth. It must
normalize surrounding spaces, so `{{ name }}` becomes `name`.

**Rationale**: Juniper Mist WAN guidance states that site variables use double
curly brackets, cannot contain spaces, and allow underscores. Mist management
guidance states that site variables are site scope values used by templates for
site-specific text.

**Alternatives considered**: A parser for malformed brace text was rejected.
The scanner must ignore incomplete tokens and report only complete valid tokens.

## Decision: Keep variable analysis in pure model functions

The model layer must accept already loaded dictionaries and return dataclass
records. It must not call Mist APIs, write files, or read environment state.

**Rationale**: Pure functions make the nested token scanner and count logic easy
to test without a network.

**Alternatives considered**: Placing scan logic in the operation class was
rejected because it would mix API reads, transformation, and file writes.

## Decision: Use `SourceDependencyResolver` and `DataExporter`

`SiteVariableAudit.run()` must obtain the API session and organization context
through `SourceDependencyResolver`. It must write reports through
`DataExporter.write_with_format_selection`.

**Rationale**: Existing new menu operations use this pattern. The closest
examples are `src/security/rogue_dhcp/operation.py` and
`src/marvis/actions/operation.py`.

**Alternatives considered**: Direct file writes were rejected because report
exports must use existing output backend behavior.

## Decision: Defer menu wiring to the integration pull request

This plan defines the package and contracts. The integration pull request adds
the Menu 275 registration, the `OperationRegistry` entry, and generated
references. This branch adds the release note fragment and the final wiring
manifest because the fleet contract assigns those files to this feature branch.

**Rationale**: The fleet contract for this step allows edits only under
`specs/3556-site-variable-audit/`.

**Alternatives considered**: Editing `MistHelper.py`, `operation_registry.py`,
or `changelog.d/` was rejected because this planning step must not touch them.
The implementation step can add the assigned release note fragment.
