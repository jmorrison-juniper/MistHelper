"""Tests for the starlink_dashboard startup order and for the GPS output precision.

Issue #1721 moved the logging configuration above the dependency bootstrap.
Issue #1737 reduced the default precision of a printed GPS coordinate.
Issue #1838 routed the status line through the same precision control.

The module runs its dependency bootstrap at import time. That bootstrap can install
packages and can call sys.exit, so these tests never import the module. They read the
source, and they run only the symbols under test.
"""

import ast
import logging
import os
from pathlib import Path
from typing import Any

import pytest

# Absolute path to the module under test. The conftest fixture changes the working
# directory for every test, so a relative path cannot find the file.
MODULE_PATH = Path(__file__).resolve().parents[2] / "starlink_dashboard.py"

# Symbols the GPS tests need. The loader below runs these and nothing else.
GPS_SYMBOLS = frozenset(
    {
        "GPS_PRECISION_DECIMALS",
        "GPS_EXACT_ENV_VAR",
        "GPS_EXACT_OPT_IN_VALUES",
        "_exact_gps_enabled",
        "_format_gps_coordinate",
        "_dump_diagnostics_location",
        "_status_part_location",
    }
)

# Names that hold a GPS coordinate. The guard test below rejects a hardcoded format
# specifier on any one of them, because such a specifier bypasses the precision control.
COORDINATE_NAMES = frozenset({"lat", "latitude", "lon", "lng", "longitude"})

# A latitude and a longitude with more digits than the default output keeps.
EXACT_LATITUDE = 37.7749295
EXACT_LONGITUDE = -122.4194155


class FakeLocation:
    """Minimal stand-in for the location sub-message a Starlink terminal reports."""

    def __init__(self, latitude: float, longitude: float) -> None:
        """Store the two coordinates and the fields the dump reads.

        Args:
            latitude: The latitude the terminal reported.
            longitude: The longitude the terminal reported.
        """
        self.latitude = latitude  # The dump prints this value through the format helper.
        self.longitude = longitude  # The dump prints this value through the format helper.
        self.altitude_meters = 12.5  # The dump prints the altitude with no change.
        self.uncertainty_meters_valid = False  # Keep the optional branch out of the output.
        self.uncertainty_meters = 0.0  # Present so the optional branch cannot raise.
        self.enabled = True  # The status builder returns None when the terminal disables location.


class FakeDiagnostics:
    """Minimal stand-in for the diagnostics object the status builder reads."""

    def __init__(self, location: "FakeLocation | None") -> None:
        """Store the location sub-message the status builder reads.

        Args:
            location: The location sub-message, or None to drop the attribute.
        """
        if location is not None:  # A terminal without a location holds no attribute at all.
            self.location = location  # The status builder reads this sub-message.


def _module_source() -> str:
    """Return the source text of the module under test.

    Returns:
        str: The full file content.
    """
    return MODULE_PATH.read_text(encoding="utf-8")  # One read keeps every test on the same text.


def _module_body() -> list[ast.stmt]:
    """Return the top-level statements of the module under test.

    Returns:
        list[ast.stmt]: The module body in source order.
    """
    tree = ast.parse(_module_source(), filename=str(MODULE_PATH))  # Parse only, so no code runs.
    return tree.body  # The caller reads the order of these statements.


def _is_startup_statement(node: ast.stmt) -> bool:
    """Return True when the statement runs at import time.

    Args:
        node: A top-level statement of the module.

    Returns:
        bool: False for a definition, because a definition only binds a name.
    """
    return not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))


def _is_docstring(node: ast.stmt) -> bool:
    """Return True when the statement is a bare string expression.

    Args:
        node: A top-level statement of the module.

    Returns:
        bool: True for the module docstring, which runs but does nothing.
    """
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def _is_action_statement(node: ast.stmt) -> bool:
    """Return True when the statement does startup work.

    Args:
        node: A top-level statement of the module.

    Returns:
        bool: False for a definition, an import, and the module docstring.
    """
    if not _is_startup_statement(node):  # A definition only binds a name.
        return False
    if isinstance(node, (ast.Import, ast.ImportFrom)):  # An import must stay at the top.
        return False
    return not _is_docstring(node)  # The docstring does no work.


