# Research: Preserve Rate-Limit State on HTTP Failure

## Decision 1: Check the SDK status before reading quota data

**Decision**: Accept data only when the underlying HTTP status is in the 200 through 299 range.

**Rationale**: The installed SDK keeps parsed JSON in `.data` for failed responses. A usage-shaped error body must not refresh the quota cache.

**Alternatives considered**:

- Trust `.data` without checking status. The offline reproduction showed that this stores values from HTTP 403 and HTTP 503 responses.
- Use a second HTTP request. This violates the existing SDK boundary and adds a live operation.
- Change retry behavior. Retries are outside the issue scope and can increase API load.

## Decision 2: Preserve existing cache state on failure

**Decision**: Validate the response and extract its data before writing any cache field.

**Rationale**: The cache holds the last accepted quota values. A failed refresh must not reset its values, timestamp, request counter, or initialization flag.

**Alternatives considered**:

- Clear the cache after a refusal. This discards valid quota data.
- Write defaults when a field is absent. This can mark invalid data as fresh.

## Decision 3: Test without a live service

**Decision**: Construct native response objects locally and patch only the SDK method boundary.

**Rationale**: This preserves SDK status and payload parsing while avoiding Mist credentials and network activity.

**Alternatives considered**:

- Call the Mist service. This is unnecessary and can affect production access.
- Use a status-shaped mock. It does not verify the installed SDK response shape.
