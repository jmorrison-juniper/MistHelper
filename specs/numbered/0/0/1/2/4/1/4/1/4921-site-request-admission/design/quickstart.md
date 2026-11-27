# Quickstart: Site Request Admission by Organization

Use these steps to reproduce issue #4921 and to verify the fix. Run each command from the root of a worktree that starts at `main`. Do not run commands in the shared checkout that holds the local working-copy edits (`research.md` section 4).

## Prerequisites

1. Install Python 3.15 and create the environment with the bootstrap command in `.github/copilot-instructions.md`, section Language and environment.
2. Activate the environment with `.venv\Scripts\Activate.ps1` on Windows, or `source .venv/bin/activate` on Linux.
3. Confirm the pinned SDK with `python -m pip show mistapi`. The expected version is 0.64.1 (`requirements.txt` line 129).
4. The unit tests need no Mist token and no Redis service. They use a fake Redis client.

## Reproduce the Defect on Main

1. Run the fail-closed test that already exists on `main`:

   `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py::TestRequestAdmission::test_site_request_requires_organization_context -q`

   Expected result: one test passes. An unscoped site request with no organization refuses.

2. Run the learning test that task T005 adds, before the fix lands:

   `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py::TestRequestAdmission::test_listed_site_uses_the_listing_organization -q`

   Expected result on `main`: the test fails with `ConnectionError: Site API request admission requires a selected organization.` The organization listing has no effect on the site request.

3. Run the batch-thread test that task T005 adds, before the fix lands:

   `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py::TestRequestAdmission::test_worker_thread_admits_a_listed_site_without_a_binding -q`

   Expected result on `main`: the test fails with the same refusal. This case matches the batch workers that menu 309 runs.

## Verify the Change

Run these commands after each task. Each command names one task from `tasks.md`.

| Task | Command | Expected result |
| --- | --- | --- |
| T005 and T006 | `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py -q` | All tests pass |
| T008 | `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py -q` | All tests pass |
| T009 | `python -m pytest tests/unit/ex_hardware_inventory/scope/test_hardware_session.py -q` | All remaining tests pass |
| T012 | `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py -q` | All tests pass |
| T010 | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` | All tests pass |
| T013 | `python -m pytest tests/guardrails/test_process_folder_structure.py -q` | All tests pass |
| T-LOCAL-GATES | `python -m ruff check .` | `All checks passed` |
| T-LOCAL-GATES | `python -m black --check .` | No file needs a change |
| T-LOCAL-GATES | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| T-LOCAL-GATES | `radon cc src/interfaces/wan_performance/collection/request_admission.py -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| T-LOCAL-GATES | `bandit -c pyproject.toml -r src/interfaces/wan_performance/collection -q` | No finding |
| T-LOCAL-GATES | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| T-LOCAL-GATES | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| T-LOCAL-GATES | `pydocstyle src/ wsgi.py web_portal` | No violation |
| T-LOCAL-GATES | `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v` | Coverage 90 percent or above |
| T-LOCAL-GATES | `symbol-diff --base origin/main src\operations\exporting\ex_hardware_inventory\scope\session.py` | Only `AdmissionBinding` is removed. Exit code is 0 |
| T-LOCAL-GATES | `symbol-diff --base origin/main src\interfaces\wan_performance\collection\request_admission.py` | Only the new class and the new methods are added |
| T-LOCAL-GATES | `symbol-diff --base origin/main src\operations\exporting\ex_hardware_inventory\run\batch.py` | Only the import of `AdmissionBinding` is removed |
| T-LOCAL-GATES | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Coverage holds at 80 percent or above for the shards |
| T-LOCAL-GATES | `python MistHelper.py --test` | Each `safe` operation completes. Without `MIST_APITOKEN`, the Mist checks skip with a credential reason |

The symbol command reports the removal of `AdmissionBinding`. That removal is intended, and the pull request body must say so.

## Optional Live Read-Only Check

Use this check only after the unit tests pass. It needs a valid `MIST_APITOKEN` in the environment. Never store the token in a file under version control.

1. Set `WAN_SHARED_ADMISSION` to `true` in the environment.
2. Use the existing `misthelper-redis` service of the compose group. Do not start a second Redis service.
3. Run `python MistHelper.py --menu 309`.
4. Stop at the preview. Confirm that the preview lists the connected EX switches. Confirm that no line shows `Site API request admission requires a selected organization.`

Caution: confirming the batch opens remote shells on EX switches. Do not type the confirmation phrase in this check.

Caution: a second Redis service on port 9379 or 9529 can take the port of the running store. Do not publish those ports.

## Cleanup

Remove any ephemeral container by its exact name only, for example `misthelper-tmp-issue4921-site-request-admission`.

Warning: a system prune or a volume prune command removes the data of other users on a shared host. Do not run either command.
