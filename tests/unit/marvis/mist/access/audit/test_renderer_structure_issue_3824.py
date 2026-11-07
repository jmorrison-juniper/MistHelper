"""Verify the canonical renderer imports and reject removed module paths."""

import importlib  # WHY: resolve Python module paths without retaining aliases.

import pytest  # WHY: mark the retired imports as expected failures.

NEW_RENDERER_MODULES = (  # WHY: enumerate the canonical source modules moved by issue #3824.
    "src.mist.access.audit.rendering.renderer",  # WHY: renderer facade owns the public report class.
    "src.mist.access.audit.rendering._renderer_delta",  # WHY: delta helpers remain separate.
    "src.mist.access.audit.rendering._renderer_format",  # WHY: HTML value formatting remains separate.
    "src.mist.access.audit.rendering._renderer_time",  # WHY: timestamp formatting remains separate.
    "src.mist.access.audit.rendering.clusters._renderer_html",  # WHY: HTML cluster resides in its subpackage.
    "src.mist.access.audit.rendering.clusters._renderer_mermaid",  # WHY: Mermaid cluster resides in its subpackage.
)

LEGACY_RENDERER_MODULES = (  # WHY: prevent compatibility modules from hiding obsolete paths.
    "src.mist.access.audit.renderer",  # WHY: facade moved under rendering.
    "src.mist.access.audit._renderer_delta",  # WHY: delta helper moved under rendering.
    "src.mist.access.audit._renderer_format",  # WHY: format helper moved under rendering.
    "src.mist.access.audit._renderer_html",  # WHY: HTML cluster moved under rendering.clusters.
    "src.mist.access.audit._renderer_mermaid",  # WHY: Mermaid cluster moved under rendering.clusters.
    "src.mist.access.audit._renderer_time",  # WHY: time helper moved under rendering.
)


@pytest.mark.parametrize("module_name", NEW_RENDERER_MODULES)
def test_new_renderer_module_imports(module_name: str) -> None:
    """Resolve each renderer module from its canonical path."""
    imported_module = importlib.import_module(module_name)  # WHY: prove the intended import path exists.
    assert imported_module.__name__ == module_name  # WHY: reject a module that resolves through an alias.


def test_renderer_class_reports_its_canonical_module() -> None:
    """Keep the renderer class module identity aligned with its new path."""
    renderer_module = importlib.import_module(NEW_RENDERER_MODULES[0])  # WHY: load the canonical facade.
    renderer_class = renderer_module.AuditReportRenderer  # WHY: inspect the public renderer class.
    assert renderer_class.__module__ == NEW_RENDERER_MODULES[0]  # WHY: record the intentional identity change.


@pytest.mark.parametrize("module_name", LEGACY_RENDERER_MODULES)
def test_legacy_renderer_module_import_fails(module_name: str) -> None:
    """Reject each retired renderer import path."""
    with pytest.raises(ModuleNotFoundError):  # WHY: old paths must not resolve through wrappers.
        importlib.import_module(module_name)  # WHY: resolve the removed path and require failure.
