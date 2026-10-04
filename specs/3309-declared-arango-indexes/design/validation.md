# Validation Record: Declared ArangoDB indexes

The initial sections contain the historical measurements from 2026-10-01.
The local refresh record contains the repeated measurements on the earlier accepted base.
The publication record contains the repeated measurements on the approved predecessor.

## Initial evidence

The issue was open, unassigned, and had no comments before the claim.
The authenticated account was `jmorrison-juniper`.
The claim added the `bug`, `src`, `tests`, and `in-progress` labels.
The app session is `5a6310ca-dc9b-4058-bb3a-737ea559440a`.
Both live checks covered all 12 open pull requests and their exact files.
No reserved file overlapped an open pull request.

The base revision is `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
That revision is not a remote authorization grant.
The production writer did not read the strategy indexes.
The installed SDK is `python-arango` 8.3.5.

## Baseline

| Command | Result |
| - | - |
| `rtk proxy python3.13 -m pytest tests/unit/test_arango_writer.py -q --no-cov` | Could not run because the initial interpreter lacked pytest |
| `rtk proxy env UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 UV_LINK_MODE=copy uv venv --python python3.13 --seed .venv` | Passed with Python 3.13.13 and an owned environment |
| `rtk proxy .venv/bin/python scripts/bootstrap_worktree.py` | Passed with current runtime and development manifests |
| `rtk proxy .venv/bin/python -m pytest tests/unit/test_arango_writer.py tests/unit/test_router.py -q --no-cov` | Passed all 289 tests |

## Repair evidence

The unchanged writer failed 23 of 26 declared-index tests.
Ten parameterized cases used five unchanged strategy fixtures across new and existing collections.
Their failure compared zero actual index requests against the exact declared requests.
Eight invalid-declaration cases failed because the writer raised no error.
The run reported zero collection errors and zero skips.
The three existing empty or missing declaration cases passed.

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/arango_indexes/test_declared_indexes.py -q --no-cov --tb=short --junitxml=/Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/red-index-tests.xml
```

The final offline command passes 445 tests with zero skips.
It includes 71 feature tests and 374 existing adjacent database tests.
The suite checks new and existing collections with five unchanged strategy fixtures.
The native SDK tests exercise the actual index formatter, connection parser, and query explanation return shape.

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/arango_indexes tests/contract/test_arango_declared_indexes.py tests/unit/test_arango_writer.py tests/unit/test_router.py tests/unit/db tests/unit/refactors/test_sqlite_database_writer.py -q --tb=short --cov=src.foundation.persistence.db.arango_writer --cov=src.foundation.persistence.db.database_schema_utils --cov-branch --cov-report=term-missing --cov-report=json:/Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/index-coverage.json --cov-fail-under=90
```

The two changed database modules reach 96.48 percent combined statement and branch coverage.
`database_schema_utils.py` reaches 100 percent.
All seven new or changed methods reach 100 percent statement and branch coverage.
The unchanged writer methods contain the remaining uncovered lines.
Existing SQLite tests emit three warnings about unclosed database connections.
Those warnings do not fail the tests and do not belong to this repair.

| Behavior | Measured result |
| - | - |
| First complete declaration | One ordered persistent request per distinct declared field |
| Repeated declaration | Zero additional index requests |
| Failure on the second field | Two attempted requests and zero document imports |
| Retry after that failure | Five unconfirmed field requests, including equal-index reuse |
| Failed strategy extension | Preserve the earlier confirmed field and retry the four unconfirmed fields |
| Concurrent first writes | One complete five-field request set and two successful document writes |
| Concurrent retry after the first failure | One failed request, then one complete five-field retry |
| Separate server, database, or account | Each scope sends its own complete five-field request set |
| Independent same-scope clients | Share one check while retaining each writer's own client |
| Native empty or malformed JSON | Expose the SDK exception, import no document, then retry all five fields |
| Invalid test targets | Reject 13 URLs with `checked_count=1` before any connection |
| Existing batching | Preserve the 5,000-record boundary and the final one-record batch |
| Record values | Preserve full prepared documents and 30 generated JSON examples |

## Integration evidence

The isolated ArangoDB 3.12.4-3 store passed both live tests.
Its endpoint was `http://127.0.0.1:9650`.
The container, volume, network, and compose project used `misthelper-tmp-issue3309-indexes-5a6310ca`.
The service used the issue-specific profile and started with `--no-deps`.
Its published address was `127.0.0.1:9650`.
It started no production dependency.

