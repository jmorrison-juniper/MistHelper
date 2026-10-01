# Research: Alert Digest Acknowledge

## Decision: Use the installed `mistapi` SDK methods for all Mist calls

**Rationale**: The installed SDK exposes `searchOrgAlarms`, `listAlarmDefinitions`, `ackOrgMultipleAlarms`, and `unackOrgMultipleAlarms`. This follows the constitution rule that direct path calls are used only when the SDK lacks a method.

**Evidence**: `C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -c "import mistapi; print(mistapi.api.v1.orgs.alarms.searchOrgAlarms); print(mistapi.api.v1.const.alarm_defs.listAlarmDefinitions); print(mistapi.api.v1.orgs.alarms.ackOrgMultipleAlarms); print(mistapi.api.v1.orgs.alarms.unackOrgMultipleAlarms)"` printed four function objects.

**Alternatives considered**: Use `apisession.mist_get` and `apisession.mist_post`. Rejected because the SDK methods exist.

## Decision: Read alarm rows with `searchOrgAlarms`

**Rationale**: The OpenAPI document defines `GET /api/v1/orgs/{org_id}/alarms/search` with operation ID `searchOrgAlarms`. It accepts the path parameter `org_id` and query parameters `site_id`, `type`, `status`, `start`, `end`, `duration`, and `limit`. The response schema is `alarm_search_result` with `results`, `start`, `end`, `limit`, `total`, optional `next`, and alarm rows.

**Response shape**: Each alarm has required fields `count`, `group`, `id`, `last_seen`, `severity`, `timestamp`, and `type`. Optional fields include `acked`, `acked_time`, `site_id`, `status`, `aps`, `bssids`, `gateways`, `hostnames`, `ssids`, `switches`, and `note`.

**Alternatives considered**: Reuse menu 20 as an exporter. Rejected because the digest must group rows and menu 281 must acknowledge unacknowledged alarm IDs.

## Decision: Read category and severity from `listAlarmDefinitions`

**Rationale**: The OpenAPI document defines `GET /api/v1/const/alarm_defs` with operation ID `listAlarmDefinitions`. It takes no parameters. The response is an array of `const_alarm_definition` objects with required fields `display`, `fields`, `group`, `key`, and `severity`.

**Response shape**: Each definition maps `key` to the alarm `type`, and includes `group` and `severity`. The example shows group `infrastructure`, key `device_down`, and severity `warn`.

**Alternatives considered**: Trust the `group` and `severity` fields on each alarm row. Rejected because the acceptance criteria require the category to come from the alarm definitions constant.

## Decision: Send one bulk acknowledgement request

**Rationale**: The OpenAPI document defines `POST /api/v1/orgs/{org_id}/alarms/ack` with operation ID `ackOrgMultipleAlarms`. It accepts the path parameter `org_id` and a JSON body with `alarm_ids` and optional `note`. A successful response has HTTP 200 with no content.

**Safety rule**: The operation sends no request until the operator enters `ACK <count>`, where `<count>` equals the number of displayed unacknowledged alarms. The `--dry-run` mode prints the alarm IDs and sends no request.

**Alternatives considered**: Send one request per alarm. Rejected because the contract requires one bulk request.

## Decision: Record unacknowledge support in the client

**Rationale**: The OpenAPI document defines `POST /api/v1/orgs/{org_id}/alarms/unack` with operation ID `unackOrgMultipleAlarms`. It accepts the same body as the acknowledgement request. This feature does not call it from a menu, but the client records it because the contract lists it as a required operation to verify.

**Alternatives considered**: Omit the method. Rejected because the assignment requires verification.

## Decision: Use Mist alert categories and dashboard labels from the AIOps skill pages

**Rationale**: The AIOps alert dashboard page states that Mist sorts alerts into four categories: Infrastructure, Marvis, Security, and Certificate. It also names the dashboard columns `Recurrence`, `First Seen`, `Last Seen`, and `Details`. It defines the severity labels `Critical`, `Warning`, and `Informational`.

**Citations**:
- `juniper-mist-aiops/04-alerts/01-alerts-dashboard-categories-and-severity.md`
- `juniper-mist-aiops/04-alerts/02-certificate-and-infrastructure-alert-types.md`
- `juniper-mist-aiops/04-alerts/03-marvis-and-security-alert-types.md`
- `juniper-mist-aiops/04-alerts/04-alert-configuration-templates-and-pause-rules.md`

**Alternatives considered**: Use raw API severity values only. Rejected because the handover summary must use the operator terms from the Mist portal.

## Decision: Cite page tiles and related evidence from domain skill pages

**Rationale**: The feature reports alert context that an operator can correlate with Mist pages. The wired skill names `Switch-AP Affinity`, `PoE Compliance`, `VLANs`, `Version Compliance`, `Switch Uptime`, `Config Success`, `Switchport Usage`, and `Potential Anomalies` as `Switches` page tiles. The wireless skill names `Access Points` page fields and bulk operations that help validate AP-related alert context. The WAN skill names `Config Success`, `Version Compliance`, `WAN Edge Uptime`, and `Potential Anomalies` as WAN Edge tiles.

**Citations**:
- `juniper-mist-wired/09-wired-visibility-and-switch-management/01-switches-page-metrics-and-front-panel.md`
- `juniper-mist-wireless/04-device-profiles-and-ap-operations/02-access-points-page-and-bulk-actions.md`
- `juniper-mist-wan/10-monitoring-sles-and-troubleshooting/01-wan-edge-inventory-insights-and-alerts.md`

**Alternatives considered**: Omit domain context. Rejected because the assignment requires these skills to be consulted.
