# Research: Exported cell values stay out of DEBUG logs

Each decision lists the choice, the alternatives, the rationale, and the risk. Each code fact cites a repository path and a line. Each remote fact cites the blob SHA on `main` in the table in section "Remote verification".

## Log Statement Inventory

This table lists each log statement in the four exporter files that logs a cell value, a device value, a site address, or a table. The line numbers refer to `main`.

| Statement | Path | Line | Logged values | Decision |
| - | - | - | - | - |
| `logger.debug("Row %s written: %s", idx, row)` | `src/operations/exporting/export/data_exporter.py` | 443 | Every key and every cell value of rows 0, 1, and 2 of each CSV write | Remove (D-2) |
| `logger.debug("CSV fields determined: %s", fields)` | `src/operations/exporting/export/data_exporter.py` | 410 | The list of column names | Replace with a count (D-3) |
| `logger.debug("Enriched device %s (%s) with site info.", device.get("name", ""), device.get("mac", ""))` | `src/operations/exporting/export/org_inventory_exporter.py` | 613 | The `name` and `mac` values of every device | Replace with one count after the loop (D-5) |
| `logger.debug("\n%s", table.get_string())` in `_display_devices_summary_table` | `src/operations/exporting/export/org_inventory_exporter.py` | 652 | The `name`, `mac`, `model`, `serial`, `type`, `site_name`, `street`, `city`, `state`, `zip_code`, and `country` values of every device | Remove the table and its call (D-4) |
| `logger.debug("\n%s", table.get_string())` in `_display_gateways_summary_table` | `src/operations/exporting/export/org_inventory_exporter.py` | 766 | The `name`, `mac`, `model`, `serial`, `site_name`, `street`, `city`, `state`, `zip_code`, and `country` values of every gateway | Remove the table and its call (D-4) |
| `logging.debug("Failed to split address '%s': %s", address, exception)` | `src/operations/exporting/export/org_inventory_exporter.py` | 723 | The full site address and the exception text | Log the error type only (D-6) |
| `logging.debug("Failed to split address '%s': %s", address, exception)` | `src/operations/exporting/export/sites_by_ap_model_exporter.py` | 88 | The full site address and the exception text | Log the error type only (D-6) |
| `logger.debug("\n%s", table.get_string())` in `_display_inventory_table` | `src/operations/exporting/export/site_device_exporter.py` | 110 | Every flattened field of every inventory row | Remove the table and its call (D-4) |

The four exporter files hold more log statements. Each of them logs a count, a path, a fixed phrase, or an exception text. The count and path statements stay unchanged. Examples are `data_exporter.py` lines 374, 385, 401, 407, 412, and 529, and `org_inventory_exporter.py` lines 157, 163, 629, 630, 711, and 712. The exception text statements stay unchanged under D-8. They are `data_exporter.py` lines 121, 149, and 315, and `org_inventory_exporter.py` lines 136, 193, 327, 529, and 543 (RV-15 to RV-17, RV-32 to RV-36).

## Data Path and Log Level

- `--debug` calls `_apply_debug_log_level` (`MistHelper.py`, line 7686). The function sets the root logger to DEBUG (line 7688). It sets each file handler to DEBUG. It sets each console handler to INFO (RV-93, RV-94).
- The file handler writes `data/script.log` (`MistHelper.py`, line 147, RV-95). Each DEBUG line therefore reaches that file under `--debug`.
- The hardware report calls `DataExporter.write_with_format_selection` (`src/operations/exporting/ex_hardware_inventory/report/export.py`, line 81, RV-49). Its rows pass through `_emit_rows`, so the fix covers the EX hardware inventory report too.
- Without `--debug`, the console stays at INFO. The statements in this change are DEBUG statements, except the two INFO lines that the change adds (D-2 and D-5).

Warning: existing `data/script.log` files from earlier `--debug` runs hold cell values. Deleting those files is irreversible, so review each file before you delete it.

## Decisions

### D-1. Fix four exporter-package locations

