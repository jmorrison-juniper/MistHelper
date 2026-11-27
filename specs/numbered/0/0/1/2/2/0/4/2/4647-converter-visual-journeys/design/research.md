# Research: Add independently authored converter visual journeys

**Evidence rules**: Remote checks read the `main` tree (`git/trees/main?recursive=1`) and file bodies (`contents/<path>?ref=main`). Line numbers come from decoded remote text. Local files gave context only. Six local files also matched their remote blob SHA (`git hash-object`, read only). Local packages are third-party sources and carry the ref `local`.

## R1. Issue facts

- Issue #4647 is open. Labels: `feature`, `web-portal`. Created 2026-11-07. Last updated 2026-11-09.
- The body asks for browser tests in the real portal host. It names these journeys: structured review, proposal, typed confirmation, cancel and reset, status, and keyboard access. It names these checks: four theme intentions, desktop and narrow viewports, safe text, and failure traces.
- The body forbids copying source templates, styles, screenshots, prose, or animation.
- The body requires synthetic input, mocked responses, and no cloud write in browser tests.
- The body keeps shared navigation and portal registration out of scope until the integration-owner handover.
- Comment 1 names PR #4596 as the task map. It records lines 104 and 105 for the browser tests and the presentation. It also records that prerequisites #4636, #4641, and #4642 stay open.
- Comment 2 records that `tests/e2e/web_portal/` already holds 32 tracked direct children. It asks for a compliant test layout before a new file is added.
- The live task map on `main` confirms T029 and T030 (RC-62, RC-63).

## R2. Linked work, comments, and state

- A PR search for `4647` returned no pull request.
- PR #4596 is merged. It merged on 2026-11-13. Its head was `7f024aab89e5e71d8f0a1cf41025ee5ff0a1d533`. Its content lives on `main` under `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity` (RC-62 to RC-67).
- Program issues #4224, #4634 to #4646, #4648, and #4649 are open. Issue #4636 has a draft record in `spec-drafts\4636`.
- Seven pull requests are open. PR #4208 touches `web_portal/templates/base.html` and `web_portal/app.py` (RC-72). This change touches neither file.

## R3. Legacy record check

