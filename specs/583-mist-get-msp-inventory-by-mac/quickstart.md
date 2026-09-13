# Phase 1 Quickstart: getMspInventoryByMac (Menu 96)

**Feature**: 583-mist-get-msp-inventory-by-mac

This quickstart shows a developer how to exercise the new menu item locally on a
Windows 11 + venv workstation. The container path (Podman on 2200) is identical
except for the launch command.

---

## 1. Required `.env` Variables

Add or confirm the following in the repo-root `.env` file (already git-ignored):

```ini
# Already required by every MistHelper menu
MIST_HOST=api.mist.com                                  # or api.eu.mist.com, etc.
MIST_API_TOKEN=<your_long_lived_api_token>              # never log this

# Used as the default for the msp_id prompt (press Enter to accept)
MSP_ID=00000000-0000-0000-0000-000000000000             # your MSP UUID

# Used by `--test` to make the menu sweep non-interactive
MSP_TEST_DEVICE_MAC=aa:bb:cc:dd:ee:ff                   # any known-good MAC in MSP scope
```

Nothing else is required. The API token is loaded by `mistapi.APISession`; the host
selects the regional cluster.

---

## 2. Activate the venv

```powershell
cd "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging"
.venv\Scripts\Activate.ps1
```

If the venv does not exist:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

---

## 3. Run the Menu Item Interactively

```powershell
python MistHelper.py --menu 96
```

Expected interaction:

```
Enter MSP ID (UUID) [00000000-0000-0000-0000-000000000000]: <Enter to accept default>
Enter device MAC (any separator): aa:bb:cc:dd:ee:ff
[INFO] Looking up MSP 00000000-... inventory for MAC aa:bb:cc:dd:ee:ff
[DEBUG] Inventory hit: org_id=a97c1b22-a4e9-411e-9bfd-d8695a0f9e61
        site_id=441a1214-6928-442a-8e92-e1d34b8ec6a6 model=AP43 serial=ABC123
[INFO] Writing 1 row(s) to data/msp_inventory_by_mac.csv
[DEBUG] Wrote 1 row(s); SQLite upsert via PK (msp_id, mac) -- 0 duplicates
```

If the MAC is not found in any org under the MSP, the API returns 404 and MistHelper
logs:

```
[WARNING] MAC aa:bb:cc:dd:ee:ff not found in MSP 00000000-... inventory (HTTP 404)
```

The process exits 0 (not a traceback) in both the success and the 404 case.

---

## 4. Expected Output Files

After a successful run, `data/` contains:

```text
data/msp_inventory_by_mac.csv     # One header row + one data row per successful lookup
data/mist_data.db                 # SQLite -- new table msp_inventory_by_mac
                                  # (created on first run by DataExporter)
data/script.log                   # Standard MistHelper log; new INFO/DEBUG lines
```

Re-running with the same MAC overwrites the SQLite row via `INSERT OR REPLACE`
on the composite PK `(msp_id, mac)` -- no duplicates. The CSV file is appended
to per existing DataExporter convention.

---

## 5. Run Non-Interactively (Test Mode)

```powershell
python MistHelper.py --test --menu 96
```

This skips the prompts by using `MSP_ID` and `MSP_TEST_DEVICE_MAC` from `.env`,
and is what the full `--test` sweep exercises against menu 96 in CI.

---

## 6. Method Outline (For the Implementer)

The new method on `MSPInventoryExporter` looks roughly like this (inline comments
shown at the constitutional density -- one per executable line):

```python
def lookup_msp_inventory_by_mac(self, msp_id=None, device_mac=None):
    # Resolve msp_id from arg / .env / prompt without breaking SSH EOF handling
    msp_id = msp_id or os.environ.get('MSP_ID') or safe_input(
        "Enter MSP ID (UUID): ", context="msp_inventory_by_mac:msp_id")
    # Resolve device_mac the same way; honor --test mode via env override
    device_mac = device_mac or os.environ.get('MSP_TEST_DEVICE_MAC') or safe_input(
        "Enter device MAC (any separator): ",
        context="msp_inventory_by_mac:device_mac")
    # Validate msp_id shape early to avoid burning an API call on malformed input
    if not UUID_REGEX.match(msp_id):
        logging.warning("Invalid MSP UUID: %s -- aborting lookup", msp_id)
        return
    # Normalize MAC to lowercase colon-separated form the Mist API expects
    mac_normalized = normalize_mac(device_mac)
    # Validate the normalized MAC against 12-hex-digit regex before SDK call
    if not MAC_REGEX.match(mac_normalized):
        logging.warning("Invalid device MAC: %s -- aborting lookup", device_mac)
        return
    # Action log BEFORE the SDK call per Principle VII
    logging.info("Looking up MSP %s inventory for MAC %s", msp_id, mac_normalized)
    # Single GET; no pagination, no retry-loop needed beyond SDK defaults
    response = mistapi.api.v1.msps.inventory.getMspInventoryByMac(
        self.apisession, msp_id, mac_normalized)
    # Action log AFTER with summary fields per Principle VII
    logging.debug("Inventory hit: org_id=%s site_id=%s model=%s serial=%s",
                  response.data.get('org_id'), response.data.get('site_id'),
                  response.data.get('model'), response.data.get('serial'))
    # Flatten one-row payload + synthesize msp_id (not in response body)
    row = self._build_inventory_row(msp_id, response.data)
    # Hand off to multi-backend writer -- it owns CSV/SQLite/ArangoDB path selection
    DataExporter.write_with_format_selection(
        [row], "msp_inventory_by_mac",
        api_function_name="getMspInventoryByMac")
```

---

## 7. Quality Gates (Run BEFORE Commit)

```powershell
# 1. Syntax check (no output = pass)
python -m py_compile MistHelper.py

# 2. Lint check (must be clean)
python -m ruff check MistHelper.py

# 3. Format check (run without --check to auto-fix)
python -m black --check MistHelper.py

# 4. Full test sweep (skips destructive 90-100, but 96 sits OUTSIDE that band per
#    coding-standards skip list which is actually 14, 18, 63-65, 90-100; 96 is in-scope)
python MistHelper.py --test
```

All four MUST pass before committing. If any fail, fix and re-run.

---

## 8. After Implementation: Deployment Pipeline

Per the project deployment pipeline (NON-NEGOTIABLE):

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 96 getMspInventoryByMac"
git push origin main
gh run watch <run-id>                                        # wait for container build
podman pull ghcr.io/jmorrison-juniper/misthelper:latest      # pull new image
podman stop misthelper ; podman rm misthelper                # stop old container
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 `
    -v "${PWD}/data:/app/data:rw" `
    -v "${PWD}/.env:/app/.env:ro" `
    ghcr.io/jmorrison-juniper/misthelper:latest              # restart container
podman ps                                                    # verify running
```
