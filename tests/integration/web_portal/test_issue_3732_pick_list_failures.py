"""Prove that issue #3732 distinguishes failed portal reads from valid empty results."""

from __future__ import annotations  # Keep modern annotations compatible with runtime imports.

import sys  # Install the fake mistapi module for route-local imports.
from types import ModuleType, SimpleNamespace  # Build the minimum installed SDK shape.
from unittest.mock import ANY, MagicMock  # Match the session object and record each fake SDK endpoint call.

import pytest  # Provide fixtures and parameterized picker cases.
import requests  # Block external Requests traffic during every feature test.
from flask import Flask  # Exercise the production Blueprint through a local test client.
from flask.testing import FlaskClient  # Type the local portal client fixture.

from web_portal.routes.operations import (
    API_ERROR_REASON,  # Assert the exact operator retry message.
    NO_ROWS_REASON,  # Preserve the ordinary valid-empty message.
    operations_bp,  # Register the production picker routes in the local app.
)


class FakeResponse:
    """Represent one local mistapi response without credentials or network traffic."""

    def __init__(self, status_code: object, data: object) -> None:
        """Store the response fields that the production picker reads."""
        self.status_code = status_code  # Supply a usable, missing, or invalid HTTP status.
        self.data = data  # Supply local rows without any cloud request.


class FakeMistSdk:
    """Expose the four installed mistapi endpoints used by the reserved pickers."""

    def __init__(self) -> None:
        """Build local endpoint mocks with valid empty responses by default."""
        self.list_sites = MagicMock(return_value=FakeResponse(200, []))  # Model a valid empty site answer.
        self.list_devices = MagicMock(return_value=FakeResponse(200, []))  # Model a valid empty device answer.
        self.wireless = MagicMock(return_value=FakeResponse(200, {"results": []}))  # Model valid empty wireless data.
        self.wired = MagicMock(return_value=FakeResponse(200, {"results": []}))  # Model valid empty wired data.

    def module(self) -> ModuleType:
        """Return a module that matches the installed mistapi attribute paths."""
        module = ModuleType("mistapi")  # Let route-local import use this fake instead of the installed SDK.
        module.api = SimpleNamespace(  # Build only the API namespace that the portal calls.
            v1=SimpleNamespace(  # Match the installed versioned API namespace.
                orgs=SimpleNamespace(sites=SimpleNamespace(listOrgSites=self.list_sites)),  # Keep the org endpoint.
                sites=SimpleNamespace(  # Keep the three site endpoint groups.
                    devices=SimpleNamespace(listSiteDevices=self.list_devices),  # Keep the device endpoint.
                    clients=SimpleNamespace(searchSiteWirelessClients=self.wireless),  # Keep the wireless endpoint.
                    wired_clients=SimpleNamespace(searchSiteWiredClients=self.wired),  # Keep the wired endpoint.
                ),
            )
        )
        return module  # Give the local route import the complete fake SDK shape.

    def set_failure(self, picker: str, status: object) -> None:
        """Set one picker source to a local failed response."""
        data = {"results": []} if picker in {"wireless", "wired"} else []  # Match each SDK response shape.
        endpoints = {  # Map route names to the fake installed SDK methods.
            "sites": self.list_sites,  # The organization site picker uses listOrgSites.
            "devices": self.list_devices,  # The site device picker uses listSiteDevices.
            "wireless": self.wireless,  # The wireless source uses searchSiteWirelessClients.
            "wired": self.wired,  # The wired source uses searchSiteWiredClients.
        }
        endpoints[picker].return_value = FakeResponse(status, data)  # Replace only the selected source.


