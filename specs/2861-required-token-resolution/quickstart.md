# Required token resolution: Local verification

Part of [#2861](https://github.com/jmorrison-juniper/MistHelper/issues/2861). The 31-candidate campaign remains open.

## Safety boundary

Use only controlled provider values and a mocked SDK constructor.
Do not supply a real token.
Do not contact Redis, Vault, Mist, SMTP, or a production container.
Do not publish before the parent grants the full verified-main SHA for position 36.

## Isolated setup

The backend owns its runtime and development dependencies in `mist-ops-platform/pyproject.toml`.
Its `requirements-dev.txt` supplies additional test tools.
The documented backend setup is:

```bash
cd mist-ops-platform
rtk proxy .venv/bin/python -m pip install -e '.[dev]' -r requirements-dev.txt
```

Use a separate root environment for root gates.
Do not install the two editable `src` packages into one environment.

## Required verification

Run these commands from `mist-ops-platform`:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/mist/token_resolution -q
rtk proxy .venv/bin/python -m pytest --collect-only -q
rtk proxy .venv/bin/python -m pytest --cov=src --cov-fail-under=56 --timeout=120
rtk proxy .venv/bin/python -m ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise
```

The collection count must remain at least 390.
The complete coverage denominator remains `src`.
Required token tests must not skip.
Record existing optional-SDK skips by name and reason.

## Evidence record

The original source base is `644037dcc1eee0e43fac0d40b1186ff1cb6e322e`.
The parent proof used an extracted method. This slice requires the imported factory and real session boundary.

The three original cases failed through the imported factory before the source edit.
The unchanged source SHA256 was `070360e8de7aab76f9f480349192b1b03272839998521f9545f2c1aae795f3b5`.
The final focused suite passes 134 cases with no skip.
The changed method covers all 15 executable statements and all six branches.
The method has complexity 7, below the ceiling of 10.

The complete backend collects 641 cases.
It passes 609 cases and skips 32 existing optional-method checks.
Coverage is 63.02 percent against the unchanged floor of 56 percent.
The collection floor remains 390.
Eight skips concern absent read methods. Six concern absent write methods. Eighteen concern absent list methods.
Only `tests/unit/mist/test_registry_validation.py` holds those optional skips.
No required token case skips.

The final offline runner records zero transport attempts.
It supplies an in-memory rate client to four existing organization probes.
Those probes previously attempted the default async Redis connection.
The runner blocked every attempt before a connection.
No production setting, handler, or existing test file changes.

The owned backend environment was absent before setup.
The owned root environment was absent before setup.
Both initial `.venv/bin/python -m pytest --version` checks failed with a missing-executable error.
The standard backend `python3.13 -m venv` command completed without an EnvBuilder failure.

The direct `pip-audit -r requirements.txt` command later reproduced the EnvBuilder failure from issue #3701.
Its temporary `ensurepip` process stopped with `SIGABRT`.
The requirements-only recovery used an owned UV-seeded environment, copied packages, and system certificates.
All 106 packages in that recovered scope pass the audit.
The root installed audit assesses 159 packages. The backend installed audit assesses 158 packages.
Both final audits report zero findings.
PyPI cannot assess the Git-only `misthelper-devtools` package.
The backend installed audit also cannot assess the editable local `mist-ops-platform` project.
The audit JSON files preserve every package name, version, and skip reason.
Seeded pip 26.0.1 caused eight initial advisory entries.
The two owned environments now use pip 26.2.1. No dependency manifest changes.

The PowerShell SpecKit setup failed because `pwsh` is unavailable.
The companion hook command failed because its executable is unavailable.
The feature uses the current templates directly and leaves shared feature state unchanged.

### Exact local gate commands and results

Backend commands run from `mist-ops-platform`.
Root commands run from the repository root.
The backend interpreter is `.venv/bin/python` in its own directory.
The root interpreter is the separate root `.venv/bin/python`.

| Scope | Command | Result |
| - | - | - |
| Backend setup | `rtk proxy .venv/bin/python -m pip install --quiet -e '.[dev]' -r requirements-dev.txt` | Passed. |
| Missing backend quality tools | `rtk proxy uv pip install --python .venv/bin/python --quiet -r ../requirements-dev.txt` | Passed after missing Black, Bandit, and audit-tool failures. |
| Original proof | `rtk proxy .venv/bin/python -m pytest tests/unit/mist/token_resolution/test_required_resolution.py::TestOriginalFailures -q --tb=short` | Three expected failures against unchanged source. |
| Focused matrix | `rtk proxy .venv/bin/python -m pytest tests/unit/mist/token_resolution -q --tb=short` | 134 passed. |
| Backend collection | `pytest.main(["--collect-only", "-q"])` through the offline runner | 641 collected. Zero transport attempts. |
| Complete backend | `pytest.main(["--cov=src", "--cov-fail-under=56", "--timeout=120", "-q", "-rs"])` through the offline runner | 609 passed. 32 named optional skips. Coverage 63.02 percent. Zero transport attempts. |
| Owned syntax | `rtk proxy mist-ops-platform/.venv/bin/python -m py_compile mist-ops-platform/src/shared/mist/session.py mist-ops-platform/tests/unit/mist/token_resolution/conftest.py mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py mist-ops-platform/tests/unit/mist/token_resolution/test_provider_contracts.py mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py` | Passed for all five files. |
| Owned backend Ruff | `rtk proxy .venv/bin/python -m ruff check src/shared/mist/session.py tests/unit/mist/token_resolution --output-format=concise` | Passed under the full backend configuration. |
| Complete backend correctness | `rtk proxy .venv/bin/python -m ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise` | Passed with unchanged configured exclusions. |
| Backend Ruff advisory | `rtk proxy .venv/bin/python -m ruff check . --statistics` | 394 existing findings remain. No owned-file finding remains. |
| Targeted strict types | `rtk proxy .venv/bin/python -m mypy src/shared/mist/session.py tests/unit/mist/token_resolution --config-file pyproject.toml` | Four existing provider findings remain. No new test or resolver finding. |
| Complete strict backend types | `rtk proxy .venv/bin/python -m mypy src --config-file pyproject.toml` | 176 existing findings across 31 files. |
| Original type comparison | The same strict command with `--shadow-file src/shared/mist/session.py <session-artifact>/original_session.py` | The original and current scopes report the same 176 findings. |
| Entry-point syntax | `rtk proxy .venv/bin/python -m py_compile MistHelper.py` | Passed. |
| Complete root Ruff | `rtk proxy .venv/bin/python -m ruff check .` | Passed. |
| Complete root Black | `rtk proxy .venv/bin/python -m black --check --diff .` | Passed for 2,013 files. |
| Complete root strict types | `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Passed for 663 source files. |
| Complete root Bandit | `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r . -q` | Passed. Existing annotation warnings remain. |
| Bandit path contract | `rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/utils/zen_city_metadata.py --include-sample '.\src\utils\zen_city_metadata.py'` | Passed. The optional SARIF formatter reports missing `sarif_om`. |
| Complete root Pylint | `rtk proxy .venv/bin/python -m pylint src/ --fail-under=9.5` | Passed with score 9.83. |
| Complete root complexity | `rtk proxy .venv/bin/python -m radon cc src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -j \| rtk proxy .venv/bin/complexity-gate --max 10` | Passed. |
| Factory complexity | `rtk proxy .venv/bin/python -m radon cc mist-ops-platform/src/shared/mist/session.py -j \| rtk proxy .venv/bin/complexity-gate --max 10` | Passed. |
| Complete root dead code | `rtk proxy .venv/bin/python -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Passed. |
| Complete root docstring style | `rtk proxy .venv/bin/python -m pydocstyle src/ wsgi.py web_portal` | Passed. |
| Complete root docstring coverage | `rtk proxy .venv/bin/interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | Passed. |
| Diagram references | `rtk proxy .venv/bin/diagram-refs --source-files MistHelper.py src/ --allowlist-file .github/diagram-refs-allowlist.txt` | Passed for 153 references in 15 files. |
| Citation references | `rtk proxy .venv/bin/check-citations src tests` | Passed for 251 citations. |
| Related root contracts | `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/guardrails/local_test_quality_loop tests/integration/test_mistapi_sdk_compatibility.py --timeout=120` | 536 passed. |
| Required-input preflight | `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | Six inputs read and validated. Three guides checked. |
| Complete test-quality ratchet | `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` | 1,000 files checked. 725 accepted findings. Zero new findings. |
| Explicit new-test ratchet | The same command with `--roots mist-ops-platform/tests/unit/mist/token_resolution` | All three new test modules enter analysis. Zero findings. |

Every audit command uses no vulnerability ignore:

```bash
rtk proxy .venv/bin/python -m pip_audit --local --format=json
cd mist-ops-platform
rtk proxy .venv/bin/python -m pip_audit --local --format=json
```

The recovered requirements-only audit uses `pip_audit --path` for the owned audit environment.
The full package lists and output files stay in the session artifacts.

The source comparison proves all three exception handlers remain unchanged.
The factory retains ten methods. The module retains five semantic declarations.
All 33 owned functions remain within 25 lines.
No baseline, configuration, suppression, threshold, or exclusion changes.

### Certification and publication limits

The strict backend type check and its advisory Ruff check do not provide a clean full-backend certification.
The writing check passes the configured score gate, but dictionary coverage remains partial.
The licensed dictionary artifact is unavailable.

The root SDK guard checks 547 signatures and resolves 913 function names.
It records ten unresolved call sites and 366 unverifiable signatures.
It reports zero known signature failures.
The native backend SDK checks run against `mistapi` 0.64.0.
No test creates a real Mist SDK session or contacts a live provider.

The offline PR draft preserves every heading, comment, and checklist item from the 23-item template.
It leaves whole-campaign and unperformed checks incomplete.
The post-commit changed-scope ratchet must use freshly fetched `origin/main`.
That comparison does not constitute the parent's verified-main grant.

Remote CI, CodeQL, verified-main, publication, and deployment remain unperformed.
The root menu references, browser tests, frontend tests, and container builds have no changed surface in this slice.
Do not start a remote workflow to certify this local candidate.
