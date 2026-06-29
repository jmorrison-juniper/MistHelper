# Phase 1 Quickstart: countOrgSiteMxEdgeEvents Menu Item

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This quickstart describes how a developer (or an autonomous agent) runs the new menu
item locally, what `.env` variables are needed, what files appear in `data/` after a
successful run, and which quality gates must pass before commit.

---

## Prerequisites

- Python 3.13+ available on `PATH`.
- A working virtualenv at `.venv/` populated from `requirements.txt`
  (`uv pip install -r requirements.txt` or `python -m pip install -r requirements.txt`).
- A `.env` file at the repository root (git-ignored) populated with at minimum:
  ```env
  MIST_HOST=api.mist.com
  MIST_API_TOKEN=<your-mist-api-token>
  MIST_ORG_ID=<a-known-org-uuid-for-default-prompts>
  ```
- The `data/` directory must be writable. On a fresh clone:
  ```powershell
  New-Item -ItemType Directory -Force -Path data | Out-Null
  ```
  Inside the container the bind-mounted host directory must be world-writable
  (`chmod -R 777 data`) -- see `.github/copilot-instructions.md` "Data Directory
  Permissions" section.

---

## Required .env Variables

| Variable | Purpose | Required | Notes |
|----------|---------|----------|-------|
| `MIST_HOST` | API hostname for the Mist cloud region | yes | Never logged. |
| `MIST_API_TOKEN` | Bearer token for Mist API auth | yes | Never logged; loaded via `python-dotenv`. |
| `MIST_ORG_ID` | Default org for interactive prompt 1 | no | If set, the org prompt accepts blank to use it. |

No additional environment variables are introduced by this feature.

---

## Expected Output Files

After a successful run the following files appear under `data/`:

- `data/org_mxedge_events_count_summary.csv` -- one row for the window just queried
  (or appended when the active backend is CSV-only).
- `data/org_mxedge_events_count_results.csv` -- N rows, one per bucket returned in
  `results[]`.
- `data/mist_data.db` -- updated with the same rows in the two tables defined in
  `data-model.md` (`org_mxedge_events_count_summary` and
  `org_mxedge_events_count_results`), upserted by composite primary key.
- `data/script.log` -- ASCII-only INFO/DEBUG lines confirming the API call, the
  flatten step, and the DataExporter writes.

When the polyglot ArangoDB + Redis backend is enabled (controlled by `.env`
`DATA_BACKEND=polyglot`) the same data appears as two document collections in
ArangoDB and a Redis cache key under namespace `mist:mxedge:event_count:`.

---

## Example Interactive Invocation

```powershell
.\.venv\Scripts\Activate.ps1
python MistHelper.py
# select menu number:
58
# org prompt (press Enter to use $env:MIST_ORG_ID):
<your-org-uuid>
# distinct attribute (default type):
type
# mxedge_id filter (blank to skip):

# mxcluster_id filter (blank to skip):

# event type filter (blank to skip):

# service filter (blank to skip):

# duration (default 1d):
1d
# limit (default 100):
100
```

Truncated log output:

```
INFO Counting org mxedge events for org <org-uuid> distinct=type duration=1d
DEBUG MxEdge events count: distinct=type total=842 results=14 window=[1751145216..1751231616]
INFO Writing org_mxedge_events_count_summary (1 row)
INFO Writing org_mxedge_events_count_results (14 rows)
```

## Example Non-Interactive Invocation (for `--test` / automation)

```powershell
python MistHelper.py --menu 58 --org-id <your-org-uuid> --distinct type --duration 1d
```

The `--menu <num>` direct invocation is the established automation entry point. When
the surrounding test harness pipes input lines, use stdin redirection:

```powershell
@"
<your-org-uuid>
type



1d
100
"@ | python MistHelper.py --menu 58
```

---

## Pseudocode of the New Method

For implementer reference; the actual code goes into the existing
`MistEdgeExportUtils` class (or equivalent existing mxedge-scoped class) in
`MistHelper.py`. Every line gets an inline comment per Constitution VI.

