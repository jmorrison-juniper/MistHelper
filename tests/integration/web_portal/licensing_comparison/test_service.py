"""Test Mist licensing comparison rules without live API credentials."""

from collections import deque
from types import SimpleNamespace
from typing import Any

import pytest

import src.interfaces.portals.licensing_comparison.api as licensing_api
from src.interfaces.portals.licensing_comparison.api import MistApiRequester, OrganizationDataReader, ServiceContext
from src.interfaces.portals.licensing_comparison.service import LicensingComparisonService
from src.interfaces.portals.licensing_comparison.validation import ManualRowValidator, OrganizationIdValidator

API_SESSION = object()  # Use one test session marker to prove that the service shares it.


class StubMistApi:
    """Replace Mist SDK calls with ordered response records."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, responses: dict[str, Any]) -> None:
        """Patch each SDK method and disable network pacing for deterministic tests."""
        self.responses = responses  # Keep each operation's prepared response.
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []  # Record SDK arguments.
        for module, operation in (
            (licensing_api.self_api, "getSelf"),
            (licensing_api.msp_orgs_api, "listMspOrgs"),
            (licensing_api.licenses_api, "getOrgLicensesSummary"),
            (licensing_api.licenses_api, "getOrgLicensesBySite"),
            (licensing_api.inventory_api, "getOrgInventory"),
            (licensing_api.license_types_api, "listLicenseTypes"),
        ):  # Patch only the SDK methods used by this service.
            self._patch_method(monkeypatch, module, operation)  # Route the call to the fixture response.
        monkeypatch.setattr(
            licensing_api.RateLimitingUtils,
            "get_rate_limited_delay",
            lambda *_arguments: (None, 0.0),
        )  # Prevent shared rate-limit state from sleeping in tests.

    def _patch_method(self, monkeypatch: pytest.MonkeyPatch, module: Any, operation: str) -> None:
        """Bind one SDK function to the ordered stub response."""
        monkeypatch.setattr(
            module,
            operation,
            lambda *arguments, _operation=operation, **keywords: self._respond(_operation, arguments, keywords),
        )  # Capture each SDK call with its explicit test response.

    def _respond(self, operation: str, arguments: tuple[Any, ...], keywords: dict[str, Any]) -> Any:
        """Record one call and return its next prepared response."""
        self.calls.append((operation, arguments, keywords))  # Retain arguments for contract assertions.
        response = self.responses[operation]  # Read the fixture result for this method.
        if isinstance(response, deque):  # A queue models retries and page reads.
            return response.popleft()  # Return one response in the prepared sequence.
        if callable(response):  # A callback can inspect page parameters.
            return response(*arguments, **keywords)  # Build the response from the request.
        return response  # Reuse a single response for the method.


def api_response(status: int, data: Any, next_page: str | None = None) -> Any:
    """Build the small response shape used by the installed SDK."""
    return SimpleNamespace(status_code=status, data=data, next=next_page)  # Model the SDK response fields.


def direct_profile() -> Any:
    """Provide one direct organization grant for request tests."""
    return api_response(200, {"privileges": []})  # Avoid MSP discovery unless a test requests it.


def service_for_test(session_available: bool = True) -> LicensingComparisonService:
    """Build a service with a synthetic Mist session and no production values."""
    return LicensingComparisonService(
        ServiceContext(API_SESSION if session_available else None, "org-1", "Primary", {})
    )  # Use only a process-local session marker.


@pytest.mark.parametrize("failure_status", [400, 503])
def test_http_client_and_server_errors_remain_visible(monkeypatch: pytest.MonkeyPatch, failure_status: int) -> None:
    """Keep 4xx and 5xx responses visible as partial organization results."""
    StubMistApi(
        monkeypatch,
        {
            "getSelf": direct_profile(),
            "getOrgLicensesSummary": api_response(failure_status, {"error": "synthetic"}),
            "getOrgLicensesBySite": api_response(200, []),
            "getOrgInventory": api_response(200, []),
        },
    )  # Keep every request inside the in-memory SDK stub.
    payload, error, status = service_for_test().compare(["org-1"], [], {})  # Compare one authorized organization.
    assert error is None  # The service returns readable partial results for request failures.
    assert status == 200  # A partial Mist result remains a valid comparison response.
    assert payload["results"][0]["request_status"] == "partial"  # Do not hide the failed endpoint.
    assert payload["results"][0]["license_summary"]["status_code"] == failure_status  # Preserve the HTTP status.


def test_rejects_organization_outside_the_active_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an organization before any organization-specific API request."""
    api = StubMistApi(monkeypatch, {"getSelf": direct_profile()})  # Expose only the configured direct organization.
    payload, error, status = service_for_test().compare(["org-2"], [], {})  # Request an inaccessible organization.
    assert payload is None  # Do not return comparison data for a denied organization.
    assert status == 403  # Return an explicit authorization failure.
    assert error == (
        "The request includes an organization that this session cannot access."
    )  # Explain the access denial.
    assert [call[0] for call in api.calls] == ["getSelf"]  # Stop before license or inventory reads.


