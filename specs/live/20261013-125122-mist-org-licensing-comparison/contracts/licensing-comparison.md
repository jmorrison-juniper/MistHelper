# Licensing Comparison Interface Contract

**Date**: 2026-10-13
**Feature**: [../spec.md](../spec.md)

This contract describes proposed routes in the existing MistHelper Flask application. It adds no server or public port.

## Page

### `GET /license-comparison`

Return the comparison page inside the existing portal frame.

- Use the authenticated portal session and existing access controls.
- Show the current page title, organization selector, comparison table, manual row controls, purchase fields, balance totals, export action, and source attribution.
- Include stable `data-testid` attributes for each interactive control.
- Return an explicit authentication error when the Mist session is unavailable.

## Organization Choices

### `GET /api/license-comparison/organizations`

Return only organizations that the shared Mist session can access.

Successful response:

```json
{
  "organizations": [
    {"org_id": "authorized-org-id", "name": "Organization"}
  ]
}
```

- Derive MSP choices from the shared `getSelf` response and `listMspOrgs`.
- Include the configured direct organization when its session scope is present.
- Do not accept an organization list from the browser as proof of access.
- Keep 4xx and 5xx Mist responses distinct from an empty organization list.

## Comparison

### `POST /api/license-comparison`

Accept selected organization IDs and the current browser-session comparison inputs. Recheck organization access before every Mist request.

The response contains one result per requested row. Each result includes license summary, license use by site, inventory, and a request status. A failed request has an error status and no fabricated numeric values.

- Use `getOrgLicensesSummary`, `getOrgLicensesBySite`, and `getOrgInventory` through `mistapi`.
- Reject unauthorized IDs, duplicate rows, invalid numeric inputs, and unsupported license types.
- Send one Mist request at a time through the shared `RateLimitingUtils` pacing policy.
- After HTTP 429, wait 60 seconds for that token and retry once.
- Do not retry other HTTP responses.
- Return a visible error for each failed organization while retaining successful results.
- Do not persist manual rows or purchased amounts.

## CSV Export

### `POST /api/license-comparison/export`

Accept the current comparison rows after the portal validates their shape.

- Write only after an operator requests export.
- Use `DataExporter.write_with_format_selection` and the existing data directory.
- Use the portal's safe download path for the generated file.
- Preserve the current displayed values and the source attribution.
- Neutralize spreadsheet formula prefixes in every text cell.
- Do not log Mist tokens, secrets, raw request headers, or unredacted exception text.

## Error Behavior

| Condition | Required result |
| - | - |
| No Mist session | Return a clear authentication error |
| Organization not accessible | Reject the request before a Mist call |
| Invalid manual value | Identify the invalid field and retain no invalid value |
| Mist 4xx or 5xx response | Show the failed operation and status without a success-shaped zero |
| Mist rate limit | Wait 60 seconds for the token, then retry once |
| CSV write or download failure | Show an export error and do not report success |
