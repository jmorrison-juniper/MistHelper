# Phase 1 Quickstart: getOrgOtherDevice (Menu 96)

Feature: `629-mist-get-org-other-device`
Endpoint: `GET /api/v1/orgs/{org_id}/otherdevices/{device_mac}`

## Purpose

Retrieve the full record for one non-Juniper (third-party) device tracked by a Mist
organization, keyed on the device MAC address, and persist the result through the
standard multi-backend exporter.

## Prerequisites

- Python 3.13+ on the host or Podman container.
- `mistapi` 0.59+ installed (already in `requirements.txt` / `uv.lock`).
- A Windows 11 venv activated (`.venv\Scripts\Activate.ps1`) or the standard container
  image `ghcr.io/jmorrison-juniper/misthelper:latest`.
- Valid `.env` at repo root.

## Required `.env` Variables

| Variable                       | Required | Purpose                                                             |
|--------------------------------|----------|---------------------------------------------------------------------|
| `MIST_HOST`                    | Yes      | Mist cloud host (e.g., `api.mist.com`, `api.eu.mist.com`).          |
| `MIST_API_TOKEN`               | Yes      | API token; loaded by `mistapi.APISession`; never logged.            |
| `MIST_ORG_ID`                  | Optional | Pre-fills the `org_id` prompt when set. Skipped otherwise.          |
| `MIST_TEST_OTHER_DEVICE_MAC`   | Optional | Used only by `python MistHelper.py --test` to skip the MAC prompt.  |

## How to Run Locally

### Interactive mode (menu-driven)

```powershell
.venv\Scripts\Activate.ps1                # Activate the project virtual environment.
python MistHelper.py                      # Launch the interactive menu.
# At the menu prompt:
96                                        # Select "Get Org Other Device by MAC".
# When prompted (skip org_id if MIST_ORG_ID is in .env):
<org_id>                                  # e.g., a97c1b22-a4e9-411e-9bfd-d8695a0f9e61
<device_mac>                              # e.g., aa:bb:cc:dd:ee:ff or aabbccddeeff
```

### Direct invocation (automation-friendly)

```powershell
python MistHelper.py --menu 96
```

The `--menu 96` path still uses `safe_input()` for the two prompts, so it works in
SSH and container contexts. If `MIST_ORG_ID` and `MIST_TEST_OTHER_DEVICE_MAC` are set,
both prompts are auto-satisfied and the command runs non-interactively.

## Expected Output

- **CSV**: `data/org_other_device.csv` -- one row per successful invocation, appended
  and deduplicated on `id`.
- **SQLite**: Table `org_other_device` in `data/mist_data.db` -- one upserted row
  keyed on `id`.
- **ArangoDB**: Document upserted into the `org_other_device` collection
  (`_key = <id>`) when the polyglot backend is enabled.
- **Redis**: Key `org_other_device:<id>` populated when the polyglot backend is
  enabled.

Log output (INFO level) at successful completion looks like:

```
INFO Fetching other device aabbccddeeff for org a97c1b22-a4e9-411e-9bfd-d8695a0f9e61
DEBUG Received other device id=53f10664-3ce8-4c27-b382-0ef66432349f vendor=cisco model=cat9300 state=connected
INFO Writing 1 row to data/org_other_device.csv via DataExporter
DEBUG Export complete: csv=1 sqlite=1
```

## Method Outline (Reference for `/speckit.implement`)

The new method on `OrgExportUtils` follows this shape. Every executable line carries
an inline comment (Constitution VI) and INFO / DEBUG log calls bracket every action
(Constitution VII):

```python
def export_org_other_device(self, org_id: str | None = None,
                            device_mac: str | None = None) -> None:
    """Fetch and persist one third-party device record by MAC."""
    org_id = org_id or ConfigUtils.get_org_id()  # Resolve org from .env or prompt.
    if not org_id:                                # Guard: user cancelled or empty env.
        org_id = safe_input("Enter org_id: ",     # Fall back to interactive prompt.
                            context="org_other_device:org_id").strip()
    if not ValidationUtils.is_valid_uuid(org_id): # Reject malformed UUIDs early.
        logging.warning("Invalid org_id: %s", org_id)  # ASCII warning, no traceback.
        return                                    # Early exit per Principle III.
    if not device_mac:                            # Prompt when caller did not supply.
        device_mac = safe_input("Enter device MAC: ",  # safe_input for SSH/container EOF.
                                context="org_other_device:device_mac").strip()
    normalized_mac = ValidationUtils.normalize_mac(device_mac)  # aabbccddeeff form.
    if not normalized_mac:                        # normalize_mac returns None on bad input.
        logging.warning("Invalid device_mac: %s", device_mac)   # Warn and exit cleanly.
        return                                    # No SDK call on invalid MAC.
    logging.info("Fetching other device %s for org %s",         # Action logging: before.
                 normalized_mac, org_id)
    response = mistapi.api.v1.orgs.otherdevices.getOrgOtherDevice(  # Sole SDK call.
        self.mist_session, org_id, normalized_mac)
    other_device_row = response.data or {}        # Empty dict on 404-style empty.
    logging.debug("Received other device id=%s vendor=%s model=%s state=%s",
                  other_device_row.get("id"), other_device_row.get("vendor"),
                  other_device_row.get("model"), other_device_row.get("state"))
    if not other_device_row:                      # Nothing to persist on empty response.
        logging.warning("Other device not found: %s", normalized_mac)
        return
    DataExporter.write_with_format_selection(     # Multi-backend write (CSV/SQLite/etc).
        [other_device_row],                       # Wrap the single object as a one-row list.
        "org_other_device.csv",                   # Filename stem drives table/collection.
        api_function_name="getOrgOtherDevice",    # Matches ENDPOINT_PRIMARY_KEY_STRATEGIES.
    )
```

Line count: ~22 executable lines, `<=3` parameters, `<=5` logical blocks (prompt ->
validate -> API call -> validate response -> export). Constitution Principle I (Five
Item Rule) satisfied.

## Quality Gates

Run every gate before committing. Every gate must pass clean.

```powershell
python -m py_compile MistHelper.py       # Syntax check (no output on success).
python -m ruff check MistHelper.py       # Lint check (must be clean).
python -m black --check MistHelper.py    # Format check (rerun without --check to fix).
python MistHelper.py --test              # Test sweep; item 96 is inside default range.
```

If any gate fails, do not commit. Fix locally, rerun all four gates, then proceed to
the standard deployment pipeline documented in `.github/copilot-instructions.md`
(commit -> push -> container build -> pull -> restart -> verify).

## Verification Steps

1. `Test-Path data\org_other_device.csv` returns `True` after the first successful run.
2. Open `data\mist_data.db` with any SQLite browser; confirm the `org_other_device`
   table exists, contains at least one row, and that `id` is the primary key.
3. Re-run menu 96 with the same MAC; row count in the table stays constant (upsert).
4. Re-run menu 96 with a fresh MAC; row count increases by exactly one.
5. Run menu 96 with an obviously invalid MAC (e.g., `zz-zz-zz-zz-zz-zz`); the process
   exits with code 0, no traceback, and a single WARNING line in the log.
