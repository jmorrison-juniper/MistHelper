# Implementation Plan: Resumed 52-week device-event CSV export

**Branch**: `fix/4721-device-events-csv-resume` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/3/4/1/4721-device-events-csv-resume/spec.md`. The base route comes from `.specify\scripts\powershell\spec-route.ps1` line 17.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design\`.

## Summary

Menu 97 streams 52 weeks of device events to `data\OrgDeviceEvents_52w.csv`. Merged PR #4834 added header checks, a missing-CSV refusal, and a read-failure stop. Three gaps remain on main. An empty checkpoint file starts a fresh run that replaces the CSV file. An in-place checkpoint write can leave that empty file. A resumed run with no new rows logs a misleading message. This plan closes those gaps in the existing exporter module and the existing extended test module.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.

**Primary Dependencies**: `mistapi` 0.64.x only. The pin is `mistapi>=0.64.0,<0.65` (`.github\copilot-instructions.md` line 21). The local `.venv` holds `mistapi` 0.64.1.

**Storage**: CSV file `data\OrgDeviceEvents_52w.csv`. Checkpoint file `data\OrgDeviceEvents_52w.<org_id>.checkpoint`. SQLite database `data\mist_data.db` stays unchanged.

**Testing**: `pytest` with mocked `searchOrgDeviceEvents`. No live Mist request is part of the tests.

**Target Platform**: Windows 11, macOS, and Linux. The product also ships as a Podman container. This change does not change the container.

**Project Type**: Single Python CLI project with a `src\` package tree.

**Performance Goals**: No measurable change. The change adds one temporary-file replace for each checkpoint write.

**Constraints**: No new dependency. No module or directory change. Log text must stay ASCII. Lines must stay at or below 120 columns (`pyproject.toml` line 202).

**Scale/Scope**: One exporter class, one test module, one operator guide section, one README row, one endpoint note line, and one changelog fragment.

## Constitution Check

*Gate: must pass before research and again after design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (`.specify\memory\constitution.md` line 40) | Pass with recorded debt | No module, directory, or test file is added. The proposed test path is rejected. See Complexity Tracking. |
| II. Class-based architecture | Pass | Changes stay inside the existing `DeviceEvents52wExporter` class. No wrapper function is added. |
| III. Safety-first | Pass | Every refusal runs before a write. No new destructive operation is added. No credential path is added. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline. |
| V. Observability and ASCII logging | Pass | New log text is ASCII. Each log call uses `%s` formatting. |
| VI. Inline comments | Pass | Each changed line gets an inline comment during implementation. |
| VII. Action logging | Pass | The checkpoint write logs info before and debug after. Each refusal logs an error. A failed write logs a warning. |
| Technology: mistapi only | Pass | The exporter keeps the `self.mistapi.api.v1.orgs.devices.searchOrgDeviceEvents` call. No direct HTTP request is added. |
| Technology: Podman | Pass (not applicable) | No container, compose, or image file changes. |
| Technology: file paths | Pass | The temporary name adds a suffix to the file name. It does not join path segments by hand. |
| Technology: data directory | Pass | All outputs stay under `data\`. |
| Technology: output backends | Fail (pre-existing, not changed) | `_write_initial_batch` and `_append_rows` write CSV rows with `csv` directly (`device_events_52w_exporter.py` lines 311 and 326). This change adds no new bypass. |
| Technology: database keys | Pass (not applicable) | The SQLite key is outside this change. |

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\2\3\4\1\4721-device-events-csv-resume\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      checkpoint-file.md
      csv-resume.md
      search-org-device-events.md
    checklists\
      requirements.md
      data-safety.md
```

### Source Code (repository root)

```text
src\operations\exporting\export\device_events_52w_exporter.py    (modify: lines 90-91, 120-125, 141-155, 342-353)
tests\unit\test_device_events_52w_exporter_extended.py            (modify: lines 83-88, and append six tests)
documentation\operator-guide.md                                   (modify: insert a section before line 744)
README.md                                                         (modify: add one row to the table at lines 115-133)
documentation\api\orgs\GET_orgs_org_id_devices_events_search.md   (modify: line 269)
changelog.d\issue-4721-device-events-csv-resume.md                (add)
```

No file is deleted. No module, package, directory, or test file is added.

**Structure Decision**: Keep the change inside existing files. The proposed path `tests\unit\export\test_device_events_checkpoint_recovery.py` is rejected. See `design\research.md` decision D-8.

## Implementation Outline

1. Add six new tests and update one existing test. Four new tests fail on main. This proves the defects (T001).
2. Change `_read_checkpoint` to refuse an empty checkpoint file when the CSV file exists (T002).
3. Change `_write_checkpoint` to write a temporary file, then replace the checkpoint file (T003).
4. Change `export()` and `_handle_empty_result` so a resumed run with no rows keeps both files and logs that no rows follow the checkpoint (T004).
5. Confirm the existing regression tests pass without edits (T009).
6. Update the operator guide, the README row, the endpoint note, and the changelog fragment (T005 to T008).
7. Run the local gates, open the pull request, watch CI, and merge only after authorization (T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).

### Code shape for the three changed methods

