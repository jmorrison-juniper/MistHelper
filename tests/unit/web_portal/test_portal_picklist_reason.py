"""Tests that an empty selector always names the reason it is empty.

Issue #3163 reported a site picker that answered HTTP 200 with an empty
list and no explanation. The control rendered blank, and an operator read
that blank control as a stalled portal. The real causes differ. The portal
may hold no API session, it may hold no organization identifier, the Mist
API may have failed, or the organization may truly hold no site.

These tests hold the explanation in place for all three selectors.
"""

import pytest

from web_portal.routes.operations import (
    API_ERROR_REASON,
    NO_ORG_REASON,
    NO_ROWS_REASON,
    NO_SESSION_REASON,
    NO_SITE_REASON,
    PickList,
    _fetch_org_sites,
    _fetch_site_clients,
    _fetch_site_devices,
    _pick_list_payload,
)


class TestThePickListType:
    """The result type stays a list, so every existing reader keeps working."""

    def test_an_empty_pick_list_equals_an_empty_list(self):
        """A reader that compares against [] still works."""
        assert PickList(reason="any reason") == []  # The old contract must survive.

    def test_a_filled_pick_list_equals_a_plain_list(self):
        """A reader that compares against a plain list still works."""
        assert PickList([{"id": "a"}]) == [{"id": "a"}]  # The old contract must survive.

    def test_a_pick_list_reports_its_length(self):
        """A reader that calls len() still works."""
        assert len(PickList([1, 2, 3])) == 3  # The routes size the control from this count.

    def test_a_pick_list_carries_its_reason(self):
        """The new attribute holds the explanation."""
        assert PickList(reason=NO_ORG_REASON).reason == NO_ORG_REASON  # The route reads this value.

    def test_a_filled_pick_list_needs_no_reason(self):
        """A list that holds rows carries no reason by default."""
        assert PickList([1]).reason is None  # A filled control needs no explanation.


class TestTheJsonBody:
    """The route body names the reason whenever the list is empty."""

    def test_an_empty_list_carries_a_reason(self):
        """An empty selector answer always holds a reason field."""
        body = _pick_list_payload("sites", PickList(reason=NO_SESSION_REASON))  # Run the code under test.
        assert body["total_count"] == 0  # The page reads the count to size the control.
        assert body["reason"] == NO_SESSION_REASON  # The page shows this sentence in the control.

    def test_an_empty_list_with_no_stated_reason_still_carries_one(self):
        """A list emptied by a genuine zero-row answer still explains itself."""
        # A truly empty organization is a valid answer, and the operator still needs the words.
        body = _pick_list_payload("sites", PickList())
        assert body["reason"] == NO_ROWS_REASON  # The fallback sentence must never be blank.

    def test_a_filled_list_carries_no_reason(self):
        """A populated selector answer holds no reason field."""
        body = _pick_list_payload("sites", PickList([{"id": "a"}]))  # Run the code under test.
        assert "reason" not in body  # A filled control must not show an explanation.
        assert body["total_count"] == 1  # The count must match the rows.


class TestTheSiteSelector:
    """The site selector names every cause of an empty list."""

    def test_no_session_names_the_session(self, caplog):
        """A portal with no API session says so."""
        result = _fetch_org_sites(None, "org-1")  # Run the code under test with no session.
        assert result == []  # The control still receives a list.
        assert result.reason == NO_SESSION_REASON  # The control receives the cause.
        assert "no Mist API session" in caplog.text  # The operator finds the cause in the log.

    def test_no_org_names_the_org(self, caplog):
        """A portal with no organization identifier says so."""
        result = _fetch_org_sites(object(), "")  # Run the code under test with no organization.
        assert result == []  # The control still receives a list.
        assert result.reason == NO_ORG_REASON  # The control receives the cause.
        assert "no organization identifier" in caplog.text  # The operator finds the cause in the log.


class TestTheDeviceSelector:
    """The device selector names every cause of an empty list."""

    def test_no_session_names_the_session(self):
        """A portal with no API session says so."""
        result = _fetch_site_devices(None, "site-1", "all")  # Run the code under test.
        assert result.reason == NO_SESSION_REASON  # The control receives the cause.

    def test_no_site_names_the_site(self):
        """A request with no chosen site says so."""
        result = _fetch_site_devices(object(), "", "all")  # Run the code under test.
        assert result.reason == NO_SITE_REASON  # The control receives the cause.


class TestTheClientSelector:
    """The client selector names every cause of an empty list."""

    def test_no_session_names_the_session(self):
        """A portal with no API session says so."""
        result = _fetch_site_clients(None, "site-1")  # Run the code under test.
        assert result.reason == NO_SESSION_REASON  # The control receives the cause.

    def test_no_site_names_the_site(self):
        """A request with no chosen site says so."""
        result = _fetch_site_clients(object(), "")  # Run the code under test.
        assert result.reason == NO_SITE_REASON  # The control receives the cause.


class TestACloudFailureNamesItself:
    """A failed Mist API call reaches the operator, not a silent blank."""

    @pytest.fixture
    def broken_mistapi(self, monkeypatch):
        """Install a mistapi module whose every call raises."""
        import sys
        import types

        module = types.ModuleType("mistapi")  # Build a stand-in, so no real request leaves the machine.

        def _raise(*args, **kwargs):
            raise RuntimeError("the cloud refused the call")  # Any exception proves the path.

        for path in ("api.v1.orgs.sites", "api.v1.sites.devices", "api.v1.sites.clients"):
            node = module
            for part in path.split("."):
                if not hasattr(node, part):
                    setattr(node, part, types.ModuleType(part))  # Build the nested module path.
                node = getattr(node, part)
            for call in ("listOrgSites", "listSiteDevices", "searchSiteWirelessClients"):
                setattr(node, call, _raise)  # Every entry point must raise.
        monkeypatch.setitem(sys.modules, "mistapi", module)
        return module

    def test_a_failed_site_call_names_the_error(self, broken_mistapi, caplog):
        """A failed site call returns the error name, not a blank control."""
        result = _fetch_org_sites(object(), "org-1")  # Run the code under test.
        assert result == []  # The control still receives a list.
        assert result.reason == API_ERROR_REASON.format(error="RuntimeError")  # The control names the error.

    def test_a_failed_device_call_names_the_error(self, broken_mistapi):
        """A failed device call returns the error name, not a blank control."""
        result = _fetch_site_devices(object(), "site-1", "all")  # Run the code under test.
        assert result.reason == API_ERROR_REASON.format(error="RuntimeError")  # The control names the error.

    def test_a_failed_client_call_reports_at_error_level(self, broken_mistapi, caplog):
        """A failed client call reports at ERROR, not at DEBUG."""
        import logging

        # The old code logged this at DEBUG on the root logger, so no operator ever saw it.
        with caplog.at_level(logging.ERROR, logger="web_portal.routes.operations"):
            _fetch_site_clients(object(), "site-1")  # Run the code under test.
        assert "Failed to list wireless clients" in caplog.text  # The record must reach the error log.

    def test_two_failed_client_sources_never_report_no_rows(self, broken_mistapi):
        """When both client sources fail, the control names the failure."""
        # Both inner helpers catch their own error and return no row. The old
        # code then reported "the Mist API answered with no rows", which sent
        # the operator to look for missing clients instead of a failed call.
        result = _fetch_site_clients(object(), "site-1")  # Run the code under test.
        assert result == []  # The control still receives a list.
        assert result.reason == API_ERROR_REASON.format(error="RuntimeError")  # The wireless source failed first.
        assert result.reason != NO_ROWS_REASON  # The control must never claim the site holds no client.
