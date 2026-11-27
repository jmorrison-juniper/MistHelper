# Quickstart: Other-Device Event Export Fails Closed on Failed Pages

**Scope**: The exact steps to reproduce issue #4709, the expected test results before and after the fix, and the exact verification commands. Run the commands from the root of the feature worktree with `.venv` active.

## 1. Preconditions

1. The #1794 owner handoff names both files and is posted (T001).
2. A worktree exists for branch `fix/4709-other-device-events-page-failures`, created from `main`.
3. The worktree holds a `.venv`. Create it with the bootstrap steps in `.github/copilot-instructions.md`, section "Language and environment". A new worktree has no `.venv`.

## 2. Reproduce the Defect

No live Mist call is needed. The tests mock the SDK search function, `mistapi.get_next`, the site resolver, and the writer.

Run the targeted test file on the current exporter:

```powershell
python -m pytest tests/unit/export/test_site_other_device_events_exporter.py -q
```

Expected result before the fix:

| Test case | Result before the fix | Reason |
| - | - | - |
| 1 to 5 (`test_failed_first_page_writes_nothing`) | Fail | No ERROR line. The current code prints the no-data message. |
| 6 (`test_unknown_site_404_logs_error_without_raise`) | Fail | No ERROR line names HTTP 404. |
| 7a (`list_with_headers`) | Fail | The current code writes the first page. This is the issue's second case. |
| 7b (`dict_with_next`) | Fail | The current code ends with a `KeyError` and no page-named ERROR line. |
| 8 (`test_non_object_row_rejects_page`) | Fail | The current code writes the row. |
| 9 (`test_repeated_next_cursor_rejects_read`) | Fail | No ERROR line names the repeated cursor. |
| 10 (`test_total_mismatch_rejects_read`) | Fail | The current code writes one row when `total` is 2. |
| 11 (`test_non_integer_x_page_header_rejects_read`) | Fail | The current code writes the first page. |
| 12 (`test_complete_empty_read_prints_no_data_message`) | Pass | Guard test for the unchanged success path. |
| 13 (`test_complete_two_page_read_writes_once`) | Fail | The current code calls `mistapi.get_all`. |
| 14 (`test_failure_logs_omit_body_cursor_and_url`) | Fail | No ERROR line appears. |
| 15 (`test_successful_page_logs_before_and_after_request`) | Fail | The page-level INFO and DEBUG lines do not exist. |
| Five retained tests | Pass | Unchanged behavior. |

Caution: every `get_next` mock must use a finite `side_effect` list. A missing guard then raises an error and does not loop forever.

## 3. Verify the Fix

Run each command after the fix. Each command must report the expected result from `tasks.md`.

```powershell
python -m pytest tests/unit/export/test_site_other_device_events_exporter.py -q
python -m pytest tests/unit/export -q
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -q
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main
radon cc src/operations/exporting/export/site_other_device_events_exporter.py -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/operations/exporting/export/site_other_device_events_exporter.py -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src/operations/exporting/export/site_other_device_events_exporter.py
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4709-other-device-events-page-failures.md
```

Expected result after the fix: all 16 test cases and all five retained tests pass. The other commands report the results listed in `tasks.md`, task T-LOCAL-GATES.

Run the two full-test shards from `tasks.md` after the targeted commands pass.

## 4. Operator Check After the Fix

Run menu 258 against a known site with a complete result. The menu prints the count line and the file name. Run it again against a site with a failed page. The menu prints one ERROR line that names the page and the HTTP status, and no file is written.

Caution: a failed run leaves no file. Run menu 258 again after the cloud recovers.

## 5. Post-Merge Revision Check

After the squash merge and the `container-build.yml` run, compare the image revision with the merged commit. The command comes from `documentation/container-deployment.md`, section "Check the revision of the running container" (line 268).

```powershell
podman inspect misthelper-app --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'
git rev-parse origin/main
```

The two values must match. Deployment is an owner action, and this record claims no deployment.
