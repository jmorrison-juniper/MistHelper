# Phase 1 Quickstart: countSiteRogueEvents (Menu 197)

End-to-end developer recipe for running the new menu item locally on a Windows 11 +
venv host or inside the production Podman container.

## Required .env variables

These keys must be present in `.env` (git-ignored) at the repo root:

```
MIST_HOST=api.mist.com                # or api.eu.mist.com / api.gc1.mist.com depending on cloud
MIST_API_TOKEN=<your-api-token>       # never logged; loaded by mistapi.APISession
MIST_ORG_ID=<org-uuid>                # used by the site picker helper, not by this endpoint directly
```

The endpoint itself only needs `site_id`. `org_id` is read once at startup by the
existing site picker so the user can pick the site from a list instead of pasting
a UUID.

## Expected data/ output filenames

CSV backend writes two files per invocation:

```
data/site_rogue_events_count_summary_<site_id>_<utc_timestamp>.csv
data/site_rogue_events_count_results_<site_id>_<utc_timestamp>.csv
```

SQLite backend (`data/mist_data.db`) writes to:

```
site_rogue_events_count_summary
site_rogue_events_count_results
```

ArangoDB + Redis backend writes to the same-named collections plus an edge
`site_to_rogue_event_count` from the site vertex to the summary vertex.

## Local invocation (Windows + venv)

```powershell
# Activate the project venv (standard environment)
.venv\Scripts\Activate.ps1

# Interactive run via the menu
python MistHelper.py
# (then select menu 197 from the Safe Site Reads category)

# Direct non-interactive run for automation
python MistHelper.py --menu 197
```

## Example prompt walk-through

```
> Select menu item: 197
[INFO] Loading sites for org 11111111-2222-3333-4444-555555555555
[Picker] Pick a site:
  1) HQ-Campus (aaaa1111-bbbb-2222-cccc-333333333333)
  2) Branch-EMEA (aaaa2222-bbbb-3333-cccc-444444444444)
Selection [1-2]: 1
Distinct attribute [type / ssid / bssid / ap_mac / channel / seen_on_lan] (default: type):
Duration (e.g. 1d, 7d, 2w) (default: 1d):
Advanced filters? (y/N): N
[INFO] Counting rogue events at site aaaa1111-bbbb-2222-cccc-333333333333 grouped by type
[DEBUG] Rogue event count returned total=59 results=3
[INFO] Flattening response into summary + results
[DEBUG] Flatten produced summary_rows=1 result_rows=3
[INFO] Writing site_rogue_events_count_summary and _results via DataExporter
[INFO] Wrote 1 row to site_rogue_events_count_summary
[INFO] Wrote 3 rows to site_rogue_events_count_results
[INFO] Menu 197 complete; exit code 0
```

## Container invocation (production parity)

```powershell
# Pull the latest image
podman pull ghcr.io/jmorrison-juniper/misthelper:latest

# Run interactively (mount data/ writable and .env read-only)
podman run --rm -it `
  -v "${PWD}\data:/app/data:rw" `
  -v "${PWD}\.env:/app/.env:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest --menu 197

# SSH into the running container (port 2200, ForceCommand launches MistHelper)
ssh -p 2200 misthelper@localhost
# (then select menu 197)
```

## Method outline (showing required comment + logging density)

The implementation must include an inline comment on every executable line and a
before/after log pair around every meaningful step, per Constitution VI and VII.
This outline shows the expected shape; the actual code lives on `RogueDataProcessor`
in `MistHelper.py`.

```python
def export_site_rogue_events_count(
    self,
    site_id: str,                                            # UUID of target site
    distinct: str = "type",                                  # Grouping attribute (API default)
    duration: str = "1d",                                    # Time window length
    extra_filters: dict | None = None,                       # Optional ssid/bssid/etc.
) -> int:
    """Count rogue events at a site, grouped by a distinct attribute."""
    # Validate site_id shape before any network call
    if not _MIST_UUID_RE.match(site_id):                     # Avoid burning a request on bad input
        logging.warning("Invalid site_id shape: %s", site_id)# Surface the problem; no traceback
        return 1                                             # Non-zero exit signals validation fail

    # Build the SDK kwargs from defaults + user-provided filters
    kwargs = {"distinct": distinct, "duration": duration}    # Start with the required pair
    if extra_filters:                                        # Only merge if user opted in
        kwargs.update(extra_filters)                         # Optional ssid/bssid/ap_mac/etc.

    # Action log: before the API call
    logging.info(                                            # ASCII INFO before the SDK call
        "Counting rogue events at site %s grouped by %s",
        site_id,
        distinct,
    )
    response = mistapi_count_site_rogue_events(              # Bound to mistapi SDK function
        self._mist_session,                                  # Existing APISession singleton
        site_id,
        **kwargs,                                            # Spread the optional filters
    )

    # Action log: after the API call with result summary
    payload = response.data or {}                            # Defensive default on empty body
    results = payload.get("results", [])                     # Per-distinct-value rows
    logging.debug(                                           # ASCII DEBUG after the SDK call
        "Rogue event count returned total=%d results=%d",
        payload.get("total", 0),
        len(results),
    )

    # Flatten into summary + results rows
    logging.info("Flattening response into summary + results")  # Before flatten
    summary_row, result_rows = self._flatten_count_response(    # Private helper on same class
        site_id, payload,
    )
    logging.debug(                                              # After flatten
        "Flatten produced summary_rows=%d result_rows=%d",
        1 if summary_row else 0,
        len(result_rows),
    )

    # Persist via the multi-backend exporter
    logging.info("Writing site_rogue_events_count_summary and _results via DataExporter")
    self._data_exporter.write_with_format_selection(            # Multi-backend route
        data=[summary_row],
        filename="site_rogue_events_count_summary",
        api_function_name="countSiteRogueEvents_summary",       # Selects the PK strategy entry
    )
    self._data_exporter.write_with_format_selection(
        data=result_rows,
        filename="site_rogue_events_count_results",
        api_function_name="countSiteRogueEvents_results",
    )
    return 0                                                    # Success
```

## Quality gates (must all pass before commit)

```powershell
# Syntax check (no output = valid)
python -m py_compile MistHelper.py

# Lint must pass clean
python -m ruff check MistHelper.py

# Format must already match Black (run without --check to auto-fix)
python -m black --check MistHelper.py

# Functional smoke test (uses .env credentials)
python MistHelper.py --menu 197
# Expect exit code 0 and two files under data/

# Full sweep (heavy/destructive skip list 14, 18, 63-65, 90-100 already applied; 197 is in scope)
python MistHelper.py --test
```

## Rollback

The change is additive (one new menu, two new SQLite tables, one new
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, README + CHANGELOG entries). Rollback is a
single `git revert` of the feature commit. The auto-created SQLite tables remain
harmless if left in place across a revert.
