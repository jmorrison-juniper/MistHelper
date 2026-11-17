# Research: VPN Inventory Failure Handling

## Decision

Use the existing `mistapi` pagination method and validate every VPN page before the builder uses any VPN name.

## Rationale

The builder already uses the SDK and has a page-validation pattern for gateway profiles. Applying that pattern keeps Mist authentication and endpoint behavior unchanged and prevents a partial VPN inventory from reaching the name check.

## Native SDK Evidence

The worktree uses `mistapi` 0.64.1. Its `APIResponse` constructor initializes `next` to `None`. Its `_check_next` reads `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` only when all three values are truthy. A missing value or an integer conversion failure leaves `next` as `None`. Mocked native `requests.Response` tests reproduce this behavior without network access.

The Mist API reference for `listOrgVpns` defines a VPN array response. The installed SDK also logs a truthy `error` field in a 2xx response as an error. A body with both `error` and `results` does not match the endpoint response shape, so the builder rejects it.

The builder accepts a successful single-page response when no pagination headers are present. When any pagination header is present, it requires a nonnegative total, positive limit and page values, a matching SDK next-link decision, and stable totals, limits, and sequential page numbers.

## Alternatives Considered

- **Keep `mistapi.get_all` and return a failure sentinel on exceptions**: Rejected because it does not prove that every page succeeded before returning accumulated data.
- **Add direct HTTP requests**: Rejected because the existing SDK method is available and the repository requires the SDK for Mist REST calls.
- **Treat failed inventory as empty**: Rejected because an existing VPN name could remain hidden and a duplicate could be created.

## Open Questions

None. The issue defines the failure behavior, and the existing profile pagination code provides a compatible local pattern.
