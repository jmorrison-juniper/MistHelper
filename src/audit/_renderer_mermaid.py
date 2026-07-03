"""Mermaid Markdown rendering cluster for :mod:`src.audit.renderer`.

Owns the four ``_mermaid_*`` sections (header, admin timeline, object
changelogs, rollback table). Split out to shrink the parent module and
keep each rendering method within the compliance budget.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import json  # WHY: pretty-print original/final states in fenced code blocks
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids circular import at runtime

from src.audit._renderer_delta import compute_delta  # WHY: shared delta walker
from src.audit._renderer_time import epoch_to_readable, epoch_to_short  # WHY: shared timestamp formatters

if TYPE_CHECKING:  # WHY: only imported by type-checkers
    from src.audit.analyzer import AuditAnalysisResult  # WHY: analysis payload type

MERMAID_NODE_CAP = 500  # WHY: hard cap avoids diagrams that break Mermaid rendering


class _MermaidCluster:  # WHY: private cluster owned by AuditReportRenderer
    """Render Mermaid markdown sections for an audit analysis result."""

    def header(self, analysis: AuditAnalysisResult) -> str:  # WHY: public entry for markdown title block
        """Generate the report header section."""
        return (  # WHY: multi-line f-string builds the markdown header block
            f"# Org Audit Log Analysis\n\n"
            f"**Time Range**: {analysis.time_range_description}\n"
            f"**Total Entries (after filter)**: {analysis.filtered_entries}\n"
            f"**Admins Active**: {len(analysis.admin_timelines)}\n"
            f"**Objects Modified**: {len(analysis.object_changelogs)}\n"
            f"**Net Changes (rollback needed)**: {len(analysis.rollback_diffs)}\n"
        )

    def admin_timeline(self, analysis: AuditAnalysisResult) -> str:  # WHY: public entry for waterfall graph
        """Generate vertical admin timeline using Mermaid ``graph TD``."""
        lines: list[str] = ["## Admin Activity Timeline\n", "```mermaid", "graph TD"]  # WHY: block prelude
        node_count = self._render_admin_subgraphs(analysis, lines)  # WHY: emit per-admin subgraphs
        lines.append("```")  # WHY: close the fenced mermaid block
        self._append_admin_summary_bullets(analysis, lines)  # WHY: readable per-admin action summary
        if node_count >= MERMAID_NODE_CAP:  # WHY: single info line when we capped the diagram
            pass  # WHY: cap line already emitted inline by _render_admin_subgraphs
        return "\n".join(lines)  # WHY: markdown output is newline-joined lines

    def _render_admin_subgraphs(
        self,
        analysis: AuditAnalysisResult,
        lines: list[str],
    ) -> int:  # WHY: returns updated node count so parent can respect global cap
        """Emit per-admin subgraph blocks; return total node count emitted."""
        node_count = 0  # WHY: shared counter respects MERMAID_NODE_CAP across admins
        for timeline in analysis.admin_timelines:  # WHY: one subgraph per admin
            node_count = self._render_one_admin_subgraph(timeline, node_count, lines)  # WHY: accumulate emitted nodes
            if node_count >= MERMAID_NODE_CAP:  # WHY: stop emitting subgraphs once capped
                lines.append(f"  %% Capped at {MERMAID_NODE_CAP} nodes")  # WHY: inform reader we truncated
                break  # WHY: bail out of the admin loop once cap reached
        return node_count  # WHY: hand updated count back so caller can decide next steps

    def _render_one_admin_subgraph(
        self,
        timeline: Any,
        node_count: int,
        lines: list[str],
    ) -> int:  # WHY: returns updated node count so caller can enforce global cap
        """Emit one admin subgraph and return the updated node counter."""
        safe_name = timeline.admin_name.replace(" ", "_").replace(".", "")  # WHY: mermaid id safety
        lines.append(f'  subgraph {safe_name}["{timeline.admin_name}"]')  # WHY: subgraph opener
        entries_to_show = timeline.entries[:MERMAID_NODE_CAP]  # WHY: pre-slice bounds inner loop
        prev_node = None  # WHY: prev-pointer builds the chain edges
        for entry in entries_to_show:  # WHY: iterate capped entry list
            if node_count >= MERMAID_NODE_CAP:  # WHY: honor global cap even mid-subgraph
                break  # WHY: caller detects cap and appends the truncation marker
            prev_node = self._emit_timeline_entry(entry, node_count, prev_node, lines)  # WHY: emit node and edge
            node_count += 1  # WHY: advance shared counter
        lines.append("  end")  # WHY: close subgraph
        return node_count  # WHY: pass counter back so caller keeps global tally

    def _emit_timeline_entry(
        self,
        entry: dict[str, Any],
        node_count: int,
        prev_node: str | None,
        lines: list[str],
    ) -> str:  # WHY: return new node id so caller can chain edges
        """Emit a single entry node (and its edge) and return the new prev_node."""
        ts = entry.get("timestamp", 0)  # WHY: pull optional timestamp for label
        msg = entry.get("message", "")[:60].replace('"', "'")  # WHY: truncate + de-quote for label safety
        time_str = epoch_to_short(ts)  # WHY: shared formatter avoids cross-cluster private access
        node_id = f"n{node_count}"  # WHY: unique mermaid id per emitted node
        lines.append(f'    {node_id}["{time_str}: {msg}"]')  # WHY: emit the node line
        if prev_node:  # WHY: skip edge before the first node
            lines.append(f"    {prev_node} --> {node_id}")  # WHY: connect to preceding node in chain
        return node_id  # WHY: caller uses this as prev_node for next iteration

    def _append_admin_summary_bullets(
        self,
        analysis: AuditAnalysisResult,
        lines: list[str],
    ) -> None:  # WHY: side effect only; extends the shared lines list
        """Append the trailing bulleted summary of per-admin activity."""
        for timeline in analysis.admin_timelines:  # WHY: one bullet per admin
            start = epoch_to_readable(timeline.first_action)  # WHY: shared formatter, module-level import
            end = epoch_to_readable(timeline.last_action)  # WHY: shared formatter, module-level import
            lines.append(  # WHY: emit one markdown bullet summarizing this admin's activity
                f"- **{timeline.admin_name}**: {timeline.action_count} actions " f"({start} to {end})"
            )

    def object_changelogs(self, analysis: AuditAnalysisResult) -> str:  # WHY: public entry for per-object tables
        """Generate per-object changelog section."""
        lines: list[str] = ["## Object Changelogs\n"]  # WHY: section header
        for changelog in analysis.object_changelogs[:MERMAID_NODE_CAP]:  # WHY: cap number of tables
            self._emit_changelog_table(changelog, lines)  # WHY: delegate table emission per object
        return "\n".join(lines)  # WHY: newline-join keeps markdown output stable

    def _emit_changelog_table(self, changelog: Any, lines: list[str]) -> None:
        """Append one changelog table for a single object."""
        lines.append(f"### {changelog.object_type}: {changelog.object_name} " f"({len(changelog.changes)} changes)")
        lines.append("")  # WHY: blank line between heading and table
        lines.append("| Time | Admin | Action |")  # WHY: markdown table header
        lines.append("| - | - | - |")  # WHY: markdown separator row
        for change in changelog.changes:  # WHY: one row per change
            time_str = epoch_to_readable(change.timestamp)  # WHY: shared formatter, module-level import
            msg_short = change.message[:80]  # WHY: keep table cells readable
            lines.append(f"| {time_str} | {change.admin_name} | {msg_short} |")
        lines.append("")  # WHY: trailing blank line after each table

    def rollback_table(self, analysis: AuditAnalysisResult) -> str:
        """Generate rollback diff summary and detailed diffs."""
        lines: list[str] = ["## Rollback Summary (Objects with Net Changes)\n"]  # WHY: section header
        if not analysis.rollback_diffs:  # WHY: early return when no rollbacks needed
            lines.append("No net changes detected - all objects returned to original state.")
            return "\n".join(lines)
        self._emit_rollback_summary(analysis, lines)  # WHY: two-column summary table
        lines.append("")  # WHY: spacer before details
        lines.append("### Detailed Diffs\n")  # WHY: subheading for diff blocks
        self._emit_rollback_details(analysis, lines)  # WHY: expandable per-object diff details
        return "\n".join(lines)

    def _emit_rollback_summary(
        self,
        analysis: AuditAnalysisResult,
        lines: list[str],
    ) -> None:
        """Emit the top-level rollback summary table."""
        lines.append("| Object | Type | Fields Changed |")  # WHY: markdown table header
        lines.append("| - | - | - |")  # WHY: markdown separator row
        for diff in analysis.rollback_diffs:  # WHY: one row per object with net change
            fields = ", ".join(diff.fields_changed[:5])  # WHY: cap for legibility
            if len(diff.fields_changed) > 5:  # WHY: signal truncation to the reader
                fields += f" (+{len(diff.fields_changed) - 5} more)"
            lines.append(f"| {diff.object_name} | {diff.object_type} | {fields} |")

    def _emit_rollback_details(
        self,
        analysis: AuditAnalysisResult,
        lines: list[str],
    ) -> None:
        """Emit expandable details for each object with a non-empty delta."""
        for diff in analysis.rollback_diffs:  # WHY: iterate net-changed objects
            delta_orig, delta_final = compute_delta(diff.original_state, diff.final_state)
            if not delta_orig and not delta_final:  # WHY: skip when delta collapses to empty
                continue
            self._emit_rollback_detail_block(diff, delta_orig, delta_final, lines)

    def _emit_rollback_detail_block(
        self,
        diff: Any,
        delta_orig: dict[str, Any],
        delta_final: dict[str, Any],
        lines: list[str],
    ) -> None:
        """Emit a single ``<details>`` block with before/after JSON snippets."""
        lines.append(f"<details><summary>{diff.object_type}: {diff.object_name}</summary>\n")
        lines.append("**Original (changed fields only):**")  # WHY: label for before block
        lines.append("```json")  # WHY: fenced JSON block open
        lines.append(json.dumps(delta_orig, indent=2, default=str)[:2000])  # WHY: cap payload size
        lines.append("```")  # WHY: fenced JSON block close
        lines.append("**Final (changed fields only):**")  # WHY: label for after block
        lines.append("```json")
        lines.append(json.dumps(delta_final, indent=2, default=str)[:2000])
        lines.append("```")
        lines.append("</details>\n")  # WHY: close details container
