# Research: Batch Parent Terminal Requests

**Issue**: #4782, "Runtime: portal batch parents request unsupported terminal endpoints"
**Date**: 2026-11-26
**Truth order**: GitHub `main` outranks local search. Each remote row cites a blob or commit SHA.

## Findings

- F-A: The defect in issue #4782 is fixed on `main`. Commit `4e81b2a4a724e29476270564be927f797def82be` added the guard at `websockets.js` line 1894 (R-17, R-53).
- F-B: Commit `4e81b2a4a7` is PR #4924. It merged on 2026-11-26 at 00:30:01Z. Issue #4932 closed at 00:36:18Z with the same symptom.
- F-C: The owner comment of 2026-11-15 describes the code before that merge. Git blame shows the guard line was added on 2026-11-25.
- F-D: The retained commit `c07cb9f8616568ca55ed5933960be2282aeadd93` exists on GitHub (R-54). It has no `multi_site` check in `isTerminalSession` (R-55).
- F-E: The retained branch name `feat/4769-ex-hardware-inventory` does not exist on GitHub (R-56). Local git holds it only as `refs/heads/feat/4769-ex-hardware-inventory`.
- F-F: The existing e2e test checks terminal reads only (R-49). The fake resize method records no call (R-41). No test checks resize requests.
- F-G: Route strings for terminal reads and resize occur only in `reader.js` line 88 and `transport.js` line 20 (R-25, R-26, R-29).
- F-H: The terminal controller is constructed once, at `websockets.js` line 1928 (R-24, R-28).
- F-I: No record for issue 4782 exists on `main` (R-15, R-16) or under `specs\` in this checkout.
- F-J: Seven pull requests were open on 2026-11-26. The owner comment counted ten. None lists the held test module or `websockets.js` (R-62, R-63).
- F-K: Issue #4782 has no linked pull request. The search for `4782` returned none.
- F-L: The constitution requires a fragment for each change (R-65). Its README exempts internal-only changes (R-66). D-6 follows the README.

## Decisions

### D-1 Keep the existing guard

- Alternatives: (a) return an empty success for a batch parent terminal read. (b) Add a second check in `selectSession` only. (c) Keep the guard in `isTerminalSession`.
- Chosen: (c).
- Reason: `isTerminalSession` decides the terminal branch in `selectSession` (R-19). Other callers read the same predicate, so one guard covers each path. The server keeps its 409 contract (R-37).
- Risk: A later edit removes the guard. The regression tests in FR-005 detect that change.

### D-2 Assert request URLs with a request listener

- Alternatives: (a) match console text that contains `409`. (b) Register a response listener for status 409. (c) Register a request listener for session route URLs.
- Chosen: (c).
- Reason: The page cannot fail on a request that it never starts. The URLs match the two routes that the issue names. Console wording depends on the browser version, which this record does not verify.
- Risk: A route rename makes the substring filter miss the new URL. The existing `terminal_reads` assertion stays as a second check.

### D-3 Add one reload test

- Alternatives: (a) extend the batch parent test with a reload. (b) Add a second test for the reload. (c) Add no reload test.
- Chosen: (b).
- Reason: The restore path calls `selectSession` (R-21) and shows the batch progress panel (R-22). A separate test names one journey. Option (c) leaves the restore path unchecked.
- Risk: The websockets-tab shard runs about two seconds longer.

### D-4 Do not reuse the retained commit

- Alternatives: (a) merge `c07cb9f8`. (b) Cherry-pick its test hunk. (c) Leave the retained branch unchanged.
- Chosen: (c).
- Reason: The commit changes server files `live/sessions/record/session.py` and `web/services/operations/sessions.py`. It also removes the guard (R-55). A cherry-pick needs the ownership hold released first.
- Risk: The unpublished #4773 work conflicts with `main` when it resumes. The owner rebases that work before it merges.

Caution: Merging `c07cb9f8` removes the guard from `isTerminalSession`. Revert that merge to restore the guard.

Warning: Deleting `refs/heads/feat/4769-ex-hardware-inventory` can make commit `c07cb9f8` unreachable. Keep that ref until the owner releases the hold.

### D-5 Edit the existing e2e module after the owner releases the hold

- Alternatives: (a) create a new test module with copied fixtures. (b) create a new test module that imports fixtures from the held module. (c) Edit the existing module after release.
- Chosen: (c).
- Reason: The fixtures and helpers exist only in `tests/e2e/websockets_tab/test_websockets_page.py` (R-39, R-43, R-44, R-45). Copying them duplicates the setup code. Importing from a test module couples the new module to the held file.
- Risk: A merge conflict occurs if #4773 resumes first. The release check T001 runs before the edit, and the edit stays small.

### D-6 Add no changelog fragment

- Alternatives: (a) add `changelog.d/issue-4782-batch-parent-terminal-requests.md`. (b) Add no fragment and state the reason in the pull request body.
- Chosen: (b).
- Reason: The constitution says each change adds a fragment (R-65). Its full rule defers to `changelog.d/README.md`, which exempts an internal-only change (R-66). This change is test-only and changes no user-visible behavior.
- Risk: A reviewer reads the rule differently. The pull request body states the exemption, so the reviewer can ask for a fragment.

### D-7 Keep the server contract

- Alternatives: (a) return HTTP 200 for a terminal request on a batch parent. (b) Keep code `not_terminal` with HTTP 409.
- Chosen: (b).
- Reason: The 409 response shows that the client sent a wrong request. A 200 response hides the client defect. Code `not_terminal` maps to HTTP 409 (R-37).
- Risk: None for this change.

### D-8 Run the staging smoke only after a credential decision

HUMAN-DECISION-REQUIRED: The owner selects the credential source and the staging organization for a live smoke test.

- Alternatives: (a) Run a live staging smoke with a credential source that the owner approves. (b) Skip the live smoke and rely on the e2e tests.
- Chosen: (b) until the owner selects a credential source.
- Reason: Credential policy in AGENTS.md section Secrets requires an owner decision. The fake-service tests cover the client path. The live messages route stays unverified (U-2).
- Risk: The live behavior of the messages route for a batch parent stays unverified.

### D-9 Close the issue with the pull request

- Alternatives: (a) Close now as fixed by PR #4924. (b) Close when the pull request merges. (c) Keep the issue open until #4773 resolves.
- Chosen: (b).
- Reason: The resize path has no regression test yet (F-F). Closing now skips that check. Keeping the issue open after the merge adds no value, because the symptom no longer reproduces on `main`.
- Risk: Low. The pull request body contains `Closes #4782`.

