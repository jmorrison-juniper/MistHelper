# Research: Client Device Fingerprint Census

## Decision: Prefer the live organization fingerprint count path

The live Mist cloud answers `200` for `GET /api/v1/orgs/{org_id}/insights/fingerprints/count`.
The live Mist cloud answered the same seven family rows with and without
`site_id=cf36153a-97bb-4974-8f8f-e9cc25d64d83` on 2026-10-01. The top rows were
`Unknown=7`, `Phone/Tablet/Wearable=6`, `Access Point=1`,
`Audio/Imaging/Video Equipment=1`, and `Gaming Console=1`. This shows that the
current live endpoint accepts the site filter but does not honor it for that org.

**Rationale**: Menu 289 must stop the live HTTP 404 and must send the selected
site filter when the cloud starts to honor it.

**Alternatives considered**: Use only the documented site path. Rejected because
the live cloud returns HTTP 404 for that path.

## Decision: Use the site-scoped fingerprint count endpoint

The OpenAPI operation `countOrgClientFingerprints` is `GET /api/v1/sites/{site_id}/insights/fingerprints/count`. Its tag is `Orgs NAC Fingerprints`, but its path parameter is `site_id`. Query parameters are `distinct`, `start`, `end`, `duration`, and `limit`. The `distinct` schema is `fingerprints_count_distinct`.

The response `200` schema extends `response_count`. It includes `distinct`, `start`, `end`, `limit`, `total`, and `results`. Each result uses the count shape, with `count` and a grouped `property` value.

**Rationale**: The site-scoped path matches the menu requirement to ask for one site.

**Alternatives considered**: Use an organization prompt. Rejected because the OpenAPI path has no `org_id` parameter.

## Decision: Use the OpenAPI distinct enum

The OpenAPI enum for `fingerprints_count_distinct` is `family`, `model`, `os`, and `os_type`. The issue text also names `mfg`, but the count endpoint enum does not include `mfg`.

**Rationale**: The acceptance criteria require distinct values from the OpenAPI enum and a test that asserts that list.

**Alternatives considered**: Offer `mfg` from the search endpoint. Rejected because the count endpoint would reject an unsupported distinct value.

## Decision: Use the installed SDK site aliases

The installed `mistapi` package does not define `mistapi.api.v1.orgs.nac_fingerprints.countOrgClientFingerprints`. It defines `mistapi.api.v1.sites.insights.countSiteClientFingerprints` with this signature:

```text
(mist_session, site_id, distinct=None, start=None, end=None, duration=None, limit=None)
```

It also defines `searchSiteClientFingerprints` with filters `family`, `client_type`, `model`, `mfg`, `os`, `os_type`, `mac`, `sort`, `limit`, `start`, `end`, `duration`, and `interval`.

**Rationale**: The SDK alias matches the site-scoped OpenAPI path and keeps request construction inside `mistapi`.

**Alternatives considered**: Call `apisession.mist_get` directly. Rejected because the SDK provides the site-scoped count function.

## Decision: Paginate the count response before export

The SDK call sends `limit=100` to the count endpoint. The client then calls `mistapi.get_all(response=response, mist_session=mist_session)` so the CSV receives all result pages.

**Rationale**: The report is a census. The console table is capped at 20 rows, but the export must contain all groups returned by pagination.

**Alternatives considered**: Treat the first page as the complete result. Rejected because a large site can have more than 100 fingerprint groups.

## Decision: Use a composite business key in the wiring manifest

The count endpoint returns grouped rows with no stable Mist identifier. The wiring manifest uses `site_id`, `distinct`, and `value` as the composite primary key.

**Rationale**: The key identifies one grouped count for one site and one fingerprint field without an artificial identifier.

**Alternatives considered**: Use `misthelper_internal_id`. Rejected because the project constitution prefers natural business keys when the row has enough stable fields.

## Decision: Reuse the count exporter prompt pattern

`src/operations/exporting/export/count_exporter.py` menus `235`, `236`, and `237` list count operations, ask the operator to select one, resolve the identifier, call the SDK, flatten rows, and pass rows to `DataExporter.write_with_format_selection`.

**Rationale**: Menu `289` needs a narrower version of that pattern: prompt for the site, prompt for the distinct field, call one count endpoint, then export.

**Alternatives considered**: Add the endpoint to menu `236` only. Rejected because issue `#3569` asks for a dedicated operator report.

## Decision: Cite NAC and Insights context

Access Assurance policy design uses device capability and proof strength before it assigns a VLAN, role, or filter. The skill page `juniper-access-assurance-nac/06-validation-results/02-authorization-results-filters-and-caveats.md` states that MAB is for clients that cannot run an EAP supplicant and that specific policies must sit above generic policies.

NAC Client Insights exposes NAC client events and Current Values. The skill page `juniper-mist-aiops/02-insights/06-nac-client-application-and-meeting-insights.md` names `NAC Client Events`, event classes, `Properties`, and `Connection Status`.

**Rationale**: The fingerprint census supports NAC policy discovery before enforcement changes.

**Alternatives considered**: Treat the report as a capacity-only report. Rejected because the issue names NAC design as a primary use case.
