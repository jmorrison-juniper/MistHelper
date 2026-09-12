# Phase 1 Quickstart: countSiteZoneSessions (Menu 195)

**Feature**: 570-mist-count-site-zone-sessions
**Date**: 2026-06-29

This quickstart describes how to run the new menu item locally on Windows 11 with a
venv, what `.env` variables are required, what file lands in `data/`, what the
interactive prompt sequence looks like, and which quality gates must pass before
committing.

## Prerequisites

- Python 3.13+ installed and on PATH.
- A populated venv at the repo root: `.venv\Scripts\Activate.ps1`.
- `mistapi` 0.59+ available in the venv (`pip install -r requirements.txt`).
- A `.env` file at the repo root containing valid Mist credentials.

## Required `.env` Variables

```dotenv
# Mist API credentials -- never logged, never committed.
MIST_HOST=api.mist.com                 # Or api.eu.mist.com / api.gc1.mist.com per region.
MIST_API_TOKEN=<redacted_token_value>  # Token with read access to the target org / site.

# Optional defaults used by the prompt fall-through.
MIST_ORG_ID=<org_uuid>                 # Used by adjacent org-scoped menus; not required here.
MIST_SITE_ID=<site_uuid>               # Used by this menu when the operator presses Enter on the site_id prompt.
```

If `MIST_SITE_ID` is unset and the operator presses Enter, the menu logs a warning and
exits cleanly (FR-002, Acceptance Scenario 2). No traceback, no partial write.

## Expected `data/` Output

| Backend                | Artifact                                                          |
|------------------------|-------------------------------------------------------------------|
| CSV (default)          | `data/SiteZoneSessionCounts.csv` -- one row per distinct value    |
| SQLite                 | `data/mist_data.db` table `site_zone_session_counts` (DDL in `data-model.md`) |
| ArangoDB + Redis       | Collection `site_zone_session_counts` upserted by composite key   |

All three backends are wired through one call to
`DataExporter.write_with_format_selection(rows, "SiteZoneSessionCounts.csv", api_function_name="countSiteZoneSessions")`.

## Interactive Invocation

```powershell
# Activate venv.
.venv\Scripts\Activate.ps1

# Launch MistHelper menu and pick 195.
python MistHelper.py
# At the menu prompt:
#   Selection: 195

# Prompt sequence (all wrapped in safe_input()):
#   Enter site_id (blank = MIST_SITE_ID from .env): <paste site uuid or press Enter>
#   Enter zone_type [zones|rssizones] (default zones): <Enter for zones>
#   Enter distinct attribute (default zone_id): <Enter for zone_id>
#   Enter duration (default 1d): <Enter for 1d>
#   Enter limit (default 100): <Enter for 100>

# Expected stdout (truncated):
#   INFO  Counting zone sessions for site <site_id> zone_type=zones distinct=zone_id
#   DEBUG Zone session count response: total=14 returned=14
#   INFO  Flattening 14 count_result rows
#   DEBUG Flattened 14 rows for SiteZoneSessionCounts.csv
#   INFO  Writing 14 rows via DataExporter
#   DEBUG DataExporter wrote 14 rows to data/SiteZoneSessionCounts.csv
```

## Non-Interactive Invocation (used by `--test` and CI)

```powershell
python MistHelper.py --menu 195
```

`--menu 195` skips the menu prompt and runs the dispatch directly; the per-prompt
defaults are taken from `.env` (`MIST_SITE_ID`) and the SDK / endpoint defaults
(`zone_type=zones`, `distinct=zone_id`, `duration=1d`, `limit=100`).

## Method Outline (target: ~22 lines on `SiteExportUtils`)

```python
def count_site_zone_sessions(                                                # New public method on SiteExportUtils.
    self,                                                                    # Instance owns api session and exporter.
    site_id: str | None = None,                                              # Optional override; .env fallback used when None.
    zone_type: str = "zones",                                                # zones or rssizones; validated below.
    distinct: str = "zone_id",                                               # Grouping attribute echoed in response.
    duration: str = "1d",                                                    # Time window per Mist API grammar.
    limit: int = 100,                                                        # Server-side row cap.
) -> int:                                                                    # Returns rows written for --test asserts.
    """Menu 195: count site zone sessions by distinct attribute."""           # Catalogue description.
    site_id = site_id or safe_input(                                         # Prompt if not supplied programmatically.
        "Enter site_id (blank = MIST_SITE_ID from .env): ",                  # Operator-friendly prompt text.
        context="count_site_zone_sessions:site_id",                          # Context used for EOF logging.
    ) or os.environ.get("MIST_SITE_ID", "")                                  # Fall back to .env on empty input.
    if zone_type not in {"zones", "rssizones"}:                              # Enum validation per Constitution III.
        logging.warning("Invalid zone_type %s; aborting", zone_type)         # ASCII log, no traceback.
        return 0                                                             # Safe early return.
    logging.info(                                                            # Action log before API call (Principle VII).
        "Counting zone sessions for site %s zone_type=%s distinct=%s",
        site_id, zone_type, distinct,
    )
    response = mistapi.api.v1.sites.count.countSiteZoneSessions(             # Single SDK call.
        self.apisession, site_id, zone_type,                                 # Required path params.
        distinct=distinct, duration=duration, limit=limit,                   # Optional query params.
    )
    payload = response.data or {}                                            # Normalize None to empty dict.
    logging.debug(                                                           # Action log after API call.
        "Zone session count response: total=%d returned=%d",
        payload.get("total", 0), len(payload.get("results", [])),
    )
    rows = self._flatten_count_results(site_id, zone_type, payload)          # Helper produces one row per distinct value.
    return self.data_exporter.write_with_format_selection(                   # Multi-backend write (FR-004).
        rows, "SiteZoneSessionCounts.csv",                                   # Canonical CSV filename.
        api_function_name="countSiteZoneSessions",                           # Drives PK strategy lookup.
    )
```

The private `_flatten_count_results(site_id, zone_type, payload)` helper iterates
`payload["results"]`, pulls the `count` field and the dynamic distinct-attribute value,
and emits one dict per row with the columns enumerated in `data-model.md`.

## Quality Gates (run before every commit)

```powershell
# Activate venv first.
.venv\Scripts\Activate.ps1

# Hard gates -- all three must exit 0 before committing.
python -m py_compile MistHelper.py        # Syntax check (no output = valid).
python -m ruff check MistHelper.py        # Lint must be clean.
python -m black --check MistHelper.py     # Format must be clean (drop --check to auto-fix).

# Functional smoke -- requires .env credentials.
python MistHelper.py --menu 195           # Should exit 0 and write data/SiteZoneSessionCounts.csv.

# Full sweep -- skips heavy/destructive defaults; menu 195 is included.
python MistHelper.py --test
```

Only after all four commands report success may the operator proceed to the standard
deployment pipeline (`git add` / `git commit` / `git push` / `gh run watch` /
`podman pull` / restart).
