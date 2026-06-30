# Phase 1 Quickstart: getOrgMxEdgeUpgrade

This quickstart shows how to run the new MistHelper menu item locally,
which environment variables it needs, what files appear under `data/`, and
which quality gates must pass before commit.

The target menu number is **96** (subject to re-verification at task
generation). All commands assume Windows 11 + PowerShell with the project
venv activated.

---

## 1. Prerequisites

- Python 3.13+ installed and on PATH.
- The project venv created and activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- `mistapi` 0.59+ and the rest of the project's pinned dependencies
  installed via UV or pip:
  ```powershell
  uv pip install -r requirements.txt
  ```
- A valid `.env` at the repository root with the variables below.

---

## 2. Required `.env` variables

| Variable             | Required | Purpose                                                |
|----------------------|----------|--------------------------------------------------------|
| `MIST_HOST`          | yes      | Mist API cloud host (e.g. `api.mist.com`).             |
| `MIST_API_TOKEN`     | yes      | API token with read access to the target org.          |
| `MIST_DEFAULT_ORG_ID`| no       | Pre-fills the org_id prompt. Falls back to manual entry. |

The API token is never logged. The new menu method only reads, never
writes, these values.

---

## 3. Inputs collected at run time

The menu method prompts for exactly two values, both via `safe_input()`:

1. `org_id` -- a Mist organization UUID. Defaults to
   `MIST_DEFAULT_ORG_ID` if set in `.env`.
2. `upgrade_id` -- the UUID of the specific Mist Edge upgrade job to
   inspect. No default; per-run value.

Both inputs are validated against the Mist UUID shape (regex) before any
SDK call. On EOF (SSH/container session closed) the method exits cleanly
with code 0 and no traceback.

---

## 4. Running the menu item

### Interactive mode

```powershell
python MistHelper.py
```

Then at the menu prompt enter `96` and supply the two UUIDs when asked.

### Direct (scripted) invocation

```powershell
python MistHelper.py --menu 96
```

The `--menu` shortcut still runs the `safe_input()` prompts; pipe the
values in via stdin for fully non-interactive runs.

### Full test sweep

```powershell
python MistHelper.py --test
```

Menu 96 is inside the default sweep range (the documented skip list is
`14, 18, 63-65, 90-100`, so 96 currently sits inside a skipped range --
invoke the menu directly with `--menu 96` during local QA, or extend the
sweep configuration so this new viewer is exercised).

---

## 5. Expected output

After a successful run against an org that has an in-progress Mist Edge
upgrade, the following files appear under `data/`:

```text
data/org_<org_id>_mx_edge_upgrade_<upgrade_id>_summary.csv
data/org_<org_id>_mx_edge_upgrade_<upgrade_id>_progress.csv
data/mist_data.db                # SQLite, augmented with the new tables
```

If the SQLite backend is active the following tables are populated (DDL
in `data-model.md`):

- `org_mx_edge_upgrade_summary` -- one row, upserted on
  `(org_id, upgrade_id)`.
- `org_mx_edge_upgrade_progress` -- zero or more rows, upserted on
  `(org_id, upgrade_id, mxedge_id)`.

If the ArangoDB + Redis polyglot backend is configured, graph edges from
`org -> upgrade_job -> mx_edge` are written, and per-entity caches are
refreshed in Redis. No code change in the new method is required for that
path -- it is handled inside
`DataExporter.write_with_format_selection()`.

When the upstream API returns an empty progress array (job created but no
edges have started yet), the summary file is still written, and the method
logs a `WARNING` -- `"No per-edge progress entries returned for upgrade
%s"`. No traceback, no non-zero exit.

---

## 6. Example session

```text
> python MistHelper.py --menu 96
[INFO] Loading .env from C:\...\MistHelper\.env
Enter org_id (UUID) [default from .env]:  <press Enter to accept>
Enter Mist Edge upgrade_id (UUID): 8f3a9c1d-1234-4abc-9def-1234abcd0001
[INFO] Fetching Mist Edge upgrade 8f3a9c1d-... for org 1111aaaa-...
[DEBUG] Upgrade status=inprogress target_version=4.2.31337 mxedge_count=3
[INFO] Flattening summary row + per-edge progress rows
[DEBUG] Flatten produced 1 summary row, 3 progress rows
[INFO] Writing summary CSV/SQLite via DataExporter
[INFO] Writing progress CSV/SQLite via DataExporter
[INFO] Done. Files written under data/
```

---

## 7. Expected method shape (~20 lines, <=5 blocks)

```python
def export_org_mx_edge_upgrade(self, org_id: str = None, upgrade_id: str = None) -> int:
    org_id = org_id or safe_input("Enter org_id (UUID): ", context="org_mx_edge_upgrade:org_id")  # Prompt for org if not preset
    upgrade_id = upgrade_id or safe_input("Enter Mist Edge upgrade_id (UUID): ", context="org_mx_edge_upgrade:upgrade_id")  # Prompt for job UUID
    if not _is_uuid(org_id) or not _is_uuid(upgrade_id):  # Fail fast on shape errors before any API call
        logging.warning("Invalid UUID input: org=%s upgrade=%s", org_id, upgrade_id)  # Log validation failure for the operator
        return 1  # Non-zero exit signals input error to the caller
    logging.info("Fetching Mist Edge upgrade %s for org %s", upgrade_id, org_id)  # Action log BEFORE the SDK call (Constitution VII)
    response = mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgrade(self.session, org_id, upgrade_id)  # Sole permitted Mist transport
    payload = response.data or {}  # Tolerate empty response without IndexError
    logging.debug("Upgrade status=%s target_version=%s mxedge_count=%d", payload.get("status"), payload.get("target_version"), len(payload.get("progress", [])))  # Result summary AFTER call
    summary_row = self._flatten_upgrade_summary(org_id, payload)  # Build the one summary row
    progress_rows = self._flatten_upgrade_progress(org_id, payload)  # Build zero or more per-edge rows
    DataExporter.write_with_format_selection([summary_row], f"org_{org_id}_mx_edge_upgrade_{upgrade_id}_summary", api_function_name="getOrgMxEdgeUpgrade")  # Persist summary
    DataExporter.write_with_format_selection(progress_rows, f"org_{org_id}_mx_edge_upgrade_{upgrade_id}_progress", api_function_name="getOrgMxEdgeUpgrade")  # Persist per-edge progress
    return 0  # Zero on success per CLI convention
```

Every line carries an inline comment per Constitution VI. The
`INFO`/`DEBUG` pair brackets the SDK call per Constitution VII. The
function is 13 executable lines, 2 parameters beyond `self`, 5 logical
blocks -- well inside the Five-Item Rule.

---

## 8. Quality gates (required green before commit)

Run all four locally; the container build workflow re-runs them in CI and
blocks merge on failure.

```powershell
# Syntax check
python -m py_compile MistHelper.py

# Lint (must be clean)
python -m ruff check MistHelper.py

# Format (use --check during gate; drop --check to auto-fix locally)
python -m black --check MistHelper.py

# Functional smoke test (heavy/destructive ops are skipped by default)
python MistHelper.py --test
```

Optional but recommended:

```powershell
# Type check
python -m mypy MistHelper.py

# Security lint
python -m bandit -r MistHelper.py

# Property tests (Hypothesis is configured if installed)
python -m pytest tests/ -q
```

The full deployment pipeline (commit -> push -> container build -> pull ->
restart) is documented in `.github/copilot-instructions.md` under "Full
Deployment Pipeline" and is **mandatory** after any code change.
