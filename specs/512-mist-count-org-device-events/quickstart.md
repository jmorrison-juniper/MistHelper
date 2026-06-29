# Phase 1 Quickstart: CountOrgDeviceEvents Menu Item

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Contract**: [contracts/count_org_device_events.md](./contracts/count_org_device_events.md)
**Data model**: [data-model.md](./data-model.md)

This quickstart shows a developer how to run the new menu item locally, what `.env`
values it needs, what files it writes, and how to confirm the quality gates.

## 1. Prerequisites

- Python 3.13+ installed.
- Repo checked out at the worktree root.
- Venv activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Dependencies installed:
  ```powershell
  pip install -r requirements.txt   # or: uv pip sync requirements.txt
  ```

## 2. Required `.env` Variables

The repo-local `.env` (git-ignored) MUST contain:

```dotenv
MIST_HOST=api.mist.com                    # or api.eu.mist.com / api.gc1.mist.com etc.
MIST_API_TOKEN=<your_personal_api_token>  # never log; never commit
MIST_ORG_ID=<your_default_org_uuid>       # pre-fills the org_id prompt
```

Optional:
```dotenv
MIST_PAGE_LIMIT=1000                      # global page-size knob, unused by this op
```

## 3. Expected Output

When the menu item completes successfully, two files appear under `data/` (CSV backend
shown; SQLite and ArangoDB backends write equivalent structures):

| File | Contents |
|------|----------|
| `data/org_device_events_count_summary.csv` | One row: `org_id, distinct, start, end, limit_value, total, result_row_count, retrieved_at_epoch` |
| `data/org_device_events_count_results.csv` | N rows: `org_id, distinct, start, end, result_key, count, retrieved_at_epoch` |

SQLite backend writes the same fields into the tables defined in
[data-model.md](./data-model.md) (`org_device_events_count_summary` and
`org_device_events_count_results`) inside `data/mist_data.db`.

## 4. Example Invocation

### Interactive (menu)

```powershell
python MistHelper.py
# At the menu prompt, type: 195
# (or whatever menu number this op was assigned at task generation time)
```

Prompt sequence:
```text
[org_device_events_count:org_id] Org ID [<MIST_ORG_ID>]: <Enter to accept>
[org_device_events_count:distinct] Group by attribute (type / model / ap / apfw /
                                     site_id / text / timestamp) [type]: type
[org_device_events_count:duration] Window (e.g. 1d, 7d, 2w) [1d]: 1d
INFO  Counting device events for org abc123... distinct=type duration=1d
DEBUG Count response: total=4287 results_rows=12 window=1719527496-1719613896
INFO  Flattening count response into summary + results rows
DEBUG Flattened 1 summary row and 12 result rows
INFO  Writing output via DataExporter (backend=csv)
Wrote data/org_device_events_count_summary.csv (1 row)
Wrote data/org_device_events_count_results.csv (12 rows)
```

### Direct (automation)

```powershell
python MistHelper.py --menu 195
# With prompts pre-answered via .env defaults; non-interactive in --test mode.
```

## 5. Implementation Sketch (for the implementer)

The method body in `MistHelper.py` looks roughly like this. Every line carries an inline
comment and the action-logging pattern brackets every meaningful step (per Constitution
principles VI and VII).

```python
def export_org_device_events_count(self, org_id=None, distinct="type", duration="1d"):
    # Step 1: prompt sequence via safe_input (SSH/container EOF safe)
    org_id = org_id or safe_input(                                  # accept arg or prompt
        f"Org ID [{os.environ.get('MIST_ORG_ID','')}]: ",           # show default from env
        context="org_device_events_count:org_id",                   # context for EOF log
    ) or os.environ.get("MIST_ORG_ID", "")                          # fall back to env
    if not is_valid_uuid(org_id):                                   # validate-early
        logging.warning("Invalid org_id supplied: %s", org_id)      # log and exit
        return                                                      # no API call
    distinct = safe_input(                                          # prompt for distinct
        f"Group by [{distinct}]: ",                                 # show current default
        context="org_device_events_count:distinct",                 # context tag
    ) or distinct                                                   # keep default on empty
    if distinct not in ALLOWED_DISTINCT_KEYS:                       # allow-list enforce
        logging.warning("Distinct key not allowed: %s", distinct)   # log and exit
        return                                                      # safety-first
    duration = safe_input(                                          # prompt for window
        f"Duration [{duration}]: ",                                 # show default
        context="org_device_events_count:duration",                 # context tag
    ) or duration                                                   # default on empty
    # Step 2: API call (single GET, no pagination needed for count)
    logging.info(                                                   # log before action
        "Counting device events for org %s distinct=%s duration=%s",
        org_id, distinct, duration,                                 # values for trace
    )
    response = mistapi.api.v1.orgs.devices.events.count.countOrgDeviceEvents(
        self.session, org_id, distinct=distinct, duration=duration, # SDK call
    ).data                                                          # mistapi returns Response
    logging.debug(                                                  # log after action
        "Count response: total=%d results_rows=%d window=%d-%d",
        response.get("total", 0), len(response.get("results", [])), # summary counts
        response.get("start", 0), response.get("end", 0),           # window echo
    )
    # Step 3: flatten into summary + results rows
    logging.info("Flattening count response into summary + results rows")
    summary_row, result_rows = self._flatten_count_response(        # private helper
        org_id, response,                                           # inputs
    )
    logging.debug(                                                  # log after flatten
        "Flattened 1 summary row and %d result rows", len(result_rows),
    )
    # Step 4: write both tables via DataExporter (backend-agnostic)
    logging.info("Writing output via DataExporter")                 # log before write
    DataExporter.write_with_format_selection(                       # summary table
        [summary_row], "org_device_events_count_summary",
        api_function_name="countOrgDeviceEvents",                   # PK lookup key
    )
    DataExporter.write_with_format_selection(                       # results table
        result_rows, "org_device_events_count_results",
        api_function_name="countOrgDeviceEvents",                   # PK lookup key
    )
    logging.debug("DataExporter writes complete")                   # log after write
```

The total line count is well under 25 executable lines, the parameter count is 4, and
the logical block count is 4 (prompts / validate / API call / write) -- all within the
Five-Item Rule limits.

## 6. Quality Gates (run before committing)

```powershell
# Syntax (no output = success)
python -m py_compile MistHelper.py

# Lint (must pass clean)
python -m ruff check MistHelper.py

# Format (run without --check to auto-fix)
python -m black --check MistHelper.py

# Smoke test (uses .env for prompt defaults; --test mode is non-interactive)
python MistHelper.py --test
```

If any gate fails, fix the underlying issue (do **not** add `# noqa`, `# type: ignore`,
or `# nosec` suppressions -- see Constitution: Security Findings: Fix Over Suppress).

## 7. Deployment Pipeline (after gates pass)

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 195 countOrgDeviceEvents"
git push origin main
gh run watch                                                # wait for container build
podman pull ghcr.io/jmorrison-juniper/misthelper:latest     # pull new image
podman stop misthelper ; podman rm misthelper               # cycle the container
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest             # restart
podman ps                                                   # verify healthy
```
