# Research: WebSocket Audit Compatibility

## Decision: Keep the repair inside the isolated audit

**Decision**: Change the existing audit policy and dialog inspector. Keep the portal and its production request handlers unchanged.

**Rationale**: The permitted operation is an audit decision. Existing Playwright fixtures render tracked portal assets and fulfill approved requests from local synthetic data.

**Alternatives considered**: Change the portal request flow or add a live integration. Both exceed the requested audit scope and add production risk.

## Decision: Bind device scope to its approved site response

**Decision**: Store approved device IDs under the site ID that supplied the device response. Permit the client path only when both IDs exist in that association.

**Rationale**: `ReadScope.allowed` currently approves site children and map client reads. It does not model a device-to-site association or the client path. `ReadScope.register` already validates response envelopes and UUID identifiers.

**Alternatives considered**: Permit any syntactically valid device ID or add it to a global device set. Neither proves that the requested device belongs to the requested site.

## Decision: Verify SDK source without calling methods

**Decision**: Extend `ReadScope.verify_sdk` for `sites.wired_clients.searchSiteWiredClients`. Retain source inspection and the existing GET-only check.

**Rationale**: The existing test verifies installed method source with `inspect.getsource`. It does not invoke the SDK methods. `sites.devices.listSiteDevices` and `sites.stats.getSiteSdkStatsByMap` are already in the verification list.

**Alternatives considered**: Probe the SDK against a live account or infer the method from its name. A live call is outside scope. A name does not prove the HTTP method.

## Decision: Count Cancel controls in the rendered operation form

**Decision**: Report the count of visible controls with the exact accessible name `Cancel` and test ID `ws-cancel-selection-button`. Use that evidence for the existing `operation-cancel` finding.

**Rationale**: `DialogInspector.inspect` currently writes a fixed unsupported value. The rendered form contains a testable Cancel control. Counting all matching nodes would include hidden controls.

**Alternatives considered**: Keep a constant audit result or count all DOM matches. The constant contradicts rendered evidence. The DOM count does not establish visibility.

## Decision: Keep tests offline and local

**Decision**: Add regressions to `test_inventory.py` and `test_dialogs.py`. Use the existing `audit_page` and `audit_inventory` fixtures.

**Rationale**: `audit_page` installs a browser request guard before navigation and serves local tracked assets. `audit_inventory` denies Python socket access during SDK discovery. The selected test files do not require live mode.

**Alternatives considered**: Add tests to `test_live.py` or start a portal service. Both are prohibited by the user request and are unnecessary for this audit repair.

## Research Results

No unresolved technical choice remains. No new package, external service, persistent store, or API contract is needed.
