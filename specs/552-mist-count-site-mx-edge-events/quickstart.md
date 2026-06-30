# Phase 1 Quickstart: countSiteMxEdgeEvents (Menu 96)

**Feature**: 552-mist-count-site-mx-edge-events

## Run the Menu Item Locally

```powershell
# 1. From the worktree root, activate the venv
.venv\Scripts\Activate.ps1

# 2. Interactive run (will prompt for site_id, distinct, duration, etc.)
python MistHelper.py --menu 96

# 3. Non-interactive run during automated tests
python MistHelper.py --test            # Includes menu 96 in the default sweep
```

## Required .env Variables

```dotenv
# Mist Cloud regional host -- pick the one that matches your org tenant.
# Examples: api.mist.com, api.eu.mist.com, api.gc1.mist.com, api.ac2.mist.com
MIST_HOST=api.mist.com

# API token issued to a user that has read access to the target org / site.
# Never logged, never written to data/. Pulled by mistapi.APISession.
MIST_API_TOKEN=<your-mist-api-token>

# Optional: pin the default org used for --test runs.
# The menu itself does not require ORG_ID because the endpoint is site-scoped,
# but the test harness uses it to authenticate.
ORG_ID=<your-default-org-uuid>
```

The `MIST_HOST` and `MIST_API_TOKEN` values are required. The menu prompts for
`site_id` and every optional query parameter at runtime through `safe_input()`,
so no extra `.env` entries are needed for this feature.

## Expected `data/` Output

After a successful run the following files exist:

```text
data/site_mxedge_events_count_summary.csv     # One row per (site, distinct, window) slice
data/site_mxedge_events_count_buckets.csv     # One row per (slice, grouping value)
data/mist_data.db                              # SQLite tables of the same names (if SQLite backend selected)
data/script.log                                # Action log with INFO/DEBUG entries for this run
```

Sample summary row (CSV):

```text
site_id,distinct,start,end,total,limit,bucket_count,retrieved_at
4ac1d65b-...-...-...-4f8e9b21a113,type,1719360000,1719446400,4218,100,12,1719660000
```

Sample bucket rows (CSV):

```text
site_id,distinct,start,end,bucket_key,bucket_value,count,retrieved_at
4ac1d65b-...-...-...-4f8e9b21a113,type,1719360000,1719446400,type,MXEDGE_TUNTERM_CONNECTED,2031,1719660000
4ac1d65b-...-...-...-4f8e9b21a113,type,1719360000,1719446400,type,MXEDGE_AUTH_FAILURE,57,1719660000
```

## Example Invocation With Prompts

```text
PS> python MistHelper.py --menu 96
[INFO] Menu 96: Count Mist Edge events for a site by distinct attribute.
Enter site_id (UUID): 4ac1d65b-1234-4def-89ab-4f8e9b21a113
Enter distinct attribute [type]: type
Enter duration window (e.g. 1h, 1d, 7d) [1d]: 1d
Enter mxedge_id filter (blank for all):
Enter mxcluster_id filter (blank for all):
Enter type filter (blank for all):
Enter service filter (blank for all):
Enter bucket limit [100]: 100
[INFO] Counting Mist Edge events for site 4ac1d65b-...-4f8e9b21a113 by distinct=type
[DEBUG] Received envelope: total=4218 buckets=12 limit=100
[INFO] Flattening response into 1 summary row and 12 bucket rows
[INFO] Writing to backend: csv,sqlite
[DEBUG] Wrote 1 row to site_mxedge_events_count_summary
[DEBUG] Wrote 12 rows to site_mxedge_events_count_buckets
[INFO] Menu 96 complete.
PS>
```

## Expected Method Outline (in `MistHelper.py`)

Placed on the existing `MxEdgeExportUtils` class. Sketch only -- final code is
produced during `/speckit.tasks` and `/speckit.implement`.

