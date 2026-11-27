# Contract: gate configuration

This contract lists each gate setting that the audit reads or changes. The final gate pull request changes only the settings marked as changed. All other settings stay as they are on main.

| Setting | Value on main | Value after the final gate | Source |
| - | - | - | - |
| Python requirement | `>=3.15` | unchanged | `pyproject.toml` line 23 (RC-005) |
| Ruff target | `py315` | unchanged | `pyproject.toml` line 203 (RC-006 corrects the older 3.13 claim) |
| Ruff select list | `"E", "F", "W", "I", "UP", "B", "G", "PLW1514", "RUF100"` | adds `BLE001` and keeps `RUF100` | `pyproject.toml` line 209 (RC-003, RC-035, FR-022) |
| Ruff extend-exclude | four paths | unchanged | `pyproject.toml` line 206 (RC-004, FR-025) |
| Pylint disable list | `"C0114", "C0115", "C0116", "W0613", "W0718"` | removes `W0718` | `pyproject.toml` line 594 (RC-002, FR-023) |
| Pylint comment block | lines 588 to 593 state the 493-site count | rewritten to cite this record | `pyproject.toml` lines 588 to 593 (FR-023) |
| Pylint score floor | 9.5 | unchanged | `pyproject.toml` line 565, `ci.yml` line 122 (RC-128) |
| Pylint scope in CI | `SRC_PATH`, which is `src/` | unchanged | `ci.yml` lines 78 and 529 (RC-014) |
| Vulture confidence | 70 | unchanged | `ci.yml` line 127 (RC-010) |
| Radon maximum | 10 | unchanged | `ci.yml` line 549 (RC-016) |
| Bandit command | `bandit -c pyproject.toml -r .` | unchanged | `ci.yml` line 451 (RC-015) |
| Baseline excluded components | `["tests"]` | unchanged | `.github/blind-exception-handler-baseline.json` line 6 (RC-033) |
| Stored-baseline test | requires at least one entry | accepts an empty baseline | `tests/guardrails/test_blind_exception_handler_ratchet.py` line 445 (RC-032, FR-026) |
| Growth guard in CI | runs in the `tests/guardrails` shard | unchanged | `ci.yml` line 255 (RC-017) |

## Out of scope

- The black target version stays `py313` at `pyproject.toml` line 561 (Local evidence, blob equal to main). This audit does not change formatter settings.
- The `extend-exclude` list stays unchanged (FR-025, D-8). Follow-up issues cover the excluded trees (FR-032).

## Rules for the final gate

- Both changes land in one pull request (FR-024, D-9).
- Run the pylint gate before merge. The score must stay at 9.5 or higher (FR-023, U-14).
- Update the stored-baseline test in the same change (FR-026).
