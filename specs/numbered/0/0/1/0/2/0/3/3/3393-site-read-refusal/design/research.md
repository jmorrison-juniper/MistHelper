# Research: Site read refusal

Each decision lists the chosen option, the alternatives, the rationale, and the risk. The remote verification table holds every check. Its row count equals the `remote_checks` count in the STATUS file.

## Method

- Remote truth: GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read on 2026-11-26. The recursive tree holds 11404 entries and is not truncated.
- Each of the 55 cited repository files has a local blob hash equal to its `main` blob SHA. Line numbers from local views are therefore valid on `main`.
- Runtime behavior outside the repository came from local source only. No test, build, container, or live Mist call ran in this record.
- The `skill` tool was not used. No local skill covers the Flask portal or the mistapi transport fault path.

## Decisions

### D-1 Reuse the legacy record folder

- Decision: Use the slug `site-read-refusal`. The record folder is `specs\numbered\0\0\1\0\2\0\3\3\3393-site-read-refusal`.
- Alternatives: (a) a new slug, which gives issue 3393 two records. (b) Reuse the folder, which replaces the nine legacy files.
- Rationale: One record per issue keeps the route at one child. The legacy files match `main`, and analysis.md grades each legacy claim.
- Risk: The landing commit replaces the legacy text. The claim table in analysis.md names each stale claim.
- Human decision: no.

### D-2 Keep issue 3393 open

- Decision: Keep the issue open until a human reviews the production-path finding and closes it.
- Alternatives: (a) Close now as fixed. (b) Keep open until review.
- Rationale: PR 4413 says "Keep the issue open, as requested". Issue comment 6, dated 2026-11-11, reports a review hold, and its file owners merged on 2026-11-13 (finding A-7). Finding A-1 in analysis.md shows the production path is unproven.
- Risk: The issue stays open for longer. The cost is one open issue.
- Human decision: no.

### D-3 Use HTTP 503 for a site list transport fault

- Decision: Answer 503 for each route that reads the site list and hits a transport fault.
- Alternatives: (a) 502, which the module uses for a refused cloud result (RC-19). (b) 503, which the module uses for a failed status read (RC-20).
- Rationale: A transport fault means the service did not answer. RC-20 and the existing sibling handlers use 503 for a failed cloud read.
- Risk: A future reader might expect 502. The contract test pins 503 (RC-37).
- Human decision: no.

### D-4 Catch RequestException at each route boundary

- Decision: Keep the three `except RequestException` handlers in `org_upgrade.py` (RC-09, RC-10, RC-11). Do not add a handler in `select.py`.
- Alternatives: (a) A handler in `default_cloud_read` in `select.py`, which returns a partial reason. (b) A blueprint-wide error handler. (c) Route boundary handlers.
- Rationale: `default_cloud_read` has several callers (RC-23). A blueprint-wide handler changes unrelated routes. A route handler owns the response contract.
- Risk: Each new route that reads sites needs its own handler. Finding A-4 names the route that lacks one.
- Human decision: no.

### D-5 Keep the shipped refusal text

- Decision: Keep the message `The Mist cloud site read failed. Try again.` (RC-08).
- Alternatives: (a) The example text in issue 3393, `The Mist cloud did not answer. Save the options again.` (b) A new text.
- Rationale: The shipped text names the cloud and gives a recovery step. The contract and browser tests check it. A new text needs new tests and no safety gain.
- Risk: The wording differs from the example in the issue. The text tells the operator to try again.
- Human decision: no.

### D-6 Track the org_controls retry caller in a separate issue

- Decision: File a separate issue for `open_retry` in `org_controls.py`, which calls `selected_rows` without a handler (RC-29).
- Alternatives: (a) Add a handler in this issue. (b) A separate issue.
- Rationale: AGENTS.md states that one issue holds one subject. The retry route has its own contract and tests. The factory discovers the blueprint by name (RC-28).
- Risk: The retry route answers the generic 500 until the separate issue lands. The retry route fails closed, because it opens no plan.
- Human decision: no.

### D-7 Keep issue 3394 out of this record

- Decision: Keep the family-level save defect of issue 3394 out of this record and out of its repair.
- Alternatives: (a) Fold the 3394 repair into this record. (b) Keep it in its own issue.
- Rationale: PR 4413 states that issue 3394 is outside the repair. RC-16 shows the family check is absent on `main`. The two defects have different code paths.
- Risk: The 3394 defect stays open. Its follow-up order appears in D-11.
- Human decision: no.

### D-8 Fix the missing inline comments in a comment-only change

