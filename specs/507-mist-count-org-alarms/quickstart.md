# Phase 1 Quickstart: countOrgAlarms

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Data model**: [data-model.md](./data-model.md) | **Contract**: [contracts/count_org_alarms.md](./contracts/count_org_alarms.md)

This quickstart shows a junior NOC engineer how to run the new menu item
locally on Windows, what `.env` variables it needs, what files appear in
`data/`, and which quality gates must be green before commit.

## 1. Prerequisites

- Python 3.13+ installed on Windows 11.
- The MistHelper repo cloned to a worktree and the venv activated:

  ```powershell
  cd "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging"
  .venv\Scripts\Activate.ps1
  ```

- Dependencies installed:

  ```powershell
  python -m pip install -r requirements.txt
  ```

- `data\` directory writable (the container runs as a non-root user, so on
  Linux/Podman it requires `chmod -R 777 data/`; on Windows the default ACL
  already permits the venv user to write).

## 2. Required `.env` variables

The file `.env` lives at the repo root and is git-ignored. The new menu item
needs only the standard Mist authentication pair:

```ini
# Mist API host (regional endpoint -- pick one)
MIST_HOST=api.mist.com

# API token issued from the Mist UI (Org Settings -> API Tokens)
MIST_API_TOKEN=replace-with-your-real-token
```

Optional knobs that already exist project-wide and still apply here:

- `MIST_PAGE_LIMIT=1000` -- default per-page cap (this endpoint defaults to
  100, controlled separately by the menu's own `limit` prompt).
- `FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8` -- only honored when run with
  `--fast`. This endpoint is a single GET, so `--fast` has little effect.

No new `.env` variable is introduced by this feature.

## 3. Run the menu item

### Interactive (menu-driven)

```powershell
python MistHelper.py
```

At the menu prompt, type `58` and press Enter. The session then asks (each
prompt is wrapped in `safe_input()` so EOF in SSH/container exits cleanly with
code 0):

```
Enter org_id (UUID) [required]: 203d3d02-XXXX-XXXX-XXXX-XXXXXXXXXXXX
Enter distinct grouping field (e.g. type, severity, hostname) [optional]: type
Enter duration window (e.g. 1d, 7d, 1w) [default 1d]:
Enter result limit (1-1000) [default 100]:
```

Pressing Enter on the latter two accepts the documented defaults (`1d`, `100`).

### Direct (automation-friendly)

```powershell
python MistHelper.py --menu 58
```

In `--menu` mode the operation still prompts for `org_id` interactively because
the org context is per-run. To skip every prompt (CI / `--test` mode), pre-set
the org in the test harness section of `.env`:

```ini
TEST_ORG_ID=203d3d02-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

Then:

```powershell
python MistHelper.py --test
```

The test sweep includes menu 58 because it sits inside the default range
(1-89) and is not on the heavy/destructive skip list (14, 18, 63-65, 90-100).

## 4. Expected output

Two artifacts land under `data/` per run (timestamps reflect the local clock):

```
data\org_alarms_count_summary_20260628_225200.csv
data\org_alarms_count_buckets_20260628_225200.csv
```

If the active backend is SQLite, the same rows upsert into
`data\mist_data.db` under tables `org_alarms_count_summary` and
`org_alarms_count_buckets`. Re-running the menu item with the same `org_id`,
`distinct`, and `duration` does **not** create duplicate rows -- the composite
primary key replaces the previous envelope in place.

Sample console output (ASCII, no Unicode):

```
INFO  Counting org alarms for org 203d3d02 distinct=type window=1d limit=100
DEBUG Count result: total=42 buckets=6
INFO  Flattening 6 bucket rows for org 203d3d02
DEBUG Flatten complete: 1 summary row, 6 bucket rows
INFO  Writing org_alarms_count to backend(s)
DEBUG DataExporter wrote 1 summary row, 6 bucket rows
```

## 5. Method skeleton (what the implementer will write)

