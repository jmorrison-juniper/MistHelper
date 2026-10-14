# Restoration acceptance evidence

## Limits of this evidence

All restoration requests used fixture settings and mocked SDK transport.
No production restoration or firmware execution occurred.
Automated acceptance does not establish human approval.
Windows ACL decisions have automated coverage. Native Windows execution remains unverified.
The parent session owns deployment and the persistent runtime volume.

## Issue acceptance mapping

Test paths below use these roots:

- Unit: `tests/unit/firmware_policy/recovery/`
- Integration: `tests/integration/firmware_policy/recovery/`
- Contract: `tests/contract/firmware_policy/recovery/`
- Browser: `tests/e2e/web_portal/firmware_restore/`

| Issue criterion | Executed evidence |
| - | - |
| Separate menu restores selected verified records | Menu metadata guards, integration `test_cli_complete_and_dry_run`, browser selection flow |
| Every recovery backup verifies before the first write | Integration `test_complete_restore_preserves_original_and_verifies_all_recovery_records` |
| Preview and exact typed confirmation | Integration `test_exact_confirmation_precedes_backups_and_writes`, browser typed-confirmation controls |
| Every completed scope passes saved-state verification | Integration complete restoration and `test_failed_saved_state_stops_later_scopes` |
| First failure stops later writes and reports partial results | Integration HTTP 400/403/500/503 matrix, unit `test_mid_run_failures_stop_with_exact_partial_results`, browser failure flow |
| No firmware execution request | Exact settings endpoint/body assertions and contract `test_sdk.py` |
| Original backups remain unchanged and private | Integration byte equality, hostile-bundle unit tests, protected download denial, Windows owner/access tests |
| Protected dynamic graphical workflow | Browser `test_restore_portal.py`, real Chromium, real request protection, session ownership, expiration, cancellation, and single-use checks |

## Requirement coverage

| Requirement | Tasks | Verification |
| - | - | - |
| FR-001 | T012–T017 | CLI, menu metadata, protected portal, Chromium |
| FR-002 | T005–T006 | Corrupt, empty, malformed, linked, public, oversized, wrong-owner, duplicate, and invalid-record bundles |
| FR-003 | T009 | Wrong-cloud rejection and checksum authenticity warning |
| FR-004 | T007–T011 | Exact complete writable bodies and preserved unselected scopes |
| FR-005 | T007–T009 | Schema-defined exclusions and exact per-scope exclusion names |
| FR-006 | T007–T008 | Unknown fields, unsupported schema shapes, masked values, and schema errors |
| FR-007 | T007–T008 | Proven site inheritance deletion and rejection of unproven missing-field deletion |
| FR-008 | T009 | Complete paginated membership, foreign-site and ambiguous-owner rejection |
| FR-009 | T009–T011 | Dependency rejection and organization-before-site request order |
| FR-010 | T009, T017 | Safe identifiers, exact changed-field/deletion counts, exclusions, and zero preview writes |
| FR-011 | T010–T012 | Empty, lower-case, whitespace, and incorrect-word rejection |
| FR-012 | T010–T011 | All-target durable coverage and rejected private recovery-file access |
| FR-013 | T010–T011 | Changed settings, source, cloud, membership, and post-backup freshness |
| FR-014 | T010–T014 | Failed write, failed readback, ignored update, changed identity, and immediate stopping |
| FR-015 | T010, T017 | Exact completed, failed, and remaining identifiers |
| FR-016 | T014 | Settings-only requests and actual SDK HTTP 429 loop with one write attempt |
| FR-017 | T004–T005, T014, T017 | Source byte equality, private output denial, SDK logger/console redaction, and secret-free browser responses |
| SC-001 | T005, T007, T010, T017 | Invalid scenarios assert zero writes |
| SC-002 | T010 | Recovery evidence covers every selected scope before the first write |
| SC-003 | T010 | Completed scopes require exact saved writable equality |
| SC-004 | T010, T014 | Failure scenarios assert no later write |
| SC-005 | T012, T017 | Real CLI and Chromium flows use mocked SDK transport |
| SC-006 | T014, T017 | Fixture secret values are absent from output, logs, and browser responses |
| SC-007 | T005, T010 | Original source bytes remain equal |

## Recorded local results

- Feature and predecessor tests: **188 passed**. Changed-package coverage: **94.67 percent**.
- Move, structural, menu, SDK compatibility, and output guards: **977 passed, 3 skipped**.
- Symbol preservation: **862 modules and 15,069 baseline symbols checked**. No lost symbol.
- Full Ruff: `All checks passed!`
- Full Black: **2,412 files unchanged**.
- Configured mypy: `Success: no issues found in 844 source files`.
- Full configured Bandit: no finding. The fixed Windows command has documented false-positive annotations.
- Scoped complexity: `All functions within complexity threshold.`
- Source-package docstrings: **100 percent**. Configured whole-product docstrings: **99.7 percent**.
- Full source pylint: **9.93/10**, above 9.5. Scoped pylint: **9.99/10**.
- Configured whole-product Vulture and pydocstyle: no finding.
- Safe sweep without cloud credentials: **1 successful, 0 failed, 305 skipped**.
  The sweep skipped destructive menu 306. It did not test a cloud restoration.
- Runtime dependency audit of the fully resolved requirements: `No known vulnerabilities found`.
  The original audit command failed because its temporary ensurepip process terminated.
  UV resolution and `pip-audit --disable-pip --no-deps` supplied the complete-tree alternative.

Interrogate excludes `__init__.py` modules through the repository configuration.
Both firmware-policy portal modules use that filename.
A direct portal-only invocation therefore reported no Python files.
The source-package docstring result does not claim portal coverage.

The three guard skips have explicit causes.
The changelog diff guard needs a pull request event.
The Git environment regression needs a platform that removes an empty environment value.
The portal registry contains no operation of the tested unregistered class.

The advisory `speckit-task-audit --root .` reported existing historical references to absent session artifacts.
It is not a passing gate result. This feature adds no reference to an external session artifact.
Its remaining unchecked tasks describe the uncompleted commit, pull request, merge, and deployment sequence.

The full unrelated unit and integration suites were not run locally.
The targeted acceptance suite and every move guard ran locally.
The pull request must pass all required CI checks and CodeQL before merge.

Browser screenshots remain in ignored `test-artifacts/issue4218-complete.png` and `test-artifacts/issue4218-partial.png`.
They contain fixture data only.

## Specification analysis

The analysis examined the specification, plan, tasks, and constitution.
All 24 requirements and success criteria map to the 23 tasks.
Coverage is 100 percent. No uncovered requirement or blocking artifact conflict was found.
The analysis changed no constitution or quality baseline.

Optional commit hooks were deferred. Disabled companion hooks were not executed.
Safe explicit prerequisite checks replaced unavailable PowerShell commands.
Native Windows testing and actual human acceptance remain explicit verification limits.
