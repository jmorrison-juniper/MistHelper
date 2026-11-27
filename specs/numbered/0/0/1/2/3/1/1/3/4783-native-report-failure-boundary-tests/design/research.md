# Research: Native Report Failure-Boundary Tests

## Method

The research used read-only sources only. GitHub reads used `gh` with the account variable set. Local git used `show`, `grep`, `ls-tree`, `cat-file`, `rev-parse`, and `hash-object`. The analyzer did not run, because brief rule 2 forbids it. The detector behavior comes from a hand trace of its source. Each claim below cites a row in the remote verification table.

## R-A. Issue Facts

The issue is open. It has the labels `bug` and `tests`. It was created on 2026-11-11 by `jmorrison-juniper`.

- The body reports five findings from the committed-change ratchet for #4773. Two are `missing_fm_empty_body` and two are `missing_fm_malformed_json`, one pair for `test_normalization.py` and one pair for `test_report.py`. One is `weak_bare_assert` for `test_contracts.py` line 59.
- The OWNER comment of 2026-11-11 reports local commits `58ab484` and `07cf3ee`. It says two findings remain for `test_report.py`, and that the cause is in the shared analyzer.
- The body names the analyzer command with `--changed-from origin/main`. CI invokes the analyzer with a scope array that carries that option (R07).
- The body names `weak_bare_assert`. The settings key is `weak_bare_truthy` (R42). The emitted rule ID is `weak_bare_assert` (R41). This record uses the emitted ID for findings and the settings key for settings.

The linked issue #4773 is open, with labels `feature`, `web-portal`, and `in-progress`. Its body names PR #4607 as the owner of `MistHelper.py`. PR #4607 merged on 2026-11-13, so that body text is stale.

## R-B. Linked Work and Chain State

A search for PRs that mention 4783 returned no result. A search for PRs that mention 4773 returned three PRs: #4619 (merged), #4607 (merged), and #4208 (open). None of them carries the chain.

The chain is four local commits on top of merge base `ac046837b2bef943f0edbcd3298456265d7014fe`:

| Commit | Subject | Local date |
| - | - | - |
| `5e3868f87` | docs: specify EX transceiver master report | 2026-11-11 15:52 -06:00 |
| `8140bb37c` | feat(websocket): add optional transceiver master report | 2026-11-11 17:51 -06:00 |
| `58ab484ba` | test(websocket): cover invalid native report boundaries | 2026-11-11 17:54 -06:00 |
| `07cf3eec5` | test(websocket): verify native decoding failure evidence | 2026-11-11 17:56 -06:00 |

