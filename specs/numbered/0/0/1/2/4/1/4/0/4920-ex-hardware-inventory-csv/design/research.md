# Research: EX Hardware Inventory CSV

Each decision lists what the plan chose, why, and what else the team considered. Facts come from code reads and from one local retained run of issue #4769. The research notes hold no customer value.

## R1. How the CLI runs the collection

- **Decision**: The CLI drives the same batch service layer that the portal uses. It builds `WebSocketBatchService` with its collaborators, calls `preview`, then `start`, and polls `summary` and `targets`. No Flask object is needed.
- **Rationale**: The service layer already owns target discovery, status re-check, typed confirmation binding, bounded concurrency, the verified collector, and durable artifacts. Existing tests drive these classes without Flask. The CLI adds no second collector.
- **Alternatives considered**:
  - Build a `BatchExecutionPlan` directly. It skips the preview, the limits, and the durable writer. It couples the CLI to plan internals.
  - Drive only the runner. It skips the live-session limit and the shared transport gate.
  - Use the older `src/mist/realtime/websocket` package. It serves single-device menus, and it has no bounded batch.

## R2. Where the CSV is compiled

- **Decision**: One report compiler reads the saved per-switch XML files. The portal calls it from the artifact finish step and publishes `hardware/inventory.csv` through the existing atomic publisher. The CLI calls the same compiler after each batch and writes through the standard exporter.
- **Rationale**: The portal keeps no validated document in memory, so the saved XML files are the only copy. The finish step already holds the unredacted outcomes and runs once. The publisher already stages files, replaces them atomically, and counts quota.
- **Alternatives considered**:
  - Compile at download time. It repeats work and has no durable copy.
  - Compile in the browser. It exposes raw device text to a script and cannot run for the CLI.
  - Wrap the hardware writer to collect documents in memory. It loses data on a process restart, and the durable-run rule needs files.

## R3. How the CLI handles organizations and previews

- **Decision**: The CLI runs organizations one after another, each as its own batch. It previews every organization first to show the counts and the exclusions. After one typed confirmation it re-previews each organization just before that organization starts. It runs only targets that the operator confirmed. A new target that appears after the confirmation stops that organization with a message.
- **Rationale**: A preview expires after 300 seconds and binds to one organization checker. A long MSP run exceeds that time. A sequential run also keeps the number of open shells at or below the limit. A confirmed set guards against a larger run than the operator approved.
- **Alternatives considered**:
  - Run organizations at the same time. It multiplies the open shells.
  - Reuse the first preview. It expires during a long run.

## R4. How the tool detects the credential scope

