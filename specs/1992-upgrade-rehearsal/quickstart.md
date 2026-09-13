# Quickstart: The upgrade rehearsal harness

**Feature**: `specs/1992-upgrade-rehearsal/` | **Date**: 2026-09-04

This guide states how to run the rehearsal suite. It states how to read the
result. It states how to run the defect drill of User Story 3.

Warning: do not run the live scenario C or the live scenario D from this guide.
The live run writes firmware to real hardware. One switch of issue #2007 rebooted
with the reboot control off, and six access points lost power for six minutes.

## 1. Prerequisites

Use the virtual environment of this worktree. Every command below uses it.

```powershell
.venv\Scripts\python.exe --version   # The version must read 3.13 or newer.
```

The rehearsal needs no cloud token. It needs no network. It needs no browser.

## 2. Run the whole rehearsal suite

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_cascade.py tests/unit/upgrade_portal/test_rehearsal_stop.py tests/unit/upgrade_portal/test_rehearsal_defects.py -v
```

**Expected result**: Every test passes. The run finishes in under 60 seconds.
The summary line reports the duration, which proves SC-002.

## 3. Run one story at a time

Each story runs alone. The specification asks for that independence.

| Story | Command |
| - | - |
| User Story 1, the settle gate | `pytest tests/unit/upgrade_portal/test_rehearsal_cascade.py` |
| User Story 2, the stop control | `pytest tests/unit/upgrade_portal/test_rehearsal_stop.py` |
| User Story 3, the defect drill | `pytest tests/unit/upgrade_portal/test_rehearsal_defects.py` |

## 4. Read the result of the cascade rehearsal

The cascade test asserts these facts. Each fact maps to a pass condition of
scenario C.

1. The phases settle in the order gateways, switches, access points, clients.
2. No later phase started before the earlier phase settled.
3. A device stayed unsettled at 59 seconds after the reboot proof.
4. The gate marked that device settled at 60 seconds.
5. An access point stayed unsettled at 60 seconds.
6. The gate marked the access point settled at 120 seconds.
7. The driver started the post-check capture after the client phase settled.
8. The run status answer arrived in under 1 second during the run.
9. The stand-in cloud counted zero firmware write calls.

## 5. Read the result of the stop rehearsal

The stop test asserts these facts. Each fact maps to a pass condition of
scenario D.

1. The stop cancelled every device that did not start to write firmware.
2. The stop did not interrupt the device that writes firmware now.
3. That device appears in the `already_writing` list.
4. The message states that the device will finish the write.
5. The session smart router cancelled through the organization scope call.
6. The run record shows `scope: "org"` for that device.

## 6. Run the defect drill

The drill applies each defect with `monkeypatch`. Each drill test passes when
the matching rehearsal fails.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_defects.py -v
```

**Expected result**: Three tests pass. Each test names its defect class in the
test name and in the failure message that it captured.

| Defect class | What the drill changes | What the rehearsal reports |
| - | - | - |
| The search omits `device_type` | The stand-in loses the parameter | The gateway phase and the switch phase never settle |
| The gate reads a local clock | `gate.uptime_decreased` always answers true | A device settles on the first poll round |
| The code reads `phase` | `_normalize_status` reads the wrong key | The status carries no phase |

The drill needs no scratch copy of the branch. pytest reverts each patch at the
end of its test, so the worktree stays clean.

## 7. Prove that the suite makes no network call

The suite blocks the socket layer for the whole run. Run this command to see the
guard report its count.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_cascade.py -k network -v
```

**Expected result**: The guard reports zero attempts. A blocked socket changes
no result, which proves SC-004.

## 8. Run the quality gates

Run each gate before you open a pull request.

```powershell
.venv\Scripts\python.exe -m ruff check tests/support/rehearsal tests/unit/upgrade_portal
.venv\Scripts\python.exe -m black --check tests/support/rehearsal
.venv\Scripts\python.exe -m mypy tests/support/rehearsal
.venv\Scripts\python.exe -m pylint --fail-under=9.5 tests/support/rehearsal
.venv\Scripts\python.exe -m radon cc -n C tests/support/rehearsal
.venv\Scripts\python.exe -m vulture tests/support/rehearsal
.venv\Scripts\python.exe -m pydocstyle tests/support/rehearsal
.venv\Scripts\python.exe -m interrogate --fail-under 90 tests/support/rehearsal
```

## 9. Grade every Markdown file of this feature

FR-032 and SC-008 ask for a score of 80 or above. Grade all 11 Markdown files
of this feature.

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/spec.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/plan.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/research.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/data-model.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/quickstart.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/tasks.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/live-checklist.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/analysis.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/checklists/requirements.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/contracts/rehearsal-cloud.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/1992-upgrade-rehearsal/contracts/rehearsal-clock.md
```

## 10. What the rehearsal cannot prove

The rehearsal proves the portal logic. It cannot prove two facts.

1. The cloud accepts the upgrade call and the cancel call.
2. The hardware reboots and returns with the new firmware.

The live checklist of User Story 4 holds those facts. The implementation phase
writes that checklist to `specs/1992-upgrade-rehearsal/live-checklist.md`. The
checklist holds 5 items or fewer, and it carries the reboot warning of issue
#2007.

## 11. Known limitation

The rehearsal does not replace the browser suite. The browser suite keeps the
site lock, the reschedule, the cancel, and the retry. Issue #1992 stays open,
because the live run of scenario C and scenario D stays a human decision.

## 12. The measured duration

SC-002 caps the whole rehearsal suite at 60 real seconds. SC-003 caps one wait
at 1 real second. The command below measures both.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_support.py tests/unit/upgrade_portal/test_rehearsal_cascade.py tests/unit/upgrade_portal/test_rehearsal_stop.py tests/unit/upgrade_portal/test_rehearsal_defects.py -q --durations=20
```

The run of 4 September 2026 gave these results.

| Reading | Value | Budget |
| --- | --- | --- |
| Tests | 48 passed | - |
| Whole suite, fixed order | 5.26 seconds | 60 seconds |
| Whole suite, random order | 41.00 seconds | 60 seconds |
| Longest single test | 0.63 seconds | 1 second |

The longest test is the first defect drill. That drill hides every gateway
event, so the run waits for the phase deadline. The deadline is 1800 simulated
seconds, and the driven clock spends no real time on them.

## 13. A note on the type gate

The `pyproject.toml` file holds `\tests` in the mypy exclude list, so a plain
`mypy tests/support/rehearsal` reads no file at all. Run the gate with a small
config file that turns strict mode on and excludes nothing.

```powershell
.venv\Scripts\python.exe -m mypy --config-file .mypy_rehearsal.ini tests/support/rehearsal
```

The file holds five lines: `[mypy]`, `strict = True`,
`explicit_package_bases = True`, `ignore_missing_imports = True`, and
`warn_unused_ignores = False`.
