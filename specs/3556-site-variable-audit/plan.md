# Implementation Plan: Site Variable Audit

**Branch**: `3556-site-variable-audit` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3556-site-variable-audit/spec.md`

## Summary

Add Menu 275 as a read-only site variable coverage audit. The operation reads
sites, assigned templates, WLANs, and site variables through `mistapi`, scans
assigned template bodies for `{{name}}` tokens, and writes two CSV reports with
`DataExporter`. The design uses a new package at
`src/reports/site_variable_audit/` with a client module, a model module, and an
operation module.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, `SourceDependencyResolver`,
`DataExporter`, and standard-library modules only.

**Storage**: CSV reports under `data/`. No database schema change is required.

**Testing**: `pytest` unit tests under
`tests/unit/reports/site_variable_audit/`.

**Target Platform**: Windows local development and Linux container execution.

**Project Type**: MistHelper CLI menu operation.

**Performance Goals**: Read each unique gateway template, network template,
template, WLAN, device profile, and site variable search result once per run.

**Constraints**: Do not call per-site settings retrieval. Do not mutate Mist
configuration. Use deterministic row order for repeated runs with same input.

**Scale/Scope**: One organization, all sites in that organization, assigned
gateway templates, network templates, WLANs, and device profiles.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I. Five-Item Rule

Pass. The feature adds one compliant nested package:
`src/reports/site_variable_audit/`. The planned package has three modules:
`client.py`, `model.py`, and `operation.py`. The tests use one matching nested
directory.

### Principle II. Class-Based Architecture

Pass. The design uses `SiteVariableAuditClient`, model dataclasses, and
`SiteVariableAudit`. No wrapper function is planned.

### Principle III. Safety-First

Pass. The operation is read-only. It uses `SourceDependencyResolver` for the API
session and organization context. It does not prompt in `--test`.

### Principle IV. Full Deployment Pipeline

Pass for planning. Implementation must run the local gates that apply to the
changed files. This step does not commit or push.

### Principle V. Observability and Logging

Pass. The implementation must log before and after each API read, transform, and
CSV write. Log output must use ASCII only.

### Principle VI. Inline Comments

Pass. The implementation must add inline comments to every new executable line.
This plan adds no Python code.

### Principle VII. Action Logging

Pass. The implementation must add action logging before and after each
meaningful operation.

## Project Structure

### Documentation for this feature

```text
specs/3556-site-variable-audit/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── wiring.md
├── contracts/
│   └── report-contract.md
└── tasks.md
```

`tasks.md` is created by the task workflow, not by this plan step. `wiring.md`
is deferred to implementation, but tasks must create it before the integration
pull request.

### Source code

```text
src/reports/site_variable_audit/
├── __init__.py
├── client.py
├── model.py
└── operation.py

tests/unit/reports/site_variable_audit/
├── test_client.py
└── test_model.py
```

**Structure Decision**: Use one nested report package. `client.py` isolates
`mistapi` reads. `model.py` holds pure dataclasses and pure functions.
`operation.py` wires `SourceDependencyResolver`, the client, the model, and
`DataExporter`.

## Planned Modules

### `client.py`

`SiteVariableAuditClient` reads all required Mist data through installed
`mistapi` functions:

- `mistapi.api.v1.orgs.sites.listOrgSites`
- `mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates`
- `mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates`
- `mistapi.api.v1.orgs.templates.listOrgTemplates`
- `mistapi.api.v1.orgs.wlans.listOrgWlans`
- `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles`
- `mistapi.api.v1.orgs.vars.searchOrgVars`

The client must support fixture injection for tests. Tests must not use the
network.

### `model.py`

The model module owns pure functions and dataclasses. It extracts variable
tokens from nested dictionaries and lists. It builds audit rows and summary
rows from already loaded records.

Planned dataclasses:

- `TemplateReference`
- `VariableTokenUse`
- `SiteVariableDefinition`
- `MissingVariableFinding`
- `SiteVariableSummary`
- `SiteVariableAuditResult`

### `operation.py`

`SiteVariableAudit.run()` takes no positional argument. It reads the API session
and organization data through `SourceDependencyResolver`. It writes
`SiteVariableAudit.csv` and `SiteVariableSummary.csv` with `DataExporter`.

## Mist API Contract

The feature uses these OpenAPI operations:

| Operation ID | Method and path | Required input | Optional query | Responses |
| - | - | - | - | - |
| `listOrgSites` | `GET /api/v1/orgs/{org_id}/sites` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgGatewayTemplates` | `GET /api/v1/orgs/{org_id}/gatewaytemplates` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgNetworkTemplates` | `GET /api/v1/orgs/{org_id}/networktemplates` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgTemplates` | `GET /api/v1/orgs/{org_id}/templates` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgWlans` | `GET /api/v1/orgs/{org_id}/wlans` | `org_id` | `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `listOrgDeviceProfiles` | `GET /api/v1/orgs/{org_id}/deviceprofiles` | `org_id` | `type`, `limit`, `page` | `200`, `400`, `401`, `403`, `404` |
| `searchOrgVars` | `GET /api/v1/orgs/{org_id}/vars/search` | `org_id` | `site_id`, `var`, `src`, `limit`, `page` | `200`, `400`, `401`, `403`, `404` |

## Deferred Integration Work

The integration pull request must add:

- Menu 275 registration in `MistHelper.py`.
- An `OperationRegistry` entry for Menu 275.
- Generated menu references.
- A complete `specs/3556-site-variable-audit/wiring.md` manifest.

This planning step must not edit those files.

The implementation step in this branch must add:

- A release note fragment at
  `changelog.d/issue-3556-site-variable-audit.md`.

## Complexity Tracking

No constitution violation is planned.

## Post-Design Constitution Check

The design still passes all constitution gates. The planned feature remains
read-only, uses a compliant nested package, uses existing dependencies, avoids
per-site settings calls, and keeps source integration work deferred.
