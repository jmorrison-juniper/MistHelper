# Phase 1 Quickstart: countSiteNacClientEvents (menu 96)

This quickstart shows how to run, validate, and verify the new MistHelper menu item
locally on Windows 11 with a Python 3.13+ venv.

## 1. Required `.env` Variables

The new menu item reads only the existing MistHelper credentials -- no new variables
are introduced. Confirm `.env` (at the repo root, git-ignored) contains:

```ini
MIST_HOST=api.mist.com                  # or api.eu.mist.com / api.gc1.mist.com etc.
MIST_API_TOKEN=<your-mist-api-token>    # never logged; loaded by mistapi.APISession
MIST_ORG_ID=<your-org-uuid>             # optional, used by other menu items
MIST_SITE_ID=<your-site-uuid>           # optional, lets --test auto-fill the prompt
```

## 2. Expected Output Files in `data/`

| Backend | Files created on first run |
|---------|----------------------------|
| CSV     | `data/site_nac_client_events_count_summary.csv` and `data/site_nac_client_events_count_results.csv` |
| SQLite  | Two tables in `data/mist_data.db`: `site_nac_client_events_count_summary`, `site_nac_client_events_count_results` |
| ArangoDB + Redis | Two collections of the same names; Redis cache key prefixes `mist:countSiteNacClientEvents:` |

The `data/` directory must be writable. If you see
`PermissionError: [Errno 13] Permission denied: '/app/data/script.log'` from inside
the container, fix host permissions:

```powershell
chmod -R 777 data\
```

## 3. Local Run (Interactive)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the prompt enter: 96
# Then answer the five prompts (press Enter to accept defaults):
#   site_id:           <paste your site UUID>
#   distinct [type]:   <Enter>
#   type filter []:    <Enter>
#   duration [1d]:     <Enter>
#   limit [100]:       <Enter>
```

Expected log lines (ASCII-only, `%s` formatted):

```
INFO  Counting NAC client events for site 11111111-2222-3333-4444-555555555555 distinct=type duration=1d
DEBUG NAC events count: total=42 distinct_buckets=5 limit=100
INFO  Flattening NAC events count response into summary + results rows
DEBUG Flattened: 1 summary row, 5 results rows
INFO  Writing NAC events count to backend via DataExporter
DEBUG DataExporter wrote site_nac_client_events_count_summary (1 row), site_nac_client_events_count_results (5 rows)
```

## 4. Local Run (Non-Interactive Test Sweep)

```powershell
python MistHelper.py --test
```

Menu 96 is inside the default sweep range and is exercised automatically. The test
sweep uses `MIST_SITE_ID` from `.env` and accepts all defaults for the four optional
prompts.

## 5. Direct-Invocation One-Shot

```powershell
python MistHelper.py --menu 96
```

Skips the top-level menu and jumps straight to the five prompts.

## 6. Quality Gates (Run Before Every Commit)

All three gates must pass clean. None is allowed to be skipped or `# noqa`'d.

```powershell
python -m py_compile MistHelper.py     # syntax check (no output on success)
python -m ruff check MistHelper.py     # lint check (must be empty)
python -m black --check MistHelper.py  # format check (re-run without --check to auto-fix)
```

After the gates pass, run the test sweep one more time to confirm the new menu item
returns 0:

```powershell
python MistHelper.py --test
```

## 7. Method Outline (Reference Only -- Implementation Lives in Phase 2)

The new method on the existing site-NAC / events export class will look approximately
like this. Each executable line carries an inline comment per Constitution Principle VI;
`logging.info` / `logging.debug` bookend every meaningful step per Principle VII.

```python
def export_site_nac_client_events_count(
    self,
    site_id: str,
    distinct: str = "type",
    duration: str = "1d",
    limit: int = 100,
) -> int:
    """Count NAC client events at a site, grouped by a chosen distinct attribute."""
    if not self._is_valid_uuid(site_id):                                  # Reject malformed site_id before wasting an API call
        logging.warning("Invalid site_id shape: %s", site_id)             # Log and bail; user-friendly message, no traceback
        return 1                                                          # Non-zero exit signals validation failure to --test sweep
    logging.info(                                                         # Action log before SDK call (Principle VII)
        "Counting NAC client events for site %s distinct=%s duration=%s",
        site_id, distinct, duration,
    )
    api_response = mistapi.api.v1.sites.nac_clients.events.count \
        .countSiteNacClientEvents(                                        # The one and only Mist API call this method makes
            self.mist_session, site_id,
            distinct=distinct, duration=duration, limit=limit,
        )
    envelope = api_response.data                                          # Unwrap APIResponse to the JSON envelope dict
    logging.debug(                                                        # Action log after SDK call with summary counts
        "NAC events count: total=%d distinct_buckets=%d limit=%d",
        envelope.get("total", 0), len(envelope.get("results", [])),
        envelope.get("limit", limit),
    )
    summary_row, result_rows = self._flatten_count_envelope(              # Single flatten helper, kept private to this class
        site_id, distinct, envelope,
    )
    DataExporter.write_with_format_selection(                             # Multi-backend output: CSV / SQLite / ArangoDB+Redis
        {"summary": [summary_row], "results": result_rows},
        filename="site_nac_client_events_count",
        api_function_name="countSiteNacClientEvents",                     # Drives ENDPOINT_PRIMARY_KEY_STRATEGIES lookup
    )
    return 0                                                              # 0 == success for --test sweep aggregation
```

Method line count: 20 executable lines (well under the 25-line ceiling). Parameter
count: 5 (`self` plus 4 caller args) -- inside the 5-param ceiling. Nesting depth: 2
levels max. All three structural-discipline limits satisfied.
