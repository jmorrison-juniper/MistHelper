"""Migration helper: split viewer_callbacks.py into helper modules per wave.

Usage: `python scripts/_migrate_viewer_wave.py <wave>` where wave is one of
`ui`, `refresh`, `clone`, `drawing`, `site`, `url`.

For each wave the script:
1. Parses `viewer_callbacks.py` with :mod:`ast` to locate the named methods.
2. Writes a helper module `src/maps/launcher/_viewer_<wave>.py` containing
   a `_Viewer<Wave>` class with the extracted method bodies plus a
   `register(app)` method wiring this wave's Dash `app.callback` blocks.
3. Rewrites `viewer_callbacks.py` in place: replaces the moved methods
   with slim delegate stubs (or drops them entirely when they are
   private helpers only used inside the cluster).

Idempotent: running the same wave twice is a no-op.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

SOURCE = Path("src/maps/launcher/viewer_callbacks.py")


WAVES: dict[str, dict[str, object]] = {
    "ui": {
        "target": Path("src/maps/launcher/_viewer_ui.py"),
        "attr": "_ui",
        "class": "_ViewerUI",
        "public": [
            "display_click_data",
            "toggle_origin_mode",
            "toggle_zone_name_input",
            "toggle_auto_refresh",
            "toggle_individual_zones",
            "toggle_delete_panel",
            "toggle_clone_panel",
            "handle_utilities",
            "update_shape_labels",
            "set_origin_from_click",
            "execute_delete_map",
            "handle_zone_actions",
        ],
        "private": [
            "_update_origin_traces",
            "_backup_before_delete",
            "_render_delete_result",
            "_handle_zone_edit",
            "_handle_zone_remove",
            "_render_zone_delete_result",
            "_render_zone_not_selected",
            "_handle_zone_click",
        ],
    },
    "refresh": {
        "target": Path("src/maps/launcher/_viewer_refresh.py"),
        "attr": "_refresh",
        "class": "_ViewerRefresh",
        "public": [
            "update_countdown_display",
            "update_clients_traces",
            "update_coverage_heatmap",
        ],
        "private": [
            "_fetch_fresh_clients",
            "_partition_clients_by_link",
            "_apply_client_traces",
            "_apply_client_annotations",
            "_refresh_zones_silent",
            "_refresh_walls_silent",
            "_fetch_coverage_results",
            "_resolve_coverage_config",
            "_extract_coverage_indices",
            "_aggregate_grid_cells",
            "_build_z_matrix",
            "_compute_rssi_bounds",
            "_build_coverage_grid",
            "_apply_coverage_trace",
        ],
    },
    "clone": {
        "target": Path("src/maps/launcher/_viewer_clone.py"),
        "attr": "_clone",
        "class": "_ViewerClone",
        "public": [
            "execute_clone_operation",
        ],
        "private": [
            "_validate_clone_inputs",
            "_backup_before_clone",
            "_fetch_source_map",
            "_perform_clone",
            "_build_clone_payload",
            "_download_source_image",
            "_create_cloned_map",
            "_upload_clone_image",
            "_clone_zones_for_map",
            "_clone_single_zone",
            "_render_clone_success",
        ],
    },
    "drawing": {
        "target": Path("src/maps/launcher/_viewer_drawing.py"),
        "attr": "_drawing",
        "class": "_ViewerDrawing",
        "public": [
            "handle_drawing_tools",
        ],
        "private": [
            "_dispatch_drawing_button",
            "_handle_save_shape",
            "_save_zone_shape",
            "_save_wall_shape",
            "_save_validation_path_shape",
            "_render_save_result",
            "_delete_validation_paths",
            "_delete_wayfinding_paths",
            "_delete_walls",
            "_delete_all_zones",
            "_delete_zones_one_by_one",
        ],
    },
    "site": {
        "target": Path("src/maps/launcher/_viewer_site_switch.py"),
        "attr": "_site",
        "class": "_ViewerSiteSwitch",
        "public": [
            "set_scale",
            "refresh_map_dropdown",
            "handle_site_from_url",
            "sync_dropdown_with_url",
            "handle_site_switch_from_dropdown",
        ],
        "private": [
            "_find_last_line_shape",
            "_line_length_px",
            "_compute_new_ppm",
            "_store_new_ppm",
            "_reannotate_measurements",
            "_update_annotation_text",
            "_extract_url_param",
            "_resolve_site_name",
            "_perform_site_switch",
            "_fetch_site_maps",
            "_build_empty_site_payload",
            "_build_first_map_payload",
            "_merge_site_switch_config",
            "_build_site_switch_figure",
            "_add_background_image",
            "_fetch_site_switch_devices",
            "_add_simple_device_traces",
            "_simple_device_color",
            "_simple_device_symbol",
            "_add_single_device_trace",
            "_apply_site_switch_layout",
        ],
    },
    "url": {
        "target": Path("src/maps/launcher/_viewer_url_switch.py"),
        "attr": "_url",
        "class": "_ViewerUrlSwitch",
        "public": [
            "handle_url_map_switch",
        ],
        "private": [
            "_prepare_url_map_switch",
            "_validate_url_map_id",
            "_fetch_valid_map_ids",
            "_perform_url_map_switch",
            "_fetch_target_map",
            "_fetch_devices_for_map",
            "_fetch_zones_for_map",
            "_fetch_clients_for_map",
            "_build_url_switch_figure",
            "_add_url_switch_devices",
            "_group_devices_by_type",
            "_url_switch_device_config",
            "_render_url_switch_device_type",
            "_build_device_colors_and_hovers",
            "_add_url_switch_marker_trace",
            "_add_url_switch_device_labels",
            "_add_url_switch_orientation_crosshairs",
            "_add_crosshair_lines",
            "_add_orientation_dot",
            "_add_url_switch_clients",
            "_collect_client_arrays",
            "_add_url_switch_origin",
            "_add_url_switch_heatmap",
            "_fetch_url_switch_coverage",
            "_render_url_switch_heatmap",
            "_resolve_url_switch_indices",
            "_build_url_switch_grid",
            "_add_url_switch_heatmap_trace",
            "_apply_url_switch_layout",
            "_merge_url_switch_config",
        ],
    },
}


def _method_range(node: ast.FunctionDef) -> tuple[int, int]:
    start = node.lineno
    if node.decorator_list:
        start = min(d.lineno for d in node.decorator_list)
    return start, node.end_lineno


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise ValueError(f"class {name} not found")


def _method_signature(node: ast.FunctionDef, src_lines: list[str]) -> tuple[str, list[str]]:
    """Return the raw ``def ...:`` header text plus the list of arg names.

    We reconstruct the delegate stub by reusing the original signature
    verbatim (so type hints and defaults survive) and forwarding the
    parameters positionally, minus ``self``.
    """
    header_start = node.lineno - 1
    # WHY: use the body's first statement line as the exclusive end of the
    # signature; the previous "line ends with ':'" heuristic failed on
    # single-line ``def foo(...):  # WHY: comment`` headers because the
    # trailing WHY comment causes rstrip() to end with the comment text
    # rather than the colon, so the parser walked past the def into the
    # method body.
    first_body_stmt = node.body[0]
    body_start_line = first_body_stmt.lineno
    header_end = body_start_line - 2  # index of last signature line (0-based, inclusive)
    header = "".join(src_lines[header_start : header_end + 1])
    args = [a.arg for a in node.args.args if a.arg != "self"]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    for a in node.args.kwonlyargs:
        args.append(a.arg + "=" + a.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return header, args


def do_wave(wave_key: str) -> None:
    cfg = WAVES[wave_key]
    target: Path = cfg["target"]  # type: ignore[assignment]
    attr: str = cfg["attr"]  # type: ignore[assignment]
    class_name: str = cfg["class"]  # type: ignore[assignment]
    public: list[str] = cfg["public"]  # type: ignore[assignment]
    private: list[str] = cfg["private"]  # type: ignore[assignment]
    all_methods = set(public) | set(private)

    src_text = SOURCE.read_text(encoding="utf-8")
    src_lines = src_text.splitlines(keepends=True)
    tree = ast.parse(src_text)
    cls = _find_class(tree, "MapViewerCallbacks")

    # Collect method blocks in order of appearance in source
    blocks = []
    for item in cls.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in all_methods:
            start, end = _method_range(item)
            blocks.append(
                {
                    "name": item.name,
                    "start": start,
                    "end": end,
                    "text": "".join(src_lines[start - 1 : end]),
                    "node": item,
                }
            )

    missing = all_methods - {b["name"] for b in blocks}
    if missing:
        print(f"WARN: methods not found in source (already extracted?): {missing}")

    print(f"Extracting {len(blocks)} methods for wave {wave_key}: {[b['name'] for b in blocks]}")

    # --- Write helper module ---
    print(f"Writing {target}")
    helper_body_parts: list[str] = []
    for b in blocks:
        helper_body_parts.append(b["text"])
        if not b["text"].endswith("\n"):
            helper_body_parts.append("\n")
        helper_body_parts.append("\n")

    # Assemble the file
    file_content = target.read_text(encoding="utf-8") if target.exists() else ""
    if not file_content.strip():
        raise SystemExit(f"target {target} must be pre-seeded with header + register(app)")
    # Splice: replace `# METHODS_INSERT_HERE` marker with method bodies.
    # WHY: skip cleanly when the target has already been populated so we can
    # rerun just the source rewrite step (e.g. after fixing a delegate bug).
    if "# METHODS_INSERT_HERE" not in file_content:
        print(f"  target {target} already populated; skipping helper module rewrite")
    else:
        methods_text = "".join(helper_body_parts).rstrip() + "\n"
        # WHY: strip leading whitespace on the marker line so the first method's own
        # indentation isn't compounded with the marker line's indent (that produced
        # 8-space indent on the very first def during Wave 1).
        new_file = re.sub(
            r"^[ \t]*# METHODS_INSERT_HERE\n",
            methods_text,
            file_content,
            count=1,
            flags=re.MULTILINE,
        )
        target.write_text(new_file, encoding="utf-8", newline="\n")

    # --- Rewrite viewer_callbacks.py: replace public methods with delegates, drop privates ---
    # Sort blocks by start line descending so removals don't disturb earlier line numbers
    blocks_desc = sorted(blocks, key=lambda b: b["start"], reverse=True)
    new_lines = list(src_lines)
    for b in blocks_desc:
        start_idx = b["start"] - 1
        end_idx = b["end"]  # exclusive
        if b["name"] in public:
            header, args = _method_signature(b["node"], src_lines)
            call_args = ", ".join(args) if args else ""
            # Build delegate: header + one-line body
            method_lc = b["name"].replace("_", " ").strip()
            delegate = (
                header
                + f"        \"\"\"Delegate to :class:`{class_name}` for {b['name']}.\"\"\"\n"
                + f"        return self.{attr}.{b['name']}({call_args})  # WHY: delegate to {class_name} cluster\n"
                + "\n"
            )
            new_lines[start_idx:end_idx] = [delegate]
        else:
            # Drop private helper entirely
            new_lines[start_idx:end_idx] = []
        # Also drop the trailing blank line if present
        if start_idx < len(new_lines) and new_lines[start_idx].strip() == "":
            # keep single separator
            pass

    SOURCE.write_text("".join(new_lines), encoding="utf-8", newline="\n")
    print(f"Rewrote {SOURCE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: _migrate_viewer_wave.py <wave>")
        raise SystemExit(1)
    do_wave(sys.argv[1])
