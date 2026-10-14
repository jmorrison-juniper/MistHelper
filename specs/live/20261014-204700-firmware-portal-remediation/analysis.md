# Specification Analysis Report

The analysis examined `spec.md`, `plan.md`, `tasks.md`, and the project constitution.
It checked all three required artifacts through the active feature pointer.
PowerShell is unavailable, so the prerequisite script could not execute.
A direct path check verified the same required inputs and reported three examined artifacts.

The analysis itself was read-only. This file records its completed result as required by T020 and T021.

## Findings

| ID | Category | Severity | Locations | Summary | Recommendation |
| - | - | - | - | - | - |
| None | Consistency | None | The three core artifacts | No blocking artifact conflict, uncovered requirement, or unresolved placeholder was found. | Continue the release checks. |

## Coverage summary

| Requirement key | Has task | Task IDs | Notes |
| - | - | - | - |
| FR-001 | Yes | T007, T010 | Category, semantic selection, and responsive workspace |
| FR-002 | Yes | T006, T009, T013 | Checked identity and saved-record labels |
| FR-003 | Yes | T005, T008, T010 | Complete supported catalogs across hardware classes |
| FR-004 | Yes | T008, T010 | Dynamic controls and natural descending order |
| FR-005 | Yes | T008, T010 | Every day and 02:00 defaults |
| FR-006 | Yes | T004, T009, T012, T014 | Complete verified preparation before confirmation |
| FR-007 | Yes | T006, T009, T015, T016 | Exact words, ownership, and single use |
| FR-008 | Yes | T005, T006, T008, T013, T016 | Waiting progress and sorted compact results |
| FR-009 | Yes | T011, T012, T014, T016 | More than 4000 sites and large bundles |
| FR-010 | Yes | T011, T014 | Bounded record parsing without aggregate limits |
| FR-011 | Yes | T004, T011, T012, T014 | Privacy, integrity, freshness, recovery, and readback |
| FR-012 | Yes | T005, T016 | Shared admission and authoritative rolling-hour usage |
| FR-013 | Yes | T004, T012, T014, T016 | Organization-first writes and uncertain outcomes |
| FR-014 | Yes | T006, T015, T016 | Persistent state and explicit interruption |
| FR-015 | Yes | T011, T014, T017 | Private records and sanitized fixture evidence |
| FR-016 | Yes | T018, T019, T021 | Guides, references, release note, and acceptance mapping |
| SC-001 | Yes | T007, T010 | 1440-pixel, 800-pixel, and 390-pixel browser checks |
| SC-002 | Yes | T014, T016 | Exact complete 4001-site request budgets |
| SC-003 | Yes | T011, T014 | Roundtrip above 17402805 bytes |
| SC-004 | Yes | T009, T014, T016 | Zero premature writes across failure paths |
| SC-005 | Yes | T015, T016 | Valid waits beyond ten minutes and refresh |
| SC-006 | Yes | T014, T017 | Private output denial and fixture-only evidence |

## Constitution alignment

The described design retains SDK transport, typed confirmation, private storage, and separate destructive workflows.
It does not weaken the generic safe-operation gate.
New job modules use a nested package. Existing operation-page files receive narrow integration changes.
The plan records existing structure debt and incremental remediation.
No constitution change or new transport exception is requested.

The parent owns the remaining release stages, including connected acceptance, merge approval, image verification, and deployment.
These stages are pending, not bypassed.
This analysis does not certify every inherited source-style rule or claim Windows execution.

T001 through T003 cover setup. T020 through T022 cover validation and release.
The remaining tasks map to the requirements above. No task is unrelated.

## Metrics

- Total requirements: 22, including six measurable success criteria.
- Total tasks: 22.
- Requirement coverage: 100 percent.
- Ambiguity findings: 0.
- Duplication findings: 0.
- Critical findings: 0.

## Local gate evidence

The table below records the implementation milestone.
The guarded-candidate checks follow it.
Actual-source acceptance remains blocked and is not a passing release criterion.

Commands below use `.venv/bin/` executables in this worktree.

