"""Unit tests for src/ui/execution/output_formatter.py."""

from __future__ import annotations

from src.ui.execution.output_formatter import APIResponseParser, HierarchicalFormatter


class _FakeAPIResponse:
    """Minimal stub mimicking a mistapi APIResponse."""

    def __init__(self, data) -> None:  # generic payload
        self.data = data  # Mimic the .data attribute


def test_api_response_parser_extracts_data() -> None:
    """Parser returns ``.data`` when present."""
    parsed = APIResponseParser().parse(_FakeAPIResponse({"x": 1}))  # Extract .data
    assert parsed == {"x": 1}  # Inner payload returned


def test_api_response_parser_passthrough_when_no_data_attr() -> None:
    """Parser returns the original value when it has no ``.data`` attr."""
    assert APIResponseParser().parse(["raw"]) == ["raw"]  # Passthrough


def test_format_result_emits_success_header() -> None:
    """The output starts with a SUCCESS banner naming the function."""
    output = HierarchicalFormatter().format_result({"results": [1, 2]}, "myFunc")  # Format payload
    assert output[0] == "[SUCCESS] myFunc completed"  # Banner first


def test_format_result_includes_debug_hint_when_raw_result_present() -> None:
    """When raw_result is supplied, a debug-path hint line is included."""
    output = HierarchicalFormatter().format_result({}, "fn", raw_result="anything")  # Debug branch
    assert any("Debug:" in line for line in output)  # Debug hint emitted


def test_format_result_emits_large_data_tip() -> None:
    """Large nested payloads get the 'full data available' tip."""
    big = {"key" + str(i): i for i in range(200)}  # Force str(...) > 500 chars
    output = HierarchicalFormatter().format_result(big, "fn")  # Format
    assert any("Full data available" in line for line in output)  # Tip present


def test_render_dict_emits_header_and_keys() -> None:
    """A dict value emits a header and one line per scalar entry."""
    out: list[str] = []  # Accumulator
    HierarchicalFormatter()._render({"a": 1, "b": "x"}, out, indent=0, key_name=None)  # Render
    assert out[0] == "dict (2 keys)"  # Header line
    assert any(line.endswith("a: 1") for line in out)  # 'a' entry
    assert any(line.endswith("b: x") for line in out)  # 'b' entry


def test_render_list_emits_header_and_items() -> None:
    """A list emits its header + a line per first-N items + remainder hint."""
    out: list[str] = []  # Accumulator
    HierarchicalFormatter()._render(list(range(10)), out, indent=0, key_name="nums")
    assert out[0].startswith("nums: list (10 items)")  # Header with named key
    assert any("... 5 more items" in line for line in out)  # Truncation hint (10 > 5)


def test_render_empty_sequence_emits_empty_marker() -> None:
    """Empty sequence produces an explicit ``(empty)`` line."""
    out: list[str] = []  # Accumulator
    HierarchicalFormatter()._render([], out, indent=0, key_name=None)  # Empty list
    assert "  (empty)" in out  # Empty marker present


def test_render_dict_inside_list_uses_3_key_sample() -> None:
    """List items that are dicts get a 3-key sample + remainder note."""
    out: list[str] = []  # Accumulator
    big_dict = {f"k{i}": i for i in range(5)}  # 5 keys -> truncated to 3
    HierarchicalFormatter()._render([big_dict], out, indent=0, key_name="rows")
    assert any("more keys" in line for line in out)  # Truncation marker
    assert any("[0]: dict (5 keys)" in line for line in out)


def test_render_none_value() -> None:
    """None values are rendered with the literal 'None' token."""
    out: list[str] = []  # Accumulator
    HierarchicalFormatter()._render(None, out, indent=0, key_name="x")  # None branch
    assert out == ["x: None"]  # Single line, key + None


def test_truncate_str_caps_long_strings() -> None:
    """Strings over the limit get a trailing '...'."""
    long = "a" * 300  # 300-char string
    assert HierarchicalFormatter()._truncate_str(long, 50).endswith("...")
    assert len(HierarchicalFormatter()._truncate_str(long, 50)) == 53  # 50 + '...'
    assert HierarchicalFormatter()._truncate_str("ok", 50) == "ok"  # Short unchanged


def test_render_nested_sequence_inside_list() -> None:
    """A list-of-lists triggers the nested-sequence recursion branch."""
    out: list[str] = []  # Accumulator
    HierarchicalFormatter()._render([[1, 2], [3]], out, indent=0, key_name="grid")
    assert out[0].startswith("grid: list (2 items)")  # Outer header
    # The two child lists each emit their own header below the outer one:
    assert sum(1 for line in out if "list (2 items)" in line or "list (1 items)" in line) >= 2


def test_render_dict_entry_with_nested_value_recurses() -> None:
    """A dict entry whose value is itself a dict recurses one level deeper."""
    out: list[str] = []  # Accumulator
    HierarchicalFormatter()._render({"outer": {"inner": 9}}, out, indent=0, key_name=None)
    assert any("outer: dict (1 keys)" in line for line in out)  # Recursion header
    assert any(line.endswith("inner: 9") for line in out)  # Inner entry rendered