## Remote verification

Legend:

- Ref `main` means the tree or the contents at `main`. A commit SHA means the contents at that commit.
- Ref `commits-api`, `compare-api`, `git-ref-api`, and `pr-list` name the GitHub call or list used.
- Result `present` means that the searched item exists. Result `absent` means that it does not exist.
- Line 0 means the claim concerns the whole file, folder, or object.
- Blob or commit column holds a blob SHA for a file, a commit SHA for a commit row, or `none` when no object exists.

Every row maps one-to-one to the `remote_checks` array in `META_DIR\4782-STATUS.json`. The row count is 68.

| No. | Claim | Path | Ref | Blob or commit | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Agent rules file exists on main | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R-02 | Repository rules file exists on main | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 0 |
| R-03 | Constitution file exists on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| R-04 | Spec template exists on main | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R-05 | Plan template exists on main | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R-06 | Tasks template exists on main | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R-07 | Checklist template exists on main | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R-08 | Quality gates document lists the playwright gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 68 |
| R-09 | Development setup states that the bootstrap downloads Chromium | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 265 |
| R-10 | Mist OpenAPI file exists on main and grep found no portal route | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 0 |
| R-11 | CI shard websockets-tab runs tests/e2e/websockets_tab | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 797 |
| R-12 | E2E shard partition guard exists on main | tests/guardrails/test_e2e_shard_partition.py | main | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | present | 1 |
| R-13 | WebSocket transport policy guard class exists on main | tests/guardrails/test_websocket_transport_constitution.py | main | 447306b0a09400daabf79987e2b1a97f6430d951 | present | 44 |
| R-14 | Reference record spec exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-15 | Route parent for this record is absent on main | specs/numbered/0/0/1/2/3/1/1/2/ | main | none | absent | 0 |
| R-16 | No folder whose name starts with 4782- exists under specs | specs/ | main | none | absent | 0 |
| R-17 | Guard returns false when session mode is multi_site | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1894 |
| R-18 | selectSession has the batch parent branch | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1857 |
| R-19 | selectSession gates the terminal branch with isTerminalSession | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1884 |
| R-20 | selectSession starts message polling for non-terminal sessions | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1890 |
| R-21 | Restore path calls selectSession for the saved session | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1851 |
| R-22 | Restore path shows the batch progress panel for a batch parent | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1862 |
| R-23 | showTerminalSession is called once | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1885 |
| R-24 | TerminalController is constructed in showTerminalSession | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1928 |
| R-25 | Terminal read route string is built in reader.js | src/mist/realtime/websocket_streams/web/static/terminal/controller/reader.js | main | f92115420acf8c221eaf8175b0e580093a710c67 | present | 88 |
| R-26 | Resize route string is built in transport.js | src/mist/realtime/websocket_streams/web/static/terminal/controller/transport.js | main | 658a18f38724972ed2ef470430dded176918295f | present | 20 |
| R-27 | Resize starts with the terminal controller | src/mist/realtime/websocket_streams/web/static/terminal/controller/controller.js | main | bba8c65c7d508776e97b382329f1e534337e0d78 | present | 104 |
| R-28 | Terminal folder holds no other TerminalController construction | src/mist/realtime/websocket_streams/web/static/terminal/ | main | none | absent | 0 |
| R-29 | Resize and terminal route strings occur only in reader.js and transport.js | src/mist/realtime/websocket_streams/web/static/terminal/ | main | none | present | 0 |
| R-30 | Terminal read route is registered | src/mist/realtime/websocket_streams/web/blueprint/registry.py | main | d984a6fb5b3e63ec9778459969a07fc621d3ca80 | present | 83 |
| R-31 | Resize route is registered for POST | src/mist/realtime/websocket_streams/web/blueprint/registry.py | main | d984a6fb5b3e63ec9778459969a07fc621d3ca80 | present | 86 |
| R-32 | Messages route passes the request to the message service | src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py | main | 2b94e1d02056c38e7e0a21342f08f036b97a2d05 | present | 35 |
| R-33 | Message service read method exists | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 1009 |
| R-34 | Terminal gateway raises not_terminal for a non-terminal session | src/mist/realtime/websocket_streams/live/terminal/gateway.py | main | 24011b91d8333362a2ecd358a2586421eb51ed5e | present | 68 |
| R-35 | Input context calls the terminal lookup for resize | src/mist/realtime/websocket_streams/live/terminal/gateway.py | main | 24011b91d8333362a2ecd358a2586421eb51ed5e | present | 73 |
| R-36 | Resize gateway returns the accepted size | src/mist/realtime/websocket_streams/live/terminal/gateway.py | main | 24011b91d8333362a2ecd358a2586421eb51ed5e | present | 176 |
| R-37 | not_terminal maps to HTTP 409 | src/mist/realtime/websocket_streams/intake/fields/error.py | main | a509d72dee9a9249dc5e992498a2b93f76f7cfd4 | present | 22 |
| R-38 | Server sets mode multi_site on the batch session payload | src/mist/realtime/websocket_streams/live/sessions/record/session.py | main | b2efe313dae8c46817e9826e2851acb93227536e | present | 106 |
| R-39 | Fake services class exists in the e2e module | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 88 |
| R-40 | Fake terminal read records each session it reads | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 247 |
| R-41 | Fake resize returns the size and records no call | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 273 |
| R-42 | Fake batch payload sets mode multi_site | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 474 |
| R-43 | fake_services fixture exists | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 690 |
| R-44 | websocket_portal fixture exists | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 703 |
| R-45 | open_page helper exists | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 753 |
| R-46 | start_hardware_batch helper exists | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 1031 |
| R-47 | Reload test for the hardware CSV table exists | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 1548 |
| R-48 | Batch parent test exists | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 1562 |
| R-49 | Batch parent test asserts no terminal read | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 1569 |
| R-50 | Resize journey test test_j5_resize exists | tests/e2e/websockets_tab/test_websockets_terminal.py | main | a7c66602dd25101c02f1fc7506fc63e9b3b74eca | present | 226 |
| R-51 | not_terminal is a parametrized case in the terminal test module | tests/e2e/websockets_tab/test_websockets_terminal.py | main | a7c66602dd25101c02f1fc7506fc63e9b3b74eca | present | 749 |
| R-52 | Main head commit | refs/heads/main | git-ref-api | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-53 | Guard commit 4e81b2a4a7 is an ancestor of main | commits/4e81b2a4a724e29476270564be927f797def82be | compare-api | 4e81b2a4a724e29476270564be927f797def82be | present | 0 |
| R-54 | Retained commit c07cb9f8 exists on GitHub | commits/c07cb9f8616568ca55ed5933960be2282aeadd93 | commits-api | c07cb9f8616568ca55ed5933960be2282aeadd93 | present | 0 |
| R-55 | Retained isTerminalSession at line 1652 has no multi_site check | src/mist/realtime/websocket_streams/web/static/websockets.js | c07cb9f8616568ca55ed5933960be2282aeadd93 | 696c5d52b198e1d1bd86869a35567c71640a1395 | present | 1652 |
| R-56 | Retained branch feat/4769-ex-hardware-inventory exists on GitHub | refs/heads/feat/4769-ex-hardware-inventory | git-ref-api | none | absent | 0 |
| R-57 | Commit 8140bb3 exists on GitHub | commits/8140bb3 | commits-api | none | absent | 0 |
| R-58 | Commit 58ab484 exists on GitHub | commits/58ab484 | commits-api | none | absent | 0 |
| R-59 | Commit 07cf3ee exists on GitHub | commits/07cf3ee | commits-api | none | absent | 0 |
| R-60 | Commit edc12d5 exists on GitHub | commits/edc12d5 | commits-api | none | absent | 0 |
| R-61 | Owner-cited HEAD commit 2a6a5844 exists on GitHub | commits/2a6a5844698aeb180fea353e0243034890774565 | commits-api | 2a6a5844698aeb180fea353e0243034890774565 | present | 0 |
| R-62 | No open pull request lists the held e2e test module | tests/e2e/websockets_tab/test_websockets_page.py | pr-list | none | absent | 0 |
| R-63 | No open pull request lists websockets.js | src/mist/realtime/websocket_streams/web/static/websockets.js | pr-list | none | absent | 0 |
| R-64 | selectSession stops the terminal controller before it selects a session | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 1855 |
| R-65 | Constitution says each change MUST add one unique changelog fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-66 | Changelog README exempts an internal-only change from a fragment | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-67 | Route parent specs/numbered/0/0/1/2/3/1 holds children 0, 2, and 4 on main | specs/numbered/0/0/1/2/3/1/ | main | none | present | 0 |
| R-68 | CI type, dead-code, docstring, and interrogate path variables omit the tests folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 0 |

