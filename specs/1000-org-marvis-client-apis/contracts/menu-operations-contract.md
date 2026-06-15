# Contract: Org Marvis Client Menu Operations

## Scope

Defines behavioral contracts for five new org-level Marvis Client operations using mistapi 0.63.0 endpoints.

## Shared Preconditions

1. `apisession` initialized.
2. org context resolved before endpoint call.
3. prompts handled via `safe_input()`.
4. logging before and after each meaningful action.
5. all outputs routed through existing exporter path.

## Operation A: Marvis Client Insights Export (Safe)

### Intent
Export org-level insight records for operator review.

### Input contract
| Input | Required | Validation |
| - | - | - |
| org_id | yes | non-empty |
| optional filters | no | endpoint-compatible values |
| duration/window | optional per endpoint | validated format |

### Output contract
| Output | Required behavior |
| - | - |
| terminal summary | show filters, effective window, row count |
| CSV/SQLite export | exporter call with explicit `api_function_name` |

### Error contract
- empty dataset is success with explicit message.
- validation and API errors return actionable guidance.

---

## Operation B: Marvis Client Events Count (Safe)

### Intent
Provide aggregate event counts for triage.

### Input contract
| Input | Required | Validation |
| - | - | - |
| org_id | yes | non-empty |
| optional filters | no | endpoint-compatible values |
| duration/window | no | validated format |

### Output contract
- export aggregate rows for reconciliation.
- deterministic count key behavior across identical scope reruns.

### Error contract
- invalid duration/filter rejected pre-call.
- API/output failures reported clearly.

---

## Operation C: Marvis Client Events Search (Safe, Paginated)

### Intent
Retrieve detailed event records with continuation support.

### Input contract
| Input | Required | Validation |
| - | - | - |
| org_id | yes | non-empty |
| optional filters | no | endpoint-compatible values |
| duration/window | no | validated format |
| search_after token | no | must be syntactically valid when provided |

### Output contract
- multi-page traversal supported until terminal page.
- summary includes page progress and total exported rows.
- persistence strategy prevents duplicates across retries/pages.

### Error contract
- malformed/expired token fails safely with restart guidance.

---

## Operation D: Marvis Client Stats Count (Safe)

### Intent
Provide aggregate stats counts for trend triage.

### Input contract
Same pattern as events count.

### Output contract
- export aggregate rows.
- deterministic update behavior on repeated runs with identical scope.

### Error contract
Same pattern as events count.

---

## Operation E: Marvis Client Stats Search (Safe, Paginated)

### Intent
Retrieve detailed stats records with continuation support.

### Input contract
Same pattern as events search.

### Output contract
- multi-page continuation with no row duplication/loss.
- summary includes pagination and row count metrics.

### Error contract
Same pattern as events search.

## Persistence Contract

`ENDPOINT_PRIMARY_KEY_STRATEGIES` must include explicit entries for all five API function names.

| Dataset class | Key behavior requirement |
| - | - |
| insights | uniqueness-preserving key (natural preferred, composite fallback) |
| events count | deterministic scope-based update key |
| events search | idempotent detail record key across retries/pages |
| stats count | deterministic scope-based update key |
| stats search | idempotent detail record key across retries/pages |

## Test Contract

Required regression tests:
1. happy path for each operation
2. invalid duration/filter input handling
3. search-after continuation no-dup/no-drop invariants
4. malformed/expired token handling
5. CSV and SQLite export compatibility for each operation
6. output failure handling with actionable message
