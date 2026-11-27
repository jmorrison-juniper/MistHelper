# Contract: Audit store

**Record**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

**File**: `data/mist_data.db`. The path comes from the portal data directory. Table: `guest_authorization_audit`. Module: `src/interfaces/portals/guest_authorizations/services/audit_store.py`.

## 1. Table Definition

```sql
CREATE TABLE IF NOT EXISTS guest_authorization_audit (
  operation_id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  wlan_id TEXT NOT NULL,
  masked_target TEXT NOT NULL,
  requested_minutes INTEGER,
  operator_identity TEXT NOT NULL,
  intent_utc TEXT NOT NULL,
  outcome TEXT,
  http_status INTEGER,
  outcome_utc TEXT,
  error_category TEXT
)
```

```sql
CREATE INDEX IF NOT EXISTS guest_auth_open_target
  ON guest_authorization_audit (site_id, wlan_id, masked_target, outcome)
```

## 2. Column Rules

| Column | Value | Rule |
| --- | --- | --- |
| `operation_id` | UUID version 4 | Generated for each intent |
| `action` | `GRANT`, `UPDATE`, `EXTEND`, `REVOKE`, or `IMPORT_ROW` | Matches the typed word or the batch row |
| `masked_target` | `xx:xx:xx:xx:AA:BB` | Never the full MAC address |
| `requested_minutes` | Integer or null | Null for revoke and update without minutes |
| `operator_identity` | Trusted header value | Stored for attribution under D-4 |
| `intent_utc` | UTC ISO 8601 | Written before dispatch |
| `outcome` | One value from `design/contracts/portal.md` Section 4, or null | Null means the outcome is open |
| `http_status` | Integer or null | The final response status when Mist answered |
| `outcome_utc` | UTC ISO 8601 or null | Written after the response |
| `error_category` | Short text or null | Never a message from Mist and never a private value |

## 3. Write Sequence

1. Start a transaction with `BEGIN IMMEDIATE`.
2. Check the in-flight rule. A row with the same `site_id`, `wlan_id`, and `masked_target` and a null `outcome` blocks the write.
3. Insert the intent row.
4. Commit.
5. Read the intent row back by `operation_id`. A missing row returns `unavailable` before dispatch (FR-018).
6. Make one Mist call (`design/contracts/mist-api.md`).
7. Update the outcome columns by `operation_id` in one statement.
8. Read the row back. A failed update returns `audit_failed` to the caller and stops later writes (FR-019).

## 4. Failure Rules

| Failure | Result | Effect |
| --- | --- | --- |
| Intent insert fails | `unavailable` with category `audit_unavailable` | No Mist call |
| Intent read-back fails | `unavailable` with category `audit_unavailable` | No Mist call |
| Outcome update fails | `audit_failed` with the Mist outcome in the response | Stops later writes. The operator reviews the intent |
| Process restarts with an open intent | Intent shows as open | The in-flight rule blocks a new write to the same target until review |

Caution: an open intent does not prove that Mist applied the change. Read the record before any new write to the same target.

## 5. Retention and Recovery

- The feature never deletes a row. The module holds no `DELETE` statement (TEST-017).
- The operator copies `data/mist_data.db` while the portal is stopped. The copy keeps the audit rows.
- A restored copy must pass the read-back test in TEST-017 before the portal starts.
- Rollback keeps the audit rows (`plan.md` Rollback Steps).

## 6. Locking

- The portal runs one Gunicorn worker with four threads (`wsgi.py` line 4). A process lock guards the store.
- Each write uses `BEGIN IMMEDIATE`. A second writer waits for the lock.
- TEST-018 runs two threads against one target. One write proceeds and one blocks.

## 7. Masking

- The store holds no full MAC address, no name, no email address, and no field value.
- The store holds no token and no request body.
- Logs repeat the masked target only.
