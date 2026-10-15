# Synthetic validation

Use the isolated worktree environment. Do not configure production credentials.

```sh
source .venv/bin/activate
python -m pytest tests/unit/firmware_policy_jobs tests/integration/firmware_policy tests/e2e/web_portal/test_firmware_policy.py
python -m ruff check web_portal/routes/firmware_policy src/operations/execution/firmware_policy tests/unit/firmware_policy_jobs tests/integration/firmware_policy tests/e2e/web_portal/test_firmware_policy.py
```

Expected results include one-scope comparisons, no private fixture values,
unchanged bundle bytes, unchanged proof availability, locked preparation,
safe definite-failure retry, and highest initial versions.
Browser tests use synthetic settings and a kernel-selected loopback port.

## Recorded local results

The affected suite passed 357 tests with 93.14 percent coverage.
The suite includes unit, contract, integration, and Chromium tests.
Three comparison flows also passed explicit 800-pixel geometry checks.
Each check measures content width and detects horizontal scope-table movement.

```sh
.venv/bin/python -m pytest -q tests/unit/firmware_policy_jobs tests/integration/firmware_policy tests/unit/firmware_policy tests/contract/firmware_policy tests/e2e/web_portal/test_firmware_policy.py tests/e2e/web_portal/firmware_restore/test_restore_portal.py --cov=src.operations.execution.firmware_policy --cov=web_portal.routes.firmware_policy --cov-report=term --cov-fail-under=80 --screenshot only-on-failure --tracing retain-on-failure --output="$(pwd)/test-artifacts/issue-4229-browser"
.venv/bin/python -m pytest -q tests/e2e/web_portal/test_firmware_policy.py -k 'expands_owned or historical_view or restore_comparison'
```

The relevant structural, changelog, registry, SDK, and destructive-menu guards
passed 53 tests. Two existing guard checks skipped with documented causes.
The SDK scanner examined 559 signatures and reported no known signature failure.

| Command | Result |
| - | - |
| `.venv/bin/python -m ruff check .` | All checks passed. |
| `.venv/bin/python -m black --check .` | 2,437 files unchanged. |
| `.venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Success across 844 source files. |
| `.venv/bin/python -m mypy web_portal/routes/firmware_policy/restore/policies.py web_portal/routes/firmware_policy/restore/inspection.py web_portal/routes/firmware_policy/restore/__init__.py web_portal/routes/firmware_policy/jobs/manager.py --config-file pyproject.toml` | Success across four portal files. |
| `.venv/bin/python -m py_compile MistHelper.py web_portal/routes/firmware_policy/jobs/manager.py web_portal/routes/firmware_policy/restore/inspection.py web_portal/routes/firmware_policy/restore/policies.py` | No errors. |
| `node --check web_portal/static/js/firmware-policy.js` | No errors. |
| `.venv/bin/bandit -c pyproject.toml -r src/operations/execution/firmware_policy web_portal/routes/firmware_policy -q` | No findings. |
| `.venv/bin/pydocstyle src/operations/execution/firmware_policy web_portal/routes/firmware_policy` | No violations. |
| `.venv/bin/interrogate src/operations/execution/firmware_policy web_portal/routes/firmware_policy --fail-under 90` | 100 percent. |
| `.venv/bin/radon cc src/operations/execution/firmware_policy web_portal/routes/firmware_policy/restore -j \| .venv/bin/complexity-gate --max 10` | No block exceeds 10. |
| `.venv/bin/vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No findings. |

Symbol comparison against the base found no lost module-level names.
The route initializer intentionally adds `HistoricalInspection`, `InspectionRoutes`,
and the imported Flask `session` name. Its symbol command therefore returns 1.
The other four changed product modules report no symbol changes.

The direct requirements audit could not create its temporary environment.
Its `ensurepip` subprocess stopped with `SIGABRT`.
The alternate audit examined the complete UV-resolved runtime requirements and
reported `No known vulnerabilities found`.
The installed-tool audit separately reported existing pip 26.0.1 advisories.
No dependency file changed.

```sh
uv pip compile requirements.txt --python .venv/bin/python --quiet --output-file test-artifacts/issue-4229-runtime-resolved.txt
.venv/bin/pip-audit --no-deps --disable-pip -r test-artifacts/issue-4229-runtime-resolved.txt
```

The parent owns connected acceptance, production evidence, and release.
No container, production credential, real backup, or production write was used.

## Parent browser acceptance

The parent independently examined policy and historical screenshots at 800 pixels.
Saved, current, proposed, and difference labels remained visible without clipped fields.
The parent confirmed the highest default, preparation locking, accessible expansion,
selection invalidation, historical viewing, and explicit current comparison.
The browser reported zero page errors.

The CI evidence contract and workflow guards passed 29 tests.
The contract checks two artifact paths and three browser capture arguments.
Four mutation cases prove that missing paths or capture arguments fail.
Two additional cases prove repository-rooted paths after a working-directory change.
The dedicated `firmware-policy-browser-evidence` artifact retains successful-flow
screenshots and failed-flow screenshots and traces.
The existing restoration evidence artifact remains unchanged.
Screenshot paths resolve from the test module to the repository artifact directory.
The CI failure-output path uses `github.workspace`, not the isolated test working directory.
Local preflight verified both repository PNG files at 800 pixels wide.
An intentionally failing synthetic capture probe retained one PNG and one valid trace ZIP.
The temporary probe test was removed after verification.

The parent recorded independent connected read-only acceptance in
[the issue evidence](https://github.com/jmorrison-juniper/MistHelper/issues/4229#issuecomment-6186028684).
The parent owns the private inputs and artifacts. This child received only sanitized results.

This acceptance used the credential-free fixture at `127.0.0.1:9667`.
Its responsive JavaScript matches product commit
`b0a2a98bde3f29dd3ad7c652557f6f734b761a33`.
The server process preceded the final server edits.
This result confirms synthetic browser behavior, not the final server process or production acceptance.
The final handoff identifies the committed candidate and its restarted fixture separately.