- `_read_checkpoint`: when the token is empty, find the CSV path with `self._paths()`. If the output format is CSV and the CSV exists, call `_refuse_resume`. Otherwise return `None`.
- `_write_checkpoint`: build the temporary sibling name from the checkpoint file name. Write the token to it. Call `os.replace`. On any exception, log a warning and keep the previous file.
- `export()` and `_handle_empty_result`: pass `search_after is not None` into `_handle_empty_result`. For a resumed run, log that no rows follow the checkpoint and return. Do not call `DataExporter`. Do not remove the checkpoint. Otherwise keep the fresh-run branch.

No new method, constant, or import is added. This keeps the module-level names unchanged. The symbol gate in T-LOCAL-GATES checks this.

## Local gate plan

The authoring agent ran no gate. The implementer runs these gates. Each gate names its expected result.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile MistHelper.py` and `python -m py_compile src\operations\exporting\export\device_events_52w_exporter.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Tests | `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py -q -p no:cacheprovider` | All tests pass |
| Full tests | The CI shards run the full unit tree. Local runs cover the changed module only. | CI result on the pull request |
| Coverage | `python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py --cov=src\operations\exporting\export --cov-report=term-missing` | Module coverage 99 percent or above |
| Test quality | The procedure in `.github\copilot-instructions.md` section "Test quality ratchet" (line 95) | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src\operations\exporting\export\device_events_52w_exporter.py -j \| complexity-gate --max 10` | No block above 10 |
| Security lint | `bandit -c pyproject.toml -r src\operations\exporting\export -q` | No finding |
| Dependency audit | Not applicable. The change adds no dependency. | Not run |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and coverage 90 percent or above |
| Menu reference | Not applicable. No menu title, handler, or registry entry changes. | Not run |
| Symbols | `symbol-diff --base origin/main src\operations\exporting\export\device_events_52w_exporter.py` | `no module-level name changed` |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md documentation/operator-guide.md documentation/api/orgs/GET_orgs_org_id_devices_events_search.md changelog.d/issue-4721-device-events-csv-resume.md` | Each file scores 80 or above |
| Ops portal and platform | Not applicable. No file in those trees changes. | Not run |
| Safe sweep | Not applicable. Menu 97 is in the `resource_intensive` category, and the sweep skips it. | Not run |
| Guardrail | `python -m pytest tests\guardrails\test_nested_package_structure.py -q -p no:cacheprovider` | Ratchet test passes with no new child |
| SDK compatibility | `python -m pytest tests\integration\test_mistapi_sdk_compatibility.py` | Guard passes with no new call site |

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| Windows blocks the replace step while another process holds the checkpoint | The checkpoint keeps the previous token. The next run repeats a batch. | The warning names the file. The operator guide describes the duplicate risk. |
| Operators meet the new refusal on an empty checkpoint | The run stops until the operator acts. | The refusal names the file and the next step. The operator guide gives the steps. |
| A resumed run with no new rows keeps its checkpoint | An operator must remove the checkpoint by hand. The next run then replaces the CSV. | The info line names the checkpoint. The operator guide describes the step. |
| An API error returns an empty page (finding A-19) | A streaming run can log completion and remove the checkpoint. | Out of scope. A follow-up issue is required (decision D-12). |
| The extended test module grows | Review cost rises. | Recorded as debt. A separate issue must split the module. |
| Draft PR #4813 changes the shared `escape_multiline` helper | Device-event CSV text could change. | Rebase after #4813 lands. Rerun the resume tests before merge. |
| The live `next` value is a URL, not a cursor | Resume requests fail or skip pages. | The owner verifies the live form before merge. See `design\research.md` Unverified item U-1. |
| `.tmp` files remain after a crash | Disk clutter. | The next successful write replaces the file. The operator guide names the file. |

## Rollback Steps

1. Revert the squash commit on `main`. The change has one commit.
2. Remove `data\OrgDeviceEvents_52w.<org_id>.checkpoint.tmp` when it exists.
3. No data migration is needed. The CSV and checkpoint formats do not change.

## Complexity Tracking

Existing violations that this change touches. Each one stays grandfathered. The change adds no new direct child.

| Violation | Measured value | Why it stays | Remediation action |
| - | - | - | - |
| `src\operations\exporting\export\` has more than five children | 49 children (tree `a0956c911946e08c84fee7a003099c7dc5f60a1e`) | The exporter file already exists in this folder. | Separate issue: move the device-event exporters into a compliant package. |
| `device_events_52w_exporter.py` holds more than five top-level names and class members | About 33 module-level names (lines 16-387) and 25 class methods (lines 74-368) | The change edits existing members only. | Separate issue: split the exporter by responsibility. |
| `tests\unit\test_device_events_52w_exporter_extended.py` holds more than five test functions | 49 test functions | The change adds six tests to the existing module. | Separate issue: split the extended module by method group. |

Rejected alternative: `tests\unit\export\test_device_events_checkpoint_recovery.py`. The folder `tests\unit\export\` has 55 children (tree `f87e46d24e73c34cda279cc88a5dfd16c26d55e4`). A new file adds a child to a noncompliant parent, which Principle I forbids.
