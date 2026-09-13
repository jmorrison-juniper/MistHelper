# Phase 1 Quickstart: countSiteWirelessClientEvents Menu Item

**Feature**: 567-mist-count-site-wireless-client-events
**Proposed menu number**: 78 (subject to re-verification at `/speckit.tasks`)
**operationId**: `countSiteWirelessClientEvents`

---

## Prerequisites

- Python 3.13+
- A populated `.env` at the repo root (or mounted into the container) with:

```ini
MIST_HOST=api.mist.com               # or your regional endpoint (api.eu.mist.com, etc.)
MIST_API_TOKEN=<your-mist-api-token> # never commit this file
MIST_DEFAULT_SITE_ID=<optional UUID> # offered as default for the site_id prompt
MIST_PAGE_LIMIT=1000                 # optional, overrides DEFAULT_API_PAGE_LIMIT
```

- For local dev: `.venv\Scripts\Activate.ps1` (Windows) and `pip install -r
  requirements.txt` (or `uv sync` if using UV).
- For the container path: `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`.

---

## Running the menu item locally

### Interactive mode

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the menu prompt, select 78 (countSiteWirelessClientEvents).
```

### Direct invocation

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --menu 78
```

### Containerized via SSH on port 2200

```powershell
ssh -p 2200 misthelper@localhost
# ForceCommand launches MistHelper directly. Select 78.
```

---

## Prompts you will see

The menu collects these inputs via `safe_input()`. Press Enter on any optional prompt
to accept the default (or skip the argument when the default is "blank").

1. `Site ID [<MIST_DEFAULT_SITE_ID or blank>]:`
2. `Distinct attribute (type|ssid|ap|band|proto|wlan_id|reason_code) [type]:`
3. `Filter: event type (blank = all):`
4. `Filter: reason_code (blank = all):`
5. `Filter: ssid (blank = all):`
6. `Filter: ap MAC (blank = all):`
7. `Filter: proto (a|b|g|n|ac|ax, blank = all):`
8. `Filter: band (2.4|5|6, blank = all):`
9. `Filter: wlan_id (blank = all):`
10. `Window start (epoch seconds or relative like -1d, blank = use duration):`
11. `Window end (epoch seconds or relative like now, blank = use duration):`
12. `Duration [1d]:`
13. `Limit per page [100]:`

EOF on any prompt (SSH disconnect, container shutdown) exits the operation cleanly
with code 0.

---

## Expected `data/` output

After a successful run you will see (or, on subsequent runs, upserts of) these files
under `data/`:

- `data/site_wireless_client_events_count_summary.csv` (one row per query)
- `data/site_wireless_client_events_count_results.csv` (one row per bucket)
- `data/mist_data.db` -- the SQLite database -- now contains the two tables
  `site_wireless_client_events_count_summary` and
  `site_wireless_client_events_count_results` (created on first run by
  `DataExporter.write_with_format_selection`).
- `data/script.log` -- structured action log including the INFO line "Fetching
  wireless client event count for site %s distinct=%s" and the matching DEBUG line
  with bucket counts.

If the ArangoDB+Redis backend is configured, the same rows land in the equivalent
collections.

---

## Example invocation

```text
Select operation: 78
Site ID [aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee]: <enter>
Distinct attribute [type]: ssid
Filter: event type (blank = all): <enter>
Filter: reason_code (blank = all): <enter>
Filter: ssid (blank = all): <enter>
Filter: ap MAC (blank = all): <enter>
Filter: proto (blank = all): <enter>
Filter: band (blank = all): <enter>
Filter: wlan_id (blank = all): <enter>
Window start (blank = use duration): <enter>
Window end (blank = use duration): <enter>
Duration [1d]: 7d
Limit per page [100]: <enter>

[INFO] Fetching wireless client event count for site aaaaaaaa-... distinct=ssid
[DEBUG] count_results: total=42137 buckets=12
[INFO] Flattening 12 bucket(s) into results table
[DEBUG] Wrote 1 summary row + 12 result rows
[INFO] Export complete -- see data/site_wireless_client_events_count_*.csv
```

Re-running the same prompts immediately is safe: the composite primary key upserts
in place; no duplicates appear in SQLite, the CSV is rewritten, and the ArangoDB
documents are replaced by `_key`.

---

## Quality gates

All four must pass before commit. Run them in this order:

```powershell
# Syntax check -- no output on success
python -m py_compile MistHelper.py

# Lint -- must report zero violations
python -m ruff check MistHelper.py

# Format -- must report zero diffs
python -m black --check MistHelper.py

# Smoke test -- skip list (14, 18, 63-65, 90-100) is unaffected; menu 78 is in scope
python MistHelper.py --test
```

If `ruff check` or `black --check` reports issues, run `python -m ruff check --fix
MistHelper.py` and `python -m black MistHelper.py` respectively, then re-verify.

---

## Method outline (informative, not implementation)

Pseudocode showing the inline-comment density and action-logging pairs the
implementation must follow. Every executable line carries a comment; every action is
bracketed by INFO/DEBUG.

```python
def export_site_wireless_client_events_count(
    self,                                                              # class instance
    site_id: str,                                                      # site under inspection
    distinct: str,                                                     # grouping attribute
    filters_dict: dict,                                                # optional event filters
    time_window_dict: dict,                                            # start/end/duration
) -> None:
    logging.info("Fetching wireless client event count for site %s distinct=%s",
                 site_id, distinct)                                    # INFO before API call
    if not self._is_valid_uuid(site_id):                               # validate before SDK
        logging.warning("Invalid site_id %s -- aborting", site_id)     # WARN on bad input
        return                                                         # early return on fail
    response = mistapi.api.v1.sites.clients.events.count.\
        countSiteWirelessClientEvents(                                 # the only SDK call
            self.api_session,                                          # APISession from .env
            site_id,                                                   # path param
            distinct=distinct,                                         # grouping attr
            **filters_dict,                                            # optional filters
            **time_window_dict,                                        # window kwargs
        )                                                              # returns dict envelope
    payload = response.data                                            # extract JSON body
    logging.debug("count_results: total=%d buckets=%d",                # DEBUG after API call
                  payload.get("total", 0),                             # safe default
                  len(payload.get("results", [])))                     # safe default
    summary_row = self._flatten_count_summary(site_id, payload,        # one row for envelope
                                              time_window_dict)        # carry user duration
    bucket_rows = self._flatten_count_results(site_id, payload)        # N rows for buckets
    logging.info("Flattening %d bucket(s) into results table",
                 len(bucket_rows))                                     # INFO before flatten
    DataExporter.write_with_format_selection(                          # multi-backend write
        {"summary": [summary_row], "results": bucket_rows},            # two-shape payload
        filename="site_wireless_client_events_count",                  # base filename
        api_function_name="countSiteWirelessClientEvents",             # PK-strategy lookup
    )                                                                  # DataExporter logs
    logging.debug("Wrote 1 summary row + %d result rows",
                  len(bucket_rows))                                    # DEBUG after write
```

This outline obeys the 5-Item Rule (24 executable lines including the signature, 5
parameters, 4 logical blocks: validate / SDK call / flatten / export) and every
NON-NEGOTIABLE principle from the Constitution.
