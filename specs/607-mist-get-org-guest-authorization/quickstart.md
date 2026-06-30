# Phase 1 Quickstart: GetOrgGuestAuthorization (Menu 96)

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Data Model**: [data-model.md](./data-model.md)
**Date**: 2026-06-30

This quickstart shows how to run menu 96 locally on Windows 11 against a real Mist
org, and the exact quality gates the AI agent or human implementer must pass before
committing.

## Prerequisites

- Python 3.13+
- `git clone` of this repo onto a Windows 11 dev box
- A populated `.venv` in the repo root (`python -m venv .venv`)
- A populated `.env` in the repo root (see below)

## Required `.env` Variables

```ini
# Mist cloud region host -- e.g. api.mist.com / api.eu.mist.com / api.gc1.mist.com
MIST_HOST=api.mist.com

# Mist API token with read access to the target org -- never commit
MIST_API_TOKEN=<token-from-mist-portal>

# Default org UUID -- pressing Enter at the org_id prompt falls back to this
MIST_ORG_ID=<org-uuid>

# Optional: log level for the run
LOG_LEVEL=INFO
```

`MIST_API_TOKEN` is consumed exclusively by `mistapi.APISession` and is never echoed
or logged by MistHelper. `MIST_ORG_ID` is the convenience fallback; if both the
prompt and this env var are empty the menu method logs a warning and returns early.

## Activate Environment

```powershell
cd "C:\Users\<you>\...\MistHelper.worktrees\copilot-openapi-mist-api-endpoint-cataloging"
.venv\Scripts\Activate.ps1
```

## Interactive Invocation

```powershell
python MistHelper.py
```

Then at the menu prompt enter `96`. You will be asked for two values in order:

```
Enter org UUID (Enter for MIST_ORG_ID from .env):
Enter guest MAC (any format -- will be normalized):
```

Acceptable MAC input formats (all normalize to the same value):

- `aa:bb:cc:dd:ee:ff`
- `AA-BB-CC-DD-EE-FF`
- `aabbccddeeff`
- `aabb.ccdd.eeff`

## Direct (Non-Interactive) Invocation

```powershell
python MistHelper.py --menu 96
```

In `--test` mode the runner supplies `MIST_ORG_ID` from `.env` for `org_id` and
expects either an env-supplied `TEST_GUEST_MAC` or skips the test if that variable
is absent. (The skip is silent and reported in the test summary.)

## Expected Output

On success a single row is written under `data/`. Filenames depend on the active
backend:

| Backend | Output |
|---------|--------|
| CSV | `data/org_guest_authorization.csv` (header + 1 row, upserts on rerun) |
| SQLite | `data/mist_data.db` -- table `org_guest_authorization`, row keyed `(org_id, mac)` |
| JSON | `data/org_guest_authorization.json` |
| ArangoDB + Redis | Document in collection `org_guest_authorization`; edges to `org` and (when `wlan_id` present) `wlan`; Redis cache key `org_guest_authorization:<org_id>:<mac>` |

Expected console log lines (ASCII only, no PII):

```
INFO  Fetching guest authorization for org <org_id_short> mac <mac>
DEBUG Guest auth: authorized=True ssid=Guest-SSID auth_method=email
INFO  Flattening guest authorization record
DEBUG Flattened 1 record with 20 columns
INFO  Writing guest authorization to data/org_guest_authorization
```

## Expected Method Outline

The implementer writes one new method on the chosen exporter class. The skeleton
below illustrates required commenting density and log placement (Principles VI and
VII). Final code lives in `MistHelper.py`.

```python
def export_org_guest_authorization(self, org_id: str, guest_mac: str) -> None:
    # Normalize the user-supplied MAC to 12 lower-case hex chars for SDK + PK stability
    normalized_mac = re.sub(r"[^0-9a-fA-F]", "", guest_mac).lower()
    # Validate UUID + MAC shape early so a typo never reaches the API
    if not _is_valid_uuid(org_id) or len(normalized_mac) != 12:
        logging.warning("Invalid org_id or guest_mac -- aborting")  # User-visible reason
        return  # Early return per Safety-First principle

    logging.info("Fetching guest authorization for org %s mac %s",
                 org_id[:8], normalized_mac)  # PII-safe context line
    # Single non-paginated GET via the canonical mistapi entry point
    response = mist_guests.getOrgGuestAuthorization(self.session, org_id, normalized_mac)
    record = response.data or {}  # API returns {} on empty -- guard against None
    logging.debug("Guest auth: authorized=%s ssid=%s auth_method=%s",  # ASCII summary
                  record.get("authorized"), record.get("ssid"), record.get("auth_method"))

    logging.info("Flattening guest authorization record")  # Phase boundary log
    record["org_id"] = org_id                                # Inject for backend joinability
    record["mac"] = normalized_mac                           # Force PK alignment
    record["polled_at_utc"] = datetime.datetime.now(datetime.UTC).isoformat(
        timespec="seconds")                                  # Audit timestamp
    logging.debug("Flattened 1 record with %d columns", len(record))

    logging.info("Writing guest authorization to data/org_guest_authorization")
    # Multi-backend persistence -- DataExporter routes to CSV / SQLite / ArangoDB
    DataExporter.write_with_format_selection(
        data=[record],
        filename="org_guest_authorization",
        api_function_name="getOrgGuestAuthorization",
    )
```

Line count: well under the 25-line Five-Item Rule ceiling. Parameter count: 3
(includes `self`). Logical blocks: 5 (normalize/validate, API call, flatten,
write -- with logging interleaved).

## Quality Gates

Run all of the following before committing. Each must exit 0 / pass clean.

```powershell
# 1. Syntax check -- no output on success
python -m py_compile MistHelper.py

# 2. Lint -- must pass clean
python -m ruff check MistHelper.py

# 3. Formatting -- must be a no-op (re-run without --check to auto-fix)
python -m black --check MistHelper.py

# 4. Functional test sweep -- exercises the new menu item in non-interactive mode
python MistHelper.py --test
```

If any gate fails, fix it before commit. Do not suppress findings -- see
constitution "Security Findings: Fix Over Suppress (NON-NEGOTIABLE)".

## Manual Verification Checklist

- [ ] `data/org_guest_authorization.csv` exists after the run.
- [ ] Re-running menu 96 with the same `org_id` / `guest_mac` produces no duplicate
      rows in `data/mist_data.db` (`SELECT COUNT(*) FROM org_guest_authorization WHERE
      org_id = ? AND mac = ?;` returns 1, not 2).
- [ ] Log output contains no email addresses, company strings, or `fieldN` values.
- [ ] Log output contains no `MIST_API_TOKEN` value.
- [ ] Running under `podman exec -it misthelper python MistHelper.py --menu 96`
      works identically to the Windows venv run.
- [ ] Pressing Ctrl-D (EOF) at either prompt exits cleanly with code 0 and no
      Python traceback.