```bash
rtk proxy env MISTHELPER_ISSUE3309_ARANGO_URL=http://127.0.0.1:9650 .venv/bin/python -m pytest tests/integration/test_arango_declared_indexes_live.py -q -s --no-cov --tb=short
```

The combined run included both live tests and passed all 445 tests before the final two native JSON cases were added.
The final offline run includes those two additional cases.
The repair therefore has 447 distinct passing tests across the offline and live commands.

The live proof compares 1,001 complete prepared documents before and after index creation.
It excludes only the server-owned `_id` and `_rev` fields from the comparison.
The normal optimizer plan changes from zero index nodes to one index node on `status`.
The selective query returns exactly `["action-0"]`.
The collection contains exactly five declared non-unique persistent indexes.
An equal `status` index request retains its index identifier and returns `isNewlyCreated=False`.
A replacement write retains one document and updates its status.

The first query proof exposed a test's incorrect REST wrapper assumption.
The repair corrected that helper to the native SDK plan shape and added a native SDK contract case.
The subsequent live proof passed.

Each fixture removed its own issue-prefixed database.
The owned store contained only `_system` before container cleanup.
The session removed the exact container, volume, and network.
All three exact-name cleanup scans returned empty results.
No production store access occurred.

## Quality and writing coverage

| Exact command | Result |
| - | - |
| `rtk proxy .venv/bin/python -m ruff check .` | Passed with zero findings |
| `rtk proxy .venv/bin/python -m black --check --diff .` | Passed across 2,007 files |
| `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Passed across 663 source files |
| `rtk proxy .venv/bin/bandit-exclude-check --pyproject pyproject.toml` | Passed both separator spellings |
| `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r . -q -f json -o /Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/bandit-report.json` | Passed across 786 files with zero findings and zero read errors |
| `rtk proxy .venv/bin/python -m pylint src/ --fail-under=9.5` | Passed with a score of 9.83 |
| `rtk proxy bash -o pipefail -c '.venv/bin/radon cc src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -j \| .venv/bin/complexity-gate --max 10'` | Passed every configured block |
| `rtk proxy .venv/bin/vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Passed with zero findings |
| `rtk proxy .venv/bin/pydocstyle src/ wsgi.py web_portal` | Passed |
| `rtk proxy .venv/bin/interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | Passed with 99.6 percent coverage |
| `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --log-level WARNING` | Passed with 997 files checked, 725 existing findings, zero new findings, and zero parse errors |
| `rtk proxy .venv/bin/check-citations src tests` | Passed 251 citations with zero unresolved references |
| `rtk proxy .venv/bin/diagram-refs --docs-dir documentation/diagrams --extra-files README.md --allowlist-file .github/diagram-refs-allowlist.txt` | Passed 153 references across 15 diagrams |

The syntax command compiles `MistHelper.py` and all nine changed Python files.
All compile checks pass.
The new function review finds no function above 25 lines.

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py src/foundation/persistence/db/arango_writer.py src/foundation/persistence/db/database_schema_utils.py tests/unit/arango_indexes/conftest.py tests/unit/arango_indexes/fakes.py tests/unit/arango_indexes/test_declared_indexes.py tests/unit/arango_indexes/test_retry_concurrency.py tests/unit/arango_indexes/test_preservation.py tests/contract/test_arango_declared_indexes.py tests/integration/test_arango_declared_indexes_live.py
```

The unchanged test-quality ratchet initially rejected missing native empty-body and malformed-JSON evidence.
The final cases use actual SDK connection parsing, explicit source calls, and invalid wire bytes.
They prove the original exception and complete-check retry.
The ratchet then reports zero new findings.
The configuration, baseline, exclusions, and suppressions remain unchanged.

