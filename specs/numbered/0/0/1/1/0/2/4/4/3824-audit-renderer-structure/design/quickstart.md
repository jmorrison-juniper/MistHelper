# Quickstart: Nested Source Package Remediation

Run these checks from the repository root after installing the development environment.

1. Run `python -m pytest tests/test_audit_renderer.py tests/unit/audit/test_renderer_format_wave9.py tests/unit/audit/test_renderer_time_wave9.py`.
2. Run `python -c "from src.mist.access.audit.rendering.renderer import AuditReportRenderer; print(AuditReportRenderer.__module__)"`. Expect `src.mist.access.audit.rendering.renderer`.
3. Run `python -m pytest tests/unit/websocket_streams/catalog/test_ws_utility_text.py tests/unit/websocket_streams/catalog/test_ws_utility_text_3890.py`.
4. Run `python -c "from src.mist.realtime.websocket_streams.catalog.utilities.utility_text import UtilityText; print(UtilityText.__module__)"`. Expect `src.mist.realtime.websocket_streams.catalog.utilities.utility_text`.
5. Run `python -m pytest tests/unit/audit/test_renderer_structure_issue_3824.py tests/unit/websocket_streams/catalog/test_ws_utility_text.py`. Expect every retired import path to fail.
6. Run `python -m pytest tests/guardrails/test_nested_package_structure.py`. Expect 33 violations and 236 total excess.

Run the import and structure checks with the quality gates in the implementation task list.