Row count: 68. The `remote_checks` count in STATUS and the count in `summary.md` both equal 68.

## Sources

Local (read-only):

- `AGENTS.md`: read in full. Sections used: Your role, Writing style, Code quality, Git flow, Specifications.
- `.github/copilot-instructions.md`: read lines 1 through 540. Sections used: Local gates (line 50), Architecture and conventions (line 153), Safety in this repository (line 309).
- `.specify/memory/constitution.md`: read lines 1 through 520. Principles I through VII and the Technology and Compatibility Constraints section.
- `.specify/templates/`: spec, plan, tasks, and checklist templates read in full.
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`: `spec.md` lines 1 through 90 read. Headings of every file read with grep. Shape used, content not copied.
- `documentation\quality-gates.md`: lines 56 through 84 read. The `playwright` row is line 68.
- `documentation\development-setup.md`: lines 258 through 312 read. Browser test commands and the strict variable.
- `documentation\mist-api-openapi31yaml.yaml`: grep for `websockets/sessions`, `/resize`, and `/terminal` returned no match. The file is 4.3 MB, so only grep read it.
- `documentation\MIST_API_GET_ENDPOINTS.md` and `documentation\MIST_API_MISSING_ENDPOINTS.md`: the same grep returned no match.
- `documentation\architecture.md`: grep read lines 35, 56, 122, 248, 269, and 287. Not relied upon.
- `changelog.d\README.md`: read in full. Rule 4 for internal-only changes is on remote line 58 (R-66). The constitution rule is on remote line 409 (R-65).
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`: present. The pin `mistapi>=0.64.0,<0.65` is satisfied. This record makes no SDK claim.
- Portal package under `src\mist\realtime\websocket_streams\web\`: grep and view. Line numbers come from the remote decode in R-17 through R-55.
- `tests\e2e\websockets_tab\`: grep and view. Line numbers come from the remote decode in R-39 through R-51.
- Local git (read-only commands): `rev-parse`, `log`, `ls-files`, `blame -L`, `show --name-only`, and `for-each-ref --contains`. Commit SHAs are content-addressed, so the local `show` of `c07cb9f8` lists the same files as GitHub. The commit list names `websockets.js`, `websockets_page.html`, and `test_websockets_page.py`.

Remote (GitHub, read-only `gh api` and `gh` list calls):

- `gh issue view 4782 -R jmorrison-juniper/MistHelper --json <fields>`: open, labels `bug` and `web-portal`, one owner comment dated 2026-11-15.
- `gh issue view 4932` and `gh pr view 4924`: closed issue and merged pull request. Closing time and merge time recorded in F-B.
- `gh issue view 4773` and `gh issue view 4769`: open and closed issues. `gh pr view 4772` and `gh pr view 4924`: merged pull requests.
- `gh pr list --state all --search 4782`: empty list. No linked pull request.
- `gh pr list --state open` with files: seven pull requests. Rows R-62 and R-63 record the overlap result.
- `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`: `truncated` is false. Matched paths and blob SHAs recorded in R-01 through R-14 and R-17 through R-51.
- `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main` decoded from base64: line numbers in the table.
- Compare endpoint with base `4e81b2a4a724e29476270564be927f797def82be` and head `main`: status ahead, ahead by 2, behind by 0.
- Compare endpoint with base `c07cb9f8616568ca55ed5933960be2282aeadd93` and head `main`: status diverged, ahead by 74, behind by 1.
- `gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main`: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- `gh api repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/feat/4769` returned no match. `gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/feat/4769-ex-hardware-inventory` returned HTTP 404.
- `gh api repos/jmorrison-juniper/MistHelper/commits/<sha>`: present for `c07cb9f8`, `2a6a5844`, `4e81b2a4`, and `ac046837`. HTTP 422 for `8140bb3`, `58ab484`, `07cf3ee`, and `edc12d5`.

Upstream URLs: none fetched. The `web_fetch` tool was not used, because local and GitHub sources answered every question.

## Unverified

- U-1: Pass or fail status of the existing e2e tests on `main`. Reason: rule 2 forbids running tests in this step.
- U-2: Live server response of the messages route for a batch parent. Reason: no live portal run was made. The e2e tests use fake services.
- U-3: Live staging behavior, the credential source, and the staging organization. Reason: the owner decision D-8 is open.
- U-4: Keys of the terminal read success body. Reason: `TerminalChunk.payload` was not read in this step. The contract marks the keys unverified.
- U-5: Server parsing of the resize request body. Reason: `TerminalRoutes.resize` was not read in this step.
- U-6: Route strings in `websockets_page.html` and `websockets.css`. Reason: the remote scan covered the terminal folder and `websockets.js`. Those two files were not scanned.
- U-7: The owner statement that `documentation\architecture.md` names the old path `src/mist/realtime/websocket/`. Reason: not checked on GitHub, and out of scope for this issue.

## Skills

No skill was loaded. The issue asks no Podman or Juniper device question, so no skill applies.