### Runtime dependency audit

The configured `pip-audit -r requirements.txt` aborts before an audit on the uv-managed macOS interpreter.
Its temporary interpreter fails during `ensurepip` with `SIGABRT`.
This result is not an audit pass.

```bash
rtk proxy env UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 UV_LINK_MODE=copy uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file /Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/runtime-audit-requirements.txt --quiet
rtk proxy .venv/bin/pip-audit -r /Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/runtime-audit-requirements.txt --no-deps --disable-pip --strict --format json --output /Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/pip-audit-runtime.json
```

The complete runtime resolution contains 105 exact package pins and 2,083 SHA-256 hashes.
The strict audit checks all 105 packages, skips none, and reports zero known vulnerabilities.
The Git-only development tool package is outside this runtime audit.
The runtime and development manifests remain unchanged.

### Links and writing

The feature link command is:

```bash
rtk proxy .venv/bin/markdown-link-check --root . specs/3309-declared-arango-indexes changelog.d/issue-3309-declared-arango-indexes.md documentation/diagrams/core/database-strategy.md
```

The configured STE command uses `--config .ste-linter.toml --min-score 80 --format json` and names all 20 feature files.
The final scores range from 92 through 98.
The link check covers all 11 staged Markdown files and reports zero broken links.
No licensed STE dictionary is authorized for this repair.
The report states `dictionary_unavailable`, `scope=partial`, and `unintended_skip=false`.
This evidence covers the configured heuristics only.
It does not prove licensed dictionary coverage.

## SpecKit analysis

The final review covers 14 functional requirements and seven success criteria.
Every requirement has an implementation task and passing behavioral evidence.

| Requirements | Tasks | Evidence |
| - | - | - |
| FR-001 through FR-004 | T006 through T009 | Exact real-strategy requests, empty writes, and native SDK responses |
| FR-005 and FR-006 | T014 and T015 | Same-scope coordination and independent scope cases |
| FR-007 and FR-008 | T010 and T011 | Failure, partial extension, complete retry, and concurrent retry |
| FR-009 and FR-010 | T010 through T012 | Ordered diagnostic events, checked counts, and explicit single and dual failures |
| FR-011 | T006 and T010 | Invalid declarations fail before database mutations |
| FR-012 and FR-013 | T013 and T018 | Complete document comparisons, preserved imports, batching, and coverage |
| FR-014 | T016 | Real owned-store proof, target guard failure, and complete resource cleanup |

The review finds zero unmapped requirements, zero behavioral ambiguities, and zero critical implementation findings.
The parent directory and existing class limits remain documented pre-existing structural debt.
The workflow uses the existing templates without changing shared `.specify` state.
The tracked task list keeps local commit reporting and remote delivery conditional until their actual receipts exist.

## Remote boundary

The coordinator has not granted remote work.
The repair must stop after its verified local commit.
A push, pull request, protected merge, and exact-main local tests remain blocked until the explicit grant.

## Local refresh on 2026-10-03 UTC

