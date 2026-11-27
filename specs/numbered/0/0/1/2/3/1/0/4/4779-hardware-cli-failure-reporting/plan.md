# Implementation Plan: Hardware CLI failure reporting

**Branch**: `feat/4773-transceiver-master-report` (publication branch) | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/3/1/0/4/4779-hardware-cli-failure-reporting/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/3/1/0/4/4779-hardware-cli-failure-reporting/spec.md`.

## Summary

Keep the committed narrow failure boundary in the hardware CLI. Verify the three regression cases with a test run. Add four hardening changes: propagation for two more programming-error classes, a three-state admission model, a validated start reply, and operator cautions with matching logs. Publish the repair with the #4773 pull request.

## Technical Context

- **Language/Version**: Python 3.15. `pyproject.toml` requires `>=3.15`.
- **Primary Dependencies**: None new. The CLI uses the standard library and `InputUtils`. The failure path calls no `mistapi` function. Its batch calls go to internal services (`cli.py` lines 92 and 101).
- **Storage**: None new. Durable output stays under `data/`.
- **Testing**: pytest. Command: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`.
- **Target Platform**: Windows 11 development host. The code must also run on Linux and macOS.
- **Project Type**: Python CLI class inside the Flask portal package. The CLI needs no Flask app.
- **Performance Goals**: No change. Waits stay bounded by the deadlines in `Completion.wait`.
- **Constraints**: ASCII-only output and logs. No secret in logs. No new dependency. No new file in `operations/hardware/` or `tests/unit/websocket_streams/web/hardware/`.
- **Scale/Scope**: One CLI file, one test module, one operator-guide section, and one changelog fragment. Ten pytest cases.

## Current State

The table compares the issue text with the committed code.

| Topic | Issue 4779 text | Committed code (commit `8140bb37c`, branch tip `edc12d5ef`) |
| - | - | - |
| Exception catch | "catches Exception broadly" | Catches `StreamRequestError`, `OSError`, and `RuntimeError` (`cli.py` lines 70 and 243). |
| TypeError | Returns an incomplete result | Propagates, because no clause catches it. |
| Log text | "Hardware CLI ends without verified completion. Error type: OSError." | "Hardware CLI ends without verified completion. Cause: %s. Admitted: %s." (`cli.py` line 79). |
| Timing | Issue created 2026-11-11 23:05:37 UTC | Commit `8140bb37c` committed 2026-11-11 23:51:08 UTC. |

The issue output came from an earlier state that the committed code does not reproduce. Task T001 confirms the current result.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Fail, existing debt | `operations/hardware/` holds six children. `tests/unit/websocket_streams/web/hardware/` holds six. `test_cli.py` holds seven top-level names. This repair adds one test function and no child. See CT-1 to CT-4. Remediation: F-4. |
| II. Class-Based Architecture | Pass | The repair changes methods and state in existing classes. It adds no wrapper function. |
| III. Safety-First | Pass | The repair keeps `InputUtils.safe_input` for every prompt. Messages print class names and codes only. |
| IV. Full Deployment Pipeline | Pass, not executed | The plan lists each step: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. This step executed none of them. |
| V. Observability and Logging | Pass after T006 and T007 | The new log lines are ASCII and omit secrets. The branch has no log line before the preview and start requests (`cli.py` lines 92 and 101). T007 adds them. |
| VI. Inline Comments | Pass, with condition | Each new line gets an inline comment. T003 to T007 check each touched block. |
| VII. Action Logging | Pass after T007 | The branch lacks action logs in `_collect` (`cli.py` lines 89 to 103). T007 adds the info and debug pair. |
| Test containers | Not applicable | The tests run on the host with `.venv`. No container starts. |
| File paths | Pass | The repair builds no path string. The existing code uses `pathlib.Path`. |
| Output backends and export boundary | Not applicable | The CLI does not export rows. |
| Operational store | Not applicable | The repair adds no coordination record. |
| Database keys | Not applicable | The repair adds no table or key. |
| Data directory | Pass | The repair adds no output path. |
| Container security | Not applicable | No container change. |
| Zscaler and proxy | Not applicable | No container image push occurs. |
| Security findings | Pass | The repair adds no suppression. Production code contains no `assert` statement. |
| Documentation | Pass after T011 | T011 updates the operator guide and the changelog fragment. |
| Audience standard | Pass | Each operator message uses plain words and ASCII. |
| SpecKit escalation | Pass | The change touches four files and one class group. This specification applies. |
| Multi-agent git workflow | Pass with conditions D-1 and D-2 | Add `in-progress` to issue 4779 before T-PR. The branch name follows D-2. |
| Mist Cloud transport | Not applicable | The repair opens no HTTP request and changes no transport. |