- **Decision**: Change the four files in `src/operations/exporting/export/` that log exported values: `data_exporter.py`, `org_inventory_exporter.py`, `sites_by_ap_model_exporter.py`, and `site_device_exporter.py`.
- **Alternatives**: (a) Change only the two locations that issue #4775 names, and open two follow-up issues. (b) Change all DEBUG statements in the repository.
- **Rationale**: The issue title covers every CSV exporter debug log. The sweep found the same kind of value in the two extra files. Each fix changes one statement or one table. Option (b) reaches display code that is outside the exporter output, and that needs its own review (D-9).
- **Risk**: Two extra test files change. Each change is small, and the existing tests cover those functions.

### D-2. Replace the per-row trace with counts

- **Decision**: In `_emit_rows`, log an INFO line before the writes and a count-only DEBUG line after them. Remove the per-row trace for rows 0 to 2.
- **Alternatives**: (a) Keep the first three rows with masked values. (b) Keep the first three rows with key names only.
- **Rationale**: A masked value still shows the row shape. Key names still show the schema of the row. Counts give the operator the same post-mortem signal without a cell value.
- **Risk**: A support engineer loses the per-row trace. The counts and the write messages in `write_to_csv` remain.

### D-3. Log the field count, not the field names

- **Decision**: Change the message at `data_exporter.py` line 410 to `Determined %s CSV fields` with `len(fields)`.
- **Alternatives**: (a) Keep the list of names. (b) Remove the field line entirely.
- **Rationale**: The issue asks for field counts. A count is the smallest signal that still shows the column set.
- **Risk**: None known. The column names still appear in the CSV header.

### D-4. Remove the three summary tables

- **Decision**: Delete `_display_devices_summary_table` and `_display_gateways_summary_table` in `org_inventory_exporter.py`, and delete their calls at lines 674 and 698. Delete `_display_inventory_table` in `site_device_exporter.py`, and delete its call at line 82. Remove the PrettyTable import in each of the two modules.
- **Alternatives**: (a) Keep each table with the sensitive columns masked. (b) Keep each table at a new log level.
- **Rationale**: A masked table still shows the device list and the column layout. A new log level still prints to `data/script.log` under `--debug`. The count messages that already exist give the operator the same scale.
- **Risk**: Caution: an operator who reads the summary table loses that view. The changelog fragment names the removal.

### D-5. Replace the per-device line with counts

- **Decision**: In `_enrich_devices_with_site_info`, log an INFO line before the loop. Remove the per-device DEBUG line (line 613). Log a count-only DEBUG line after the loop.
- **Alternatives**: (a) Remove the line without a replacement. (b) Keep the line and mask the name and MAC values.
- **Rationale**: Constitution Principle VII requires an action log before and after the action. The loop is the action, so the loop carries the logs.
- **Risk**: None known. The existing INFO line for VC inheritance stays unchanged.

### D-6. Keep each parse-failure line with the error type only

- **Decision**: Keep one DEBUG line in `_split_full_address` (line 723) and one in `_split_address` (`sites_by_ap_model_exporter.py`, line 88). Each line names the error type, through `type(exception).__name__`, and omits the address.
- **Alternatives**: (a) Remove each line. (b) Count the failures for each run.
- **Rationale**: Option (a) removes the only log signal for a failed split. Option (b) changes the return type of two helpers, and the existing tests pin that return type. The repository already logs the error type alone in `src/operations/exporting/ex_hardware_inventory/operation.py` (RV-50).
- **Risk**: A DEBUG line remains for each failed split. The line holds no address.

### D-7. Accept no per-call INFO line in the two pure parse helpers

- **Decision**: `_split_full_address` and `_split_address` keep no per-call INFO line. Each helper only parses a value.
- **Alternatives**: (a) Add an INFO line before each call. (b) Count the failures in the callers and log one count line.
- **Rationale**: A per-call line prints once for each row. The issue asks for aggregate-only action logs. The deviation is recorded in `plan.md`, Complexity Tracking.
- **Risk**: A reviewer applying Principle VII strictly may reject the change. The plan records the reason, so the reviewer can decide.

### D-8. Keep warnings and errors that carry exception text

