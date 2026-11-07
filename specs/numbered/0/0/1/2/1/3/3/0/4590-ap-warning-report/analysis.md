# AP warning report progress and validation

## Result

The report package, natural-key strategy, CLI menu 307, and portal listing are implemented.
The user requests progress rather than waiting for the unfinished WAN feature.
A three-way README merge preserves both features without conflict.
The obsolete wait automation is removed.

## Artifact analysis

| ID | Severity | Finding | Resolution |
| --- | --- | --- | --- |
| I1 | Medium | The export contract described a Boolean return, but the callable returns a row count. | The contract now specifies the verified row count. |
| B1 | Resolved | The README overlap originally delayed menu integration. | A measured three-way merge preserves both features. Menu integration proceeds independently. |

All fourteen functional requirements have task coverage.
FR-001 now has CLI registration and portal visibility tests.
The other requirements have implementation and tests.
There are no unresolved code-meaning or connection-state questions.
All seven success criteria map to the source, row, definition, and failure-path tests.
The final analysis covers 21 requirements and success criteria across 25 tasks.
Coverage is 100 percent, with no critical findings or unmapped tasks.

## Verified behavior

The report includes connected and disconnected inventory APs with nonzero trouble codes.
It preserves unknown codes and observation times.
It does not equate historical trouble evidence with a current LED color.
Every required source read finishes before persistence.
Failures on later pages prevent partial reports.
The real CSV writer retains the report columns.
The real SQLite writer replaces repeated organization-and-MAC identities without duplicate AP rows.

## Local gate evidence

Commands ran from the feature worktree.
The paths below use the worktree virtual environment.

| Command | Result |
| --- | --- |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\ap_warning_report tests\integration\ap_warning_report tests\integration\test_mistapi_sdk_compatibility.py tests\unit\refactors\test_sqlite_database_writer.py -q --cov=src.operations.exporting.ap_warning_report --cov-report=term-missing --cov-fail-under=90` | 160 passed. New report package coverage: 100 percent. |
| `rtk proxy .venv\Scripts\python.exe -m ruff check src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py tests\unit\ap_warning_report tests\integration\ap_warning_report` | All checks passed. |
| `rtk proxy .venv\Scripts\python.exe -m black --check src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py tests\unit\ap_warning_report tests\integration\ap_warning_report` | Twelve files need no format changes. |
| `rtk proxy .venv\Scripts\python.exe -m mypy src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py --config-file pyproject.toml` | Success. Six source files checked. |
| `rtk proxy .venv\Scripts\python.exe -m bandit -c pyproject.toml -r src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py -q` | No findings. |
| `rtk proxy .venv\Scripts\python.exe -m compileall -q src\operations\exporting\ap_warning_report` | No output. |
| `rtk proxy .venv\Scripts\radon.exe cc src\operations\exporting\ap_warning_report -j \| .venv\Scripts\complexity-gate.exe --max 10` | All functions within the threshold. |
| `rtk proxy .venv\Scripts\python.exe -m pylint src\operations\exporting\ap_warning_report --fail-under=9.5` | 9.73 out of 10. |
| `rtk proxy .venv\Scripts\python.exe -m pydocstyle src\operations\exporting\ap_warning_report` | No violations. |
| `rtk proxy .venv\Scripts\interrogate.exe src\operations\exporting\ap_warning_report --fail-under 90` | 100 percent documentation coverage. |
| `rtk proxy .venv\Scripts\python.exe -m vulture src\operations\exporting\ap_warning_report --min-confidence 70` | No findings. |
| `rtk proxy .venv\Scripts\symbol-diff.exe --base origin/main src\foundation\support\refactors\endpoint_primary_key_strategies.py` | No module-level name changed. |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\guardrails\test_nested_package_structure.py tests\guardrails\test_process_folder_structure.py tests\guardrails\test_changelog_fragment_policy.py -q -rs` | 37 passed. One pull-request-only diff check skipped outside a pull request event. |
| `rtk proxy .venv\Scripts\markdown-link-check.exe specs\numbered\0\0\1\2\1\3\3\0\4590-ap-warning-report changelog.d\issue-4590-ap-warning-report.md` | Ten tracked Markdown files scanned. Zero broken links. |
| `rtk proxy .venv\Scripts\python.exe -m py_compile src\foundation\support\refactors\endpoint_primary_key_strategies.py` | No output. |
| `rtk proxy .venv\Scripts\python.exe -m pydocstyle src\foundation\support\refactors\endpoint_primary_key_strategies.py` | No violations. |

