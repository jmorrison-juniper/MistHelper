# Quickstart: countSiteOtherDeviceEvents (Menu 197)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md)

This quickstart shows a developer how to run the new menu item locally on
Windows 11, what `.env` variables are required, what file lands in `data/`,
and which quality gates must be green before commit.

## Prerequisites

- Python 3.13 or newer on PATH.
- A populated `.venv` in the repo root:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- `pip install -r requirements.txt` has been run (or `uv pip sync` if using
  UV). Specifically, `mistapi>=0.59` must be importable.
- A valid Mist API token with at least read access to the target site.
- The target site exists and has at least one non-Juniper ("other") device
  reporting events; otherwise the response will be empty and the menu will
  log "no data returned".

## Required `.env` Variables

The menu item reads these from `.env` (git-ignored) via `python-dotenv` and
the existing MistHelper bootstrap:

| Variable | Purpose | Example |
|----------|---------|---------|
| `MIST_HOST` | Mist Cloud host (region-dependent). | `api.mist.com` |
| `MIST_API_TOKEN` | API token. Never logged. Loaded into `mistapi.APISession`. | `abc...` |
| `MIST_PAGE_LIMIT` (optional) | Default page size for paginated endpoints. Not used by this count endpoint but inherited from existing config. | `1000` |

No new `.env` keys are introduced by this feature. Update
`deploy/.env.example` only if and when this list expands.

## Expected `data/` Output

After a successful run, two files (CSV backend) or two SQLite tables (SQLite
backend) appear under `data/`:

- `data/site_<site_id>_other_device_events_count_<distinct>_<YYYYMMDDHHMMSS>_summary.csv`
- `data/site_<site_id>_other_device_events_count_<distinct>_<YYYYMMDDHHMMSS>_results.csv`

SQLite tables (always created if the SQLite backend is active):

- `site_other_device_events_count_summary` -- one row per run.
- `site_other_device_events_count_results` -- one row per distinct group
  returned.

ArangoDB backend writes to collections of the same names. Redis caches the
most recent summary keyed by `(site_id, distinct, start, end)`.

## Example Invocation (Interactive)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the menu prompt:
197
# Then respond to the safe_input() prompts:
#   site_id: 11111111-2222-3333-4444-555555555555
#   distinct attribute (Enter for API default): type
#   event type filter (Enter to skip): <Enter>
#   time window [1d/7d/custom] (Enter for 1d): 1d
#   limit (Enter for 100): <Enter>
```

Expected console output (ASCII-only, structured per Principle V):

```
INFO  Counting other-device events for site 11111111-... distinct=type window=1d
DEBUG Count response: total=42 groups=2 limit=100
INFO  Flattening other-device count response (2 groups)
DEBUG Flattened 2 result rows + 1 summary row
INFO  Exporting other-device count results (api_function_name=countSiteOtherDeviceEvents)
DEBUG Export complete: backend=sqlite tables=2 rows=3
```

## Example Invocation (Non-Interactive Test Sweep)

```powershell
python MistHelper.py --menu 197
```

In `--test` mode, MistHelper sources `site_id` and other prompts from a
known-good test fixture in `.env` (e.g. `TEST_SITE_ID`). The menu must exit 0
on a healthy fixture; on a fixture with no other devices, it must exit 0 with
a single `WARNING` log line ("no data returned"), not a traceback.

## Method Outline (for implementation reference)

The new method on `SiteOtherDeviceExportUtils` follows the documented inline
comments + action logging pattern. Skeleton:

```python
def export_site_other_device_events_count(self, site_id, distinct=None, time_window="1d"):
    # Validate the user-supplied site UUID before any network I/O.
    if not is_valid_uuid(site_id):                             # Reject malformed UUIDs early per Principle III
        logging.warning("Invalid site_id %s; aborting", site_id)  # ASCII-only warning, no secrets
        return                                                 # Early return -- never proceed with bad input
    logging.info("Counting other-device events for site %s distinct=%s window=%s",
                 site_id, distinct, time_window)               # Action log BEFORE the API call per Principle VII
    response = mistapi.api.v1.sites.otherdevices.events.count.countSiteOtherDeviceEvents(
        self.mist_session, site_id,                            # Reuse existing APISession from .env bootstrap
        distinct=distinct, duration=time_window,               # Forward optional grouping + window
    )                                                          # Single SDK call, no manual pagination needed
    logging.debug("Count response: total=%s groups=%s limit=%s",
                  response.data.get("total"),                  # Total distinct groups the API observed
                  len(response.data.get("results", [])),       # Groups actually returned
                  response.data.get("limit"))                  # Limit the API echoed back
    summary_row, count_rows = self._flatten_count_payload(site_id, distinct, response.data)  # Helper splits envelope from results
    DataExporter.write_with_format_selection(                  # Multi-backend writer per Principle IV constraint
        {"summary": [summary_row], "results": count_rows},     # Two-table payload for the exporter
        filename=f"site_{site_id}_other_device_events_count_{distinct or 'default'}",  # Disk-friendly filename root
        api_function_name="countSiteOtherDeviceEvents",        # Lookup key into ENDPOINT_PRIMARY_KEY_STRATEGIES
    )
```

Every executable line above carries an inline comment per Principle VI. The
method is 12 executable lines (well under the 25-line limit), takes 4
parameters (under the 5-param limit), and contains 3 logical blocks
(validate, call, export) -- all under the Five-Item Rule ceilings.

## Quality Gates (run all three before commit)

Every gate must pass with zero output (or "All checks passed" style success
banners) before `git add` / `git commit`:

```powershell
# 1. Syntax: must produce zero output on success
python -m py_compile MistHelper.py

# 2. Lint: must show "All checks passed!"
python -m ruff check MistHelper.py

# 3. Format: must show "would be left unchanged" (run without --check to auto-fix)
python -m black --check MistHelper.py

# 4. Runtime smoke (requires a known-good TEST_SITE_ID in .env)
python MistHelper.py --menu 197
```

If any gate fails, fix the root cause in MistHelper.py (do **not** add
`# noqa` / `# nosec` / `# type: ignore` suppressions -- see Constitution
"Fix Over Suppress"). Then re-run all four gates from scratch.

## Post-Commit Pipeline

Per Constitution Principle IV (Full Deployment Pipeline, NON-NEGOTIABLE),
after a green commit the following steps are mandatory and may not be
skipped:

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 197 countSiteOtherDeviceEvents"
git push origin main
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest
podman ps
```

The pipeline finishes only when `podman ps` shows the freshly tagged image
running with the new menu item dispatchable.