- **Decision**: Keep these statements unchanged: `data_exporter.py` lines 121, 149, and 315. Keep `org_inventory_exporter.py` lines 136, 193, 327, 529, and 543.
- **Alternatives**: (a) Log the error type only in every warning and error. (b) Remove the exception text from every warning and error.
- **Rationale**: The error rules require the exception context. AGENTS.md, section "Action logging," and constitution Principle VII both say so. These statements report failures, and the issue names DEBUG cell values. The exception text can carry a rejected value. For example, an `int()` conversion error can repeat the rejected input. Line 327 logs the exception of a `try` block that converts a device timestamp. The record does not confirm the exact message text (see "Unverified").
- **Risk**: Caution: a WARNING line can carry one rejected value. A follow-up audit issue reviews these statements.

### D-9. Keep DEBUG tables outside the exporter package

- **Decision**: Keep these statements unchanged: `src/interfaces/visualization/ui/display_utils.py` line 58, `src/mist/access/api/api_data_fetcher.py` line 428, and `src/mist/resources/device/arp_command_manager.py` line 299.
- **Alternatives**: (a) Remove every DEBUG table in the repository. (b) Mask the cell values in each of the three tables.
- **Rationale**: The three statements are not exporter output. Each one needs a separate review of its data. The issue names exporter output.
- **Risk**: Caution: each of these tables still prints under `--debug`. A follow-up issue owns that audit.

### D-10. Update one documentation row only

- **Decision**: Change the Logging row of `documentation/security.md` (line 13). Keep the flag help (`MistHelper.py`, line 7271), `documentation/cli-reference.md` (line 19), and `documentation/wiki/Troubleshooting.md` (line 27) unchanged.
- **Alternatives**: (a) Edit the three flag and help statements to say that exporter tables no longer appear. (b) Edit only the flag help text.
- **Rationale**: The three statements remain true for the other DEBUG tables (D-9). `README.md` has no debug text (RV-69). `documentation/architecture.md` (line 258) still names the same output writer.
- **Risk**: The flag help stays general. The security row states the exported-value rule.

### D-11. Name the changelog fragment after the issue

- **Decision**: Create `changelog.d/issue-4775-csv-exporter-aggregate-logging.md`. Keep that name after the pull request opens.
- **Alternatives**: (a) Name the file after the pull request number. (b) Use a date-based name.
- **Rationale**: The rule in `changelog.d/README.md` (RV-70, RV-71) names an issue file before a pull request exists. A rename creates a delete and an add, and that pair reads as a conflict.
- **Risk**: None known.

### D-12. Wait for pull request #4813

- **Decision**: Start the implementation only after pull request #4813 (issue #4776) merges. Alternatively, the owner hands over the two shared files.
- **Alternatives**: (a) Stack the branch on #4813. (b) Start now and resolve conflicts later.
- **Rationale**: Option (a) breaks the branch rule in AGENTS.md. Option (b) overlaps the `write_to_csv` lines 405 to 411 and the test class at lines 511 to 516. The `AGENTS.md` rule says that a conflict over 20 lines forces a fresh branch.
- **Risk**: The change waits. The orchestrator must watch pull request #4813.

### D-13. Add the in-progress label before the branch exists

- **Decision**: The orchestrator adds the `in-progress` label to issue #4775. The existing `security` and `MistHelper.py` labels stay.
- **Alternatives**: (a) Add no label until the pull request opens. (b) Add the label through the pull request instead.
- **Rationale**: AGENTS.md and the repository instructions require a claim label before the branch is created.
- **Risk**: The label stays after an abandoned change. The orchestrator removes it then.

### D-14. Do not purge logs and do not change the flag

- **Decision**: The change does not delete any file under `data/`. It keeps the `--debug` flag, the flag help, and the log file path.
- **Alternatives**: Add a command that purges old logs. Change the `--debug` behavior.
- **Rationale**: Deletion is irreversible, and an operator should choose it. The flag and the log path are product behavior, and FR-013 keeps them fixed.
- **Risk**: Warning: old logs keep their values until an operator removes them.

### D-15. Run symbol-diff and document the intended removals

- **Decision**: Run `symbol-diff --base origin/main <file>` for each changed Python file. The removed PrettyTable import in `org_inventory_exporter.py` and `site_device_exporter.py` is intended. The pull request body names both removals.
- **Alternatives**: (a) Keep each unused import and add a suppression comment. (b) Skip symbol-diff for the two changed files.
- **Rationale**: The unused import fails the ruff unused-import rule and the vulture rule (CI runs both, RV-81 to RV-86). A suppression comment breaks FR-015. `ci.yml` runs no symbol-diff job (RV-87), so the symbol check stays a local check.
- **Risk**: The symbol check reports two removed module-level names. The pull request body explains them.