GitHub returns HTTP 422 for each full SHA (R28 to R31). The compare call for the base `main` and the commit `58ab484` returns HTTP 404. Local `origin/main` equals GitHub `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The chain is not an ancestor of that head (`git merge-base --is-ancestor` exit code 1). Main has 73 commits after the merge base.

The chain adds the three hardware test modules named in the issue. It also adds `test_cli.py`, `test_native.py`, and `__init__.py`. The folder then holds six children (R15, local `ls-tree` at `58ab484`). Main holds none of these files (R15 to R19).

## R-C. Existing Record Search

No folder whose name starts with `4783-` exists under `specs\`. No file whose name starts with `4783` exists under `specs\`. The only grep hit for the number is a CSV artifact under `2448-misthelper-performance-monitoring`, which is unrelated. The DRAFT_DIR and META_DIR held no 4783 file before this run. No legacy record needs reuse.

## R-D. Route

The route comes from the base-5 expansion of 4783. The expansion has six digits: 1, 2, 3, 1, 1, 3. The script `.specify/scripts/powershell/spec-route.ps1` uses base 5 at lines 17 to 29 (R14). Padding to eight digits gives 0 0 1 2 3 1 1 3, which matches the given route. The reference record 4920 uses the same method and gives 0 0 1 2 4 1 4 0 (R26).

## R-E. Analyzer Mechanics (Hand Trace)

The pinned analyzer lives at `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` at commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (R32). The local installed copy has the same blob SHA (`git hash-object` returns `6e1da595`). The following steps describe the detector:

1. `FailureModeApplicabilityInferer.infer()` reads risk from imports. A module is in scope when an imported symbol body holds `json.loads`, a `.json()` call, or an HTTP client use.
2. `SourceDrivenCoverageSlicer(test_path, tree).source_text()` keeps only test functions for which `_calls_source` is true (R33, line 451). A call drives source when its leftmost name is a source root, or when its name is in `_source_driver_names` (R34, line 508).
3. `_collect_source_driver_names` builds that set from module-level helper functions only (R35, line 538). The code comment on that path states that only local helper functions bridge a test to source.
4. Markers are literal substrings of the kept source. The empty-body markers are `b""`, `b''`, `data=""`, and `data=''` (R38, line 39). The malformed-JSON markers are `JSONDecodeError` and `bad json` (R37, line 38).
5. The findings are emitted per module at line 1 (R39 and R40 for the rule IDs).

Applied to `test_report.py` at the chain tip, the trace gives this result:

- The module has no module-level function other than `test_` functions. The only other top-level name is `class ReportRun` at line 37 (local `git grep`, chain tip).
- The two boundary tests call `ReportRun.create`. The root name `ReportRun` is not a source root. The call name is empty for an attribute call. No helper bridges it.
- Those tests are therefore not in the coverage source. Their markers do not count. Two findings remain, as the owner comment reports.

Applied to `test_normalization.py` at the chain tip, the test functions call `InventoryNormalizer` directly. Its root is an imported source name, so they count. The markers appear in the marker-only `b""` at line 83 and in the cause assertion at line 92. The owner comment reports these findings cleared.

## R-F. Product Byte Boundary

Device output enters the product as bytes. The hardware decoder takes `raw: bytes` (`HardwareXmlSupport.Decoder.decode_output`, R22, line 156). It reaches `HardwareXmlSupport.Rules.terminal_output` (R22, line 47) through `_extract_xml` (line 171). That method checks the size (line 49), decodes with strict UTF-8 (line 52), and requires a verified prompt line (lines 58 and 59). An empty input has no prompt line, so it raises `HardwareOutputError` with the prompt message. The decoder class path is `HardwareXmlSupport.Decoder`. The command constants are `HardwareXmlPreset.COMMANDS`, with keys `xml` and `json` (local commit `8140bb37c`, `preset.py` lines 277 to 280).

Native text is `str`. The artifact writer encodes it with UTF-8 (local `artifacts.py` line 145, chain tip). The report decodes the stored bytes with strict UTF-8 and passes them to the normalizer (local `report.py` line 239). The normalizer refuses empty text with the message `The hardware response exceeds its size limit or is empty.` (local `normalization.py` line 104). It wraps malformed JSON with `The hardware JSON is malformed or ambiguous.` from the `json.loads` error (local `normalization.py` lines 75 to 82).

The stdlib `json.JSONDecodeError` class is defined at line 20 of the bundled Python 3.15 `json/decoder.py` (R45). The parser raises it with `Expecting value` at several lines of the same file.

## R-G. Test-Quality Gate Scope

CI defines the job `test_quality_gate` at line 602 (R06). A pull request run scans only the changed test files. A change to the settings file, the baseline, `ci.yml`, or `requirements-dev.txt` makes the run scan the whole suite (R07 and the job comment). The analyzer prints `gate_scope` and `gate: K new findings vs baseline`.

The CI scopes for other tools exclude the test folder:

- `MYPY_PATHS` covers `src/`, `MistHelper.py`, `wsgi.py`, and two scripts (R08). The test folder is not listed.
- `RADON_PATHS` covers `src/` and some scripts. The hardware tests are not listed (R09).
- `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` cover `src/`, `web_portal`, and entry points. They do not cover `tests/` (`ci.yml` lines 101, 104, and 107).
- `bandit -c pyproject.toml -r .` covers the repository root, so it includes the tests (R10).

## R-H. Governance Constraints

- `AGENTS.md` line 197 requires a branch from main only. The constitution at line 483 forbids a branch from another feature branch.
- The constitution requires one changelog fragment per change (Principle IV and the Documentation section). The copilot instructions limit the fragment rule to user-visible changes. The constitution controls, because it names itself the authority.
- Principle I limits each directory to five children (R03). The hardware folder has six children on the chain.
- Principle IV requires steps 10 to 12. `container-build.yml` runs only for a push that changes a product file or for a manual dispatch (R46).
- `AGENTS.md` requires a comparison of module-level names after a scripted edit. Issue #1796 records the lost-name defect. The symbol-diff command exits 1 when a file loses or adds a module-level name (R43). It prints `no module-level name changed` only when no name changed (R43, line 126). When a side is unreadable, it prints `cannot read` and returns no delta (R44).
- `documentation/quality-gates.md` lists the CI job IDs in lines 3 to 9. No symbol job appears in that list, and the document has no `symbol` match.

## R-I. Reference Record Shape

The reference record `4920-ex-hardware-inventory-csv` holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\`. `design\` holds `research.md`, `data-model.md`, `quickstart.md`, `contracts\`, and `checklists\`. Its `spec.md` headings include Clarifications, User Scenarios and Testing, Requirements, Success Criteria, Assumptions, and Non-Goals. Its `research.md` uses numbered headings from R1 to R17. Its `data-model.md` uses named headings. This record copies the section order of `spec.md` and the folder layout, with a smaller size and no contracts folder (R26).

## R-J. Document Applicability

- `.github/copilot-instructions.md` applies. It defines the local gate table and the test-quality procedure (R02).
- `.specify/memory/constitution.md` applies. It defines the principles in `plan.md` (R03).
- `documentation/quality-gates.md` applies. Its row at line 63 names the analyzer command (R12).
- `documentation/development-setup.md` applies to the test environment. Lines 37 to 41 say that a new worktree holds no `.venv` and name the bootstrap step. Lines 264 to 281 describe the browser tests, which this change does not touch.
- `documentation/architecture.md` applies only to the layer names. Lines 248 and 269 name the websocket layer. No test rule appears in it.
- `documentation/container-deployment.md` and `documentation/operator-guide.md` do not apply. Each holds zero matches for `test-quality`, `test quality`, or `tests/unit`.

## R-K. Skills

No skill was loaded. No listed local skill covers a Python test-quality change or a Junos reply format. The reply shapes are in the repository tests and the product code, so no external device behavior is claimed.

## R-L. Mist API and mistapi

Not applicable. The issue and the chain tests use synthetic values. The change makes no Mist REST call and no mistapi call. The pinned mistapi package is not used by these tests.

## Decisions

### D-1 Analyzer Blind Spot: Fix in the Test Module

- **Options**: (a) Replace the class staticmethod with a module-level source-driving helper in the test module. (b) Extend the analyzer in misthelper-devtools and bump the pin. (c) Update the baseline or the settings file. (d) Exclude `test_report.py` from the scan.
- **Chosen**: (a).
- **Reason**: The analyzer documents that only local helper functions bridge a test to source (R35). The change keeps the assertions, the product, and the gate settings the same. Option (b) is a second repository change, a new release, and a pin change. Option (c) breaks FR-009 and the baseline rule. Option (d) hides findings.
- **Risk**: A reviewer may read the helper as tuned to the analyzer. Mitigation: FR-002 and FR-006 require a real boundary, and D-3 removes the marker-only code.
- **Recommended**: (a). The devtools fix is a separate follow-up (FR-016).
- **Human decision**: no.

### D-2 Delivery Path for the Chain and the Fix

- **Options**: (1) One pull request from main with the chain and the fix. It closes #4783 and refers to #4773. (2) Hold the chain until the #4773 owner finishes, then one pull request for #4773 that includes the fix. (3) Two pull requests, the chain first and the fix second. (4) A branch stacked on the chain.
- **Chosen**: Recommended option (1). The human decides.
- **Reason**: The chain fails the gate without the fix. The fix changes files that exist only in the chain. Option (3) cannot merge, because the chain fails the required gate. Option (4) breaks AGENTS.md. Option (2) keeps main clean but delays the fix until the #4773 handover completes.
- **Risk**: Unfinished feature code reaches main. Mitigation: the CSV option stays off by default, as the #4773 body requires. The menu entry and README stay out of scope. The owner comment reports 358 passing tests and 93.98 percent hardware coverage. This record does not verify those figures.
- **Human decision**: yes. The choice sets product priority for an unfinished feature.

### D-3 Empty-Body Input

- **Options**: (a) Keep `""` and accept the finding. (b) Decode `b""` into a string, as the chain tip does. (c) Pass `b""` into `HardwareXmlSupport.Decoder.decode_output`. (d) Use a mock that produces the marker.
- **Chosen**: (c).
- **Reason**: Device output enters as bytes (R22). Option (c) tests the real boundary, and the marker matches a real input. Option (a) fails the gate. Option (b) is marker-only: `b""` decodes to the same empty string that option (a) uses. Option (d) tests no product path.
- **Risk**: The decoder reports the prompt message, not the word `empty`. Mitigation: the test asserts `HardwareOutputError` only.
- **Human decision**: no.

### D-4 Malformed-JSON Assertion

- **Options**: (a) Keep only the `json.JSONDecodeError` precondition. (b) Assert that the normalizer's error cause is `json.JSONDecodeError`. (c) Add a new error code.
- **Chosen**: (b). The report test keeps the precondition as fixture validation.
- **Reason**: Option (b) proves that the product wraps the parser error (normalization.py lines 75 to 82). Option (a) tests Python, not the product. Option (c) adds a product change, which FR-010 forbids.
- **Risk**: Low. The assertion depends on the wrapping line, which a refactor could move.
- **Human decision**: no.

### D-5 Helper Shape and Symbol Gate

- **Options**: (a) Rename the class to a module-level function `create_report_run` and add `_synthetic_identity`. (b) Keep the class and add a module-level alias. (c) Inline the setup in each of the two boundary tests.
- **Chosen**: (a).
- **Reason**: It meets the detector rule (R35). It keeps one setup path. Option (b) is a shim, which AGENTS.md forbids. Option (c) copies about 20 lines.
- **Risk**: `symbol-diff` exits 1 when the base holds the file, because `ReportRun` is lost and `create_report_run` is added (R43). CI has no symbol job. Mitigation: the output goes into the pull request body.
- **Human decision**: no.

### D-6 Logging in the Publication Helper

- **Options**: (a) Log at info level before the publication call and at debug level after it. (b) Add no logging, following the repository test convention.
- **Chosen**: (a).
- **Reason**: Constitution Principle VII is non-negotiable for generated code. The helper performs a publication action. The log text stays ASCII (Principle V).
- **Risk**: Test output gets two more lines per case. Mitigation: debug level for the second line.
- **Human decision**: no.

## Remote Verification Table

The table holds 46 rows. Each row is one check. The `Ref` column names the revision that the check used. `absent` in the blob column means no blob exists at that ref. For a chain-only claim, the line number refers to the local commit object, and the result is absent on GitHub.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | AGENTS.md holds the generic rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R02 | The repository instructions hold the local gate table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| R03 | The constitution holds Principle IV and the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| R04 | The settings file exists on main | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| R05 | The baseline exists on main | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| R06 | The test_quality_gate job starts on line 602 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 602 |
| R07 | CI invokes the analyzer with a scope array that carries --changed-from | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| R08 | MYPY_PATHS covers src and two scripts, not tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R09 | RADON_PATHS does not list the hardware tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| R10 | CI runs bandit on the repository root | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| R11 | requirements-dev.txt pins misthelper-devtools to 2239e7bd | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| R12 | The gate table row names the analyzer command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| R13 | The preflight guard exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| R14 | The route script uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R15 | The hardware test folder is absent on main and has six children on the chain | tests/unit/websocket_streams/web/hardware/ | main | absent | absent | 0 |
| R16 | The ReportRun class is at line 37 of test_report.py on the chain | tests/unit/websocket_streams/web/hardware/test_report.py | main | absent | absent | 37 |
| R17 | The empty-body case is marker-only at line 85 on the chain tip | tests/unit/websocket_streams/web/hardware/test_report.py | main | absent | absent | 85 |
| R18 | The empty-body case is marker-only at line 83 on the chain tip | tests/unit/websocket_streams/web/hardware/test_normalization.py | main | absent | absent | 83 |
| R19 | The contracts assertion compares is True at line 59 on the chain | tests/unit/websocket_streams/web/hardware/test_contracts.py | main | absent | absent | 59 |
| R20 | The native acceptance test exists on main under its old name | tests/unit/websocket_streams/web/test_hardware_native_acceptance.py | main | 176188efcafd1c9fe1f5193014995992aed7e9f0 | present | 0 |
| R21 | The native decoder file exists on main under its old name | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 0 |
| R22 | The decoder class is in preset.py on the chain, at line 156 | src/mist/realtime/websocket_streams/web/services/operations/hardware/preset.py | main | absent | absent | 156 |
| R23 | The hardware operations package is absent on main | src/mist/realtime/websocket_streams/web/services/operations/hardware/ | main | absent | absent | 0 |
| R24 | The route folder is absent on main | specs/numbered/0/0/1/2/3/1/1/3/ | main | absent | absent | 0 |
| R25 | The #4773 record is absent on main | specs/numbered/0/0/1/2/3/0/4/3/4773-transceiver-master-report/ | main | absent | absent | 0 |
| R26 | The reference record 4920 folder is present on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/ | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| R27 | make_batch_service is a module-level helper on main | tests/unit/websocket_streams/web/test_ws_web_services.py | main | d20a6c7b2f7e2f479f2d2db1e0df8265411e62ce | present | 4 |
| R28 | Commit 5e3868f87 exists on GitHub | commits/5e3868f87a716670571dbf572d3087fdaf9e3d97 | 5e3868f87a716670571dbf572d3087fdaf9e3d97 | absent | absent | 0 |
| R29 | Commit 8140bb37c exists on GitHub | commits/8140bb37cb4e84be7c298929f0ac5f9ad2308add | 8140bb37cb4e84be7c298929f0ac5f9ad2308add | absent | absent | 0 |
| R30 | Commit 58ab484ba exists on GitHub | commits/58ab484badf9656f8fe46a00cf137c1c0102d539 | 58ab484badf9656f8fe46a00cf137c1c0102d539 | absent | absent | 0 |
| R31 | Commit 07cf3eec5 exists on GitHub | commits/07cf3eec5eafbc131091fb5debf9f20036f293d9 | 07cf3eec5eafbc131091fb5debf9f20036f293d9 | absent | absent | 0 |
| R32 | SourceDrivenCoverageSlicer is defined at the pinned devtools commit | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 438 |
| R33 | source_text keeps only source-driving tests | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 451 |
| R34 | A call drives source through a source root or a driver name | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 508 |
| R35 | Only module-level helper functions bridge a test to source | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 538 |
| R36 | detect builds coverage from the slicer output | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 652 |
| R37 | The malformed-JSON marker constant lists JSONDecodeError | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 38 |
| R38 | The empty-body marker constant lists b and data empty literals | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 39 |
| R39 | The rule ID missing_fm_malformed_json is emitted | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 726 |
| R40 | The rule ID missing_fm_empty_body is emitted | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 735 |
| R41 | The bare-assert rule ID weak_bare_assert is emitted | src/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 954ff75110492c221efba929f200225ac6415f54 | present | 349 |
| R42 | The settings key missing_empty_body maps to a severity | src/misthelper_devtools/test_quality_analyzer/config.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | d8613e823501b33d0526a30b4dab5faca7797a79 | present | 41 |
| R43 | symbol-diff reports lost and added names and returns 1 | src/misthelper_devtools/symbol_diff/comparator.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | dddeb45429e5c4a77dec8806209d2d7be610753e | present | 129 |
| R44 | symbol-diff returns no delta when a side is unreadable | src/misthelper_devtools/symbol_diff/comparator.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | dddeb45429e5c4a77dec8806209d2d7be610753e | present | 144 |
| R45 | The stdlib JSONDecodeError class exists in the bundled Python 3.15 (local, outside the repository) | Python\pythoncore-3.15-64\Lib\json\decoder.py | local | ee0464318458117836fbcc9c854a0d6c734612b9 | present | 20 |
| R46 | The container-build workflow runs for product files only | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |

Notes on the table:

- R15 to R19, R22, and R28 to R31 are absent on GitHub. Their line numbers are from local git objects.
- R32 to R44 are in the pinned devtools commit. The local installed copy has identical blob SHAs for `missing_failure_mode.py`, `weak_assertion.py`, `config.py`, and `comparator.py`.
- R27 comes from `gh api repos/jmorrison-juniper/MistHelper/contents/tests/unit/websocket_streams/web/test_ws_web_services.py?ref=main`, which returns the blob SHA. Line 4 comes from the decoded body.
- R45 is local and outside the repository. The brief permits this with a local path.

## Sources

- S1. `gh issue view 4783` on 2026-11-26. Fields: body, comments, labels, state, and timestamps.
- S2. `gh issue view 4773` and `gh pr list --search 4773` on 2026-11-26.
- S3. `gh pr list --search 4783` on 2026-11-26. Result: empty list.
- S4. One `gh api` commit call for each full SHA in rows R28 to R31. Result: HTTP 422 for each. Also one compare call for the base `main` and the commit `58ab484`, result HTTP 404.
- S5. `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` with a path filter, on the head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- S6. `gh api repos/jmorrison-juniper/misthelper-devtools/git/trees/2239e7bd468fd27e40c43f2b87fcd35a2e49672b?recursive=1` with path filters.
- S7. `gh search code` in `jmorrison-juniper/misthelper-devtools`. The match URL is `https://github.com/jmorrison-juniper/misthelper-devtools/blob/2239e7bd468fd27e40c43f2b87fcd35a2e49672b/src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py`.
- S8. `gh api repos/jmorrison-juniper/misthelper-devtools/contents/src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py?ref=2239e7bd468fd27e40c43f2b87fcd35a2e49672b`, decoded from base64. The decoded file has 770 lines.
- S9. Local git objects at `58ab484`, `07cf3ee`, and `8140bb37c`, read with `git show`, `git grep`, `ls-tree`, `cat-file`, and `hash-object`.
- S10. Local installed package `.venv\Lib\site-packages\misthelper_devtools`. The dist-info `direct_url.json` names commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- S11. Local repository files: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, the four templates, `documentation/quality-gates.md`, `documentation/development-setup.md`, `documentation/architecture.md`, `documentation/container-deployment.md`, `documentation/operator-guide.md`, `.github/workflows/ci.yml`, `requirements-dev.txt`, and the settings and baseline files.
- S12. Local stdlib `Python\pythoncore-3.15-64\Lib\json\decoder.py`.
- S13. Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, local read only.
- S14. No web source was fetched. No skill was loaded.

