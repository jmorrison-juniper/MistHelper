# Phase 1 Quickstart: countOrgBgpStats Menu Item

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) |
**Data Model**: [data-model.md](./data-model.md) |
**Contract**: [contracts/count_org_bgp_stats.md](./contracts/count_org_bgp_stats.md)

## Prerequisites

- Python 3.13+ with the repository virtualenv activated:
  `\.venv\Scripts\Activate.ps1`
- `mistapi` 0.59+ installed (covered by `requirements.txt` / `uv.lock`).
- `data/` directory exists and is writable (Podman runs require
  `chmod -R 777 data/` for the unprivileged container user).
- A valid Mist API token in `.env`.

## Required `.env` Variables

| Variable          | Required | Purpose                                                    |
|-------------------|----------|------------------------------------------------------------|
| `MIST_HOST`       | Yes      | Mist cloud host (e.g. `api.mist.com`, `api.eu.mist.com`).  |
| `MIST_API_TOKEN`  | Yes      | API token used by `mistapi.APISession`. Never logged.      |
| `MIST_ORG_ID`     | No       | Default for the first prompt; bypassed if the user types a different UUID. |

## How to Run This Menu Item Locally

Direct (non-interactive, single operation):

```powershell
.\.venv\Scripts\Activate.ps1                                       # Activate Python venv
python MistHelper.py --menu 96                                     # Run only menu item 96
```

Interactive (full menu):

```powershell
.\.venv\Scripts\Activate.ps1                                       # Activate Python venv
python MistHelper.py                                               # Launch menu loop
# at the prompt, type: 96
```

Containerized (Podman):

```powershell
podman exec -it misthelper python MistHelper.py --menu 96          # Run inside running container
```

## Example Invocation With Prompts

```text
$ python MistHelper.py --menu 96
[INFO] Counting org BGP stats
Org ID (UUID) [203d3d02-dbc0-4c1b-9f8a-f1e2c3a4b5d6]:              # press Enter to accept .env default
BGP state filter (blank = all):                                     # press Enter to skip filter
Distinct attribute (default: vrf_name): vrf_name                    # press Enter to accept
Limit (default: 100): 100                                           # press Enter to accept
[INFO] Counting org BGP stats org=203d... state= distinct=vrf_name
[DEBUG] BGP count: total=12 buckets=3
[INFO] Flattening 3 buckets into row representation
[DEBUG] Flatten produced 3 bucket rows + 1 summary row
[INFO] Writing org_bgp_stats_count_203d...-vrf_name.csv via DataExporter
[INFO] Wrote data/org_bgp_stats_count_203d3d02_vrf_name.csv (3 rows)
[INFO] Upserted 3 rows into org_bgp_stats_count (composite_pk)
[INFO] Upserted 1 row into org_bgp_stats_count_runs (composite_pk)
[INFO] Menu 96 complete
```

## Expected `data/` Output

- `data/org_bgp_stats_count_<org_id>_<distinct>.csv` -- one CSV per
  `(org_id, distinct)` slice. Re-running with the same slice overwrites the file.
- `data/mist_data.db` -- SQLite database with two tables populated by upsert:
  - `org_bgp_stats_count_runs` -- one row per `(org_id, distinct_field, state_filter)` tuple.
  - `org_bgp_stats_count` -- one row per `(org_id, distinct_field, distinct_value, state_filter)` bucket.
- ArangoDB+Redis (when the polyglot backend is active) receives the same data
  shaped per the existing `DataExporter.write_with_format_selection` pipeline --
  no special handling required from this menu item.

## Method Outline (Implementation Reference)

The new method lives on the existing `StatsExportUtils` class in `MistHelper.py`.
Every executable line carries an inline comment per Constitution VI; action
logging surrounds every meaningful step per Constitution VII.

```python
def export_org_bgp_stats_count(                                   # New menu 96 entry point
    self,
    org_id: str | None = None,                                    # Optional CLI/.env override
    state: str | None = None,                                     # Optional state filter
    distinct: str = "vrf_name",                                   # Default grouping axis
    limit: int = 100,                                             # Default page cap
) -> int:                                                         # Returns rows written
    org_id = org_id or safe_input(                                # Prompt only if not supplied
        f"Org ID (UUID) [{os.getenv('MIST_ORG_ID', '')}]: ",      # Show .env default in brackets
        context="org_bgp_count:org_id",                           # EOF-safe context tag
    ) or os.getenv("MIST_ORG_ID", "")                             # Fall back to env var on blank
    state = state if state is not None else safe_input(           # Prompt for optional state filter
        "BGP state filter (blank = all): ",                       # Free-text prompt
        context="org_bgp_count:state",                            # EOF-safe context tag
    )
    distinct = distinct or safe_input(                            # Prompt for distinct axis
        "Distinct attribute (default: vrf_name): ",               # Show default in label
        context="org_bgp_count:distinct",                         # EOF-safe context tag
    ) or "vrf_name"                                               # Hard default on blank
    logging.info(                                                 # Action log BEFORE API call
        "Counting org BGP stats org=%s state=%s distinct=%s",     # ASCII-only format string
        org_id, state or "", distinct,                            # Never logs the API token
    )
    response = countOrgBgpStats(                                  # mistapi SDK call
        self.apisession, org_id,                                  # Required path param
        distinct=distinct, state=state or None, limit=limit,      # Optional query params
    )
    payload = response.data                                       # SDK envelope -> JSON body
    logging.debug(                                                # Action log AFTER API call
        "BGP count: total=%d buckets=%d",                         # ASCII format string
        payload.get("total", 0), len(payload.get("results", [])), # Summary counts only
    )
    rows = self._flatten_bgp_count(payload, org_id, distinct,     # Build bucket + summary rows
                                   state or "")                   # Pass normalized state filter
    DataExporter.write_with_format_selection(                     # Multi-backend write
        rows, f"org_bgp_stats_count_{org_id}_{distinct}.csv",     # Filename embeds slice
        api_function_name="countOrgBgpStats",                     # Drives PK strategy lookup
    )
    return len(rows)                                              # Caller logs final summary
```

## Quality Gates (Run Before Every Commit)

Each command must exit 0. Inline comments document why every gate is required.

```powershell
.\.venv\Scripts\Activate.ps1                                       # Activate Python venv
python -m py_compile MistHelper.py                                 # Syntax must compile cleanly
python -m ruff check MistHelper.py                                 # Lint must pass with no findings
python -m black --check MistHelper.py                              # Formatting must be canonical
python MistHelper.py --test                                        # Test sweep must include menu 96
```

If `python -m black --check` reports differences, run `python -m black
MistHelper.py` to auto-fix and re-run the check.

## Deployment Pipeline (After Quality Gates Pass)

```powershell
git add MistHelper.py README.md CHANGELOG.md specs\510-mist-count-org-bgp-stats # Stage related files
git commit -m "version YY.MM.DD.HH.MM - add menu 96 countOrgBgpStats"           # UTC timestamp version
git push origin main                                                            # Triggers CI + container build
gh run watch                                                                    # Wait for container-build.yml
podman pull ghcr.io/jmorrison-juniper/misthelper:latest                         # Pull new image
podman stop misthelper ; podman rm misthelper                                   # Replace running container
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `                     # Restart with same mounts
    -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest
podman ps                                                                       # Verify container is up
```
