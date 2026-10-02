# Tasks: Multi-site model versions

- [x] Read issue #3204 and verify that no open pull request or branch claims it.
- [x] Trace the multi-site form, model validation, and aggregate child planner.
- [x] Add failing tests for explicit mixed-model version choices.
- [x] Add per-device version controls to the multi-site page.
- [x] Send and restore explicit device version choices.
- [x] Use explicit site plans when access point versions differ.
- [x] Add the release-note fragment.
- [x] Run the focused tests and quality gates.
- [ ] Commit, push, open the pull request, and merge when policy permits.

## Local integration tasks

- [X] Find each browser reference to the removed family-wide version controls.
- [X] Reuse a suitable shared helper or add one class-based per-device control helper.
- [X] Update the browser journeys to select and verify the real per-device controls.
- [X] Preserve empty-site, excluded-family, refusal, retry, restoration, and cancellation assertions.
- [ ] Run the full strict upgrade-portal browser suite and the changed-test quality gate.
- [X] Record the exact counts, capability skips, and static-check results before publication.

Local validation: the strict standard suite passed 318 cases and kept one existing capability skip.
The complete isolated journey run reported 21 passed, 8 xfailed, and 22 failed.
Compile, Ruff, and Black passed for 16 changed Python files.
The approved `ModelVersionPicker` passed mypy. The broader mypy run reported five errors in unchanged test functions.
The changed-test quality gate checked 15 modules and reported zero findings and zero new findings.
The full validation task remains open. No commit or publication occurred.
