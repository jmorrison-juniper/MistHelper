"""HTML rendering cluster for :mod:`src.audit.renderer`.

Owns the ``_build_html``, timeline JavaScript, and diff-section generators
that together produce the self-contained HTML audit report. Split out to
shrink the parent module and keep each rendering method within the
compliance budget.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import html  # WHY: escape user-supplied strings before embedding in HTML
import json  # WHY: serialize Plotly trace/layout dicts
from datetime import UTC, datetime  # WHY: ISO-format timestamps for Plotly x-axis
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids circular import at runtime

from src.audit._renderer_delta import compute_delta  # WHY: shared delta walker
from src.audit._renderer_format import format_delta_html  # WHY: reused leaf HTML formatter
from src.audit._renderer_time import epoch_to_readable  # WHY: shared timestamp formatter

if TYPE_CHECKING:  # WHY: only imported by type-checkers
    from src.audit.analyzer import AuditAnalysisResult  # WHY: analysis payload type

# WHY: Plotly marker palette; index cycles through admins for stable per-admin coloring
_TIMELINE_COLORS: tuple[str, ...] = (  # WHY: module constant so palette is shared across trace builds
    "#00d4ff",
    "#ff6b6b",
    "#50fa7b",
    "#ffb86c",
    "#bd93f9",
    "#ff79c6",
    "#8be9fd",
    "#f1fa8c",
)


class _HtmlCluster:  # WHY: private cluster owned by AuditReportRenderer, not part of public API
    """Render the interactive HTML audit report for an analysis result."""

    def build(self, analysis: AuditAnalysisResult) -> str:  # WHY: sole public entry point for the cluster
        """Build the self-contained HTML report."""
        parts = _HtmlParts(  # WHY: bundle rendered fragments so template kwargs stay <=5
            timeline_data=self.timeline_data(analysis),
            diffs=self.diffs(analysis),
            user_diffs=self.user_diffs(analysis),
            rollback=self.rollback_table(analysis),
            squashed=self.squashed_diffs(analysis),
        )
        return _render_html_document(analysis, parts)  # WHY: pure template renderer keeps this thin

    def timeline_data(self, analysis: AuditAnalysisResult) -> str:  # WHY: emits Plotly script for template
        """Generate the Plotly timeline chart JavaScript block."""
        traces = [
            _build_timeline_trace(idx, timeline)  # WHY: one Plotly trace per admin
            for idx, timeline in enumerate(analysis.admin_timelines)
        ]
        layout = _default_timeline_layout()  # WHY: static layout keeps this function tiny
        return (  # WHY: three-line JS block instantiating the Plotly chart
            f"var traces = {json.dumps(traces)};\n"
            f"var layout = {json.dumps(layout)};\n"
            f"Plotly.newPlot('timeline', traces, layout);"
        )

    def diffs(self, analysis: AuditAnalysisResult) -> str:  # WHY: object-scoped diff sections
        """Generate collapsible diff sections for each object changelog."""
        parts = [
            self._render_object_diff_section(changelog)  # WHY: per-object <details> block
            for changelog in analysis.object_changelogs
        ]
        return "\n".join(parts)  # WHY: newline-join keeps HTML readable in source view

    def _render_object_diff_section(self, changelog: Any) -> str:  # WHY: single-object <details> renderer
        """Render one ``<details>`` block for a single object changelog."""
        changes_html = [self._render_change_entry(change) for change in changelog.changes]  # WHY: per-change fragments
        inner = "\n".join(changes_html)  # WHY: join per-change fragments inside the details block
        return (  # WHY: assemble the <details> block wrapping this object's changes
            f"<details>"
            f"<summary>{html.escape(changelog.object_type)}: "
            f"{html.escape(changelog.object_name)} "
            f"({len(changelog.changes)} changes)</summary>"
            f"{inner}</details>"
        )

    def _render_change_entry(self, change: Any) -> str:  # WHY: renders one <p> + optional delta block
        """Render a single change as a ``<p>`` header plus optional delta block."""
        time_str = epoch_to_readable(change.timestamp)  # WHY: shared formatter, module-level import
        header = (  # WHY: single <p> header identifies the change author + summary
            f"<p><strong>{time_str}</strong> - "
            f"{html.escape(change.admin_name)}: "
            f"{html.escape(change.message[:100])}</p>"
        )
        delta_block = _render_delta_block(change.before, change.after)  # WHY: '' when no delta present
        return header + delta_block  # WHY: concatenate header and delta fragments

    def squashed_diffs(self, analysis: AuditAnalysisResult) -> str:  # WHY: net-change section entry point
        """Generate the full starting-vs-ending config block per object."""
        parts = _collect_squashed_blocks(analysis)  # WHY: helper keeps this method CC<=5
        if not parts:  # WHY: friendlier empty-state message
            return "<p>No net changes detected across the time range.</p>"  # WHY: readable empty-state marker
        return "\n".join(parts)  # WHY: join collected blocks into final HTML section

    def user_diffs(self, analysis: AuditAnalysisResult) -> str:  # WHY: admin-scoped section entry point
        """Generate collapsible diff sections grouped by admin."""
        user_changes = _group_changes_by_admin(analysis)  # WHY: reshape by admin_name key
        parts = [
            self._render_admin_diff_section(admin_name, user_changes[admin_name])  # WHY: per-admin <details>
            for admin_name in sorted(user_changes.keys())  # WHY: deterministic admin order
        ]
        return "\n".join(parts)  # WHY: join admin sections for the final HTML block

    def _render_admin_diff_section(
        self,
        admin_name: str,
        changes: list[tuple[str, str, Any]],
    ) -> str:  # WHY: one admin -> one <details> block
        """Render a ``<details>`` block for one admin's aggregated changes."""
        changes_html = [self._render_admin_change_entry(entry) for entry in changes]  # WHY: per-change rows
        inner = "\n".join(changes_html)  # WHY: join per-change fragments
        return (  # WHY: wrap admin fragments in a single <details> block
            f"<details>"
            f"<summary>{html.escape(admin_name)} "
            f"({len(changes)} changes)</summary>"
            f"{inner}</details>"
        )

    def _render_admin_change_entry(self, entry: tuple[str, str, Any]) -> str:  # WHY: per-row admin renderer
        """Render one (obj_type, obj_name, change) row inside the admin block."""
        obj_type, obj_name, change = entry  # WHY: unpack tuple for readability
        time_str = epoch_to_readable(change.timestamp)  # WHY: shared formatter, module-level import
        header = (  # WHY: assemble the <p> header identifying object+admin+summary
            f"<p><strong>{time_str}</strong> - "
            f"{html.escape(obj_type)}: "
            f"{html.escape(obj_name)} - "
            f"{html.escape(change.message[:100])}</p>"
        )
        delta_block = _render_delta_block(change.before, change.after)  # WHY: '' when no delta present
        return header + delta_block  # WHY: concatenate header and optional delta

    def rollback_table(self, analysis: AuditAnalysisResult) -> str:  # WHY: public entry point for rollback HTML table
        """Generate the HTML rollback summary table."""
        if not analysis.rollback_diffs:  # WHY: early return matches the mermaid variant
            return "<p>No net changes detected.</p>"  # WHY: friendly empty-state marker for the report
        rows = [_render_rollback_row(diff) for diff in analysis.rollback_diffs]  # WHY: one <tr> per diff
        return (  # WHY: wrap generated <tr> rows in a full <table>
            "<table><thead><tr>"
            "<th>Object</th><th>Type</th><th>Fields Changed</th>"
            "</tr></thead><tbody>" + "\n".join(rows) + "</tbody></table>"
        )


