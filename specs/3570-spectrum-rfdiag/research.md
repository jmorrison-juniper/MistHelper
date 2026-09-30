# Phase 0 Research: Spectrum RF Diagnostics

This document records each design decision. Each entry states the decision, the reason, and the alternatives. No open clarification remains.

## 1. Mist spectrum analysis start request

**Decision**: Use `POST /api/v1/sites/{site_id}/analyze_spectrum` to start spectrum analysis. The path parameter is `site_id`. The request body follows the `spectrum_analysis` schema. It must include `band`. It may include `device_id`, `duration`, and `format`. The 200 response follows the `websocket_session` schema and includes `session`.

**Rationale**: The OpenAPI shape gives the smallest valid request. `band` is the only required field. `device_id` ties the scan to the selected AP. The returned `session` gives the operator a clear start result.

**Alternatives considered**:

- Send a free-form body. Rejected. Tests must prove the OpenAPI request shape.
- Start analysis without AP selection. Rejected. The spec requires a site and AP before start.

## 2. Mist spectrum running-state request

**Decision**: Use `GET /api/v1/sites/{site_id}/analyze_spectrum` to read the running spectrum analysis state. The path parameter is `site_id`. There is no request body. The 200 response follows `response_running_spectrum_analysis` and can include `band`, `device_id`, `duration`, `format`, and `started_time`. The SDK lacks this function, so the client must call `apisession.mist_get('/api/v1/sites/{site_id}/analyze_spectrum')` or an equivalent API-session method.

**Rationale**: The constitution says to use the SDK when it exists. Here the SDK method is missing, so the API-session fallback is needed and limited to this endpoint. The fallback stays inside the RF diagnostics client class so it does not spread through the operation.

**Alternatives considered**:

- Wait without polling. Rejected. The operator needs a clear final result or a failure.
- Add a fake SDK wrapper. Rejected. It would hide that the SDK does not expose the method.

## 3. RF diagnostic recording API methods

**Decision**: Use the SDK for RF diagnostic recording methods that exist:

- `mistapi.api.v1.sites.rfdiags.startSiteRecording` for `POST /api/v1/sites/{site_id}/rfdiags`. The request body requires `name` and `type`. It may include `duration`, `mac`, and `sdkclient_id`.
- `mistapi.api.v1.sites.rfdiags.getSiteRfdiagRecording` for `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}`.
- `mistapi.api.v1.sites.rfdiags.stopSiteRfdiagRecording` for `POST /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/stop`.
- `mistapi.api.v1.sites.rfdiags.downloadSiteRfdiagRecording` for `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download`. The call returns download bytes.

**Rationale**: These SDK methods exist, so direct HTTP is not needed. Unit tests can inject callables and assert request bodies without network access. Stop must run after a started recording even when the wait is interrupted.

**Alternatives considered**:

- Use direct HTTP for all RF diagnostic endpoints. Rejected. The SDK exists for recording endpoints.
- Download before stop. Rejected. The recording must be stopped before the file is complete.

## 4. RF diagnostic recording list-name discrepancy

**Decision**: Record the assignment discrepancy and use the actual OpenAPI and SDK name. The assignment names `listSiteRfdiagRecording`, but OpenAPI and the SDK expose `getSiteSiteRfdiagRecording` at `GET /api/v1/sites/{site_id}/rfdiags`. Query parameters are `start`, `end`, `duration`, `limit`, and `page`.

**Rationale**: The client must call names that exist. The note helps maintainers understand why the apparent list name is not used.

**Alternatives considered**:

- Use the assignment name. Rejected. The method does not match OpenAPI or the SDK.
- Skip the list endpoint note. Rejected. The issue asked to record the discrepancy.

## 5. Guided operator flow and safe cancellation

**Decision**: Use a class-based operation that asks for mode, site, target, duration or operator stop, and explicit confirmation. Enter or any answer other than `y` means no. A cancelled confirmation still writes one audit row. A Ctrl+C during the recording wait triggers stop before return.

**Rationale**: The spec requires safe prompts and a durable audit trail. This behavior prevents accidental remote actions and keeps a record of declined runs.

**Alternatives considered**:

- Start immediately after target selection. Rejected. The spec requires confirmation.
- Treat Enter as yes. Rejected. The default must be no.

## 6. Audit file and recording download storage

**Decision**: Append one row per run to `data/RfDiagnostics.csv`. Save recording bytes under `data/rfdiags/`. Use `pathlib.Path` for paths. Create `data/rfdiags/` when it is missing. Use a file-system safe name that includes site, client MAC, and run time.

**Rationale**: The paths are fixed by the spec. The audit is not an API export. It is a local operator log, so a focused CSV writer is simpler than multi-backend export. The write must fail closed: if the audit row cannot be written, the operation reports failure instead of saying the run is fully recorded.

**Alternatives considered**:

- Use a database. Rejected. The spec requires `data/RfDiagnostics.csv` and only one small row per run.
- Store downloads outside `data/`. Rejected. The constitution requires application outputs under `data/`.

## 7. RF evidence context from Juniper skill pages

**Decision**: Describe spectrum and RF recording as evidence helpers, not as replacements for Marvis, SLE, Insights, or packet captures. Research cites these local skill pages:

- `C:\Users\jmorrison\.copilot\skills\juniper-mist-wireless\09-roaming-reason-codes-and-troubleshooting\04-ap-power-reboot-replace-reset-and-packet-capture.md`
- `C:\Users\jmorrison\.copilot\skills\juniper-mist-aiops\01-aiops-model-and-subscriptions\01-aiops-features-and-explainable-ai.md`

The wireless page states that AP insights show channel utilization and that it should stay below `50%`. It also says dynamic packet captures and manual packet captures help when client events do not explain the failure. The AIOps page states that Insights can include a dynamic packet capture for a qualifying incident. It also states that Juniper APs keep a packet buffer, and Mist can save that buffer for an event and expose a `Download Packet Capture` action.

**Rationale**: Operators need the RF diagnostics flow as one more evidence path. The skill pages explain when packet capture evidence is useful and why AP packet buffer behavior matters.

**Alternatives considered**:

- Present RF diagnostics as the only troubleshooting path. Rejected. Marvis, SLE, Insights, and packet capture remain valid paths.
- Omit channel utilization guidance. Rejected. Channel utilization is a key RF symptom for spectrum analysis.

## 8. Unit test strategy

**Decision**: Use unit tests with injected dependencies. Tests assert request bodies, call order, confirmation behavior, bounded polling, Ctrl+C stop behavior, file naming, download writes, and audit row output.

**Rationale**: The feature can be proven without a live Mist tenant. Injection keeps tests deterministic and avoids real waits or network calls.

**Alternatives considered**:

- Use live Mist API tests. Rejected. They need credentials and can start real diagnostics.
- Test only the happy path. Rejected. The spec requires decline, interrupt, failure, and request-shape coverage.
