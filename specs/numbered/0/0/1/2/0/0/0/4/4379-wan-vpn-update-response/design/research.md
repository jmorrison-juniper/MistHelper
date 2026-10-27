# Research: WAN VPN Update Response

## SDK response contract

**Decision**: Read `status_code` from the `APIResponse` returned by `updateOrgVpn`. Accept values from 200 through 299. Treat `None` and every other value as failure.

**Rationale**: In `mistapi` 0.64.1, `updateOrgVpn` returns `_APIResponse`, and `APIResponse.status_code` has type `int | None`. The SDK can return an HTTP error response without raising an exception.

**Alternatives considered**:

- Check only for exceptions. Rejected because an HTTP refusal can return normally.
- Check only for status 200. Rejected because other 2xx responses also confirm success.
- Inspect response content. Rejected because the status field provides the needed result and response content can contain sensitive details.

## Source evidence

- [`updateOrgVpn` in mistapi 0.64.1](https://github.com/tmunzer/mistapi_python/blob/v0.64.1/src/mistapi/api/v1/orgs/vpns.py)
- [`APIResponse.status_code` in mistapi 0.64.1](https://github.com/tmunzer/mistapi_python/blob/v0.64.1/src/mistapi/__api_response.py)

Tests must mock both the read and update SDK calls. No Mist credentials or live requests are required.
