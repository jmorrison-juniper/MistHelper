# Research: AP warning report

## Trouble evidence

**Decision**: Read `listOrgDevicesStats` with `type="ap"` and `status="all"`.

**Rationale**: The local OpenAPI schema documents `stats_ap.last_trouble.code` and its timestamp.
The inventory schema does not document trouble fields.
Use inventory trouble evidence only when statistics lack the `last_trouble` field.
An explicit empty statistics observation must not resurrect stale inventory evidence.

**Alternatives considered**: Inventory alone can omit documented trouble evidence.
Per-site statistics require more requests without adding required fields.

## Definition dictionary

**Decision**: Read `listApLedDefinition` from `const.ap_led_status`.

**Rationale**: Its records contain `code`, `key`, `name`, and `description`.
The general alarm dictionary describes alarm events instead of AP trouble codes.

**Alternatives considered**: Hardcoded definitions would become stale and would hide unknown codes.

## Pagination

**Decision**: Use SDK `get_next` and validate every returned response.

**Rationale**: SDK `get_all` can stop on an absent next response and return partial rows.
An incomplete report must fail before persistence.

**Alternatives considered**: A first-page-only status check cannot detect a later HTTP error.

## State interpretation

**Decision**: Report the latest nonzero code and its observation time, not an asserted current LED color.

**Rationale**: `last_trouble` is historical evidence.
Connection state is independent of the trouble code.

**Alternatives considered**: Treating every disconnected AP as faulty contradicts the confirmed user filter.

## Environment

The standard bootstrap rejected the current lock metadata.
`uv sync --frozen --extra dev` installed the existing lock without editing dependency files.
The separate bootstrap defect is tracked independently.
