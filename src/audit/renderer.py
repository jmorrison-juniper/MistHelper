"""Report rendering for audit log analysis.

Generates two output formats:
1. Mermaid Markdown - vertical waterfall timeline + object changelogs
2. Interactive HTML - Plotly charts + collapsible JSON diffs

Rendering logic is split into cohesive cluster modules:
    * :mod:`src.audit._renderer_mermaid` - Mermaid markdown sections
    * :mod:`src.audit._renderer_html` - HTML document + fragments
    * :mod:`src.audit._renderer_format` - HTML delta formatter
    * :mod:`src.audit._renderer_delta` - shared delta / diff engine

The static methods bound below preserve the historical public surface
consumed by ``tests/test_audit_renderer.py``.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import os  # WHY: filesystem primitives for output-path handling
from typing import TYPE_CHECKING  # WHY: TYPE_CHECKING avoids runtime import cycle

from src.audit._renderer_delta import (  # WHY: shared delta engine bound to class for tests
    DiffKeyContext,
    build_identity_map,
    check_reorder,
    compute_delta,
    compute_delta_list,
    delta_by_identity,
    diff_anonymous,
    diff_identified,
    diff_key,
    element_identity,
    reorder_label,
    strip_id_prefix,
)
from src.audit._renderer_format import format_delta_html  # WHY: HTML formatter bound for tests
from src.audit._renderer_html import _HtmlCluster  # WHY: HTML rendering cluster
from src.audit._renderer_mermaid import _MermaidCluster  # WHY: Mermaid rendering cluster
from src.audit._renderer_time import epoch_to_readable, epoch_to_short  # WHY: shared timestamp formatters

if TYPE_CHECKING:  # WHY: only imported by type-checkers
    from src.audit.analyzer import AuditAnalysisResult  # WHY: analysis payload type

__all__ = ["AuditReportRenderer", "DiffKeyContext"]  # WHY: public surface for callers


class AuditReportRenderer:  # WHY: thin facade wraps cluster modules + preserves test API
    """Render audit analysis results into Mermaid and HTML reports."""

    # WHY: bind cluster module functions as static methods to preserve the
    # AuditReportRenderer._method(...) test call surface without wrappers
    _compute_delta = staticmethod(compute_delta)  # WHY: shared dict-delta walker exposed for tests
    _compute_delta_list = staticmethod(compute_delta_list)  # WHY: list-delta walker exposed for tests
    _diff_key = staticmethod(diff_key)  # WHY: dispatch helper exposed for tests via DiffKeyContext
    _element_identity = staticmethod(element_identity)  # WHY: identity extractor exposed for tests
    _build_identity_map = staticmethod(build_identity_map)  # WHY: id-map builder exposed for tests
    _diff_identified = staticmethod(diff_identified)  # WHY: identified diff exposed for tests
    _diff_anonymous = staticmethod(diff_anonymous)  # WHY: anonymous diff exposed for tests
    _check_reorder = staticmethod(check_reorder)  # WHY: reorder detector exposed for tests
    _delta_by_identity = staticmethod(delta_by_identity)  # WHY: full flow exposed for tests
    _reorder_label = staticmethod(reorder_label)  # WHY: reorder label helper exposed for tests
    _strip_id_prefix = staticmethod(strip_id_prefix)  # WHY: id-prefix stripper exposed for tests
    _format_delta_html = staticmethod(format_delta_html)  # WHY: leaf HTML formatter exposed for tests
    _epoch_to_readable = staticmethod(epoch_to_readable)  # WHY: preserve _epoch_to_readable test surface
    _epoch_to_short = staticmethod(epoch_to_short)  # WHY: preserve _epoch_to_short test surface

    def __init__(self) -> None:  # WHY: constructs owned cluster instances
        """Instantiate the Mermaid and HTML clusters."""
        self._mermaid = _MermaidCluster()  # WHY: owns all Mermaid section rendering
        self._html = _HtmlCluster()  # WHY: owns full HTML document assembly

    def render_mermaid(
        self,
        analysis: AuditAnalysisResult,
        output_path: str,
    ) -> None:  # WHY: public entry point for Mermaid report generation
        """Generate the Mermaid markdown report at ``output_path``."""
        sections = [
            self._mermaid.header(analysis),  # WHY: title + summary block
            self._mermaid.admin_timeline(analysis),  # WHY: waterfall graph per admin
            self._mermaid.object_changelogs(analysis),  # WHY: per-object change tables
            self._mermaid.rollback_table(analysis),  # WHY: rollback summary + details
        ]
        content = "\n\n".join(sections)  # WHY: blank-line separated sections
        _write_report(output_path, content)  # WHY: shared file writer keeps this thin

    def render_html(
        self,
        analysis: AuditAnalysisResult,
        output_path: str,
    ) -> None:  # WHY: public entry point for HTML report generation
        """Generate the interactive HTML report at ``output_path``."""
        content = self._html.build(analysis)  # WHY: cluster owns full document assembly
        _write_report(output_path, content)  # WHY: shared file writer keeps this thin


def _write_report(output_path: str, content: str) -> None:  # WHY: shared writer keeps render_* methods thin
    """Write ``content`` to ``output_path``, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)  # WHY: mkdir -p semantics
    with open(output_path, "w", encoding="utf-8") as fh:  # WHY: UTF-8 safe for Mermaid + HTML
        fh.write(content)  # WHY: single-shot write avoids partial-file surprises
