# Research: searchSiteDiscoveredSwitches

## Endpoint verification

The installed `mistapi` package exposes this signature:

```text
searchSiteDiscoveredSwitches(
    mist_session,
    site_id,
    adopted=None,
    system_name=None,
    hostname=None,
    vendor=None,
    model=None,
    version=None,
    limit=None,
    start=None,
    end=None,
    duration=None,
    sort=None,
    search_after=None,
)
```

The callable is in `mistapi.api.v1.sites.stats`. The implementation passes the
required session and site values. Mist applies the endpoint defaults.

## Repository findings

The endpoint implementation already exists in the current `main` branch from
the shared site-search delivery:

- Menu 228 calls `SiteSearchExporter.discovered_switches`.
- The exporter calls the SDK once after site resolution.
- `mistapi.get_all` retrieves all pages.
- Nested rows are flattened and escaped before persistence.
- `DataExporter.write_with_format_selection` receives
  `api_function_name="searchSiteDiscoveredSwitches"`.
- The primary-key strategy is composite on
  `system_name`, `mgmt_addr`, and `timestamp`.
- API, menu, and menu-highlight documentation already list the endpoint.

## Test evidence

The shared exporter test table already covers the endpoint binding. This
delivery adds a direct test so the endpoint contract remains visible when the
shared table changes.

## Risks

- A live Mist API call requires credentials and is not suitable for unit tests.
- The endpoint can return no rows. The exporter treats that result as a clean
  informational outcome.
- The primary key depends on fields present in the endpoint response. Missing
  fields must remain an API-data problem, not a new fallback strategy.
