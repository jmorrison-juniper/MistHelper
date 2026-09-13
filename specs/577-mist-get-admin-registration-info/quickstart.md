# Phase 1 Quickstart: getAdminRegistrationInfo (Menu 59)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Operation**: `getAdminRegistrationInfo` -- read the public reCAPTCHA configuration used
by the Mist admin registration form.

## What this menu item does

- Calls `mistapi.api.v1.admins.admins.getAdminRegistrationInfo(apisession, recaptcha_flavor=None)`.
- Normalizes the single-object JSON response into a one-row list.
- Writes the row through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
  ArangoDB+Redis all receive the same data.
- Upserts cleanly on re-run via the new `natural_pk` strategy on `sitekey`.

## Required `.env` variables

```ini
# Mandatory -- mistapi.APISession needs to know which cloud region to call.
MIST_HOST=api.mist.com

# Optional for this endpoint -- the doc marks it as public. If absent, the menu still works.
# Keep it set for normal MistHelper usage; this menu item just does not require it.
MIST_API_TOKEN=<redacted>
```

No new variables are introduced by this feature.

## Expected `data/` output

| Backend           | Path / location                                |
|-------------------|------------------------------------------------|
| CSV (default)     | `data/admin_registration_info.csv`             |
| SQLite            | `data/mist_data.db` table `admin_registration_info` |
| ArangoDB + Redis  | Collection `admin_registration_info` + Redis key `mist:admin_registration_info:<sitekey>` |

First-time runs create the SQLite table (DDL in `data-model.md`). Subsequent runs
upsert by `sitekey`.

## Run it locally (Windows venv)

```powershell
# Activate the project venv (project standard).
.venv\Scripts\Activate.ps1

# Interactive launch -- menu-driven.
python MistHelper.py
# Then type: 59  <Enter>
# Then at the "reCAPTCHA flavor (google|hcaptcha, blank for default):" prompt,
# either press <Enter> for the API default or type "google" or "hcaptcha".

# Non-interactive direct invocation -- preferred for automation and --test runs.
python MistHelper.py --menu 59
# safe_input() returns the default ("") in non-interactive mode, so the API
# default flavor is used.
```

## Run it in the container

```powershell
# After the standard container-build pipeline completes:
podman exec -it misthelper python /app/MistHelper.py --menu 59
# Or SSH onto port 2200 and select 59 from the menu.
```

## Example session (interactive)

```text
$ python MistHelper.py
...
Select operation: 59
[INFO ] Fetching admin registration reCAPTCHA info, flavor=<default>
reCAPTCHA flavor (google|hcaptcha, blank for default):  <-- user hits Enter
[DEBUG] Got reCAPTCHA flavor=google required=True sitekey_len=40
[INFO ] Writing 1 row to admin_registration_info via DataExporter
[DEBUG] DataExporter wrote csv=data/admin_registration_info.csv sqlite=admin_registration_info rows=1
[INFO ] Menu 59 complete in 0.83s
```

## Implementation outline (for the task generator)

```python
# In MistHelper.py, inside class OrgExportUtils:
def export_admin_registration_info(self, recaptcha_flavor: str = "") -> None:
    """Export the public reCAPTCHA registration config (menu 59)."""
    # Prompt user via safe_input -- empty default means 'let the API choose'.
    flavor_input = safe_input(
        "reCAPTCHA flavor (google|hcaptcha, blank for default): ",
        context="admin_registration_info:recaptcha_flavor",
    ).strip()
    # Validate against documented enum; drop unknown values with a warning.
    flavor = flavor_input if flavor_input in ("", "google", "hcaptcha") else ""
    if flavor_input and not flavor:                                  # User typed something invalid.
        logging.warning("Ignoring unknown recaptcha_flavor=%r", flavor_input)
    # INFO log before the API call (Principle VII).
    logging.info("Fetching admin registration reCAPTCHA info, flavor=%s", flavor or "<default>")
    # Single GET via the mistapi SDK -- no path params, one optional query arg.
    response = mistapi.api.v1.admins.admins.getAdminRegistrationInfo(
        self.api_session, recaptcha_flavor=(flavor or None),
    )
    # mistapi returns a .data attribute on the response wrapper.
    payload = response.data if hasattr(response, "data") else response
    # Normalize the single object into a one-row list for DataExporter.
    rows = [payload] if isinstance(payload, dict) and payload.get("sitekey") else []
    # DEBUG log with parsed fields (Principle VII).
    logging.debug(
        "Got reCAPTCHA flavor=%s required=%s sitekey_len=%d",
        payload.get("flavor") if rows else None,
        payload.get("required") if rows else None,
        len(payload.get("sitekey", "")) if rows else 0,
    )
    # INFO log before write.
    logging.info("Writing %d row to admin_registration_info via DataExporter", len(rows))
    # Multi-backend write -- CSV / SQLite / ArangoDB+Redis decided by user setting.
    self.data_exporter.write_with_format_selection(
        rows, "admin_registration_info", api_function_name="getAdminRegistrationInfo",
    )
```

Every executable line above carries an inline comment (Principle VI), and every
meaningful step has a before/after log pair (Principle VII). Function is 18 lines, takes
2 parameters, contains 5 logical blocks (prompt -> validate -> API call -> normalize ->
write) -- all under the 5-Item Rule (Principle I).

## Quality gates

Run these in order before committing. All four must pass.

```powershell
# 1. Syntax check -- silent on success, blocking on failure.
python -m py_compile MistHelper.py

# 2. Lint -- must report zero violations.
python -m ruff check MistHelper.py

# 3. Format -- must report "would be left unchanged".
python -m black --check MistHelper.py

# 4. Functional smoke test -- exercises menu 59 via --test against the .env org.
python MistHelper.py --test
```

Then follow the full deployment pipeline in `.github/copilot-instructions.md`
(commit -> push -> watch container build -> podman pull -> restart container -> verify).

## Troubleshooting

| Symptom                                       | Likely cause                              | Fix                                                |
|-----------------------------------------------|-------------------------------------------|----------------------------------------------------|
| `MIST_HOST is not set` at startup             | `.env` missing or not loaded              | Copy `deploy/.env.example` -> `.env`, set host.    |
| Empty CSV / "no data returned" log            | API returned `{}` (rare)                  | Re-run; if persistent, check the host region.      |
| `PermissionError: data/...`                   | `data/` not writable in container         | `chmod -R 777 data/` then restart container.       |
| Duplicate rows in SQLite after several runs   | PK strategy not registered                | Confirm `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry.   |
