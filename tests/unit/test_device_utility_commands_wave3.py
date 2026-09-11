"""Wave 3 top-up tests for DeviceUtilityCommands (initiative 1018).

Targets the last two uncovered branches in
``src/device/utility_commands.py``:

* Line 70: ``_extract_error_detail`` returns ``""`` when ``response.data``
  is not a dict (e.g. ``None``, string, list). Existing tests only cover
  the ``isinstance(data, dict)`` happy path.
* Line 165: ``DeviceUtilityCommands.__getattr__`` raises ``AttributeError``
  when no cluster class defines the requested attribute. Existing tests
  cover the success path through the cluster loop but never provoke the
  final ``raise``.

Tests are pure (no I/O, no mistapi calls); all injected dependencies are
``MagicMock(spec=...)`` where a spec object is available and plain
``MagicMock`` otherwise.
"""

from __future__ import annotations  # WHY: PEP 604 unions in annotations across module.

from unittest.mock import MagicMock  # WHY: build synthetic response/deps with spec-locked attrs.

import pytest  # WHY: expect AttributeError with pytest.raises.

from src.device.utility_commands import (  # WHY: SUTs under test.
    DeviceUtilityCommands,
    UtilityCommandsDeps,
    _extract_error_detail,
)


def _make_deps() -> UtilityCommandsDeps:
    """Build a fully-mocked deps bundle so DeviceUtilityCommands can be constructed."""
    return UtilityCommandsDeps(  # WHY: frozen struct satisfies parent __init__ signature.
        apisession=MagicMock(name="apisession"),  # WHY: no spec available on 3rd-party session shape.
        select_site_fn=MagicMock(name="select_site_fn"),  # WHY: callable stub; never invoked here.
        select_device_fn=MagicMock(name="select_device_fn"),  # WHY: callable stub; never invoked here.
        safe_input_fn=MagicMock(name="safe_input_fn"),  # WHY: callable stub; never invoked here.
        write_export_fn=MagicMock(name="write_export_fn"),  # WHY: callable stub; never invoked here.
        websocket_manager_factory=MagicMock(name="ws_factory"),  # WHY: factory stub; never invoked here.
    )


class TestExtractErrorDetailNonDict:
    """Cover the ``return ""`` branch when ``response.data`` is not a dict."""

    def test_data_is_none_returns_empty_string(self) -> None:
        """When ``response.data`` is None, _extract_error_detail must return ""."""
        response = MagicMock(name="response")  # WHY: build a response whose data attribute is set to None.
        response.data = None  # WHY: force the isinstance check to fall through.
        assert _extract_error_detail(response) == ""  # WHY: non-dict shape yields empty detail string.

    def test_data_is_string_returns_empty_string(self) -> None:
        """A string ``data`` also hits the non-dict branch."""
        response = MagicMock(name="response")  # WHY: build a response with a string body.
        response.data = "opaque error text"  # WHY: exercises the isinstance(data, dict) False branch.
        assert _extract_error_detail(response) == ""  # WHY: only dict shapes carry the detail key.

    def test_data_missing_attribute_returns_empty_string(self) -> None:
        """A response with no ``data`` attribute at all also returns ""."""

        class Bare:  # WHY: minimal class without a data attribute forces getattr default None.
            """Placeholder response with no data attribute for the negative path."""

        assert _extract_error_detail(Bare()) == ""  # WHY: getattr(None) then isinstance False yields "".


class TestGetattrUnknownRaises:
    """Cover the trailing ``raise AttributeError`` when no cluster owns the name."""

    def test_unknown_attribute_raises_attribute_error(self) -> None:
        """A wholly unknown attribute must raise AttributeError with the stdlib-style message."""
        commands = DeviceUtilityCommands(_make_deps())  # WHY: real init to populate _clusters tuple.
        with pytest.raises(AttributeError) as excinfo:  # WHY: assert the terminal raise fires.
            _ = commands.definitely_no_such_helper  # WHY: none of the 5 clusters expose this name.
        assert "definitely_no_such_helper" in str(excinfo.value)  # WHY: message must name the attribute.

    def test_dunder_style_unknown_also_raises(self) -> None:
        """Non-magic dunder-adjacent names still hit the raise since clusters do not define them."""
        commands = DeviceUtilityCommands(_make_deps())  # WHY: fresh instance; clusters bind self.
        with pytest.raises(AttributeError):  # WHY: proves the raise is reachable for any missing attr.
            _ = commands._nope_definitely_missing_helper  # WHY: single underscore avoids Python name-mangling.
