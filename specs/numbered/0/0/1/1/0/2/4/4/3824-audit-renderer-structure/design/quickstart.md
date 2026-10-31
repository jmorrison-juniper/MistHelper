# Quickstart: Audit Renderer Structure

Run these checks from the repository root after installing the development environment.

1. Run `python -m pytest tests/test_audit_renderer.py tests/unit/audit/test_renderer_format_wave9.py tests/unit/audit/test_renderer_time_wave9.py`.
2. Run `python -c "from src.mist.access.audit.rendering.renderer import AuditReportRenderer; print(AuditReportRenderer.__module__)"`. Expect `src.mist.access.audit.rendering.renderer`.
3. Run a failing import check for `src.mist.access.audit.renderer` and each removed `_renderer_*` module path.
4. Run `python -m pytest tests/guardrails/test_nested_package_structure.py`. Expect 179 directories examined, 34 violations, and 237 total excess.

Run the import and structure checks with the quality gates in the implementation task list.
