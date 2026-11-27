# Quickstart: Validate menu 309 with an MSP login

## 1. Implementer checks (no credential, no live request)

Prepare the environment with the bootstrap in `.github/copilot-instructions.md`, section "Language and environment":

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Run these checks from the checkout root:

```powershell
git rev-parse HEAD
gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha
python -m pytest tests/unit/ex_hardware_inventory/scope/test_hardware_resolver.py
python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py
python -m pytest tests/unit/websocket_streams/live/transport/test_ws_endpoint.py
python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_publisher.py
python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_master_xml.py
python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py
```

Expected result: the two SHAs are equal. Each pytest command ends with every test passed.

## 2. Owner preparation (human-only)

1. Confirm that the checkout SHA equals the SHA of `main`. Keep the SHA for the evidence.
2. Confirm that the MSP login has at least one MSP grant.
3. Estimate the number of API calls. Compare the estimate with 5000 calls per hour (FR-007).

## 3. CLI live check (human-only)

1. Open a terminal in the checkout. Run `python MistHelper.py --login --menu 309`.
2. Answer the prompts. Type the current 2FA code when the terminal asks for it.
3. Confirm the line `  + Login successful!`. Confirm the line `  + MSP access detected: N MSP(s) available`.
4. Read step 1. Expect `  Credential: interactive login (user account)`, `  Scope: MSP`, and `  Organizations in scope: N`. If the scope is not MSP, stop. Record the cause.
5. Count the step 2 lines. The count must equal N. Read each line that says `was not read`.
6. Read the total of targets. Press Enter to cancel. Or type the phrase that step 3 shows, exactly, to start.
7. After step 4, read the `Report` line and the `Master XML` line.
8. Count the outcome rows of unread organizations:

```powershell
$csvFile = Get-ChildItem -Path data -Filter 'ExHardwareInventory_*.csv' | Sort-Object LastWriteTime | Select-Object -Last 1
Import-Csv -LiteralPath $csvFile.FullName | Where-Object { $_.record_type -eq 'device_outcome' -and $_.collection_status -eq 'failed' -and $_.site_id -eq '' } | Measure-Object | Select-Object -ExpandProperty Count
```

9. Count the organization elements with `status="failed"`:

```powershell
$xmlFile = Get-ChildItem -Path data -Filter 'ExHardwareInventory_*.xml' | Sort-Object LastWriteTime | Select-Object -Last 1
Select-String -LiteralPath $xmlFile.FullName -Pattern '<mh:organization [^>]*status="failed"' | Measure-Object | Select-Object -ExpandProperty Count
```

10. Search the four locations for each secret. Type the secret text at the prompt. The command must print no line:

```powershell
Get-ChildItem -Path data -Recurse -File | Select-String -SimpleMatch -Pattern (Read-Host 'Secret text')
```

11. Post the counts in the form of `design/contracts/live-msp-evidence.md`. Do not post a name, an identifier, a token, a password, or a code.
12. If a check fails, open a new issue that names the cause. Do not post the secret.

Warning: a posted secret cannot be removed from the issue history. Do not paste a token, a password, or a 2FA code into the issue.

## 4. Portal check (human-only)

1. Run `python MistHelper.py --login --web-portal` in a terminal. Answer the prompts in that terminal.
2. Open the address that the terminal prints in a browser. Open WebSockets, then Multi Site.
3. Open the hardware action of Multi Site. Select the output `One combined CSV report (.csv)`.
4. Read the preview scope line. It starts with `Scope: MSP,`.
5. Compare the preview count with the step 2 count of the CLI check.
6. Post a counts-only result on issue #4925.

## 5. Rollback

Caution: remove only the CSV report, the master XML file, and the run folder of that run. Remove them by exact name. Do not delete the whole `data` folder.
