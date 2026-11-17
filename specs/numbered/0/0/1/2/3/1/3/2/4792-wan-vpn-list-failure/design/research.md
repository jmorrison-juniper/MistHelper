# Research: VPN Inventory Failure Handling

## Decision

Use the existing `mistapi` pagination method and validate every VPN page before the builder uses any VPN name.

## Rationale

The builder already uses the SDK and has a page-validation pattern for gateway profiles. Applying that pattern keeps Mist authentication and endpoint behavior unchanged and prevents a partial VPN inventory from reaching the name check.

## Alternatives Considered

- **Keep `mistapi.get_all` and return a failure sentinel on exceptions**: Rejected because it does not prove that every page succeeded before returning accumulated data.
- **Add direct HTTP requests**: Rejected because the existing SDK method is available and the repository requires the SDK for Mist REST calls.
- **Treat failed inventory as empty**: Rejected because an existing VPN name could remain hidden and a duplicate could be created.

## Open Questions

None. The issue defines the failure behavior, and the existing profile pagination code provides a compatible local pattern.
