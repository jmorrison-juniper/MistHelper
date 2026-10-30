# Research: Required Device Identity for Inventory Failure Records

## Decision

Treat a device ID as required in both inventory failure-record paths.

## Rationale

The issue manifest identifies the ID as the device primary key. A blank ID prevents an operator from matching a failure row to a device.

## Alternatives Considered

- Keep a blank ID and rely on the serial number. Rejected because the row contract names the device ID as its primary key.
- Skip the failure row. Rejected because the comparison would hide an error.
- Write a row with an explicit failure marker and no device ID. Rejected because the row would still lack the identity needed for follow-up.

## Open Questions

None. The selected scope changes no Mist request or production state.
