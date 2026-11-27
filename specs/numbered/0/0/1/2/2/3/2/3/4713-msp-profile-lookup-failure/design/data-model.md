# Data Model: MSP Profile Lookup Failure

The change adds one in-memory result type and changes no stored data. The data model names each entity, its natural key, and the state transitions that the dispatch uses.

## Entities

### MspPrivilegeLookup (new, in memory)

- **Source**: `src/foundation/support/refactors/msp_privilege_detection.py`, a frozen dataclass.
- **Fields**:
  - `succeeded` (bool). True only for a valid profile. It is False for every failed lookup.
  - `grants` (list of MSP grants). It holds the MSP grants of a valid profile. It is an empty list for a failed lookup, and it may be an empty list for a valid profile.
- **Natural key**: None. The value lives for one call.
- **Persistence**: None. The value is never written to a file or a database.

### MSP grant (existing shape, unchanged)

- **Source**: One entry of the `privileges` list in the `getSelf` response (OpenAPI `admin_privilege`, lines 68139 to 68177 of `documentation/mist-api-openapi31yaml.yaml`).
- **Natural key**: `msp_id`. The OpenAPI schema names it `admin_privilege_msp_id` (RC-48).
- **Attributes used by the detector**:
  - `msp_id` (string, required for an MSP grant).
  - `msp_name` (string or null). The detector falls back to a name lookup when it is absent or `Unknown`.
  - `role` (string). The detector defaults it to `unknown`.
  - `scope` (string). The detector defaults it to `unknown`.
- **Rule**: Only an entry with a string `msp_id` counts as an MSP grant (existing rule in `_msp_parse_one_privilege`).

### Grant list (existing module global, unchanged type)

- **Source**: `msp_privileges` in `src/mist/resources/inventory/org_device_inventory_msp.py` (RC-07).
- **Type**: `list[dict[str, Any]]`. The type does not change (FR-014).
- **Writers**: The startup path, the restore path, the login path, the exporter, and the facade configure call (RC-09, RC-12, RC-14, RC-19, RC-20).
- **Readers**: The dispatch, the resolver, the firmware cache, and the org config exporter (RC-10, RC-24, RC-25).
- **Meaning of an empty list**: The writers cannot tell a failed lookup from confirmed absence. Menu 13 therefore makes a live lookup before it treats an empty list as absence.

## State Transitions

### Profile lookup outcome

| From | Event | To |
| - | - | - |
| Not run | Missing session | Failed lookup, no API call |
| Not run | Call raises an exception | Failed lookup |
| Not run | Response has no status, or a non-2xx status | Failed lookup |
| Not run | 2xx response with a non-object body, or without a `privileges` list | Failed lookup |
| Not run | 2xx response with a `privileges` list of zero MSP grants | Valid profile, confirmed absence |
| Not run | 2xx response with a `privileges` list of one or more MSP grants | Valid profile with grants |

### Menu 13 dispatch

| From | Condition | To |
| - | - | - |
| Entry | Grant list holds one or more MSP grants | Menu shown, no profile lookup |
| Entry | Grant list is empty | Live lookup |
| Live lookup | Failed lookup | Stop with `_LOOKUP_FAILED_MSG`, no callback |
| Live lookup | Valid profile with zero MSP grants | Single-organization callback runs once |
| Live lookup | Valid profile with one or more MSP grants | Stop with `_RESTART_FOR_GRANTS_MSG`, no callback |

## Constraints

- Each state transition runs inside one call. The change keeps no state between calls.
- A failed lookup never changes the grant list. The writers of the grant list stay unchanged (FR-014).
- No field holds a token, a password, a response body, or an exception message (FR-013).
