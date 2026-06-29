# Phase 1 Quickstart: countSiteWanClients

**Feature**: 563-mist-count-site-wan-clients
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md) | **Data Model**: [data-model.md](./data-model.md)

This quickstart walks a developer through running, validating, and shipping the new
menu item locally on Windows 11. The container deployment pipeline is identical to
every other MistHelper feature and is documented in
`.github/copilot-instructions.md` (Full Deployment Pipeline section).

---

## 1. Prerequisites

- Python 3.13+ available as `python` on `PATH`.
- An activated MistHelper venv: `.venv\Scripts\Activate.ps1`.
- `mistapi` 0.59+ installed (already pinned in `requirements.txt`).
- A populated `.env` at the repository root.
- A known good Mist `site_id` you have read access to.
- `data\` directory exists and is writable (`chmod -R 777 data\` if running in
  container).

---

## 2. Required `.env` Variables

```ini
# Mist API session
MIST_HOST=manage.mist.com                   # or eu.mist.com / gc1.mist.com etc.
MIST_API_TOKEN=<your API token>             # never log this value

# Optional defaults to speed up prompts during dev
MIST_DEFAULT_SITE_ID=<UUID of a test site>

# Output backend selection (existing knob)
MIST_OUTPUT_BACKEND=sqlite                  # one of: csv | sqlite | arangodb

# Optional smoke-test variable used by --test sweep when present
MIST_TEST_SITE_ID=<UUID>                    # same as MIST_DEFAULT_SITE_ID is fine
```

No new environment variables are introduced by this feature. The two listed defaults
(`MIST_DEFAULT_SITE_ID`, `MIST_TEST_SITE_ID`) are existing conventions reused here.

---

## 3. Run the Menu Item Locally

### Interactive mode

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# Then type: 96
```

Expected prompt sequence (all answered through `safe_input()`):

```
[96] Site WAN Clients - Count by Distinct Attribute
site_id [<MIST_DEFAULT_SITE_ID>]: <press Enter to accept default>
distinct (e.g. mac, hostname, ip, port_id) []: mac
duration [1d]: 7d
start []: <Enter>
end []: <Enter>
limit [100]: <Enter>
```

### Direct (non-interactive) mode

```powershell
python MistHelper.py --menu 96
```

When `--menu 96` is supplied, prompts still apply but defaults are auto-accepted from
the environment when an empty answer is given (current behavior of the menu loop).

---

## 4. Expected Output

### Filesystem (CSV backend)

```
data\site_wan_clients_count_summary_<site_id>_<distinct>_<UTC_TS>.csv
data\site_wan_clients_count_buckets_<site_id>_<distinct>_<UTC_TS>.csv
```

### SQLite backend

```
data\mist_data.db
  +-- table site_wan_clients_count_summary   (1 row appended per invocation)
  `-- table site_wan_clients_count_buckets   (N rows appended per invocation)
```

DDL and primary keys are defined in [data-model.md](./data-model.md).

### Log lines (excerpt, ASCII only)

```
INFO  Counting WAN clients for site %s distinct=%s duration=%s
DEBUG WAN client count response: total=%d buckets=%d
INFO  Flattening %d buckets for export
DEBUG Flatten complete: summary_rows=1 bucket_rows=%d
INFO  Writing site_wan_clients_count_summary via DataExporter
INFO  Writing site_wan_clients_count_buckets via DataExporter
```

---

## 5. Implementation Sketch (for context only -- do NOT commit this verbatim)

The new method belongs on `SiteClientExportUtils` (or nearest existing site-clients
class). It MUST follow Constitution Principles I (5-Item Rule), VI (Inline Comments),
and VII (Action Logging) -- every executable line gets an inline comment, every
meaningful step gets a before / after log pair.

```python
def export_site_wan_clients_count(self, site_id, distinct, time_window):
    # Validate the site UUID before any network call so a typo exits cleanly.
    if not self._is_mist_uuid(site_id):                           # cheap shape check
        logging.warning("Invalid site_id %s -- aborting menu 96", site_id)  # warn, no PII
        return                                                    # early return
    # Log before the SDK call per Action Logging principle.
    logging.info(                                                 # INFO marker pre-call
        "Counting WAN clients for site %s distinct=%s duration=%s",
        site_id, distinct, time_window.get("duration"),
    )
    response = wan_clients_count.countSiteWanClients(             # the read-only SDK call
        self.apisession,                                          # injected session
        site_id=site_id,                                          # required path param
        distinct=distinct or None,                                # optional facet
        start=time_window.get("start"),                           # optional window start
        end=time_window.get("end"),                               # optional window end
        duration=time_window.get("duration", "1d"),               # API default mirrored
        limit=time_window.get("limit", 100),                      # API default mirrored
    )
    body = response.data or {}                                    # null-safe payload
    buckets = body.get("results", [])                             # buckets list
    logging.debug(                                                # DEBUG marker post-call
        "WAN client count response: total=%d buckets=%d",
        body.get("total", 0), len(buckets),
    )
    summary_row, bucket_rows = self._flatten_wan_client_count(    # private flattener
        site_id, body, time_window,                               # pass context for PK
    )
    self.exporter.write_with_format_selection(                    # summary table
        data=[summary_row], filename="site_wan_clients_count_summary",
        api_function_name="countSiteWanClients",                  # PK strategy lookup key
    )
    self.exporter.write_with_format_selection(                    # bucket table
        data=bucket_rows, filename="site_wan_clients_count_buckets",
        api_function_name="countSiteWanClients",
    )
```

All prompts feeding the three parameters use `safe_input()` with explicit `context=`
strings (`"site_wan_clients_count:site_id"`, etc.) so SSH and container EOFs exit 0
with no traceback.

---

## 6. Quality Gates (run before every commit)

```powershell
python -m py_compile MistHelper.py          # syntax check; silent on success
python -m ruff check MistHelper.py          # lint; must pass clean
python -m black --check MistHelper.py       # format check; rerun without --check to auto-fix
python MistHelper.py --test                 # full sweep; menu 96 is inside the safe range
```

All four must pass before `git commit`. The container build workflow re-runs the same
checks in CI and refuses to build on failure.

---

## 7. Negative-Path Smoke Tests

| Scenario | Input | Expected |
|---|---|---|
| Invalid `site_id` | `not-a-uuid` | `WARNING` log line, exit 0, no API call |
| Unknown `site_id` | well-formed UUID for a non-existent site | 404 logged as warning, exit 0 |
| Empty result set | a valid site with no WAN clients in the window | summary row written, zero bucket rows, "no data" notice on stdout |
| Rate-limit (429) | rapid repeated invocations | adaptive delay back-off kicks in via the existing `delay_metrics.json` machinery |
| SSH EOF mid-prompt | Ctrl-D / closed session | `safe_input()` returns exit 0, no traceback |

---

## 8. Where to Look If Something Breaks

- `data\agent_logs\*.json` -- structured logs for the most recent run.
- `delay_metrics.json` -- shows adaptive-delay state if you suspect rate limiting.
- `documentation\api\sites\GET_sites_site_id_wan_clients_count.md` -- authoritative
  endpoint contract.
- `.github\copilot-instructions.md` -- Database Strategy, Adding New Menu Operations,
  and Full Deployment Pipeline sections.
