# Quickstart: EX Transceiver Master Report

This guide gives the steps to reproduce the gap, the local gate commands, and the authorized live check.

Warning: Do not commit any file under `data/`. The folder holds device data, and `.gitignore` line 95 ignores it.

## Reproduce the Gap

1. Open a terminal in the repository root.
2. Run `python MistHelper.py --menu 309` with an organization token configured.
3. Confirm the run writes native XML files and the hardware CSV report.
4. Confirm that no transceiver master CSV exists. Menu 309 does not write one.

## Run the Local Gates

Run each command from the Local gates table in `.github/copilot-instructions.md`. Each command must print its expected result.

1. Run `python -m py_compile MistHelper.py`. Expect no output.
2. Run `python -m ruff check .`. Expect `All checks passed`.
3. Run `python -m black --check .`. Expect no file that needs a change.
4. Run `python -m pytest tests/unit/export/test_pk_strategies.py`. Expect all tests to pass.
5. Run `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py`. Expect all tests to pass.
6. Run `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py`. Expect all tests to pass.
7. Run `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_export.py`. Expect all tests to pass.
8. Run `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`. Expect all tests to pass.
9. Run `python -m pytest tests/unit/test_menu_entry_metadata.py`. Expect all tests to pass.
10. Run `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py`. Expect all tests to pass.
11. Run `python -m pytest tests/unit/websocket_streams/web/test_ws_hardware_csv.py`. Expect all tests to pass.
12. Run `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py`. Expect all tests to pass.
13. Run `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py`. Expect all tests to pass.
14. Run `python -m pytest tests/guardrails`. Expect all tests to pass.
15. Run `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`. Expect each file to score 80 or above.

## Live Check (Authorized, Read Only)

The issue body authorizes read-only live testing in the configured lab organization. The operator runs this check.

Caution: The run opens one shell on each connected EX switch. The shell runs only the fixed read-only show commands. Run it only on the authorized lab organization.

1. Start `python MistHelper.py --menu 310`.
2. At the format prompt, type `BOTH` to collect both formats. Press Enter to collect XML only.
3. Read the target counts. Type the phrase `RUN <count> TARGETS` to start the run.
4. Open the transceiver master CSV in the `data/` folder.
5. Compare the serial numbers in the CSV with the serial numbers in the saved replies (SC-007).
6. Record counts only in the pull request, and never record device names or serial numbers (task T034).

## Portal Check

1. Open the WebSockets tab in the portal.
2. Select the EX hardware action.
3. Tick the transceiver master CSV checkbox. The checkbox is off by default.
4. Request a preview, then start the run.
5. Download the transceiver CSV from the run results.
6. Compare the rows with the CLI output for the same switch data.