The SDK compatibility tests passed with the targeted selection.
This result does not constitute full repository SDK verification.

The test run reported one Dash plugin deprecation warning and three existing SQLite fixture resource warnings.
The feature tests do not use production credentials.
No full-suite coverage run, portal browser run, or container deployment occurred.
The live menu 307 report result appears below.
The portal checks use the real Flask routes without a browser or cloud session.

## Environment notes

The standard bootstrap failed because locked dependency metadata did not match.
The separate bootstrap issue preserves the full failure output.
`uv sync --frozen --extra dev` installed the existing lock without dependency-file changes.
The first SQLite integration assertion used an unsanitized table name.
The test now uses the established SQLite table name normalization.
The first test-quality check found two missing SQLite failure cases.
The added cases reject empty bodies and malformed JSON before the SQLite writer runs.
Their first assertions expected the internal client message rather than the public report message.
The assertions now use the public error boundary, and both cases pass.
The analyzer requires literal failure bodies.
The fixtures now bind those bodies directly to SDK response objects.
The test-quality baseline remains unchanged.

## Recovery filtering verification, issues #4624 and #4625

The completion worktree preserves the previous agent's uncommitted changes without modifying its files.
The branch uses current `origin/main`.
The recovery rules retain untimed observations, unknown evidence, and repeated interruptions.
Verified recoveries use a separate output and database strategy.

The artifact review covers 20 functional requirements, nine success criteria, and 30 tasks.
Every requirement has an implementation or verification task.
The review found contradictory missing-timestamp rules in the earlier specification and plan.
The corrected rules consistently retain untimed nonzero observations.
No requirement lacks task coverage.
Publication task T030 remains external to local implementation verification.

The first local recovery test exposed fractional epoch rounding at an identical evidence cutoff.
The repair compares validated numeric epochs without converting them through ISO display precision.
A deterministic regression covers fractional history boundaries and the fresh statistics cutoff.
Malformed event catalogue keys now retain uncertainty instead of raising an uncaught type error.
New recovery methods remain within 25 lines and complexity ten.
The existing row builder and export orchestration retain their documented structural debt.

### Completion worktree gates

| Command | Result |
| --- | --- |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\ap_warning_report tests\integration\ap_warning_report tests\e2e\web_portal\test_ap_warning_report.py --cov=src.operations.exporting.ap_warning_report --cov-report=term-missing -q` | 181 passed. Package coverage: 96.65 percent. |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\integration\test_mistapi_sdk_compatibility.py tests\unit\refactors\test_sqlite_database_writer.py tests\guardrails\test_endpoint_catalog.py tests\guardrails\test_nested_package_structure.py tests\guardrails\test_process_folder_structure.py tests\guardrails\test_changelog_fragment_policy.py -q -rs` | 189 passed. One pull-request-only check skipped. |
| `rtk proxy .venv\Scripts\python.exe -m ruff check src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py tests\unit\ap_warning_report tests\integration\ap_warning_report` | All checks passed. |
| `rtk proxy .venv\Scripts\python.exe -m black --check src\operations\exporting\ap_warning_report tests\unit\ap_warning_report tests\integration\ap_warning_report` | Thirteen files unchanged. |
| `rtk proxy .venv\Scripts\python.exe -m mypy src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py --config-file pyproject.toml` | Success. Six source files checked. |
| `rtk proxy .venv\Scripts\python.exe -m bandit -c pyproject.toml -r src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py -q` | No findings. |
| `rtk proxy .venv\Scripts\python.exe -m pip_audit -r requirements.txt` | No known vulnerabilities. |
| `rtk proxy .venv\Scripts\symbol-diff.exe --base origin/main src\foundation\support\refactors\endpoint_primary_key_strategies.py` | No module-level name changed. |

