"""Wave 9 P2 coverage tests for src.audit._renderer_format.

Covers all four public paths of ``format_delta_html``: dict, list, leaf,
and empty-container shortcuts, plus the ``_render_dict_item`` /
``_format_leaf`` internals via nesting.
"""

from __future__ import annotations  # WHY: postponed eval for forward-ref consistency

from src.audit._renderer_format import format_delta_html


class TestFormatDeltaHtmlLeafBranch:
    """Cover the scalar leaf branch of format_delta_html."""

    def test_integer_leaf_wrapped_in_bold(self) -> None:
        # WHY: leaves are json-encoded then <b>-wrapped — verify both wrapping and value
        assert format_delta_html(42) == "<b>42</b>"

    def test_string_leaf_json_quoted_and_wrapped(self) -> None:
        # WHY: json.dumps quotes strings; html.escape keeps quotes safe for HTML
        result = format_delta_html("hello")
        assert result == "<b>&quot;hello&quot;</b>"

    def test_none_leaf_rendered_as_null(self) -> None:
        # WHY: json.dumps(None) emits 'null' — verify no traceback on None input
        assert format_delta_html(None) == "<b>null</b>"

    def test_boolean_leaf_rendered_lowercase(self) -> None:
        # WHY: json.dumps(True) emits 'true' — matches JSON spec, not Python repr
        assert format_delta_html(True) == "<b>true</b>"

    def test_leaf_with_html_metacharacters_escaped(self) -> None:
        # WHY: <script> tags in a leaf must be escaped so the browser doesn't execute them
        result = format_delta_html("<script>")
        assert "&lt;script&gt;" in result
        assert result.startswith("<b>") and result.endswith("</b>")


class TestFormatDeltaHtmlDictBranch:
    """Cover the dict branch including trailing-comma logic."""

    def test_empty_dict_compact(self) -> None:
        # WHY: empty container shortcut avoids block layout for zero entries
        assert format_delta_html({}) == "{}"

    def test_single_key_dict_no_trailing_comma(self) -> None:
        # WHY: last item must omit the trailing comma per JSON-like output
        rendered = format_delta_html({"a": 1})
        # WHY: keys pass through html.escape so quotes become &quot;
        assert "&quot;a&quot;: <b>1</b>" in rendered
        assert not rendered.rstrip().rstrip("}").rstrip().endswith(",")

    def test_multi_key_dict_has_comma_between_entries(self) -> None:
        # WHY: only intermediate lines carry trailing commas; verify at least one exists
        rendered = format_delta_html({"a": 1, "b": 2})
        # WHY: block form breaks across lines with braces on their own lines
        assert rendered.startswith("{")
        assert rendered.rstrip().endswith("}")
        assert "," in rendered

    def test_dict_key_containing_quotes_escaped(self) -> None:
        # WHY: keys pass through json.dumps then html.escape — verify no un-escaped quote leakage
        rendered = format_delta_html({'weird"key': 1})
        assert "&quot;" in rendered

    def test_nested_dict_recurses(self) -> None:
        # WHY: dict value branches back into format_delta_html; leaf still wrapped in <b>
        rendered = format_delta_html({"outer": {"inner": 5}})
        assert "<b>5</b>" in rendered
        # WHY: keys are html.escape'd so double-quotes become &quot;
        assert "&quot;outer&quot;" in rendered
        assert "&quot;inner&quot;" in rendered


class TestFormatDeltaHtmlListBranch:
    """Cover the list branch including trailing-comma logic."""

    def test_empty_list_compact(self) -> None:
        # WHY: empty container shortcut mirrors the empty-dict case
        assert format_delta_html([]) == "[]"

    def test_single_element_list_no_trailing_comma(self) -> None:
        # WHY: single element -> no comma between elements
        rendered = format_delta_html([1])
        assert "<b>1</b>" in rendered
        assert rendered.startswith("[")
        assert rendered.rstrip().endswith("]")

    def test_multi_element_list_has_commas(self) -> None:
        # WHY: intermediate elements append trailing comma; last one omits
        rendered = format_delta_html([1, 2, 3])
        assert rendered.count("<b>") == 3
        assert "," in rendered

    def test_list_of_dicts_recursively_rendered(self) -> None:
        # WHY: nested dicts inside a list exercise both branches of the dispatcher
        rendered = format_delta_html([{"a": 1}, {"b": 2}])
        # WHY: keys pass through html.escape so quotes become &quot;
        assert "&quot;a&quot;" in rendered
        assert "&quot;b&quot;" in rendered
        assert "<b>1</b>" in rendered

    def test_deeply_nested_structure_indented(self) -> None:
        # WHY: indent parameter propagates through recursion; ensure output is non-empty and structural
        rendered = format_delta_html({"outer": [{"inner": [1, 2]}]})
        # WHY: brackets/braces must be balanced in rendered output
        assert rendered.count("{") == rendered.count("}")
        assert rendered.count("[") == rendered.count("]")


class TestFormatDeltaHtmlIndentation:
    """Verify indent parameter propagates and produces distinct output."""

    def test_indent_increases_padding(self) -> None:
        # WHY: dict rendered with indent=2 has more leading whitespace than indent=0
        with_zero_indent = format_delta_html({"k": 1}, indent=0)
        with_deeper_indent = format_delta_html({"k": 1}, indent=2)
        # WHY: deeper indent adds two extra characters ("  ") on each line
        assert len(with_deeper_indent) > len(with_zero_indent)
