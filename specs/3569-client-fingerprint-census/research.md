# Research: Client Device Fingerprint Census

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

## Decision: Reuse the count exporter prompt pattern

`src/export/count_exporter.py` menus `235`, `236`, and `237` list count operations, ask the operator to select one, resolve the identifier, call the SDK, flatten rows, and pass rows to `DataExporter.write_with_format_selection`.

**Rationale**: Menu `289` needs a narrower version of that pattern: prompt for the site, prompt for the distinct field, call one count endpoint, then export.

**Alternatives considered**: Add the endpoint to menu `236` only. Rejected because issue `#3569` asks for a dedicated operator report.

## Decision: Cite NAC and Insights context

Access Assurance policy design uses device capability and proof strength before it assigns a VLAN, role, or filter. The skill page `juniper-access-assurance-nac/06-validation-results/02-authorization-results-filters-and-caveats.md` states that MAB is for clients that cannot run an EAP supplicant and that specific policies must sit above generic policies.

NAC Client Insights exposes NAC client events and Current Values. The skill page `juniper-mist-aiops/02-insights/06-nac-client-application-and-meeting-insights.md` names `NAC Client Events`, event classes, `Properties`, and `Connection Status`.

**Rationale**: The fingerprint census supports NAC policy discovery before enforcement changes.

**Alternatives considered**: Treat the report as a capacity-only report. Rejected because the issue names NAC design as a primary use case.
