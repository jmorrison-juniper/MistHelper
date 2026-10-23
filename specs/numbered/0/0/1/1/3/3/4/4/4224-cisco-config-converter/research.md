# Research: Mist Cisco Config Converter

**Date**: 2026-10-18
**Feature**: [Mist Cisco Config Converter](spec.md)

## Existing MistHelper Portal

**Decision**: Add the converter as a Flask blueprint in the existing portal. Keep its routes,
models, templates, and browser behavior in the feature package.

**Rationale**: The portal factory registers the current blueprints, and the shared base template
owns the navigation. The feature package avoids another module in the overfull
`web_portal/routes/` directory.

**Alternatives considered**:

- Add another module to `web_portal/routes/`. Rejected because the directory is already overfull.
- Run a separate converter application or Compose group. Rejected because the feature belongs in
  the existing MistHelper portal.

**Integration decision**: Reconcile changes to shared portal registration and navigation files
with their current owner before implementation changes are published. Keep WAN Performance
registration conditional on its package being present.

## Mist API Contract

**Verified contract**: The local OpenAPI identifies
`POST /api/v1/orgs/{org_id}/gatewaytemplates` as `createOrgGatewayTemplate`. The installed
`mistapi` SDK exposes `mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate` with the
signature `(mist_session, org_id, body)`. The request body uses the gateway-template schema
directly. The schema requires `name`, accepts `standalone` and `spoke`, and defines
`dns_servers` as an array of strings.

**Decision**: Do not call the SDK operation in the first release. Contract verification does not
authorize a cloud change. Defer apply until separate scope and approval exist.

## Input Parsing and License

**Decision**: Implement parsing and conversion from original code and verified public contracts.
Show unsupported commands and known gaps. Do not copy code, mappings, documentation text, or
images from the source repository.

**Rationale**: The source repository uses CC BY-NC 4.0. The issue requires an original
implementation. The supported subset maps global IPv4 `ip name-server` commands to
`dns_servers`. No verified source supports hardware-role or hardware-model mappings.

**Alternatives considered**:

- Port the source converter as-is. Rejected because the issue prohibits source copying before
  license approval.
- Hide commands that the converter does not support. Rejected because operators must see
  unsupported input before export.

## Validation and Storage

**Decision**: Process uploads in memory. Accept `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, and
`.log` files up to 16 MiB. Reject path-like names, invalid UTF-8, null characters, and oversized
files. Do not add a database or Redis service.

**Rationale**: MistHelper has no shared portal upload-size setting. The feature uses the observed
16 MiB source limit and a 16 KiB multipart overhead bound. Preview does not need durable storage.

**Alternatives considered**:

- Create a separate database or Compose stack. Rejected because the feature must use the
  existing runtime.
- Store credentials or configuration in browser storage. Rejected because the security
  requirements prohibit it.

## Test Layout

**Decision**: Place parser and conversion tests in
`tests/unit/gateway/overrides/test_cisco_config_converter.py`. Place route tests under
`tests/integration/web_portal/cisco_config_converter/`. Place browser acceptance under
`tests/e2e/web_portal/test_portal_smoke.py`.

**Rationale**: These locations keep feature tests in named directories and avoid adding direct
children to overfull test directories.

**Alternatives considered**:

- Add test modules directly under `tests/unit/` or `tests/e2e/web_portal/`. Rejected because
  those directories are overfull.
