"""Browser proofs for accessible names on the Operations page."""

from __future__ import annotations

import logging
import socket
import threading
from collections.abc import Iterator
from typing import Any

import pytest

logger = logging.getLogger(__name__)

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

READY_TIMEOUT_MS = 15000
STATIC_CONTROLS = (
    ("#opSearch", "Search operations"),
    ("#resultsFileSelect", "Select a result file"),
    ("#resultsSearch", "Filter result rows"),
    ("#dataPreviewSearch", "Search preview rows"),
)
DYNAMIC_MENUS = tuple(str(menu_number) for menu_number in range(257, 269))


def free_port() -> int:
    """Return an available loopback port for the test server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def portal_url(flask_app: Any) -> Iterator[str]:
    """Serve the Flask application for browser accessibility checks."""
    from werkzeug.serving import make_server

    port = free_port()
    server = make_server("127.0.0.1", port, flask_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the accessibility test server on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        logger.info("Stopping the accessibility test server on port %d", port)
        server.shutdown()
        thread.join(timeout=10)


@pytest.fixture
def operations_page(page: Any, portal_url: str) -> Any:
    """Return the rendered Operations page after its operation list loads."""
    page.set_viewport_size({"width": 402, "height": 874})
    page.goto(f"{portal_url}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.wait_for_selector(".op-item", state="attached", timeout=READY_TIMEOUT_MS)
    return page


def test_static_controls_have_programmatic_names(operations_page: Any) -> None:
    """Each existing static control must use a label or an ARIA label."""
    present_count = 0
    for selector, expected_name in STATIC_CONTROLS:
        control = operations_page.locator(selector)
        assert control.count() == 1, f"{selector} is absent, so the accessibility proof measures nothing."
        present_count += 1
        name_source = control.evaluate(
            "element => ({"
            "labelCount: element.labels ? element.labels.length : 0,"
            "ariaLabel: element.getAttribute('aria-label') || ''"
            "})"
        )
        assert (
            name_source["labelCount"] > 0 or name_source["ariaLabel"] == expected_name
        ), f"{selector} has no label or expected aria-label. A placeholder does not satisfy this proof."
    print(f"The static accessibility proof examined {present_count} Operations controls.")
    assert present_count == len(STATIC_CONTROLS)


def assert_generated_labels(page: Any) -> int:
    """Check each generated control against its visible sibling label."""
    controls = page.locator("#parameterFields select, #parameterFields input")
    records = controls.evaluate_all(
        "elements => elements.map(element => ({"
        "id: element.id,"
        "name: element.name,"
        "labelCount: element.labels.length,"
        "labelFor: element.parentElement.querySelector('label').htmlFor,"
        "labelText: element.parentElement.querySelector('label').textContent.trim()"
        "}))"
    )
    assert len(records) > 0, "No generated controls were examined."
    assert len({record["id"] for record in records}) == len(records), "Generated control IDs are not unique."
    assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
    for record in records:
        assert record["id"] == "param-" + record["name"]
        assert record["labelCount"] == 1, f"{record['id']} must have exactly one associated label."
        assert record["labelFor"] == record["id"], f"{record['id']} does not match its visible label."
        assert record["labelText"] != "", f"{record['id']} has an empty visible label."
    return len(records)


@pytest.mark.parametrize("menu_number", DYNAMIC_MENUS)
def test_generated_controls_have_programmatic_names(operations_page: Any, menu_number: str) -> None:
    """Every endpoint replacement must retain the visible label association."""
    operation = operations_page.locator(f'.op-item[data-menu="{menu_number}"]')
    assert operation.count() == 1, f"Menu {menu_number} is absent, so the accessibility proof measures nothing."
    operation.evaluate("element => element.click()")
    operations_page.wait_for_selector("#parameterFields select, #parameterFields input", state="attached")
    examined_count = assert_generated_labels(operations_page)
    chooser = operations_page.locator("#param-endpoint_operation")
    if chooser.count() == 1:
        choice_count = chooser.locator("option").count()
        assert choice_count > 1, f"Menu {menu_number} has no endpoint choices."
        for index in range(1, choice_count):
            chooser.select_option(index=index)
            examined_count += assert_generated_labels(operations_page)
        chooser.select_option(index=0)
        examined_count += assert_generated_labels(operations_page)
        assert operations_page.locator("[data-dynamic-parent]").count() == 0
    print(f"The dynamic accessibility proof examined {examined_count} controls for menu {menu_number}.")


@pytest.mark.parametrize("parameter_type", ("choice", "text", "number"))
def test_generated_label_preserves_control_contract(operations_page: Any, parameter_type: str) -> None:
    """Label association must preserve defaults, dependencies, and submitted answers."""
    operations_page.locator('.op-item[data-menu="257"]').evaluate("element => element.click()")
    operations_page.wait_for_selector("#parameterFields select", state="visible")
    result = operations_page.evaluate(
        """parameterType => {
            const parameter = {name: 'label_probe', label: 'Probe', param_type: parameterType,
                required: true, default: '7', depends_on: 'parent', options: [{value: '7', label: 'Seven'}]};
            const group = buildParameterGroup(parameter);
            document.getElementById('parameterFields').appendChild(group);
            currentParameters = [parameter];
            const control = group.querySelector('select, input');
            const label = group.querySelector('label');
            const hidden = group.style.display === 'none';
            handleDependencyChange('parent', 'selected');
            const shown = group.style.display === '';
            label.click();
            return {id: control.id, name: control.name, value: control.value, required: control.required,
                labelFor: label.htmlFor, labelText: label.textContent.trim(), hidden, shown,
                focused: document.activeElement === control, answers: collectInputAnswers()};
        }""",
        parameter_type,
    )
    assert result == {
        "id": "param-label_probe",
        "name": "label_probe",
        "value": "7",
        "required": True,
        "labelFor": "param-label_probe",
        "labelText": "Probe *",
        "hidden": True,
        "shown": True,
        "focused": True,
        "answers": ["7"],
    }