class _HtmlParts:  # WHY: bundle template kwargs so build() call stays under 5-param limit
    """Bundle rendered HTML fragments passed into the document template.

    Kept as a plain class (not a dataclass) to avoid adding dependencies;
    frozen semantics are unnecessary because instances are short-lived.
    """

    def __init__(  # WHY: struct-style ctor keeps template kwargs bundled in one object
        self,
        timeline_data: str,
        diffs: str,
        user_diffs: str,
        rollback: str,
        squashed: str,
    ) -> None:
        """Store the five HTML fragments produced by the cluster."""
        self.timeline_data = timeline_data  # WHY: Plotly script for the timeline chart
        self.diffs = diffs  # WHY: object-scoped diff sections
        self.user_diffs = user_diffs  # WHY: admin-scoped diff sections
        self.rollback = rollback  # WHY: rollback summary table
        self.squashed = squashed  # WHY: starting-vs-ending config blocks


def _render_html_document(analysis: AuditAnalysisResult, parts: _HtmlParts) -> str:  # WHY: pure template renderer
    """Return the final HTML document string built from ``parts``."""
    stats_block = _render_stats_block(analysis)  # WHY: 4-card summary grid
    sections = _render_body_sections(analysis, parts)  # WHY: rollback + collapsibles + timeline script
    return (  # WHY: concatenate prefix, stats, sections, and suffix into final document
        _HTML_DOC_PREFIX
        + "<h1>Org Audit Log Analysis</h1>\n"
        + f"<p><strong>Time Range:</strong> {html.escape(analysis.time_range_description)}</p>\n\n"
        + stats_block
        + sections
        + _HTML_DOC_SUFFIX
    )


