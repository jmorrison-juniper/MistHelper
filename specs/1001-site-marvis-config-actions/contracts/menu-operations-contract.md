# Contract: Site Marvis Config Actions Menu Operations

## Scope

Defines behavioral contracts for four new site-level Marvis config action operations using mistapi 0.63.0 APIs.

## Shared Preconditions

1. `apisession` initialized and valid.
2. org/site context resolved before endpoint call.
3. prompts handled via `safe_input()`.
4. logging before and after each meaningful action.
5. all outputs routed through existing exporter path.

## Operation A: Site Config Action Count (Safe)

### Intent
Return aggregate count of site Marvis config actions for triage and reporting.

### Input contract
| Input | Required | Validation |
| - | - | - |
| org_id | yes | non-empty |
| site_id | yes | non-empty |
| optional filters | no | endpoint-compatible values |
| duration/window | no | validated format and valid range |

### Output contract
| Output | Required behavior |
| - | - |
| terminal summary | show site scope, filters/window, count total |
| CSV/SQLite/polyglot export | exporter call with explicit `api_function_name` |

### Error contract
- invalid scope/filters rejected pre-call.
- empty result treated as success with explicit message.
- API/output errors provide actionable guidance.

---

## Operation B: Site Config Action Search (Safe, Paginated)

### Intent
Retrieve detailed config action records for the selected site.

### Input contract
| Input | Required | Validation |
| - | - | - |
| org_id | yes | non-empty |
| site_id | yes | non-empty |
| optional filters | no | endpoint-compatible values |
| duration/window | no | validated format |
| pagination continuation | no | validated when provided |

### Output contract
- multi-page traversal supported until terminal page.
- summary includes page count and total exported rows.
- persistence strategy prevents duplicates across retries/pages.

### Error contract
- malformed continuation data fails safely with restart guidance.
- partial failure reports completed page/row progress for operator recovery.

---

## Operation C: Submit Config Action Feedback (Mutating)

### Intent
Submit operator feedback for a specific site config action.

### Input contract
| Input | Required | Validation |
| - | - | - |
| org_id | yes | non-empty |
| site_id | yes | non-empty |
| action_id | yes | non-empty, format-valid |
| feedback_type | yes | allowlisted enum |
| feedback_value | yes | type/range-valid for selected feedback_type |
| comment | no | bounded length + safe text constraints |

### Output contract
- successful submissions return explicit status and operation summary.
- rejected payloads return field-level corrective guidance.
- result dataset exported for audit trace.

### Error contract
- any validation failure blocks mutating endpoint call.
- API failures include actionable retry/remediation context.

---

## Operation D: Delete Config Action by ID (Destructive)

### Intent
Delete a specific site config action only after explicit operator confirmation.

### Input contract
| Input | Required | Validation |
| - | - | - |
| org_id | yes | non-empty |
| site_id | yes | non-empty |
| action_id | yes | non-empty, format-valid |
| typed confirmation | yes | exact, case-sensitive expected phrase |

### Guard contract
1. Warning banner must be shown before confirmation prompt.
2. Delete endpoint must not be called unless confirmation is exact match.
3. Cancellation path must report non-execution clearly.

### Output contract
- status message must indicate cancelled/rejected/success/failed.
- destructive execution result exported/logged for audit trace.

### Error contract
- confirmation mismatch triggers safe cancel path.
- API failures return actionable operator guidance.

## Persistence Contract

`ENDPOINT_PRIMARY_KEY_STRATEGIES` must include explicit entries for all new datasets.

| Dataset class | Key behavior requirement |
| - | - |
| count results | deterministic scope-based update key |
| search results | idempotent per-record key across pages/retries |
| feedback results | operation-audit key with action context |
| delete results | operation-audit key with destructive execution context |

## Test Contract

Required automated coverage:
1. safe count/search happy paths
2. search pagination traversal correctness
3. feedback validation rejects invalid payloads pre-call
4. feedback valid payload submits successfully
5. delete confirmation mismatch prevents destructive call
6. exact delete confirmation allows destructive call path
7. unattended test mode skips/guards destructive execution with explicit reporting
8. CSV and SQLite compatibility for all operation outputs