- A local search of `specs\` for `4647-*` found no folder. A glob search found no match.
- The remote route folder for this record is absent (RC-71).
- `spec-drafts\4647` held no file before this run. No legacy record exists, so `existing_record.found` is `false`.

## R4. Current converter state

- The converter package holds five direct children (RC-01). Its presentation folder holds two files (RC-02).
- The blueprint mounts at `/cisco-config-converter` with the page, preview, review, and export routes (RC-04, RC-05, RC-18).
- Preview reads the upload and form fields. Review and export read a JSON body (RC-19, RC-20).
- Invalid input returns 400 JSON. A failed state check returns 409 JSON (RC-16, RC-17). Review and export also return 400 JSON for an invalid body (RC-100).
- Export names the file `cisco-proposal.json` (RC-21). Responses use `no-store` (RC-06).
- The routes module imports no Mist SDK module (RC-07).
- The review state stores a digest under two session keys (RC-24). The proposal type declares three fields (RC-25).
- The current page extends the host base template and has a status region and two action buttons (RC-08, RC-09, RC-10).
- The current page has no typed confirmation, cancel, reset, or focus control (RC-11).
- The current script renders text with `textContent` and guards stale responses with a generation token (RC-12, RC-13).
- The current script resets state on input and page hide (RC-14). It has no `innerHTML` and no browser storage call (RC-15).
- The script posts preview data as form data (RC-22) and sends the CSRF header on review and export (RC-23).

## R5. Portal host, themes, and storage

- The host factory takes session identity, menu actions, and an organization ID (RC-29).
- The host registers no converter blueprint (RC-30). The host base template has no converter navigation (RC-31).
- The host theme service stores the saved theme under `misthelper-theme` (RC-32). The theme function writes browser storage on each call (RC-33).
- The brand test lists four shipped themes: magenta, dark, light, and high-contrast (RC-34).
- Only the magenta theme defines the focus ring token (RC-35). Dark, light, and high-contrast define none (RC-36 to RC-38).
- The responsive stylesheet switches layout below 575.98 pixels (RC-39). The responsive test defines the phone viewport at 390 by 844 and the desktop viewport at 1440 by 900 (RC-40).
- The session secret falls back to a random value when `PORTAL_SECRET_KEY` is empty (RC-41). The content security policy allows inline script and inline style (RC-42).
- Repeated installation of the input interceptor returns early (RC-43). The host base template exposes the theme switcher test ID (RC-99). The blueprint guard checks the request class and CSRF before registration (RC-101).

## R6. Browser test setup

- The E2E fixture creates the host with `WebPortalApp.create_app` and stops it with `WebPortalApp.shutdown_app` (RC-44, RC-45). The E2E hook sets a 120-second timeout on each test (RC-46).
- The E2E root holds exactly five entries (RC-47).
- The browser shard row runs `tests/e2e/web_portal` (RC-50). Browser jobs install Chromium (RC-51). The browser command keeps screenshots and traces on failure (RC-52).
- Coverage shards exclude `tests/e2e` (RC-53). The browser shard budget is 20 minutes (RC-54). The shard guard requires the tracing option (RC-55).
- The pinned versions are mistapi 0.64.1 (RC-57), Playwright 1.65.2 (RC-58), and pytest-playwright 0.10.0 (RC-59).
- The bootstrap downloads Chromium (RC-61). Git ignores `test-artifacts` (RC-60).
- The installed Playwright package defines `Page.route`, `Route.fulfill`, and `Page.set_viewport_size` (RC-74 to RC-76). The installed pytest-playwright plugin defines the tracing option (RC-77).
- The installed Flask package records the first request (RC-73). The test host must register its blueprint before that point.

## R7. Layout and process constraints

- Constitution Principle I forbids a direct child under a noncompliant parent (RC-79). Grandfathered debt stays allowed only as existing debt (RC-84).
- Constitution Principles III, IV, VI, and VII require typed confirmation, the full pipeline, inline comments, and action logging (RC-80 to RC-83).
- The constitution branch rule names `feat/<issue>-<slug>` from `main` (RC-85).
- The style rules for instructions and descriptions appear in AGENTS (RC-86). AGENTS also requires `Warning` or `Caution` prefixes (RC-87).
- AGENTS requires `Closes #<issue>` in the body (RC-88). It requires the `auto-merge` label only after green checks (RC-89). It requires a squash merge (RC-90).
- The repository guide defines the Lint, Format, Tests, STE, and test quality gates (RC-91 to RC-95). It requires web UI tests under `tests/e2e` with `data-testid` values (RC-96).
- The repository guide requires one serial merge slot until the owner activates a queue (RC-97). It sets the Conventional Commits forms for pull request titles (RC-98).
- Constitution v1.9.0 is the version in force (RC-78).

## R8. Decisions

Each decision names its alternatives, the chosen option, the reason, and the risk. No decision requires a human (section 6 categories do not apply).

### D-1. Browser journeys live in the existing smoke module

- Alternatives: (a) add `test_cisco_parity.py` to `tests/e2e/web_portal/`. Rejected: it adds a direct child to a noncompliant parent (RC-48, RC-79). (b) Add a package under `tests/e2e/web_portal/`. Rejected: the same rule applies. (c) Add a package under `tests/e2e/`. Rejected: the guard requires exactly five entries (RC-47). (d) Put browser tests under `tests/integration/`. Rejected: Chromium installs only in browser jobs (RC-51), coverage excludes E2E (RC-53), and the timeout hook covers E2E only (RC-46).
- Chosen: replace the isolated class in `tests/e2e/web_portal/test_portal_smoke.py`.
- Reason: no child is added. The browser shard row covers the module (RC-50). The timeout applies (RC-46).
- Risk: the module grows. Mitigation: small classes, constitution limits, and remediation R-1.

### D-2. Typed word `EXPORT`

- Alternatives: `APPLY` is reserved for cloud apply (RC-65). `CONFIRM` is reserved for administrative writes (RC-67). `EXPORT` is chosen.
- Reason: the export is offline, and the word names the action. The reserved words stay free for later tasks.
- Risk: the owner may prefer another word. One constant changes in the script and the tests.

### D-3. Test host mounts the blueprint

