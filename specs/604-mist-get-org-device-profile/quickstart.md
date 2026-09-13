# Phase 1 Quickstart: getOrgDeviceProfile (Menu 96)

**Feature**: 604-mist-get-org-device-profile
**Endpoint**: `GET /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}`
**Proposed menu number**: 96 (Viewers cluster 92-96)

## Prerequisites

- Python 3.13 or newer.
- `mistapi` 0.59+ installed (`pip install -r requirements.txt` or
  `uv pip install -r requirements.txt`).
- A populated `.env` at the repo root (never committed):

  ```ini
  MIST_HOST=api.mist.com
  MIST_API_TOKEN=<your-token>
  MIST_ORG_ID=<your-default-org-uuid>
  ```

- A known device-profile UUID for the org above. To find one quickly, first
  run Menu 35 (`listOrgDeviceProfiles`) and copy the `id` field of any row
  from `data/org_device_profiles.csv`.
- Writable `data/` directory:

  ```powershell
  chmod -R 777 data\
  ```

## Required `.env` Variables

| Variable | Required | Used For |
|----------|----------|----------|
| `MIST_HOST` | Yes | Mist cloud region hostname. |
| `MIST_API_TOKEN` | Yes | Bearer token; injected by `mistapi.APISession`. Never logged. |
| `MIST_ORG_ID` | Recommended | Default value offered at the first `safe_input()` prompt. |

No new `.env` variable is introduced by this feature.

## Expected `data/` Output

After a successful run with the SQLite + CSV backends active, the following
files exist under `data/`:

| Path | Contents |
|------|----------|
| `data/org_device_profile.csv` | One row -- the flattened profile. |
| `data/mist_data.db` | Table `org_device_profile` now has (or has upserted) one row keyed on the profile UUID. |
| `data/script.log` | Append-only log of the run; INFO / DEBUG lines for the new menu method. |

When the ArangoDB + Redis backend is active the same logical row is also
written to the `org_device_profile` collection and cached at
`mist:org_device_profile:<id>` (see `data-model.md`).

## Interactive Invocation

From the repo root in a Windows PowerShell session:

```powershell
.\.venv\Scripts\Activate.ps1
python MistHelper.py
```

Then at the menu prompt enter `96`. Expected prompt sequence:

```text
Enter Mist org ID [default: <MIST_ORG_ID from .env>]: <Enter>
Enter device profile UUID: 11111111-2222-3333-4444-555555555555
INFO  Fetching device profile 11111111-... for org abcd1234-...
INFO  Writing org_device_profile via DataExporter
DEBUG Profile fetched: type=ap name=Lobby-AP
DEBUG Wrote 1 row to org_device_profile across active backends
Operation 96 complete. Press Enter to return to menu.
```

## Direct (Non-Interactive) Invocation

For scripted / CI runs:

```powershell
python MistHelper.py --menu 96
```

In direct mode `safe_input()` reads from stdin; pipe answers in via a here-
string when fully automating:

```powershell
@'
<org-uuid-or-blank-for-default>
<deviceprofile-uuid>
'@ | python MistHelper.py --menu 96
```

## Skeleton of the New Method (for orientation)

The actual implementation is produced by `/speckit.tasks` then
`/speckit.implement`. This skeleton illustrates the comment density,
logging pairs, and 5-Item-Rule structure required by the constitution -- it
is **not** the final code:

```python
def export_org_device_profile(self, org_id: str | None = None,
                              deviceprofile_id: str | None = None) -> None:
    org_id = org_id or safe_input(  # Reuse caller-supplied value when scripted
        f"Enter Mist org ID [default: {self.default_org_id}]: ",
        context="org_device_profile:org_id",
    ) or self.default_org_id  # Fall back to .env MIST_ORG_ID on empty input
    deviceprofile_id = deviceprofile_id or safe_input(  # Same pattern for profile UUID
        "Enter device profile UUID: ",
        context="org_device_profile:deviceprofile_id",
    )
    if not _is_mist_uuid(org_id) or not _is_mist_uuid(deviceprofile_id):  # Cheap local validation
        logging.warning("Invalid UUID supplied; aborting menu 96")  # ASCII-only warning
        return  # Early-exit per 5-Item Rule
    logging.info(  # Action log BEFORE the API call
        "Fetching device profile %s for org %s", deviceprofile_id, org_id,
    )
    response = mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile(  # SDK call
        self.apisession, org_id, deviceprofile_id,
    )
    profile = response.data or {}  # Defensive default for empty body
    logging.debug(  # Action log AFTER the API call
        "Profile fetched: type=%s name=%s",
        profile.get("type"), profile.get("name"),
    )
    DataExporter.write_with_format_selection(  # Multi-backend persistence
        [profile], "org_device_profile",
        api_function_name="getOrgDeviceProfile",
    )
```

Every executable line carries an inline comment per Constitution VI. The
method is 17 executable lines (well under 25), takes 3 parameters (under 5),
and has 5 logical blocks (prompt org -> prompt profile -> validate -> call
-> export) -- compliant with Principle I.

## Quality Gates (run all four before commit)

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
python MistHelper.py --test
```

All four must return zero / no findings. The first three are pre-commit
hooks; the fourth exercises menu 96 in non-interactive mode using the
`.env` defaults. If `--test` cannot reach a valid device profile (404 from
Mist), the run logs a warning and exits 0 -- this is by design so CI does
not fail when test data is missing.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `PermissionError: '/app/data/script.log'` | Container data volume not world-writable. | `chmod -R 777 data\` then re-run the container. |
| `WARNING Invalid UUID supplied; aborting menu 96` | UUID typo or extra whitespace. | Re-enter the value; copy from `data/org_device_profiles.csv`. |
| `WARNING 404 from getOrgDeviceProfile` | Profile UUID not in this org. | Confirm org context; the profile may belong to a different org. |
| `429 Too Many Requests` surfaced as backoff in logs | Rate cap hit. | Wait; the adaptive delay system handles retry automatically. |
| `ImportError: No module named 'mistapi.api.v1.orgs.deviceprofiles'` | mistapi older than 0.59. | `pip install --upgrade mistapi` then verify with `python -c "import mistapi; print(mistapi.__version__)"`. |
