"""Guard the portal controls that answer required plain prompts."""

from __future__ import annotations  # Keep annotations lazy for the Python test runtime.

import sys  # Add the repository root when pytest starts from another directory.
from pathlib import Path  # Resolve the repository root without a hardcoded separator.

import pytest  # Parametrize the menu checks so each row reports its own failure.

REPO_ROOT = Path(__file__).resolve().parents[3]  # Locate the checkout from this test file.
if str(REPO_ROOT) not in sys.path:  # Make direct pytest invocation behave like the CI runner.
    sys.path.insert(0, str(REPO_ROOT))  # Let imports find local packages before installed packages.

from src.export import endpoint_family_exporter  # noqa: E402
from src.export.count_exporter import _MSP_OPS as COUNT_MSP_OPS  # noqa: E402
from src.export.count_exporter import _ORG_OPS as COUNT_ORG_OPS  # noqa: E402
from src.export.endpoint_catalog import menu_text  # noqa: E402
from src.export.simple_endpoint_exporter import _MSP_OPS as ENDPOINT_MSP_OPS  # noqa: E402
from src.export.simple_endpoint_exporter import _NONE_OPS as ENDPOINT_NONE_OPS  # noqa: E402
from src.export.simple_endpoint_exporter import _ORG_OPS as ENDPOINT_ORG_OPS  # noqa: E402
from web_portal.services.operation import PARAMETER_REGISTRY  # noqa: E402

CHOOSER_EXPECTATIONS = {  # Map each chooser row to its source table and parameter name.
    "235": ("count_operation", "Count Operation", COUNT_ORG_OPS),  # Menu 235 chooses one org count operation.
    "237": ("count_operation", "Count Operation", COUNT_MSP_OPS),  # Menu 237 chooses one MSP count operation.
    "259": ("endpoint_operation", "Endpoint", ENDPOINT_NONE_OPS),  # Menu 259 chooses one global endpoint.
    "260": ("endpoint_operation", "Endpoint", ENDPOINT_ORG_OPS),  # Menu 260 chooses one org endpoint.
    "262": ("endpoint_operation", "Endpoint", ENDPOINT_MSP_OPS),  # Menu 262 chooses one MSP endpoint.
}

CONTROL_EXPECTATIONS = {  # State each prompt sequence that issue #3230 repaired.
    "235": [("choice", "count_operation", "Count Operation")],  # Menu 235 has one chooser.
    "237": [("choice", "count_operation", "Count Operation"), ("text", "msp_id", "MSP ID")],
    "238": [("text", "msp_id", "MSP ID")],  # Menu 238 asks only for the MSP identifier.
    "242": [("text", "ssid", "SSID")],  # Menu 242 asks for one SSID and rejects an empty answer.
    "247": [("text", "email_change_token", "Email Change Token")],  # Menu 247 asks for one email token.
    "259": [("choice", "endpoint_operation", "Endpoint")],  # Menu 259 has one chooser.
    "260": [("choice", "endpoint_operation", "Endpoint")],  # Menu 260 has one chooser.
    "262": [("choice", "endpoint_operation", "Endpoint"), ("text", "msp_id", "MSP ID")],
}

ENDPOINT_FAMILY_TABLES = {  # Map each dynamic endpoint row to its source table.
    "263": endpoint_family_exporter._SITE_SLE_OPS,  # Menu 263 models site SLE endpoint prompts.
    "264": endpoint_family_exporter._SITE_MAP_OPS,  # Menu 264 models site map endpoint prompts.
    "265": endpoint_family_exporter._SITE_DETAIL_OPS,  # Menu 265 models site detail endpoint prompts.
    "266": endpoint_family_exporter._ORG_DETAIL_OPS,  # Menu 266 models org detail endpoint prompts.
    "267": endpoint_family_exporter._MSP_DETAIL_OPS,  # Menu 267 models MSP detail endpoint prompts.
    "268": endpoint_family_exporter._OTHER_DETAIL_OPS,  # Menu 268 models other endpoint prompts.
}


def _parameters(menu: str) -> list[dict]:
    """Return the parameter list for one menu row."""
    entry = PARAMETER_REGISTRY[menu]  # Fail loudly if the repaired menu row is absent.
    return entry["parameters"]  # Return the portal controls in the order the handler reads answers.


@pytest.mark.parametrize("menu,expected", sorted(CONTROL_EXPECTATIONS.items()))  # Check each repaired row.
def test_required_prompt_rows_declare_their_controls(menu: str, expected: list[tuple[str, str, str]]) -> None:
    """The portal declares one required control for each fixed prompt."""
    parameters = _parameters(menu)  # Read the controls that the browser renders for this row.
    actual = [  # Keep only the fields that prove the prompt contract.
        (parameter.get("param_type"), parameter.get("name"), parameter.get("label")) for parameter in parameters
    ]
    assert actual == expected  # The control order must match the prompt order.
    assert all(
        parameter.get("required") is True for parameter in parameters
    )  # Each repaired prompt rejects empty input.


@pytest.mark.parametrize("menu,expected", sorted(CONTROL_EXPECTATIONS.items()))  # Check each repaired row.
def test_required_prompt_rows_are_browser_runnable(menu: str, expected: list[tuple[str, str, str]]) -> None:
    """The fixed prompt rows remain runnable in the browser."""
    del expected  # The parametrized value names the row in a failure without repeating a table.
    assert PARAMETER_REGISTRY[menu]["category"] == "interactive"  # The portal must show Run after answers exist.


