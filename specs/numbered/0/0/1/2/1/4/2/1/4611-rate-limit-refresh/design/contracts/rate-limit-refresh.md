# Rate Limit Refresh Contract

**Feature**: [spec.md](../../spec.md)

## Mist SDK Call

- Method: `mistapi.api.v1.self.usage.getSelfApiUsage`
- Authentication: Use the existing Mist SDK session.
- Endpoint: Use the SDK's existing self-usage endpoint.
- Transport: Do not add a direct HTTP request.

## Response Handling

- Accept usage data only when `status_code` is from 200 through 299.
- For any other status, preserve the complete existing cache and log a warning.
- On a successful response, retain current usage-field defaults and cache updates.
- On a raised exception, preserve the cache and keep the existing failure warning.

## Offline Test Contract

- Build native `requests.Response` and `mistapi.APIResponse` objects.
- Control the SDK call with a mock session. Do not open a socket.
- Test one 4xx status, one 5xx status, and a successful status.
- Assert full cache equality after failures, successful cache values, and visible failure logs.
- Assert the failed-response payload does not replace valid cached values.
