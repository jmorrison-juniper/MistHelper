"""Guard the portal controls that answer required plain prompts."""

from __future__ import annotations  # Keep annotations lazy for the Python test runtime.

import sys  # Add the repository root when pytest starts from another directory.
from pathlib import Path  # Resolve the repository root without a hardcoded separator.

import pytest  # Parametrize the menu checks so each row reports its own failure.

REPO_ROOT = Path(__file__).resolve().parents[3]  # Locate the checkout from this test file.
if str(REPO_ROOT) not in sys.path:  # Make direct pytest invocation behave like the CI runner.
    sys.path.insert(0, str(REPO_ROOT))  # Let imports find local packages before installed packages.

from src.export.count_exporter import _MSP_OPS as COUNT_MSP_OPS  # noqa: E402
from src.export.count_exporter import _ORG_OPS as COUNT_ORG_OPS  # noqa: E402
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

ENDPOINT_FAMILY_MENUS = ("263", "264", "265", "266", "267", "268")  # These rows have dynamic prompts.


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


@pytest.mark.parametrize("menu", ENDPOINT_FAMILY_MENUS)  # Check each dynamic endpoint family row.
def test_endpoint_family_rows_are_cli_only(menu: str) -> None:
    """Endpoint family rows hide Run until the browser models per-choice prompts."""
    entry = PARAMETER_REGISTRY[menu]  # Read the row state that the browser consumes.
    assert entry["category"] == "cli_only"  # The operator must not be offered a run that cannot succeed.
    assert entry["parameters"] == []  # A fixed control list cannot answer a dynamic prompt sequence.
    assert "per-choice prompts" in entry["cli_only_message"]  # The message must name the exact limitation.
    assert f"python MistHelper.py --menu {menu}" in entry["cli_only_message"]  # The message must give the CLI path.