- Decision: Add the inline comments to the 11 lines that lack them (T007).
- Alternatives: (a) Leave the lines as merged. (b) Add comments in a comment-only change.
- Rationale: The constitution, Principle VI, forbids merged code without inline comments. AGENTS.md states the same rule.
- Risk: A merge conflict with later edits to `org_upgrade.py`. No open pull request touches the file on 2026-11-26.
- Human decision: no.

### D-9 Use `Refs #3393` in the pull request body

- Decision: Write `Refs #3393` in the body of the T-PR pull request, not `Closes #3393`.
- Alternatives: (a) `Closes #3393`, as the brief template requires. (b) `Refs #3393`.
- Rationale: D-2 keeps the issue open until review. A closing keyword closes the issue on merge.
- Risk: The template deviates from the brief for this issue only. The reason appears here.
- Human decision: no.

### D-10 Prove the production path below the SDK boundary

- Decision: Add a contract test (T008) that patches the mistapi session transport to raise `requests.exceptions.ConnectionError`. The test records the answer of the save, the options page, and the confirmation page.
- Alternatives: (a) Accept the source reading in analysis.md A-1. (b) Prove the answer with the test. (c) Change the code before the proof.
- Rationale: The current contract tests inject the exception above mistapi (RC-37 and contract lines 33-42). Source reading predicts other answers. The authoring brief forbids a test run in this record, so the proof belongs to T008.
- Risk: The predicted answers may differ. A different answer changes the follow-up scope.
- Human decision: no.

### D-11 Set the order of the follow-up issues

- Decision: The recommended order is: (1) issue 3394, the silent drop of a checked device family. (2) The save refusal text for an unread site, finding A-2. (3) The retry caller, finding A-4.
- Alternatives: (a) Start with the save refusal text. (b) Start with the retry caller. (c) Start with issue 3394.
- Rationale: Issue 3394 saves a plan that lacks a checked family, and no message reports the loss. The save refusal text tells the operator to clear a healthy site. The retry caller fails closed with the generic 500.
- Risk: The operator still sees the misleading text while issue 3394 waits. The text is recoverable, because the operator can save again.
- Human decision: HUMAN-DECISION-REQUIRED. The order sets product priority.

## Remote verification

The Ref column holds `main` for a repository file, `object` for a commit lookup, and `local-venv` for a file in the pinned `.venv` package. The Blob or commit SHA column holds the blob SHA of a file or the full commit SHA. The Line column holds the line of the claim, or 0 for a file-level claim.