### D-16. Add tests to four existing files

- **Decision**: Add the new regression tests to `test_data_exporter.py`, `test_org_inventory_exporter_helpers.py`, `test_sites_by_ap_model_exporter.py`, and `test_site_device_exporter.py`.
- **Alternatives**: (a) Add one new test module under `tests/unit/export/`. (b) Add a new test folder beside `tests/unit/export/`.
- **Rationale**: The folder already holds 55 entries (RV-08). Constitution Principle I forbids a new child in a noncompliant folder.
- **Risk**: The change may conflict with pull request #4813 in `test_data_exporter.py`. D-12 addresses that risk.

### D-17. Use synthetic marker values only

- **Decision**: The tests use values that start with `SYNTHETIC-MARKER`. The record and the tests hold no real export value.
- **Alternatives**: (a) Use a sample export from an operator host. (b) Use a copy of the live output.
- **Rationale**: Issue #4775 states that no private inventory is attached. A marker value proves absence in the log without a real value.
- **Risk**: None known.

### D-18. Classify the change as size M

- **Decision**: The size is M. The change touches ten paths, with four source files, four test files, one document, and one fragment. It changes no architecture.
- **Alternatives**: (a) Size S, because each change is small. (b) Size L, because the record is long.
- **Rationale**: The AGENTS.md rule requires a specification for a change that touches three files or more. The size follows the number of paths, not the number of lines.
- **Risk**: None known.

## Remote Verification

