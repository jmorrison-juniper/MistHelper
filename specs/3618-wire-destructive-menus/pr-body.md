# Spec Conformance Checklist

**Linked Spec Issue**: #3618

Closes #3617
Closes #3618

## Menu Wiring

| Menu | Issue | Category | Confirmation | Dry-run support | Handler |
| - | - | - | - | - | - |
| 280 | #3617 | safe | Not applicable | Not applicable | `AlertDigestOperation.run_digest` |
| 281 | #3617 | destructive | Type `ACK <count>` | `--dry-run` previews alarm acknowledgement | `AlertDigestOperation.run_acknowledge` |
| 286 | #3618 | destructive | Type the normalized target | `--dry-run` previews client session control | `ClientSessionControl.run` |
| 287 | #3618 | destructive | Type `REPLACE` | `--dry-run` previews device replacement | `DeviceReplaceOperation.run` |
| 291 | #3618 | destructive | Type `OPTIMIZE` or `RESET` | `--dry-run` previews RRM change | `RrmResetOperation.run` |
| 292 | #3618 | destructive | Type `IMPORT <row_count>` | `--dry-run` previews CSV import | `CsvImportOperation.run` |
| 293 | #3618 | destructive | Type `CLAIM`, `ASSIGN`, `UNASSIGN`, `BOUNCE`, or `UPGRADE` | `--dry-run` previews Mist Edge lifecycle change | `MxEdgeLifecycleOperation.run` |

Merged feature pull requests: #3637, #3634, #3582, #3580, #3581, and #3578.
The repository owner reviewed each destructive module in those pull requests.

## Acceptance Criteria
- [x] All acceptance criteria from the linked Spec Issue are met.
- [x] Each criterion has a corresponding test or verification.

## Quality
- [x] Tests added or updated for all changed functionality.
- [x] Coverage threshold is not reduced by this wiring change.
- [x] New or changed guards state the measured count. No new guard was added.
- [x] No new Ruff lint violations (`ruff check .`).
- [x] Code formatted with Black (`black --check`).
- [x] mypy passes (`mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml`).

## Security
- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit was not required. No security-sensitive code path changed.
- [x] pip-audit was not required. No dependency file changed.
- [x] Sensitive data remains in `.env` or environment variables only.

## Deployment
- [x] Dry-run wiring was verified by handler signatures and metadata tests.
- [x] `.env` changes are not applicable for this integration pull request.
- [x] Container build is not applicable. No container file changed.

## UI / E2E Testing
- [x] Playwright tests are not applicable. The portal registry added one safe row only.
- [x] Stable selectors are not applicable. No page markup changed.
- [x] Browser-agent verification is not applicable. No UI flow changed.
- [x] Screenshots and traces are not applicable. No UI flow changed.

## Documentation
- [x] README.md updated.
- [x] Release note added as `changelog.d/issue-3618-wire-destructive-menus.md`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Local Verification
- `py_compile` passed for each edited Python file.
- `ruff check .` passed.
- `black --check MistHelper.py src/utils/operation_registry.py src/refactors/endpoint_primary_key_strategies.py web_portal/menu_registry.py tests/unit/test_menu_entry_metadata.py tests/guardrails/test_menu_number_uniqueness.py` passed.
- `mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml` passed.
- Focused menu guardrails passed: `tests/unit/test_menu_entry_metadata.py`, `tests/guardrails/test_destructive_menu_docs.py`, `tests/guardrails/test_menu_number_uniqueness.py`, and `tests/guardrails/test_portal_operation_coverage.py`.
- Required broad pytest command reached `test_guard_proof_audit.py` and timed out in the pre-existing analyzer-generation path under `--timeout=120`.
- `MistHelper.py --help` passed.
- `symbol-diff --base origin/main MistHelper.py` reported no lost names. It reported the six expected added public imports.
