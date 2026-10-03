# Specification Analysis: Bounded numeric inputs

## Initial Consistency Review

All eleven functional requirements map to the three user stories or cross-cutting proof tasks.
The specification, plan, and tasks name the same four source files and two test files.
The design preserves the existing sign, whitespace, leading zero, fallback, and refusal rules.
It adds no stored record, firmware callback, dependency, suppression, or shared SpecKit state.

| Requirement | Tasks |
| - | - |
| FR-001, FR-002, FR-003 | T003 through T008, T013 |
| FR-004 | T007, T008 |
| FR-005, FR-006 | T009, T010 |
| FR-007, FR-008, FR-009 | T006 through T012 |
| FR-010 | T003 through T005, T008, T010, T012, T013 |
| FR-011 | T001, T014, T016 |

The existing large test directories remain a recorded structural constraint.
The explicit issue reservation prohibits unrelated test tree restructuring.
The legacy branch hook cannot operate within the app-managed branch rules.
This workflow therefore uses file-only specification artifacts.

## Local Evidence

The original regression run executed 134 tests.
It reported 39 failures, 95 passes, and zero skips.
The persisted report is `3395-red.xml` in the session artifact directory.

The real picker answered status 500 for superscript digits, excessive digits,
excessive leading zeros, and repeated plus signs.
Arabic and fullwidth digits selected the wrong page.
The real JSON and form capture posts answered status 500 for superscript and excessive digits.
Arabic and fullwidth tier digits incorrectly started the capture boundary with status 202.
The real client setting reader raised `ValueError` or accepted the wrong page limit.
The unmodified existing client suite passed all 39 tests.

The final focused run passed all 174 tests with zero skips.
The related regression run passed all 372 tests with zero skips.
The related run includes the existing client, picker, capture start, lock grant, and SDK compatibility tests.
Every test used local requests or injected offline sources.
No test used a live Mist account, production store, firmware action, or container.

The exhaustive corpus checked 4008 page limit decisions.
It checked 2394 reader decisions for all 798 non-ASCII digits in this interpreter.
It checked 351 reader decisions for all 117 environment-compatible ASCII non-digits.
It checked two additional NUL request decisions.
The host environment cannot store NUL.
The total exhaustive corpus therefore contains 6755 reader decisions.

Three Hypothesis properties each recorded 100 passing examples.
They recorded zero failing examples and zero invalid examples.
The properties checked 700 additional reader decisions.
Five unusable text cases checked all three readers with zero integer conversions.
Three positive boundary controls each recorded exactly one integer conversion.

The real JSON and form refusal corpus checked 26 capture posts.
Every refusal returned the exact status 400 `bad_tier` body.
Every refusal recorded zero capture launches, zero workers, and zero firmware launches.

## Coverage Proof

The focused coverage collector records four source modules.
The local proof requires complete coverage of the changed methods, not unrelated methods in those modules.
The JSON collection threshold is not a project coverage gate.
The proof checked eight functions and the complete new module.
It found no missing statement or branch.

| Scope | Statements | Branches |
| - | - | - |
| Complete `api/numeric_input.py` module | 36/36 | 8/8 |
| Shared `read` method | 20/20 | 8/8 |
| Shared backend limit method | 4/4 | 0/0 |
| Shared refusal diagnostic method | 2/2 | 0/0 |
| Picker `read_whole_number` | 7/7 | 0/0 |
| Capture `tier_number` | 12/12 | 6/6 |
| Client `page_limit` | 12/12 | 4/4 |
| Existing `read_tier` decision | 3/3 | 0/0 |
| Real `start_capture` refusal boundary | 12/12 | 6/6 |

The six changed methods covered 57 statements and 18 branches.
The eight verified functions covered 72 statements and 24 branches.
The complete new module and every measured function reached 100 percent coverage.

## Exact Local Commands and Results

The command paths below refer to this worktree's `.venv`.
`ARTIFACTS` names the session artifact directory for execution reports.

