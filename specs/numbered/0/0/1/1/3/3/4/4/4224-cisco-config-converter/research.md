# Research: Mist Cisco Config Converter

**Date**: 2026-10-14
**Feature**: [Mist Cisco Config Converter](spec.md)

## Existing MistHelper Portal

**Decision**: Add a new Flask blueprint to the existing portal and register it through `WebPortalApp._register_blueprints`. Add a portal navigation link in the shared base template. Keep the feature's routes, templates, and static files within its own package.

**Rationale**: `web_portal/app.py` registers the current portal blueprints, and `web_portal/templates/base.html` contains the global navigation. The dedicated package avoids another module under the overfull `web_portal/routes/` directory.

**Alternatives considered**:

- Add another module to `web_portal/routes/`. Rejected because the directory already has more than five direct children.
- Run a separate converter application or Compose group. Rejected because issue #4224 requires one MistHelper portal and its existing services.

## Mist Cloud Apply

**Decision**: Create a new organization gateway template with the Mist SDK operation `createOrgGatewayTemplate`. Do not update an existing template or attach the new template to a site or device.

**Rationale**: The Mist API specification identifies `POST /api/v1/orgs/{org_id}/gatewaytemplates` as `createOrgGatewayTemplate` and accepts the `gateway_template` request schema. Creating a new template avoids overwriting existing configuration. The issue names organization selection and typed confirmation but does not request site assignment.

**Alternatives considered**:

- Update an existing organization template. Rejected because issue #4224 does not identify a target template, and an update could replace existing settings.
- Apply settings directly to a gateway or site. Rejected because the issue does not identify a device-level operation, and the API specification does not identify a matching gateway-wide update operation.
- Use direct HTTP. Rejected because MistHelper requires the supported `mistapi` package for Mist REST access.
- Use an owned WebSocket. Rejected because the feature needs a single configuration write, not a live stream.

**Implementation check**: `mistapi` is not installed in this workspace. Before implementation, verify the operation's SDK module, function signature, authentication, payload, and response against the repository's required 0.64.x package. Do not treat the OpenAPI operation name alone as proof of SDK support.

## Input Parsing and License

**Decision**: Implement parsing and conversion from original code and approved mapping requirements. Show unsupported commands and known gaps. Do not copy code, mappings, documentation text, or images from the source repository until maintainers approve a license-compatible path.

**Rationale**: Issue #4224 states that the source repository uses CC BY-NC 4.0 and prohibits code and image copying before approval. The issue also requires visible conversion limitations.

**Alternatives considered**:

- Port the source converter as-is. Rejected because the issue prohibits source copying before license approval.
- Hide commands that the converter does not support. Rejected because operators must see unsupported input before they export or apply a proposal.

## Validation and Storage

**Decision**: Use the existing portal upload limits and configured data area. Validate file type, size, encoding, and resolved path before parsing. Do not add a database or Redis service.

**Rationale**: The issue requires safe input paths and shared MistHelper services. Preview does not need durable state, and no data schema change is required by the issue.

**Alternatives considered**:

- Create a separate database or Compose stack. Rejected by the issue's compatibility constraints.
- Store credentials or configuration in browser storage. Rejected by the issue's security requirements.

## Test Layout

**Decision**: Place new parser, conversion, route, and SDK contract tests under `tests/integration/web_portal/cisco_config_converter/`. Extend the existing `tests/e2e/web_portal/test_portal_smoke.py` for the browser journey.

**Rationale**: The parent integration package has one direct child, so it can accept one feature package within the five-item rule. The browser-test directory already exceeds that limit, so the plan adds no new direct child there.

**Alternatives considered**:

- Add new test modules directly under `tests/unit/` or `tests/e2e/web_portal/`. Rejected because those directories already exceed the five-item limit.
