# Validation: Tenant identifier validation

## Preconditions

Use the isolated app worktree and its own Python 3.13 environment.
Do not use production credentials or production stores.
No test in this guide requires a live Mist call.

## Environment

The documented bootstrap initially stopped during `ensurepip` with `SIGABRT`.
The allowed uv recovery created the worktree's own pip installation.
The repeated bootstrap installed both current requirement files successfully.
It read 160 package records and found zero corrupt installations.
The interpreter uses Python 3.13.13.

```bash
rtk proxy env UV_LINK_MODE=copy UV_SYSTEM_CERTS=1 UV_NATIVE_TLS=1 \
  uv venv --seed --allow-existing --python python3.13 .venv
rtk proxy env UV_LINK_MODE=copy UV_SYSTEM_CERTS=1 UV_NATIVE_TLS=1 \
  .venv/bin/python -B scripts/bootstrap_worktree.py
```

## Public-Boundary Proof

Run the regression tests before the production change.
The original methods must fail the missing-identifier assertions.
The checked-case output must show the SDK calls that caused the failure.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q \
  tests/unit/api/test_tenant_identifier_validation.py \
  -k '(test_missing_org and blank and organization_tenants) or (test_missing_required_site and none and site_tenants) or (test_invalid_optional_site and blank)' \
  --show-capture=no
```

After the repair, run the same command.
Every refusal must name its field and show zero SDK calls.

**Result**: Before the repair, all four selected tests failed.
Each failure made one SDK call.
After the repair, all four tests passed.
Each case raised the named `ValueError` and made zero SDK calls.
The full deterministic refusal set covers 88 cases.

## Focused Compatibility and Coverage

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q \
  tests/unit/test_api_tenant_fetch.py \
  tests/unit/api/test_tenant_identifier_validation.py \
  tests/unit/api/test_response_integrity.py \
  tests/unit/websocket/test_service_ping_discovery.py \
  tests/unit/test_issue_2971_status_before_count.py::test_organization_tenants_503_returns_empty_and_suppresses_success \
  tests/unit/test_issue_2971_status_before_count.py::test_site_tenants_503_returns_empty_and_suppresses_success \
  --cov=src.api.tenant_fetch --cov-branch \
  --cov-report=term-missing --cov-fail-under=90
```

The coverage result must meet 90 percent.
The existing test files remain unchanged.

**Result**: The focused selection passed 309 tests.
That count includes all 54 original tenant tests and 149 new tests.
The selection also covers 90 discovery tests and 14 response-integrity tests.
Two unchanged HTTP-status regression tests complete the selection.
Tenant coverage is 98.31 percent with branch measurement.
The shared validator and name collector have complete executable-line coverage.
Two unchanged union exception handlers account for four uncovered lines.
One existing template-router branch remains uncovered.

The three Hypothesis properties each passed 40 generated examples.
Each property covers blank inputs, non-string inputs, or valid opaque strings.
The new tests also prove actual timeout and connection-error behavior at every
affected tenant boundary.

## Local Gates

Run full configured Ruff, Black, Bandit, and the CI mypy scope.
Read that scope from `MYPY_PATHS` in `.github/workflows/ci.yml`.
Run the required-input preflight before the unchanged test-quality ratchet.
Run Markdown link checks and the configured STE linter.
If the licensed dictionary is unavailable, record a partial heuristic result.

```bash
rtk proxy .venv/bin/python -m py_compile \
  MistHelper.py src/api/tenant_fetch.py \
  tests/unit/api/test_tenant_identifier_validation.py
rtk proxy .venv/bin/python -m ruff check .
rtk proxy .venv/bin/python -m black --check --diff .
rtk proxy .venv/bin/python -m mypy \
  src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml
rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r .
rtk proxy .venv/bin/python -m pylint src/api/tenant_fetch.py
rtk proxy .venv/bin/radon cc src/api/tenant_fetch.py -j | \
  rtk proxy .venv/bin/complexity-gate --max 10
rtk proxy .venv/bin/python -m pydocstyle src/api/tenant_fetch.py
rtk proxy .venv/bin/python -m vulture src/api/tenant_fetch.py \
  --min-confidence 70
```

**Results**: Syntax, full Ruff, full Black, the CI mypy scope, and full Bandit
passed. Black checked 2,009 files.
mypy checked 663 source files under the existing repository overrides.
Bandit reported no issues under the existing configuration.
Pylint scored 10.00. Complexity, docstring style, and unused-symbol checks passed.
Docstring coverage is 100 percent.
The structural check covered 23 new production and test methods.
It found zero violations.
The two public union methods each have 24 lines.
The production module retains eight children and 18 fetch methods.

## Test-Quality Scope

Run the required-input preflight before each analyzer check.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q \
  tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
rtk proxy .venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q \
  tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
rtk proxy .venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --roots tests/unit/api/test_tenant_identifier_validation.py \
  --include-mist-api
```

**Results**: The preflight read six inputs and checked three active guides.
The unchanged full ratchet checked 997 discovered files and 725 findings.
It reported zero new findings and zero parse errors.
Its existing API predicate excludes this new module and the original tenant
test module.

The stronger file-scoped check explicitly includes the new API test module.
Its report proves one analyzed file, zero findings, and zero parse errors.
Two omitted repository roots identify that deliberate supplemental scope.
The initial supplemental check found missing transport cases.
The added timeout and connection-error cases repaired both findings.
No baseline, stored exclusion, rule, or suppression changed.

## Runtime Dependency Audit

The standard strict runtime audit stopped during `ensurepip` with `SIGABRT`.
It did not complete dependency collection.
The allowed uv resolution produced a complete hashed runtime input.
The strict audit then ran without the failed pip resolver.

Set `AUDIT_INPUT` to a file in the session artifact directory.
Do not commit that generated file.

```bash
rtk proxy env UV_LINK_MODE=copy UV_SYSTEM_CERTS=1 UV_NATIVE_TLS=1 \
  uv pip compile requirements.txt --python .venv/bin/python \
  --generate-hashes --quiet --output-file "$AUDIT_INPUT"
rtk proxy .venv/bin/pip-audit -r "$AUDIT_INPUT" \
  --strict --require-hashes --no-deps --disable-pip \
  --progress-spinner off
```

**Result**: The hashed runtime audit checked 105 dependencies.
It reported zero known vulnerabilities and zero skipped dependencies.
The Git-pinned development tool is not a runtime audit input.
No requirement file, dependency pin, or audit ignore changed.

## Documentation and Publication

The Markdown link check scanned six tracked issue-owned files.
It reported zero broken links.
The configured STE linter passed the eight changed files at its score threshold.
Its dictionary scope is partial because `data/ste_dictionary.json` is unavailable.
The reported reason is `dictionary_unavailable`.
No licensed dictionary was created or obtained.

Publication remains blocked until the parent grants the verified `main` SHA.
The initial revision is `a5d465a461d2512b717e943278fdff2b1897df84`.
That initial revision is not a publication grant.
The post-commit comparison must use a freshly fetched `origin/main`.
The parent handoff records the clean commit SHA and post-commit results.
The broader audit of 102 historical candidates remains open.