## Unverified

- U1. The analyzer result after this change. It did not run, because brief rule 2 forbids it. The prediction is that both `test_report.py` findings clear. Reason: the markers appear in a source-driving helper path.
- U2. The current analyzer result on the chain tip. The only evidence is the OWNER comment of 2026-11-11. Reason: the analyzer did not run.
- U3. The rebase of the chain onto main. Reason: rule 3 forbids a rebase. The merge base is known, but no conflict check ran. Main has 73 commits after the base.
- U4. The `symbol-diff` result for the renamed file on a base that holds the file. Reason: no run. The rule for an unreadable side is verified (R44).
- U5. The devtools `main` branch line numbers. The pinned commit is verified. Reason: only the path presence was compared on `main`.
- U6. The unit shard duration on this machine. `copilot-instructions.md` records 1179.3 seconds on 2026-09-17. Reason: no test run allowed.
- U7. The `b""` decoder outcome on the chain tip. The inference uses lines 47 to 59 of `preset.py`. Reason: no test run allowed.
- U8. The content of the chain on GitHub. Reason: the commits are absent, so no remote read can confirm their content.
- U9. CI runtime for the pull request. Reason: no pull request exists.
- U10. The number of the devtools follow-up issue. Reason: this run cannot create issues.
- U11. The coverage and test counts in the owner comment (358 tests, 93.98 percent). Reason: no test run allowed.

## Structure Check

The record folder holds five children at the feature root: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`. The `design` folder holds four children: `research.md`, `data-model.md`, `quickstart.md`, and `checklists`. The `checklists` folder holds two children. No folder exceeds the five-child limit.
