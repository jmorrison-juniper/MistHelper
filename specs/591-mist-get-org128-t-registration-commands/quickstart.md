# Phase 1 Quickstart: getOrg128TRegistrationCommands

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) |
**Data Model**: [data-model.md](./data-model.md) |
**Contract**: [contracts/get_org128_t_registration_commands.md](./contracts/get_org128_t_registration_commands.md)

## Goal

Run the new menu item (proposed number **96**) locally against a known
Mist org, confirm the output file lands under `data/`, and exercise the
quality gates.

## Required `.env` Variables

Populate `.env` at the repo root (git-ignored). The same `.env` already
used by every other MistHelper menu item is sufficient:

```ini
MIST_HOST=api.mist.com                # or api.eu.mist.com / api.gc1.mist.com
MIST_API_TOKEN=<your-mist-api-token>  # never commit; never log; 4096-char Mist token
MIST_ORG_ID=<your-org-uuid>           # optional but recommended for non-interactive --test runs
```

No new environment variables are introduced by this feature. The
`registration_code` returned by the API is **not** persisted in `.env`
-- it lives only in `data/org_128t_registration_commands.csv` and the
matching SQLite row.

## Expected Output

- File: `data/org_128t_registration_commands.csv`
  Header: `org_id,registration_code,conductor_cmd,router_shell_cmd,requested_ttl,requested_at_utc`
- Table: `org_128t_registration_commands` in `data/mist_data.db`
  (created automatically on first run from the registered PK strategy).
- Log lines (ASCII only, INFO and above by default):
  - `WARNING: getOrg128TRegistrationCommands: upstream endpoint is DEPRECATED; may be removed in a future Mist release`
  - `INFO: Fetching 128T registration commands for org <org_id>`
  - `INFO: Persisting 1 row via DataExporter to data/org_128t_registration_commands.csv`

## Run It Locally

### 1. Activate the venv

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Interactive invocation

```powershell
python MistHelper.py
# Select menu 96 ("Export 128T/SSR registration commands (DEPRECATED upstream)")
# When prompted:
#   org_id     -> press Enter to use $env:MIST_ORG_ID, or paste a UUID
#   ttl        -> press Enter for server default (1 year), or type e.g. 3600
#   asset_ids  -> press Enter for "all assets", or type "uuid1,uuid2,uuid3"
```

### 3. Direct invocation (automation friendly)

```powershell
python MistHelper.py --menu 96
# Same prompts as above. With MIST_ORG_ID set, blank answers proceed
# non-interactively when run from --test.
```

### 4. Test-sweep invocation

```powershell
python MistHelper.py --test
# Menu 96 is included in the default sweep (outside the
# heavy/destructive skip list 14, 18, 63-65, 90-100). The test harness
# uses MIST_ORG_ID from .env, sends blank ttl and asset_ids, and asserts
# data/org_128t_registration_commands.csv is non-empty when the upstream
# API returns a 200.
```

## Method Outline (Drives Inline Comment + Logging Density)

The implementation method on the new `SSRRegistrationExportUtils` class
follows this exact skeleton. Every executable line carries an inline
comment per Constitution VI; every meaningful step is bracketed by
INFO/DEBUG logs per Constitution VII:

```python
def export_org_128t_registration_commands(self, org_id, ttl, asset_ids):
    logging.warning(                                                # surface deprecation on every call
        "getOrg128TRegistrationCommands: upstream endpoint is DEPRECATED; "
        "may be removed in a future Mist release"
    )                                                                # WARNING per Principle V
    org_id = self._validate_uuid(org_id, "org_id")                   # reject malformed UUIDs early
    if org_id is None:                                               # validate_uuid returns None on bad input
        return                                                       # bail out without an API call
    ttl_clean = self._coerce_ttl(ttl)                                # None or 60..31_536_000
    asset_ids_clean = self._split_csv(asset_ids)                     # None or list[str]
    logging.info(                                                    # observability: before API call
        "Fetching 128T registration commands for org %s", org_id
    )                                                                # INFO per Principle VII
    response = routers_128t_module.register_cmd.getOrg128TRegistrationCommands(
        self.mist_session, org_id, ttl=ttl_clean, asset_ids=asset_ids_clean
    )                                                                # single SDK call
    payload = response.data if response and response.data else {}    # normalize empty response
    logging.debug(                                                   # observability: after API call
        "Got registration response: code_len=%d shell_cmd_len=%d conductor_cmd_len=%d",
        len(payload.get("registration_code", "") or ""),             # length only, never the code
        len(payload.get("router_shell_cmd", "") or ""),              # length only, never the cmd
        len(payload.get("conductor_cmd", "") or ""),                 # length only, never the cmd
    )                                                                # DEBUG per Principle V
    if not payload.get("registration_code"):                         # nothing to persist
        logging.warning("Empty registration response for org %s", org_id)  # WARNING and bail
        return                                                       # no DataExporter call
    row = {                                                          # one-row flatten
        "org_id": org_id,                                            # PK part 1
        "registration_code": payload.get("registration_code"),       # PK part 2
        "conductor_cmd": payload.get("conductor_cmd"),               # sensitive command bundle
        "router_shell_cmd": payload.get("router_shell_cmd"),         # sensitive command bundle
        "requested_ttl": ttl_clean,                                  # echo for audit
        "requested_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",  # audit timestamp
    }                                                                # end flatten dict
    logging.info("Persisting 1 row via DataExporter to data/org_128t_registration_commands.csv")
    DataExporter.write_with_format_selection(                        # multi-backend persistence
        [row], "org_128t_registration_commands.csv",                 # filename per Research Task 3
        api_function_name="getOrg128TRegistrationCommands",          # routes to PK strategy
    )                                                                # end write
    logging.debug("Wrote 1 row for org %s", org_id)                  # after-write summary
```

Lines: ~22 executable lines (within Principle I limits). Parameters: 4
including `self` (within the 5-parameter limit). Logical blocks: 5
(warn -> validate -> call -> flatten -> write).

## Quality Gates (Run Before Every Commit)

```powershell
python -m py_compile MistHelper.py                                   # syntax must be clean
python -m ruff check MistHelper.py                                   # lint must pass without violations
python -m black --check MistHelper.py                                # formatting must already be applied
python MistHelper.py --test                                          # menu sweep including new item 96
```

All four gates must pass before commit. If `black --check` fails, run
`python -m black MistHelper.py` once to auto-fix, then re-run the gate.

## Common Pitfalls

- **Forgetting the `mistapi` import alias for the digit-prefixed
  package**: `import 128routers` is a SyntaxError. Use
  `from mistapi.api.v1.orgs import _128routers as routers_128t_module`
  or `getattr(mistapi.api.v1.orgs, "128routers")`.
- **Echoing the registration code to stdout**: The code is sensitive.
  Print only `data/org_128t_registration_commands.csv` as the
  user-facing confirmation. Never `print(payload)`.
- **Skipping `safe_input()`**: A bare `input()` will traceback on SSH
  EOF and break the container session. Every prompt goes through
  `safe_input(..., context="org_128t_register_cmd:<field>")`.
- **Unicode in log messages**: All logs must be ASCII. Substitute
  characters such as the en dash or smart quotes with hyphen-minus and
  ASCII apostrophe before logging.
