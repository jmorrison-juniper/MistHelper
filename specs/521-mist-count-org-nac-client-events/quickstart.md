# Quickstart: countOrgNacClientEvents (menu 195)

**Feature**: `521-mist-count-org-nac-client-events`

This quickstart shows a developer how to run, validate, and gate the new menu
item locally.

## 1. Prerequisites

- Python 3.13+ with the project venv activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- `mistapi` 0.59+ installed (already in `requirements.txt`).
- `data/` directory writable (`chmod -R 777 data/` on first container run).
- An `.env` file at the repo root containing:

  | Variable         | Required | Purpose                                                        |
  |------------------|----------|----------------------------------------------------------------|
  | `MIST_HOST`      | Yes      | Mist Cloud regional host (e.g. `api.mist.com`, `api.eu.mist.com`).|
  | `MIST_API_TOKEN` | Yes      | API token with read access to NAC events on the target org.    |
  | `MIST_ORG_ID`    | No       | Default org UUID used to pre-fill the first prompt.            |

## 2. Run the menu item interactively

```powershell
python MistHelper.py
# In the menu, type:
195
```

You will be prompted in order:

1. `Enter org_id [<MIST_ORG_ID default if set>]:` -- press Enter to accept the default.
2. `Distinct attribute [type / nas_vendor / vlan / ssid / port_type / auth_type] (default: type):` -- press Enter for `type`.
3. `Filter by event_type (blank = no filter):` -- press Enter to skip.
4. `Time window: (d)uration or (r)ange? [d]:` -- press Enter for duration mode.
5. `Duration (e.g. 1d, 7d, 2w) [1d]:` -- press Enter for the default.
6. `Result limit [100]:` -- press Enter for the default.

## 3. Non-interactive run (for `--test` and CI)

```powershell
python MistHelper.py --menu 195
```

In non-interactive mode the method takes its inputs from environment defaults
(`MIST_ORG_ID`, `distinct=type`, `duration=1d`, `limit=100`) and skips any
prompt whose value can be resolved. EOF on `safe_input()` exits cleanly with
status code 0.

## 4. Expected output

CSV (when CSV backend is active):

```
data\org_nac_client_events_count_<org_id>_<YYYYMMDD_HHMMSS>.csv
```

Header row:

```
org_id,distinct_field,distinct_value,count,start_epoch,end_epoch,query_limit,query_total,event_type_filter,fetched_at
```

SQLite (when SQLite backend is active):

```
data\mist_data.db -> table org_nac_client_events_count
```

First run creates the table and indexes via the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry; subsequent runs upsert in place via
the unique composite index.

## 5. Method outline (for reviewers)

The new method on the NAC client export class follows this skeleton -- every
executable line carries an inline comment per Constitution VI, and action
logging brackets every meaningful step per Constitution VII:

```python
def export_org_nac_client_events_count(self):  # menu 195 entrypoint
    org_id = safe_input(  # prompt with .env default; EOF-safe in SSH
        f"Enter org_id [{self.default_org_id}]: ",
        context="nac_client_events_count:org_id",
    ) or self.default_org_id  # fall back to .env when blank
    distinct_field = self._prompt_distinct()  # validates against allow-list
    event_type_filter = safe_input(  # optional filter, blank = no filter
        "Filter by event_type (blank = no filter): ",
        context="nac_client_events_count:type",
    ) or None  # convert empty string to None for the SDK
    window = self._prompt_time_window()  # returns dict with start/end/duration
    logging.info(  # before-call action log
        "Fetching NAC client event counts for org %s grouped by %s window=%s",
        org_id, distinct_field, window,
    )
    response = mistapi.api.v1.orgs.nac_clients.events.count.countOrgNacClientEvents(  # SDK call
        self.session,
        org_id=org_id,
        distinct=distinct_field,
        type=event_type_filter,
        start=window.get("start"),
        end=window.get("end"),
        duration=window.get("duration"),
        limit=window.get("limit", 100),
    )
    payload = response.data or {}  # defensive default on empty body
    rows = self._flatten_count_rows(  # build one row per group with envelope fields denormalized
        payload, org_id=org_id, distinct_field=distinct_field,
        event_type_filter=event_type_filter,
    )
    logging.debug(  # after-call action log with counts
        "NAC event count: total=%d groups=%d limit=%d",
        payload.get("total", 0), len(rows), payload.get("limit", 0),
    )
    DataExporter.write_with_format_selection(  # routes to CSV / SQLite / ArangoDB
        rows,
        filename=f"org_nac_client_events_count_{org_id}",
        api_function_name="countOrgNacClientEvents",
    )
```

## 6. Quality gates (run before commit)

```powershell
python -m py_compile MistHelper.py     # syntax (no output = pass)
python -m ruff check MistHelper.py     # lint
python -m black --check MistHelper.py  # format check (drop --check to auto-fix)
python MistHelper.py --test            # exercises menu 195 in non-interactive mode
```

All four must pass before committing. The commit follows the deployment
pipeline documented in `.github/copilot-instructions.md`:

```powershell
git add MistHelper.py README.md CHANGELOG.md specs/521-mist-count-org-nac-client-events/
git commit -m "version YY.MM.DD.HH.MM - add menu 195 countOrgNacClientEvents"
git push origin main
gh run watch  # wait for container-build.yml
```
