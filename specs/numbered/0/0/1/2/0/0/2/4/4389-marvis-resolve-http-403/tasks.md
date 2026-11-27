# Tasks: Marvis resolve HTTP 403 handling

**Input**: Numeric record `specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/contracts/resolve-refusal.md`.

**Format**: Each task names its requirements, exact paths, a parallel flag, an acceptance statement, one verification command, and a status. Status values are `open`, `verified-present`, `partial`, and `absent`.

**Base commit**: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Tests T002 to T006 and T015 fail or pass against this base as stated in each task.

## Phase 1: Evidence and tests

### T001. Verify the accepted-status rule

- **Parallel**: yes
- **Requirements**: FR-001
- **Files**: `src/mist/intelligence/marvis/actions/client.py` (lines 184 to 189 on remote `main`, blob `a7577ff0167e7462fb73adc39adc81036247cbdf`)
- **Depends on**: none
- **Acceptance**: The rule accepts HTTP 200 through 299 and refuses every other status. The rule is present on remote `main`.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_client.py`
- **Status**: verified-present

### T002. Add client tests for HTTP 401 and HTTP 403

- **Parallel**: no, same file as T003 and T007
- **Requirements**: FR-001, FR-010
- **Files**: `tests/unit/marvis/actions/test_client.py` (class `TestResolveRequest`, line 358)
- **Depends on**: T001
- **Acceptance**: Two parametrized cases, one for 401 and one for 403. Each case returns the status and the error text that starts with the status. Each case passes on the base commit, because the 2xx rule already holds. The cases guard the rule.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_client.py`
- **Status**: open

### T003. Add masking and length tests

- **Parallel**: no, same file as T002
- **Requirements**: FR-002, FR-003, FR-010
- **Files**: `tests/unit/marvis/actions/test_client.py` (class `TestResolveRequest`)
- **Depends on**: T001
- **Acceptance**: One masking test replaces a UUID with `<uuid>`, a value after `Token` with `<masked>`, and an email address with `<email>`. One test keeps the text at 300 characters or fewer and printable ASCII only. Both tests fail on the base commit.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_client.py`
- **Status**: open

### T004. Add the run-level stop test

- **Parallel**: yes
- **Requirements**: FR-004, FR-005, FR-010
- **Files**: `tests/unit/marvis/actions/test_operation.py` (class `TestResolve`, line 416)
- **Depends on**: none
- **Acceptance**: A parametrized test for 401 and 403. Three targets. The first PUT returns the refusal. The fake session receives exactly one PUT. Rows two and three hold outcome `not_sent` and the refusal message. The test fails on the base commit, because the base sends all three PUT requests.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_operation.py`
- **Status**: open

### T005. Add the refusal warning, no-verify, and no-acknowledge test

- **Parallel**: no, same file as T004 and T006
- **Requirements**: FR-006, FR-010
- **Files**: `tests/unit/marvis/actions/test_operation.py` (class `TestResolve`)
- **Depends on**: T004
- **Acceptance**: After one refusal, the log holds one WARNING line that names the status and the role check. The list read after the requests does not run. No `ACKNOWLEDGE` prompt appears.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_operation.py`
- **Status**: open

### T006. Add the regression test for accepted requests

- **Parallel**: no, same file as T004 and T005
- **Requirements**: FR-007, FR-008, FR-010
- **Files**: `tests/unit/marvis/actions/test_operation.py` (class `TestResolve`)
- **Depends on**: none
- **Acceptance**: Three targets with three HTTP 200 answers send three PUT requests and no stop occurs. The test passes on the base commit and after the change.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_operation.py`
- **Status**: open

### T007. Verify the existing refusal tests