def _index_of_basic_config(body: list[ast.stmt]) -> int:
    """Return the position of the logging.basicConfig call in the startup path.

    Args:
        body: The top-level statements of the module.

    Returns:
        int: The index of the call, or -1 when the startup path holds no call.
    """
    for index, node in enumerate(body):  # Walk the startup path in source order.
        if not _is_startup_statement(node):  # A definition does not configure logging.
            continue
        for inner in ast.walk(node):  # Look inside the statement for the call.
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                if inner.func.attr == "basicConfig":  # This is the configuration call.
                    return index
    return -1  # No call found, which the test reports as a failure.


def _index_of_startup_call(body: list[ast.stmt], name: str) -> int:
    """Return the position of the first startup call to *name*.

    Args:
        body: The top-level statements of the module.
        name: The bare function name, such as "check_and_install_grpcio".

    Returns:
        int: The index of the call, or -1 when the startup path holds no call.
    """
    for index, node in enumerate(body):  # Walk the startup path in source order.
        if not _is_startup_statement(node):  # Skip a definition, because it does not call anything.
            continue
        for inner in ast.walk(node):  # Look inside the statement for the call.
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name):
                if inner.func.id == name:  # This is the bootstrap call.
                    return index
    return -1  # No call found, which the test reports as a failure.


def _collect_gps_nodes() -> list[ast.stmt]:
    """Return the GPS symbols of the module, with every decorator removed.

    Returns:
        list[ast.stmt]: The picked nodes in source order.
    """
    picked: list[ast.stmt] = []  # Holds only the nodes the GPS tests need.
    for node in ast.walk(ast.parse(_module_source(), filename=str(MODULE_PATH))):
        if isinstance(node, ast.FunctionDef) and node.name in GPS_SYMBOLS:
            node.decorator_list = []  # Drop staticmethod, so the function runs on its own.
            picked.append(node)  # Keep the function for the exec below.
        elif isinstance(node, ast.Assign) and _assigns_gps_symbol(node):
            picked.append(node)  # Keep the constant the functions read.
    picked.sort(key=lambda item: item.lineno)  # Restore source order, so names resolve.
    return picked


def _assigns_gps_symbol(node: ast.Assign) -> bool:
    """Return True when the assignment binds a GPS symbol.

    Args:
        node: A top-level assignment statement.

    Returns:
        bool: True when any target name is a GPS symbol.
    """
    return any(isinstance(target, ast.Name) and target.id in GPS_SYMBOLS for target in node.targets)


def _load_gps_namespace() -> dict[str, Any]:
    """Run the GPS symbols in an isolated namespace and return it.

    Returns:
        dict[str, Any]: The namespace that holds the GPS constants and functions.
    """
    module = ast.Module(body=_collect_gps_nodes(), type_ignores=[])  # A module of picked nodes only.
    namespace: dict[str, Any] = {
        "os": os,  # The opt-in check reads the environment.
        "logging": logging,  # The opt-in check writes a debug record.
        "Any": Any,  # Python evaluates the annotation when it runs the def statement.
        "logger": logging.getLogger("starlink_dashboard_test"),  # The dump writes debug records.
    }
    exec(compile(module, str(MODULE_PATH), "exec"), namespace)  # nosec B102 - the input is repository source.
    return namespace  # The caller reads the loaded symbols from here.


def test_logging_is_configured_before_the_dependency_bootstrap() -> None:
    """The logging configuration must run before both bootstrap calls (issue #1721)."""
    body = _module_body()  # Startup statements in source order.
    config_index = _index_of_basic_config(body)  # Position of the logging configuration.
    grpc_index = _index_of_startup_call(body, "check_and_install_grpcio")  # First bootstrap call.
    pyqt_index = _index_of_startup_call(body, "check_and_install_pyqt6")  # Second bootstrap call.
    assert config_index >= 0, "The startup path must call logging.basicConfig"
    assert grpc_index >= 0, "The startup path must call check_and_install_grpcio"
    assert pyqt_index >= 0, "The startup path must call check_and_install_pyqt6"
    assert config_index < grpc_index, "logging.basicConfig must run before check_and_install_grpcio"
    assert config_index < pyqt_index, "logging.basicConfig must run before check_and_install_pyqt6"


