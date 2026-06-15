# Contract: Menu Operations for Org Async Claims

## Scope

Defines behavioral contracts for three new MistHelper menu operations using mistapi 0.63.0 org async-claim APIs.

- **Menu 208**: List Org Async Claims (safe)
- **Menu 209**: Create Org Async Claim (destructive)
- **Menu 210**: Get Org Async Claim Status by Claim ID (safe)

## Shared Preconditions

1. `apisession` initialized.
2. org context resolved via existing `get_cached_or_prompted_org_id()` flow.
3. All prompts use `safe_input()`.
4. All operations log before and after API actions.

## Menu 208 Contract — List Org Async Claims (Safe)

### Intent
Read-only export of org async claim records.

### API mapping
- Preferred: `mistapi.api.v1.orgs.licenses.listOrgAsyncClaims(apisession, org_id, ...)`

### Inputs
| Input | Type | Required | Validation |
| - | - | - | - |
| `org_id` | string | yes | non-empty |

### Outputs
| Output | Behavior |
| - | - |
| terminal | summary count + outcome message (including empty result case) |
| export | call `DataExporter.save_data_to_output(flat_rows, filename, api_function_name="listOrgAsyncClaims")` |

### Error contract
- API exceptions caught and logged; user sees concise failure message.
- Empty list is **success** state, not error.

---

## Menu 209 Contract — Create Org Async Claim (Destructive)

### Intent
Submit org async claim creation request safely with explicit typed confirmation.

### API mapping
- Preferred: `mistapi.api.v1.orgs.licenses.createOrgAsyncClaim(apisession, org_id, body)`

### Inputs
| Input | Type | Required | Validation |
| - | - | - | - |
| `org_id` | string | yes | non-empty |
| payload fields | endpoint-specific | yes | non-empty / parseable |
| confirmation | string | yes | exact `CREATE` |

### Safety gate
- Must call `_confirm_destructive("CREATE", "org_async_claim_create")` before API execution.
- If confirmation fails, operation returns **cancelled** and sends no API request.

### Outputs
| Output | Behavior |
| - | - |
| terminal | submission success/failure + claim ID if available |
| export (optional but recommended) | write response through `DataExporter` with `api_function_name="createOrgAsyncClaim"` |

### Error contract
- Validation failures happen before API call.
- API errors are logged and surfaced without stack dump to user.

---

## Menu 210 Contract — Get Org Async Claim Status by Claim ID (Safe)

### Intent
Retrieve current claim status/details for a known claim ID and export results.

### API mapping
- Preferred: `mistapi.api.v1.orgs.licenses.getOrgAsyncClaimStatus(apisession, org_id, claim_id, detail=...)`
- Backward-compat adapter acceptable for naming differences (`GetOrgLicenseAsyncClaimStatus`) if required.

### Inputs
| Input | Type | Required | Validation |
| - | - | - | - |
| `org_id` | string | yes | non-empty |
| `claim_id` | string | yes | trim + reject empty |
| `detail` | bool | no | default false unless specified |

### Outputs
| Output | Behavior |
| - | - |
| terminal | status summary with processed/succeed/failed fields when present |
| export | call `DataExporter.save_data_to_output(..., api_function_name="getOrgAsyncClaimStatus")` |

### Error contract
- Invalid/empty claim ID rejected before API call.
- 404 and permission failures shown as clear operator feedback.

---

## Persistence Contract (SQLite/CSV)

Add endpoint mappings in `ENDPOINT_PRIMARY_KEY_STRATEGIES`:

| API function name | Strategy type | Key recommendation |
| - | - | - |
| `listOrgAsyncClaims` | `natural_pk` or `composite_pk` | use `claim_id` if present; else (`org_id`,`scheduled_at`,`timestamp`) |
| `createOrgAsyncClaim` | `natural_pk` or `composite_pk` | prefer `claim_id`; else (`org_id`,`submitted_at`,`status`) |
| `getOrgAsyncClaimStatus` | `composite_pk` | (`org_id`,`claim_id`,`timestamp`) |

## Test Contract

### Unit tests (required)
- List: success + empty result + API error.
- Create: success + confirmation mismatch/no-call + API error.
- Status: success + invalid claim id validation + API error/not-found.

### Harness behavior
- Menu 209 (destructive) must be added to destructive skip set for default `--test`.
- Menus 208 and 210 may remain eligible for safe test profiles if non-interactive path is available.