| Command | Result |
| - | - |
| `python -m pytest tests/unit/firmware_policy tests/contract/firmware_policy tests/integration/firmware_policy tests/unit/firmware_policy_jobs tests/e2e/web_portal/test_firmware_jobs.py tests/e2e/web_portal/test_firmware_policy.py tests/e2e/web_portal/firmware_restore/test_restore_portal.py -q --cov=src/operations/execution/firmware_policy --cov=web_portal/routes/firmware_policy --cov-report=term-missing --cov-fail-under=80` | 271 passed. Coverage 94.34 percent. |
| `python -m ruff check .` | All checks passed. |
| `python -m black --check .` | 2429 files unchanged. |
| `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Success for 844 source files. |
| `bandit -c pyproject.toml -r src/operations/execution/firmware_policy web_portal/routes/firmware_policy -q` | Passed with no findings. |
| `radon cc src/operations/execution/firmware_policy web_portal/routes/firmware_policy -j \| complexity-gate --max 10` | All functions within threshold. |
| `pydocstyle src/operations/execution/firmware_policy web_portal/routes/firmware_policy` | Passed. |
| `interrogate src/operations/execution/firmware_policy web_portal/routes/firmware_policy --fail-under 90` | Passed at 100 percent. |
| `pylint src/operations/execution/firmware_policy web_portal/routes/firmware_policy --fail-under=9.5` | Passed at 9.91. Existing and advisory messages remain visible. |
| `node --check web_portal/static/js/firmware-policy.js` and `node --check web_portal/static/js/operations.js` | Passed. |
| `python -m py_compile MistHelper.py` | Passed without output. |
| `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Passed without findings. |
| `markdown-link-check README.md documentation/org-auto-upgrade-policy.md documentation/backup-restoration.md` | Three files examined. Zero broken links. |
| `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | Regenerated four affected API map pages. Menu reference pages did not change. |
| `pip-audit -r requirements.txt` | Blocked when its temporary `ensurepip` process aborted with SIGABRT. |
| `uv pip compile requirements.txt --python .venv/bin/python --quiet --output-file test-artifacts/issue4227-runtime-lock.txt` then `pip-audit --disable-pip --no-deps -r test-artifacts/issue4227-runtime-lock.txt` | Passed. No known runtime dependency vulnerabilities. |

The installed-environment audit found eight advisory entries for development-environment `pip 26.0.1`.
That package is not a runtime requirement. No dependency manifest changed.
The requirements-only alternative above resolves the complete runtime dependency graph before auditing its pinned versions.

An earlier direct mypy command against `web_portal/routes/operations.py` reported 42 inherited-style errors.
That legacy module is outside the configured CI mypy paths.
The configured type gate passed. No unrelated module rewrite was attempted.

The symbol comparison examined nine changed source files against released revision `7875309b`.
The six domain modules lost no module-level name.
New domain names implement admission, streaming, and backup proofs.
The two portal route modules intentionally remove the old expiring preview stores and their unused imports.
`PortalJobs` replaces `PolicyPreviewStore` and `RestorePreviews`; no compatibility alias remains.
These functional additions and removals return exit code 1 from `symbol-diff`, as expected.
The unchanged-name CLI and operations modules return exit code 0.

Additional execution-safety and structure checks passed 88 tests and skipped two with stated causes.
Source structure, destructive-menu, and SDK compatibility checks passed 27 tests.
SDK compatibility examined 559 call signatures and reported zero known signature failures.
The existing active-operation accent-border design finding is unrelated to the firmware integration and remains unchanged.

## Extension hooks

The YAML registered optional `speckit.git.commit` hooks before and after analysis.
Command: `/speckit-git-commit`. Description: auto-commit before analysis or commit analysis results.
These optional hooks were not executed automatically. The implementation milestone already exists.
No enabled mandatory analysis hook was registered. Disabled companion hooks were not executed.

## Guarded candidate

The parent requested a guarded candidate despite the unresolved actual-source schema acceptance.
This changes the artifact handoff sequence, not the required acceptance scope.
The candidate must refuse unsupported recovery before confirmation.
No speculative writes or schema suppression are permitted.

The public upstream schema at revision `79274e6cd85327ef51a9ab99a9c40a999d4b669a` adds no property-name vocabulary.
Its 3,133 property names already occur in the pinned public documents.
The remaining vendor evidence requirements appear in the restoration guide.

The post-discovery implementation adds checked schema composition and proven legacy fields.
Policy preparation projects all saved settings before creating confirmation.
Same-host workers use lifetime ownership locks, authenticated loopback routing, and shared organization write locks.
Unknown apply responses retain the known job identifier for status recovery without another POST.
Planning reads publish target counts. Unknown totals show an explicit working state.

| Command | Result |
| - | - |
| `node --check web_portal/static/js/firmware-policy.js` | Passed. |
| `python -m pytest tests/e2e/web_portal/test_firmware_policy.py tests/e2e/web_portal/firmware_restore/test_restore_portal.py -q --no-cov` | 38 passed. |
| `python -m pytest tests/unit/firmware_policy tests/contract/firmware_policy tests/integration/firmware_policy tests/unit/firmware_policy_jobs tests/e2e/web_portal/test_firmware_jobs.py --cov=src/operations/execution/firmware_policy --cov=web_portal/routes/firmware_policy --cov-report=term:skip-covered --cov-fail-under=80 -q` | 272 passed. Coverage 91.30 percent. |
| `python -m pytest tests/guardrails -q --no-cov` | Initially 908 passed, three skipped, one failed. Two new blind handlers caused the failure. |
| `python -m pytest tests/guardrails -q --no-cov` after repair | 909 passed, three skipped. |
| `python -m ruff check .` | All checks passed. |
| `python -m black --check .` | 2431 files unchanged. |
| `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Success for 844 source files. |
| `bandit -c pyproject.toml -r src/operations/execution/firmware_policy web_portal/routes/firmware_policy -q` | Passed without findings. |
| `radon cc src/operations/execution/firmware_policy web_portal/routes/firmware_policy -j \| complexity-gate --max 10` | All functions within threshold. |
| `pydocstyle src/operations/execution/firmware_policy web_portal/routes/firmware_policy` | Passed. |
| `interrogate src/operations/execution/firmware_policy web_portal/routes/firmware_policy --fail-under 90` | Passed at 100 percent. |
| `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Passed without findings. |
| `pylint src/operations/execution/firmware_policy web_portal/routes/firmware_policy --fail-under=9.5` | Passed at 9.80. Advisory messages remain visible. |
| `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | No generated reference changes. Sixteen map pages unchanged. |
| `pip-audit --disable-pip --no-deps -r test-artifacts/issue4227-runtime-lock.txt` | Passed. No known vulnerabilities. |

