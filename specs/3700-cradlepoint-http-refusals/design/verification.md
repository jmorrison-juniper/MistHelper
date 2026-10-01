# Verification: Cradlepoint HTTP refusals

## Before the repair

The worktree began at `64c4e8bda1b56c89609d86c9eee1d3b078bbe1a2`.
Fetched main later resolved to `069f7bd8e2ae641a5de70d6aa10f5ddd88bad5c7`.
Both owned existing files matched fetched main byte for byte.
Neither SHA grants publication.

The unchanged exporter suite passed all 15 tests:

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/unit/export/test_org_cradlepoint_connection_exporter.py
```

The initial command could not start because `.venv/bin/python` was absent.
The unchanged bootstrap then failed at `ensurepip` with `SIGABRT`.
The owned UV-seeded recovery and unchanged setup succeeded.
The mandatory feature hook returned exit `1` because the app branch already exists.

## Native red proof

The unchanged source failed all 31 selected native cases.
The endpoint ran once for each case. Every live-request count was zero.
The real row and persistence methods each ran 31 times.
Five nonempty refusal dictionaries reached the shared writer and a successful notice.
The other 26 cases reached an ordinary empty-result notice.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/unit/export/cradlepoint_http_refusals/test_native_responses.py -k "native_http_4xx_5xx_refusals or native_none_transport" --tb=line
```

Result: `31 failed, 40 deselected`, as required for the red proof.
The session artifact `native-red.log` preserves the complete output.
The counted artifact `native-red-counts.json` verifies all callback and request counts.

Before the production edit, all 26 native success controls passed:

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/unit/export/cradlepoint_http_refusals/test_native_responses.py -k "native_http_200_preserves_integration_error_and_metadata or native_success_empty_and_non_dict_body" --show-capture=no --tb=line
```

Result: `26 passed, 45 deselected`.
The controls include exact integration-error rows, newline escaping, endpoint metadata, and successful empty bodies.

## Repaired behavior and coverage

The final focused run passed 199 tests.
It includes 71 native cases, all 15 existing exporter tests, and 113 adjacent tests.
The native cases include 45 guarded failures and 26 success controls.
Each native case made one endpoint call and zero live requests.
Every guarded failure made zero row, persistence, and writer callbacks.
Both complete integration-status controls wrote the exact expected row and metadata.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/unit/export/cradlepoint_http_refusals/test_native_responses.py tests/unit/export/test_org_cradlepoint_connection_exporter.py tests/unit/export/test_org_sec_intel_profile_exporter.py tests/unit/export/test_export_notice_separator.py --cov=src.export.org_cradlepoint_connection_exporter --cov-branch --cov-report=term-missing --cov-fail-under=80 --show-capture=no --tb=short
```

The measured run also wrote coverage JSON and its data file to session artifacts.
Result: `199 passed`. There were no skipped tests.

| Region | Statements | Branches |
| --- | --- | --- |
| Affected module | 63 of 63 | 12 of 12 |
| Changed `_fetch` | 10 of 10 | 2 of 2 |
| New `_require_http_success` | 7 of 7 | 4 of 4 |

Every region reached 100 percent coverage.
The new test class and measurement class each contain five semantic methods.
Every new executable method body remains below 25 lines.

### Guard failure proof with the final tests

An isolated process removed exactly one guard call from the parsed source in memory.
It did not change the file on disk.
All 31 native refusal and absent-transport tests then failed with pytest exit `1`.
The process recorded 31 endpoint, row, and persistence callbacks.
Five refused dictionaries reached the writer. All live-request counts remained zero.
The session artifact `guard-mutation-red.log` preserves this proof.

## Configured local gates

All commands used the owned Python `3.13.13` environment.
The applicable syntax, Ruff, Black, type, security, and test-quality checks passed.