| ID | Claim | Path | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Main head commit is current | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-02 | PR 4413 merge commit exists | commits/1e0e5cb385c8f9211847755874bafe6c63e0cdc4 | object | 1e0e5cb385c8f9211847755874bafe6c63e0cdc4 | present | 0 |
| RC-03 | Legacy base commit 9991d30a exists | commits/9991d30a187e5d215462eefac60a09a57e5f99e5 | object | 9991d30a187e5d215462eefac60a09a57e5f99e5 | present | 0 |
| RC-04 | Legacy feature commit 3d2e538 exists | commits/3d2e5383a2f16c29bef6c19a62647152f5e5bebf | object | 3d2e5383a2f16c29bef6c19a62647152f5e5bebf | present | 0 |
| RC-05 | PR 4413 base commit exists | commits/064cec47524fa6b3e820bddd4525d01a791cbecc | object | 064cec47524fa6b3e820bddd4525d01a791cbecc | present | 0 |
| RC-06 | PR 4413 rebased head commit exists | commits/7abf946aa064b5850a63f0c590ac23806e012d8d | object | 7abf946aa064b5850a63f0c590ac23806e012d8d | present | 0 |
| RC-07 | Route module imports RequestException | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 22 |
| RC-08 | Route module defines the 503 site read constants | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 230 |
| RC-09 | Options page handler answers 503 for RequestException | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1147 |
| RC-10 | Save handler answers 503 for RequestException | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1227 |
| RC-11 | Confirmation page handler answers 503 for RequestException | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1350 |
| RC-12 | selected_rows is defined in the route module | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 496 |
| RC-13 | selected_rows is called inside the save path | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1280 |
| RC-14 | Plan write follows the site read in the save path | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1301 |
| RC-15 | Device read runs before the site read in the save path | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 649 |
| RC-16 | Family-level check for issue 3394 exists in _complete_aggregate_options | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | absent | 701 |
| RC-17 | Records refusal is raised before the site read | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 659 |
| RC-18 | Route constants name the options page, the save, and the confirmation page | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 145 |
| RC-19 | A refused cloud result answers 502 | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1039 |
| RC-20 | A failed status read answers 503, which is the sibling precedent | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 2500 |
| RC-21 | Issue body path retired upgrade_portal/app/routes/org_upgrade.py exists | retired upgrade_portal/app/routes/org_upgrade.py | main | none | absent | 0 |
| RC-22 | build_site_rows reads listOrgSites and listOrgSiteStats | src/interfaces/portals/upgrade_portal/app/routes/select.py | main | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | present | 1060 |
| RC-23 | default_cloud_read catches RequestException | src/interfaces/portals/upgrade_portal/app/routes/select.py | main | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | absent | 357 |
| RC-24 | Site list cache keeps each read for 60 seconds | src/interfaces/portals/upgrade_portal/app/routes/select.py | main | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | present | 192 |
| RC-25 | SiteListIncompleteError is an Exception subclass | src/interfaces/portals/upgrade_portal/app/routes/select.py | main | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | present | 992 |
| RC-26 | App error handler answers SiteListIncompleteError | src/interfaces/portals/upgrade_portal/app/routes/select.py | main | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | present | 1562 |
| RC-27 | Error page text for status 500 is the unexpected fault text | src/interfaces/portals/upgrade_portal/app/factory.py | main | 5729127f3b4a0d25f45a33e8ef79a4e460d8be92 | present | 124 |
| RC-28 | Factory discovers the org_controls blueprint by name | src/interfaces/portals/upgrade_portal/app/factory.py | main | 5729127f3b4a0d25f45a33e8ef79a4e460d8be92 | present | 92 |
| RC-29 | open_retry calls selected_rows with no RequestException handler | src/interfaces/portals/upgrade_portal/app/routes/org_controls.py | main | 315ac60d079b07475d08cd223d77eaf869b66416 | absent | 170 |
| RC-30 | A reply with no HTTP status maps to the read failed reason | src/interfaces/portals/upgrade_portal/capture/devices.py | main | 82515c6dc619fbc1d7aad50ee8ea7607840c18bd | present | 265 |
| RC-31 | read_upgrade_org_inventory reads the organization inventory | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 736 |
| RC-32 | Unread-site refusal text names each site as holding no device | src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py | main | be7954035bd921c214dc69307d6ad916cadf0c2d | present | 41 |
| RC-33 | OrgSiteRefusal derives from ValueError | src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py | main | be7954035bd921c214dc69307d6ad916cadf0c2d | present | 58 |
| RC-34 | README names no cloud read refusal | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| RC-35 | Operator guide names no options refusal | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| RC-36 | Contract test module for issue 3393 exists | tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py | main | 2e54e82d5f2fabf513d5e67818c07e800a55ece3 | present | 45 |
| RC-37 | Contract test asserts the exact refusal envelope | tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py | main | 2e54e82d5f2fabf513d5e67818c07e800a55ece3 | present | 25 |
| RC-38 | Browser test keeps form values after the refusal | tests/e2e/upgrade_portal/test_org_upgrade_flow.py | main | bdfa090c1542807897afb2c2dfb7fe9ba128de2f | present | 50 |
| RC-39 | Existing failed name read contract test exists | tests/contract/upgrade_portal/test_org_site_records_routes.py | main | 8fa9d329142764464212c55ccf08a596d503d799 | present | 346 |
| RC-40 | Existing no checked device type refusal test exists | tests/contract/upgrade_portal/test_org_site_records_routes.py | main | 8fa9d329142764464212c55ccf08a596d503d799 | present | 291 |
| RC-41 | Routes regression module exists | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 0 |
| RC-42 | selected_rows unit tests exist | tests/unit/upgrade_portal/test_issue_3439_site_checks.py | main | da13d54de2f338236be2728e9183e3d4d5ea9262 | present | 229 |
| RC-43 | Changelog fragment policy guardrail exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-44 | Release fragment for issue 3393 exists | changelog.d/issue-3393-site-read-refusal.md | main | 60dab6389eecf61346de44f7e231695048aa89a6 | present | 0 |
| RC-45 | Route folder holds one child | specs/numbered/0/0/1/0/2/0/3/3 | main | e568270e3fdc7ede39ba6b5a157dcdee2b76acf5 | present | 0 |
| RC-46 | Legacy record folder exists with its nine files | specs/numbered/0/0/1/0/2/0/3/3/3393-site-read-refusal | main | b6fdb6642e915a63f2b15bfa09bedfdfc4afd33c | present | 0 |
| RC-47 | Reference record folder exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| RC-48 | Constitution version is 1.9.0 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 562 |
| RC-49 | Resolve-SpecFeaturePath is defined | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| RC-50 | Create-new-feature script exists | .specify/scripts/powershell/create-new-feature.ps1 | main | e5a18bf8e9b6fcb0163fc405a4166e7d68c1b9f8 | present | 0 |
| RC-51 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-52 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-53 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-54 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-55 | AGENTS.md exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-56 | Repository instructions hold the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-57 | CI defines the mypy path list | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-58 | Project requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RC-59 | Requirements pin mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-60 | STE configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-61 | Quality gates guide holds the writing gate command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| RC-62 | Development setup guide holds the browser test section | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 262 |
| RC-63 | Container guide holds the test and debug container section | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-64 | OpenAPI file defines the listOrgSites operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20018 |
| RC-65 | Endpoint map lists listOrgSites with its mistapi module | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 867 |
| RC-66 | mistapi defines listOrgSites | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 17 |
| RC-67 | mistapi listOrgSites requests the organization sites path | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 48 |
| RC-68 | mistapi defines listOrgSiteStats | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | local-venv | 247e4526005342dc895408519d5974a7aa86aefd | present | 1308 |
| RC-69 | mistapi mist_get sends each request through the retry wrapper | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 277 |
| RC-70 | Retry wrapper catches requests ConnectionError and returns an answer | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 225 |
| RC-71 | Retry wrapper catches every other exception and returns an answer | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 250 |
| RC-72 | An answer built without a response has no status | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 46 |
| RC-73 | requests RequestException derives from IOError | .venv\Lib\site-packages\requests\exceptions.py | local-venv | cb5e9510e3b1cf4804ac6091fd7fdb55e9f2745b | present | 20 |
| RC-74 | requests ConnectionError derives from RequestException | .venv\Lib\site-packages\requests\exceptions.py | local-venv | cb5e9510e3b1cf4804ac6091fd7fdb55e9f2745b | present | 70 |
| RC-75 | requests Timeout derives from RequestException | .venv\Lib\site-packages\requests\exceptions.py | local-venv | cb5e9510e3b1cf4804ac6091fd7fdb55e9f2745b | present | 82 |
| RC-76 | Installed mistapi package is version 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 0 |