def _render_stats_block(analysis: AuditAnalysisResult) -> str:  # WHY: emits the 4-card summary grid
    """Return the 4-card summary stats grid HTML."""
    return (  # WHY: static grid HTML with 4 stat-card <div>s interpolated
        '<div class="stats">\n'
        f'<div class="stat-card"><div class="value">{analysis.filtered_entries}</div>\n'
        '<div class="label">Events Analyzed</div></div>\n'
        f'<div class="stat-card"><div class="value">{len(analysis.admin_timelines)}</div>\n'
        '<div class="label">Admins Active</div></div>\n'
        f'<div class="stat-card"><div class="value">{len(analysis.object_changelogs)}</div>\n'
        '<div class="label">Objects Modified</div></div>\n'
        f'<div class="stat-card"><div class="value">{len(analysis.rollback_diffs)}</div>\n'
        '<div class="label">Net Changes</div></div>\n'
        "</div>\n\n"
    )


def _render_body_sections(analysis: AuditAnalysisResult, parts: _HtmlParts) -> str:  # WHY: assembles body HTML
    """Return the body block covering timeline, rollback, and collapsibles."""
    return (  # WHY: multi-line f-string composes timeline + rollback + collapsibles
        "<h2>Activity Timeline</h2>\n"
        '<div id="timeline"></div>\n\n'
        "<h2>Rollback Summary</h2>\n"
        f"{parts.rollback}\n\n"
        f'<details class="section-toggle" open>\n'
        f"<summary>Net Change Per Object ({len(analysis.rollback_diffs)} objects with changes)"
        f"</summary>\n"
        f"{parts.squashed}\n"
        "</details>\n\n"
        f'<details class="section-toggle">\n'
        f"<summary>Object Change Details ({len(analysis.object_changelogs)} objects)</summary>\n"
        f"{parts.diffs}\n"
        "</details>\n\n"
        f'<details class="section-toggle">\n'
        f"<summary>User Change Details ({len(analysis.admin_timelines)} users)</summary>\n"
        f"{parts.user_diffs}\n"
        "</details>\n\n"
        "<script>\n"
        f"{parts.timeline_data}\n"
        "</script>\n"
    )


def _build_timeline_trace(idx: int, timeline: Any) -> dict[str, Any]:  # WHY: emits one Plotly trace per admin
    """Build a single Plotly trace dict for one admin's timeline."""
    timestamps: list[str] = []  # WHY: ISO-formatted x values
    messages: list[str] = []  # WHY: hover-text list aligned with timestamps
    for entry in timeline.entries:  # WHY: entries are already sorted by timestamp upstream
        ts = entry.get("timestamp", 0)  # WHY: default 0 makes epoch conversion safe
        timestamps.append(datetime.fromtimestamp(ts, tz=UTC).isoformat())  # WHY: Plotly expects ISO strings
        messages.append(entry.get("message", "")[:100])  # WHY: cap for hover legibility
    color = _TIMELINE_COLORS[idx % len(_TIMELINE_COLORS)]  # WHY: cycle palette for many admins
    return {  # WHY: Plotly scatter-trace dict consumed by the template JS
        "x": timestamps,
        "y": [timeline.admin_name] * len(timestamps),
        "text": messages,
        "mode": "markers",
        "type": "scatter",
        "name": timeline.admin_name,
        "marker": {"size": 8, "color": color},
        "hovertemplate": "%{text}<br>%{x}<extra></extra>",
    }


def _default_timeline_layout() -> dict[str, Any]:  # WHY: static layout kept out of trace loop
    """Return the static Plotly layout for the timeline chart."""
    return {  # WHY: static Plotly layout applied to the timeline chart
        "title": "Admin Activity Over Time",
        "xaxis": {"title": "Time (UTC)"},
        "yaxis": {"title": ""},
        "plot_bgcolor": "#1a1a2e",
        "paper_bgcolor": "#1a1a2e",
        "font": {"color": "#e0e0e0"},
        "showlegend": True,
        "height": 400,
    }


def _render_delta_block(before: dict[str, Any], after: dict[str, Any]) -> str:  # WHY: shared delta HTML wrapper
    """Return the HTML ``<details>`` block for one before/after delta or ''."""
    delta_before, delta_after = compute_delta(before, after)  # WHY: reuse shared walker
    if not (before or after) or not (delta_before or delta_after):  # WHY: skip empty deltas
        return ""  # WHY: empty string keeps caller concatenation trivial when no delta
    before_html = format_delta_html(delta_before)  # WHY: pretty-print before side
    after_html = format_delta_html(delta_after)  # WHY: pretty-print after side
    return (  # WHY: multi-line f-string wraps before/after in a <details> block
        f"<details><summary>Delta (changed fields only)</summary>"
        f"<div class='diff-row'>"
        f"<div class='diff-col before'><h4>Before</h4>"
        f"<pre>{before_html}</pre></div>"
        f"<div class='diff-col after'><h4>After</h4>"
        f"<pre>{after_html}</pre></div>"
        f"</div></details>"
    )