- Alternatives: (a) register in `web_portal/app.py`. Rejected: shared registration waits for the handover (RC-30, RC-64). (b) Use an isolated Flask app. Rejected: it proves no host integration (RC-26, RC-28). (c) Use the real factory and register the blueprint before the first request. Chosen.
- Reason: the real shell and theme services load. No shared file changes.
- Risk: the test host differs from production by one registration. Mitigation: `test_production_host_serves_no_converter_route`.

### D-4. Storage assertion allows only `misthelper-theme`

- Alternatives: (a) keep the zero-storage assertion. Rejected: the host writes the key on each load (RC-33). (b) Disable host storage in tests. Rejected: it changes the behavior under test. (c) Allow the host key only. Chosen.
- Reason: the assertion matches host behavior and still proves that the converter writes no key.
- Risk: a key rename breaks the test. The key stays in one constant.

### D-5. Presentation rewrite with DOM APIs and host tokens

- Alternatives: (a) patch the current page. Rejected: it lacks the required journeys (RC-11). (b) Build markup from strings with escaping. Rejected: more risk than DOM text APIs. (c) Rewrite with DOM text APIs, host tokens, and a new stylesheet. Chosen.
- Reason: this meets FR-010 and FR-015 and keeps the current IDs (RC-10, RC-12, RC-15).
- Risk: a larger diff. The review covers each changed block.

### D-6. Server routes and JSON shapes stay unchanged

- Alternatives: (a) add server confirmation state. Rejected: issue #4641 owns versioned review. (b) Keep the typed gate in the browser and keep server review checks. Chosen.
- Reason: review binding remains on the server (RC-17, RC-24).
- Risk: a direct request skips the typed word. The server still requires a current review (RC-17).

### D-7. Stale-response guard stays

- Alternatives: (a) use an abort controller. Rejected: it changes behavior without need. (b) Keep the generation token. Chosen (RC-13).
- Risk: none beyond current behavior.

### D-8. Shipped themes and viewports come from existing constants

- Alternatives: (a) add new constants. Rejected: they duplicate existing values. (b) Import the existing constants. Chosen (RC-34, RC-40).
- Risk: a change to those constants changes this suite.

### D-9. Failure evidence comes from CI options

- Alternatives: (a) add custom trace code. Rejected: it duplicates the plugin (RC-77). (b) Use the CI options. Chosen (RC-52).
- Risk: local runs need the same options. The quickstart lists them.

### D-10. Mocks cover edge states only

- Alternatives: (a) mock every response. Rejected: it weakens the integration proof. (b) Mock stale, failure, and cloud-guard states only. Chosen (RC-74, RC-75).
- Risk: route behavior needs an executed run (U-1).

### D-11. The cloud guard aborts non-loopback requests

- Alternatives: (a) add an environment flag. Rejected: no converter flag exists, and the converter sends no request (RC-07). (b) Use a route guard. Chosen.
- Risk: none for the offline page.

### D-12. Implementation waits for #4636, #4641, and #4642

- Alternatives: (a) start now. Rejected: the state and proposal contracts can change. (b) Wait for #4641 only. Rejected: the issue names three prerequisites. (c) Wait for all three. Chosen.
- Risk: the schedule depends on three open issues.

### D-13. Tests read no secret and no environment value

- Alternatives: (a) set `PORTAL_SECRET_KEY` in tests. Rejected: it handles secret material, and #4636 D-15 owns the policy. (b) Use the host fallback secret. Chosen (RC-41).
- Risk: each test host has its own random secret. Tests keep one cookie jar per browser context, so this is acceptable.

### D-14. Independent authorship and no reuse

- Alternatives: (a) reuse with attribution. Rejected: the issue forbids copying, and #4635 stays open. (b) Author everything independently. Chosen.
- Reason: the issue already decides this. No legal text is written here.
- Risk: visual similarity to the source may be lower.

### D-15. Debt stays in place, and remediation R-1 is separate

- Alternatives: (a) move test modules now. Rejected: it is an unrelated change. (b) Record the debt and open remediation R-1. Chosen (RC-48).
- Risk: the debt remains until R-1 lands.

### D-16. One changelog fragment

- Alternatives: (a) no fragment. Rejected: the presentation change is visible to users. (b) One fragment named for the issue. Chosen.

### D-17. Keep current test IDs and add new IDs

- Alternatives: (a) rename all IDs. Rejected: the parent contract requires stable IDs (RC-70). (b) Keep current IDs and add new ones. Chosen.

## R9. Remote verification table