Each row is one remote check. The ref is `main` unless the row names another source. Result `present` means that the claim holds. Result `absent` means that the path or the text does not exist on the named source. Line `0` means that the check concerns a whole path or a list.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RV-01 | Route folder absent on main | `specs/numbered/0/0/1/2/3/1/0/0` | main | none | absent | 0 |
| RV-02 | No legacy 4775 record on main | `specs/**/4775-*` | main | none | absent | 0 |
| RV-03 | Sibling record 4776 absent on main | `specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/spec.md` | main | none | absent | 0 |
| RV-04 | Reference record spec exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RV-05 | Tree listing complete with 11404 entries | `git/trees/main?recursive=1` | main | none | present | 0 |
| RV-06 | Fragment folder holds 335 direct files | `changelog.d/` | main | none | present | 0 |
| RV-07 | No 4775 fragment on main | `changelog.d/issue-4775-csv-exporter-aggregate-logging.md` | main | none | absent | 0 |
| RV-08 | Test folder holds 55 direct entries | `tests/unit/export/` | main | none | present | 0 |
| RV-09 | Shared CSV writer class | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 81 |
| RV-10 | Field-name DEBUG statement | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 410 |
| RV-11 | Path resolution creates the data folder | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 419 |
| RV-12 | `_emit_rows` definition | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 438 |
| RV-13 | Per-row DEBUG statement logs cell values | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 443 |
| RV-14 | `_emit_rows` docstring names the first three rows | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 439 |
| RV-15 | Router warning keeps exception text | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 121 |
| RV-16 | Write failure error keeps exception text | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 149 |
| RV-17 | Polyglot warning keeps exception text | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 315 |
| RV-18 | Class `OrgInventoryExporter` with 39 method definitions | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 49 |
| RV-19 | PrettyTable import | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 32 |
| RV-20 | Comment names PrettyTable payloads | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 28 |
| RV-21 | Enrichment function definition | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 604 |
| RV-22 | Per-device DEBUG statement logs name and MAC | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 613 |
| RV-23 | Devices summary table definition | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 634 |
| RV-24 | Devices summary table DEBUG statement | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 652 |
| RV-25 | Devices docstring sentence about the table | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 660 |
| RV-26 | Devices summary table call | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 674 |
| RV-27 | Gateways docstring sentence about the table | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 681 |
| RV-28 | Gateways summary table call | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 698 |
| RV-29 | Gateways summary table definition | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 747 |
| RV-30 | Gateways summary table DEBUG statement | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 766 |
| RV-31 | Parse failure DEBUG statement logs the address | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 723 |
| RV-32 | Device skip warning keeps exception text | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 327 |
| RV-33 | Organization name warning keeps exception text | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 136 |
| RV-34 | Raw JSON warning keeps exception text | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 193 |
| RV-35 | Site cache warning keeps exception text | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 529 |
| RV-36 | Inventory cache warning keeps exception text | `src/operations/exporting/export/org_inventory_exporter.py` | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 543 |
| RV-37 | Class `SitesByAPModelExporter` | `src/operations/exporting/export/sites_by_ap_model_exporter.py` | main | 66d1ccaf05886d89802aa45792977480f73f37c4 | present | 23 |
| RV-38 | Split address definition | `src/operations/exporting/export/sites_by_ap_model_exporter.py` | main | 66d1ccaf05886d89802aa45792977480f73f37c4 | present | 76 |
| RV-39 | Parse failure DEBUG statement logs the site address | `src/operations/exporting/export/sites_by_ap_model_exporter.py` | main | 66d1ccaf05886d89802aa45792977480f73f37c4 | present | 88 |
| RV-40 | PrettyTable import | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 21 |
| RV-41 | Module docstring names prettytable | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 6 |
| RV-42 | INFO count line before the table | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 81 |
| RV-43 | Table call site | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 82 |
| RV-44 | Fields local used only by the table | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 79 |
| RV-45 | Table definition | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 99 |
| RV-46 | Table docstring | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 100 |
| RV-47 | Table DEBUG statement logs every flattened field | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 110 |
| RV-48 | EX hardware inventory report count line before the write | `src/operations/exporting/ex_hardware_inventory/report/export.py` | main | 114c629ebc534e97aafed664654159d0ffcf2fad | present | 80 |
| RV-49 | EX hardware inventory report writes through the shared writer | `src/operations/exporting/ex_hardware_inventory/report/export.py` | main | 114c629ebc534e97aafed664654159d0ffcf2fad | present | 81 |
| RV-50 | Error type only precedent | `src/operations/exporting/ex_hardware_inventory/operation.py` | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 92 |
| RV-51 | DEBUG table outside the exporter package | `src/interfaces/visualization/ui/display_utils.py` | main | 8afb2821a2756648d00ca7cba8b40dda959a5e07 | present | 58 |
| RV-52 | DEBUG table outside the exporter package | `src/mist/access/api/api_data_fetcher.py` | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 428 |
| RV-53 | DEBUG table outside the exporter package | `src/mist/resources/device/arp_command_manager.py` | main | 1858561b08b81b45de5101af575a2bfa722fb410 | present | 299 |
| RV-54 | Architecture names the output writer | `documentation/architecture.md` | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 258 |
| RV-55 | Class `TestEmitRows` | `tests/unit/export/test_data_exporter.py` | main | 8e91cbe472c2068183c15fca1fa350d1b76f9d34 | present | 540 |
| RV-56 | Existing `_emit_rows` test | `tests/unit/export/test_data_exporter.py` | main | 8e91cbe472c2068183c15fca1fa350d1b76f9d34 | present | 544 |
| RV-57 | Devices table test (obsolete) | `tests/unit/test_org_inventory_exporter_helpers.py` | main | c03346ae47b4a3904a221b7a5e7fc2b3e2e5f16b | present | 429 |
| RV-58 | Gateways table test (obsolete) | `tests/unit/test_org_inventory_exporter_helpers.py` | main | c03346ae47b4a3904a221b7a5e7fc2b3e2e5f16b | present | 437 |
| RV-59 | VC count test kept | `tests/unit/test_org_inventory_exporter_helpers.py` | main | c03346ae47b4a3904a221b7a5e7fc2b3e2e5f16b | present | 579 |
| RV-60 | Class `TestSplitAddress` | `tests/unit/export/test_sites_by_ap_model_exporter.py` | main | ca34a25bfd569e59281451151373bfac2f302c88 | present | 143 |
| RV-61 | Class `TestDeviceInventory` | `tests/unit/export/test_site_device_exporter.py` | main | 40d458f2a7a7ea042f5fe96947c96bec876516b9 | present | 53 |
| RV-62 | Table patch one (obsolete) | `tests/unit/export/test_site_device_exporter.py` | main | 40d458f2a7a7ea042f5fe96947c96bec876516b9 | present | 98 |
| RV-63 | Table patch two (obsolete) | `tests/unit/export/test_site_device_exporter.py` | main | 40d458f2a7a7ea042f5fe96947c96bec876516b9 | present | 121 |
| RV-64 | Class `TestDisplayInventoryTable` (obsolete) | `tests/unit/export/test_site_device_exporter.py` | main | 40d458f2a7a7ea042f5fe96947c96bec876516b9 | present | 155 |
| RV-65 | Logging row in the security policy | `documentation/security.md` | main | 42801c02559371708d4862b70b3ec4b973c38e59 | present | 13 |
| RV-66 | Debug flag text names table data | `documentation/cli-reference.md` | main | 2c171a635ea45241626110575e4b4fe9ed3e4f71 | present | 19 |
| RV-67 | Troubleshooting text names table data | `documentation/wiki/Troubleshooting.md` | main | 2790eca27de7e4b573cd076c6ab0a796eb6e8a00 | present | 27 |
| RV-68 | Quality gates job table | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 48 |
| RV-69 | README has no debug text | `README.md` | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 0 |
| RV-70 | Changelog naming rule for a pull request | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| RV-71 | Changelog naming rule for an issue | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RV-72 | Local gates section | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RV-73 | Local gates table header | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 55 |
| RV-74 | Writing style rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RV-75 | Action logging rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 104 |
| RV-76 | Constitution Five-Item Rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RV-77 | Constitution Observability rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| RV-78 | Constitution Inline Comments rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RV-79 | Constitution Action Logging rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RV-80 | Constitution fix over suppress rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 373 |
| RV-81 | CI MYPY path variable | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RV-82 | CI VULTURE path variable | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RV-83 | CI PYDOCSTYLE path variable | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RV-84 | CI INTERROGATE path variable | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RV-85 | CI INTERROGATE threshold | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 123 |
| RV-86 | CI VULTURE confidence | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 127 |
| RV-87 | CI runs no symbol-diff job | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 0 |
| RV-88 | Python version 3.15 | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RV-89 | Ruff line length 120 | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| RV-90 | Black line length 120 | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 559 |
| RV-91 | Pylint line length 120 | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 577 |
| RV-92 | Debug flag help text | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7271 |
| RV-93 | Debug level applied to handlers | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7686 |
| RV-94 | Root logger set to DEBUG | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7688 |
| RV-95 | Runtime log path kept | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 147 |
| RV-96 | Changelog policy guard exists | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RV-97 | Worktree bootstrap script exists | `scripts/bootstrap_worktree.py` | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |
| RV-98 | Test quality guidance test exists | `tests/guardrails/local_test_quality_loop/test_guidance.py` | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| RV-99 | Test quality config exists | `.github/test-quality-config.toml` | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| RV-100 | Test quality baseline exists | `.github/test-quality-baseline.json` | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| RV-101 | Menu reference generator exists | `scripts/generate_menu_wiki.py` | main | f959225275536743e93bc95d37cb015865a73d53 | present | 0 |
| RV-102 | Menu API map package exists (tree SHA, 19 entries) | `scripts/menu_api_map` | main | 02ab424ea291a237000554b4c3f9d2427c3e25a9 | present | 0 |
| RV-103 | Development requirements file exists | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 0 |
| RV-104 | Process folder baseline exists | `tests/guardrails/process_folder_baseline.json` | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RV-105 | STE linter config exists | `.ste-linter.toml` | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RV-106 | Pull request 4813 changes `write_to_csv` | pull request 4813 diff | pull request 4813 | none | present | 405 |
| RV-107 | Pull request 4813 changes the writer test class | pull request 4813 diff | pull request 4813 | none | present | 511 |
| RV-108 | Only pull request 4813 changes the four exporter files or their tests | open pull requests | open pull requests | none | present | 0 |
| RV-109 | Issue 4775 names the two locations | issue 4775 comment | issue 4775 | none | present | 0 |
| RV-110 | Issue 4773 is open and related | issue 4773 | issue 4773 | none | present | 0 |
| RV-111 | Issue 4920 is closed | issue 4920 | issue 4920 | none | present | 0 |
| RV-112 | No remote branch names 4773 or 4775 | `git/matching-refs/heads` | main | none | absent | 0 |
| RV-113 | Pinned SDK path present locally, read only | `.venv\Lib\site-packages\mistapi` | local checkout | local-not-tracked | present | 0 |
| RV-114 | Menu 11 handler wires `gateways_with_site_info` | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3863 |
| RV-115 | Menu 10 handler wires `devices_with_site_info` | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3871 |
| RV-116 | Menu 309 handler wires `ExHardwareInventoryReport.run` | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4838 |
| RV-117 | Menu 88 handler wires `SitesByAPModelExporter.export_sites_by_ap_model` | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6272 |
| RV-118 | Menu 10 is a safe read-only export in the registry | `src/foundation/support/utils/operation_registry.py` | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 680 |
| RV-119 | Menu 11 is a safe read-only export in the registry | `src/foundation/support/utils/operation_registry.py` | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 681 |
| RV-120 | Site device docstring names menus 60, 61, and 62 | `src/operations/exporting/export/site_device_exporter.py` | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 4 |

