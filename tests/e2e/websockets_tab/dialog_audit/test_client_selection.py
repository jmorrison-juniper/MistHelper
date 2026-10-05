"""Verify client suggestions with isolated browser responses only."""

from __future__ import annotations

import json

import pytest

from tests.e2e.websockets_tab.dialog_audit.support.journeys import IsolatedPage

SITE_ID = IsolatedPage.SITE
EX_DEVICE_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000002"
SRX_DEVICE_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000003"
SSR_DEVICE_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000004"
CLIENT_ONE = "001122334455"
CLIENT_TWO = "001122334466"
CLIENT_RESOURCE = f"/api/websockets/sites/{SITE_ID}/devices/{{device_id}}/clients"


class ClientSelectionBrowser:
    """Drive isolated client-selection journeys through the real WebSocket page."""

    @staticmethod
    def approve_clients(policy, device_id: str, payload: dict[str, object]) -> str:
        """Add one exact synthetic client response to the local-only policy."""
        resource = CLIENT_RESOURCE.format(device_id=device_id)
        policy.responses[resource] = ("application/json", json.dumps(payload))
        return resource

    @staticmethod
    def unlock_utility(page, policy, key: str) -> None:
        """Unlock only the synthetic catalog entry to inspect its confirmation field."""
        resource = "/api/websockets/catalog"
        payload = json.loads(policy.responses[resource][1])
        for utility in payload["utilities"]:
            if utility["key"] == key:
                utility["locked"] = False
        policy.responses[resource] = ("application/json", json.dumps(payload))
        page.reload()

    @staticmethod
    def select_utility(page, key: str, device_id: str) -> None:
        """Select one operation, site, and family-filtered device."""
        page.set_default_timeout(2000)
        page.get_by_test_id("ws-catalog-entry-" + key).click()
        page.get_by_test_id("ws-field-site_id").select_option(SITE_ID)
        device = page.get_by_test_id("ws-field-device_id")
        device.locator(f'option[value="{device_id}"]').wait_for(state="attached")
        device.select_option(device_id)

    @staticmethod
    def clients() -> dict[str, object]:
        """Return two synthetic records scoped by the exact read response path."""
        return {
            "rows": [
                {"id": CLIENT_ONE, "label": "Printer", "detail": CLIENT_ONE, "family": "ex"},
                {"id": CLIENT_TWO, "label": "Printer", "detail": CLIENT_TWO, "family": "ex"},
            ],
            "total_count": 2,
            "reason": None,
        }


def test_ex_dhcp_picker_keeps_manual_and_selected_macs(audit_page) -> None:
    """EX DHCP suggestions remain optional and never start the utility."""
    page, policy = audit_page
    reads: list[str] = []
    page.on("request", lambda request: reads.append(request.url))
    ClientSelectionBrowser.unlock_utility(page, policy, "ex.releaseDhcpLeases")
    ClientSelectionBrowser.approve_clients(policy, EX_DEVICE_ID, ClientSelectionBrowser.clients())
    ClientSelectionBrowser.select_utility(page, "ex.releaseDhcpLeases", EX_DEVICE_ID)
    fields = page.locator("[data-ws-field]").evaluate_all(
        "(nodes) => nodes.map(node => [node.dataset.wsField, node.dataset.wsClientField, node.value])"
    )
    assert ["macs", "multiple", ""] in fields, fields
    assert any(url.endswith("/clients") for url in reads), reads
    options = page.get_by_test_id("ws-client-options")
    options.wait_for()
    manual = page.get_by_test_id("ws-field-macs")
    manual.fill("aabbccddeeff")
    options.select_option([CLIENT_ONE, CLIENT_TWO])
    page.get_by_test_id("ws-client-add").click()
    assert manual.input_value() == "aabbccddeeff"
    assert page.get_by_test_id("ws-client-selected").locator("button").count() == 2
    assert page.get_by_test_id("ws-confirmation-group").is_visible()
    page.get_by_test_id("ws-client-remove-" + CLIENT_ONE).focus()
    page.get_by_test_id("ws-client-remove-" + CLIENT_ONE).press("Enter")
    assert page.get_by_test_id("ws-client-selected").locator("button").count() == 1
    assert page.get_by_test_id("ws-client-remove-" + CLIENT_TWO).is_visible()
    assert policy.denied == []


