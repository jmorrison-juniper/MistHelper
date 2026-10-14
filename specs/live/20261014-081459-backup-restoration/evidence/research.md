# Research: Backup restoration

## Complete writable settings

**Decision**: Validate against `org_setting` and `site_setting` in the checked-in OpenAPI 3.1 document.

**Rationale**: The update endpoints use these schemas. Replaying complete response objects would include server-managed fields.

**Alternatives considered**: Firmware-only restoration silently narrows issue #4218. Blind complete replay can overwrite server-managed fields.

Schema references mark `id`, `org_id`, `site_id`, `created_time`, and `modified_time` as read-only.
The schemas also define other read-only fields.
Exclude known top-level read-only fields. Reject unsupported nested read-only content rather than silently losing sibling values.
Reject unknown structured fields and invalid values. Permit schema-defined dynamic maps only under their declared schema.

## Absent fields

**Decision**: Preserve absence through explicit supported deletion only. Otherwise fail before writes.

**Rationale**: A PUT body that omits a current field does not prove its deletion.
The predecessor proves site `-auto_upgrade` deletion and complete replacement of named parent objects.
No generic deletion claim is available for every organization and site field.

**Alternatives considered**: Sending null or a hyphen for every missing key invents unsupported semantics.
Retaining every later field misrepresents complete restoration.

## Legacy trust and ownership

**Decision**: Require explicit active-cloud binding and current site membership.

**Rationale**: The v1 bundle contains no authenticated cloud provenance.
A checksum detects accidental corruption but does not prove the source.
A site with no saved `org_id` can bind only when the bundle has one organization.
Multiple organization records with missing site ownership are ambiguous and must fail.

## Package structure

**Decision**: Move the backup module into a nested recovery package and update every caller.

**Rationale**: A sixth direct module would violate the structural gate.
The move retains behavior and provides one compliant location for restore logic.

## Validation dependency

**Decision**: Use jsonschema with local references only.

**Rationale**: OpenAPI 3.1 schemas contain unions, references, and constraints.
A small handwritten validator would miss required cases.
No remote schema fetch is permitted.