```python
def export_site_mxedge_events_count(            # New public menu method, ~22 lines
    self,                                       # Bound to MxEdgeExportUtils instance
    site_id: str,                               # Required Mist site UUID from prompt
    distinct: str,                              # Grouping attribute (default "type")
    filters: dict,                              # Optional mxedge_id/mxcluster_id/type/service/start/end/limit
    duration: str,                              # Window like "1d" (mutually exclusive with start/end)
):
    """Count Mist Edge events for a site by distinct attribute."""
    # Validate site_id shape early -- safety-first, return on failure.
    if not self._is_valid_uuid(site_id):                                 # Reject malformed input before SDK call
        logging.warning("Invalid site_id rejected: %s", site_id)         # ASCII-only WARNING per Principle V
        return                                                            # Safety-first early return
    logging.info(                                                         # Action log BEFORE the API call (Principle VII)
        "Counting Mist Edge events for site %s by distinct=%s",           # ASCII-only with %s formatting
        site_id, distinct,
    )
    response = count_mod.countSiteMxEdgeEvents(                          # Call mistapi (sole permitted interface)
        self.api_session, site_id,                                       # Authenticated session + path param
        distinct=distinct, duration=duration, **filters,                 # Optional query params
    )
    envelope = response.data                                              # Parsed JSON object from APIResponse
    logging.debug(                                                        # Action log AFTER the API call (Principle VII)
        "Received envelope: total=%d buckets=%d limit=%d",                # Counts only -- never secrets
        envelope.get("total", 0),
        len(envelope.get("results", [])),
        envelope.get("limit", 0),
    )
    summary_row, bucket_rows = self._flatten_count_envelope(             # Single helper keeps method under 25 lines
        site_id, envelope,                                               # Pass site_id so it lands in the row
    )
    DataExporter.write_with_format_selection(                            # Multi-backend output per Principle IV
        [summary_row], "site_mxedge_events_count_summary",               # Envelope table
        api_function_name="countSiteMxEdgeEvents",                       # Drives PK strategy lookup
    )
    DataExporter.write_with_format_selection(                            # Second call for the bucket table
        bucket_rows, "site_mxedge_events_count_buckets",                  # Per-bucket rows
        api_function_name="countSiteMxEdgeEvents",                       # Same operationId; PK strategy resolves to bucket table
    )
```

## Quality Gates (run in this order before commit)

```powershell
# 1. Python syntax -- MUST pass with zero errors (Principle IV)
python -m py_compile MistHelper.py

# 2. Lint -- MUST pass clean
python -m ruff check MistHelper.py

# 3. Format -- MUST be clean (run without --check to auto-fix locally)
python -m black --check MistHelper.py

# 4. Functional test -- new menu 96 must return 0 on a known site
python MistHelper.py --test

# 5. Optional: targeted invocation
python MistHelper.py --menu 96
```

All four steps must be green before the commit. The container-build workflow
(`.github/workflows/container-build.yml`) re-runs the validation job on push;
the `auto-merge` label is added only after CodeQL is green
(`gh pr checks <pr-number> --watch`).

## Troubleshooting

| Symptom                                                | Likely Cause                                                | Fix                                                       |
|--------------------------------------------------------|-------------------------------------------------------------|-----------------------------------------------------------|
| `PermissionError: [Errno 13] ... /app/data/script.log` | Container `data/` mount not writable                        | `chmod -R 777 data/` on the host before `podman run`      |
| 401 from Mist API                                      | `MIST_API_TOKEN` missing or expired                          | Regenerate token in Mist Cloud UI, update `.env`          |
| 404 logged as WARNING                                  | `site_id` does not exist under the authenticated org         | Re-check the UUID; the run exits 0 as designed            |
| 429 logged repeatedly                                  | Rate-limit ceiling hit                                       | Let adaptive delay back off; rerun later or use `--fast`  |
| Empty `results[]`                                      | No Mist Edge events in the requested window                  | Widen `duration` (e.g. `7d`); rerun                       |