- **Parallel**: yes
- **Requirements**: FR-008
- **Files**: `tests/unit/marvis/actions/test_client.py` (lines 381, 388, 397, 412 on remote blob `19b8ca17116d2f098c639623efef496670dfece1`), `tests/unit/marvis/actions/test_operation.py` (lines 594 and 667 on remote blob `be88636e3f63030d2dd73c8f10663e6fcacd7199`)
- **Depends on**: none
- **Acceptance**: The tests for HTTP 400, 503, 429, and 500 exist. Each test checks the status and the error text. The tests remain unchanged except for the masking rule.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_client.py`
- **Status**: verified-present

## Phase 2: Implementation and documents

### T008. Mask the refused error text

- **Parallel**: no, same file as T009
- **Requirements**: FR-002, FR-003
- **Files**: `src/mist/intelligence/marvis/actions/client.py` (`_error_text`, lines 305 to 310)
- **Depends on**: T003
- **Acceptance**: The function masks UUIDs, values after `Token` or `Bearer`, and email addresses before the 300-character cap. The mask patterns are class attributes. Every changed line has an inline comment. No module-level name is removed.
- **Verification**: Lint. `python -m ruff check .`
- **Status**: open

### T009. Add the stop rule and the refusal warning

- **Parallel**: no, same file as T008 and T014
- **Requirements**: FR-004, FR-005, FR-006
- **Files**: `src/mist/intelligence/marvis/actions/operation.py` (`MarvisBulkResolver.resolve`, lines 228 to 252, and `_send`, lines 277 to 292)
- **Depends on**: T004, T005
- **Acceptance**: `REFUSAL_STATUSES` holds 401 and 403 as a class attribute. After the first refusal, later rows receive the `not_sent` message from `design/contracts/resolve-refusal.md`. `_send` writes the WARNING line from the contract. The `resolve` function keeps five logical blocks or fewer.
- **Verification**: Complexity. `radon cc src/mist/intelligence/marvis/actions -j | complexity-gate --max 10`
- **Status**: open

### T010. Verify the request path, body, and confirmation

- **Parallel**: yes
- **Requirements**: FR-007
- **Files**: `src/mist/intelligence/marvis/actions/client.py` (lines 33 and 184), `src/mist/intelligence/marvis/actions/selection.py` (lines 401 to 415 and 504)
- **Depends on**: none
- **Acceptance**: The path, body fields, and typed confirmation match the remote blobs. The existing tests for the path and the body still pass.
- **Verification**: Tests. `python -m pytest tests/unit/marvis/actions/test_client.py`
- **Status**: verified-present

### T011. Update the endpoint report

- **Parallel**: yes
- **Requirements**: FR-009
- **Files**: `documentation/marvis-actions-api-endpoints.md` (section "Response of the resolve" at line 575, the `not_sent` row of the outcome table in "Verify each resolve", and section "Permissions" at line 634)
- **Depends on**: none
- **Acceptance**: The section states that the cause of HTTP 403 is unverified. It states the stop rule, the masking rule, and the role check. The statement "no live resolve request" is replaced with the 2026-10-21 evidence. The text contains the phrase "HTTP 401 or HTTP 403".
- **Verification**: STE. `ste-linter --config .ste-linter.toml --min-score 80 documentation/marvis-actions-api-endpoints.md`
- **Status**: open

### T012. Update the operator guide

- **Parallel**: yes
- **Requirements**: FR-009
- **Files**: `documentation/operator-guide.md` (menu 270 paragraph, lines 27 to 36)
- **Depends on**: none
- **Acceptance**: The paragraph about mode 3 states what happens after HTTP 401 or HTTP 403. It names the `not_sent` outcome. It contains the phrase "HTTP 401 or HTTP 403".
- **Verification**: STE. `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
- **Status**: open

### T013. Add the changelog fragment

