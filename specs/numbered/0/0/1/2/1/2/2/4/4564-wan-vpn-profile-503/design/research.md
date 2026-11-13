# Research: Reject Profiles from Failed Responses

## Decision

Read the HTTP status from the existing Mist SDK response before using its body.

## Evidence

The installed `mistapi` 0.64.1 `APIResponse` stores the HTTP status in `status_code` and parses the response body into `data`. The current builder passes the response to `mistapi.get_all` without checking the status. A failed response can therefore supply a plausible `results` array.

## Rationale

The status is available at the existing API boundary. A status check prevents failed response data from reaching the VPN workflow without changing SDK authentication or the endpoint.

## Alternatives Considered

- Trust the body shape: rejected because an HTTP 503 body can contain a valid-looking profile array.
- Add a direct HTTP request: rejected because the existing SDK method owns the request and authentication.
- Change all profile consumers: rejected because this issue concerns the WAN VPN builder only.
