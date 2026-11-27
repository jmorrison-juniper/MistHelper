# Research: Menu 243 Result File Not Found

## Scope and method

Issue #4036 reports that menu 243 output files download with HTTP 200. The Results panel still reports `Could not read the results: File not found`. This research traces the download path and the Results panel with read-only tools. It changes no repository file, runs no test, and starts no container.

Method:

- Read issue #4036, its comments, and PRs #4081 and #4615 with `gh`.
- Read the legacy record `4036-fix-nested-json-preview` in full. Verified its claims on `main`.
- Fetched the `main` tree once. It listed 11404 entries and was not truncated. The `--jq` filter did not parse in this shell, so the same response was filtered in PowerShell.
- Read file bodies through the contents API. Decoded the base64 text. Line numbers come from the decoded text.
- Compared each cited commit with `main` through the compare API.
- Hashed 12 local files with `git hash-object`. Each hash equals the remote blob SHA. Local and remote line numbers match for those files.
- Read the pinned Werkzeug 3.1.9 source in `.venv` to explain route precedence.

Result terms in the remote table:

- present: verified on the cited ref.
- absent: not found on the cited ref.
- partial: the commit exists on GitHub but is not on `main`.
- stale: current evidence contradicts the claim.

## Findings

F-01 Root cause on revision `2a48cee`. The file route (line 35) and the table route (line 77) both exist [RC-16, RC-17]. Werkzeug sorts dynamic rules by weight [`werkzeug/routing/matcher.py` lines 56-61 and 121-129]. The weight includes the argument count [`werkzeug/routing/rules.py` lines 673-682]. The table rule has two arguments, so it sorts first.

F-02 Effect of the table match. For `mib_generator/allowlist.json`, the table rule matches with table name `allowlist.json`. The table helper asks the resolver for `mib_generator`, which is a directory. The resolver returns None, and the service returns `File not found` [data_browser.py lines 114-118]. The route maps that text to HTTP 404 [data.py function `preview_table`, line 94]. The panel renders it [RC-28].

F-03 Download path. The download route has one matcher [RC-20]. It passes the same path string to the same resolver [RC-23]. A valid file therefore returns HTTP 200, as the issue reports.

F-04 Current main. The preview route has one matcher [RC-14]. No table route exists [RC-15]. Table selection runs only when the directory part ends in `.db` or `.sqlite` and resolves to a file [RC-18]. The allowlist path keeps its complete form.

F-05 Preview and download parity on main. Both routes pass the full path to `resolve_safe_path` [RC-23, RC-20]. For one path, both return the same resolver outcome. The JSON reader returns parse text or fixed text [RC-24, RC-25]. It never returns `File not found`.

F-06 Output list. PR #4081 excluded read-only MIB inputs from output evidence [RC-53, RC-66]. On main, `_finalize_output_files` keeps only names that exist under the data root [RC-26]. The allowlist is a tracked input [RC-77]. The ledger is tracked [RC-78] and also written by each run [RC-42].

F-07 File lifetime. No code path deletes files under `data/mib_generator`. The web portal unlink calls remove probe files only [local source: `web_portal/services/output_scan.py` line 240 and `web_portal/routes/dashboard.py` line 184]. This search read local files only, so UR-10 records it as unverified on the remote tree. The ledger save writes in place [RC-42]. A file that exists stays visible to `isfile`. A truncated write yields a parse error, not `File not found`. File lifetime therefore does not explain the reported text.

F-08 Data root consistency. The portal sets `DATA_DIR` from the environment, with default `data`, made absolute [RC-37]. The runner uses `Path("data")` relative to the working directory [RC-41]. The Containerfile sets `WORKDIR /app` [RC-06]. Both paths resolve to `/app/data` in the container.

F-09 Results panel. `load()` clears rows, heading, and page controls first [RC-30]. The fetch reads the JSON body of each answer [RC-32]. `renderError` prints the server message [RC-28]. The panel text therefore equals the server message.

F-10 Test coverage on main. Route tests cover nested JSON for both menu 243 paths [RC-45]. They cover nested errors [RC-46] and nested SQLite selection [RC-48]. The browser test renders nested JSON from a list that the test passes to `showForRun` [RC-51]. No published test sends the real run output list through output discovery to the route.

