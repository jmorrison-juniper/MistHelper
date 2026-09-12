# Phase 1 Quickstart: getOrgUiSetting (Menu 58)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-07-01

This quickstart is a developer smoke test for the new menu item. It assumes the
implementation has landed on the feature branch and the standard MistHelper dev loop
is set up.

## Required `.env` Variables

| Variable                | Purpose                                              | Required |
|-------------------------|------------------------------------------------------|----------|
| `MIST_HOST`             | Mist Cloud region host (e.g. `api.mist.com`).        | Yes      |
| `MIST_API_TOKEN`        | Long-lived API token. Never logged.                  | Yes      |
| `MIST_DEFAULT_ORG_ID`   | Default org UUID for the `org_id` prompt.            | Optional |
| `MIST_DEFAULT_UISETTING_ID` | Default databoard UUID for automated testing.    | Optional |

The last variable is used only by `python MistHelper.py --test` to keep the menu-item
run non-interactive; in normal use the prompt is answered manually.

## Local Run (Interactive)

```powershell
# From the feature-branch worktree:
cd "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging"

# Activate the venv (standard MistHelper dev environment):
.venv\Scripts\Activate.ps1

# Launch MistHelper interactively:
python MistHelper.py

# Then at the top-level menu, select 58 ("Export Org UI Setting (single databoard)")
# When prompted:
#   org_id      -> paste the org UUID (or press Enter to accept the .env default)
#   uisetting_id -> paste the databoard UUID
```

## Local Run (Direct Invocation)

```powershell
# Non-interactive dispatch bypasses the top-level menu. Prompts still fire, so pipe
# answers on stdin or rely on .env defaults:
python MistHelper.py --menu 58
```

## Expected `data/` Output

After a successful run, two artefacts appear under `data/` (backend-dependent):

- CSV backend:
  - `data/org_ui_setting_<orgshort>_<uishort>.csv` -- one row (databoard summary).
  - `data/org_ui_setting_<orgshort>_<uishort>_tiles.csv` -- N rows (one per tile).
- SQLite backend:
  - `data/mist_data.db` contains upserted rows in tables `org_ui_setting` and
    `org_ui_setting_tiles`.
- ArangoDB + Redis backend:
  - Documents in `org_ui_setting` and `org_ui_setting_tiles` collections; a
    `has_tile` edge per tile; Redis key `mist:uisetting:<uisetting_id>` populated.

## Method Skeleton (target for implementation)

The following outline is the shape the tasks phase will drive to. Comment density and
logging density are illustrative -- the real implementation obeys Constitution VI and
VII on every executable line.

```python
class ConfigExportUtils:
    def export_org_ui_setting(self, org_id=None, uisetting_id=None):
        # Prompt for org_id when not provided by --menu direct invocation
        org_id = org_id or safe_input(
            "Enter org_id: ", context="org_ui_setting:org_id"
        )  # SSH/container-safe prompt with EOF handling
        # Prompt for uisetting_id
        uisetting_id = uisetting_id or safe_input(
            "Enter uisetting_id: ", context="org_ui_setting:uisetting_id"
        )  # Second required path parameter
        # Validate both UUIDs before spending an API call
        if not is_valid_uuid(org_id) or not is_valid_uuid(uisetting_id):
            logging.warning("Invalid UUID input; aborting getOrgUiSetting")
            return  # Fail fast without a Mist API round-trip
        # INFO before API call (Action Logging principle)
        logging.info("Fetching UI setting %s for org %s", uisetting_id, org_id)
        # SDK call -- see contracts/get_org_ui_setting.md for the exact signature
        response = mistapi.api.v1.orgs.ui_settings.getOrgUiSetting(
            self.apisession, org_id, uisetting_id
        )
        # Extract payload -- single JSON object
        databoard = response.data or {}
        tiles = databoard.get("tiles", []) or []
        # DEBUG after API call with count summary
        logging.debug(
            "UI setting: name=%s purpose=%s tiles=%d",
            databoard.get("name"), databoard.get("purpose"), len(tiles),
        )
        # Flatten summary into a single row (drop the tiles list from the dict)
        summary_row = {k: v for k, v in databoard.items() if k != "tiles"}
        # Flatten each tile: promote nested position.* into flat position_col/row/span
        tile_rows = [self._flatten_ui_tile(t, uisetting_id) for t in tiles]
        # Persist summary via multi-backend exporter
        DataExporter.write_with_format_selection(
            [summary_row],
            f"org_ui_setting_{org_id[:8]}_{uisetting_id[:8]}",
            api_function_name="getOrgUiSetting",
        )
        # Persist tiles via same exporter under a distinct api_function_name suffix
        DataExporter.write_with_format_selection(
            tile_rows,
            f"org_ui_setting_{org_id[:8]}_{uisetting_id[:8]}_tiles",
            api_function_name="getOrgUiSetting__tiles",
        )
```

## Quality Gates (must all pass before commit)

Run each of the following in the venv-activated worktree; each command must return
zero output (or an explicit success message) with exit code 0:

```powershell
python -m py_compile MistHelper.py         # Byte-compile / syntax check
python -m ruff check MistHelper.py         # Lint (per repo config)
python -m black --check MistHelper.py      # Formatting (per repo config)
python MistHelper.py --test                # Non-interactive sweep incl. menu 58
```

The `--test` sweep skips 14, 18, 63-65, 90-100 by default; menu 58 sits inside the
default range and must succeed on the reference org configured in `.env`. Failure of
any gate is a blocker per Constitution IV (Full Deployment Pipeline, NON-NEGOTIABLE).
