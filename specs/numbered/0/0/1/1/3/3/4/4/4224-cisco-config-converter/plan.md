# Implementation Plan: Mist Cisco Config Converter

**Branch**: `jmorrison-juniper-4224-cisco-config-converter` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Numeric feature specification from `/specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md`

## Summary

Add a Cisco IOS conversion tab to the existing MistHelper web portal. Build original parsing and conversion rules, show unsupported input, and support preview and export without credentials. For cloud apply, create a new organization gateway template through the Mist SDK after review, credential checks, and typed confirmation. Do not update an existing template or attach a template to a site in this feature.

## Technical Context

**Language/Version**: Python 3.13 or newer, with HTML and JavaScript for the existing portal.

**Primary Dependencies**: Flask and `mistapi` 0.64.0. The feature must use the existing portal and SDK.

**Storage**: No new database or Redis service. Keep uploaded input and generated output within the existing configured portal data area, with the established retention rules.

**Testing**: pytest for unit and integration coverage, plus the existing Playwright browser suite for the portal.

**Target Platform**: The existing MistHelper web portal on Windows 11, macOS, Linux, and the product container.

**Project Type**: Flask web application integrated with the existing MistHelper runtime.

**Performance Goals**: Use the existing portal upload limit and processing behavior. This feature adds no separate latency target.

**Constraints**: Validate file type, size, encoding, and resolved path. Do not log or persist credentials. Do not copy source code or images before maintainers approve a license-compatible path. Do not add a database, Redis service, or Compose group. Require a typed confirmation before a cloud change.

**Scale/Scope**: One operator at a time per browser session. The first release handles Cisco IOS inputs and gateway role and model pairs supported by an approved mapping.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Managed specification route**: Pass. This record uses the required eight-digit base-5 route for issue 4224.
- **Process-folder policy**: Pass. The feature record is under `specs/numbered/`. It adds no unmanaged direct child to `specs/`. The baseline has 792 grandfathered direct children. Keep the baseline guard readable and use its incremental ratchet for later folder cleanup.
- **Five-item structure rule**: Pass with the structure below. Add one package under `src/interfaces/portals/`, which currently has two direct children. Keep each new package at five children or fewer. Do not add a direct child to the already overfull `web_portal/routes/`, `tests/`, or `tests/unit/` directories. Put parser and conversion unit tests in `tests/unit/gateway/overrides/`, which currently has four direct children. Put route and SDK tests under the new `tests/integration/web_portal/cisco_config_converter/` package, and extend the existing web portal smoke test instead of adding a file to the overfull browser-test directory.
- **Existing structure debt**: The repository has established overfull test and portal directories. This feature does not increase their direct-child counts. Track the existing debt through the process-folder and nested-package guard baselines. Remediate it separately from this feature.
- **Mist Cloud calls**: Use the SDK operation `createOrgGatewayTemplate` only to create a new organization template. The OpenAPI operation is `POST /api/v1/orgs/{org_id}/gatewaytemplates`. This feature does not update an existing template or assign a template to a site or device. Before implementation, verify the exact SDK import and call signature against the installed 0.64.x package, then add contract tests for authentication, endpoint parity, failure safety, and secret redaction. Do not use direct HTTP or an owned WebSocket transport.
- **Safety and secrets**: Preview and export make no cloud request. Apply requires an organization, credentials, a reviewed proposal, and typed confirmation. Do not log credentials or store them in client-side state or generated files.
- **Class-based architecture**: Keep parsing, conversion, routes, and browser behavior in semantically named classes. Do not add standalone behavior wrappers.
- **Inline comments and action logging**: Follow the constitution for generated executable lines, meaningful action logs, ASCII log output, and secret exclusion.
- **Compatibility**: Register one new blueprint and navigation entry. Keep all existing portal routes and workflows unchanged.
- **Deployment**: Keep product output under `data/`. Verify that the feature adds no service, volume, network, database, Redis instance, or Compose group. Use existing shared services only when required.
- **Complete delivery pipeline**: Follow Constitution Principle IV after implementation and release-note changes. This planning request does not authorize future commit, pull-request, merge, or deployment actions.
- **Release notes**: Add one issue-specific changelog fragment when implementation starts.
- **Workflow scope**: This planning request does not implement code, commit, push, or open a pull request.

No constitution violation is required by this plan. SDK signature verification and license approval are explicit implementation prerequisites.

## Phase 0: Research

See [research.md](research.md). The design uses existing portal patterns, a new feature-owned package, validated file handling, original conversion rules, and a new organization gateway template for apply.

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/portal.md](contracts/portal.md), [contracts/mist-apply.md](contracts/mist-apply.md), and [quickstart.md](quickstart.md).

### Project Structure

#### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/
├── checklists/requirements.md
├── contracts/
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
├── spec.md
└── tasks.md
```

#### Source Code

```text
src/interfaces/portals/cisco_config_converter/
├── __init__.py
├── conversion.py
├── models.py
├── routes.py
└── presentation/
    ├── converter.html
    └── converter.js

web_portal/
├── app.py
└── templates/
    └── base.html

tests/unit/gateway/overrides/
└── test_cisco_config_converter.py

tests/integration/web_portal/cisco_config_converter/
├── __init__.py
├── test_routes.py
└── test_sdk_contract.py

tests/e2e/web_portal/test_portal_smoke.py
```

Keep the package at five direct children. Keep the feature page and script in its presentation directory and expose them through its blueprint. Keep parser and conversion tests in the existing gateway overrides unit-test directory. Do not add new files under the saturated `web_portal/routes/` or `tests/e2e/web_portal/` directories.

**Structure Decision**: Keep parsing, conversion, data models, and route ownership in one new package under `src/interfaces/portals/`. The package contains five direct children: its initializer, conversion module, model module, route module, and presentation directory. The presentation directory owns `converter.html` and `converter.js`. Register its blueprint through the existing Flask app factory. Extend the existing portal navigation and smoke journey. Add parser and conversion unit tests to `tests/unit/gateway/overrides/` and route and SDK contract tests to the new integration package.

## Complexity Tracking

No complexity exception is proposed. Keep each feature package at five direct children or fewer. Use existing portal services and test fixtures rather than adding another service layer or runtime.

## Implementation Gates

1. Obtain maintainer approval for a license-compatible implementation path before using source-derived code or assets. This plan requires original code and assets.
2. Verify and record the existing portal upload size limit and file-type policy. Do not start parser implementation until the value and boundary behavior are known.
3. Verify `mistapi` 0.64.x exposes `createOrgGatewayTemplate` with the expected request and response contract. If it does not, stop implementation and revise the contract before selecting another Mist operation.
4. Confirm the selected gateway role and hardware model mapping from approved, license-compatible product requirements. Do not infer support from unreviewed source material.
5. Obtain product-owner approval for creating a new organization gateway template as the exact cloud effect. If it is not approved, record the requested effect and revise the spec and contracts before implementation.
6. Prove that preview and export run without Mist credentials and that template creation sends no request without typed confirmation.