## Architecture

The collection runs in this order.

1. `HardwareCollectionCli.run` creates `HardwareCliWorkflow` (`cli.py` lines 60 to 74).
2. `select` and `review` read operator answers (`cli.py` lines 121 to 160). A failure here keeps the admission state `not_started`.
3. `_collect` sends one preview request. It then sets the state to `uncertain` and sends one start request (`cli.py` lines 89 to 103).
4. A verified start reply sets the state to `admitted`.
5. `Completion.wait` polls the admitted parent and returns a verified result (`cli.py` lines 212 to 233).
6. `run` maps each exception class to one of three paths: propagate, operational failure, or interruption. The contract file defines the mapping.

## File-by-File Change Map

| Path | Action | Location | Change |
| - | - | - | - |
| `src/mist/realtime/websocket_streams/web/services/operations/hardware/cli.py` | Modify | Publication branch only. Absent on `main` (R-03). | Add the admission attribute, the start-reply validation, the programming-error clauses, the caution and cause text, and the action logs (FR-003 to FR-008). |
| `tests/unit/websocket_streams/web/hardware/test_cli.py` | Modify | Publication branch only. Absent on `main` (R-01). | Change three cases and add seven cases (FR-001 to FR-008). |
| `documentation/operator-guide.md` | Modify | Branch copy. The CLI section is absent on `main` (R-23). | Describe the two cautions and the stable causes (FR-010). |
| `changelog.d/issue-4773-transceiver-master-report.md` | Modify | Branch copy. Absent on `main` (R-24). | Name the issue in each bullet and keep the file name (FR-010, D-11). |
| `src/mist/realtime/websocket_streams/web/services/operations/hardware/preset.py` | Modify during rebase | Branch rename of `hardware_xml.py` (R-06). | Keep the formats `csv`, `master-xml`, and `csv-master-xml` from `main` (FR-009, D-12). |
| `specs/numbered/0/0/1/2/3/1/0/4/4779-hardware-cli-failure-reporting/` | Add | Publication branch. The route leaf is free (R-15). | This record. |

Not changed by this issue: `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `README.md`, the menu guard tests, and `CHANGELOG.md`. The `CHANGELOG.md` file is not edited on a feature branch (`changelog.d/README.md` rule 2).

## Local Gate Matrix

Each row lists the gate, whether it applies, and the note. Long commands appear in the code blocks below the table.

| Gate | Applies | Command or note |
| - | - | - |
| Compile | Yes | `python -m py_compile` on each changed `.py` file. `MistHelper.py` is not changed. |
| Lint | Yes | `python -m ruff check .`. Expected output: `All checks passed`. |
| Format | Yes | `python -m black --check .`. Expected output: no file needs a change. |
| Types | Yes | `python -m mypy` with `MYPY_PATHS` from `ci.yml` line 93. Re-read the value on the rebased branch. |
| Tests | Yes | `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`. Expected: all cases pass. |
| Full tests | Yes | The two `pytest-chunks` commands below. Run both before the push. |
| Safe sweep | No | No registered operation changes. |
| Coverage | Yes | The command below. CI requires 80 percent or above. Record the hardware package percentage. |
| Test quality | Yes | The three commands below. Expected: `gate: 0 new findings vs baseline`. Do not change the baseline file. |
| Complexity | Yes | `radon cc` with `complexity-gate --max 10`, as below. No function may exceed 10. |
| Security lint | Yes | `bandit` on the hardware package, as below. No finding. |
| Dependency audit | No | No dependency manifest changes. |
| Code quality | Yes | `pylint src/ --fail-under=9.5`. Score 9.5 or above. |
| Dead code | Yes | `vulture` with `VULTURE_PATHS` from `ci.yml` line 101, as below. |
| Docstrings | Yes | `pydocstyle` and `interrogate` with `PYDOCSTYLE_PATHS` (line 104) and `INTERROGATE_PATHS` (line 107). |
| Menu reference | No | No menu change. |
| Symbols | Yes | `symbol-diff --base origin/main` with the path of each changed `.py` file that exists on `origin/main`. Expected: `no module-level name changed`. For `preset.py`, compare the old path `hardware_xml.py`. |
| STE | Yes | `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file. Each file scores 80 or above. |
| Ops portal | No | No ops-portal change. |
| Ops platform | No | No ops-platform change. |