```python
def export_org_mxedge_events_count(self, org_id, distinct, filters, time_range):
    # Validate the org UUID before any network I/O (cheap fail-fast path).
    if not is_valid_uuid(org_id):
        logging.warning("Invalid org_id supplied to menu 58: %s", org_id)
        return

    # Action log: BEFORE the API call (Constitution VII).
    logging.info(
        "Counting org mxedge events for org %s distinct=%s duration=%s",
        org_id, distinct, time_range.get("duration"),
    )

    # SDK call -- the only permitted Mist API interface (mistapi 0.59+).
    response = mxedge_events_count_module.countOrgSiteMxEdgeEvents(
        self.mist_session, org_id,
        distinct=distinct, **filters, **time_range,
    )
    body = response.data

    # Action log: AFTER the API call (Constitution VII).
    logging.debug(
        "MxEdge events count: distinct=%s total=%d results=%d window=[%s..%s]",
        body.get("distinct"), body.get("total", 0),
        len(body.get("results", [])),
        body.get("start"), body.get("end"),
    )

    # Flatten the response into summary + results rows for DataExporter.
    summary_row, results_rows = self._flatten_mxedge_event_count(org_id, body)

    # Persist via the multi-backend exporter (CSV / SQLite / ArangoDB+Redis).
    DataExporter.write_with_format_selection(
        [summary_row], "org_mxedge_events_count_summary",
        api_function_name="countOrgSiteMxEdgeEvents",
        pk_variant="summary",
    )
    DataExporter.write_with_format_selection(
        results_rows, "org_mxedge_events_count_results",
        api_function_name="countOrgSiteMxEdgeEvents",
    )
```

The two `DataExporter.write_with_format_selection` calls are the only persistence
path; they handle CSV append, SQLite upsert via `INSERT OR REPLACE`, and ArangoDB +
Redis updates transparently using the strategy registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

All eight `safe_input()` calls live in a small private prompt helper invoked before
this method; each prompt passes a unique `context=` string so SSH / container EOF
events log a searchable breadcrumb. See `research.md` Research Task 5 for the
prompt sequence.

---

## Quality Gates (run BEFORE every commit)

The following must all pass before staging any change for this feature. The
commit is rejected by the deployment pipeline if any gate fails (Constitution IV).

```powershell
# 1. Syntax check -- no output means valid.
python -m py_compile MistHelper.py

# 2. Lint check -- must report 0 violations.
python -m ruff check MistHelper.py

# 3. Format check -- must report nothing to change.
python -m black --check MistHelper.py

# 4. End-to-end test of the menu sweep (skip list 14, 18, 63-65, 90-100 is unchanged).
python MistHelper.py --test
```

When all four pass:

```powershell
# 5. Commit with the UTC-timestamp version string the project requires.
git add MistHelper.py README.md CHANGELOG.md `
        specs/527-mist-count-org-site-mx-edge-events/
git commit -m "version YY.MM.DD.HH.MM - add menu 58 countOrgSiteMxEdgeEvents"

# 6. Push to trigger the container build workflow.
git push origin main

# 7. Watch the container build complete (~3-5 min).
gh run watch
```

After the workflow succeeds, refresh the local container:

```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest
podman ps
```

---

## Manual Verification Steps

1. Run the menu item against a known org and verify the two CSV files appear in
   `data/` with non-zero size.
2. Inspect `data/mist_data.db` with
   `sqlite3 data\mist_data.db ".schema org_mxedge_events_count_summary"`
   and confirm the DDL matches `data-model.md`.
3. Re-run the menu item with identical inputs and confirm SQLite row counts do NOT
   double (upsert behavior).
4. Re-run with a different `distinct` value and confirm new rows are appended for
   the same window (different `distinct` -> different PK).
5. Confirm `data/script.log` shows one INFO before the API call and one DEBUG after,
   ASCII-only, no token leakage.