def test_ex_mac_table_picker_keeps_manual_filter_editable(audit_page) -> None:
    """A selected MAC does not constrain the editable MAC-table filter."""
    page, policy = audit_page
    ClientSelectionBrowser.approve_clients(policy, EX_DEVICE_ID, ClientSelectionBrowser.clients())
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    options = page.get_by_test_id("ws-client-options")
    options.wait_for()
    manual = page.get_by_test_id("ws-field-mac_address")
    manual.fill("aabbccddeeff")
    options.select_option(CLIENT_ONE)
    page.get_by_test_id("ws-client-add").click()
    assert manual.input_value() == CLIENT_ONE
    assert page.get_by_test_id("ws-client-selected").inner_text().find(CLIENT_ONE) >= 0
    page.get_by_test_id("ws-client-remove-" + CLIENT_ONE).click()
    assert manual.input_value() == "aabbccddeeff", manual.get_attribute("data-ws-client-field")
    assert policy.denied == []


def test_keyboard_selection_adds_one_client(audit_page) -> None:
    """Keyboard selection adds a client without submitting the DHCP form."""
    page, policy = audit_page
    ClientSelectionBrowser.unlock_utility(page, policy, "ex.releaseDhcpLeases")
    ClientSelectionBrowser.approve_clients(policy, EX_DEVICE_ID, ClientSelectionBrowser.clients())
    ClientSelectionBrowser.select_utility(page, "ex.releaseDhcpLeases", EX_DEVICE_ID)
    options = page.get_by_test_id("ws-client-options")
    options.wait_for()
    options.focus()
    options.press("ArrowDown")
    options.press("Space")
    assert options.evaluate("(node) => Array.from(node.selectedOptions, option => option.value)") == [CLIENT_ONE]
    page.get_by_test_id("ws-client-add").focus()
    page.get_by_test_id("ws-client-add").press("Enter")
    assert page.get_by_test_id("ws-client-selected").inner_text().find(CLIENT_ONE) >= 0
    assert policy.denied == []


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (403, "Your session expired. Reload the page, then start the operation again."),
        (503, "The portal is restarting. Wait a moment, then try again."),
    ],
)
def test_http_errors_keep_manual_input(audit_page, status_code: int, message: str) -> None:
    """HTTP 4xx and 5xx replies stay visible without disabling manual input."""
    page, policy = audit_page
    resource = ClientSelectionBrowser.approve_clients(policy, EX_DEVICE_ID, {})
    policy.responses[resource] = (status_code, "application/json", "{}")
    ClientSelectionBrowser.select_utility(page, "ex.releaseDhcpLeases", EX_DEVICE_ID)
    status = page.get_by_test_id("ws-client-picker-status")
    page.wait_for_timeout(100)
    assert status.inner_text() == message
    manual = page.get_by_test_id("ws-field-macs")
    manual.fill("deadbeefcafe")
    assert manual.input_value() == "deadbeefcafe"
    options = page.get_by_test_id("ws-client-options")
    assert options.is_hidden()
    assert options.locator("option").count() == 0
    assert resource not in policy.denied


def test_empty_and_incomplete_results_preserve_manual_input(audit_page) -> None:
    """An empty list and a partial result have distinct, safe status text."""
    page, policy = audit_page
    resource = ClientSelectionBrowser.approve_clients(
        policy,
        EX_DEVICE_ID,
        {"rows": [], "total_count": 0, "reason": None},
    )
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    status = page.get_by_test_id("ws-client-picker-status")
    status.get_by_text("No clients are listed for this switch.").wait_for()
    manual = page.get_by_test_id("ws-field-mac_address")
    manual.fill("aabbccddeeff")
    policy.responses[resource] = (
        "application/json",
        json.dumps({"error": "Client results are incomplete.", "code": "incomplete_results"}),
    )
    page.get_by_test_id("ws-field-site_id").select_option("")
    page.get_by_test_id("ws-field-site_id").select_option(SITE_ID)
    device = page.get_by_test_id("ws-field-device_id")
    device.locator(f'option[value="{EX_DEVICE_ID}"]').wait_for(state="attached")
    device.select_option(EX_DEVICE_ID)
    status.get_by_text("Client results are incomplete.").wait_for()
    assert manual.input_value() == "aabbccddeeff"
    assert page.get_by_test_id("ws-client-options").is_hidden()
    assert policy.denied == []


