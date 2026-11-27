# Privacy Checklist: Converter Privacy and Shared Portal Integration

**Purpose**: Check the privacy, secret, and logging controls of this integration.
**Feature**: [spec.md](../../spec.md)

## Design coverage

- [x] Responses hold no source text, no traceback, and no secret value. Covered by `test_error_bodies_hide_traceback_and_source` (contract `privacy-and-logs.md`).
- [x] Logs hold no source text, file name, template name, or secret value. Covered by `test_logs_omit_source_name_and_secret`.
- [x] The session holds SHA-256 digests only. Covered by `test_session_holds_digest_only`.
- [x] Unsupported items hold labels, not raw lines. Source: `conversion.py` lines 78 to 83. Covered by `test_error_bodies_hide_traceback_and_source` for the error path.
- [x] Debug stays off in the factory and the container path. Covered by `test_debug_off_in_real_factory` and `test_container_runner_forces_debug_false`.
- [x] The converter package imports no network or SDK module. Covered by `test_converter_package_imports_no_network_module`.
- [x] Tests use synthetic values. The secret comes from `monkeypatch`. Covered by the fixture in task T002.
- [x] Browser evidence goes to `test-artifacts/`, which Git ignores. Covered by `test_evidence_path_stays_under_test_artifacts`.
- [x] Browser storage stays empty. Source: `converter.js` shows no storage call (remote check R-11).

## Open items

- [ ] The owner sets the production policy for the shared `PORTAL_SECRET_KEY` fallback. Explained: decision D-9 is a human decision. This integration does not block on it.
- [ ] Storage exposure tests exist for each private folder. Explained: open until issue #4636 or #4643 writes private files. Task T014 owns the work.
