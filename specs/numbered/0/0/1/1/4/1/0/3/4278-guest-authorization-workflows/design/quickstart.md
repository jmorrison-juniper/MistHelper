# Quickstart: Guest authorization workflows

**Record**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

This guide gives the exact steps to reproduce the current state. It also gives the exact commands for each gate and each task. Run each command from the repository root. The repository path is read-only for the record author. Implementation work runs in a separate worktree.

## 1. Reproduce the Current State

1. Confirm the commit. The output must equal `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

   ```powershell
   git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" rev-parse HEAD
   ```

2. Confirm that no navigation link exists. The output must be empty.

   ```powershell
   Select-String -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\web_portal\templates\base.html" -Pattern "nav-guest-authorizations"
   ```

3. Confirm that no guest package exists. The command prints `False`.

   ```powershell
   Test-Path -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\interfaces\portals\guest_authorizations"
   ```

4. Confirm that the projection is the only guest code. The projection test must pass with 22 cases.

   ```powershell
   python -m pytest tests/unit/web_portal/test_guest_authorization_read_model.py
   ```

5. Confirm that the web portal route is absent. A request to `/guest-authorizations/` returns 404. The browser test in `T012` checks this state after the change.

## 2. Gate Checks Before Implementation

| Step | Task | Command | Expected result |
| --- | --- | --- | --- |
| 1 | T001 | `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py` | Tests pass after the PR 4208 handover |
| 2 | T002 | `ste-linter --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows\spec.md` | Score 80 or above |

## 3. Implementation Checks in Task Order

| Task | Command | Expected result |
| --- | --- | --- |
| T003 | `python -m pytest tests/unit/web_portal/guest_authorizations/test_domain.py` | 22 projection cases pass |
| T004 | `python -m pytest tests/unit/web_portal/guest_authorizations/test_domain.py` | Scope, confirmation, and identity cases pass |
| T005 | `python -m pytest tests/unit/web_portal/guest_authorizations/test_contract.py` | Contract cases pass |
| T006 | `python -m pytest tests/unit/web_portal/guest_authorizations/services/test_audit_store.py` | Audit cases pass |
| T007 | `python -m pytest tests/unit/web_portal/guest_authorizations/services/test_mutations.py` | Write cases pass |
| T008 | `python -m pytest tests/unit/web_portal/guest_authorizations/services/test_csv_import.py` | CSV cases pass |
| T009 | `python -m pytest tests/unit/web_portal/guest_authorizations/test_routes.py` | Route cases pass |
| T010 | `python -m pytest tests/unit/web_portal/guest_authorizations/test_routes.py` | Blueprint registers once |
| T011 | `python -m pytest tests/e2e/web_portal/test_guest_authorization_portal.py` | Navigation link is visible |
| T012 | `python -m pytest tests/e2e/web_portal/test_guest_authorization_portal.py` | Browser cases pass |
| T013 | `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md` | Score 80 or above |
| T014 | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | Guard passes |
| T015 | `python -m pytest tests/guardrails/test_e2e_package_structure.py` | Guard passes |
| T016 | `python -m pytest tests/guardrails/test_move_module_guidance.py` | Guard passes |

## 4. Local Gates Before the Pull Request

Run each command from the local gates table in `.github/copilot-instructions.md`. The table is the authority. `$MYPY_PATHS` and `$VULTURE_PATHS` come from `.github/workflows/ci.yml` (lines 93 and 101).

| Gate | Command | Expected result |
| --- | --- | --- |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy $MYPY_PATHS --config-file pyproject.toml` | `Success` |
| Full tests | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Coverage at 80 percent or above |
| Complexity | `radon cc src/interfaces/portals/guest_authorizations -j \| complexity-gate --max 10` | No block above 10 |
| Security lint | `bandit -c pyproject.toml -r src/interfaces/portals/guest_authorizations -q` | No finding |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture $VULTURE_PATHS --min-confidence 70` | No finding |
| Docstrings | `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90` | No violation and coverage at 90 percent or above |
| Symbols | `symbol-diff --base origin/main web_portal/app.py` | `no module-level name changed` |
| Symbols | `symbol-diff --base origin/main src/interfaces/portals/guest_authorizations/domain/read_model.py` | `no module-level name changed` |
| Test quality | The test quality ratchet procedure in `.github/copilot-instructions.md` | `gate: 0 new findings vs baseline` |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md` | Score 80 or above |

Not applicable: the menu reference gate, because no menu changes. The safe sweep, because no menu operation changes. The dependency audit, because no dependency manifest changes.

## 5. Manual Browser Check After Implementation

1. Start the portal in the compose group. Follow `documentation/container-deployment.md` section "Test and debug containers" (line 141).
2. Open the portal page. The navigation shows the Guest authorizations link.
3. Without a trusted identity, the page shows a disabled state and no record.
4. Do not run a live write. Use the mocked test environment only.