def _render_squashed_block(diff: Any) -> str:  # WHY: emits one starting-vs-ending config block
    """Return the starting-vs-ending config HTML block for one rollback diff."""
    delta_b, delta_a = compute_delta(diff.original_state, diff.final_state)  # WHY: shared walker
    if not delta_b and not delta_a:  # WHY: caller filters out empty deltas
        return ""
    before_html = format_delta_html(delta_b)  # WHY: pretty-print starting side
    after_html = format_delta_html(delta_a)  # WHY: pretty-print ending side
    return (
        f"<details>"
        f"<summary>{html.escape(diff.object_type)}: "
        f"{html.escape(diff.object_name)} "
        f"({len(diff.fields_changed)} fields changed)</summary>"
        f"<div class='diff-row'>"
        f"<div class='diff-col before'><h4>Starting Config</h4>"
        f"<pre>{before_html}</pre></div>"
        f"<div class='diff-col after'><h4>Ending Config</h4>"
        f"<pre>{after_html}</pre></div>"
        f"</div></details>"
    )


def _collect_squashed_blocks(analysis: AuditAnalysisResult) -> list[str]:
    """Return the non-empty starting-vs-ending config blocks for net-changed diffs."""
    blocks: list[str] = []  # WHY: accumulator keeps caller's comprehension shallow
    for diff in analysis.rollback_diffs:  # WHY: iterate every rollback candidate
        if not diff.net_changed:  # WHY: skip objects that returned to original state
            continue
        rendered = _render_squashed_block(diff)  # WHY: helper returns '' when delta collapses
        if rendered:  # WHY: filter out empty deltas before joining
            blocks.append(rendered)
    return blocks


def _render_rollback_row(diff: Any) -> str:
    """Return one ``<tr>`` for the rollback summary table."""
    fields = ", ".join(diff.fields_changed[:5])  # WHY: cap for legibility
    if len(diff.fields_changed) > 5:  # WHY: signal truncation to the reader
        fields += f" (+{len(diff.fields_changed) - 5} more)"
    return (
        f"<tr><td>{html.escape(diff.object_name)}</td>"
        f"<td>{html.escape(diff.object_type)}</td>"
        f"<td class='changed'>{html.escape(fields)}</td></tr>"
    )


def _group_changes_by_admin(
    analysis: AuditAnalysisResult,
) -> dict[str, list[tuple[str, str, Any]]]:
    """Build ``admin -> [(obj_type, obj_name, change)]`` sorted by time."""
    user_changes: dict[str, list[tuple[str, str, Any]]] = {}
    for changelog in analysis.object_changelogs:  # WHY: flatten changelogs into per-admin rows
        for change in changelog.changes:
            user_changes.setdefault(change.admin_name, []).append(
                (changelog.object_type, changelog.object_name, change)
            )
    for admin in user_changes:  # WHY: chronological order per admin
        user_changes[admin].sort(key=lambda row: row[2].timestamp)
    return user_changes


# WHY: extracted document head/body prelude to keep _render_html_document short
_HTML_DOC_PREFIX = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Org Audit Log Analysis</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
body { font-family: -apple-system, sans-serif; margin: 2rem; background: #1a1a2e; color: #e0e0e0; }
h1, h2, h3 { color: #00d4ff; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; }
.stat-card { background: #16213e; border-radius: 8px; padding: 1rem; border: 1px solid #0f3460; }
.stat-card .value { font-size: 2rem; font-weight: bold; color: #00d4ff; }
.stat-card .label { font-size: 0.9rem; color: #a0a0a0; }
#timeline { width: 100%; height: 500px; }
details { background: #16213e; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border: 1px solid #0f3460; }
summary { cursor: pointer; font-weight: bold; color: #00d4ff; }
details.section-toggle { background: transparent; border: none; padding: 0; }
details.section-toggle > summary { font-size: 1.3rem; padding: 0.5rem 0; }
pre { background: #0d1117; padding: 1rem; border-radius: 4px; overflow-x: auto; font-size: 0.85rem; }
.diff-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.diff-col h4 { margin: 0.3rem 0; color: #a0a0a0; font-size: 0.8rem; }
.diff-col.before h4 { color: #ff6b6b; }
.diff-col.after h4 { color: #50fa7b; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid #0f3460; padding: 0.5rem; text-align: left; }
th { background: #16213e; color: #00d4ff; }
tr:nth-child(even) { background: #1a1a2e; }
.changed { color: #ff6b6b; font-weight: bold; }
</style>
</head>
<body>
"""

# WHY: extracted document footer keeps _render_html_document short
_HTML_DOC_SUFFIX = """</body>
</html>"""