def test_network_failure_keeps_manual_input(audit_page) -> None:
    """A failed local response reports a network error and retains the filter."""
    page, policy = audit_page
    resource = ClientSelectionBrowser.approve_clients(policy, EX_DEVICE_ID, {"rows": []})
    policy.delayed[resource] = []
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    page.wait_for_function(
        "document.querySelector('[data-testid=\"ws-client-picker-status\"]')?.textContent.includes('Loading')"
    )
    route, _, _ = policy.delayed[resource].pop()
    route.abort("failed")
    status = page.get_by_test_id("ws-client-picker-status")
    status.get_by_text("The portal did not answer. Check the network, then try again.").wait_for()
    manual = page.get_by_test_id("ws-field-mac_address")
    manual.fill("aa:bb:*")
    assert manual.input_value() == "aa:bb:*"
    assert page.get_by_test_id("ws-client-options").is_hidden()
    assert policy.denied == []


def test_late_device_response_cannot_replace_current_choices(audit_page) -> None:
    """A delayed response for an old switch cannot change the current list."""
    page, policy = audit_page
    devices_path = f"/api/websockets/sites/{SITE_ID}/devices"
    devices = json.loads(policy.responses[devices_path][1])
    second_device = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
    devices["rows"].append({"id": second_device, "label": "Second switch", "family": "ex"})
    policy.responses[devices_path] = ("application/json", json.dumps(devices))
    first_resource = ClientSelectionBrowser.approve_clients(
        policy, EX_DEVICE_ID, {"rows": [{"id": CLIENT_ONE, "label": "Old client", "family": "ex"}]}
    )
    policy.delayed[first_resource] = []
    current_resource = ClientSelectionBrowser.approve_clients(
        policy, second_device, {"rows": [{"id": CLIENT_TWO, "label": "Current client", "family": "ex"}]}
    )
    page.get_by_test_id("ws-catalog-entry-ex.retrieveMacTable").click()
    page.get_by_test_id("ws-field-site_id").select_option(SITE_ID)
    device = page.get_by_test_id("ws-field-device_id")
    device.locator(f'option[value="{EX_DEVICE_ID}"]').wait_for(state="attached")
    device.select_option(EX_DEVICE_ID)
    page.wait_for_function(
        "document.querySelector('[data-testid=\"ws-client-picker-status\"]')?.textContent.includes('Loading')"
    )
    page.wait_for_timeout(50)
    assert len(policy.delayed[first_resource]) == 1
    device.select_option(second_device)
    page.get_by_test_id("ws-client-options").locator(f'option[value="{CLIENT_TWO}"]').wait_for(state="attached")
    for route, content_type, body in policy.delayed[first_resource]:
        route.fulfill(status=200, content_type=content_type, body=body)
    assert page.get_by_test_id("ws-client-options").locator(f'option[value="{CLIENT_ONE}"]').count() == 0
    assert current_resource not in policy.denied
    assert policy.denied == []


@pytest.mark.parametrize(
    ("key", "device_id"),
    [
        ("srx.releaseDhcpLeases", SRX_DEVICE_ID),
        ("ssr.releaseDhcpLeases", SSR_DEVICE_ID),
    ],
)
def test_gateways_keep_manual_only_guidance(audit_page, key: str, device_id: str) -> None:
    """Gateway client choices stay off without proven device association."""
    page, policy = audit_page
    ClientSelectionBrowser.select_utility(page, key, device_id)
    page.get_by_test_id("ws-client-manual-guidance").get_by_text("Enter MAC addresses manually.").wait_for()
    assert page.get_by_test_id("ws-client-options").count() == 0
    assert page.get_by_test_id("ws-field-macs").is_editable()
    assert not any(method == "GET" for method in policy.denied)
    assert policy.transmitted == 0


