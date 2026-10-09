# Quickstart: Validate Juniper RMA Correlation

**Feature**: `3519-juniper-rma-correlation` | **Audience**: Operators and reviewers

Run these steps in order. Steps 1 and 2 need no Juniper access. Steps 3 to 5 need completed onboarding and a filled `.env` file.

## 1. Prepare the Worktree

Run the bootstrap once in the feature worktree. A new worktree has no virtual environment.

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-3519-juniper-rma'
python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## 2. Run the Offline Tests

These tests use recorded fixtures and a fake gateway. They make no network call.

```powershell
pytest tests/unit/juniper_rma -q
```

Expected result: all tests pass. The read-only boundary test passes. It proves that no write operation name appears in the client.

## 3. Check Access (Menu 301)

Set the Juniper names in `.env`. Leave `JUNIPER_LIVE_TESTS` unset for normal runs.

```powershell
python MistHelper.py --menu 301
```

| Result | Meaning | Next step |
| - | - | - |
| Pass | Settings and gateway work | Continue to step 4 |
| Missing setting | A required name is empty | Fill the name named in the message |
| Fault 707, 735, 932, or 935 | App identifier or source identifier is wrong | Check `JUNIPER_APP_ID` and `JUNIPER_CUSTOMER_SOURCE_ID` |
| Fault 753, 754, or 771 | Contact or user is not registered for the account | Check `JUNIPER_CONTACT_EMAIL` and `JUNIPER_USER_ID` |
| TLS certificate error | Corporate inspection root is missing | Set `JUNIPER_CA_BUNDLE` to a bundle that includes the corporate root (R-13) |
| Token request fails | The client ID or client secret is wrong | Check `JUNIPER_CLIENT_ID` and `JUNIPER_CLIENT_SECRET` |
| Fault 937 | The gateway rejects the authentication method | Confirm the OAuth 2.0 setup with Juniper (O-2) |

## 4. Correlate Mist Tickets (Menu 302)

```powershell
python MistHelper.py --menu 302
```

Check the outputs under `data/`:

- `JuniperCorrelation.csv` lists every Mist ticket with its match status.
- `JuniperServiceRequests.csv` and `JuniperRmaItems.csv` hold the Juniper records.
- `JuniperRunRecords.csv` holds the run summary.

Expected result: the summary line shows `status=complete`. Personal fields in the CSV files are kept in full. The run log masks them.

If the match count is zero, check the join field (O-1) before any other step. Set `JUNIPER_TICKET_KEY_FIELD` to `id` and run again. Or confirm with Juniper which Mist field holds the customer case number.

## 5. Look Up and Enrich (Menus 303 and 304)

```powershell
python MistHelper.py --menu 303
python MistHelper.py --menu 304
```

- Menu 303 needs a request number or a customer case number. An RMA lookup also needs one of those two values.
- Menu 304 takes serial numbers. It sends them in batches of 300 or fewer.

## 6. Run the Live Smoke Test (Optional)

Only run this step with a test environment. It makes read-only calls to Juniper.

```powershell
$env:JUNIPER_LIVE_TESTS = '1'
pytest tests/unit/juniper_rma -m live -q
Remove-Item Env:JUNIPER_LIVE_TESTS
```

## 7. Troubleshooting

| Symptom | Cause | Action |
| - | - | - |
| Requests slow down or fail with HTTP 429 | Rate above the Juniper limit | Lower `JUNIPER_MAX_REQUESTS_PER_SECOND` (O-3) |
| Fault 763 for a case number | The case number maps to more than one request | Use the request number from the 90-day list. |
| Fault 955 | Repeated transaction identifier | Re-run. The client sends a new identifier on each attempt. |
| Run status is `incomplete` | Retries ran out or the run stopped early | Read the reason on the summary line and run again |
| Personal data appears in a log | Masking gap | Stop the run and file an issue. Do not share the log. |
