# MistAPI SDK Compatibility Research

## Release boundary and target version

**Decision**: Audit MistAPI releases newer than 0.59 and treat `v0.61.4` as the practical target version for compatibility planning.

**Rationale**: The release stream after 0.59 includes `v0.60.0`, `v0.60.1`, `v0.60.4`, `v0.61.0`, `v0.61.1`, `v0.61.2`, `v0.61.3`, and `v0.61.4`. The latest release, `v0.61.4`, includes the cumulative API changes we need to evaluate plus the most recent credential and WebSocket hardening.

**Alternatives considered**:

- Stop at `v0.60.4` to minimize change surface, but that would miss the breaking insight-metric change introduced in `v0.61.0`.
- Stop at `v0.61.0`, but that would miss the latest dependency and reconnect behavior in `v0.61.4`.

## Dependency floor

**Decision**: Update the MistHelper dependency floor to match the audited SDK line, with `mistapi>=0.61.4` and `websocket-client>=1.8.0` as the compatibility floor in project metadata.

**Rationale**: `mistapi` `v0.61.0` introduced a `websocket-client>=1.8.0` dependency requirement, and the current project metadata still advertises `mistapi>=0.59.0` / `websocket-client>=1.4.0`. Even though MistHelper.py does not use MistAPI's new WebSocket/device-utils modules, the dependency floor must remain compatible with the chosen SDK release.

**Alternatives considered**:

- Leave the current dependency floor unchanged and rely on pip to pull older releases; rejected because the audit is explicitly about understanding and planning the move beyond 0.59.
- Pin only `mistapi` and leave `websocket-client` untouched; rejected because the audited release notes add a newer minimum for that dependency.

## MistHelper.py impact surface

**Decision**: Treat `getSiteInsightMetricsForClient()` as the only clearly breaking MistAPI call site in MistHelper.py and schedule it for code update. Keep the rest of the direct call sites in a compatible-or-deferred category unless the implementation pass finds a hidden signature issue.

**Rationale**: `v0.61.0` / `v0.61.2` changed the insight metrics API so the client function uses a `metrics` query parameter instead of the prior positional `metric` path parameter. The existing MistHelper.py call at the client-insights workflow currently passes the metric positionally. The audited release notes do not show a breaking change for `listOrgDevicesStats`, `listSiteDevicesStats`, `listSiteMaps`, `listSiteWlans`, `getOrgSle`, or `getOrgSitesSle`.

**Alternatives considered**:

- Update all stats and SLE calls proactively; rejected because the release notes do not show a signature break for those call sites.
- Leave the insight client call unchanged and rely on backward compatibility; rejected because the release notes explicitly document the parameter change.

## Optional compatibility improvements

**Decision**: Keep `search_after` support for alarm and device-event exports as an intentionally deferred follow-up rather than a required compatibility change.

**Rationale**: `v0.59.1` added `search_after` support to `searchOrgAlarms()` and `searchOrgDeviceEvents()`, but the current MistHelper.py flows already work with the existing paging and checkpoint logic. Adding `search_after` would be an enhancement, not a necessary compatibility fix.

**Alternatives considered**:

- Implement `search_after` immediately in the audit pass; rejected because it changes pagination behavior without addressing a breaking change.

## Clearly unaffected areas

**Decision**: Do not move MistHelper.py onto `mistapi.websockets` or `mistapi.device_utils` during this audit.

**Rationale**: MistHelper.py currently uses its own `WebSocketManager` built on `websocket-client`, not MistAPI's newer WebSocket or device-utils modules. The new modules are useful upstream features but are unrelated to the existing call sites that this audit covers.

**Alternatives considered**:

- Replace the custom WebSocketManager with MistAPI's new WebSocket utilities; rejected because it is an unrelated refactor with no direct compatibility need.

## Release notes worth carrying into implementation

| Release | Key finding | MistHelper.py impact |
|---|---|---|
| `v0.59.1` | `search_after` added to search endpoints; new insight metrics helpers added | Verification only for alarms and device events |
| `v0.59.5` | Exceptions replaced `sys.exit()`, pagination URL handling improved, alarm filters expanded | Existing try/except handling should continue to work |
| `v0.60.0` | New map-stack and JSI-related APIs; MxEdge image upload path changes | Mostly irrelevant to MistHelper.py |
| `v0.60.1` | Self audit logs and SLE classifier updates | Not used by MistHelper.py |
| `v0.60.4` | New Map Stacks API, `searchOrgInventory(model=...)`, pagination and list-response fixes | `listSiteMaps` unaffected; pagination fixes are beneficial |
| `v0.61.0` / `v0.61.2` | Insight metric parameter change, stats parameter removals, WebSocket/device-utils modules, `websocket-client>=1.8.0` | **Breaking update needed for `getSiteInsightMetricsForClient()`** |
| `v0.61.1` / `v0.61.3` / `v0.61.4` | Async helpers, WebSocket tuning, credential hardening, reconnect improvements | No direct MistHelper.py call-site change identified |

## Implementation verification

**Result**: PASS

The completed implementation keeps the audit aligned with the verified code path and the focused regression suite.

| Workflow | Status | Notes |
|---|---|---|
| Alarm export | PASS | `OrgAlarmEventExporter.alarms()` still routes through `APIDataFetcher` with `searchOrgAlarms`. |
| Device-event pagination | PASS | `device_events_52w()` still paginates with `search_after` and writes the expected rows. |
| Site client stats | PASS | `SiteClientExporter.clients()` still uses `listSiteWirelessClientsStats`. |
| Site maps lookup | PASS | `E911BSSIDReportGenerator._fetch_site_maps()` still resolves site maps into `map_lookup`. |
| Site WLAN resolution | PASS | `E911BSSIDReportGenerator._resolve_site_ssids()` still resolves site-level WLANs into the band lookup. |
| Site SLE summary | PASS | `OrgExportUtils.sites_sle_summary()` still uses `getOrgSitesSle` for wifi, wired, and wan. |
| Client insight metrics | UPDATED | `SiteClientExporter.client_insights()` now calls `getSiteInsightMetricsForClient(..., metrics=metric)` and the regression test passed. |
| E911 BSSID report | PASS | `E911BSSIDReportGenerator.execute()` still resolves maps and WLAN bands before writing the BSSID report. |

**Validation**: `python -m py_compile MistHelper.py` and the focused pytest suite passed in this session.
