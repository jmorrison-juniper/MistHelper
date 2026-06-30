# Quickstart: Menu 96 -- getInstallerDeviceVirtualChassis

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Contract**: [contracts/get_installer_device_virtual_chassis.md](./contracts/get_installer_device_virtual_chassis.md)

## Prerequisites

- Python 3.13+ available on PATH.
- Local clone with venv activated:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- `mistapi` 0.59+ installed (`pip install -r requirements.txt` or `uv pip sync`).
- `.env` present at repo root (git-ignored; copy from `deploy/.env.example`).

## Required `.env` variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `MIST_HOST` | Mist cloud region hostname | `api.mist.com` |
| `MIST_API_TOKEN` | API token with Installer scope on the target org | `xxxxxxxxxxxx` |
| `MIST_ORG_ID` | Default org UUID offered at the org_id prompt | `a97c1b22-a4e9-411e-9bfd-d8695a0f9e61` |

The `fpc0_mac` is **not** read from `.env`; the user supplies it interactively per run
(see Research Task 5 rationale).

## Running the menu item locally

### Interactive mode

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the menu prompt, type:
96
# When prompted, accept the default org_id (press Enter) or paste a UUID.
# When prompted, paste the FPC0 MAC in any common notation. Examples that all work:
#   fc:33:42:12:34:56
#   FC-33-42-12-34-56
#   fc33.4212.3456
#   fc3342123456
```

### Direct (non-interactive / automation)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --menu 96 --org-id a97c1b22-a4e9-411e-9bfd-d8695a0f9e61 --fpc0-mac fc3342123456
```

### Test sweep

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --test
# Menu 96 is inside the default sweep range (not in skip list 14, 18, 63-65, 90-100).
```

## Expected output

Two files land under `data/` after a successful run (filenames include both scope IDs to
prevent overwriting prior chassis):

```text
data/installer_device_vc_summary_<org_id>_<fpc0_mac>.csv
data/installer_device_vc_members_<org_id>_<fpc0_mac>.csv
```

And two SQLite tables are upserted in `data/mist_data.db`:

```text
installer_device_vc_summary   (PK: id)
installer_device_vc_members   (PK: vc_id, fpc_idx)
```

On an empty response (rare -- only happens if Mist API returns 200 with `null` body for
a standalone switch wrongly addressed as an FPC0), the menu logs:

```text
WARNING: VC response empty for org <org_id> fpc0 <fpc0_mac>; nothing exported.
```

and returns exit code 0.

## Expected method outline (~22 executable lines)

```python
def export_installer_device_virtual_chassis(self, org_id: str, fpc0_mac: str) -> int:
    """Menu 96: export installer-scope VC topology + per-member stats."""
    # Log INFO before any I/O so the action is visible in the user's log stream.
    logging.info("Fetching installer VC status for org %s fpc0 %s", org_id, fpc0_mac)

    # Normalize MAC (lowercase, strip separators) -- Mist API expects canonical form.
    fpc0_mac_normalized = re.sub(r"[^0-9a-fA-F]", "", fpc0_mac).lower()

    # Validate normalized MAC length -- fail fast on bad input rather than 400 from API.
    if len(fpc0_mac_normalized) != 12:
        logging.warning("Invalid FPC0 MAC after normalization: %s", fpc0_mac)
        return 1

    # Invoke the SDK -- mistapi handles auth, retries, adaptive delay metrics.
    response = mistapi.api.v1.installer.orgs.devices.vc.getInstallerDeviceVirtualChassis(
        self.apisession, org_id, fpc0_mac_normalized
    )

    # DEBUG log the result shape so post-mortem analysis sees member counts.
    payload = response.data or {}
    members = payload.get("members") or []
    logging.debug("VC response: id=%s model=%s members=%d", payload.get("id"), payload.get("model"), len(members))

    # Early-exit on empty payload -- caller already saw the WARNING below.
    if not payload:
        logging.warning("VC response empty for org %s fpc0 %s; nothing exported.", org_id, fpc0_mac_normalized)
        return 0

    # Flatten summary row -- one dict ready for DataExporter.
    summary_row = {k: v for k, v in payload.items() if k != "members"}

    # Flatten members -- inject vc_id, lift cpu_stat/memory_stat/poe into top-level columns.
    member_rows = [self._flatten_vc_member(payload["id"], m) for m in members]

    # Persist summary table via DataExporter (multi-backend dispatch).
    logging.info("Writing VC summary for chassis %s", payload.get("id"))
    self.data_exporter.write_with_format_selection(
        [summary_row],
        f"installer_device_vc_summary_{org_id}_{fpc0_mac_normalized}.csv",
        api_function_name="getInstallerDeviceVirtualChassis",
    )

    # Persist members table via DataExporter (composite-PK upsert).
    logging.info("Writing %d VC member rows", len(member_rows))
    self.data_exporter.write_with_format_selection(
        member_rows,
        f"installer_device_vc_members_{org_id}_{fpc0_mac_normalized}.csv",
        api_function_name="getInstallerDeviceVirtualChassis__members",
    )

    # DEBUG log the final completion summary for the action-logging principle.
    logging.debug("Menu 96 export complete: 1 summary + %d members", len(member_rows))
    return 0
```

Prompt-gathering helper (called by the menu dispatcher before the above method):

```python
def _prompt_for_installer_vc_inputs(self) -> tuple[str, str]:
    """Gather org_id (with .env default) and fpc0_mac via safe_input()."""
    # Pull the .env default so the user can press Enter to accept it.
    default_org = os.environ.get("MIST_ORG_ID", "")
    # safe_input() handles EOF (SSH/container disconnect) gracefully.
    org_id = safe_input(
        f"Enter org_id [{default_org}]: ",
        context="installer_vc:org_id",
    ) or default_org
    # FPC0 MAC has no sensible default -- always prompt; safe_input handles EOF.
    fpc0_mac = safe_input(
        "Enter FPC0 MAC (any notation): ",
        context="installer_vc:fpc0_mac",
    )
    # Return the raw inputs; normalization happens inside the export method.
    return org_id, fpc0_mac
```

## Quality gates (run before every commit)

```powershell
# Syntax check -- no output means valid.
python -m py_compile MistHelper.py

# Lint -- must pass clean.
python -m ruff check MistHelper.py

# Format -- run without --check to auto-fix.
python -m black --check MistHelper.py

# Test sweep -- menu 96 is in the default sweep range.
python MistHelper.py --test
```

All four must succeed before committing per the mandatory deployment pipeline.

## Container test (after CI build completes)

```powershell
# Pull the latest image built by .github/workflows/container-build.yml.
podman pull ghcr.io/jmorrison-juniper/misthelper:latest

# Stop + remove any prior instance.
podman stop misthelper ; podman rm misthelper

# Run with data/ writable and .env mounted read-only.
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
  -v "${PWD}/data:/app/data:rw" `
  -v "${PWD}/.env:/app/.env:ro" `
  ghcr.io/jmorrison-juniper/misthelper:latest

# SSH in and exercise menu 96.
ssh misthelper@localhost -p 2200
# Then type 96 at the menu prompt.
```

## Rollback

If menu 96 misbehaves in production, revert the commit that introduced it:

```powershell
git log --oneline -5
git revert <sha>
git push origin main
```

The container will rebuild and republish automatically; pull and restart per the
pipeline above.