Rows match the `remote_checks` array in `META_DIR\4647-STATUS.json` in order. Result `absent` means the searched path or pattern does not exist. Line `0` means the row checks a tree or a path.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Converter package holds five direct children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| RC-02 | Presentation folder holds two files before this change | src/interfaces/portals/cisco_config_converter/presentation | main | bc5adba315c0ff6fbbb7d2b4b6e1a7680d15dce6 | present | 0 |
| RC-03 | Converter stylesheet is absent before this change | src/interfaces/portals/cisco_config_converter/presentation/converter.css | main | none | absent | 0 |
| RC-04 | Blueprint mounts at the converter URL prefix | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 54 |
| RC-05 | Blueprint registers page, preview, review, and export routes | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 61 |
| RC-06 | Converter responses set no-store caching | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 113 |
| RC-07 | Routes module imports no Mist SDK module | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | absent | 0 |
| RC-08 | Current page extends the host base template | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 1 |
| RC-09 | Current page has a live status region | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 21 |
| RC-10 | Current page has review and export buttons | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 23 |
| RC-11 | Current page has no typed confirmation, cancel, reset, or focus control | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | absent | 0 |
| RC-12 | Current script writes proposal text with textContent | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 38 |
| RC-13 | Current script drops stale preview responses with a generation token | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 36 |
| RC-14 | Current script resets the proposal on input and page hide | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 16 |
| RC-15 | Current script has no innerHTML or browser storage call | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | absent | 0 |
| RC-16 | Preview returns a 400 JSON error for invalid input | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 84 |
| RC-17 | Review and export return 409 when a state check fails | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 146 |
| RC-18 | Page renders the converter template | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 70 |
| RC-19 | Preview reads an uploaded file and form fields | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 119 |
| RC-20 | Review and export read a JSON body | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 134 |
| RC-21 | Export names the attachment cisco-proposal.json | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 148 |
| RC-22 | Script posts the preview as form data | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 33 |
| RC-23 | Script sends the CSRF header with review and export | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 56 |
| RC-24 | Review state stores the proposal digest under a session key | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 96 |
| RC-25 | Proposal type is declared as a typed dictionary | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 29 |
| RC-26 | Smoke module imports the isolated integration client | tests/e2e/web_portal/test_portal_smoke.py | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 18 |
| RC-27 | Smoke module asserts that browser storage stays empty | tests/e2e/web_portal/test_portal_smoke.py | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 58 |
| RC-28 | Integration client mounts the blueprint on a bare Flask app | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 21 |
| RC-29 | Host factory takes session identity, menu actions, and organization ID | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 37 |
| RC-30 | Host registers no converter blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| RC-31 | Host base template has no converter navigation | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| RC-32 | Host theme service stores the saved theme under the misthelper-theme key | web_portal/static/js/portal.js | main | 8dd3880bb2a3c68521f5504b57ca7559288192ba | present | 61 |
| RC-33 | Host theme function applyTheme writes browser storage on each call | web_portal/static/js/portal.js | main | 8dd3880bb2a3c68521f5504b57ca7559288192ba | present | 88 |
| RC-34 | Brand test lists the four shipped themes | tests/e2e/web_portal/test_brand_theme_contrast.py | main | 3963529ae5c28d30bd307ed0d29eb7621782b750 | present | 38 |
| RC-35 | Magenta theme defines the focus ring token | web_portal/static/css/themes/magenta.css | main | 42056dcb94ddf0526ad5364497b08ae22c7bc4ab | present | 68 |
| RC-36 | Dark theme defines no focus ring token | web_portal/static/css/themes/dark.css | main | 2d8fad95949db2a0c68ab5450253816e23f4882c | absent | 0 |
| RC-37 | Light theme defines no focus ring token | web_portal/static/css/themes/light.css | main | cac452706ffaedb969e42fa6e5570893443cd7d9 | absent | 0 |
| RC-38 | High-contrast theme defines no focus ring token | web_portal/static/css/themes/high-contrast.css | main | 5204cd3877d96de6f04a31a5c08393bc160dc905 | absent | 0 |
| RC-39 | Responsive stylesheet switches layout below 575.98 pixels | web_portal/static/css/responsive.css | main | 12c92f69f5d9297c8d29176d85e51c0983b52262 | present | 61 |
| RC-40 | Responsive test defines the phone and desktop viewports | tests/e2e/web_portal/test_responsive_layout.py | main | b95818709546ed85a07fcca76265142419094c35 | present | 36 |
| RC-41 | Session secret falls back to a random value when PORTAL_SECRET_KEY is empty | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| RC-42 | Content security policy allows inline script and inline style | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 168 |
| RC-43 | Input interceptor install returns early when already installed | web_portal/services/input_hook.py | main | d4662ef3b484a1afba84213e73d22c5d94d032cf | present | 34 |
| RC-44 | E2E fixture creates the host with WebPortalApp.create_app | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 273 |
| RC-45 | E2E fixture stops the host with WebPortalApp.shutdown_app | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 283 |
| RC-46 | E2E tests run under a 120-second timeout | tests/e2e/conftest.py | main | e450e1855770d2e0ec587935a95233262b118ae1 | present | 33 |
| RC-47 | E2E root holds exactly five entries | tests/guardrails/test_e2e_package_structure.py | main | c5be7ed0b21eec56c7d586b7025cf28f0fc4fb42 | present | 20 |
| RC-48 | Web portal test folder holds 32 direct children | tests/e2e/web_portal | main | 3d492d6e0bec7e4a76925d345c095dfa44bb813e | present | 0 |
| RC-49 | Planned T029 test file is absent | tests/e2e/web_portal/test_cisco_parity.py | main | none | absent | 0 |
| RC-50 | Browser shard row runs tests/e2e/web_portal | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 796 |
| RC-51 | Browser jobs install Chromium with Playwright | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 887 |
| RC-52 | Browser command keeps screenshots and traces on failure | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 909 |
| RC-53 | Coverage shards exclude tests/e2e | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 311 |
| RC-54 | Browser shard budget is 20 minutes | tests/guardrails/test_ci_runtime_budgets.py | main | 8d7c69490b6566ea16ebb9539b1a9786728c30c3 | present | 33 |
| RC-55 | Shard guard requires the tracing option | tests/guardrails/test_e2e_shard_partition.py | main | 8d9f45db72e88e5a48d3f2e561e3e2cba9e89fd3 | present | 29 |
| RC-56 | Spec route uses base five across eight segments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-57 | Pinned mistapi version is 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-58 | Pinned Playwright version is 1.65.2 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 272 |
| RC-59 | Pinned pytest-playwright version is 0.10.0 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 333 |
| RC-60 | Test artifacts folder is ignored by Git | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 107 |
| RC-61 | Repository guide says bootstrap downloads Chromium | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 36 |
| RC-62 | Live task T029 names the test file | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 104 |
| RC-63 | Live task T030 names the presentation files | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 105 |
| RC-64 | Live contract says the converter has no portal registration | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 23 |
| RC-65 | Live contract requires typed APPLY for apply submission | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 91 |
| RC-66 | Live contract requires keyboard focus and non-color status | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 96 |
| RC-67 | Live Mist contract reserves CONFIRM for administrative writes | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 121 |
| RC-68 | Parent task T013 marks the presentation delivered | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md | main | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 49 |
| RC-69 | Parent tasks forbid shared portal publication before owner approval | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md | main | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 183 |
| RC-70 | Parent contract requires stable data-testid values | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/portal.md | main | 774b487ab32ae1417368ba79930e7eac0b3dad43 | present | 10 |
| RC-71 | Route folder for this record is absent | specs/numbered/0/0/1/2/2/0/4/2/4647-converter-visual-journeys | main | none | absent | 0 |
| RC-72 | Open PR 4208 changes the base template that this change leaves unchanged | web_portal/templates/base.html | PR #4208 (open) | none | present | 0 |
| RC-73 | Flask stores the first-request flag | .venv\Lib\site-packages\flask\app.py | local | none | present | 911 |
| RC-74 | Playwright Page defines route | .venv\Lib\site-packages\playwright\sync_api\_generated.py | local | none | present | 19989 |
| RC-75 | Playwright Route defines fulfill | .venv\Lib\site-packages\playwright\sync_api\_generated.py | local | none | present | 22692 |
| RC-76 | Playwright Page defines set_viewport_size | .venv\Lib\site-packages\playwright\sync_api\_generated.py | local | none | present | 20615 |
| RC-77 | pytest-playwright defines the tracing option | .venv\Lib\site-packages\pytest_playwright\pytest_playwright.py | local | none | present | 767 |
| RC-78 | Constitution header states version 1.8.0 to 1.9.0 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 4 |
| RC-79 | Principle I forbids a direct child under a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 42 |
| RC-80 | Principle III requires typed confirmation for destructive operations | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 121 |
| RC-81 | Principle IV requires the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 145 |
| RC-82 | Principle VI requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 208 |
| RC-83 | Principle VII requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-84 | Compliance review requires a complexity table that separates grandfathered debt | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 551 |
| RC-85 | Constitution branch rule requires feat with issue number and slug from main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 478 |
| RC-86 | AGENTS limits instructions to 20 words and descriptions to 25 words | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 48 |
| RC-87 | AGENTS requires Warning or Caution for safety statements | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 52 |
| RC-88 | AGENTS requires Closes issue text in the pull request body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RC-89 | AGENTS adds the auto-merge label only after every check is green | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| RC-90 | AGENTS requires a squash merge and no direct push to main | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 235 |
| RC-91 | Repository guide Lint gate runs ruff check | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| RC-92 | Repository guide Format gate runs black check | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 59 |
| RC-93 | Repository guide Tests gate runs pytest on the changed file | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-94 | Repository guide STE gate lists the documentation files it checks | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-95 | Repository guide test quality gate uses the changed-from base | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 145 |
| RC-96 | Repository guide says web UI tests live under tests/e2e with data-testid values | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 301 |
| RC-97 | Repository guide requires one serial merge slot until the owner activates a queue | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 485 |
| RC-98 | Repository guide sets the Conventional Commits forms for pull request titles | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| RC-99 | Host base template exposes the theme switcher test ID | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 88 |
| RC-100 | Review and export return 400 JSON for an invalid proposal body | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 143 |
| RC-101 | Blueprint guard checks the request class and CSRF before registration | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 103 |