def test_discovers_organizations_from_a_granted_msp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read MSP organizations only when the active profile grants an MSP ID."""
    StubMistApi(
        monkeypatch,
        {
            "getSelf": api_response(200, {"privileges": [{"msp_id": "msp-1"}]}),
            "listMspOrgs": api_response(200, [{"id": "org-2", "name": "Managed"}]),
        },
    )  # Provide an explicit MSP grant and its organization list.
    choices, errors = service_for_test().discover_organizations()  # Discover direct and managed organizations.
    sources = {choice["org_id"]: choice["source"] for choice in choices}  # Index each authorized source.
    assert sources == {"org-1": "direct", "org-2": "msp"}  # Keep both authorized organizations.
    assert errors == []  # Successful profile and MSP reads have no discovery errors.


def test_missing_session_stops_before_sdk_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return a service-unavailable response when the portal has no Mist session."""
    api = StubMistApi(monkeypatch, {})  # Install spies without preparing any Mist responses.
    payload, error, status = service_for_test(False).compare([], [], {})  # Run validation without a session.
    assert payload is None  # Do not report a comparison without Mist access.
    assert status == 503  # Identify the unavailable shared session.
    assert error == "The Mist API session is unavailable."  # Give the operator the exact failure reason.
    assert api.calls == []  # Stop before discovery or organization requests.


def test_retries_one_rate_limit_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retry exactly once after an HTTP 429 response."""
    api = StubMistApi(
        monkeypatch,
        {
            "getSelf": direct_profile(),
            "getOrgLicensesSummary": deque([api_response(429, {}), api_response(200, {"summary": {}})]),
            "getOrgLicensesBySite": api_response(200, []),
            "getOrgInventory": api_response(200, []),
        },
    )  # Model one 429 response followed by a successful retry.
    waits: list[int] = []  # Record the retry delay without waiting in real time.
    monkeypatch.setattr(licensing_api.time, "sleep", waits.append)  # Replace sleep with an observation.
    payload, error, status = service_for_test().compare(["org-1"], [], {})  # Run the normal comparison flow.
    summary_calls = [call for call in api.calls if call[0] == "getOrgLicensesSummary"]  # Count summary attempts.
    assert status == 200  # The retry allows the comparison to complete.
    assert error is None  # A successful retry does not report a final request error.
    assert len(summary_calls) == 2  # The service performs only one retry.
    assert waits == [60]  # The retry follows the required delay.
    assert payload["results"][0]["request_status"] == "success"  # Report the final endpoint status.
    assert all(call[1][0] is API_SESSION for call in api.calls)  # Reuse the active session for every Mist request.


def test_reads_all_inventory_pages_using_installed_page_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read all inventory pages with the SDK's explicit limit and page arguments."""
    page_records = [
        [{"serial": f"serial-{index}"} for index in range(1000)],
        [{"serial": "last"}],
    ]  # Prepare two pages.
    api = StubMistApi(
        monkeypatch,
        {"getOrgInventory": deque([api_response(200, page_records[0], "/next"), api_response(200, page_records[1])])},
    )  # Make the first page advertise a next page.
    context = ServiceContext(API_SESSION, "org-1", "Primary", {})  # Reuse the synthetic session context.
    requester = MistApiRequester(context)  # Apply the production request policy.
    result = OrganizationDataReader(context, requester).read_inventory("org-1")  # Read pages for contract assertions.
    page_calls = [call for call in api.calls if call[0] == "getOrgInventory"]  # Collect inventory requests.
    assert result.succeeded is True  # Both pages completed with HTTP 2xx.
    assert len(result.data) == 1001  # Preserve every inventory record across the two pages.
    assert [call[2]["page"] for call in page_calls] == [1, 2]  # Request pages in ascending order.
    assert all(call[2]["limit"] == 1000 for call in page_calls)  # Use the shared Mist page size.


def test_calculates_catalog_bundle_component_balances(monkeypatch: pytest.MonkeyPatch) -> None:
    """Calculate bundle components from Mist catalog metadata, not fixed values."""
    StubMistApi(
        monkeypatch,
        {
            "getSelf": direct_profile(),
            "listLicenseTypes": api_response(
                200,
                [{"name": "SUB-AI", "key": "sub_ai", "includes": ["sub_eng", "sub_wifi", "sub_wifi"]}],
            ),
            "getOrgLicensesSummary": api_response(200, {"summary": {"SUB_AI": 2, "SUB_ENG": 3, "SUB_WIFI": 4}}),
            "getOrgLicensesBySite": api_response(200, []),
            "getOrgInventory": api_response(200, []),
        },
    )  # Return a catalog bundle with a repeated component.
    payload, error, status = service_for_test().compare(
        ["org-1"], [], {"org-1": {"SUB-AI": 5}}
    )  # Compare purchased bundles with Mist usage.
    balance = payload["results"][0]["balances"][0]  # Read the purchased bundle result.
    components = {item["license_type"]: item for item in balance["bundle_components"]}  # Index included license types.
    assert status == 200  # Complete Mist reads produce a complete comparison.
    assert error is None  # Valid catalog-backed purchase data is accepted.
    assert balance["remaining_count"] == 3  # Subtract the organization bundle use.
    assert components["SUB-ENG"]["remaining_count"] == 2  # Count one engineering license per bundle.
    assert components["SUB-WIFI"]["purchased_count"] == 10  # Count repeated Wi-Fi entries from the catalog.
    assert components["SUB-WIFI"]["remaining_count"] == 6  # Subtract the component use from the expanded total.