The original failure command was:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/upgrade_portal/test_bounded_numeric_inputs.py tests/contract/upgrade_portal/test_bounded_numeric_routes.py --no-cov -q --tb=short --show-capture=no --junitxml="$ARTIFACTS/3395-red.xml"
```

It failed with 39 failures, 95 passes, and zero skips.

The final focused coverage command was:

```bash
rtk proxy env COVERAGE_FILE="$ARTIFACTS/3395.coverage" .venv/bin/python -m coverage run --branch --source=src.interfaces.portals.upgrade_portal.api.numeric_input,src.interfaces.portals.upgrade_portal.app.routes.select,src.interfaces.portals.upgrade_portal.app.routes.capture,src.interfaces.portals.upgrade_portal.capture.clients -m pytest tests/unit/upgrade_portal/test_bounded_numeric_inputs.py tests/contract/upgrade_portal/test_bounded_numeric_routes.py tests/unit/upgrade_portal/test_capture_clients.py tests/unit/upgrade_portal/test_org_picker.py tests/contract/upgrade_portal/test_select.py tests/contract/upgrade_portal/test_capture_start.py tests/contract/upgrade_portal/test_capture_start_returns_lock_grant.py tests/integration/test_mistapi_sdk_compatibility.py --no-cov -q --tb=short --hypothesis-show-statistics -o junit_logging=system-out --junitxml="$ARTIFACTS/3395-covered.xml"
rtk proxy env COVERAGE_FILE="$ARTIFACTS/3395.coverage" .venv/bin/python -m coverage json --fail-under=0 -o "$ARTIFACTS/3395-coverage.json"
rtk proxy .venv/bin/python "$ARTIFACTS/3395-coverage-proof.py"
```

All three commands passed.
The test command passed 372 tests.
The coverage proof checked eight functions and one complete new module.

| Command | Result |
| - | - |
| `rtk proxy .venv/bin/python -m py_compile MistHelper.py src/interfaces/portals/upgrade_portal/api/numeric_input.py src/interfaces/portals/upgrade_portal/app/routes/select.py src/interfaces/portals/upgrade_portal/app/routes/capture.py src/interfaces/portals/upgrade_portal/capture/clients.py tests/unit/upgrade_portal/test_bounded_numeric_inputs.py tests/contract/upgrade_portal/test_bounded_numeric_routes.py` | Passed. |
| `rtk proxy .venv/bin/python -m ruff check .` | Passed with zero findings. |
| `rtk proxy .venv/bin/python -m black --check .` | Passed for 2003 files. |
| `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Passed for 664 source files. |
| `rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/foundation/support/utils/zen_city_metadata.py --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'` | Passed both include samples and separator forms. |
| `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r . -q` | Passed with zero findings. |
| `rtk proxy .venv/bin/python -m pylint src/ --fail-under=9.5` | Passed with score 9.83/10. |
| `rtk proxy .venv/bin/python -m radon cc src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -j` | Passed. The JSON report supplies the complexity gate. |
| `rtk proxy .venv/bin/complexity-gate --max 10` | Passed with the full Radon report as input. |
| `rtk proxy .venv/bin/python -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Passed with zero findings. |
| `rtk proxy .venv/bin/python -m pydocstyle src/ wsgi.py web_portal` | Passed. |
| `rtk proxy .venv/bin/python -m interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 --generate-badge "$ARTIFACTS" --quiet` | Passed. |
| `rtk proxy .venv/bin/check-citations src tests` | Passed with 251 citations and zero unresolved citations. |
| `rtk proxy .venv/bin/diagram-refs --source-files MistHelper.py src/ --allowlist-file .github/diagram-refs-allowlist.txt` | Passed with 153 references across 15 diagram files. |
| `rtk proxy .venv/bin/markdown-link-check specs/3395-bounded-numeric-inputs changelog.d/issue-3395-bounded-numeric-inputs.md` | Passed for 10 documents with zero broken links. |

The installed ratchet compares committed changes, not staged changes.
Its initial changed-scope command checked zero files before the commit.
That result does not prove test quality.
The unchanged full-scan fallback checked 994 files and 725 findings.
It reported zero new findings and zero parse errors.
Its 48 skipped files use the existing Mist API exclusion.
The required numeric tests skipped no case.

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report "$ARTIFACTS/3395-test-quality-full.json" --summary "$ARTIFACTS/3395-test-quality-full.md"
```

The full-scan fallback passed.
The post-commit changed-scope command must check both new test files.

## Dependency and Writing Capabilities

The normal `pip-audit -r requirements.txt` command stopped during its temporary environment creation on macOS.
The copied uv Python executable could not seed pip and exited with `SIGABRT`.
The complete hashed runtime workaround passed:

```bash
rtk proxy env UV_LINK_MODE=copy UV_SYSTEM_CERTS=1 UV_NATIVE_TLS=1 uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file "$ARTIFACTS/3395-runtime-audit.txt" --quiet
rtk proxy .venv/bin/pip-audit --strict --no-deps --disable-pip -r "$ARTIFACTS/3395-runtime-audit.txt" --format=json --output="$ARTIFACTS/3395-audit.json"
```

The audit checked all 105 resolved runtime packages.
It reported zero vulnerable packages and zero skipped packages.
The Git-only development package `misthelper-devtools` remains outside this runtime audit.
No dependency manifest or pin changed.

The configured STE command checked all 16 reserved files with `--config .ste-linter.toml --min-score 80 --format json`.
It passed the configured heuristic threshold.
Its report states `scope=partial` and `dictionary_unavailable`.
No authorized `data/ste_dictionary.json` exists in this worktree.
The result does not prove full word grading.

## Final Scope Analysis

All eleven functional requirements have execution evidence.
The new reader has two immutable fields and three methods.
The source changes remain inside the three requested reader blocks and the new API module.
The option mapper, owner tests, templates, authentication, firmware controls, schema, primary keys,
dependency manifests, quality settings, baselines, and exclusions remain unchanged.
Every local implementation task is complete.
Publication and exact merged-main verification remain outside the authorized local phase.

## Publication Boundary

Initial local base: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
Publication position: 23, after issue #3485.
No push or pull request is authorized.