Notes on the table:

- RV-106 and RV-107 cite the hunk headers `@@ -405,7` and `@@ -511,6` of the pull request diff. Pull request #4813 adds the test lines in the second hunk.
- RV-108 covers the open pull requests that touch any of the four exporter files or their test files. Pull request #4208 touches a fragment only.
- RV-109 cites the issue comment that names `DataExporter._emit_rows` and the organization inventory exporter.
- RV-113 is a local path. It stays out of the repository tree, as FR-013 requires. No SDK call changes in this change.
- Each row count equals the row count in `design/checklists/requirements.md`, the `remote_checks` array of the status file, and the summary. The count is 120.

## Local Gate Applicability

| Gate | Applies | Command | Expected result | Reason |
| - | - | - | - | - |
| Compile | Yes | `python -m py_compile MistHelper.py` and the four changed exporter files | No output | Gate table, row "Compile" (RV-72). |
| Lint | Yes | `python -m ruff check .` | `All checks passed` | Gate table, row "Lint". |
| Format | Yes | `python -m black --check .` | No file needs a change | Gate table, row "Format". |
| Types | Yes | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` | Path list from `ci.yml`, line 93 (RV-81). |
| Tests | Yes | `python -m pytest tests/unit/export/test_data_exporter.py tests/unit/test_org_inventory_exporter_helpers.py tests/unit/export/test_sites_by_ap_model_exporter.py tests/unit/export/test_site_device_exporter.py -q` | All tests pass | Gate table, row "Tests". |
| Full tests | Yes | The two `pytest-chunks` commands in `.github/copilot-instructions.md` | One summary line for each shard | The change alters a shared writer, so the full suite runs before delivery. |
| Safe sweep | Yes | `python MistHelper.py --test` | Each safe operation completes | Applies as a precaution. The local gates table lists the sweep. Mist checks skip without a token. |
| Coverage | Yes | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | 80 percent or above | Gate table, row "Coverage". |
| Test quality | Yes | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` | Gate table, row "Test quality". Run after the commit (RV-94 to RV-96, RV-99, RV-100). |
| Complexity | Yes | `radon cc src/operations/exporting/export -j \| complexity-gate --max 10` | No block above complexity 10 | Gate table, row "Complexity". |
| Security lint | Yes | `bandit -c pyproject.toml -r src/operations/exporting/export -q` | No finding | Gate table, row "Security lint". |
| Dependency audit | No | Not run | Not applicable | No requirement changes. |
| Code quality | Yes | `pylint src/ --fail-under=9.5` | Score 9.5 or above | Gate table, row "Code quality". Line length 120 (RV-91). |
| Dead code | Yes | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding | Path list from `ci.yml`, line 101 (RV-82). |
| Docstrings | Yes | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and 90 percent or above | Path lists from `ci.yml`, lines 104 and 107 (RV-83, RV-84). |
| Menu reference | Yes | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | No changed file after the run | CI job `menu_reference_drift` runs on each pull request (RV-101, RV-102). |
| Symbols | Yes | `symbol-diff --base origin/main <file>` for each changed Python file | No unintended module-level change. The two PrettyTable removals are intended (D-15). | Gate table, row "Symbols". Not a CI job (RV-87). |
| STE | Yes | `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 <changed Markdown file>` | Each file scores 80 or above | Gate table, row "STE" (RV-105). |
| Ops portal | No | Not run | Not applicable | No file under `ops-portal/` changes. |
| Ops platform | No | Not run | Not applicable | No file under `mist-ops-platform/` changes. |
| Guardrails | Yes | `python -m pytest tests/guardrails -q` | No failure | The changelog policy guard (RV-96) and the process folder baseline (RV-104) read the changed folders. |

