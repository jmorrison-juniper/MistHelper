# Phase 1 Quickstart: countSiteSkyatpEvents (Menu 195)

**Feature**: 559-mist-count-site-skyatp-events
**Audience**: Developer adding the menu, then a junior NOC engineer running it.

## What This Menu Does

Calls `GET /api/v1/sites/{site_id}/skyatp/events/count` and writes one row per
returned bucket to the active output backend (CSV, SQLite, or ArangoDB+Redis).
Useful for answering questions like "how many Sky ATP `mw` (malware) events did
this site see in the last 7 days?" or "what is the distribution of threat levels?".

## Required .env Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `MIST_HOST` | Mist Cloud API host. | `api.mist.com` |
| `MIST_API_TOKEN` | API token with read access to the site. | `xxxx...` |
| `MIST_SITE_ID` (optional) | Default site UUID used when the prompt is left blank. | `1234abcd-...` |
| `MIST_PAGE_LIMIT` (optional) | Server-side bucket cap. Defaults to 100. | `100` |

The token is loaded by `mistapi.APISession` on startup and is never logged.

## Run Locally (Bare Windows venv)

```powershell
.\.venv\Scripts\Activate.ps1
python MistHelper.py --menu 195
```

Interactive prompts (all wrapped in `safe_input()`):

1. `Enter site_id [default from .env MIST_SITE_ID]:` -- paste a Mist site UUID or
   press Enter to use the `.env` default. Validated against the Mist UUID shape.
2. `Distinct attribute (type | threat_level | mac | device_mac | ip) [type]:` -- pick
   the dimension to bucket counts by. Empty input keeps `type`.
3. `Time window (e.g. 1d, 7d, 2w) [1d]:` -- the relative window passed as `duration`.
   Empty input keeps `1d`.

Direct (non-interactive) invocation for automation / `--test`:

```powershell
python MistHelper.py --menu 195
```

(The runner uses `MIST_SITE_ID` from `.env`, `distinct=type`, `duration=1d`.)

## Run in the Container

```powershell
podman exec -it misthelper python /app/MistHelper.py --menu 195
```

Or via SSH on port 2200 (interactive menu shell):

```bash
ssh -p 2200 misthelper@<container-host>
# At the menu, type: 195
```

## Expected Output

- **CSV**: `data/site_skyatp_events_count_<site_id>_<YYYYMMDD-HHMMSS>.csv`
- **SQLite**: `data/mist_data.db`, table `site_skyatp_events_count` (auto-created
  on first run).
- **ArangoDB**: collection `site_skyatp_events_count` + edge to parent site vertex.
- **Console**: a one-line summary `Wrote <N> count buckets for site <site_id> distinct=<distinct> window=<window>`.

Empty-result behaviour: `WARNING - No Sky ATP count buckets returned for site
<site_id>` -- the menu exits 0; no empty file is written.

## Method Outline (for the developer)

The new public method on `SiteAnomalyExporter` looks like this (target <=25 lines,
<=4 parameters, <=5 logical blocks; every executable line carries an inline comment
per Constitution VI):

```python
def export_site_skyatp_events_count(self, site_id, distinct="type", time_window="1d"):
    # Validate site_id shape before paying the API call cost
    if not ValidationUtils.is_uuid(site_id):
        logging.warning("Invalid site_id %s -- aborting menu 195", site_id)
        return
    # Log INFO before the API call per Action Logging (Constitution VII)
    logging.info("Fetching Sky ATP event counts for site %s distinct=%s window=%s",
                 site_id, distinct, time_window)
    # Single GET via the typed mistapi SDK (no hand-built URLs)
    response = mistapi.api.v1.sites.skyatp.events.count.countSiteSkyatpEvents(
        self.apisession, site_id, distinct=distinct, duration=time_window
    )
    envelope = response.data or {}                                  # Defensive: empty dict on 204/empty
    buckets = envelope.get("results", [])                           # Bucket array (may be empty)
    logging.debug("Received %d count buckets total=%s",
                  len(buckets), envelope.get("total"))               # Action Logging after API call
    rows = self._flatten_skyatp_count_buckets(site_id, envelope)    # Flatten to wide rows
    logging.debug("Flattened %d rows for export", len(rows))         # Action Logging after flatten
    DataExporter.write_with_format_selection(                       # Multi-backend write
        rows,
        f"site_skyatp_events_count_{site_id}",                       # Filename stem (DataExporter adds ts)
        api_function_name="countSiteSkyatpEvents",                   # Resolves PK strategy
    )
```

## Quality Gates (Must Pass Before Commit)

```powershell
python -m py_compile MistHelper.py        # Syntax: silent on success
python -m ruff check MistHelper.py        # Lint: must be clean
python -m black --check MistHelper.py     # Format: rerun without --check to auto-fix
python MistHelper.py --test               # Sweep test (skips 14, 18, 63-65, 90-100)
```

All four must be green before `git add` / `git commit`. The CI pipeline
(`.github/workflows/ci.yml`) re-runs them along with `mypy`, `pytest --cov`,
`bandit`, `pip-audit`, and `CodeQL`; the `auto-merge` label is only added after
every check (including CodeQL) passes.

## Files Touched in the Implementation PR

| File | Change |
|------|--------|
| `MistHelper.py` | New method on `SiteAnomalyExporter`; new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry; menu 195 registration. |
| `README.md` | Operation count 194 -> 195; new row in the menu table. |
| `CHANGELOG.md` | New `version YY.MM.DD.HH.MM` entry. |
| `specs/559-mist-count-site-skyatp-events/tasks.md` | Generated by `/speckit.tasks` (not by this plan). |