F-11 Unpublished regression. Commit `18ce4c8` adds `tests/e2e/web_portal/test_issue_4036_menu_243_preview.py` [RC-68, RC-69]. The file is absent on main [RC-70]. The GitHub commit-pulls API returned no pull request for the commit. The test runs the real portal, starts menu 243, checks the output list, downloads both files, and previews the ledger.

F-12 Test wiring. The unpublished test patches `runner.MibGeneratorRunner`. `MistHelper._launch_mib_generator` imports that name at call time [RC-40], so the patch applies. The test uses a fixture and routes that exist on main [RC-44, RC-34, RC-35, RC-36].

F-13 Constitution gaps in the unpublished test. Most executable lines lack inline comments. The run and fetch steps lack action logs. Principles VI and VII require both [RC-03]. The test also defines `READY_TIMEOUT_MS`, which the target module already defines at its line 36 (blob `60b1f694`, local line equal to remote).

F-14 Placement limit. `tests/e2e/web_portal` holds 32 tracked children. `tests/unit/web_portal` holds 52 [RC-79, RC-80]. Principle I forbids a new direct child under a noncompliant parent [RC-03]. The test must join an existing file.

F-15 Closure gate. The owner comments of 2026-11-09 and 2026-11-17 keep the issue open until independent verification. No live container result exists in any source. The live check is open [UR-01].

F-16 Feature selector and legacy record. `.specify/feature.json` names feature 4785 [RC-13]. This record leaves it unchanged. The legacy record documents merged PR #4615 and stays unchanged [D-09].

## Decisions

D-01 Treat the table-route defect as fixed on main.
- Alternatives: (a) redesign the routes, (b) keep PR #4615 and verify, or (c) remove the SQLite table feature.
- Chosen: keep PR #4615 and verify.
- Reason: main has one file route, no table route, and tests for each case [RC-14, RC-15, RC-45].
- Risk: a live difference. Mitigation: D-05 and the blocked path in T-MERGE.

D-02 Keep the output-list exclusion from PR #4081 unchanged.
- Alternatives: (a) move the input files out of the run directory, (b) exclude by file name only, or (c) keep the merged rule.
- Chosen: keep the merged rule.
- Reason: moving checked-in files changes runner paths and the data layout. A name-only rule is weaker than the merged rule [RC-26, RC-53].
- Risk: a later input file needs the same exclusion. The discovery test guards the current names.

D-03 Merge the unpublished test into the existing browser module.
- Alternatives: (a) add a new file under `tests/e2e/web_portal`, (b) add a unit test without a browser, or (c) add no test.
- Chosen: merge into `tests/e2e/web_portal/test_operation_results_table.py`.
- Reason: a new direct child breaks Principle I [RC-79, RC-03]. The browser step matches the Results panel check the owner requested on 2026-11-17.
- Risk: the module grows. Mitigation: T-LOCAL-GATES runs the test-quality ratchet.

D-04 Use `Relates to #4036` in the pull request body. The orchestrator closes #4036 after the live check passes.
- Alternatives: (a) `Closes #4036` as the brief default and constitution step 7 request, (b) no closing keyword, or (c) `Closes` after the live check.
- Chosen: `Relates to #4036`, then a manual close after evidence.
- Reason: the owner keeps the issue open until independent verification [F-15]. PR #4615 used the same wording [RC-67]. The close-linked-issues workflow closes on the keyword at merge [RC-02].
- Risk: this record departs from constitution step 7 on purpose. Mitigation: the orchestrator closes the issue only after the live evidence exists.

