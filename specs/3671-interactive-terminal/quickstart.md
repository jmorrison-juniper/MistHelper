# Quickstart: Own Mist WebSocket Client and Interactive Terminal

This file tells a developer how to check the feature on a workstation.

## 1. Prepare the worktree

```powershell
python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
python -m playwright install chromium
```

## 2. Run the unit tests and the contract tests

```powershell
python -m pytest tests/unit/websocket_streams tests/contract/websocket_streams -q
```

Expected result: every test passes. The parity test reports 52 compared commands.

## 3. Run the browser journeys

```powershell
python -m pytest tests/e2e/websockets_tab -q
```

The folder holds the page journeys, the terminal journeys J1 to J22 with the review
journeys, and the performance journeys. The journeys start the portal and the fake Mist
cloud server on free local ports. The screenshots go to `test-artifacts/websockets-terminal/`.
Open each screenshot and check the terminal panel, the menu, and the dialogs.

The performance journeys print their numbers. Add `-s` to see them. Section R13 of
`research.md` records the last results.

## 4. Check the logs for secrets and keys

The journeys write the portal log to `test-artifacts/websockets-terminal/portal.log`. The
last journey scans that file. The scan fails if the log holds a test token, a test cookie, a
shell address path, a typed marker, pasted text, or terminal output.

## 5. Run the live checks

Caution: the shell runs each command on the live device. Use read-only commands only.

1. Build the local image.

   ```powershell
   podman build -t misthelper:issue3671 .
   ```

2. Start a test container in the compose group. Name it `misthelper-tmp-issue3671-live`.
   Publish the portal on a port from 9600 to 9699, bound to `127.0.0.1`.
3. Set `PORTAL_WS_ENABLE_SHELL=1` for the test container only.
4. Open a shell on "Morrison-Switch". Run `show version` and `show arp`.
5. Open a shell on "SRX-1500". Run `show arp no-resolve` and `show route summary`.
6. Run the catalog commands Show ARP and Show Route on "SRX-1500" 5 times each.
7. Run Top and Monitor Traffic on "SRX-1500" for 30 seconds each.
8. Record the shell host name only. Do not record the address path.
9. Remove the test container, its volume, and its network.

## 6. Run the owner-approved destructive journey

Warning: This journey can interrupt device traffic. Do not include it in the read-only T055
evidence. Run it only after the device owner approves the exact port.

1. Select one port that the owner approved.
2. Confirm through the Mist API that the port exists and has `up` set to false.
3. Run `show interfaces terse <port> | no-more`.
4. Continue only if the command reports that the port is administratively up and its link
   is down.
5. Confirm that the page shows the destructive-action warning.
6. Type the exact device name in the confirmation field.
7. Start the port bounce.
8. Repeat the API check and the read-only interface command after the attempt.
9. Record the before and after states separately from the T055 results.

## 7. Run the quality gates

```powershell
python -m ruff check src/mist/realtime/websocket_streams tests
python -m black --check src/mist/realtime/websocket_streams tests
python -m mypy src/mist/realtime/websocket_streams --config-file pyproject.toml
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
```