- **Parallel**: yes
- **Requirements**: FR-011
- **Files**: `changelog.d/issue-4389-marvis-resolve-403.md` (new file. The naming rule is in `changelog.d/README.md` line 27.)
- **Depends on**: none
- **Acceptance**: The file name is `issue-4389-marvis-resolve-403.md`. It holds one heading and one bullet that names issue 4389. The text is STE compliant.
- **Verification**: Tests. `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

### T014. Check module-level names

- **Parallel**: no, same files as T008 and T009
- **Requirements**: FR-001 to FR-006
- **Files**: `src/mist/intelligence/marvis/actions/client.py`, `src/mist/intelligence/marvis/actions/operation.py`
- **Depends on**: T008, T009
- **Acceptance**: The symbol check removes no module-level name. Any added module-level name appears in the pull request body.
- **Verification**: Symbols. `symbol-diff --base origin/main src/mist/intelligence/marvis/actions/client.py`
- **Status**: open

### T015. Add the documentation drift guard

- **Parallel**: no, the test run follows T009, T011, and T012
- **Requirements**: FR-009, FR-010
- **Files**: `tests/guardrails/test_marvis_actions_portal_exposure.py`
- **Depends on**: T011, T012, T009
- **Acceptance**: One test reads both documents and asserts the phrase "HTTP 401 or HTTP 403". The same test imports `MarvisBulkResolver.REFUSAL_STATUSES` and asserts the values are 401 and 403. The test fails when a document or the constant drifts.
- **Verification**: Tests. `python -m pytest tests/guardrails/test_marvis_actions_portal_exposure.py`
- **Status**: open

## Phase 3: Final tasks

### T-LOCAL-GATES. Run the applicable local gates

- **Parallel**: no
- **Requirements**: SC-001 to SC-005
- **Files**: all changed files listed in `plan.md`
- **Depends on**: T002 to T015
- **Acceptance**: Each applicable gate reports the expected result in the table below. Each gate that does not apply has a reason in the pull request body.
- **Verification**: The commands below, run in order. The first failed command stops the run.

Run each command in a worktree with the bootstrap complete (`documentation/development-setup.md`, Step 2).

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile src/mist/intelligence/marvis/actions/client.py src/mist/intelligence/marvis/actions/operation.py` | No output. `MistHelper.py` does not change. |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Tests | `python -m pytest tests/unit/marvis/actions/test_client.py`, then `python -m pytest tests/unit/marvis/actions/test_operation.py`, then `python -m pytest tests/guardrails/test_marvis_actions_portal_exposure.py`, then `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | All tests pass |
| Full tests | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` and `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line for each shard |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | 80 percent or above |
| Test quality | `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`, then `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src/mist/intelligence/marvis/actions -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src/mist/intelligence/marvis/actions -q` | No finding at any severity |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding. The values of `VULTURE_PATHS` and `VULTURE_CONFIDENCE` are in `.github/workflows/ci.yml`. |
| Docstrings | `pydocstyle src/ wsgi.py web_portal`, then `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation. Coverage 90 percent or above. |
| Symbols | `symbol-diff --base origin/main src/mist/intelligence/marvis/actions/client.py`, then the same command for `operation.py` | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 documentation/marvis-actions-api-endpoints.md documentation/operator-guide.md changelog.d/issue-4389-marvis-resolve-403.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/spec.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/plan.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/tasks.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/analysis.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/design/research.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/design/data-model.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/design/quickstart.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/design/contracts/resolve-refusal.md specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/design/checklists/requirements.md src/mist/intelligence/marvis/actions/client.py src/mist/intelligence/marvis/actions/operation.py` | Each file scores 80 or above. The two Python files are graded as well, as `documentation/quality-gates.md` requires. |

Not applicable, with the reason in the pull request body:

- Safe sweep. `MistHelper.py` does not change, and no operation changes its category.
- Dependency audit. No manifest changes.
- Menu reference. No registry row or menu text changes.
- Ops portal and ops platform. No file under `ops-portal/` or `mist-ops-platform/` changes.

### T-PR. Commit, push, and open the pull request

- **Parallel**: no
- **Requirements**: FR-001 to FR-011
- **Files**: the files in `plan.md` and the record folder `specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/`
- **Depends on**: T-LOCAL-GATES
- **Acceptance**: The commit subject is `fix(marvis): stop a Marvis Actions resolve run after HTTP 403`. The body contains `Closes #4389`. The branch is `fix/4389-marvis-resolve-403`. The pull request title uses the same subject. The issue carries the labels `in-progress`, `bug`, and `MistHelper.py`. The pull request body lists each gate result and each skipped gate. No open pull request overlaps the changed files.
- **Verification**: GitHub check, because the local gates table has no remote step. `gh pr view <number> --json body` shows `Closes #4389`.
- **Status**: open

### T-REMOTE-CI. Watch the remote checks

- **Parallel**: no
- **Requirements**: FR-001 to FR-011
- **Files**: the pull request from T-PR
- **Depends on**: T-PR
- **Acceptance**: Each required check reports success on the latest commit. A failed check blocks the merge. Fix the cause on the same branch, then rerun the checks.
- **Verification**: GitHub check, because the local gates table has no remote step. `gh pr checks <number> --watch`
- **Status**: open

### T-MERGE. Merge after human review

- **Parallel**: no
- **Requirements**: SC-001 to SC-005
- **Files**: the pull request from T-PR
- **Depends on**: T-REMOTE-CI, human review
- **Acceptance**: A human reviewer clears the `needs-human-review` label. The orchestrator authorizes the merge. The `auto-merge` label is added only after both steps. The squash commit lands on `main`. The branch is removed.
- **Verification**: GitHub check, because the local gates table has no remote step. `gh pr view <number> --json state,mergedAt`
- **Status**: open