D-05 Run the live check on the deployed product container after merge.
- Alternatives: (a) add a compose test service, (b) run the portal from the host, or (c) use the deployed container after merge.
- Chosen: the deployed container after merge.
- Reason: compose defines only the `monitoring` profile [RC-11]. A test service needs a new profile, port, and naming entry. The reporter ran the product image [issue #4036 body]. Constitution step 12 already requires a deployed-image check [RC-03].
- Risk: a defect appears after merge. Mitigation: the regression test blocks the table-route layout before merge. A second cause opens a new issue from `main`.

D-06 Make no product code change for this issue.
- Alternatives: (a) add a file-first branch in the preview route, (b) remove the table branch from `preview_file`, or (c) make no code change.
- Chosen: no code change.
- Reason: F-03 to F-07 show one resolver and one path string on main. A code change adds risk without a failing path.
- Risk: an unknown second condition. Mitigation: D-05 and the blocked path.

D-07 Add the changelog fragment under the `### Changed` heading.
- Alternatives: (a) no fragment, (b) the `### Fixed` heading, or (c) the `### Changed` heading.
- Chosen: `### Changed`.
- Reason: the constitution requires one fragment per change [RC-03]. No operator-visible behavior changes, so `### Fixed` overstates the change.
- Risk: a reviewer expects no fragment. Mitigation: the fragment names the test as the only change.

D-08 Use the record slug `menu-243-result-file-not-found`.
- Alternatives: (a) reuse `fix-nested-json-preview`, or (b) use a date slug.
- Chosen: the new slug.
- Reason: the legacy folder documents merged PR #4615. Reuse would replace that history. The new slug names the open symptom.
- Risk: two records exist for one issue. The route holds two children, which Principle I allows [RC-58].

D-09 Leave the legacy record unchanged.
- Alternatives: (a) edit its stale claims, (b) delete it, or (c) leave it unchanged.
- Chosen: leave it unchanged. List its stale claims in `analysis.md`.
- Reason: the record documents merged work. The brief gives this agent verification authority, not edit authority.
- Risk: a reader trusts a stale claim. Mitigation: `analysis.md` lists each stale claim with its row.

D-10 Make no label change on issue #4036.
- Alternatives: (a) remove `needs-human-review`, (b) add a frontend label, or (c) make no change.
- Chosen: no change.
- Reason: the existing labels match the bug, web-portal, and in-progress rules [RC-02]. The `needs-human-review` label stays until a human review.
- Risk: a reviewer expects the label removed. Mitigation: T-MERGE requires a human review before merge.

## Remote verification table

Each row is one check. The row count is 80. `summary.md` and `STATUS.json` use the same count.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| RC-01 | Generic rule set exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-02 | Repository rule file exists and names the label and workflow rules | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 0 |
| RC-03 | Constitution exists and defines Principles I to VII | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| RC-04 | Spec route default width is 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-05 | CI defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-06 | Container work directory is /app | Containerfile | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 77 |
| RC-07 | Container installs requirements.txt | Containerfile | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 120 |
| RC-08 | Python floor is 3.15 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RC-09 | Werkzeug is pinned to 3.1.9 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 291 |
| RC-10 | Mist OpenAPI JSON exists for the runner default | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 0 |
| RC-11 | Compose defines only the monitoring profile | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 273 |
| RC-12 | Test-container section exists | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-13 | Feature selector names feature 4785 | .specify/feature.json | main | b86bcad085666bd0aeb3ac2244c914908dc7fa70 | present | 2 |
| RC-14 | Preview route has one file matcher | web_portal/routes/data.py | main | 8616a3034e1ac02e23dfcccb5a4872b338ef895d | present | 45 |
| RC-15 | No SQLite table route exists | web_portal/routes/data.py | main | 8616a3034e1ac02e23dfcccb5a4872b338ef895d | present | 0 |
| RC-16 | Reporter revision has the file route | web_portal/routes/data.py | 2a48cee64a261dd0b48af8167c5f3a1b5f88a1de | 7eaa93467b96c573b8c91e26dc08a1546d7b7c8d | present | 35 |
| RC-17 | Reporter revision has the table route | web_portal/routes/data.py | 2a48cee64a261dd0b48af8167c5f3a1b5f88a1de | 7eaa93467b96c573b8c91e26dc08a1546d7b7c8d | present | 77 |
| RC-18 | Nested selection keeps the full path unless a database directory holds a table | web_portal/routes/data.py | main | 8616a3034e1ac02e23dfcccb5a4872b338ef895d | present | 53 |
| RC-19 | Table helper remains for explicit table selection | web_portal/routes/data.py | main | 8616a3034e1ac02e23dfcccb5a4872b338ef895d | present | 94 |
| RC-20 | Download route has one matcher | web_portal/routes/data.py | main | 8616a3034e1ac02e23dfcccb5a4872b338ef895d | present | 110 |
| RC-21 | Browsable extensions include json | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 26 |
| RC-22 | Missing file returns File not found | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 75 |
| RC-23 | Resolver refuses paths outside the data root | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 138 |
| RC-24 | JSON read failure returns a fixed message | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 248 |
| RC-25 | JSON read failure logs exception details | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 247 |
| RC-26 | Output names are kept only when the file exists | web_portal/services/operation.py | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 1569 |
| RC-27 | Output name pattern strips the data prefix | web_portal/services/operation.py | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 1813 |
| RC-28 | Results panel shows the reported message | web_portal/static/js/operation_results.js | main | 83b976ddf22a0695cc77e79ce948491bf797ad54 | present | 229 |
| RC-29 | Preview URL encodes the selected path | web_portal/static/js/operation_results.js | main | 83b976ddf22a0695cc77e79ce948491bf797ad54 | present | 194 |
| RC-30 | Pending preview clears rows and page controls | web_portal/static/js/operation_results.js | main | 83b976ddf22a0695cc77e79ce948491bf797ad54 | present | 207 |
| RC-31 | Operations page passes output files to the Results panel | web_portal/static/js/operations.js | main | e92f687f958dcd108f1c0db30fa86511ec68b827 | present | 1174 |
| RC-32 | Response reader always returns an object | web_portal/static/js/portal.js | main | 8dd3880bb2a3c68521f5504b57ca7559288192ba | present | 42 |
| RC-33 | Data browser table URL uses the preview route | web_portal/static/js/data_preview.js | main | 092f59f31145dbd64c14d7ffb019f056fa23e099 | present | 308 |
| RC-34 | Operation run and status routes exist | web_portal/routes/operations.py | main | c7ef542129a0764a55ba18f2a1c9a2d6c5573754 | present | 142 |
| RC-35 | CSRF token meta tag exists | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 6 |
| RC-36 | Portal factory create_app exists | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 37 |
| RC-37 | DATA_DIR defaults to data and becomes absolute | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 158 |
| RC-38 | Menu 243 is registered in the registry | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 563 |
| RC-39 | Menu 243 needs no Mist API token | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 797 |
| RC-40 | Menu 243 handler imports the runner at call time | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7067 |
| RC-41 | Runner allowlist default is relative to the working directory | src/operations/hardware/mib_generator/runner.py | main | db5583d778b0ecd866bce05b82ecaaa9d2af834a | present | 31 |
| RC-42 | Ledger save writes the file in place | src/operations/hardware/mib_generator/assignment.py | main | e1b5b9cba2a9b3b46f91ef9a57be5562e5224401 | present | 410 |
| RC-43 | Ledger payload carries base_oid | src/operations/hardware/mib_generator/assignment.py | main | e1b5b9cba2a9b3b46f91ef9a57be5562e5224401 | present | 396 |
| RC-44 | Mini OpenAPI fixture exists for the unpublished test | tests/unit/prod_readiness/operations/hardware/mib_generator/generator/fixtures/mini_openapi.json | main | 641cc012e4005e06a5f9055802c7767596e90266 | present | 0 |
| RC-45 | Nested JSON route test exists | tests/unit/web_portal/test_preview_row_order.py | main | 8719183d8790f5d528f2f71a3e95fa55aa69f5fa | present | 288 |
| RC-46 | Nested JSON error test keeps the cause | tests/unit/web_portal/test_preview_row_order.py | main | 8719183d8790f5d528f2f71a3e95fa55aa69f5fa | present | 335 |
| RC-47 | JSON read error test hides the internal path | tests/unit/web_portal/test_preview_row_order.py | main | 8719183d8790f5d528f2f71a3e95fa55aa69f5fa | present | 243 |
| RC-48 | SQLite table selection test exists | tests/unit/web_portal/test_preview_row_order.py | main | 8719183d8790f5d528f2f71a3e95fa55aa69f5fa | present | 418 |
| RC-49 | Denied path test exists | tests/unit/web_portal/test_preview_row_order.py | main | 8719183d8790f5d528f2f71a3e95fa55aa69f5fa | present | 435 |
| RC-50 | Streaming preview test module exists | tests/unit/web_portal/test_data_browser_preview_streaming.py | main | f639af44e5aed814919e3c132b471c8a13cc8ff5 | present | 0 |
| RC-51 | Browser nested JSON test exists | tests/e2e/web_portal/test_operation_results_table.py | main | 60b1f694851c85ce188edadc5c25dfb33526c82c | present | 150 |
| RC-52 | Browser missing-file test exists | tests/e2e/web_portal/test_operation_results_table.py | main | 60b1f694851c85ce188edadc5c25dfb33526c82c | present | 121 |
| RC-53 | MIB input exclusion test exists | tests/unit/prod_readiness/standalone/operations/exporting/quality/test_operation_output_file_discovery.py | main | b2329800ef47d31a6c0a10d268535e7702c7aced | present | 63 |
| RC-54 | Process folder guard test exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| RC-55 | Fragment for PR #4615 has a Fixed heading | changelog.d/issue-4036-nested-json-preview.md | main | e1a924f2d5eaacd21f9e1abc6b1e292bc5c78c29 | present | 1 |
| RC-56 | changelog.d holds 335 direct children, not 272 | changelog.d | main | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | stale | 0 |
| RC-57 | specs holds 795 direct children | specs | main | 224f0aa74b2ed841dadf30dc5a20d55adb0d388b | present | 0 |
| RC-58 | Legacy record folder exists | specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview | main | dbed369ed95fc2073113beb28ec2cb0d4ad74b9e | present | 0 |
| RC-59 | Legacy design folder holds five children | specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview/design | main | bc62b78d6bfa4b8c61f17dfafd57f81d90fa149a | present | 0 |
| RC-60 | Legacy spec.md exists | specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview/spec.md | main | dc3ffedca8545ca044ebcb8704f340a0ae245b42 | present | 0 |
| RC-61 | Legacy discovery test path exists | tests/unit/test_operation_output_file_discovery.py | main | none on main | absent | 0 |
| RC-62 | Legacy path guard test path exists | tests/unit/test_data_browser_path_guard.py | main | none on main | absent | 0 |
| RC-63 | Legacy feature selector names feature 4258 | .specify/feature.json | main | b86bcad085666bd0aeb3ac2244c914908dc7fa70 | stale | 2 |
| RC-64 | Legacy plan states Python 3.13 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 23 |
| RC-65 | Legacy spec requires Closes #4036 in the validated fix | commit message of e08f4e06167a2a33e71575c6d327fa1146aaa347 | e08f4e06167a2a33e71575c6d327fa1146aaa347 | not applicable | stale | 0 |
| RC-66 | PR #4081 squash commit is on main history | commit 0eeb9a6fe8d199f99f1c30f2552d5ea263e5c870 | 0eeb9a6fe8d199f99f1c30f2552d5ea263e5c870 | not applicable | present | 0 |
| RC-67 | PR #4615 squash commit is on main history and says Relates to #4036 | commit e08f4e06167a2a33e71575c6d327fa1146aaa347 | e08f4e06167a2a33e71575c6d327fa1146aaa347 | not applicable | present | 0 |
| RC-68 | Unpublished regression commit exists | commit 18ce4c8a265e25eef846b03dc6ee4fce4ee7d4ca | 18ce4c8a265e25eef846b03dc6ee4fce4ee7d4ca | not applicable | partial | 0 |
| RC-69 | Unpublished regression test file exists on that commit | tests/e2e/web_portal/test_issue_4036_menu_243_preview.py | 18ce4c8a265e25eef846b03dc6ee4fce4ee7d4ca | 82831ff857f7d132ba5c7a839760705e817bc479 | partial | 126 |
| RC-70 | Unpublished regression test file is absent on main | tests/e2e/web_portal/test_issue_4036_menu_243_preview.py | main | none on main | absent | 0 |
| RC-71 | Reporter revision 2a48cee is on main history | commit 2a48cee64a261dd0b48af8167c5f3a1b5f88a1de | 2a48cee64a261dd0b48af8167c5f3a1b5f88a1de | not applicable | present | 0 |
| RC-72 | Legacy HEAD fb7a7d10 is on main history | commit fb7a7d10d40c89a44ccfdaf0304ec57b2fd3b02d | fb7a7d10d40c89a44ccfdaf0304ec57b2fd3b02d | not applicable | present | 0 |
| RC-73 | Legacy coverage run head 8126f033 is not on main | commit 8126f033350b61452ea518737dd94cccbc400a79 | 8126f033350b61452ea518737dd94cccbc400a79 | not applicable | partial | 0 |
| RC-74 | Legacy run 42339040613 exists with conclusion failure | actions run 42339040613 | 8126f033350b61452ea518737dd94cccbc400a79 | not applicable | present | 0 |
| RC-75 | Assessment base e0dc054d is on main history | commit e0dc054d74e0a53c074c8b08158f105eb7c08fc0 | e0dc054d74e0a53c074c8b08158f105eb7c08fc0 | not applicable | present | 0 |
| RC-76 | Remote main head is f03c6c9b | ref main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | not applicable | present | 0 |
| RC-77 | Allowlist input is tracked on main | data/mib_generator/allowlist.json | main | d014bd95a4c0dff35c804454d6720761cffb4fa5 | present | 0 |
| RC-78 | Ledger is tracked on main | data/mib_generator/oid_assignments.json | main | 883178068836b7f9e636d2ba19c87bfa59729fba | present | 0 |
| RC-79 | tests/e2e/web_portal holds 32 direct children | tests/e2e/web_portal | main | 3d492d6e0bec7e4a76925d345c095dfa44bb813e | present | 0 |
| RC-80 | tests/unit/web_portal holds 52 direct children | tests/unit/web_portal | main | 091139596e93c865ebf1f7f93cd5b7feba2ba772 | present | 0 |

Line 0 means the check is about the path, not a line. Line 126 in RC-69 is the test function definition on that commit.

## Sources

- Issue #4036: https://github.com/jmorrison-juniper/MistHelper/issues/4036 (comments of 2026-10-07 to 2026-11-17).
- PR #4081: https://github.com/jmorrison-juniper/MistHelper/pull/4081 (merged 2026-10-09).
- PR #4615: https://github.com/jmorrison-juniper/MistHelper/pull/4615 (merged 2026-11-13).
- Werkzeug 3.1.9 source, local: `.venv\Lib\site-packages\werkzeug\routing\matcher.py` lines 56-61 and 121-129. Also `rules.py` lines 608-682.
- Governing files, read in full or by range: AGENTS.md, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four `.specify/templates` files.
- Reference record shape, folder listing only: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. No content was copied.
- Local files whose hash equals the remote blob: `web_portal/routes/data.py`, `web_portal/services/data_browser.py`, `web_portal/services/operation.py`, `web_portal/static/js/operation_results.js`, `web_portal/static/js/operations.js`, `web_portal/static/js/portal.js`, `tests/unit/web_portal/test_preview_row_order.py`, `tests/e2e/web_portal/test_operation_results_table.py`, `src/operations/hardware/mib_generator/runner.py`, `src/operations/hardware/mib_generator/assignment.py`, `web_portal/app.py`, and `documentation/container-deployment.md`.
- No `web_fetch` call was made.

## Unverified

- UR-01 The live symptom at the `main` revision. No container ran, because rule 2 prohibits it.
- UR-02 The Flask dispatch order at run time. The order derives from Werkzeug source. No test ran.
- UR-03 The Werkzeug pin in the reporter revision. This analysis uses the `main` pin [RC-09] and the Containerfile install line [RC-07].
- UR-04 The sanitized browser image that the issue body links. It is a gist URL and was not fetched.
- UR-05 The pass or fail result of the unpublished test. The test was read, not run.
- UR-06 Test counts in the legacy claims, including 2,255 tests and 41 tests. No job log was read.
- UR-07 The legacy claim that `pwsh` is not installed. The environment was not checked.
- UR-08 The 2026-11-17 synthetic run. It is known only from the issue comment and the unpublished test source.
- UR-09 Whether the reporter data volume maps to `/app/data`. The issue does not state it.
- UR-10 The absence of any delete path under `data/mib_generator`. The search read local files only, not the remote tree.

## Skills

No skill was loaded. The issue path uses no Podman storage, Mist SDK, or Juniper device behavior.