def test_picker_timeout_and_late_reply_stay_unavailable(audit_page) -> None:
    """The ten-second bound wins over a late client response."""
    page, policy = audit_page
    resource = ClientSelectionBrowser.approve_clients(
        policy, EX_DEVICE_ID, {"rows": [{"id": CLIENT_ONE, "label": "Late client", "family": "ex"}]}
    )
    policy.delayed[resource] = []
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    status = page.get_by_test_id("ws-client-picker-status")
    status.get_by_text("Client suggestions are unavailable.").wait_for(timeout=12000)
    assert len(policy.delayed[resource]) == 1
    for route, content_type, body in policy.delayed[resource]:
        route.fulfill(status=200, content_type=content_type, body=body)
    assert status.inner_text() == "Client suggestions are unavailable."
    assert page.get_by_test_id("ws-client-options").is_hidden()
    assert page.get_by_test_id("ws-client-options").locator("option").count() == 0
    assert policy.denied == []


def test_site_change_clears_a_pending_lookup(audit_page) -> None:
    """Changing the site invalidates an outstanding client lookup."""
    page, policy = audit_page
    resource = ClientSelectionBrowser.approve_clients(
        policy, EX_DEVICE_ID, {"rows": [{"id": CLIENT_ONE, "label": "Old", "family": "ex"}]}
    )
    policy.delayed[resource] = []
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    page.wait_for_function(
        "document.querySelector('[data-testid=\"ws-client-picker-status\"]')?.textContent.includes('Loading')"
    )
    page.get_by_test_id("ws-field-site_id").select_option("")
    assert page.get_by_test_id("ws-client-picker-status").inner_text() == (
        "Choose a site and EX switch to load client suggestions."
    )
    for route, content_type, body in policy.delayed[resource]:
        route.fulfill(status=200, content_type=content_type, body=body)
    assert page.get_by_test_id("ws-client-options").locator("option").count() == 0
    assert policy.denied == []


def test_operation_change_uses_only_current_results(audit_page) -> None:
    """A late result from a previous operation cannot replace current choices."""
    page, policy = audit_page
    resource = ClientSelectionBrowser.approve_clients(
        policy, EX_DEVICE_ID, {"rows": [{"id": CLIENT_ONE, "label": "Old", "family": "ex"}]}
    )
    policy.delayed[resource] = []
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    page.wait_for_function(
        "document.querySelector('[data-testid=\"ws-client-picker-status\"]')?.textContent.includes('Loading')"
    )
    policy.responses[resource] = (
        "application/json",
        json.dumps({"rows": [{"id": CLIENT_TWO, "label": "Current", "family": "ex"}]}),
    )
    page.get_by_test_id("ws-catalog-entry-ex.releaseDhcpLeases").click()
    page.get_by_test_id("ws-field-site_id").select_option(SITE_ID)
    device = page.get_by_test_id("ws-field-device_id")
    device.locator(f'option[value="{EX_DEVICE_ID}"]').wait_for(state="attached")
    device.select_option(EX_DEVICE_ID)
    page.wait_for_function(
        "document.querySelector('[data-testid=\"ws-client-picker-status\"]')?.textContent.includes('Loading')"
    )
    assert len(policy.delayed[resource]) == 2
    old_route, old_type, old_body = policy.delayed[resource][0]
    old_route.fulfill(status=200, content_type=old_type, body=old_body)
    new_route, new_type, new_body = policy.delayed[resource][1]
    new_route.fulfill(status=200, content_type=new_type, body=new_body)
    page.get_by_test_id("ws-client-options").locator(f'option[value="{CLIENT_TWO}"]').wait_for(state="attached")
    assert page.get_by_test_id("ws-client-options").locator(f'option[value="{CLIENT_ONE}"]').count() == 0
    assert policy.transmitted == 0
    assert policy.denied == []


def test_operation_change_and_cancel_ignore_late_results(audit_page) -> None:
    """Operation changes and dialog cancellation reject prior discovery results."""
    page, policy = audit_page
    resource = ClientSelectionBrowser.approve_clients(
        policy, EX_DEVICE_ID, {"rows": [{"id": CLIENT_ONE, "label": "Old", "family": "ex"}]}
    )
    policy.delayed[resource] = []
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    page.wait_for_function(
        "document.querySelector('[data-testid=\"ws-client-picker-status\"]')?.textContent.includes('Loading')"
    )
    page.get_by_test_id("ws-cancel-selection-button").click()
    assert page.locator("[data-ws-client-field]").count() == 0
    for route, content_type, body in policy.delayed[resource]:
        route.fulfill(status=200, content_type=content_type, body=body)
    assert page.get_by_test_id("ws-client-options").count() == 0
    assert policy.transmitted == 0
    assert policy.denied == []