The blind handlers now log safe exception types and action context.
The focused handler guard and owned job tests passed after repair.

The first combined post-lock run found six fixture failures among 310 tests.
The production SDK supplies `get_cloud()`, but the shared fixture lacked that method.
The fixture now supplies the same checked interface. No production cloud fallback was added.
The complete combined command above then passed 311 tests with 92.85 percent coverage.
Final Ruff, Black, configured mypy, and diff checks passed after this repair.
The schema supplement uses only the packaged OpenAPI 3.1 document.
A regression proves that no legacy-document dependency was introduced.

## Release acceptance gap

| ID | Requirement | Severity | Evidence | Required decision |
| - | - | - | - | - |
| R1 | FR-009, FR-011 and complete actual restoration | High | Both original and fresh 145-record private bundles fail strict writable projection. | Obtain the missing vendor contract and repeat actual-source acceptance. |

R1 is a release blocker, not permission to decrease the requested scope.
The guarded candidate preserves the rejected data and sends zero settings writes.
The draft pull request must keep its acceptance checklist incomplete.
The parent owns connected verification and the eventual merge decision.

## Next actions

Complete the committed test-quality check, rebase, create the pull request, and inspect its final checks.
Record connected acceptance separately. Do not merge, deploy, or enable automatic merge in this implementation session.
