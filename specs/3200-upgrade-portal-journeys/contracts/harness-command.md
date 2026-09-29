# Contract: The harness command

**Feature**: #3200 | **Package**: `tests/e2e/upgrade_portal/journeys/`

This contract states the command, the pytest entry, the selection options, and
the exit codes.

## The command

```text
python -m tests.e2e.upgrade_portal.journeys.run_journeys [options]
```

| Option | Values | Default | Rule |
| - | - | - | - |
| `--parallel` | 1 or more | 3 | The number of fresh-server journey processes that run at one time. |
| `--keyword` | A pytest `-k` expression | Empty | Selects the journey tests that match the expression. |

The runner starts one shared pytest process for each journey test file. It
also starts one pytest process for each selected `fresh_server` item. This
keeps site locks and operation records isolated.

## The pytest entry

```text
UPGRADE_PORTAL_JOURNEYS=1 pytest tests/e2e/upgrade_portal/journeys -m journey -k "test_selection_reaches_the_capture_page"
```

| Item | Rule |
| - | - |
| Gate | `UPGRADE_PORTAL_JOURNEYS=1`. Without it, each `journey` item reports `skipped`. |
| Marker `journey` | Each catalog case carries it. |
| Marker `fresh_server` | A case with `server` set to `fresh` carries it. |
| Strict `xfail` | A case with an issue carries it. The reason names the issue number. |
| Options | Use pytest selection, such as `-k` and node identifiers. |
| Self-tests | The default pytest command collects the journey folder and skips each journey with the opt-in reason. |

## The exit codes

| Code | Meaning |
| - | - |
| 0 | Each selected case passed, or it failed as its strict `xfail` expects. |
| 1 | A case failed, a gap row is out of date, a trap counter is not zero, a credential value occurs, or a harness gap occurs. |
| 2 | An option is wrong, or pytest stops before it runs a test. |
| 3 | The environment is not ready. For example, Chromium is missing. |
| 5 | No test matched the selection for one child process. The runner treats this as pass. |

## The artifact directory

```text
test-artifacts/upgrade-portal-journeys/<run-id>/
├── summary.json
├── index.html
└── <journey-name>/
    ├── journey.json
    └── <step-number>-<step-name>.png
```

The harness writes only below this directory. The `test-artifacts/` root is a
local test output root, and git ignores it.
