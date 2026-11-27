# Data Model: Lab verification of the stable word and the router channel

The record defines five data entities. Each entity has a natural key. The repository stores no lab data. The lab answers live in issue #3392 comments.

## Entities

### LabCheck

- **Natural key**: `check_id`. The values are L-AP-STABLE, L-SSR-STABLE, L-SSR-BETA, and L-SSR-ALPHA.
- **Attributes**: the route path, the body field names, the job read operation, and the target type. The target type names the lab organization, the lab site, the lab access point, or the lab router.
- **Cardinality**: one lab check has one or more lab answers. A second answer exists only after an unknown verdict (EC-1, EC-2).
- **State transitions**:

| From | Event | To |
| - | - | - |
| absent | The owner sends the call (T006 to T009) | submitted |
| submitted | The job reaches a final state, or the submit call fails | job-final |
| job-final | The owner drafts the answer with the fixed fields | drafted |
| drafted | The owner posts the answer (T010) | answered |
| answered | The verdict is unknown | absent (the owner repeats the check once, EC-1) |

### LabAnswer

- **Natural key**: the pair of `check_id` and `utc_recorded`. The time is ISO 8601 in UTC.
- **Attributes**: the fields of `design/contracts/lab-answer-record.md`. The fields hold no identifier, no token, and no response body.
- **State transitions**:

| From | Event | To |
| - | - | - |
| drafted | The owner posts the answer on issue #3392 | posted |
| posted | The agent reads the answer in the evidence audit (TST-13) | read |
| read | A gated task applies the verdict (T011 to T015) | applied |

### ChannelValue

- **Natural key**: the word, one of `alpha`, `beta`, and `stable`.
- **Attributes**: the label shown on the pages, the warning text, and the verdict of each router lab answer.
- **State transitions**:

| From | Event | To |
| - | - | - |
| offered | Every lab answer for the value has an accepted verdict | kept (no change, EC-3) |
| offered | One lab answer for the value has a refused verdict | removed (T013 to T015) |

A value stays offered until its answer exists. A split result (EC-3) counts as refused.

### AccessPointRule

- **Natural key**: the rule identifier R-AP-STABLE.
- **Attributes**: the two code sites of the refusal. One is the save refusal in `org_advanced_options.py` (RC-41, RC-42) with its call in `org_upgrade.py` (RC-43). The other is the builder guard in `aggregate_upgrade_service.py` (RC-30, RC-31).
- **State transitions**:

| From | Event | To |
| - | - | - |
| refused | An accepted lab answer exists for L-AP-STABLE | lifted (T011) |
| refused | A refused lab answer exists for L-AP-STABLE | refused (T012, no change) |

A lifted rule does not return to refused in this issue.

### ParityRow

- **Natural key**: the row identifier, C17 or C21 in `tests/e2e/upgrade_portal/journeys/parity_matrix.json`.
- **Attributes**: the families, the verdict, the journeys, and the evidence paths.
- **State transitions**:

| Row | From | Event | To |
| - | - | - | - |
| C17 | gap for the access point family | An accepted lab answer exists (T011, T017) | parity for the access point family |
| C17 | parity for the access point family (stale, RC-99) | T017 corrects the row | gap for the access point family |
| C21 | parity with the stale evidence path (RC-102) | T017 corrects the evidence path | parity with the path at line 535 (RC-45) |

### RemoteCheck

- **Natural key**: the pair of path and ref. The ref is `main` for repository rows and `local install` for installed SDK rows.
- **Attributes**: the claim, the blob SHA or the SHA-256 value, the result (present, absent, or stale), and the line.
- **State transitions**:

| From | Event | To |
| - | - | - |
| unchecked | The agent reads the tree or the content of main | checked |
| checked | The audit runs again at a later date (TST-14) | checked again, with the same or a new result |

## Relations

- Each LabCheck produces one or more LabAnswer rows.
- Each router ChannelValue depends on one LabCheck: L-SSR-STABLE, L-SSR-BETA, or L-SSR-ALPHA. A split result (EC-3) adds one LabAnswer for each lab router that the check uses.
- Each AccessPointRule depends on one LabCheck (L-AP-STABLE).
- Each ParityRow C17 depends on the AccessPointRule.
- Each RemoteCheck supports one claim in the spec, the plan, or the tasks.