def test_missing_purchase_amounts_do_not_create_false_balances(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Leave balances empty when the operator has no purchase values."""
    api = StubMistApi(
        monkeypatch,
        {
            "getSelf": direct_profile(),
            "getOrgLicensesSummary": api_response(200, {"summary": {"SUB-AI": 2}}),
            "getOrgLicensesBySite": api_response(200, []),
            "getOrgInventory": api_response(200, []),
        },
    )  # Return usage data without purchased counts.
    payload, error, status = service_for_test().compare(["org-1"], [], {})  # Omit purchase entries.
    assert status == 200  # Missing operator values do not block the comparison.
    assert error is None  # The API reads succeed.
    assert payload["results"][0]["balances"] == []  # Do not infer purchased amounts or remaining balances.
    assert not any(call[0] == "listLicenseTypes" for call in api.calls)  # Skip catalog access without purchases.


def test_rejects_fractional_manual_license_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject fractional operator counts before reading comparison endpoints."""
    api = StubMistApi(monkeypatch, {"getSelf": direct_profile()})  # Permit discovery but no data reads.
    payload, error, status = service_for_test().compare(
        [],
        [{"row_id": "manual-one", "name": "Manual", "licenses": {"SUB-AI": 1.5}}],
        {},
    )  # Submit a non-whole license amount.
    assert payload is None  # Do not compare malformed operator data.
    assert status == 400  # Report an input validation error.
    assert error == (
        "Manual license and inventory counts must be non-negative whole numbers."
    )  # Identify the invalid count.
    assert [call[0] for call in api.calls] == ["getSelf"]  # Avoid license reads after validation fails.


@pytest.mark.parametrize(
    ("rows", "expected_error"),
    [
        (None, "Manual rows must be a list."),
        ([None], "Each manual row must be an object."),
        ([{"row_id": "invalid", "name": "Manual"}], "Each manual row needs a valid row_id."),
        ([{"row_id": "manual-one", "name": " "}], "Each manual row needs a name of 1 to 120 characters."),
        (
            [{"row_id": "manual-one", "name": "Manual", "licenses": {"SUB-AI": -1}}],
            "Manual license and inventory counts must be non-negative whole numbers.",
        ),
    ],
)
def test_manual_row_validation_rejects_invalid_shapes(rows: Any, expected_error: str) -> None:
    """Reject malformed manual rows before the comparison uses their data."""
    clean_rows, error = ManualRowValidator.validate_manual_rows(rows, [])
    assert clean_rows == []
    assert error == expected_error


def test_manual_row_validation_rejects_duplicate_names_and_identifiers() -> None:
    """Prevent manual rows from shadowing accessible organizations or each other."""
    choices = [{"org_id": "org-1", "name": "Primary", "source": "direct"}]
    rows = [{"row_id": "manual-one", "name": "Primary"}]
    clean_rows, name_error = ManualRowValidator.validate_manual_rows(rows, choices)
    duplicate_rows = [
        {"row_id": "manual-one", "name": "Office"},
        {"row_id": "manual-one", "name": "Second office"},
    ]
    duplicate_result, identifier_error = ManualRowValidator.validate_manual_rows(duplicate_rows, [])
    assert clean_rows == []
    assert name_error == "Manual organization names must be unique."
    assert duplicate_result == []
    assert identifier_error == "Manual row identifiers must be unique."


@pytest.mark.parametrize(
    ("purchases", "expected_error"),
    [
        (None, "Purchased amounts must be an object."),
        ({"org-2": {"SUB-AI": 1}}, "Purchased amounts name an organization that is not in this comparison."),
        (
            {"org-1": {"SUB-AI": 1.5}},
            "Purchased amounts must use supported license names and non-negative whole numbers.",
        ),
    ],
)
def test_purchase_validation_rejects_invalid_values(purchases: Any, expected_error: str) -> None:
    """Reject purchase data that uses invalid organizations or counts."""
    clean_purchases, error = ManualRowValidator.validate_purchases(purchases, {"org-1"})
    assert clean_purchases == {}
    assert error == expected_error


def test_organization_id_validation_rejects_invalid_and_duplicate_values() -> None:
    """Reject non-string organization IDs and duplicate selections."""
    invalid_ids, invalid_error = OrganizationIdValidator.validate(["org-1", None])
    duplicate_ids, duplicate_error = OrganizationIdValidator.validate(["org-1", "org-1"])
    assert invalid_ids is None
    assert invalid_error == "Organization IDs must be a list of non-empty strings."
    assert duplicate_ids is None
    assert duplicate_error == "The organization list contains duplicate IDs."
