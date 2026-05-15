"""Report rendering for audit log analysis.

Generates two output formats:
1. Mermaid Markdown - vertical waterfall timeline + object changelogs
2. Interactive HTML - Plotly charts + collapsible JSON diffs
"""

import html
import json
import os
from datetime import UTC, datetime
from typing import Any

from src.audit.analyzer import AuditAnalysisResult

MERMAID_NODE_CAP = 500


class AuditReportRenderer:
    """Render audit analysis results into Mermaid and HTML reports."""

    def render_mermaid(
        self,
        analysis: AuditAnalysisResult,
        output_path: str,
    ) -> None:
        """Generate Mermaid markdown report.

        Args:
            analysis: Complete analysis result.
            output_path: File path for output .md file.
        """
        sections = []
        sections.append(self._mermaid_header(analysis))
        sections.append(self._mermaid_admin_timeline(analysis))
        sections.append(self._mermaid_object_changelogs(analysis))
        sections.append(self._mermaid_rollback_table(analysis))

        content = "\n\n".join(sections)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def render_html(
        self,
        analysis: AuditAnalysisResult,
        output_path: str,
    ) -> None:
        """Generate interactive HTML report with Plotly.

        Args:
            analysis: Complete analysis result.
            output_path: File path for output .html file.
        """
        content = self._build_html(analysis)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _mermaid_header(self, analysis: AuditAnalysisResult) -> str:
        """Generate report header section."""
        return (
            f"# Org Audit Log Analysis\n\n"
            f"**Time Range**: {analysis.time_range_description}\n"
            f"**Total Entries (after filter)**: {analysis.filtered_entries}\n"
            f"**Admins Active**: {len(analysis.admin_timelines)}\n"
            f"**Objects Modified**: {len(analysis.object_changelogs)}\n"
            f"**Net Changes (rollback needed)**: {len(analysis.rollback_diffs)}\n"
        )

    def _mermaid_admin_timeline(self, analysis: AuditAnalysisResult) -> str:
        """Generate vertical admin timeline using Mermaid graph TD."""
        lines = ["## Admin Activity Timeline\n"]
        lines.append("```mermaid")
        lines.append("graph TD")

        node_count = 0
        for timeline in analysis.admin_timelines:
            safe_name = timeline.admin_name.replace(" ", "_").replace(".", "")
            lines.append(f'  subgraph {safe_name}["{timeline.admin_name}"]')

            entries_to_show = timeline.entries[:MERMAID_NODE_CAP]
            prev_node = None

            for entry in entries_to_show:
                if node_count >= MERMAID_NODE_CAP:
                    break
                ts = entry.get("timestamp", 0)
                msg = entry.get("message", "")[:60].replace('"', "'")
                time_str = self._epoch_to_short(ts)
                node_id = f"n{node_count}"
                lines.append(f'    {node_id}["{time_str}: {msg}"]')
                if prev_node:
                    lines.append(f"    {prev_node} --> {node_id}")
                prev_node = node_id
                node_count += 1

            lines.append("  end")

            if node_count >= MERMAID_NODE_CAP:
                lines.append(f"  %% Capped at {MERMAID_NODE_CAP} nodes")
                break

        lines.append("```")

        for timeline in analysis.admin_timelines:
            start = self._epoch_to_readable(timeline.first_action)
            end = self._epoch_to_readable(timeline.last_action)
            lines.append(f"- **{timeline.admin_name}**: {timeline.action_count} actions " f"({start} to {end})")

        return "\n".join(lines)

    def _mermaid_object_changelogs(self, analysis: AuditAnalysisResult) -> str:
        """Generate per-object changelog section."""
        lines = ["## Object Changelogs\n"]

        for changelog in analysis.object_changelogs[:MERMAID_NODE_CAP]:
            lines.append(f"### {changelog.object_type}: {changelog.object_name} " f"({len(changelog.changes)} changes)")
            lines.append("")
            lines.append("| Time | Admin | Action |")
            lines.append("| - | - | - |")

            for change in changelog.changes:
                time_str = self._epoch_to_readable(change.timestamp)
                msg_short = change.message[:80]
                lines.append(f"| {time_str} | {change.admin_name} | {msg_short} |")
            lines.append("")

        return "\n".join(lines)

    def _mermaid_rollback_table(self, analysis: AuditAnalysisResult) -> str:
        """Generate rollback diff summary table."""
        lines = ["## Rollback Summary (Objects with Net Changes)\n"]

        if not analysis.rollback_diffs:
            lines.append("No net changes detected - all objects returned to original state.")
            return "\n".join(lines)

        lines.append("| Object | Type | Fields Changed |")
        lines.append("| - | - | - |")

        for diff in analysis.rollback_diffs:
            fields = ", ".join(diff.fields_changed[:5])
            if len(diff.fields_changed) > 5:
                fields += f" (+{len(diff.fields_changed) - 5} more)"
            lines.append(f"| {diff.object_name} | {diff.object_type} | {fields} |")

        lines.append("")
        lines.append("### Detailed Diffs\n")

        for diff in analysis.rollback_diffs:
            delta_orig, delta_final = self._compute_delta(diff.original_state, diff.final_state)
            if not delta_orig and not delta_final:
                continue
            lines.append(f"<details><summary>{diff.object_type}: {diff.object_name}</summary>\n")
            lines.append("**Original (changed fields only):**")
            lines.append("```json")
            lines.append(json.dumps(delta_orig, indent=2, default=str)[:2000])
            lines.append("```")
            lines.append("**Final (changed fields only):**")
            lines.append("```json")
            lines.append(json.dumps(delta_final, indent=2, default=str)[:2000])
            lines.append("```")
            lines.append("</details>\n")

        return "\n".join(lines)

    def _build_html(self, analysis: AuditAnalysisResult) -> str:
        """Build self-contained HTML report."""
        timeline_data = self._html_timeline_data(analysis)
        diffs_html = self._html_diffs(analysis)
        user_diffs_html = self._html_user_diffs(analysis)
        rollback_html = self._html_rollback_table(analysis)
        squashed_html = self._html_squashed_diffs(analysis)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Org Audit Log Analysis</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 2rem; background: #1a1a2e; color: #e0e0e0; }}