Full tests (Windows, from the copilot-instructions table):

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Coverage:

```powershell
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

Test quality preflight, required check, and full-suite check:

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Complexity, security lint, dead code, and docstrings:

```powershell
radon cc src/mist/realtime/websocket_streams/web/services/operations/hardware -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/mist/realtime/websocket_streams/web/services/operations/hardware -q
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
```

## Verification Checks

These checks cover the requirements that have no pytest case.

- **C-1 (publication)**: Read the pull request body with `gh pr view`. It must contain `Closes #4779` and `Refs #4773`. Covers FR-009.
- **C-2 (remote)**: Read the remote tree of the pushed commit. Record the blob SHA of each of the five changed files. Covers FR-011 and SC-004.
- **C-3 (documents)**: Run `ste-linter` on each changed document. Each file scores 80 or above. Covers FR-010.
- **C-4 (source)**: Search the CLI file for `except Exception` and `Admitted:`. Both searches return no line. Covers SC-003.

## Complexity Tracking

| ID | Violation | Why needed | Simpler alternative rejected because |
| - | - | - | - |
| CT-1 | `test_cli.py` holds eight top-level names after the repair. It held seven before. | One new test function covers three cases that share one setup. | A new test module adds a seventh child to `tests/unit/websocket_streams/web/hardware/`, which already holds six. |
| CT-2 | `operations/hardware/` holds six children. | This is the existing design of the #4773 branch. | This repair adds no child. Splitting belongs to follow-up F-4. |
| CT-3 | `tests/unit/websocket_streams/web/hardware/` holds six children. | This is the existing design of the #4773 branch. | This repair adds no child. Splitting belongs to follow-up F-4. |
| CT-4 | `HardwareCliWorkflow` gains one attribute. It already holds five methods and nested classes. | The admission state needs one stored value. The repair adds no method. | A new enum class adds a top-level name to `cli.py`, which already holds five. |

## Dependencies

- The publication depends on the decision to push the #4773 branch. The orchestrator authorizes the push.
- The repair depends on `ExplicitSessionServices` in `factory.py`. The name is absent on `main` (R-07).
- The repair depends on `raise_on_cancel` in `input_utils.py`. The parameter is absent on `main` (R-08).
- Both dependencies arrive with the publication branch. Neither is a new dependency for this repair.

## Risks and Mitigations

| ID | Risk | Mitigation |
| - | - | - |
| RK-1 | Rebase conflicts in `hardware_xml.py` and `preset.py`. `main` modified the file after the branch base, and the branch renamed it (L-19). | Keep the formats from both sides (D-12). Run `test_ws_hardware_master_xml.py` in T002. |
| RK-2 | The repair stays absent from GitHub until the push. | Verify each changed path after the push (T-REMOTE-CI and check C-2). |
| RK-3 | The three regression cases may fail on the branch. | T001 records the actual result. A failure stops the work until its cause is known. |
| RK-4 | An operator reads the caution as a portal failure. | The caution names the portal check as the next step. T011 documents the text. |
| RK-5 | The report publication path hides programming errors in the CLI result. | Follow-up F-2. This issue keeps the report path unchanged (D-9). |
| RK-6 | New test cases add test-quality findings. | Use explicit assertions. Run the required test-quality check before the push. Keep the baseline unchanged. |
| RK-7 | The #4773 record states 64 and 66 CLI cases. | Record the count from T-LOCAL-GATES. Do not copy either number. |
| RK-8 | The menu blocker from #4607 may still apply. | The owner confirms the status before menu work. This issue adds no menu. |

## Rollback Steps

1. Before the push, add a revert commit on the publication branch. The commit restores the committed content of the CLI file and the test module. Do not reset the shared checkout.
2. After the squash merge, open a new issue for any defect. Branch from `main` for the fix.
3. Do not push a commit to a branch that a merged pull request used.

Warning: never run `git reset --hard` or `git clean` in the shared checkout. Those commands delete uncommitted work.

## Not Applicable Items

- Mist API endpoint behavior: the repair calls no endpoint. `documentation/mist-api-openapi31yaml.yaml` is not needed.
- mistapi SDK: the failure path calls no `mistapi` function. The record makes no SDK claim.
- Podman containers: the tests run on the host. No container starts. `documentation/container-deployment.md` does not apply.
- Juniper device behavior and Podman skills: the issue concerns exception handling only. No skill is loaded.
