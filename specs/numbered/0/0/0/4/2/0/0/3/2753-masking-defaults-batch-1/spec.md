# Feature Specification: Reject Missing Created Identifiers

## Problem

The organization configuration import accepts a create response with no object identifier.

The import then reports the object as imported. It also omits the reference remap.

Later objects can keep stale references to the source organization.

## Scope

This batch changes one response boundary in `OrgConfigMigrationManager`.

The batch does not change credential defaults or organization and site identifier defaults.

The batch does not change the `RRM_DRY_RUN` policy.

## Requirements

### FR-001

The response reader MUST require a nonempty string in `response.data["id"]`.

### FR-002

The response reader MUST reject a missing identifier.

The refusal MUST name the required object identifier and the create-response boundary.

### FR-003

The response reader MUST reject a response whose `data` value is not a dictionary.

### FR-004

The create loop MUST record a rejected response as `failed`.

The create loop MUST NOT record the object as `imported`.

### FR-005

The operator MUST see the refusal in the immediate failure row.

The final import report MUST show the object in the `FAILED` section.

### FR-006

If no object imports and at least one object fails, the final completion message MUST report failure.

The final completion message MUST NOT report successful completion.

### FR-007

The failure log MUST NOT include an identifier value.

The broad batch handler MUST reference its bound exception.

## Acceptance scenarios

1. A response with `data={"id": "dest-1"}` returns `dest-1`.
2. A response with `data={"name": "Corp-LAN"}` raises a visible refusal.
3. A response with list data raises the same visible refusal.
4. The create loop records either refused response as failed.
5. A run with only failed rows reports that no object imported.
6. A valid create response still records the reference remap and imported status.

## Exclusions

- Issue #2861 owns credential defaults.
- Issue #2863 owns organization and site identifier defaults.
- The RRM dry-run default needs a separate safety policy decision.
- This batch adds no ratchet or baseline.