## Issue and Linked Work

Issue #4775 facts, from `gh issue view`:

- Title: Security: CSV exporter debug logs include exported cell values.
- State: OPEN. Labels: `security` and `MistHelper.py`. Created and last updated on 2026-11-11.
- The body states that the shared CSV exporter writes cell values to DEBUG logs. It asks for aggregate counts and synthetic values in tests.
- The body states that no private inventory is attached. It gives no reproduction steps and no error text.
- One owner comment confirms the review. It names `DataExporter._emit_rows` and the organization inventory exporter. It says that the fix needs a managed specification. The issue stays open until that route is available.

Linked work:

- `gh pr list --state all --search 4775` returns no pull request linked to issue #4775.
- The overlap check of open pull requests (RV-108) finds pull request #4813. It is open, and it links issue #4776. It changes the shared writer and its test class (RV-106, RV-107).
- Pull request #4208 is open. It changes none of the four exporter files or their test files.

## Sources

Local sources read for this record:

- `AGENTS.md` (repository root), read in full. Remote blob RV-74 and RV-75.
- `.github/copilot-instructions.md`, read in full. Remote blob RV-72 and RV-73.
- `.specify/memory/constitution.md`, read in full. Remote blob RV-76 to RV-80.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. The headings of this record follow them.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (reference record). Its shape guides the layout (RV-04).
- `documentation/quality-gates.md` (RV-68), `documentation/architecture.md` (RV-54), and `documentation/cli-reference.md` (RV-66).
- `changelog.d/README.md` (RV-70 and RV-71).

