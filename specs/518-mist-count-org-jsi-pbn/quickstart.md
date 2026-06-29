# Phase 1 Quickstart: countOrgJsiPbn

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Data Model**: [data-model.md](./data-model.md)
**Date**: 2026-06-29

This quickstart describes how a developer runs, tests, and validates menu item
**78 -- countOrgJsiPbn** locally on Windows 11 + venv before pushing to the
container build pipeline.

## Prerequisites

- Python 3.13+ in an activated venv (`.venv\Scripts\Activate.ps1`).
- `pip install -r requirements.txt` (or `uv pip install -r requirements.txt`).
- `data/` directory present and writable (`chmod -R 777 data` inside Linux
  container; on Windows the directory is writable by the venv user by default).
- `.env` file in the repo root populated with the variables listed below.

## Required `.env` variables

```ini
MIST_HOST=api.mist.com                 # or api.eu.mist.com, api.gc1.mist.com, etc.
MIST_API_TOKEN=<personal_or_org_token> # never commit; .env is git-ignored
MIST_ORG_ID=<optional_default_org_uuid> # if set, the prompt offers it as default
```

## Expected output

| Backend        | Location                                    |
|----------------|---------------------------------------------|
| CSV (default)  | `data/org_jsi_pbn_count.csv`                |
| SQLite         | `data/mist_data.db` -> table `org_jsi_pbn_count` |
| ArangoDB       | collection `org_jsi_pbn_count`              |
| Redis cache    | key prefix `org_jsi_pbn_count:`             |

Row count: one row per group returned by the API (bounded by the `limit`
parameter, default 100). An empty `results` array produces zero output rows and a
log line: `WARNING -- countOrgJsiPbn returned no groups for org <uuid> distinct=<field>`.

## Run the menu item interactively

```powershell
# From the repo root with venv activated:
python MistHelper.py
# At the menu, type: 78
# Answer the prompts:
#   org_id [<default from .env>]: <press Enter to accept default>
#   distinct (1=versions, 2=models, 3=customer_risk, 4=bug_type): 1
#   limit [100]: <Enter for default>
#   start [empty]: -1w
#   end [empty]: now
```

Expected console summary:

```
INFO     Fetching JSI PBN count for org <uuid> grouped by versions
DEBUG    PBN count: distinct=versions total=42 results=7
INFO     Flattening 7 group(s) into org_jsi_pbn_count rows
DEBUG    Flatten complete: 7 row(s) ready for export
INFO     Writing org_jsi_pbn_count via DataExporter (backend=csv)
DEBUG    Wrote 7 row(s) to data/org_jsi_pbn_count.csv
```

## Run the menu item non-interactively

```powershell
python MistHelper.py --menu 78 --org <uuid> --distinct versions --start -1w --end now
```

(The exact non-interactive flag names follow the existing
`--menu <N>` dispatch pattern in MistHelper.py; if the dispatcher does not yet
support `--distinct`, the implementation PR extends it in the same change set.)

## Quality gates (run before every commit)

```powershell
# Syntax check (no output == valid).
python -m py_compile MistHelper.py

# Lint (must pass clean).
python -m ruff check MistHelper.py

# Format check (run without --check to auto-fix).
python -m black --check MistHelper.py

# Functional test sweep (op 78 is inside the default range).
python MistHelper.py --test
```

All four must pass green before commit. The container-build workflow
(`.github/workflows/container-build.yml`) re-runs the first three on GitHub
infrastructure; a clean local run does not guarantee a clean CI run if line
endings or path separators differ, so always confirm the GitHub Actions result
with `gh run watch <run-id>` before pulling the new image.

## Method outline (for reviewers)

The new method on `InsightsExportUtils` follows this shape (~22 lines, <=4
parameters, <=5 logical blocks -- satisfies the 5-Item Rule):

```python
def export_org_jsi_pbn_count(                               # menu 78 entrypoint
    self,                                                   # bound class instance
    org_id: str,                                            # required Mist org UUID
    distinct: str,                                          # required grouping enum
    time_window: Optional[Tuple[str, str]] = None,          # optional (start, end)
) -> None:                                                  # void; persistence side-effect only
    logging.info("Fetching JSI PBN count for org %s grouped by %s",  # action log: before API
                 org_id, distinct)                          # ascii-safe %s formatting
    response = countOrgJsiPbn(                              # SDK call; only permitted transport
        self.apisession,                                    # token-bearing mistapi session
        org_id,                                             # path param
        distinct=distinct,                                  # required query param
        limit=self._limit_or_default(time_window),          # optional clamp
        start=time_window[0] if time_window else None,      # optional window start
        end=time_window[1] if time_window else None,        # optional window end
    )                                                       # APIResponse object
    body = response.data or {}                              # parsed JSON body, safe default
    results = body.get("results", [])                       # group list
    logging.debug("PBN count: distinct=%s total=%d results=%d",  # action log: after API
                  distinct, body.get("total", 0), len(results))   # summary counts only
    rows = self._flatten_pbn_count_rows(org_id, body)       # build PbnCountRow list
    DataExporter.write_with_format_selection(               # multi-backend dispatcher
        rows,                                               # flattened payload
        filename="org_jsi_pbn_count",                       # stem only; backend adds extension
        api_function_name="countOrgJsiPbn",                 # lookup key for PK strategy
    )                                                       # writes csv / sqlite / arango+redis
```

Every executable line carries an inline comment (Constitution VI). Action logging
brackets every meaningful step (Constitution VII). Inputs flow through
`safe_input()` in the menu-dispatch layer (not shown above; the same pattern as
the surrounding insight exports).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `PermissionError: [Errno 13] ... /app/data/script.log` | Container `data/` not writable | `chmod -R 777 data/` before container start |
| 401 from API | Stale or wrong `MIST_API_TOKEN` | Refresh token in `.env` and restart |
| 403 | Token lacks JSI / insights scope on the org | Use an org-admin token |
| 404 | Wrong `org_id` or org has no JSI subscription | Verify org UUID; check JSI entitlement |
| 429 | Rate limited | Adaptive delay kicks in automatically; re-run later |
| Empty CSV | API returned `results: []` for the window | Widen `start` / `end`; try a different `distinct` |
| ImportError on `countOrgJsiPbn` | mistapi <0.59 installed | `pip install --upgrade mistapi` |
