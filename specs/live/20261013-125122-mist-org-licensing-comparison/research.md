# Research: Mist Organization Licensing Comparison

**Date**: 2026-10-13
**Feature**: [spec.md](spec.md)

## Mist Session and Organization Access

**Decision**: Reuse `current_app.config["APISESSION"]`. Read the existing `getSelf` response for MSP grants. Use `listMspOrgs` only for MSP scopes that the response grants. Include the configured organization when the session has one. Validate every submitted organization against these server-side results.

**Rationale**: `web_portal/app.py` injects the shared session as `APISESSION`. The current operations route already reads `getSelf` and returns permitted MSP rows. A browser-provided organization ID does not prove access.

**Alternatives considered**: Create a new Mist session or call a new organization discovery service. Both would duplicate shared authentication and add a second access path.

## License and Inventory Reads

**Decision**: Use the installed `mistapi` SDK with the active session. The API reference names `getOrgLicensesSummary`, `getOrgLicensesBySite`, `getOrgInventory`, and `listMspOrgs`. The existing portal also uses `getSelf`.

**Rationale**: The local API reference identifies these operations. MistHelper already uses `getOrgInventory`. The existing portal contract test checks SDK calls against the installed package.

**Alternatives considered**: Direct REST requests or a new transport. Both bypass the supported SDK and its session contract.

**Verification**: The implementation must add each new call to the installed-SDK contract check. Tests must confirm 4xx and 5xx responses remain errors. No new endpoint path may rely only on a mock.

## Portal Placement

**Decision**: Add a blueprint package under `src/interfaces/portals/licensing_comparison/`. Register it in the existing `web_portal` app. Extend the current navigation and use the source dashboard's comparison flow.

**Rationale**: The existing Flask app already owns portal startup, security, the shared session, and the common page frame. The current `web_portal/routes/` and `web_portal/templates/` directories exceed the five-child limit. The selected source package parent has room for a new child.

**Alternatives considered**: Add another web server, a new portal service, or a second frontend. Each conflicts with issue #4197 and the feature constraints.

## Manual State and Purchased Values

**Decision**: Store manual rows and purchased amounts in browser `sessionStorage`. Do not send them to a durable store during normal comparison requests.

**Rationale**: The source app has no persistent database and no documented Redis cache. The requested state ends with the browser session.

**Alternatives considered**: Add database tables, Redis keys, or server-side sessions. Each adds persistent state that the user excluded.

## CSV Export

**Decision**: Send only the operator-requested comparison export through `DataExporter.write_with_format_selection`. Use the existing data directory and the portal's safe file download service. Neutralize formula-like cell values before writing.

**Rationale**: MistHelper documents the shared exporter as the standard export path. The existing data browser validates paths before it serves a file.

**Alternatives considered**: Add a new export service or expose a path from the browser. Both duplicate shared behavior and increase risk.

## Rate Limits and Failure Handling

**Decision**: Use `RateLimitingUtils` and send one Mist request at a time. After HTTP 429, wait 60 seconds per token and retry once. Show the failure if that retry fails.

**Assumption**: The source documents the 60-second wait but does not state a retry count. This plan uses one retry to bound the work.

**Rationale**: The source behavior is in the issue description. A missing response must not look like a zero balance.

**Alternatives considered**: Retry without a bound or convert failures to zero. Unbounded retry can hold portal work, and a false zero can mislead an operator.

## Attribution

**Decision**: Preserve CC BY-NC-SA 4.0 attribution in the integrated page and the migration record.

**Rationale**: Issue #4197 names this license as a source requirement.

**Alternatives considered**: Remove or weaken the source notice. This would violate the migration requirement.

## Repository Process

**Decision**: Use the timestamp route under `specs/live/`. Record the existing process-folder debt and do not move unrelated records in this change.

**Rationale**: Repository instructions reserve `specs/live/` for timestamp records. The baseline contains 792 grandfathered direct children and four managed roots.

**Alternatives considered**: Add a direct feature folder under `specs/` or migrate legacy records here. The first bypasses the managed route. The second widens this issue.