The extended menu and portal selection passed 343 tests with one absent-category skip before the final fractional-boundary test.
The SDK guard checked 575 call signatures and found zero known failures.
It reported ten unresolved sites and 364 unverifiable signatures, so those sites remain outside its proof.
The dependency bootstrap completed with the locked development dependencies.
No container definition or dependency manifest changed.
No container build or full repository test run occurred.

### Recovery live evidence

The authorized read-only menu run started at `2026-11-06T23:21:46.987496+00:00`.
It finished at `2026-11-06T23:31:25.827554+00:00`.
It read 3,101 sites, 14,997 inventory APs, and statistics for 14,903 APs.
The run produced 11 candidates and retained all 11.
Every candidate had complete history, but none had sufficient later connection evidence.
No AP qualified for a recovery export during this run.
This result matches the conservative rule. A code or connection status alone cannot remove a warning.
Replaying the captured evidence with the final code produced zero decision differences.

The original 20-record comparison used independent evidence collected at approximately `2026-11-06T23:04:03+00:00`.
It retains 16 observations and separates four verified recoveries.
The screenshot case qualifies through trouble at `22:17:01Z` and cloud connection at `22:17:03Z`, with fresh connected statistics.
Eleven original observations lacked a later connection.
Three had newer or changed trouble, and two had a connection no later than their trouble.
These counts do not represent the current report because the 15-minute window and network state changed between runs.
The preceding live run also retained two repeatedly interrupted APs rather than hiding them.

The live command used the project interpreter with `MistHelper.py --menu 307 --output-format csv`.
A local evidence helper supplied the existing ignored environment file and preserved unmodified SDK responses.
Standalone mode wrote CSV only and explicitly skipped ArangoDB and Redis.
Raw responses, candidate evidence, original comparison evidence, and output files remain private and local.

## Menu integration evidence

The four new menu and portal tests failed before registration and passed after registration.
The existing identity guard detected the intentionally added menu.
Its expected counts and exact identity digests now include menu 307 without weakening its comparisons.

| Command | Result |
| --- | --- |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\ap_warning_report tests\integration\ap_warning_report tests\e2e\web_portal\test_ap_warning_report.py tests\guardrails\test_menu_number_uniqueness.py tests\guardrails\test_operation_registry_menu_coverage.py tests\guardrails\test_portal_operation_coverage.py tests\guardrails\test_destructive_menu_docs.py tests\guardrails\test_endpoint_catalog.py tests\guardrails\test_e2e_shard_partition.py tests\guardrails\test_nested_package_structure.py tests\guardrails\test_process_folder_structure.py tests\integration\test_mistapi_sdk_compatibility.py -q --cov=src.operations.exporting.ap_warning_report --cov-report=term-missing --cov-fail-under=90` | 262 passed. One absent unsafe-category fixture skipped. Report package coverage: 100 percent. |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\scripts\test_menu_api_map.py -q` | 36 passed. One optional lint check skipped. |
| `rtk proxy .venv\Scripts\python.exe -m ruff check .` | All checks passed with the repository exclusion settings. |
| `rtk proxy .venv\Scripts\python.exe -m mypy src MistHelper.py wsgi.py scripts\mist_ideas_analyzer_pkg\__init__.py scripts\mist_ideas_distiller_v2_pkg\__init__.py --config-file pyproject.toml` | Success. No issues in 873 source files. |
| `rtk proxy .venv\Scripts\python.exe -m black --check MistHelper.py src\foundation\support\utils\operation_registry.py web_portal\services\operation.py web_portal\menu_registry.py tests\unit\ap_warning_report\test_menu.py tests\e2e\web_portal\test_ap_warning_report.py tests\guardrails\test_endpoint_catalog.py` | Seven files need no format changes. |
| `rtk proxy .venv\Scripts\python.exe -m py_compile MistHelper.py src\foundation\support\utils\operation_registry.py web_portal\services\operation.py web_portal\menu_registry.py` | No output. |
| `rtk proxy .venv\Scripts\python.exe -m bandit -c pyproject.toml MistHelper.py src\foundation\support\utils\operation_registry.py web_portal\services\operation.py web_portal\menu_registry.py -q` | No findings. |
| `rtk proxy .venv\Scripts\python.exe -m pydocstyle src\operations\exporting\ap_warning_report src\foundation\support\utils\operation_registry.py web_portal\services\operation.py web_portal\menu_registry.py` | No violations. |
| `rtk proxy .venv\Scripts\python.exe scripts\generate_menu_wiki.py` | Both menu-reference pages generated. |
| `rtk proxy .venv\Scripts\python.exe -m scripts.menu_api_map --check` | All 16 map pages match the source for 307 menu options. |

