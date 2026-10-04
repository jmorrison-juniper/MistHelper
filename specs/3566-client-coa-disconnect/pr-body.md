Closes #3566

## Summary

- Adds `src/mist/resources/device/client_session_control/` with `ClientSessionControl.run()`.
- Adds five supported client session control actions through the verified `mistapi` site-scoped endpoints.
- Adds exact normalized target confirmation, dry run preview, target normalization, and CSV audit logging.
- Adds no-network unit tests under `tests/unit/device/client_session_control/`.
- Adds `changelog.d/issue-3566-client-coa-disconnect.md`.

## Files changed

- `src/mist/resources/device/client_session_control/__init__.py`
- `src/mist/resources/device/client_session_control/actions.py`
- `src/mist/resources/device/client_session_control/audit.py`
- `src/mist/resources/device/client_session_control/handler.py`
- `src/mist/resources/device/client_session_control/models.py`
- `tests/unit/device/client_session_control/__init__.py`
- `tests/unit/device/client_session_control/test_client_session_control_confirmation.py`
- `tests/unit/device/client_session_control/test_client_session_control_dry_run.py`
- `tests/unit/device/client_session_control/test_client_session_control_log.py`
- `tests/unit/device/client_session_control/test_client_session_control_normalization.py`
- `tests/unit/device/client_session_control/test_client_session_control_wiring.py`
- `specs/3566-client-coa-disconnect/*`
- `specs/3566-client-coa-disconnect/contracts/client-session-control.md`
- `changelog.d/issue-3566-client-coa-disconnect.md`

## Destructive operation warning

Menu 286 is a destructive client session control operation.
Live use can reauthenticate, disconnect, unauthorize, or deauth clients.
The handler requires the operator to type the exact normalized target again before a live request.
`--dry-run` prints the request preview and sends no Mist request.

## Deferred wiring note

Repository wiring is intentionally deferred to the integration pull request.
This branch does not edit `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, README, menu documentation, web portal files, scripts, or guardrail tests.
The integration pull request must register menu 286, mark it destructive, exclude it from safe and fast automated tests, update menu documentation, and record primary-key strategy handling as not applicable or as required by review.

## Local gates

- `python -m py_compile src\mist\resources\device\client_session_control\__init__.py src\mist\resources\device\client_session_control\models.py src\mist\resources\device\client_session_control\actions.py src\mist\resources\device\client_session_control\audit.py src\mist\resources\device\client_session_control\handler.py`
- `python -m ruff check src\mist\resources\device\client_session_control tests\unit\device\client_session_control`
- `python -m black --check src\mist\resources\device\client_session_control tests\unit\device\client_session_control`
- `python -m mypy src\mist\resources\device\client_session_control --config-file pyproject.toml`
- `python -m pydocstyle src\mist\resources\device\client_session_control`
- `python -m pytest tests\unit\device\client_session_control -q --timeout=120`
- `python -m vulture src\mist\resources\device\client_session_control --min-confidence 70`
- `python -m interrogate -v src\mist\resources\device\client_session_control`

## Deployment and rollback

- Deployment requires the integration pull request to wire menu 286.
- Rollback is to remove the package, unit tests, release note, and wiring manifest changes from this branch.
