# Phase 1 Quickstart: generateSecretFor2faVerification (Menu 96)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Contract**: [contracts/generate_secret_for2fa_verification.md](./contracts/generate_secret_for2fa_verification.md)

This quickstart shows a developer how to run the new menu item locally, what to expect
in `data/`, and which quality gates must pass before the change is committed.

## Prerequisites

- Python 3.13+ (`python --version` should report 3.13 or newer).
- Active virtual environment in the repo root: `.venv\Scripts\Activate.ps1` on Windows.
- `mistapi` 0.59+ installed (`pip install -r requirements.txt`).
- A Mist account that has API token access. **The account must be the one being enrolled
  in 2FA** -- the endpoint is account-scoped.

## Required `.env` Variables

The repo's `.env` (git-ignored) must contain:

```ini
MIST_HOST=api.mist.com           # or api.eu.mist.com, api.gc1.mist.com, etc.
MIST_API_TOKEN=<your-personal-api-token>
MIST_OUTPUT_BACKEND=sqlite       # one of csv | sqlite | arango (existing variable)
```

No new `.env` variables are introduced by this menu item.

## Expected `data/` Output

| Output mode | Files written under `data/`                                                                 |
|-------------|---------------------------------------------------------------------------------------------|
| `json`      | `data/self_two_factor_token.csv` plus row in `data/mist_data.db` table `self_two_factor_token` |
| `qrcode`    | Same CSV / SQLite row (with `two_factor_secret = NULL`) plus `data/self_two_factor_qrcode_<captured_at>.png` |

The CSV header on first run:

```text
misthelper_internal_id,captured_at,output_mode,two_factor_secret,qrcode_path,account_token_hint,mist_host,source_operation_id
```

## Example Invocation

### Interactive

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the main menu, select operation 96 (Self - Generate 2FA Setup Secret).
# Prompt: Output mode [json|qrcode] (default: json):
# Press Enter to accept json.
# Expected log lines (ASCII, no secret value shown):
#   INFO  Prompting for output mode (default json)
#   DEBUG Output mode selected: json
#   INFO  Requesting 2FA secret token for self account
#   DEBUG 2FA token response received, mode=json, secret_present=True
#   INFO  Writing self_two_factor_token row to active backend
#   DEBUG self_two_factor_token wrote 1 row
```

### Non-Interactive (--menu)

```powershell
python MistHelper.py --menu 96
# Same prompts and log lines; EOF on the prompt (e.g. piped input ending) is handled by
# safe_input() and the process exits 0 without a traceback.
```

### Non-Interactive (--test)

```powershell
python MistHelper.py --test
# Operation 96 is inside the default sweep range (not in skip list 14, 18, 63-65, 90-100).
# The test harness selects json mode automatically.
```

## End-to-End Validation

1. Run the menu item once. Confirm `data/self_two_factor_token.csv` exists and has one
   data row plus the header.
2. Run it again immediately. Confirm a new row is appended (different `captured_at`),
   not an update -- this proves the `auto_increment_with_unique` strategy is working.
3. Run with `MIST_OUTPUT_BACKEND=sqlite` and inspect:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(list(c.execute('SELECT captured_at, output_mode, mist_host FROM self_two_factor_token ORDER BY captured_at DESC LIMIT 5')))"
   ```
   The secret value is intentionally not selected here -- you can fetch it separately
   when you actually need it.
4. Tail `data/script.log`. Confirm the literal `two_factor_secret` base32 string is
   NEVER present in any log line (Principle V).
5. Run the qrcode variant:
   ```powershell
   echo qrcode | python MistHelper.py --menu 96
   ```
   Confirm a `data/self_two_factor_qrcode_*.png` file exists and the matching row's
   `two_factor_secret` column is NULL but `qrcode_path` is populated.

## Quality Gates (MUST pass before commit)

Run all three from the repo root:

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
```

All three must exit 0 with no output (or `All checks passed!` from ruff). If `black
--check` reports diff candidates, run `python -m black MistHelper.py` to auto-fix and
re-run `ruff check`.

Then exercise the menu item end-to-end:

```powershell
python MistHelper.py --test
```

The `--test` sweep must exit 0. Operation 96 must appear in the summary with status
PASSED.

## Method Outline (for reviewers)

The new method on `SelfAccountUtils` has this shape (~20 lines, <= 25 per Principle I).
Every executable line carries an inline comment per Principle VI. Action logging appears
before and after every meaningful step per Principle VII.

```python
def export_self_two_factor_token(self, output_mode=None):
    # Prompt the operator only if not provided (so --test can pass mode in)
    logging.info("Prompting for 2FA token output mode")  # action log: before prompt
    if output_mode is None:                              # allow programmatic override for --test
        raw = safe_input(                                # safe_input handles SSH/container EOF
            "Output mode [json|qrcode] (default: json): ",
            context="self_two_factor_token:output_mode",
        )
        output_mode = raw.strip().lower() or "json"      # default to json on empty input
    if output_mode not in {"json", "qrcode"}:            # validate before any API call
        logging.warning("Invalid output mode %s; defaulting to json", output_mode)
        output_mode = "json"                             # safe fallback, no early return
    logging.debug("Output mode selected: %s", output_mode)  # action log: after prompt

    logging.info("Requesting 2FA secret token for self account")  # action log: before API call
    response = mistapi.api.v1.self.mfa.generateSecretFor2faVerification(  # sole permitted SDK path
        self._mist_session,                              # APISession loaded from .env at startup
        by=("qrcode" if output_mode == "qrcode" else None),  # only send the query param when needed
    )
    logging.debug(                                       # action log: after API call (NO secret value)
        "2FA token response received, mode=%s, secret_present=%s",
        output_mode,
        bool(response.data.get("two_factor_secret")) if output_mode == "json" else False,
    )

    row = self._flatten_two_factor_response(response, output_mode)  # build one persistence row
    logging.info("Writing self_two_factor_token row to active backend")  # action log: before write
    DataExporter.write_with_format_selection(            # multi-backend persistence per FR-004
        [row],
        "self_two_factor_token",
        api_function_name="generateSecretFor2faVerification",
    )
    logging.debug("self_two_factor_token wrote 1 row")   # action log: after write
```

The private `_flatten_two_factor_response` helper assembles the row dict (including
`captured_at`, `account_token_hint`, and `mist_host`) and, when `output_mode ==
"qrcode"`, writes the PNG bytes to `data/self_two_factor_qrcode_<captured_at>.png`. It
stays under 25 lines and uses the same comment-on-every-line discipline.

## Rollback

If the menu item misbehaves in production, the operator can:

1. Disable just this menu entry by reverting the single registration line in
   `MistHelper.py` and rebuilding the container.
2. Drop the new SQLite table without affecting other backends:
   `DROP TABLE self_two_factor_token;` (SQLite) -- DataExporter recreates it next run.

No data migration is required to roll forward or back.