@pytest.mark.parametrize("menu,expectation", sorted(CHOOSER_EXPECTATIONS.items()))  # Check each chooser row.
def test_chooser_options_match_the_exporter_table(menu: str, expectation: tuple[str, str, tuple]) -> None:
    """A chooser shows each exporter operation exactly once and in chooser order."""
    expected_name, expected_label, source_table = expectation  # Unpack the source table for this menu.
    parameter = _parameters(menu)[0]  # Each repaired chooser is the first prompt the handler reads.
    options = parameter["options"]  # Read the options that the browser will show.
    expected_options = [  # Build the same 1-based chooser list from the exporter source of truth.
        {"value": str(position), "label": entry.operation} for position, entry in enumerate(source_table, start=1)
    ]
    assert parameter["name"] == expected_name  # The answer key must match the row contract.
    assert parameter["label"] == expected_label  # The control label must tell the operator what to choose.
    assert options == expected_options  # A copied list cannot drift from the exporter table.
    assert len(options) == len(source_table)  # The count proves the test examined the whole chooser.


def _expected_dynamic_parameter(identifier: str) -> tuple[str, str, str] | None:
    """Return the expected prompt control shape for one endpoint identifier."""
    if identifier == "org_id":  # The portal context supplies org_id without a queued input answer.
        return None  # No portal control can be sent for an input() call that does not happen.
    if identifier == "site_id":  # The CLI prompt accepts a site name and resolves its identifier.
        return ("site", "site_id", "Site")  # The existing site selector gives a readable site list.
    if identifier == "msp_id":  # The CLI prompt asks for the MSP identifier directly.
        return ("text", "msp_id", "MSP ID")  # Keep the established MSP label from nearby portal rows.
    return ("text", identifier, identifier.replace("_", " ").title())  # Other IDs use required text controls.


def _expected_dynamic_parameters(required: tuple[str, ...]) -> list[tuple[str, str, str]]:
    """Return the prompt controls that should follow one endpoint choice."""
    controls = []  # Preserve the exporter tuple order.
    for identifier in required:  # Read every required identifier from the endpoint source table.
        control = _expected_dynamic_parameter(identifier)  # Map identifiers to portal controls.
        if control is not None:  # Context-resolved identifiers do not produce input queue answers.
            controls.append(control)  # Keep only controls that the browser must collect.
    return controls  # Return the answer controls in command-line prompt order.


@pytest.mark.parametrize("menu,source_table", sorted(ENDPOINT_FAMILY_TABLES.items()))  # Check all six families.
def test_endpoint_family_rows_are_dynamic_and_browser_runnable(menu: str, source_table: tuple) -> None:
    """Endpoint family rows expose one dynamic chooser instead of command-line-only text."""
    entry = PARAMETER_REGISTRY[menu]  # Read the row state that the browser consumes.
    assert entry["category"] == "interactive"  # The dynamic prompt model makes the row browser-runnable.
    assert len(source_table) >= 1  # The guard must prove it measured at least one operation in the family.
    assert len(entry["parameters"]) == 1  # The static control is only the endpoint chooser.
    parameter = entry["parameters"][0]  # Read the chooser that selects the operation.
    assert parameter["param_type"] == "choice"  # The first prompt is a numbered endpoint choice.
    assert parameter["name"] == "endpoint_operation"  # The answer key documents the prompt role.
    assert parameter["required"] is True  # Run must stay disabled until the endpoint choice exists.
    assert len(parameter["options"]) == len(source_table)  # The guard checks the full source table count.


@pytest.mark.parametrize("menu,source_table", sorted(ENDPOINT_FAMILY_TABLES.items()))  # Check all six families.
def test_endpoint_family_options_keep_required_tuple(menu: str, source_table: tuple) -> None:
    """Each endpoint option carries the source operation and required tuple."""
    parameter = _parameters(menu)[0]  # Read the chooser that the browser renders.
    expected_options = [  # Build the expected browser options from the exporter source table.
        {"value": str(position), "label": menu_text(operation.operation), "required": list(operation.required)}
        for position, operation in enumerate(source_table, start=1)
    ]
    assert parameter["options"] == expected_options  # The browser choice list must not drift from the exporter.


@pytest.mark.parametrize("menu,source_table", sorted(ENDPOINT_FAMILY_TABLES.items()))  # Check all six families.
def test_endpoint_family_dynamic_controls_follow_required_tuple(menu: str, source_table: tuple) -> None:
    """The dynamic controls match the selected endpoint prompts in source order."""
    parameter = _parameters(menu)[0]  # Read the chooser metadata returned to the browser.
    dynamic_parameters = parameter["dynamic_parameters"]  # The browser uses this map after a choice.
    assert len(dynamic_parameters) == len(source_table)  # The map must cover every endpoint in the family.
    assert any(dynamic_parameters.values())  # The guard must prove at least one option has later prompts.
    for position, operation in enumerate(source_table, start=1):  # Check each endpoint in source order.
        value = str(position)  # The dynamic map is keyed by the one-based chooser value.
        expected = _expected_dynamic_parameters(operation.required)  # Build the expected prompt controls.
        actual = [  # Compare only the fields that define prompt order and control type.
            (param.get("param_type"), param.get("name"), param.get("label")) for param in dynamic_parameters[value]
        ]
        assert actual == expected  # The dynamic controls must preserve command-line prompt order.
        assert all(param.get("required") is True for param in dynamic_parameters[value])  # Required prompts gate Run.
