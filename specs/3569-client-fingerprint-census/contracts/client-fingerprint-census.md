# Contract: Client Fingerprint Census

## Handler

`ClientFingerprintCensus.run()` takes no positional argument. It reads the API session from `SourceDependencyResolver.apisession`.

## Prompts

1. Resolve one site through `SourceDependencyResolver.SiteDeviceExporter._resolve_site_for_stats("client fingerprint census")`.
2. Ask for one distinct field from the OpenAPI enum.
3. Run with no other prompt.

## API Call

Call `mistapi.api.v1.sites.insights.countSiteClientFingerprints` with `site_id`, `distinct`, and `limit=100`.

Use `mistapi.get_all` on the SDK response so the CSV export receives all pages.

## Export

Write `ClientFingerprintCensus.csv` through `SourceDependencyResolver.DataExporter.write_with_format_selection` with `api_function_name="countOrgClientFingerprints"` and explicit field names.

## Console Output

Print a table header and the top 20 rows by count. If there are no rows, print `The client fingerprint census is empty for this site.`
