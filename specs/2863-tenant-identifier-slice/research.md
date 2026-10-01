# Research: Tenant identifier validation

## Proven Failure

At starting revision `a5d465a461d2512b717e943278fdff2b1897df84`,
`organization_tenants()` passes an empty resolver result to `listOrgNetworks`.
An empty response then returns `[]`.
The missing input looks like an organization with no networks.

The parent checked one case and observed one SDK call with `org_argument=''`.
This repair must repeat the public-boundary proof locally.

## Current Slice Classifications

| Surface | Classification | Decision |
| --- | --- | --- |
| Organization network identifier | Proven missing-input failure | Refuse before the SDK call. |
| Organization policy and template identifiers | Same required scope contract | Use the same validator. |
| Required site network identifier | Required scope contract | Refuse before the SDK call. |
| Private site policy and template identifiers | Required scope contract | Use the same validator. |
| Optional policy and template `site_id=None` | Intentional organization-only scope | Preserve it and prove zero site calls. |
| Supplied blank optional site | Invalid supplied scope | Refuse before either SDK call. |
| Missing per-record tenant fields | Optional payload contributions | Preserve the existing collection rules. |
| `tmpl.get("name", "unnamed")` | Diagnostic template label | Preserve it. |
| Audit inventory count of 102 | Historical campaign context | Do not report the audit complete. |

The historical tenant inventory lists eight payload defaults.
Those defaults concern collections and a diagnostic label, not required scope
identifiers. This repair does not replace them with required-input failures.

## Decisions

**Decision**: Raise a field-named `ValueError` and write a counted error log.

**Rationale**: Existing identifier checks use a logged `ValueError`.
The caller does not catch this error around tenant-source storage.
The operator therefore sees a refusal instead of an empty-source message.

**Alternative rejected**: Returning an empty list still hides the missing input.

**Decision**: Accept opaque identifiers without a UUID check.

**Rationale**: Existing contracts use identifiers such as `org-1` and `site-1`.

**Alternative rejected**: A UUID check changes valid existing inputs.

**Decision**: Place the shared validator in the existing tenant module.

**Rationale**: The source directory is already noncompliant.
Two semantic classes replace two helper functions without a new directory
child or more methods on the existing fetch class.
Required request validation stays separate from optional tenant-name collection.
No existing caller or test imports either private name helper.

**Alternative rejected**: The existing `ValidationUtils.validate_site_id`
accepts non-string values and cannot supply a validated string.
Changing that shared utility would expand this reservation and affect unrelated
callers.

**Decision**: Preserve the current exception handlers.

**Rationale**: Their transport, HTTP, and parse-failure behavior is outside the
identifier repair. Unexpected resolver errors already propagate.

**Alternative rejected**: Catching `ValueError` converts the new refusal into a
false empty result.
