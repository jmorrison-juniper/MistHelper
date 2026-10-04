# Quickstart: Client Device Fingerprint Census

## Prerequisites

1. Use the worktree `C:\Users\jmorrison\mh-fleet\3569-client-fingerprint-census`.
2. Use `C:\Users\jmorrison\mh-fleet\3569-client-fingerprint-census\.venv\Scripts\python.exe` for all Python commands.
3. Provide a Mist API token only for a manual menu run. Unit tests do not need a token.

## Validate the package

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3569-client-fingerprint-census'
C:\Users\jmorrison\mh-fleet\3569-client-fingerprint-census\.venv\Scripts\python.exe -m py_compile src\mist\intelligence\reports\client_fingerprint_census\__init__.py src\mist\intelligence\reports\client_fingerprint_census\client.py src\mist\intelligence\reports\client_fingerprint_census\model.py src\mist\intelligence\reports\client_fingerprint_census\operation.py
C:\Users\jmorrison\mh-fleet\3569-client-fingerprint-census\.venv\Scripts\python.exe -m pytest tests\unit\reports\client_fingerprint_census -q --timeout=120
```

## Manual run after integration wiring

1. Start MistHelper.
2. Select menu `289`.
3. Select one site.
4. Select one distinct field.
5. Confirm that `data\ClientFingerprintCensus.csv` exists.
6. Confirm that the console table shows no more than 20 rows.

## Expected empty result

If the API returns no rows, the console prints `The client fingerprint census is empty for this site.` The CSV file still exists with the header row.