STE checks passed for the changed instruction files, operator guide, release fragment, and specification records.
Symbol comparisons found no lost module-level names.
`MistHelper.py` adds the intended `ApWarningReport` import.
The registry, portal group module, and static portal map preserve their module-level names.

Explicitly type-checking the excluded portal modules reported 71 existing annotation errors.
Explicitly linting the generated portal map reported two existing long strings.
The configured repository mypy and Ruff commands passed without changing their exclusions.
The generated portal map changes only the new menu row.
The Markdown link check scanned 21 repository-local documents and found zero broken links.
The published wiki pages use wiki-relative links and do not enter that local-link check.
An initial check against the unpublished wiki copies reported 541 unresolved wiki-local targets.
The generated map drift check verifies those copies against their source instead.
The final test-quality procedure passed after integration commit `c0d0c56`.
The intended base resolved to `5d444bda23ea50de131d67b6e6fcf37055adfa77`.
The preflight read and validated all four required inputs.

```powershell
rtk git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
rtk git rev-parse --verify "origin/main^{commit}"
rtk proxy .venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
rtk proxy .venv\Scripts\test-quality-analyzer.exe --gate --config .github\test-quality-config.toml --baseline .github\test-quality-baseline.json --changed-from origin/main --full-gate-path .github\workflows\ci.yml --full-gate-path requirements-dev.txt
```

The analyzer reported `gate_scope: 9 files checked, 0 findings checked`.
The result was `gate: 0 new findings vs baseline`, with zero parse errors.
The two skipped discovery records describe roots omitted by the changed-test selection, not skipped feature files.
No baseline changed.
All 25 feature tasks are complete.
No pull request, merge, production deployment, or change to pull request #4208 is part of this implementation.

## End-to-end follow-up

The user requested end-to-end testing and repair of each discovered issue.
The earlier tests remain valid for their stated scope.
However, their green result did not prove correct portal execution.
The initial completion assessment was incomplete.

The added SDK transport test uses the real CLI dispatcher, SDK endpoint functions, HTTP response parser, pagination, and CSV writer.
Only HTTP transport and runtime selection are controlled.
Twelve requests cover all sources and multiple pages.
The saved report includes connected and disconnected APs.
It excludes cleared codes, absent observations, and statistics-only devices.
Sixteen negative cases cover HTTP 403, HTTP 503, empty bodies, and malformed JSON.
Each case verifies the exact failing source and page before checking that no report exists.

Issue #4592 records a defect in the initial test harness.
The SDK rejected its synthetic hostname before transport.
The initial sixteen negative-case passes are invalid.
The repaired harness uses a supported SDK hostname with controlled transport.
Its exact-page assertions reject unrelated early failures.

Real portal execution exposed issue #4593.
A successful zero-match report with missing trouble evidence appeared as failed.
The portal did not recognize the report's empty-result wording.
The report now uses the existing recognized empty-record wording.
The integer return contract and source-failure behavior remain unchanged.
Portal tests obtain the real CSRF token, start menu 307, wait for its worker, and read its terminal status.
They cover missing evidence, cleared codes, a saved CSV, source failure, and output failure.
An initial portal fixture lacked the normal runtime output directory.
That fixture was corrected before the report-classification defect was isolated.