The new method lives on the existing `AlarmExportUtils` class (the class that
owns `searchOrgAlarms`). Every executable line gets an inline comment per
Principle VI; the before/after `logging` lines satisfy Principle VII.

```python
def export_org_alarms_count(self, org_id, distinct=None, duration="1d", limit=100):
    """Menu 58 -- count org alarms grouped by a distinct attribute."""
    org_id = self._validate_uuid(org_id, context="org_alarms_count:org_id")  # Reject malformed UUIDs early
    if not org_id:                                                           # Validation failure -> exit clean
        return                                                               # safe_input already logged the issue
    logging.info("Counting org alarms for org %s distinct=%s window=%s", org_id, distinct, duration)  # Pre-call log
    response = mistapi.api.v1.orgs.alarms.count.countOrgAlarms(              # Single SDK call -- endpoint is non-paginated
        self.apisession, org_id,                                              # APISession holds the token from .env
        distinct=distinct or None, duration=duration, limit=int(limit),       # Empty distinct -> omit query param
    ).data                                                                    # .data unwraps the mistapi Response envelope
    logging.debug("Count result: total=%s buckets=%s", response.get("total"), len(response.get("results", [])))  # Post-call log
    summary_row, bucket_rows = self._flatten_count_payload(response, org_id, duration)  # Two-table split per data-model.md
    DataExporter.write_with_format_selection(                                 # Multi-backend writer (CSV/SQLite/ArangoDB)
        data=[summary_row], filename="org_alarms_count_summary",               # Envelope row
        api_function_name="countOrgAlarms_summary",                            # Drives PK strategy lookup
    )
    DataExporter.write_with_format_selection(                                 # Second write -- bucket rows
        data=bucket_rows, filename="org_alarms_count_buckets",                 # Detail rows
        api_function_name="countOrgAlarms_buckets",                            # Drives PK strategy lookup
    )
```

Line count: 13 executable lines (well under the 25-line ceiling). Parameter
count: 5 (`self`, `org_id`, `distinct`, `duration`, `limit`) -- exactly at the
ceiling, no further parameters may be added without refactoring. Block count:
4 (validate, log+call, flatten, two writes treated as one block) -- inside
the 5-block ceiling.

## 6. Quality gates (must all be green before commit)

Run in this order from the repo root:

```powershell
# 1. Syntax check -- silent success means valid
python -m py_compile MistHelper.py

# 2. Lint -- must pass clean
python -m ruff check MistHelper.py

# 3. Format -- must pass clean; drop --check to auto-fix
python -m black --check MistHelper.py

# 4. Test sweep (skip list applied automatically)
python MistHelper.py --test
```

Then follow the standard pipeline documented in
`.github/copilot-instructions.md` "MANDATORY: Full Deployment Pipeline" --
commit with a `version YY.MM.DD.HH.MM - add menu 58 countOrgAlarms` message,
push to `main`, wait for `container-build.yml`, pull the new image, restart
the container, and verify with `podman ps`.

## 7. Troubleshooting

| Symptom                                                  | Likely cause                                  | Fix                                                 |
|----------------------------------------------------------|-----------------------------------------------|-----------------------------------------------------|
| `PermissionError: [Errno 13] ... /app/data/script.log`   | Container data dir not writable               | `chmod -R 777 data/` on the host before re-running  |
| `401 Unauthorized` in log                                | Invalid or expired `MIST_API_TOKEN`           | Re-issue the token in the Mist UI, update `.env`    |
| `404 Not found` in log                                   | Wrong `org_id` or wrong `MIST_HOST` region    | Confirm the org appears under the same Mist host    |
| Empty `results` list, `total=0`                          | No alarms in the window for that grouping     | Try a wider `duration` (e.g. `7d`) or drop `distinct` |
| `429 Too Many Requests`                                  | API token hit the 5000/hr cap                 | Wait one hour; adaptive delay system handles it     |
