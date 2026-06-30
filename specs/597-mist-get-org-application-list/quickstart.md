# Phase 1 Quickstart: getOrgApplicationList (Menu 58)

Branch: `597-mist-get-org-application-list`
Date: 2026-06-29
Endpoint: `GET /api/v1/orgs/{org_id}/wxtags/apps`
Proposed menu number: **58** (Misc Safe Org Exports band 56-59)

## Goal

Run the new menu item end-to-end on a developer workstation and confirm a clean output
file lands under `data/`.

## Prerequisites

- Python 3.13 or newer with the repo's `.venv` activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Dependencies installed (`pip install -r requirements.txt` or `uv sync`). `mistapi`
  must be 0.59 or newer.
- A populated `.env` at the repo root.

## Required `.env` Variables

| Variable         | Purpose                                                                | Required for this menu item                |
|------------------|------------------------------------------------------------------------|--------------------------------------------|
| `MIST_HOST`      | Mist Cloud regional host (e.g. `api.mist.com`, `api.eu.mist.com`).     | Yes -- consumed by `mistapi.APISession`.   |
| `MIST_API_TOKEN` | API token with read access to the target org.                          | Yes -- consumed by `mistapi.APISession`.   |
| `MIST_ORG_ID`    | Default org UUID. Used when the interactive prompt is left empty and required for `--test`. | Yes (for non-interactive runs).            |
| `OUTPUT_BACKEND` | Optional. `csv`, `sqlite`, or `arangodb`. Defaults to MistHelper's configured backend. | No -- defaults are honoured.               |

## Expected Output

| Backend  | Artifact                                                                              |
|----------|---------------------------------------------------------------------------------------|
| CSV      | `data/org_wxtag_applications_<org_id>_<YYYYMMDD_HHMMSS>.csv` with header row.         |
| SQLite   | Table `org_wxtag_applications` in `data/mist_data.db`, upserted by composite PK.      |
| ArangoDB | Vertex collection `org_wxtag_applications`, document `_key = <org_id>__<group>__<key>`. |

## Run It Interactively

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --menu 58
```

Expected interaction:

```
Org UUID [default from .env MIST_ORG_ID]: <press Enter to accept default, or paste a UUID>
INFO: Fetching WxTag application catalog for org 11111111-2222-3333-4444-555555555555
DEBUG: Received 187 application signatures from Mist API
INFO: Writing 187 rows to data/org_wxtag_applications_<org_id>_<ts>.csv
DEBUG: DataExporter wrote backend=csv rows=187
```

A successful run exits with status 0 and prints the resolved output path.

## Run It Non-Interactively (CI / `--test`)

```powershell
python MistHelper.py --test
```

`--test` walks the default test sweep (skipping 14, 18, 63-65, 90-100). Menu 58 falls
inside the sweep and uses `MIST_ORG_ID` from `.env` for the prompt. A failure surfaces
as a non-zero exit code with a logged traceback context.

## Implementation Sketch

The new method lives on a configuration-adjacent export class in `MistHelper.py`
(e.g. `ConfigExportUtils` -- exact binding confirmed at `/speckit.tasks` time):

```python
def export_org_application_list(self, org_id: str | None = None) -> None:
    # 1. Resolve org_id: prompt first, .env fallback, validate UUID shape.
    org_id = self._resolve_org_id(org_id, prompt_context="org_application_list:org_id")
    if not org_id:                                              # Validation failed
        logging.warning("Skipping menu 58: no valid org_id supplied.")
        return                                                  # Clean exit, no traceback

    # 2. Action log before the API call (Principle VII).
    logging.info("Fetching WxTag application catalog for org %s", org_id)

    # 3. SDK call (Principle II: through mistapi only).
    response = mistapi.api.v1.orgs.wxtags.getOrgApplicationList(self.apisession, org_id)
    applications = response.data or []                          # Defensive: treat None as empty

    # 4. Action log after the API call.
    logging.debug("Received %d application signatures from Mist API", len(applications))

    # 5. Enrich each row with org_id so the composite PK is complete.
    enriched = [{"org_id": org_id, **app} for app in applications]

    # 6. Multi-backend write (Principle IV).
    DataExporter.write_with_format_selection(
        enriched,
        filename=f"org_wxtag_applications_{org_id}",
        api_function_name="getOrgApplicationList",
    )
```

Inline comments must remain on every executable line in the real implementation; the
sketch above is illustrative density.

## Local Quality Gates

Run all three before every commit. Each must pass clean:

```powershell
python -m py_compile MistHelper.py     # Syntax check: no output on success
python -m ruff check MistHelper.py     # Lint check: zero violations
python -m black --check MistHelper.py  # Format check: drop --check to auto-fix
```

Then run the unit / smoke sweep:

```powershell
python MistHelper.py --test            # Exits 0 if the menu sweep passes
```

## Troubleshooting

| Symptom                                                | Likely Cause                                                    | Fix                                                                                       |
|--------------------------------------------------------|-----------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `PermissionError: [Errno 13] ... data/script.log`      | Container `data/` mount not writable.                            | `chmod -R 777 data/` before launching the Podman container (see copilot-instructions.md). |
| 401 from Mist on a known-good token                    | Wrong `MIST_HOST` for the token's region.                        | Re-read `.env`; common regions: `api.mist.com`, `api.eu.mist.com`, `api.gc1.mist.com`.    |
| 404 from Mist                                          | `org_id` typo or token lacks access to the org.                  | Re-prompt with the correct UUID; verify token permissions in the Mist UI.                 |
| Repeated 429s                                          | Other tooling burning the 5000/hr budget.                        | Let the adaptive delay system back off; consider `--fast` only after the burst clears.    |
| Empty CSV / "no data returned"                          | Org has no application catalog overrides (rare).                 | Verify in another tool; if confirmed empty, no action -- the menu logs and exits cleanly. |
| Duplicate rows in SQLite after re-run                  | `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry missing or mis-keyed.    | Confirm the registered PK matches `['org_id', 'group', 'key']`; re-run.                   |
