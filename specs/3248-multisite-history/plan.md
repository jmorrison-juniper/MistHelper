# Implementation Plan: Multi-site upgrades in the history

**Issue**: #3248
**Spec**: [spec.md](./spec.md)

## Technical context

- Python 3.13, Flask 3, and `python-arango` through the capture store.
- The history page is `GET /history` in `src/upgrade_portal/app/routes/review.py`.
- The template is `src/upgrade_portal/app/assets/templates/review/history.html`.
- The aggregate service writes each operation record into `upgrade_runs` through `write_run`.
- The job page `/upgrade/org/jobs/<operation_id>` shows an operation only to the owner session of the selected organization.

No new dependency is necessary. The change adds no collection and no index.

## Design

### 1. The store

File: `src/upgrade_portal/capture/store.py`.

- `_RUN_LIST_HEAD` adds `FILTER doc.operation_id == null`. The count query and the page query of `list_runs` both start with this head, so the total and the rows agree. A single-site run holds no `operation_id` field, and AQL reads a missing field as `null`.
- `OPERATION_LIST_FIELDS` names the projected fields of one operation row.
- `OperationQuery` holds the organization, the optional site, and the page size.
- `OperationListPage` holds the rows, the page size, and the availability flag.
- `list_operations(query, database=None)` runs one query. The query filters on `operation_id != null` and on `org_id`. If the query names a site, the query also filters on `@site_id IN doc.site_ids`. The query sorts by `created_at` and then by `updated_at`, both descending. The query returns the projected fields and `families`, the unique `device_family` values of the children.

The operation query returns no `children`, no `owner` history, and no device list. The route needs `owner` for one comparison only, and the shaper drops it.

### 2. The shaper

File: `src/upgrade_portal/upgrade/org_history.py`. The module has no Flask import and no identity import, so a unit test calls it directly.

- `OperationHistorySection` is the frozen value that the template reads: `rows`, `org_selected`, and `database_available`.
- `OrgOperationHistory(owner_key, moment_text)` builds the section.
  - `section(lister, org_id, site_id, limit)` reads no record when no organization is selected.
  - `row(record)` returns one template row. The row holds `can_open` and never the owner key.

### 3. The route

File: `src/upgrade_portal/app/routes/review.py`.

- `OPERATION_LISTER_KEY = "OPERATION_LISTER"` is the new seam. A test injects a stand-in through the application config.
- `store_operation_rows(org_id, site_id="", limit=...)` is the fallback. It follows `store_run_rows` and loads the store module at call time.
- `operation_history_section(site_id, limit)` reads the owner key and the selected organization, and then builds the section.
- `history_page` passes `operation_section` to the template.

File: `src/upgrade_portal/app/seam_shapes.py` records the call `lister(org_id, site_id=..., limit=...)` for the new seam.

### 4. The template

The section follows the bulk-action dialog and comes before the Audit log. Every value arrives ready from the shaper, so the template holds no rule. The template reads `operation_section | default(none, true)`, so a direct render without the value still works.

### 5. The aggregate record

File: `src/firmware/aggregate_upgrade_service.py`. `_build_record` writes `created_at` and `updated_at` from one clock read.

### 6. The browser test stand-ins

- `PortalRecordStore.list_runs` skips each operation record, as the store does.
- `PortalRecordStore.list_operations` returns the same projection as the store.
- `E2ERecordOverrides` gains the required field `operation_lister`. The browser server then never falls back to the ArangoDB trap.

## Test plan

| Level | File | Proof |
| - | - | - |
| Unit | `tests/unit/upgrade_portal/test_store_history.py` | The run query excludes operation records. The operation query binds only the filled fields, and it projects the fields. A failed query reports an empty page. |
| Unit | `tests/unit/upgrade_portal/test_org_history.py` | The shaper rules: ownership, site names, family order, missing values, and no read without an organization. |
| Contract | `tests/contract/upgrade_portal/test_history_operations.py` | The page renders the section. The page shows the owner link, the note for another session, the state with no organization, and the state with no database. The page forwards the site filter. The HTML holds no owner key. |
| Browser | `tests/e2e/upgrade_portal/test_org_upgrade_history.py` | A real browser starts a multi-site upgrade, finds the row, and opens the progress page. A second browser sees the note and no link. |

## Risk

- The run history loses the operation rows. This loss is the purpose of the change. The history now shows those rows in their own section.
- The operation query reads the whole `upgrade_runs` collection, because no index covers `operation_id`. The collection held 71 records on 2026-09-24. The history already reads the collection in the same way when the page names no site.
- A record that an older release wrote holds no `created_at` value. The row shows "Not recorded", and the record sorts after the newer records.