## Live report result

Menu 307 completed on November 6, 2026.
It scanned 14,997 inventory APs and made 3,101 site-statistics requests.
The requests returned statistics for 14,903 APs and had no read failures.
The report logged 365 missing trouble codes and excluded 14,612 observations outside the time window.
It wrote 20 recent trouble records to `data/ApWarningReport_a8c903ae-e6d0-42a7-b815-fe395dea8017.csv`.
The run took 9.34 minutes. The report time was `2026-11-06T22:22:04.563864+00:00`.
All 20 rows had a known code definition, a site name, and a unique MAC address.
Their observation ages ranged from 1.959 to 10.909 minutes. No row exceeded the 15-minute window.

| Code | Definition | Count | Connection state |
| --- | --- | ---: | --- |
| `02` | No ethernet link | 4 | 4 disconnected |
| `03` | No IP address | 6 | 6 disconnected |
| `07` | No DNS response | 9 | 8 connected, 1 disconnected |
| `12` | Cloud unreachable | 1 | 1 connected |

Nine APs were connected when Mist returned their statistics. Eleven APs were disconnected.
Connection state is separate from the trouble code.
A recent observation does not prove that the LED remains active or that the fault remains present.
The run used standalone mode, so it wrote the CSV and skipped ArangoDB and Redis writes.

## Recent-window validation

| Command | Result |
| --- | --- |
| `rtk proxy ..\MistHelper\.venv\Scripts\python.exe -m pytest tests\unit\ap_warning_report tests\integration\ap_warning_report -q --cov=src.operations.exporting.ap_warning_report --cov-report=term-missing --cov-fail-under=90` | 122 passed. Package coverage: 98.99 percent. |
| `rtk proxy ..\MistHelper\.venv\Scripts\python.exe -m ruff check src\operations\exporting\ap_warning_report tests\unit\ap_warning_report tests\integration\ap_warning_report` | All checks passed. |
| `rtk proxy ..\MistHelper\.venv\Scripts\python.exe -m black --check src\operations\exporting\ap_warning_report tests\unit\ap_warning_report tests\integration\ap_warning_report` | Thirteen files would remain unchanged. |
| `rtk proxy ..\MistHelper\.venv\Scripts\python.exe -m mypy src\operations\exporting\ap_warning_report --config-file pyproject.toml` | Success. Five source files checked. |
| `rtk proxy ..\MistHelper\.venv\Scripts\python.exe -m bandit -c pyproject.toml -r src\operations\exporting\ap_warning_report -q` | No findings. |
| `rtk proxy ..\MistHelper\.venv\Scripts\python.exe -m compileall -q src\operations\exporting\ap_warning_report` | No output. |
| `rtk proxy git diff --check` | No output. |
| `rtk proxy ..\MistHelper\.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\2\1\3\3\0\4590-ap-warning-report\spec.md specs\numbered\0\0\1\2\1\3\3\0\4590-ap-warning-report\tasks.md specs\numbered\0\0\1\2\1\3\3\0\4590-ap-warning-report\analysis.md documentation\ap-warning-report.md changelog.d\issue-4624-ap-warning-window.md` | Scores: 96, 98, 90, 95, and 96. All five files passed. |
| `rtk proxy ..\MistHelper\.venv\Scripts\markdown-link-check.exe specs\numbered\0\0\1\2\1\3\3\0\4590-ap-warning-report changelog.d\issue-4624-ap-warning-window.md documentation\ap-warning-report.md` | Ten tracked files scanned. Zero broken links. |

The test run also confirmed that the site lock trail had zero lines before and after the tests.

The integrated command in the menu evidence table was repeated after the repair.
It passed 284 tests, with one unrelated absent-category skip and 100 percent report-package coverage.
The seventeen new SDK-flow cases passed.
All seven AP portal cases passed, including five worker execution cases.
Targeted Ruff, Black, mypy, and Bandit checks passed.
Mypy checked five report source files.
The four changed Markdown documents passed STE with scores of 95, 99, 96, and 89.
The test-quality baseline remains unchanged.
