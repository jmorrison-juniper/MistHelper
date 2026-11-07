# Research: Preserve API Usage After Failed Refresh

**Date**: 2026-11-07
**Feature**: [spec.md](../spec.md)

## Decision

Check the response object's HTTP status before reading its usage data. Accept status codes from 200 through 299. Treat any other status as a failed refresh.

## Rationale

The installed `mistapi` 0.64.1 `APIResponse` exposes both `status_code` and parsed `data`. A controlled native response with status 403 or 503 can therefore carry valid-looking data. The current refresh reads that data without checking the status and changes the cache.

## Alternatives Considered

- **Use the response data alone**: Rejected because a failed HTTP response can contain parsed data.
- **Add a direct HTTP request**: Rejected because the existing Mist SDK method provides the needed status and data.
- **Change SDK or dependency versions**: Rejected because the installed supported version provides the required response status.

## Evidence

- `mistapi.__api_response.APIResponse` assigns the transport status to `status_code` and parsed JSON to `data`.
- The issue reproduction uses native `requests.Response` and `mistapi.APIResponse` objects and performs no network request.