@pytest.fixture(autouse=True)
def block_live_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test if production code attempts any live Requests call."""

    def refuse_request(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Issue #3732 tests permit no live HTTP request.")  # Stop any network escape.

    monkeypatch.setattr(requests.sessions.Session, "request", refuse_request)  # Guard every Requests session.


@pytest.fixture
def portal(monkeypatch: pytest.MonkeyPatch) -> tuple[FlaskClient, FakeMistSdk]:
    """Return a local Flask client and fake SDK for the picker routes."""
    sdk = FakeMistSdk()  # Build local endpoint responses with no credentials.
    monkeypatch.setitem(sys.modules, "mistapi", sdk.module())  # Redirect every route-local SDK import.
    app = Flask(__name__)  # Build an isolated local application for the production Blueprint.
    app.config.update(TESTING=True, APISESSION=object(), ORG_ID="org-local")  # Supply non-secret local identifiers.
    app.register_blueprint(operations_bp)  # Exercise the production route and response serialization.
    return app.test_client(), sdk  # Give each test isolated endpoint mocks and application state.


def _route_for(picker: str) -> str:
    """Return the local portal route that exercises one picker source."""
    if picker == "sites":  # The site route includes the filter override to avoid a second SDK read.
        return "/api/operations/sites?show_empty=1"
    if picker == "devices":  # The device route verifies the default all-device request.
        return "/api/operations/sites/site-local/devices?type=all"
    return "/api/operations/sites/site-local/clients"  # Both client sources share one route response.


def _response_key(picker: str) -> str:
    """Return the JSON row key for one picker route."""
    return picker if picker in {"sites", "devices"} else "clients"  # Client sources merge into one list.


class TestFailedPickerStatuses:
    """Prove that missing and refused responses use the retry message."""

    @pytest.mark.parametrize("status", [None, 400, 500, 302, "unknown"])
    @pytest.mark.parametrize("picker", ["sites", "devices", "wireless", "wired"])
    def test_failed_status_uses_the_reachability_reason(
        self, portal: tuple[FlaskClient, FakeMistSdk], picker: str, status: object
    ) -> None:
        """Each unusable source returns an explicit failed-read result."""
        client, sdk = portal  # Read the isolated portal and local SDK.
        sdk.set_failure(picker, status)  # Give only the selected picker an unusable response.
        response = client.get(_route_for(picker))  # Exercise the production route with no live HTTP call.
        body = response.get_json()  # Read the local JSON result for operator-facing assertions.
        assert response.status_code == 200  # The list route keeps its existing HTTP response contract.
        assert body[_response_key(picker)] == []  # List compatibility remains intact for a failed read.
        assert body["reason"] == API_ERROR_REASON  # The operator learns that the portal could not reach Mist.
        assert body["reason"] != NO_ROWS_REASON  # A failed read cannot look like a valid empty answer.

    def test_failure_log_names_operation_target_and_status(
        self, portal: tuple[FlaskClient, FakeMistSdk], caplog: pytest.LogCaptureFixture
    ) -> None:
        """The failed read log contains useful non-secret context."""
        client, sdk = portal  # Read the isolated portal and local SDK.
        sdk.set_failure("devices", 503)  # Model one refused device picker response.
        client.get(_route_for("devices"))  # Exercise the production failure log path.
        assert "listSiteDevices" in caplog.text  # The log names the failed SDK operation.
        assert "site-local" in caplog.text  # The log names the non-secret selected target.
        assert "503" in caplog.text  # The log names the unusable response status.


class TestValidEmptyPickerStatuses:
    """Prove that empty HTTP 2xx answers remain ordinary empty results."""

    @pytest.mark.parametrize("picker", ["sites", "devices", "wireless"])
    def test_valid_empty_response_keeps_the_no_rows_reason(
        self, portal: tuple[FlaskClient, FakeMistSdk], picker: str
    ) -> None:
        """An empty successful response does not become a reachability failure."""
        client, _sdk = portal  # Read the isolated portal with valid empty defaults.
        response = client.get(_route_for(picker))  # Exercise the production route with local fake data.
        body = response.get_json()  # Read the local JSON result for operator-facing assertions.
        assert body[_response_key(picker)] == []  # The successful response contains no rows.
        assert body["reason"] == NO_ROWS_REASON  # The operator receives the ordinary empty-result message.
        assert body["reason"] != API_ERROR_REASON  # A valid HTTP answer is not a reachability failure.


class TestClientSourceMerging:
    """Prove that one valid client source can survive the other source failure."""

    def test_wireless_rows_survive_a_wired_failure(self, portal: tuple[FlaskClient, FakeMistSdk]) -> None:
        """Valid wireless rows remain available when the wired read fails."""
        client, sdk = portal  # Read the isolated portal and local SDK.
        sdk.wireless.return_value = FakeResponse(200, {"results": [{"mac": "aa", "hostname": "alpha"}]})  # Add rows.
        sdk.set_failure("wired", None)  # Fail only the wired source before an HTTP status exists.
        body = client.get(_route_for("wireless")).get_json()  # Exercise the production client merger.
        assert body["clients"][0]["type"] == "wireless"  # Keep the valid source row and its existing label.
        assert "reason" not in body  # A populated picker does not return a success-shaped failure reason.

    def test_wired_rows_survive_a_wireless_failure(self, portal: tuple[FlaskClient, FakeMistSdk]) -> None:
        """Valid wired rows remain available when the wireless read fails."""
        client, sdk = portal  # Read the isolated portal and local SDK.
        sdk.set_failure("wireless", 500)  # Fail only the wireless source with an HTTP refusal.
        sdk.wired.return_value = FakeResponse(200, {"results": [{"mac": "bb", "hostname": "beta"}]})  # Add rows.
        body = client.get(_route_for("wired")).get_json()  # Exercise the production client merger.
        assert body["clients"][0]["type"] == "wired"  # Keep the valid source row and its existing label.
        assert "reason" not in body  # A populated picker reports rows instead of an empty failure.

    def test_both_valid_empty_sources_return_no_rows(self, portal: tuple[FlaskClient, FakeMistSdk]) -> None:
        """Two valid empty client answers remain an ordinary empty result."""
        client, _sdk = portal  # Read the isolated portal with valid empty client defaults.
        body = client.get(_route_for("wireless")).get_json()  # Exercise both local client sources.
        assert body["clients"] == []  # The merged valid result contains no rows.
        assert body["reason"] == NO_ROWS_REASON  # The existing valid-empty reason remains intact.


class TestSdkEndpointContract:
    """Prove that the routes still use the installed mistapi endpoint names."""

    def test_each_picker_uses_only_the_fake_sdk_endpoint(self, portal: tuple[FlaskClient, FakeMistSdk]) -> None:
        """The feature keeps all four SDK methods and makes no direct HTTP call."""
        client, sdk = portal  # Read the isolated portal and local SDK.
        client.get(_route_for("sites"))  # Exercise the organization site picker.
        client.get(_route_for("devices"))  # Exercise the site device picker.
        client.get(_route_for("wireless"))  # Exercise both site client sources.
        sdk.list_sites.assert_called_once_with(ANY, "org-local")  # Keep the organization SDK call.
        sdk.list_devices.assert_called_once_with(ANY, site_id="site-local", type="all")  # Keep all devices.
        sdk.wireless.assert_called_once_with(ANY, "site-local")  # Keep the wireless SDK call.
        sdk.wired.assert_called_once_with(ANY, "site-local")  # Keep the wired SDK call.