Rows RC-66 through RC-76 use local package files. Their blob SHA is the git blob hash that the local file produces. These files are outside the repository tree, so the value is a computed identity and not a GitHub blob.

## Sources

- AGENTS.md at repository root, blob `44a9afffb5bd6f774973a845d27343e4e528b6ad` (RC-55).
- `.github/copilot-instructions.md`, blob `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` (RC-56).
- `.specify/memory/constitution.md`, blob `4584997a264c5a7ade2ca7441246e1f067083aa1` (RC-48).
- Four templates under `.specify/templates/` (RC-51 to RC-54).
- Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (RC-47). It supplies the shape only.
- Documentation sections: RC-61, RC-62, RC-63, RC-64, RC-65.
- Mist API definition: `documentation\mist-api-openapi31yaml.yaml` line 20018 (RC-64). The local file matches the `main` blob.
- Mist SDK: `.venv\Lib\site-packages\mistapi` (RC-66 to RC-72, RC-76).
- HTTP library: `.venv\Lib\site-packages\requests\exceptions.py` (RC-73 to RC-75).
- Python requirement: `pyproject.toml` line 23 (RC-58). Pin: `requirements.txt` line 129 (RC-59).
- No URL source was used. The `web_fetch` tool was not called.

## Unverified

- U-1: Runtime answers for a transport fault below mistapi. Reason: the authoring brief forbids a test run, and no live Mist call is allowed. Analysis A-1 gives source predictions. T008 proves them.
- U-2: The test pass counts and gate outputs in the legacy record, such as 106 passed and a pylint score of 9.86. Reason: tool output cannot be reproduced without a run.
- U-3: The dry run of `create-new-feature.ps1 -DryRun -Number 3393` and the behavior of `.specify/feature.json`. Reason: a script run is forbidden in this record.
- U-4: Whether mistapi redacts a token inside the exception text that its logger writes at `__api_request.py` lines 226 and 251. Reason: the sanitizer at line 34 exists, but the logged text was not traced.
- U-5: The artifact list endpoint returns HTTP 404, as the legacy research states. Reason: the state of the issue artifact service cannot be read from the repository.
- U-6: The open pull request count of 14 in the legacy analysis. Reason: the state of 2026-10-23 cannot be reread.
- U-7: The line numbers in the 2026-10-06 assessment comments at base `efd0828`. Reason: `main` moved to `f03c6c9`, and the base was not re-measured.
- U-8: The body of `read_upgrade_org_inventory` in `upgrade/options.py`. Reason: only its signature (RC-31) was read. A grep found no direct `requests` call in the upgrade portal, but the body was not traced.
