# Quickstart: EX Hardware Inventory CSV

This guide proves the feature end to end. Run each scenario from the worktree root. Use the Python 3.15 environment of the repository. No scenario needs a production credential, except the live scenario, which is read-only and runs on one organization.

## Prerequisites

- The worktree for branch `feat/4920-ex-hardware-inventory-csv`.
- The environment from `scripts/bootstrap_worktree.py`, or the `.venv` of the main checkout.
- For the live scenario only: the variables `MIST_APITOKEN`, `MIST_HOST`, and `org_id` in the process. The loader script copies them from the `.env` file of the main checkout. It prints no value. It also sets `MISTHELPER_STANDALONE=true`, so the run writes no database.

## Scenario 1: Report rules (no network)

```powershell
python -m pytest tests/unit/ex_hardware_inventory/report -q
```

Expected: every test passes. The flattener reads a synthetic reply with the real shape: a default namespace on `chassis-inventory`, `junos:style` on `chassis`, `cli/banner`, one-space version fields, empty serial fields, disk and USB modules, and a two-member virtual chassis. The report holds one row for each item and keeps the fixed column order. A cell that starts with `=` gets an apostrophe.

## Scenario 2: Scope detection (mocked Mist)

```powershell
python -m pytest tests/unit/ex_hardware_inventory/scope -q
```

Expected: an organization token gives organization scope. An MSP login with a good organization list gives MSP scope. An MSP grant with HTTP 403 gives organization scope and one note. A refused profile stops the run. A credential with several grants and no `org_id` stops the run.

## Scenario 3: Concurrency (fake shell)

```powershell
python -m pytest tests/unit/ex_hardware_inventory/run tests/unit/websocket_streams -q -k "concurrency or hardware"
```

Expected: with 12 targets and limits of 1, 3, and 5, the peak number of open shells never exceeds the limit. An unset variable gives 3. A bad value gives 3 and one warning that names `PORTAL_WS_HARDWARE_CONCURRENCY`.

## Scenario 4: The CLI flow (mocked batch service)

```powershell
python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py tests/integration/ex_hardware_inventory -q
```

Expected: a wrong phrase opens no shell and writes no file. The right phrase runs each organization in turn. One failing switch gives one outcome row. A Ctrl+C gives a partial report. An MSP run with one failing organization finishes the others.

## Scenario 5: The Multi Site action (fake services and a fake browser)

```powershell
python -m pytest tests/unit/websocket_streams/web -q -k "csv"
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -q -k "csv"
```

Expected: the output choice **One combined CSV report** appears. A preview shows the scope line. A finished run lists `hardware/inventory.csv` in the manifest and offers the download. XML, JSON, and both runs behave as before.

## Scenario 6: Repository guards

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py tests/guardrails/test_src_domain_structure.py tests/guardrails/test_endpoint_catalog.py tests/guardrails/test_operation_registry_menu_coverage.py tests/guardrails/test_destructive_menu_docs.py tests/guardrails/test_portal_operation_coverage.py -q
python -m pytest tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py -q
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
git status --short
```

Expected: every guard passes. The generators change only the documented menu pages, and a second run changes nothing.

## Scenario 7: Live read-only run on one organization

```powershell
. "<temp folder>\live-env.ps1"
python MistHelper.py --menu 309
```

Steps:

1. Check that step 1 names one organization and the scope `organization`.
2. Check that step 2 shows the number of connected EX switches that you expect.
3. Type the phrase that the menu shows.
4. Wait for the summary line, the report path, and the `Master XML:` path.
5. Open the report. Check that the number of distinct `device_id` values equals the collected count.
6. Compare the serial numbers: the set of `item_serial_number` values in the report must equal the set of `serial-number` values in the saved XML files of the run folder.
7. Search the report, the run folder, and the log for the token. Expect zero matches.

Expected: the run ends with exit code 0, one report file, and no secret in any output. The issue gets only aggregate counts.

## Scenario 8: MSP scope (mocked only)

```powershell
python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_routing.py -q
```

Expected: the scope-aware picker returns the sites of all organizations. The checker builds each request for the right organization. One preview holds targets from several organizations and shows the organization count. The owner tests live MSP scope later.

## Scenario 9: The master XML (no network)

```powershell
python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_master_xml.py tests/unit/ex_hardware_inventory/run/test_hardware_master_xml_properties.py -q
python -m pytest tests/unit/websocket_streams/web/test_ws_hardware_master_xml.py tests/unit/websocket_streams/web/test_ws_hardware_csv.py -q
python -m pytest tests/integration/ex_hardware_inventory -q
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -q -k "master_xml or ex_hardware"
```

Expected: the document has the exact form of `contracts/report-xml.md`, byte for byte. Hostile names, hostile replies, and generated text never break it. The standard library readers, a safe parser, and the canonicalizer read it, and the schema file matches the code. The CLI writes the file next to the CSV report and removes it when a check fails. The portal publishes the file with the CSV report in one step, or publishes neither, and `format=xml` returns `application/xml`. The page shows the **Download combined XML** link only for the two outputs that hold the file.

The `lxml` test skips when `lxml` is not installed. It prints its reason.

## Scenario 10: Check a live master XML with other readers

Run a live scenario 7 first. Then check the file with readers that the tool does not use. Create a throwaway environment outside the repository, for example with `uv venv` and `uv pip install lxml xmlschema`. The commands for libxml2, `lxml`, and the .NET reader are in `documentation/ex-hardware-master-xml.md`.

Check these points. The live run of issue #4933 used a throwaway script for each group. The scripts stay outside the repository, and they print counts only.

1. The bytes: the exact first line, no byte order mark, one final line feed, strict UTF-8, and only characters that XML 1.0 allows.
2. Four readers accept the file and agree on the number of elements: the expat reader of ElementTree, SAX with namespaces, minidom, and libxml2 through `lxml` with recovery off.
3. The canonical form of libxml2 (C14N 2.0) equals the canonical form of the standard library for the same file.
4. The schema accepts the file in libxml2, in `xmlschema`, and in the .NET `XmlReader`, which also checks characters and refuses a DTD. Then `XmlDocument` and LINQ to XML load it.
5. Each embedded reply equals its saved file apart from formatting white space, and the serial numbers of the file equal the serial numbers of the saved replies.
6. The devices and statuses equal the devices and statuses of the CSV report, and the token is not in the file.
7. A control run: nine corrupted copies of the file (a control character, a wrong count, a changed serial number, an undeclared prefix, a missing required attribute, two root elements, no declaration, a truncated file, and a DTD) must each fail at least one check.

Expected: every check passes for the real file, and every corrupted copy fails.

## Scenario 11: Sign in for an MSP run (mocked tests and the owner check)

```powershell
python -m pytest tests/unit/ex_hardware_inventory/scope tests/unit/websocket_streams/live/transport/test_ws_endpoint.py tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q
python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py -q -k "msp"
```

Expected: a password login with an MSP grant gives MSP scope and the credential type `login`. A group, site, or site-group grant adds no organization. A 2FA login replays the email and the password with the code. A password login sends its cookies and no token header. Step 1 prints `Credential: interactive login (user account)`, `Scope: MSP`, and the organization count.

The owner check (issue #4925) is the only live proof. Run `python MistHelper.py --login --menu 309`, answer the prompts (cloud, email, password, 2FA code), and check the three lines of step 1. For the portal, run `python MistHelper.py --login --web-portal`, answer the same prompts in that terminal, and check the scope line of the Multi Site preview. Do not paste the code or the password anywhere.