def test_startup_configures_logging_before_any_other_startup_action() -> None:
    """No startup action may run before the logging configuration (issue #1721)."""
    body = _module_body()  # Startup statements in source order.
    actions = [index for index, node in enumerate(body) if _is_action_statement(node)]  # Working statements.
    config_index = _index_of_basic_config(body)  # Position of the logging configuration.
    assert actions, "The module must hold at least one startup action"
    assert config_index == actions[0], "logging.basicConfig must be the first startup action"


def test_default_location_dump_rounds_both_coordinates() -> None:
    """A default run must not print an exact coordinate pair (issue #1737)."""
    namespace = _load_gps_namespace()  # Load the GPS symbols with no module import.
    assert namespace["GPS_PRECISION_DECIMALS"] == 3, "The default precision must stay at three places"
    latitude = namespace["_format_gps_coordinate"](EXACT_LATITUDE)  # Format the latitude.
    longitude = namespace["_format_gps_coordinate"](EXACT_LONGITUDE)  # Format the longitude.
    assert latitude == "37.775", "The default latitude must round to three decimal places"
    assert longitude == "-122.419", "The default longitude must round to three decimal places"


def test_default_location_dump_output_holds_no_exact_coordinate(capsys: pytest.CaptureFixture) -> None:
    """The printed dump must hold the rounded pair and not the exact pair (issue #1737)."""
    namespace = _load_gps_namespace()  # Load the GPS symbols with no module import.
    namespace["_dump_diagnostics_location"](FakeLocation(EXACT_LATITUDE, EXACT_LONGITUDE))  # Run the dump.
    output = capsys.readouterr().out  # Everything the dump sent to stdout.
    assert "  - Latitude: 37.775\n" in output, "The dump must print the rounded latitude"
    assert "  - Longitude: -122.419\n" in output, "The dump must print the rounded longitude"
    assert str(EXACT_LATITUDE) not in output, "The dump must not print the exact latitude"
    assert str(EXACT_LONGITUDE) not in output, "The dump must not print the exact longitude"