The [public grant](https://github.com/jmorrison-juniper/MistHelper/issues/3309#issuecomment-5965138986) authorizes local work only.
The accepted base is `f48f653ae6145b0ea3aa82a76ffa4c6cf86897c0`.
Only issue #3311 and pull request #3746 hold publication permission.
The single open pull request contains nine paths.
None overlaps the corrected twenty-file reservation.
The authenticated account and active issue claim remain `jmorrison-juniper`.

### Exact source preservation and rebase

The worktree started clean at `7da4424c8ad36941937d6462ac766cfbe730b9ad`.
The raw commit contains exactly one parent, `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The exact source range contains one commit and the corrected twenty paths.
The source, source parent, and accepted target objects are available.

Git reports a shallow repository.
The target has no traversable parent, and the initial merge-base command returned status 1.
The session reported those facts before the rebase.
It restored no shared history and reconstructed no patch.

The local tag `preservation/3309-local-refresh-20261002-source` preserves the original source.
The explicit rebase used this command:

```bash
rtk proxy git -c rebase.updateRefs=false -c rebase.autoStash=false rebase --no-fork-point --no-autosquash --no-autostash --onto f48f653ae6145b0ea3aa82a76ffa4c6cf86897c0 ff3cc1bea8ab58026210a968ff1465f61c9fec78
```

The rebase completed without a conflict.
The rebased repair is `bbbaf6ec5b13fcc02f29b032ef621928dee15a12`.
Its raw sole parent is the exact accepted base.
The complete range comparison reports an equal patch.
The source changes no DNS preflight code.
The strategy catalog, configuration, natural and composite keys, documents, imports, and batch semantics remain unchanged.
No dependency, detector, baseline, exclusion, or suppression changes.

### Current offline and guide proof

The repeated offline command passes 445 tests with zero failures, errors, or skips.
Its 71 feature tests repeat failure, retry, concurrency, scope separation, native SDK responses, and record preservation.
The remaining 374 tests cover the adjacent writer, router, schema, retention, and SQLite paths.
The combined statement and branch coverage is 96.48 percent.
All seven new or changed methods have zero missing statements and zero missing branches.
The existing SQLite tests again report three unclosed-connection warnings.

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/arango_indexes tests/contract/test_arango_declared_indexes.py tests/unit/test_arango_writer.py tests/unit/test_router.py tests/unit/db tests/unit/refactors/test_sqlite_database_writer.py -q --tb=short --cov=src.foundation.persistence.db.arango_writer --cov=src.foundation.persistence.db.database_schema_utils --cov-branch --cov-report=term-missing --cov-report=json:/Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/refresh-index-coverage.json --cov-fail-under=90
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_wave1_safe_input_paths.py tests/guardrails/local_test_quality_loop/test_guidance.py -q --no-cov --tb=short
rtk proxy .venv/bin/python -m pytest tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides::test_required_local_procedures -q -s --no-cov --tb=short
```

The input and guidance suite passes 452 tests with zero failures, errors, or skips.
The direct current-guide test also passes.
It reports six attempted inputs, six completed reads, six validations, three guide reads, and three guide checks.
It measures two explicit paths, two automatic paths, and four effective paths.
These measurements describe actual current inputs, not historical counts.

### Current owned integration proof

The original Podman capability remains available.
The repeated integration uses the unchanged session-only compose overlay and the original issue-specific profile.
The service starts alone with `--no-deps`.
Its container, volume, network, and project use `misthelper-tmp-issue3309-indexes-5a6310ca`.
The only published address is `127.0.0.1:9650`.
The actual server reports ArangoDB `3.12.4-3`, and the current Python SDK is `8.3.5`.

```bash
rtk proxy env MISTHELPER_ISSUE3309_ARANGO_URL=http://127.0.0.1:9650 .venv/bin/python -m pytest tests/integration/test_arango_declared_indexes_live.py -q -s --no-cov --tb=short
```

Both current live tests pass with zero failures, errors, or skips.
The real writer stores 1,001 prepared documents before index creation and 1,001 after index creation.
The complete document comparison remains equal, excluding only server `_id` and `_rev`.
The collection contains six total indexes, including exactly five declared non-unique persistent indexes.
The normal optimizer changes from zero index nodes to one index node on `status`.
The query returns exactly `["action-0"]`.
The equal `status` request retains its identifier and returns `isNewlyCreated=False`.
The replacement test retains one document and updates its status.

The two fixtures remove two owned databases.
The store contains only `_system` before resource cleanup.
The session removes one exact owned container, one exact owned volume, and one exact owned network.
Each exact-name cleanup scan returns zero resources.
No production store, container, port, service, network, or volume is accessed.

### Current configured gates

The earlier command table defines the unchanged configured scopes.
The repeated measurements are:

| Gate | Current result |
| - | - |
| Full-root Ruff | Passed with zero findings |
| Full-root Black | Passed across 2,044 files |
| Exact CI mypy scope | Passed across 667 source files |
| Syntax | Passed for the entrypoint and all nine feature Python files |
| Bandit and separator guard | Passed across 790 files with zero findings and zero read errors |
| Pylint | Passed with a score of 9.83 |
| Configured Radon and complexity guard | Passed every block at the maximum of 10 |
| Configured Vulture | Passed with zero findings at confidence 70 |
| Configured pydocstyle | Passed |
| Configured Interrogate | Passed with 99.6 percent coverage |
| Citation references | Passed 251 citations with zero unresolved references |
| Diagram references | Passed 153 references across 15 diagrams |
| Feature Markdown links | Passed 11 files with zero broken links |

Both unchanged test-quality commands pass:

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --log-level WARNING
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from f48f653ae6145b0ea3aa82a76ffa4c6cf86897c0 --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt --log-level WARNING
```

The full command checks 1,021 files, analyzes 973 modules, and compares 725 existing findings.
It reports zero new findings, zero parse errors, and 48 declared skips.
The committed command analyzes all five feature test modules with zero findings and zero parse errors.
That scope includes the native SDK contract module and the live integration module.
Its two skip records describe omitted full-suite roots, not an excluded native module or skipped test.

The normal runtime audit again aborts during temporary macOS interpreter setup.
It performs no audit and receives no passing status.
The approved complete hashed resolution and strict audit both succeed:

```bash
rtk proxy env UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 UV_LINK_MODE=copy uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file /Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/refresh-runtime-audit-requirements.txt --quiet
rtk proxy .venv/bin/pip-audit -r /Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/refresh-runtime-audit-requirements.txt --no-deps --disable-pip --strict --format json --output /Users/jmorrison/.copilot/session-state/87bdb7f6-0891-4536-a492-c22ffb198106/files/refresh-pip-audit-runtime.json
```

The current resolution contains 105 exact pins and 2,177 SHA-256 hashes.
The strict audit checks 105 packages, skips zero packages, and reports zero known vulnerabilities.
The Git-only development tools remain outside this runtime audit.
The manifests and configured policies remain unchanged.

The configured STE heuristics pass all twenty feature files with scores from 92 through 98.
The report retains `dictionary_unavailable`, `scope=partial`, and `unintended_skip=false`.
No licensed dictionary coverage is claimed.

### Local-only delivery state

The local evidence update changes only this validation record and the existing feature task record.
The corrected twenty-file boundary remains unchanged.
The production patch remains equivalent to the preserved source.
Publication still requires the actual accepted predecessor after #3311 and a separate full-SHA publication grant.
No push, pull request, Actions run, merge, dispatch, production write, DNS migration, or next-owner release occurs.

## Publication proof on 2026-10-03 UTC

The [sole publication grant](https://github.com/jmorrison-juniper/MistHelper/issues/3309#issuecomment-5965481973) authorizes position 25.
The only approved predecessor is `10fbd06110101e7f75705dbd585796dfeff8a3ab`.
The coordinator accepted issue #3311 through pull request #3746.
The current main read matches that complete predecessor and its sole parent, `f48f653ae6145b0ea3aa82a76ffa4c6cf86897c0`.
Its tree is `883fb049a45a7843f2bd572a496ef6fbd31a01a4`.
No open pull request overlaps a reserved path.

### Complete saved range

The session preserves `1c69ee953252aa6e88cf21af4ebdd88a73504532` under `preservation/3309-publication-20261003-refresh`.
It preserves `bbbaf6ec5b13fcc02f29b032ef621928dee15a12` under `preservation/3309-publication-20261003-repair`.
The original `7da4424c8ad36941937d6462ac766cfbe730b9ad` remains under its existing preservation tag.
The raw parent chain proves exactly two saved commits above the earlier accepted base.
All required source, parent, and target objects are available.

The bounded rebase completes without conflict:

```bash
rtk proxy git -c rebase.updateRefs=false -c rebase.autoStash=false rebase --no-fork-point --no-autosquash --no-autostash --onto 10fbd06110101e7f75705dbd585796dfeff8a3ab f48f653ae6145b0ea3aa82a76ffa4c6cf86897c0
```

The rebased repair is `da82f742862edb245e6e8109733f7fe56a9955a6`.
The preserved evidence commit becomes `f9dfff11e88837e76083fc5b74d226071ab93902`.
The raw chain ends at the exact approved predecessor.
The complete range comparison reports both patches equal.
The twenty-path boundary remains identical to the saved source.
The rebase changes no other owner ref and restores no shared history.

### Repeated current measurements

The offline command recorded above passes all 445 tests again.
The input and guidance command passes all 452 tests again.
Both results have zero failures, errors, and skips.
All seven changed methods retain 100 percent statement and branch coverage.
The two changed database modules retain 96.48 percent combined coverage.
The three pre-existing SQLite connection warnings remain explicit.

The direct current-guide preflight reads and validates all six required inputs.
It reads and checks all three active guides.
It measures two explicit paths, two automatic paths, and four effective paths.
The preflight completes before the analyzer commands.

The original owned integration capability remains available.
Both real ArangoDB tests pass again with zero failures, errors, and skips.
The repeated proof preserves 1,001 complete prepared documents.
It measures five declared non-unique persistent indexes and six total indexes.
The optimizer changes from zero index nodes to one index node on `status`.
The query returns exactly `["action-0"]`.
The equal-index request retains its identifier and reports `isNewlyCreated=False`.

The original issue-specific compose service starts alone with `--no-deps`.
It uses the unchanged session-only overlay and exact owned resource names.
It publishes only `127.0.0.1:9650`.
The fixtures remove two test databases.
The store contains only `_system` before resource cleanup.
The session removes the exact one container, one volume, and one network.
All three exact-name scans return zero resources.
The run accesses no production resource.

### Repeated current gates

| Gate | Publication-base result |
| - | - |
| Full-root Ruff | Passed with zero findings |
| Full-root Black | Passed across 2,047 files |
| Exact CI mypy scope | Passed across 667 source files |
| Syntax | Passed for the entrypoint and all nine feature Python files |
| Bandit and separator guard | Passed across 790 files with zero findings and read errors |
| Pylint | Passed with a score of 9.83 |
| Configured complexity, dead-code, and docstring gates | Passed with complexity at most 10 and docstring coverage 99.6 percent |
| Feature links | Passed all 11 Markdown files with zero broken links |
| Citations and diagrams | Passed 251 citations and 153 references across 15 diagrams |
| CodeQL verdict register | Matched all 88 dismissed alerts without a register change |

The complete configured test-quality gate checks 1,023 files and analyzes 975 modules.
It compares 725 existing findings and reports zero new findings and zero parse errors.
The committed scope analyzes all five real feature test modules with zero findings and zero parse errors.
Both the native SDK contract and live integration module participate.

The forced native command also passes:

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --roots tests/contract/test_arango_declared_indexes.py --include-mist-api --log-level WARNING
```

That command analyzes exactly one native SDK module and reports zero findings and parse errors.
Its two skipped discovery roots omit the full-suite roots from this explicit scope.
They do not exclude the native module.
No analyzer rule, baseline, pin, suppression, or exclusion changes.

The normal macOS runtime audit again aborts before scanning.
The approved complete hashed alternative succeeds with 105 exact pins and 2,177 SHA-256 hashes.
The strict audit checks all 105 packages, skips none, and reports zero known vulnerabilities.
The Git-only development tools remain outside this runtime audit.

The configured writing heuristics pass all twenty files with scores from 92 through 98.
The applicable writing-guide test also passes.
The licensed dictionary remains unavailable, and the report states partial coverage without an unintended skip.

### Protected publication boundary

The source retains the semantic manager in `database_schema_utils.py` and the unique integration basename.
The DNS, key, preparation, and batching methods remain unchanged against the approved predecessor.
The catalog, documents, configuration, dependencies, and policies remain unchanged.

Publication requires one push and one full current-template pull request.
The ordinary protected squash must match the complete checked head and the approved predecessor.
Every fresh applicable job and all fifteen strict contexts must pass first.
The independent CodeQL status must originate from app 57789.
The exact actual-main proof and automatic outcomes remain mandatory after the merge.
The coordinator alone can accept that receipt and release the next owner.
This grant permits no DNS migration, production write, restart, or deployment.