## R10. Sources

- Issue #4647 body and comments, read with `gh issue view` on 2026-11-26.
- PR #4596 metadata, read with `gh pr view` (state MERGED, merged 2026-11-13).
- PR search for `4647`, read with `gh pr list` (no result). Open pull requests, read with `gh pr list --json files` (7 open, overlap with PR #4208 only).
- Program issue states, read with `gh issue view` for #4224 and #4634 to #4649.
- Remote tree and file bodies on `main` (RC-01 to RC-71 and RC-78 to RC-101).
- Local read-only commands: `git rev-parse HEAD` (f03c6c9b36d612a48d7b9652998c2fd87dd777ca) and `git hash-object` on six files that matched their remote blob SHA.
- Installed third-party sources in `.venv\Lib\site-packages` (RC-73 to RC-77).
- Sibling draft `spec-drafts\4636` and its `_meta\4636-STATUS.json` and `_meta\4636-summary.md`, read for consistent decisions.
- Reference record headings in `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, read for shape only.
- Templates in `.specify\templates`, read in full.
- Operator and API documents searched locally: `documentation\architecture.md`, `development-setup.md`, `operator-guide.md`, `MIST_API_GET_ENDPOINTS.md`, and `MIST_API_MISSING_ENDPOINTS.md`. No converter reference was found.
- No URL was fetched. No skill was loaded because no listed skill covers Flask and Playwright portal tests.

## Unverified

- U-1: Playwright route behavior with a held response. Only method signatures were checked (RC-74 to RC-76). An executed run must confirm the behavior.
- U-2: Whether Principles VI and VII (RC-82, RC-83) cover browser script. The principles name AI-generated code. The browser script adds no server action.
- U-3: Duration of the `web_portal` browser shard after this change. No CI run was made in this pass.
- U-4: Whether issue #4641 changes the proposal JSON shape. The issue is open.
- U-5: Whether issue #4636 D-5 changes the test host. D-5 refuses state when `PORTAL_SECRET_KEY` is empty. The issue is open.
- U-6: Provenance of the current presentation files. No source comparison was run. The provenance checklist covers the review.
- U-7: Document search scope. Five documents were searched locally. Other documents were not searched against `main`.
- U-8: Exact Flask setup-guard text. Only the first-request flag was checked (RC-73).
- U-9: Chromium on a Windows developer host. No browser run was made in this pass.