GitHub sources read through `gh`:

- Issues #4775, #4773, and #4920, the open pull request list, and pull request #4813 (files and diff).
- The remote tree of `main` (RV-05) and the contents of each file in the remote verification table.

No web source was fetched. No claim in this record depends on a web page.

## Skills, Mist API, and Containers

- No skill was loaded. The issue asks no Podman, container, or Juniper device question.
- Mist API: not applicable to the change. No endpoint call changes. The logged fields come from repository code, which this record cites by path and line. The OpenAPI file and the endpoint coverage files were not used for a claim.
- Container runtime: not applicable. The tests run on the host environment. No container starts.
- The pinned `mistapi` package stays read only in `.venv\Lib\site-packages\mistapi` (RV-113). No SDK claim depends on it.

## Unverified

- Test results: not produced. Rule 2 of the brief forbids running tests while the record is written. The red and green results come from tasks T006 and T-LOCAL-GATES.
- Runtime output with real Mist data: not produced. The record relies on code reads only.
- Python exception text: the record does not confirm the exact text that each exception can carry. Example: `int()` conversion messages can repeat the rejected input. No local source confirms this message text. D-8 depends on it.
- Pytest `caplog` behavior: relied on from existing tests (`tests/unit/export/test_site_device_exporter.py`, line 144). No external pytest page was fetched.
- Operator use of the removed summary tables: no evidence exists in the repository. The change removes that view for any operator who uses it.
- Coverage of the sweep: the sweep searched the exporting package for log statements with value-like names. It did not read every log statement in the package.
- Required checks in branch protection: not read from GitHub settings. The CI job list comes from `documentation/quality-gates.md` (RV-68) and from `ci.yml` (RV-81 to RV-87).
- Final content of pull request #4813: read at the time of this record. The owner may change it before it merges.
- Count of files in `changelog.d/`: 335 at the time of this record. The count changes when another change adds a fragment.
- Operator guide: `documentation/operator-guide.md` was searched locally for DEBUG output statements. The search found only container text at lines 151 and 153. The local copy is not remote-verified, and no claim in this record depends on it.