| Check | Exact command or scope | Result |
| --- | --- | --- |
| Syntax | `rtk proxy .venv/bin/python -m py_compile MistHelper.py src/export/org_cradlepoint_connection_exporter.py tests/unit/export/test_org_cradlepoint_connection_exporter.py tests/unit/export/cradlepoint_http_refusals/test_native_responses.py` | Passed. |
| Ruff | `rtk proxy .venv/bin/python -m ruff check MistHelper.py src/export/org_cradlepoint_connection_exporter.py tests/unit/export/test_org_cradlepoint_connection_exporter.py tests/unit/export/cradlepoint_http_refusals/test_native_responses.py` | Passed. |
| Black | `rtk proxy .venv/bin/python -m black --check MistHelper.py src/export/org_cradlepoint_connection_exporter.py tests/unit/export/test_org_cradlepoint_connection_exporter.py tests/unit/export/cradlepoint_http_refusals/test_native_responses.py` | Passed. |
| Types | `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Passed across 663 source files. The scope came from current CI. |
| Bandit | `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r src/export/org_cradlepoint_connection_exporter.py -q -f json -o <session artifact>` | Passed. One file, zero findings, zero errors. |
| Pylint | `rtk proxy .venv/bin/python -m pylint src/export/org_cradlepoint_connection_exporter.py --rcfile=pyproject.toml --score=y` | Passed at 9.83 of 10. The existing `R0903` remains. |
| Complexity | `rtk proxy .venv/bin/radon cc src/export/org_cradlepoint_connection_exporter.py -j` through `complexity-gate --max 10` | Passed. Six blocks. Maximum complexity: 5. |
| Docstring style | `rtk proxy .venv/bin/python -m pydocstyle src/export/org_cradlepoint_connection_exporter.py --config=pyproject.toml` | Passed. |
| Docstring coverage | `rtk proxy .venv/bin/interrogate src/export/org_cradlepoint_connection_exporter.py --fail-under 90 -v` | Passed. All seven documented objects have docstrings. |
| Dead code | `rtk proxy .venv/bin/python -m vulture src/export/org_cradlepoint_connection_exporter.py --min-confidence 70 --config pyproject.toml` | Passed. |
| Symbols | `rtk proxy .venv/bin/symbol-diff --base 64c4e8bda1b56c89609d86c9eee1d3b078bbe1a2 src/export/org_cradlepoint_connection_exporter.py` | Passed. Zero lost or added module-level names. |

The generated Interrogate badge was an ignored temporary file.
The session removed that exact file after the check.

### Test-quality ratchet

The required preflight passed with six input reads and three guide checks:

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

The unchanged configured ratchet inspected both owned test modules:

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --roots tests/unit/export/test_org_cradlepoint_connection_exporter.py tests/unit/export/cradlepoint_http_refusals/test_native_responses.py
```

The measured command also wrote its report and summary to session artifacts.
Result: two files checked, five accepted existing findings, zero new findings, and zero parse errors.
Neither owned module was excluded.
The two reported omitted roots belong to the intentionally bounded file scope.

The initial measurement could not trace a source call through the measurement class.
The tests now call the real exporter directly inside the profiling context.
No detector, setting, threshold, baseline, exclusion, or suppression changed.
The four edits in the existing test module preserve every old finding line number.

After the local commit, repeat the required preflight and run the committed comparison:

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

The local handoff records that result and the full commit SHA outside the tracked source.
This document does not claim a post-commit result before the commit exists.

### Dependency audit

The normal strict command failed before it audited packages:

```bash
rtk proxy .venv/bin/pip-audit -r requirements.txt --strict --progress-spinner off --format json --output <session artifact>
```

The temporary copied interpreter stopped at `ensurepip` with `SIGABRT`.
That failure is not an audit pass.

The authorized alternative compiled the complete runtime requirements with UV:

```bash
rtk proxy uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --no-config --index-url https://pypi.org/simple --quiet --output-file <session artifact>/runtime-hashed.txt
rtk proxy .venv/bin/pip-audit --strict --no-deps --disable-pip --require-hashes --progress-spinner off --requirement <session artifact>/runtime-hashed.txt --format json --output <session artifact>/runtime-audit.json
```

Result: 105 pinned runtime packages, 2,083 SHA-256 hashes, and zero known vulnerabilities.
The audit skipped zero packages and zero advisories.
The closure includes `mistapi` `0.64.0`.

The runtime audit does not cover Git-only development tools.
The installed `misthelper-devtools` version is `0.6.0`, from commit
`b140350ebc40e61b57a3a65731c0df520f143661`.
No PyPI advisory result for that Git source is claimed.

### Writing capability

The configured STE heuristic inspected all 13 owned files with logging and printed strings enabled.
Each score met the threshold of 80.
The licensed dictionary is absent: `dictionary_unavailable`.
This is partial heuristic validation, not complete dictionary validation.

## Source and delivery boundaries

The 13 reserved files are the only intended tracked changes.
The `_build_row`, `_persist`, and `status` methods match the original source byte for byte.
The endpoint call, writer metadata, filename, dependencies, schemas, and primary keys remain unchanged.
The template exporter test for #2711 and `src/api/response_integrity.py` remain read-only.
The shared SpecKit state, governance files, and `CHANGELOG.md` remain unchanged.
No publication, live Mist request, production store action, container, or workflow is authorized.
The offline pull request draft must preserve all 23 current template checklist items.
