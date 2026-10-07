# Data Model: Phase-Watch Wording

This feature changes no runtime data model. It defines a documentation and test
contract only.

## Boundary Statement

**Purpose**: Describe the current phase-watch submission boundary.

**Fields**:

| Field | Value |
| - | - |
| start_boundary | `The phase watch starts after the portal sends the upgrade requests.` |
| action_boundary | `It observes the submitted work and sends no firmware request.` |
| proof_boundary | `It does not prove that the cloud accepted each request or that the portal sent device types in this order.` |

**Validation rules**:

- Each value is exact and case-sensitive.
- The values define no runtime transition.
- The values define no cloud acceptance result.
- The values define no submission order.

## Operator Warning

**Purpose**: Prevent a second upgrade during an uncertain submission result.

**Value**:

`Warning: If a submission result is uncertain, do not start another upgrade. A second upgrade can target the same devices.`

**Validation rules**:

- The warning starts with `Warning:`.
- The warning contains one direct instruction.
- The warning defines no recovery action.
- The warning defines no retry or resume rule.

## Approved File Manifest

**Purpose**: Limit implementation changes.

**Members**:

1. `src/interfaces/portals/upgrade_portal/upgrade/driver.py`
2. `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`
3. `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html`
4. `tests/contract/upgrade_portal/test_org_phase_watch_contract.py`
5. `tests/unit/upgrade_portal/test_org_phase_list_parity.py`
6. `changelog.d/issue-3332-phase-watch-wording.md`

**Validation rules**:

- The implementation diff contains no other product or test file.
- The changelog fragment uses the issue-named path.
- The implementation changes no executable control flow.

## Relationships

The driver statement and the organization watch statement share the same three
boundary values.

The organization phase card shows the three boundary values and the operator
warning.

The contract test reads the rendered phase card and directly asserts all four
values.

## State Transitions

None. This feature adds no state and changes no transition.