- **Decision**: The resolver calls `getSelf` and requires status 200. A profile with no `email` is an organization token. A profile with an `email` is a user credential. A grant with `scope` equal to `msp` and an `msp_id` marks an MSP login. The resolver then calls `listMspOrgs`. It chooses MSP scope only when that call succeeds with status 200 and returns organizations. A 403 gives one warning and organization scope. A failed profile read stops the run.
- **Rationale**: Mist has no token-type field. The SDK itself labels a token by the presence of `email`. The shared MSP detector reads no status, so a refused answer looks like "no MSP" (issue #4713). The new resolver checks the status. The plan does not change the shared detector, because that is a separate issue.
- **Alternatives considered**:
  - Reuse `detect_msp_privileges`. It hides refused answers.
  - Reuse the menu 308 client for discovery. It binds to that report package and logs two SDK error lines on a 403.
  - Ask the operator for the scope. It adds a prompt and a wrong choice.

## R5. The concurrency variable

- **Decision**: Add `hardware_concurrency` to `StreamSettings`. The variable is `PORTAL_WS_HARDWARE_CONCURRENCY`, with default 3 and range 1 through 5. A bad value gives the default and one warning. `limits_payload` publishes the value, so the page and the preview show it.
- **Rationale**: `StreamSettings` is the one settings object that both front ends can read. The `PORTAL_WS_*` family already uses the fall-back idiom. The Multi Site batch already validates 1 through 5. The shared transport gate allows 5 live sessions by default.
- **Alternatives considered**:
  - A new `MISTHELPER_*` variable. It starts a second settings path.
  - Fail on a bad value. It differs from every sibling setting.

## R6. How the XML becomes rows

- **Decision**: A flattener walks the validated XML. An item is an element whose local name starts with `chassis` and that is not `chassis-inventory`. The flattener matches local names only, because the namespace changes with the Junos release. A row holds the level, the path of item names, the element type, every non-item child as a field, and every attribute. The `cli/banner` text is a device-level field. The report holds the union of field names. The preferred order is name, version, part number, serial number, model number, CLEI code, description. Other fields follow in sorted order.
- **Rationale**: A retained live run shows this structure: chassis, chassis-module, chassis-sub-module, chassis-sub-sub-module, chassis-re-disk-module, and chassis-re-usb-module. Each leaf occurs at most once for each parent. A virtual chassis shows one chassis and several FPC modules. Some version fields hold one space. Some serial fields are empty. The marker `{master:n}` sits in `cli/banner`.
- **Alternatives considered**:
  - `DataProcessingUtils.flatten_dict` on JSON. It makes index keys and hyphen names, and it needs the JSON command.
  - A fixed field list. It drops fields from other models.
  - Parse the text view. It differs by model and has no field names.

## R7. CSV safety and size

- **Decision**: The report neutralizes a text cell that starts with `=`, `+`, `-`, `@`, a tab, or a carriage return by a leading apostrophe. The file uses UTF-8 text and a header row. The portal limit for saved output stays at 64 MiB for the whole run. The compiler refuses to publish a report that would pass the remaining quota.
- **Rationale**: Switch text is device-controlled. A spreadsheet can run a formula in a cell. The existing quota already guards the run folder.
- **Alternatives considered**:
  - Leave cells unchanged. It leaves the formula risk.
  - Quote every cell. Quotes do not stop a formula.

## R8. Shared admission on a workstation

- **Decision**: The CLI binds the active organization to the shared request ledger before each organization run, and it restores the earlier value after. It finds the ledger through the adapter that the session mounts. A small context manager also mutes the SDK error lines for the MSP organization list, because the tool logs one warning for that outcome.
- **Rationale**: The admission module rejects a site request when the ledger holds no organization. Nothing sets the organization after the ledger is built. A contextvar scope would not reach the worker threads of the batch. An attribute on the ledger reaches every thread. The organizations run in sequence, so one value is correct at each moment. The admission design stays unchanged.
- **Alternatives considered**:
  - Edit the admission module. It is a separate issue with its own owner.
  - Run with the ledger off. It changes the operator environment.

## R9. Menu category and confirmation

- **Decision**: Menu 309 is `resource_intensive`. The unattended sweeps skip that category. The menu requires the typed phrase `RUN <target_count> TARGETS` through `InputUtils.safe_input`.
- **Rationale**: The action opens shells on many devices. The constitution requires a typed confirmation for device command execution. The command is read-only, so the action is not `destructive`.
- **Alternatives considered**: `safe` fails the prompt guard. `interactive_safe` makes `--testinteractive` open shells.

## R10. Package placement

- **Decision**: All new code goes in one new package, `src/operations/exporting/ex_hardware_inventory/`. The parent folder holds three children now and will hold four. The package has one module (`operation.py`) and three subpackages: `scope`, `report`, and `run`. The `report` subpackage has no dependency on the WebSocket package. The portal finish step imports `report`. The `run` subpackage imports the WebSocket service layer. The package `__init__.py` files stay empty, so no import cycle forms. Edits to the guarded WebSocket files stay narrow.
- **Rationale**: The nested package guard fails when a directory passes five children. `websocket_streams` holds four children, so a fifth child would use its last slot. The menu 307 report followed the same shape under the same parent. The WebSocket structure guard limits functions to 25 lines and classes to five methods in its scoped directories, so the feature adds no code there beyond narrow edits. The repository has no import-layering guard, and mist modules already import from `operations`.
- **Alternatives considered**: `src/mist/realtime/websocket_streams/hardware_inventory/` uses the last free slot of a feature package. `src/mist/intelligence/reports` holds 18 children and cannot take another. `src/operations` holds five.

## R11. MSP scope in the portal

- **Decision**: The portal gets scope-aware collaborators. A scope-aware picker adds `hardware_sites` and routes device and status reads by site. A scope-aware checker routes `check_batch` to the per-organization checker. Both delegate to the single-organization objects in organization scope. The preset reads the scope at preview time. Every target keeps its own organization in its identity.
- **Rationale**: The batch service accepts duck-typed collaborators. The shell trigger needs only a site and a device. The status re-check at dispatch reads by site, so it works for any organization. One parent session then holds all targets, within the 1000-target limit.
- **Alternatives considered**: One parent session for each organization needs a new page flow. A portal-wide MSP mode changes generic batches.

## R12. Test strategy

- **Decision**: Synthetic fixtures copy the real structure: default namespace on `chassis-inventory`, `junos:style` on `chassis`, `cli/banner`, one-space version fields, empty serial fields, a virtual chassis, and disk and USB modules. Orchestration tests inject a fake batch service. A guard test proves the structure limits. A live smoke test proves the real path.
- **Rationale**: The tracked fixtures differ from real output. Real output stays in the ignored `data/` folder.

## R13. Live validation

- **Decision**: The live run is read-only and uses the one organization of the configured token. It runs one switch first, then the whole organization. The CSV is checked against the saved XML. The issue gets aggregate counts only.
- **Rationale**: The owner asked for live checks on this organization only. The owner tests MSP later.

## R14. What this change does not do

- It does not run `taskstoissues`. The tracking issue holds the checklist.
- It does not change the admission design or the shared MSP detector (issue #4713).
- It does not add a README menu table. Issue #4916 removed menu text from the README.
- It does not add live MSP validation.
- It does not convert the Junos XML to another vocabulary, and it does not merge the JSON replies into the master XML (issue #4933).

## R15. How the master XML stays valid (issue #4933)

- **Decision**: The builder does not concatenate strings that it did not escape. A strict, namespace-aware expat parser reads each reply and builds a small tree. One renderer writes that tree with one set of escapers. Each wrapper value goes through a cleaner that replaces each character that XML 1.0 forbids or discourages with U+FFFD, then through the attribute escaper. The wrapper elements use one namespace address and the prefix `mh`.
- **Rationale**: A string copy of a reply carries every defect of the reply into the master file, and one bad byte then breaks the whole file for the customer system. A parser-driven copy turns each defect into a refused reply, and the device shows the status `failed`. Writing the tree with one escaper gives the escaping and the namespace declarations one owner.
- **Alternatives rejected**: `xml.etree.ElementTree` as the writer renames the prefixes (`ns0`) and cannot keep the prefixes of the reply, so it fails the rule that the reply keeps its prefixes. `xml.dom.minidom` reads a DTD and can expand an entity. `lxml` is not in the lock, and a new dependency is a change of its own.
- **Decision (second pass)**: A verifier that shares no output code with the writer reads the final bytes. It checks the bytes, the characters, a strict parse, the structure, the counts, and the equality of the events of each embedded reply with the events of its source, then it runs the standard canonicalizer. The CLI also reads the file back from the disk.
- **Rationale**: A bug in the writer cannot hide from a reader that writes nothing. The event comparison is the exact meaning of "the file holds the reply".
- **Decision (white space)**: White space between the child elements of an element that holds no other text is formatting, and the writer replaces it with the indent of the file. All other white space is data and stays, as does all white space below `xml:space="preserve"`.
- **Rationale**: One indented tree is easier for a person to read, and no reader that follows the rules of XML sees a difference in the data.
- **Decision (portal)**: The two new outputs reuse the atomic publication that the CSV report uses, and the finish step compiles each report within the quota that is left. If any report fails, none is published.
- **Rationale**: A run that lists one report without the other would force the operator to guess which file is complete.
- **Decision (validation)**: The live runs check the files with readers that the tool does not use: libxml2, `xmlschema`, and the .NET reader with the schema, besides the standard library. A control run of corrupted copies proves that the checks can fail.

## R16. Validation that was not possible, and what covers the gap

- The customer parsers are not known. The schema accepts every file that the tool writes, and the live checks used four independent stacks. A parser that needs a DTD, or that rejects a namespace prefix on the wrapper elements, is outside this contract.
- No public schema covers each Junos release, so the schema leaves the reply under a lax wildcard.

## R17. How the operator signs in for an MSP run, with 2FA (FR-070, FR-071)

- **Decision**: The tool opens no sign-in step of its own. It reads the grants from the profile of the session that the launcher built (`ProfileReader`, `getSelf`). The sign-in happens at launch. The CLI uses `python MistHelper.py --login --menu 309`. The prompts come from `LoginOrchestrator`: the cloud, `Email:`, a hidden `Password:`, and `Enter 2FA code:` when `POST /api/v1/login` answers that a code is required. The portal on a workstation uses `python MistHelper.py --login --web-portal`, because `establish_mist_session` runs before the portal mode and the portal gets that session. The portal in a container reads an API token from its environment, because `wsgi.py` calls `APISession.login()`, and the SDK asks for a 2FA code with `input()`, which a container cannot answer. A token of the operator account carries the account privileges, including an MSP grant (`documentation/api/self/POST_self_apitokens.md`), and it never asks for a code.
- **Rationale**: One session serves every part of the process, the existing login is covered by a regression test of the real SDK (issue #4755), and no password or code ever reaches a web page, a log, or a file. A cookie session already opens a shell: `SessionConnectionValues.headers()` gives no header and `cookie()` gives the session cookies for a login.
- **Evidence**: The OpenAPI file gives the privilege scopes (`msp`, `org`, `orggroup`, `site`, `sitegroup`), says that `msp_id` is required for `msp` and `org_id` for `org`, gives `listMspOrgs` the one parameter `msp_id`, and gives the profile the field `session_expiry` (minutes). The two-step login is `POST /api/v1/login` and `POST /api/v1/login/two_factor`. The `listMspOrgs` call takes no `limit`, so the `limit=1000` rule does not apply.
- **Alternatives rejected**: A browser sign-in form on the operations portal needs its own specification (credential handling, the session store, the 2FA states, CSRF, rate limits, and redaction), so issue #4936 tracks it. The upgrade capture portal on port 8056 has a browser sign-in, but it is a separate application with no Multi Site action. Support for `orggroup` grants needs `GET /api/v1/msps/{msp_id}/orggroups`, and the schema does not say that an `orggroup` grant carries the `msp_id` that this call needs, so it stays out of scope.
- **Not verified live**: Nobody typed a 2FA code in this change, and no MSP account was used. The owner tests the MSP sign-in and the MSP run (issue #4925). The documentation and the mocked tests (T095 through T099) cover the code paths.
