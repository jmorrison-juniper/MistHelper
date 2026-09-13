# Phase 1 Quickstart: countSiteAlarms Menu Item

This quickstart walks a developer through running the new menu item locally on Windows
11 with the project virtualenv. It also lists the quality gates that must pass before
the change can be committed.

## 1. Prerequisites

- Python 3.13+
- Project venv activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- `.env` populated with the following keys at the repo root:
  ```env
  MIST_HOST=api.mist.com          # or api.eu.mist.com / api.gc1.mist.com / etc.
  MIST_API_TOKEN=<your token>      # Required, never logged
  MIST_ORG_ID=<your org UUID>      # Optional, used as default for org-scoped menus
  ```
  The new menu item does **not** require `MIST_ORG_ID` because the SDK derives the org
  from the active `APISession` and the supplied `site_id`. `MIST_API_TOKEN` and
  `MIST_HOST` are mandatory.

## 2. Expected output

After a successful run, the following files appear under `data/`:

- `data/site_alarms_count_summary.csv` -- one new row per `(site_id, distinct, start,
  end)` window
- `data/site_alarms_count_buckets.csv` -- one row per bucket returned in `results[]`
- `data/mist_data.db` -- SQLite tables `site_alarms_count_summary` and
  `site_alarms_count_buckets` upserted via `INSERT OR REPLACE`
- `data/script.log` -- ASCII-only log lines emitted by the new method

If the ArangoDB + Redis polyglot backend is enabled (see `documentation/` for the
configuration steps), the graph edges to the existing `site_id` vertex are written by
`DataExporter` automatically.

## 3. Interactive invocation

```powershell
python MistHelper.py
# Menu prompt appears.
# Select operation 97 (countSiteAlarms).
# Prompts (all driven by safe_input):
#   Site ID:                <paste UUID, e.g. 441a1214-6928-442a-8e92-e1d34b8ec6a6>
#   Distinct field [type]:  type            # press Enter to accept default
#   Duration [1d]:          1d              # press Enter to accept default
# The method:
#   1. logs INFO before the SDK call
#   2. calls mistapi.api.v1.sites.alarms.count.countSiteAlarms(...)
#   3. logs DEBUG with bucket count and total
#   4. flattens response.results into bucket rows + summary row
#   5. logs DEBUG with row counts produced
#   6. logs INFO before write
#   7. calls DataExporter.write_with_format_selection(summary_rows,
#         "site_alarms_count_summary.csv",
#         api_function_name="countSiteAlarms",
#         pk_strategy_key="summary")
#   8. calls DataExporter.write_with_format_selection(bucket_rows,
#         "site_alarms_count_buckets.csv",
#         api_function_name="countSiteAlarms",
#         pk_strategy_key="buckets")
#   9. returns 0
```

## 4. Non-interactive (test sweep / automation) invocation

```powershell
python MistHelper.py --menu 97
```

When `--test` is set, the menu method reads `MIST_SITE_ID` from `.env` (added to
`.env.example`) and uses the documented defaults (`distinct=type`, `duration=1d`) so
no `safe_input()` prompts block the test sweep. The skip list (14, 18, 63-65, 90-100)
is unaffected. The proposed menu number 97 sits at the bottom of the Resource Intensive
cluster; if `python MistHelper.py --test` is configured to skip 97 it must be updated
in the same PR.

## 5. Quality gates (run **before** every commit)

All four gates must pass on `MistHelper.py` before the change is allowed to push.

```powershell
# 1. Syntax check -- no output on success
python -m py_compile MistHelper.py

# 2. Lint -- must report 0 errors
python -m ruff check MistHelper.py

# 3. Format -- must report "would reformat 0 files"
python -m black --check MistHelper.py

# 4. Test sweep -- must exit 0 on menu 97 against a known org/site
python MistHelper.py --test
```

If `black --check` reports differences, run `python -m black MistHelper.py` to apply
formatting, then re-run the full four-gate sequence. Do **not** commit until all four
gates pass cleanly.

## 6. Acceptance verification

After the change is live, confirm:

1. `data/site_alarms_count_summary.csv` exists and has at least one new row.
2. `data/site_alarms_count_buckets.csv` exists and `count` columns sum to the
   `total` column on the matching summary row (sanity check).
3. Rerunning the menu against the same site does **not** create duplicate primary keys
   in `site_alarms_count_summary` (SQLite `INSERT OR REPLACE` upsert behavior).
4. `data/script.log` contains the ASCII-only log lines `Fetching alarm counts for site
   ...` (INFO) and `Alarm count buckets=... total=...` (DEBUG); no API token or
   personally identifying data is logged.
5. README.md operation count was bumped and the new operation row appears in the menu
   table.
6. CHANGELOG.md has a new `version YY.MM.DD.HH.MM - add menu 97 countSiteAlarms` entry.
