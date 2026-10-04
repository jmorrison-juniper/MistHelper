# Tasks: Maps Site Selection

**Input**: [spec.md](spec.md), [plan.md](plan.md), and [requirements checklist](checklists/requirements.md).

**Issue**: [#3366](https://github.com/jmorrison-juniper/MistHelper/issues/3366).

**Template**: [Repository task template](../../.specify/templates/tasks-template.md).

## Format: `[ID] [P?] [Story] Description`

Each task names its owned file or its evidence record.
Check a task only after its execution evidence satisfies the requirement.
Keep release-dependent tasks unchecked until the parent supplies the exact authority.

## Phase 1: Setup

- [x] T001 Record the live claim and exact eight-file reservation in `specs/3366-map-site-selection/tasks.md`.
- [x] T002 Complete specify, plan, and tasks in `specs/3366-map-site-selection/`.
- [x] T003 Prepare the missing isolated Python environment and verify execution capabilities in this evidence record.

The authenticated account is `jmorrison-juniper`.
The issue was open, unassigned, and without reservation comments.
Every open pull request file list was checked before the claim.
The exact reservation appears in [the claim comment](https://github.com/jmorrison-juniper/MistHelper/issues/3366#issuecomment-5936415025).
No open pull request owned these files.

Initial clean HEAD: `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.

The absent `.venv/bin/python` failed the capability command.
An issue-owned UV seed/copy environment then ran the current bootstrap successfully.
It uses Python 3.13.13 and the unchanged dependency manifests.
Actual Chromium, Node, and pytest-timeout executed.
The STE dictionary and PowerShell remain unavailable.

## Phase 2: Foundation and Red Proof

- [x] T004 Add independent fixture facts, actual-script execution, and failing observation guards in `tests/unit/web_portal/test_map_site_selection_race.py`.
- [x] T005 Add the real local HTTP hold and Chromium A-B journey in `tests/e2e/test_map_site_selection_race_journey.py`.
- [x] T006 Run unchanged-source red proof and retain its exact evidence in this record.

T004 requires T003. T005 requires T003 and T004. T006 requires T004 and T005.
No production edit precedes T006.

The template matched the initial commit before red execution.
Its SHA-256 was `ac1bd1a420ed6f39b2923368edac2bac902290201459dfe30b65c4fda0efdf5f`.

**Browser red**: The primary Chromium journey failed on A's option contaminating B's exact option list.
It held A at the actual HTTP server, completed B, released A, and observed both completion callbacks.
It recorded exactly two GET requests.
Result: **1 failed, zero skipped**.
Artifacts: `data/issue-3366/red/browser.log`, browser trace, screenshot, ledger, observations, and coverage.

**Offline red**: Four original selection cases failed on stale option contamination.
Fifteen independent observation and missing-input guard cases passed.
Result: **4 failed, 15 passed, zero skipped**.
Artifacts: `data/issue-3366/red/offline.log`.

The independent guard accepted known-good controls.
It rejected five bad control cases, five missing observation cases, four missing or unreadable source cases, and two incorrect request ledgers.
The guard printed checked source, request, selection, observation, and rejected-case counts.

## Phase 3: User Story 1 - Latest Site Controls

- [X] T007 [US1] Add the occurrence counter and stale-success guard in `web_portal/templates/map_viewer.html`.
- [x] T008 [US1] Verify A-B, pending B, A-B-A, and A-blank-A in the two issue-owned test files.

T007 requires T006. T008 requires T007.
Advance the counter before the blank return.
Preserve the fetch URL, method, options, count, and existing map-view counter.
Do not use cancellation or compare only site identifiers.

## Phase 4: User Story 2 - Current Errors

- [X] T009 [US2] Add response validation and guarded current-error notification in `web_portal/templates/map_viewer.html`.
- [x] T010 [US2] Verify current and stale transport, status, JSON, explicit-error, and list failures in the two issue-owned test files.

T009 requires T007. T010 requires T009.
Validate all entries before adding options.
Keep fixed safe error text, blank disabled controls, and zero stale mutations.
Add bounded ASCII action logs and rare meaningful comments.

## Phase 5: User Story 3 - Blank and Empty Choices

- [x] T011 [US3] Verify blank site, blank map, empty success, and error replacement in the two issue-owned test files.

T011 requires T010.
Require exact request deltas and actual handler execution.
An empty evidence collection cannot prove a blank-choice result.

## Phase 6: User Story 4 - Compatibility

- [x] T012 [US4] Verify option order, dimensions, safe labels, and selected-map preservation in the two issue-owned test files.
- [x] T013 [US4] Run unchanged adjacent Maps and title tests and record their results here.

T012 requires T011. T013 requires T012.
Keep existing image handling, current map-data errors, late view protection, title contrast, and theme behavior.

## Phase 7: Final Verification and Local Delivery

- [x] T014 Verify changed-region V8 coverage and independent missing-range guard failures in the two issue-owned test files.
- [X] T015 [P] Add `changelog.d/issue-3366-map-site-selection.md` without editing CHANGELOG.
- [x] T016 Run configured local quality, runtime audit, Markdown link, and STE commands and record exact outcomes here.
- [x] T017 Run final read-only SpecKit analyze and exact-manifest review using these issue-specific artifacts.
- [x] T018 Create the authorized local Conventional Commit and send the parent the exact SHA, files, red and green evidence.

T014 requires T013. T015 requires T007 and T009. T016 requires T014 and T015.
T017 requires T016. T018 requires T017.
An unavailable dictionary or PowerShell capability remains explicitly unmeasured.
Do not replace a missing capability with a success claim.
Other local failures in changed code must be repaired before the commit.

## Phase 8: Released Publication

- [x] T019 Record the parent's explicit full verified-main SHA release here at position 15 after #3353.
- [ ] T020 Rebase, read current manifests, repeat local proof, push once, and create the original-template pull request.
- [ ] T021 Verify exact-head quality, title, CodeQL, strict base checks, and a protected squash merge without admin bypass or branch deletion.
- [ ] T022 Run exact merged-main local proof in this isolated worktree and report persistent completion to the parent.

T019 requires T018 and explicit parent release. T020 requires T019.
T021 requires T020 and all required checks. T022 requires T021.
The initial SHA, observed main, and sibling reports do not release publication.
No deployment, cloud login, firmware, production store, or container action is authorized.

The parent granted sole publication and delivery on `1a06f1516223a20eef715d91a32255e6219331db`.
The [predecessor receipt](https://github.com/jmorrison-juniper/MistHelper/pull/3725#issuecomment-5949473435) records the verified base.
Live main and all open pull request file lists matched the grant before the rebase.
The issue still belongs to this session, and no open pull request exists.
The original clean local repair was `7f7f860908f1088952102df967ee5472705ea54b`.
The clean rebased repair is `eba2ef4eb546562e9fd5d9f5e5432d3b4e29cefb`.
Its exact parent is the granted full main.
Current dependency manifests match the original manifests, so no dependency restoration is needed.

Current-base proof will include the full CI collection, strict import decisions, and process-owned response evidence.
The two issue tests keep all support inside the owned files.
They import no `conftest` globals and change no shared browser support.

### Current-base repeated proof

The repeated red template matched the granted source byte-for-byte.
Its SHA-256 remained `ac1bd1a420ed6f39b2923368edac2bac902290201459dfe30b65c4fda0efdf5f`.
Full CI collection selected the primary actual Chromium race.
It failed specifically on A's stale option, with **1 failed and 589 deselected**.
The four offline race variants also failed on stale contamination.
These red records remain under `data/issue-3366/release/red/`.

The restored repair matches the original production repair byte-for-byte.
Every rendering, map-data, image, and theme region matches the granted base.
The issue-owned browser fixture now verifies the existing run-owner header.
Each evidence record names its unique run and owning process.
The fixture proves that every held response releases and its server thread stops.
Five direct import-decision cases prove normal skips and strict missing-package failure.

| Current-base measurement | Result |
| - | - |
| Full strict CI browser collection | **590 collected, 538 passed, 52 pre-existing skips**, zero failures or errors. |
| Required Maps, image, and title cases within that collection | **97 passed**, zero skipped. All 75 issue cases and 22 adjacent cases executed. |
| Complete offline Maps selection | **441 passed**, zero skipped. The original 436 cases plus five import-decision cases executed. |
| Changed JavaScript coverage | All **30 statements and four guarded returns** executed across 75 records and 216 samples. |
| Full Ruff and syntax | **Passed** on the current source. |
| Full Black | **Passed** for 2,018 files. |
| Exact current CI MYPY_PATHS | **Passed** for 665 source files. |
| Configured Bandit | **Passed**, zero issues over 214,983 code lines. No exclusions or annotations changed. |
| Required input preflight | **Passed**. Six inputs read and validated, three live guide procedures checked. |
| Full unchanged quality ratchet | **Passed**. 1,003 files discovered, 725 existing findings, zero new findings or parse errors. |
| Strict current runtime audit | **Passed** through the authorized complete hashed resolution. No known vulnerabilities. |

The 52 pre-existing browser skips have two exact reasons.
Fifty-one operator journeys run only on request.
The adjacent capture walk says: `The options page offered no version, so the save would keep an empty plan.`
Those skipped cases remain unverified, not passed.
No required Maps case skipped.

The full browser command used `UPGRADE_PORTAL_E2E_STRICT=1`, private `DATA_DIR`, private `TMPDIR`, and unreachable connector sentinels.
It used the existing repository fixtures without edits or imported `conftest` globals.

```text
rtk proxy .venv/bin/python -m pytest tests/e2e/ --browser chromium --timeout=180 --basetemp=data/issue-3366/release/full-browser-tmp --output=data/issue-3366/release/full-browser --tracing=retain-on-failure --screenshot=on --junitxml=data/issue-3366/release/full-browser.xml -p no:cacheprovider -q --tb=short -ra
```

Result: **538 passed, 52 named pre-existing skips**.
The run checked 134 audit records across eight sites, with zero leaked holds.
The live-run guard read 363 history rows across 65 modules, with zero leaked live runs.
The checkout audit trail stayed at zero lines.
All 75 issue journey records show zero page errors.
Every stale-completion assertion required zero DOM mutations.

Current-base receipts are `data/issue-3366/release/full-browser.xml`, `offline.xml`, and `coverage-summary.json`.
Current gate records remain below `data/issue-3366/release/gates/`.
The original and repeated red receipts remain separate.
The post-commit changed-scope ratchet and publication remain next.

### Caused test regression and narrow correction

The first checked publication is `8042621aa6b4ab4e9917a57d825281ffeaabc3bb`.
Fresh Quality run 36993915078 marked 32 executed issue cases failed before the E2E job exceeded its fixed 15-minute limit.
The other 27 jobs and all 22 executed adjacent Maps cases passed.
The [public hold](https://github.com/jmorrison-juniper/MistHelper/pull/3727#issuecomment-5950684079) records each failed case and successful job.
No newer same-head Quality run supersedes that evidence.
These results do not justify an infrastructure-only retry.

Unchanged-source local diagnosis disabled optional tracing and screenshots, as CI does.
It kept all 590 collection members and stopped on the first actual failure.
The result was one failure and 19 passes, not full acceptance.
`MapSiteBrowser.choose` waited for actual request 2 while the wildcard Python route callback could not run.
The request arrived only after teardown resumed Playwright event processing.
Optional tracing had concealed that test-harness defect.
Complete stdout, stderr, and JUnit remain in `data/issue-3366/release/ci-options.log` and `ci-options.xml`.

The parent authorized a correction only in the issue-owned E2E file and these existing evidence records.
A serialized regular expression excludes the exact owned local origin from Python route callbacks.
The matcher permits no other host, port, scheme, or lookalike prefix.
Direct decisions check three permitted and six denied URLs.
A real browser navigation to a second owned loopback listener must abort before any TCP connection or response.
Each process-owned case retains that negative proof in `matcher.json`.

Production bytes, all cases, assertions, coverage observers, shared fixtures, and timeout budgets remain unchanged.
The original checked head remains preserved in history.
A new unamended corrective commit requires full default-option acceptance and repeated local gates before a substantive checked push.
No workflow retry, timeout increase, protection change, new publication window, or trigger-only push is authorized.

### Final default-option correction proof

The parent recorded the narrow grant in [the public correction comment](https://github.com/jmorrison-juniper/MistHelper/pull/3727#issuecomment-5950881493).
The final full collection ran without diagnostic stopping, tracing, or screenshots.
It passed **538 of 590 cases**, with the same 52 named baseline skips.
All 97 required Maps cases passed without skips.
The unchanged offline selection passed all **441 cases** after the native abort-code correction.
These results do not reuse the tracing-enabled proof or the failed diagnostic run.

Every original test method and assertion matches the published `8042621aa6b4ab4e9917a57d825281ffeaabc3bb` version.
All 590 collection identities match the earlier full collection.
Only the issue-owned route matcher, its direct negative proof, and these evidence records changed.

The matcher records cover 75 actual native aborts and 675 explicit URL decisions.
Each actual request names its exact blocked URL once.
Each probe receives no response and records zero accepted TCP connections at its separate loopback listener.
Only `net::ERR_BLOCKED_BY_CLIENT` and `net::ERR_BLOCKED_BY_CLIENT.Inspector` satisfy the native failure assertion.
Generic errors, timeouts, connection refusals, and substring matches cannot pass.
Each socket and probe page closes in the same test.

The earlier setup validation with a missing output parent did not execute valid acceptance.
Its JUnit errors remain in `browser-setup-error.xml` and `offline-setup-error.xml`.
The first native proof rejected Chromium's `.Inspector` suffix.
Its 75 setup errors remain in `browser-negative-proof-error.xml`.
Neither error set counts as passing evidence.
The final prepared runs below supersede those local failures without deleting their records.

| Final correction evidence | Result |
| - | - |
| `data/issue-3366/correction/final-browser.xml` | 590 collected, 538 passed, 52 named baseline skips, zero failures or errors. |
| `data/issue-3366/correction/final-offline.xml` | 441 passed, zero skipped, failed, or errored. |
| `data/issue-3366/correction/coverage-summary.json` | 75 records, 216 samples, all 30 changed statements and four guarded returns executed. |
| Stale-window observation | All 47 windows have zero DOM mutations and page errors. |
| Production and offline source comparison with `8042621aa6b4ab4e9917a57d825281ffeaabc3bb` | Byte-identical. The production SHA-256 remains `a4a09ecea9a52b47d311c4f5a1eba68b8f55e81ec45e39e43960559cdf35a7fb`. |
| Syntax, full Ruff, full Black | Passed. Black checks 2,018 files. |
| Exact CI MYPY_PATHS | Passed for 665 source files. |
| Configured Bandit | Zero issues over 214,983 lines. No settings, exclusions, or annotations changed. |
| Six-input preflight | Six required inputs read and validated, three guide procedures checked. |
| Full unchanged quality ratchet | 1,003 discovered files, 725 existing findings, zero new findings or parse errors. |
| Strict complete runtime audit | No known vulnerabilities or ignored findings. |

The exact final browser command uses strict mode, private paths, and unreachable connector sentinels:

```text
rtk proxy .venv/bin/python -m pytest tests/e2e/ --browser chromium --timeout=180 --tracing=off --screenshot=off --basetemp=data/issue-3366/correction/socket-proof-full-tmp --output=data/issue-3366/correction/final-browser --junitxml=data/issue-3366/correction/final-browser.xml -p no:cacheprovider -q --tb=short -ra
```

Result: **538 passed, 52 named baseline skips**.
The run reports zero leaked holds, zero leaked live runs, and an unchanged zero-line checkout audit trail.
The new unamended commit, clean committed-scope ratchet, and fresh corrective-head CI results remain next.

## Exact Local Command Register

Use this worktree's `.venv` and issue-owned artifacts.
Read the current CI MYPY_PATHS before each commit or released-base validation.
Retain original gate settings, baselines, exclusions, and thresholds.

| Gate | Command |
| - | - |
| Syntax | `rtk proxy .venv/bin/python -m py_compile MistHelper.py tests/e2e/test_map_site_selection_race_journey.py tests/unit/web_portal/test_map_site_selection_race.py` |
| Full Ruff | `rtk proxy .venv/bin/python -m ruff check .` |
| Full Black | `rtk proxy .venv/bin/python -m black --check --diff .` |
| Exact CI types | `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` |
| Bandit exclusion guard | `rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/foundation/support/utils/zen_city_metadata.py --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'` |
| Full Bandit | `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r .` |
| Full quality ratchet | `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report data/issue-3366/gates/quality.json --summary data/issue-3366/gates/quality.md` |
| Runtime audit | `rtk proxy .venv/bin/python -m pip_audit -r requirements.txt` |
| Markdown links | `rtk proxy .venv/bin/markdown-link-check specs/3366-map-site-selection changelog.d/issue-3366-map-site-selection.md` |
| STE | `rtk proxy .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 specs/3366-map-site-selection changelog.d/issue-3366-map-site-selection.md tests/e2e/test_map_site_selection_race_journey.py tests/unit/web_portal/test_map_site_selection_race.py` |

If normal pip-audit aborts, use the authorized runtime-only hashed UV resolution.
Then run pip-audit with `--no-deps --disable-pip --require-hashes --strict`.
Keep the Git-only development tool outside the runtime audit.

**Browser selection**: `tests/e2e/test_map_site_selection_race_journey.py`, `tests/e2e/test_map_viewer_image.py`, and `tests/e2e/test_map_title_contrast.py`.

**Offline selection**: `tests/maps/`, `tests/unit/web_portal/test_map_image_route.py`, `tests/unit/web_portal/test_map_viewer_xss.py`,
`tests/unit/web_portal/test_map_title_theme.py`, and `tests/unit/web_portal/test_map_site_selection_race.py`.

Use `--browser chromium`, bounded pytest timeouts, private `--basetemp`, private `--output`, and retained failure traces and screenshots.
Run no unrelated store-dependent local suite.
All original required remote checks remain active after publication.

## Verification Results

The final production template SHA-256 is `a4a09ecea9a52b47d311c4f5a1eba68b8f55e81ec45e39e43960559cdf35a7fb`.
The comparison proved that only `siteChoiceNumber` and `onSiteChange()` changed.
All rendering, map-data, image, and theme regions match the initial source byte-for-byte.

### Behavior

| Evidence | Result |
| - | - |
| Primary unchanged-source Chromium race | **1 failed**, zero skipped. A's option contaminated B's list. |
| Original offline race plus independent guard proof | **4 failed, 15 passed**, zero skipped. All four race failures showed stale contamination. |
| Final Chromium issue and adjacent Maps selection | **97 passed**, zero failures, errors, or skips. This includes 75 issue cases and 22 unchanged adjacent cases. |
| Final offline issue and adjacent Maps selection | **436 passed**, zero failures, errors, or skips. This includes 196 issue cases and 240 unchanged adjacent cases. |
| Explicit independent observation and coverage guards | **23 passed**, with checked counts and rejected inputs in the log. |
| Precise changed-region browser coverage | **100 percent** of 30 changed statement lines and four guarded return branches executed. |

The coverage result uses 75 real Chromium records and 216 samples.
It includes successful and failed responses whose headers arrived before a later site choice.
Their actual JSON bodies completed after that later choice.
These cases prove the guards after JSON parsing, not only the guard before parsing.
All stale windows recorded zero DOM mutations and zero uncaught page errors.
The adjacent tests measured all four title themes at or above 4.5:1.

Final behavior artifacts use `data/issue-3366/green/verified-browser*` and `data/issue-3366/green/verified-offline*`.
The exact request ledgers, callback counts, console records, screenshots, and control observations remain under those paths.
The coverage summary is `data/issue-3366/coverage/verified-summary.json`.
The guard counts are in `data/issue-3366/green/verified-guards.log`.
The original red evidence remains unchanged.

### Executed behavior commands

Both commands used `rtk proxy env PYTHONDONTWRITEBYTECODE=1` and an absolute issue-owned `DATA_DIR`.
They also used private pytest caches and JUnit output paths.

```text
.venv/bin/python -m pytest tests/e2e/test_map_site_selection_race_journey.py tests/e2e/test_map_viewer_image.py tests/e2e/test_map_title_contrast.py --browser chromium --timeout=120 --basetemp=data/issue-3366/green/verified-browser-tmp --output=data/issue-3366/green/verified-browser --tracing=retain-on-failure --screenshot=on --junitxml=data/issue-3366/green/verified-browser.xml -o cache_dir=data/issue-3366/green/verified-browser-cache -q
```

Result: **97 passed**.

```text
.venv/bin/python -m pytest tests/maps/ tests/unit/web_portal/test_map_image_route.py tests/unit/web_portal/test_map_viewer_xss.py tests/unit/web_portal/test_map_title_theme.py tests/unit/web_portal/test_map_site_selection_race.py --timeout=120 --basetemp=data/issue-3366/green/verified-offline-tmp --junitxml=data/issue-3366/green/verified-offline.xml -o cache_dir=data/issue-3366/green/verified-offline-cache -q
```

Result: **436 passed**.

### Configured local gates

| Command from the register | Result |
| - | - |
| Syntax | **Passed** for MistHelper.py and both new test files. |
| Full Ruff | **Passed**. No findings. |
| Full Black | **Passed**. All 2,002 files remain unchanged. |
| Exact CI MYPY_PATHS | **Passed**. No issues in 663 source files. |
| Bandit exclusion guard and full Bandit | **Passed**. The scan checked 213,949 code lines and found zero issues. Existing suppressions remain unchanged. |
| Full unchanged test-quality ratchet | **Passed**. It checked 994 files and 725 existing findings, with zero new findings or parse errors. |
| Owned Markdown links | **Passed**. The guard checked all five tracked Markdown files and found zero broken links. |
| Dictionary-based STE | **UNAVAILABLE**. `data/ste_dictionary.json` is missing. Seven-file heuristic prose results are partial, not a dictionary measurement. |
| PowerShell-dependent checks | **UNAVAILABLE**. Neither `pwsh` nor `powershell` is installed. No replacement shared-state script ran. |

The normal runtime audit aborted in the known macOS `ensurepip` path.
The authorized alternative resolved the unchanged runtime requirements with hashes:

```text
rtk proxy env UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 UV_LINK_MODE=copy uv pip compile requirements.txt --python .venv/bin/python --native-tls --generate-hashes --quiet --output-file data/issue-3366/runtime-audit-lock.txt
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes -r data/issue-3366/runtime-audit-lock.txt --strict
```

Result: **Passed**. No known vulnerabilities.
The audit includes runtime requirements only, not the Git-only development tool.
No dependency, baseline, suppression, exclusion, README, CHANGELOG, or shared feature state changed.

### Final analysis

The read-only SpecKit analysis checked all 30 requirements and all 22 tasks.
It found complete requirement coverage, zero functional defects, zero incorrect evidence claims, and no unauthorized source changes.
It independently checked the raw browser observations and coverage records.

The analysis disclosed C1, a formal alignment conflict with older constitution requirements.
The documented exceptions follow the explicit task scope, including comments, commit format, file ownership, and restricted deployment authority.
This repair does not amend project governance or authorize additional work.
C1 is not a functional defect or a reason to violate the authorized scope.

The local commit receipt remains next.
The commit receipt belongs in the parent handoff, not in a self-referencing commit file.
Publication, merge, and exact-main proof now require current-base verification under the explicit parent release.