def test_selection_payload_is_unchanged_and_blocked_locally(audit_page) -> None:
    """A blocked local start body keeps the existing flat SDK parameter shape."""
    page, policy = audit_page
    ClientSelectionBrowser.unlock_utility(page, policy, "ex.releaseDhcpLeases")
    resource = ClientSelectionBrowser.approve_clients(policy, EX_DEVICE_ID, ClientSelectionBrowser.clients())
    ClientSelectionBrowser.select_utility(page, "ex.releaseDhcpLeases", EX_DEVICE_ID)
    page.get_by_test_id("ws-client-options").wait_for()
    page.get_by_test_id("ws-field-macs").fill("aabbccddeeff")
    page.get_by_test_id("ws-client-options").select_option(CLIENT_ONE)
    page.get_by_test_id("ws-client-add").click()
    assert page.get_by_test_id("ws-field-macs").input_value() == "aabbccddeeff"
    page.locator("#wsConfirmation").fill("EX switch")
    with page.expect_request(
        lambda request: request.method == "POST" and request.url.endswith("/api/websockets/sessions")
    ) as request_info:
        page.locator("#wsStartButton").click()
    body = json.loads(request_info.value.post_data or "{}")
    assert body["parameters"] == {"macs": "aabbccddeeff, " + CLIENT_ONE}
    assert body["targets"] == {"site_id": SITE_ID, "device_id": EX_DEVICE_ID}
    assert resource not in policy.denied
    assert policy.denied == ["POST"]
    assert policy.transmitted == 0


def test_mac_table_payload_keeps_single_optional_field(audit_page) -> None:
    """A blocked local start keeps the original single-string MAC-table field."""
    page, policy = audit_page
    ClientSelectionBrowser.approve_clients(policy, EX_DEVICE_ID, ClientSelectionBrowser.clients())
    ClientSelectionBrowser.select_utility(page, "ex.retrieveMacTable", EX_DEVICE_ID)
    page.get_by_test_id("ws-client-options").wait_for()
    page.get_by_test_id("ws-client-options").select_option(CLIENT_ONE)
    page.get_by_test_id("ws-client-add").click()
    assert page.get_by_test_id("ws-field-mac_address").input_value() == CLIENT_ONE
    with page.expect_request(
        lambda request: request.method == "POST" and request.url.endswith("/api/websockets/sessions")
    ) as request_info:
        page.get_by_test_id("ws-start-button").click()
    body = json.loads(request_info.value.post_data or "{}")
    assert body["parameters"] == {"mac_address": CLIENT_ONE}, body
    assert body["targets"] == {"site_id": SITE_ID, "device_id": EX_DEVICE_ID}
    assert policy.denied == ["POST"]
    assert policy.transmitted == 0


@pytest.mark.parametrize(
    ("key", "field_name"),
    [
        ("ex.releaseDhcpLeases", "macs"),
        ("ex.retrieveMacTable", "mac_address"),
    ],
)
def test_empty_optional_client_field_stays_omitted(audit_page, key: str, field_name: str) -> None:
    """An empty optional client field stays absent from the blocked request."""
    page, policy = audit_page
    if key == "ex.releaseDhcpLeases":
        ClientSelectionBrowser.unlock_utility(page, policy, key)
    ClientSelectionBrowser.select_utility(page, key, EX_DEVICE_ID)
    page.get_by_test_id("ws-field-" + field_name).wait_for()
    if key == "ex.releaseDhcpLeases":
        page.locator("#wsConfirmation").fill("EX switch")
    with page.expect_request(
        lambda request: request.method == "POST" and request.url.endswith("/api/websockets/sessions")
    ) as request_info:
        page.get_by_test_id("ws-start-button").click()
    body = json.loads(request_info.value.post_data or "{}")
    assert body["parameters"] == {}
    assert policy.denied == ["POST"]
    assert policy.transmitted == 0


def test_aggregate_stream_has_no_client_picker(audit_page) -> None:
    """Aggregate streams do not request or display device client choices."""
    page, policy = audit_page
    page.get_by_test_id("ws-catalog-entry-site.stats.clients").click()
    assert page.get_by_test_id("ws-client-options").count() == 0
    assert page.locator("[data-testid='ws-client-picker-status']").count() == 0
    assert policy.transmitted == 0
