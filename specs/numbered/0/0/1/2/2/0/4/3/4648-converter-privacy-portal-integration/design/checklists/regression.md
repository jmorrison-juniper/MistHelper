# Regression Checklist: Existing Portal Behavior

**Purpose**: Name the existing tests that prove the portal keeps its behavior.
**Feature**: [spec.md](../../spec.md)

## Existing tests and checks

- [x] Offline journey test: `tests/integration/web_portal/cisco_config_converter/test_routes.py`, function `test_complete_offline_journey` (line 60).
- [x] Existing upload compatibility test: `test_routes.py`, function `test_other_uploads_keep_flask_behavior` (line 194).
- [x] Existing health test class: `tests/e2e/web_portal/test_portal_smoke.py`, class `TestHealthEndpoint` (line 404).
- [x] Existing navigation checks: `tests/e2e/web_portal/test_portal_smoke.py` lines 105 to 109, which name the `nav-*` test IDs.
- [x] Existing isolated converter browser test: `tests/e2e/web_portal/test_portal_smoke.py`, class `TestCiscoOfflinePreview` (line 23). It stays unchanged in this issue.
- [x] Nested package guard: `tests/guardrails/test_nested_package_structure.py`.
- [x] Changelog fragment guard: `tests/guardrails/test_changelog_fragment_policy.py`.

## Regression run

- [ ] Pass counts before and after the integration match. Explained: pending. This draft ran no test. Task T012 records the counts in `analysis.md`.
- [ ] The regression run covers `tests/e2e/web_portal/test_portal_smoke.py` and `tests/integration/web_portal`. Explained: pending task T012.
- [x] Shared file edits stay within two lines in `web_portal/app.py` and one anchor in `web_portal/templates/base.html`. Source: tasks T009 and T010.