h1, h2, h3 {{ color: #00d4ff; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; }}
.stat-card {{ background: #16213e; border-radius: 8px; padding: 1rem; border: 1px solid #0f3460; }}
.stat-card .value {{ font-size: 2rem; font-weight: bold; color: #00d4ff; }}
.stat-card .label {{ font-size: 0.9rem; color: #a0a0a0; }}
#timeline {{ width: 100%; height: 500px; }}
details {{ background: #16213e; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border: 1px solid #0f3460; }}
summary {{ cursor: pointer; font-weight: bold; color: #00d4ff; }}
details.section-toggle {{ background: transparent; border: none; padding: 0; }}
details.section-toggle > summary {{ font-size: 1.3rem; padding: 0.5rem 0; }}
pre {{ background: #0d1117; padding: 1rem; border-radius: 4px; overflow-x: auto; font-size: 0.85rem; }}
.diff-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }}
.diff-col h4 {{ margin: 0.3rem 0; color: #a0a0a0; font-size: 0.8rem; }}
.diff-col.before h4 {{ color: #ff6b6b; }}
.diff-col.after h4 {{ color: #50fa7b; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #0f3460; padding: 0.5rem; text-align: left; }}
th {{ background: #16213e; color: #00d4ff; }}
tr:nth-child(even) {{ background: #1a1a2e; }}
.changed {{ color: #ff6b6b; font-weight: bold; }}
</style>
</head>
<body>
<h1>Org Audit Log Analysis</h1>
<p><strong>Time Range:</strong> {html.escape(analysis.time_range_description)}</p>

<div class="stats">
<div class="stat-card"><div class="value">{analysis.filtered_entries}</div>
<div class="label">Events Analyzed</div></div>
<div class="stat-card"><div class="value">{len(analysis.admin_timelines)}</div>
<div class="label">Admins Active</div></div>
<div class="stat-card"><div class="value">{len(analysis.object_changelogs)}</div>
<div class="label">Objects Modified</div></div>
<div class="stat-card"><div class="value">{len(analysis.rollback_diffs)}</div>
<div class="label">Net Changes</div></div>
</div>

<h2>Activity Timeline</h2>
<div id="timeline"></div>

<h2>Rollback Summary</h2>
{rollback_html}

<details class="section-toggle" open>
<summary>Net Change Per Object ({len(analysis.rollback_diffs)} objects with changes)</summary>
{squashed_html}
</details>

<details class="section-toggle">
<summary>Object Change Details ({len(analysis.object_changelogs)} objects)</summary>
{diffs_html}
</details>

<details class="section-toggle">
<summary>User Change Details ({len(analysis.admin_timelines)} users)</summary>
{user_diffs_html}
</details>

<script>
{timeline_data}
</script>
</body>
</html>"""

    def _html_timeline_data(self, analysis: AuditAnalysisResult) -> str:
        """Generate Plotly timeline chart JavaScript."""
        traces = []
        colors = [
            "#00d4ff",
            "#ff6b6b",
            "#50fa7b",
            "#ffb86c",
            "#bd93f9",
            "#ff79c6",
            "#8be9fd",
            "#f1fa8c",
        ]

        for idx, timeline in enumerate(analysis.admin_timelines):
            timestamps = []
            messages = []
            for entry in timeline.entries:
                ts = entry.get("timestamp", 0)
                timestamps.append(datetime.fromtimestamp(ts, tz=UTC).isoformat())
                messages.append(entry.get("message", "")[:100])

            color = colors[idx % len(colors)]
            trace = {
                "x": timestamps,
                "y": [timeline.admin_name] * len(timestamps),
                "text": messages,
                "mode": "markers",
                "type": "scatter",
                "name": timeline.admin_name,
                "marker": {"size": 8, "color": color},
                "hovertemplate": "%{text}<br>%{x}<extra></extra>",
            }
            traces.append(trace)

        layout = {
            "title": "Admin Activity Over Time",
            "xaxis": {"title": "Time (UTC)"},
            "yaxis": {"title": ""},
            "plot_bgcolor": "#1a1a2e",
            "paper_bgcolor": "#1a1a2e",
            "font": {"color": "#e0e0e0"},
            "showlegend": True,
            "height": 400,
        }

        return (
            f"var traces = {json.dumps(traces)};\n"
            f"var layout = {json.dumps(layout)};\n"
            f"Plotly.newPlot('timeline', traces, layout);"
        )

    def _html_diffs(self, analysis: AuditAnalysisResult) -> str:
        """Generate collapsible diff sections for each object."""
        parts = []

        for changelog in analysis.object_changelogs:
            changes_html = []
            for change in changelog.changes:
                time_str = self._epoch_to_readable(change.timestamp)
                delta_before, delta_after = self._compute_delta(change.before, change.after)
                before_html = self._format_delta_html(delta_before)
                after_html = self._format_delta_html(delta_after)

                changes_html.append(
                    f"<p><strong>{time_str}</strong> - "
                    f"{html.escape(change.admin_name)}: "
                    f"{html.escape(change.message[:100])}</p>"
                )
                has_delta = delta_before or delta_after
                if (change.before or change.after) and has_delta:
                    changes_html.append(
                        f"<details><summary>Delta (changed fields only)</summary>"
                        f"<div class='diff-row'>"
                        f"<div class='diff-col before'><h4>Before</h4>"
                        f"<pre>{before_html}</pre></div>"
                        f"<div class='diff-col after'><h4>After</h4>"
                        f"<pre>{after_html}</pre></div>"
                        f"</div></details>"
                    )

            inner = "\n".join(changes_html)
            parts.append(
                f"<details>"
                f"<summary>{html.escape(changelog.object_type)}: "
                f"{html.escape(changelog.object_name)} "
                f"({len(changelog.changes)} changes)</summary>"
                f"{inner}</details>"
            )

        return "\n".join(parts)

    def _html_squashed_diffs(self, analysis: AuditAnalysisResult) -> str:
        """Generate full starting vs ending config per object."""
        parts = []

        for diff in analysis.rollback_diffs:
            if not diff.net_changed:
                continue

            delta_b, delta_a = self._compute_delta(diff.original_state, diff.final_state)
            if not delta_b and not delta_a:
                continue

            before_html = self._format_delta_html(delta_b)
            after_html = self._format_delta_html(delta_a)

            parts.append(
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

        if not parts:
            return "<p>No net changes detected across the time range.</p>"
        return "\n".join(parts)

    def _html_user_diffs(self, analysis: AuditAnalysisResult) -> str:
        """Generate collapsible diff sections grouped by admin."""
        user_changes = self._group_changes_by_admin(analysis)
        parts = []

        for admin_name in sorted(user_changes.keys()):
            changes = user_changes[admin_name]
            changes_html = []
            for obj_type, obj_name, change in changes:
                time_str = self._epoch_to_readable(change.timestamp)
                delta_before, delta_after = self._compute_delta(change.before, change.after)
                before_html = self._format_delta_html(delta_before)
                after_html = self._format_delta_html(delta_after)

                changes_html.append(
                    f"<p><strong>{time_str}</strong> - "
                    f"{html.escape(obj_type)}: "
                    f"{html.escape(obj_name)} - "
                    f"{html.escape(change.message[:100])}</p>"
                )
                has_delta = delta_before or delta_after
                if (change.before or change.after) and has_delta:
                    changes_html.append(
                        f"<details><summary>Delta (changed fields only)</summary>"
                        f"<div class='diff-row'>"
                        f"<div class='diff-col before'><h4>Before</h4>"
                        f"<pre>{before_html}</pre></div>"
                        f"<div class='diff-col after'><h4>After</h4>"
                        f"<pre>{after_html}</pre></div>"
                        f"</div></details>"
                    )

            inner = "\n".join(changes_html)
            parts.append(
                f"<details>"
                f"<summary>{html.escape(admin_name)} "
                f"({len(changes)} changes)</summary>"
                f"{inner}</details>"
            )

        return "\n".join(parts)

    @staticmethod
    def _group_changes_by_admin(
        analysis: AuditAnalysisResult,
    ) -> dict[str, list[tuple[str, str, Any]]]:
        """Build admin -> [(obj_type, obj_name, change)] sorted by time."""
        user_changes: dict[str, list[tuple[str, str, Any]]] = {}

        for changelog in analysis.object_changelogs:
            for change in changelog.changes:
                admin = change.admin_name
                if admin not in user_changes:
                    user_changes[admin] = []
                user_changes[admin].append((changelog.object_type, changelog.object_name, change))

        for admin in user_changes:
            user_changes[admin].sort(key=lambda x: x[2].timestamp)

        return user_changes

    def _html_rollback_table(self, analysis: AuditAnalysisResult) -> str:
        """Generate HTML rollback summary table."""
        if not analysis.rollback_diffs:
            return "<p>No net changes detected.</p>"

        rows = []
        for diff in analysis.rollback_diffs:
            fields = ", ".join(diff.fields_changed[:5])
            if len(diff.fields_changed) > 5:
                fields += f" (+{len(diff.fields_changed) - 5} more)"
            rows.append(
                f"<tr><td>{html.escape(diff.object_name)}</td>"
                f"<td>{html.escape(diff.object_type)}</td>"
                f"<td class='changed'>{html.escape(fields)}</td></tr>"
            )

        return (
            "<table><thead><tr>"
            "<th>Object</th><th>Type</th><th>Fields Changed</th>"
            "</tr></thead><tbody>" + "\n".join(rows) + "</tbody></table>"
        )

    @staticmethod
    def _format_delta_html(obj: object, indent: int = 0) -> str:
        """Render a delta object as HTML with bold leaf values.

        Structure keys are rendered normally; leaf values (the actual
        changed data) are wrapped in <b> tags.
        """
        pad = "  " * indent
        inner_pad = "  " * (indent + 1)

        if isinstance(obj, dict):
            if not obj:
                return "{}"
            lines = ["{"]
            items = list(obj.items())
            for idx, (key, val) in enumerate(items):
                comma = "," if idx < len(items) - 1 else ""
                rendered = AuditReportRenderer._format_delta_html(val, indent + 1)
                safe_key = html.escape(json.dumps(key))
                lines.append(f"{inner_pad}{safe_key}: {rendered}{comma}")
            lines.append(f"{pad}}}")
            return "\n".join(lines)

        if isinstance(obj, list):
            if not obj:
                return "[]"
            lines = ["["]
            for idx, item in enumerate(obj):
                comma = "," if idx < len(obj) - 1 else ""
                rendered = AuditReportRenderer._format_delta_html(item, indent + 1)
                lines.append(f"{inner_pad}{rendered}{comma}")
            lines.append(f"{pad}]")
            return "\n".join(lines)

        safe_val = html.escape(json.dumps(obj, default=str))
        return f"<b>{safe_val}</b>"

    @staticmethod
    def _compute_delta(before: dict[str, Any], after: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Extract only the fields that differ between before and after.

        Returns:
            Tuple of (delta_before, delta_after) containing only
            the differing branches.
        """
        if not before and not after:
            return {}, {}
        if not before:
            return {}, after
        if not after:
            return before, {}

        delta_b: dict[str, Any] = {}
        delta_a: dict[str, Any] = {}
        all_keys = set(list(before.keys()) + list(after.keys()))

        for key in sorted(all_keys):
            val_b = before.get(key)
            val_a = after.get(key)
            if val_b == val_a:
                continue
            AuditReportRenderer._diff_key(
                key,
                val_b,
                val_a,
                before,
                after,
                delta_b,
                delta_a,
            )

        return delta_b, delta_a

    @staticmethod
    def _diff_key(
        key: str,
        val_b: object,
        val_a: object,
        before: dict[str, Any],
        after: dict[str, Any],
        delta_b: dict[str, Any],
        delta_a: dict[str, Any],
    ) -> None:
        """Diff a single key's values and update delta dicts in place."""
        if isinstance(val_b, dict) and isinstance(val_a, dict):
            AuditReportRenderer._diff_key_dict(
                key,
                val_b,
                val_a,
                delta_b,
                delta_a,
            )
        elif isinstance(val_b, list) and isinstance(val_a, list):
            AuditReportRenderer._diff_key_list(
                key,
                val_b,
                val_a,
                delta_b,
                delta_a,
            )
        else:
            if key in before:
                delta_b[key] = val_b
            if key in after:
                delta_a[key] = val_a

    @staticmethod
    def _diff_key_dict(
        key: str,
        val_b: dict[str, Any],
        val_a: dict[str, Any],
        delta_b: dict[str, Any],
        delta_a: dict[str, Any],
    ) -> None:
        """Diff nested dict values for a key."""
        sub_b, sub_a = AuditReportRenderer._compute_delta(val_b, val_a)
        if sub_b or sub_a:
            delta_b[key] = sub_b
            delta_a[key] = sub_a

    @staticmethod
    def _diff_key_list(
        key: str,
        val_b: list[Any],
        val_a: list[Any],
        delta_b: dict[str, Any],
        delta_a: dict[str, Any],
    ) -> None:
        """Diff nested list values for a key."""
        list_b, list_a = AuditReportRenderer._compute_delta_list(
            val_b,
            val_a,
        )
        if list_b is not None or list_a is not None:
            delta_b[key] = list_b if list_b is not None else []
            delta_a[key] = list_a if list_a is not None else []

    @staticmethod
    def _compute_delta_list(before: list[Any], after: list[Any]) -> tuple[list[Any] | None, list[Any] | None]:
        """Extract delta for list values.

        For lists of dicts, matches elements by identifier key
        (name/id/servicepolicy_id) rather than position, then
        shows only changed, added, or removed elements.
        """
        if before == after:
            return None, None

        all_dicts = all(isinstance(item, dict) for item in before) and all(isinstance(item, dict) for item in after)

        if not all_dicts:
            return before, after

        return AuditReportRenderer._delta_by_identity(before, after)

    @staticmethod
    def _element_identity(element: dict[str, Any]) -> str | None:
        """Get a stable identity string for a dict element.

        Tries several candidate keys in priority order. Returns
        the first non-None value found, or None if unidentifiable.
        """
        candidates = ("name", "id", "ssid", "network_id", "servicepolicy_id")
        for key in candidates:
            val = element.get(key)
            if val is not None:
                return f"{key}={val}"
        return None

    @staticmethod
    def _build_identity_map(
        elements: list[dict[str, Any]],
    ) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
        """Split list elements into identified and anonymous groups."""
        id_map: dict[str, dict[str, Any]] = {}
        anon: list[dict[str, Any]] = []
        for elem in elements:
            eid = AuditReportRenderer._element_identity(elem)
            if eid and eid not in id_map:
                id_map[eid] = elem
            else:
                anon.append(elem)
        return id_map, anon

    @staticmethod
    def _diff_identified(
        before_map: dict[str, dict[str, Any]],
        after_map: dict[str, dict[str, Any]],
        delta_b: list[dict[str, Any]],
        delta_a: list[dict[str, Any]],
    ) -> None:
        """Diff elements matched by identity key, appending to deltas."""
        all_ids = list(dict.fromkeys(list(before_map) + list(after_map)))
        for eid in all_ids:
            item_b = before_map.get(eid)
            item_a = after_map.get(eid)
            if item_b == item_a:
                continue
            if item_b and item_a:
                sub_b, sub_a = AuditReportRenderer._compute_delta(
                    item_b,
                    item_a,
                )
                if sub_b or sub_a:
                    delta_b.append(sub_b)
                    delta_a.append(sub_a)
            elif item_b:
                delta_b.append(item_b)
                delta_a.append({"_status": "(removed)"})
            elif item_a:
                delta_b.append({"_status": "(added)"})
                delta_a.append(item_a)

    @staticmethod
    def _diff_anonymous(
        before_anon: list[dict[str, Any]],
        after_anon: list[dict[str, Any]],
        delta_b: list[dict[str, Any]],
        delta_a: list[dict[str, Any]],
    ) -> None:
        """Diff unidentified elements by position, appending to deltas."""
        min_len = min(len(before_anon), len(after_anon))
        for i in range(min_len):
            if before_anon[i] != after_anon[i]:
                sub_b, sub_a = AuditReportRenderer._compute_delta(
                    before_anon[i],
                    after_anon[i],
                )
                if sub_b or sub_a:
                    delta_b.append(sub_b)
                    delta_a.append(sub_a)
        for item in before_anon[min_len:]:
            delta_b.append(item)
            delta_a.append({"_status": "(removed)"})
        for item in after_anon[min_len:]:
            delta_b.append({"_status": "(added)"})
            delta_a.append(item)

    @staticmethod
    def _check_reorder(
        before_map: dict[str, dict[str, Any]],
        after_map: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
        """Detect reordering when elements match but order differs."""
        before_ids = list(before_map.keys())
        after_ids = list(after_map.keys())
        if before_ids != after_ids and sorted(before_ids) == sorted(after_ids):
            label = AuditReportRenderer._reorder_label(before_ids)
            strip = AuditReportRenderer._strip_id_prefix
            return (
                [{label: [strip(k) for k in before_ids]}],
                [{label: [strip(k) for k in after_ids]}],
            )
        return None, None

    @staticmethod
    def _delta_by_identity(
        before: list[dict[str, Any]],
        after: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
        """Match list elements by best-available identity and diff."""
        before_map, before_anon = AuditReportRenderer._build_identity_map(
            before,
        )
        after_map, after_anon = AuditReportRenderer._build_identity_map(
            after,
        )

        delta_b: list[dict[str, Any]] = []
        delta_a: list[dict[str, Any]] = []

        AuditReportRenderer._diff_identified(
            before_map,
            after_map,
            delta_b,
            delta_a,
        )
        AuditReportRenderer._diff_anonymous(
            before_anon,
            after_anon,
            delta_b,
            delta_a,
        )

        if not delta_b and not delta_a:
            return AuditReportRenderer._check_reorder(
                before_map,
                after_map,
            )
        return delta_b, delta_a

    @staticmethod
    def _reorder_label(identity_keys: list[str]) -> str:
        """Build a descriptive label from identity key prefixes."""
        prefixes = {k.split("=", 1)[0] for k in identity_keys if "=" in k}
        fields = ", ".join(sorted(prefixes)) if prefixes else "index"
        return f"_reordered (by {fields})"

    @staticmethod
    def _strip_id_prefix(identity: str) -> str:
        """Strip the 'key=' prefix from an identity string."""
        return identity.split("=", 1)[1] if "=" in identity else identity

    @staticmethod
    def _epoch_to_readable(epoch: int) -> str:
        """Convert epoch to human-readable UTC string."""
        if not epoch:
            return "N/A"
        return datetime.fromtimestamp(epoch, tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

    @staticmethod
    def _epoch_to_short(epoch: int) -> str:
        """Convert epoch to short time string for Mermaid nodes."""
        if not epoch:
            return "?"
        return datetime.fromtimestamp(epoch, tz=UTC).strftime("%m/%d %H:%M")
