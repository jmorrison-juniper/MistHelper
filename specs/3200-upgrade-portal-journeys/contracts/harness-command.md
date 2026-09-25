# Contract: The harness command

**Feature**: #3200 | **Package**: `tests/support/upgrade_portal_e2e/harness/run/`

This contract states the command, the pytest entry, the selection options, and
the exit codes.

## The command

```text
python -m tests.support.upgrade_portal_e2e.harness.run [options]
```

| Option | Values | Default | Rule |
| - | - | - | - |
| `--set` | `smoke`, `default`, `large`, `all` | `smoke` | `smoke` holds `M-ASG` and `S-ASG` (FR-049). `default` holds each case of the default fleet. |
| `--journey` | A catalog identifier, one or more times | None | Selects each named case |
| `--story` | `US1` to `US8` | None | Selects the cases of a user story |
| `--mode` | `single`, `multi`, `shared` | None | Selects the cases of a mode |
| `--families` | `A`, `S`, `G`, `AS`, `AG`, `SG`, `ASG` | None | Selects the cases of a family combination |
| `--fleet` | `default`, `large` | From the set | Selects the cases of a fleet |
| `--workers` | 1 or more | 3 | The number of child processes. Each child has its own journey server. |
| `--multiple` | 1 or more | 60 | The multiple of the journey clock |
| `--run-id` | Text | UTC time and a random suffix | The name of the run directory |
| `--seed-defect` | A name of [journey-server.md](journey-server.md) | None | Starts each journey server with that seeded defect |
| `--earlier-report` | A path | The newest report of the same fleet | The source of each delta (PR-011) |
| `--profile` | None | Off | Runs `RouteProfile` after the journeys |

The options `--journey`, `--story`, `--mode`, `--families`, and `--fleet`
select the cases that match each given option.

## The pytest entry

```text
UPGRADE_PORTAL_JOURNEYS=1 pytest tests/integration/upgrade_portal/journeys -m journey --journey-id M-ASG
```

| Item | Rule |
| - | - |
| Gate | `UPGRADE_PORTAL_JOURNEYS=1`. Without it, each `journey` item reports `skipped`. |
| Marker `journey` | Each catalog case carries it. |
| Marker `fresh_server` | A case with `server` set to `fresh` carries it. |
| Strict `xfail` | A case with an issue carries it. The reason names the issue number. |
| Options | `--journey-id`, `--journey-story`, `--journey-mode`, `--journey-family`, `--journey-fleet`, `--journey-set` |
| Self-tests | `test_harness_contract.py` carries no `journey` marker, so the default pytest command runs it. |

## The exit codes

| Code | Meaning |
| - | - |
| 0 | Each selected case passed, or it failed as its strict `xfail` expects. |
| 1 | A case failed, a gap row is out of date, a trap counter is not zero, a credential value occurs, or a harness gap occurs. |
| 2 | An option is wrong. |
| 3 | The environment is not ready. For example, Chromium is missing, or no port is free. |

## The artifact directory

```text
data/test-artifacts/upgrade-portal-journeys/<run-id>/
├── report.json
├── index.html
├── parity-matrix.md
├── inspection.json
├── servers/<worker>/server.log
└── journeys/<case>/
    ├── journey.json
    ├── step-<number>.png
    ├── trace.zip            # A failed case only (FR-063)
    ├── server-excerpt.log
    └── runner-excerpt.log
```

The harness writes only below this directory and the temporary directory of
the operating system (SR-015). The harness keeps each earlier run directory.