def test_exact_coordinates_need_an_explicit_opt_in(
    capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An operator who sets the opt-in variable gets the exact pair (issue #1737)."""
    namespace = _load_gps_namespace()  # Load the GPS symbols with no module import.
    monkeypatch.setenv(namespace["GPS_EXACT_ENV_VAR"], "1")  # Opt in for this test only.
    namespace["_dump_diagnostics_location"](FakeLocation(EXACT_LATITUDE, EXACT_LONGITUDE))  # Run the dump.
    output = capsys.readouterr().out  # Everything the dump sent to stdout.
    assert str(EXACT_LATITUDE) in output, "The opt-in must print the exact latitude"
    assert str(EXACT_LONGITUDE) in output, "The opt-in must print the exact longitude"


def test_opt_in_variable_ignores_an_unrelated_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only an opt-in value turns on the exact output (issue #1737)."""
    namespace = _load_gps_namespace()  # Load the GPS symbols with no module import.
    monkeypatch.setenv(namespace["GPS_EXACT_ENV_VAR"], "0")  # A value that is not an opt-in.
    assert namespace["_exact_gps_enabled"]() is False, "The value 0 must keep the safe default"
    monkeypatch.setenv(namespace["GPS_EXACT_ENV_VAR"], " YES ")  # An opt-in with extra spaces.
    assert namespace["_exact_gps_enabled"]() is True, "The value yes must turn on the exact output"


def _referenced_names(node: ast.expr) -> set[str]:
    """Return the names and the attributes the expression reads, in lower case.

    Args:
        node: The expression inside one f-string replacement field.

    Returns:
        set[str]: Every name and every attribute the expression reads.
    """
    names: set[str] = set()  # Collects one entry for each name the expression reads.
    for inner in ast.walk(node):  # Walk the expression, because a call can hide the name.
        if isinstance(inner, ast.Name):  # A bare name, such as latitude.
            names.add(inner.id.lower())  # Store the lower case form, so the match ignores case.
        elif isinstance(inner, ast.Attribute):  # An attribute, such as loc.latitude.
            names.add(inner.attr.lower())  # Store the attribute name on its own.
    return names  # The caller compares this set against COORDINATE_NAMES.


def _hardcoded_coordinate_formats() -> list[int]:
    """Return the module lines that format a coordinate with a hardcoded precision.

    Returns:
        list[int]: One line number for each replacement field that carries a format
        specifier on a coordinate name. An empty list means every path calls the helper.
    """
    offenders: list[int] = []  # Collects one line number for each offending field.
    for node in ast.walk(ast.parse(_module_source(), filename=str(MODULE_PATH))):
        if not isinstance(node, ast.FormattedValue):  # Only a replacement field can pin a precision.
            continue
        if node.format_spec is None:  # No specifier means the field cannot pin a decimal count.
            continue
        if _referenced_names(node.value) & COORDINATE_NAMES:  # The field formats a coordinate.
            offenders.append(node.lineno)  # Report the line, so a reader can find it.
    return offenders  # The guard test fails when this list holds any line.


def test_status_line_rounds_both_coordinates_on_a_default_run() -> None:
    """The status line must hold the rounded pair on a default run (issue #1838)."""
    namespace = _load_gps_namespace()  # Load the GPS symbols with no module import.
    diag = FakeDiagnostics(FakeLocation(EXACT_LATITUDE, EXACT_LONGITUDE))  # A terminal that reports a position.
    line = namespace["_status_part_location"](diag)  # Build the status line under the default settings.
    assert line == "Location: 37.775, -122.419", "The status line must round both coordinates"
    assert str(EXACT_LATITUDE) not in line, "The status line must not hold the exact latitude"
    assert str(EXACT_LONGITUDE) not in line, "The status line must not hold the exact longitude"
    assert "37.7749" not in line, "The status line must not keep the four decimal places of the old code"


def test_status_line_returns_the_exact_pair_after_the_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """An operator who sets the opt-in variable gets the exact pair (issue #1838)."""
    namespace = _load_gps_namespace()  # Load the GPS symbols with no module import.
    monkeypatch.setenv(namespace["GPS_EXACT_ENV_VAR"], "1")  # Opt in for this test only.
    diag = FakeDiagnostics(FakeLocation(EXACT_LATITUDE, EXACT_LONGITUDE))  # A terminal that reports a position.
    line = namespace["_status_part_location"](diag)  # Build the status line under the opt-in.
    assert str(EXACT_LATITUDE) in line, "The opt-in must return the exact latitude"
    assert str(EXACT_LONGITUDE) in line, "The opt-in must return the exact longitude"


def test_status_line_stays_empty_when_the_terminal_reports_no_location() -> None:
    """A terminal that reports no location produces no status line (issue #1838)."""
    namespace = _load_gps_namespace()  # Load the GPS symbols with no module import.
    build = namespace["_status_part_location"]  # One name keeps the two checks below short.
    assert build(FakeDiagnostics(None)) is None, "A missing location sub-message must return None"
    disabled = FakeLocation(EXACT_LATITUDE, EXACT_LONGITUDE)  # A terminal that turns location reporting off.
    disabled.enabled = False  # The status builder must skip a disabled sub-message.
    assert build(FakeDiagnostics(disabled)) is None, "A disabled location sub-message must return None"


def test_no_coordinate_format_string_hardcodes_a_decimal_count() -> None:
    """One helper must govern every coordinate the module prints (issue #1838)."""
    offenders = _hardcoded_coordinate_formats()  # Line numbers that pin a decimal count.
    assert not offenders, f"These lines must call _format_gps_coordinate: {offenders}"


def test_both_codeql_alerts_carry_a_recorded_verdict() -> None:
    """Every GPS alert must keep a verdict, a review date, and a review trigger (issue #1737)."""
    source = _module_source()  # The full module text holds the verdict comment.
    required = (
        "py/clear-text-logging-sensitive-data",  # The rule the verdict answers.
        "alert 190",  # The original latitude alert.
        "alert 191",  # The original longitude alert.
        "alert 193",  # The residual latitude alert on the rounded value.
        "alert 194",  # The residual longitude alert on the rounded value.
        "Verdict: fixed",  # The verdict for the exact coordinate pair.
        "accepted_with_rationale",  # The verdict for the residual rounded flow.
        "Review date: 2026-08-22",  # The date of the review.
        "Next review trigger:",  # The condition that reopens the review.
    )
    for marker in required:  # Each marker must survive any later edit.
        assert marker in source, f"The verdict comment must hold {marker}"
