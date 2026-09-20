"""Tests for the dropdown order of the operations page (issue #3083).

Why:
    The site dropdown, the device dropdown, and the client dropdown listed their
    entries in the order the Mist API returned them. That order is not the name
    order, and it is not stable between calls. An engineer who looks for one
    site then reads the whole list.

    The client dropdown was worse. It joined the wireless list to the wired
    list, so every wireless client sorted before every wired one whatever its
    name.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from web_portal.routes.operations import (
    CLIENT_LABEL_FIELDS,
    DEVICE_LABEL_FIELDS,
    _fetch_org_sites,
    _fetch_site_clients,
    _fetch_site_devices,
    display_label,
    sort_by_name,
)


def names(entries: list, fields: tuple[str, ...] = ("name",)) -> list[str]:
    """Return the label of each entry, in the order the caller received them."""
    return [display_label(entry, fields) for entry in entries]


class TestTheSortRule:
    """Prove the rule itself, before any network shape reaches it."""

    def test_the_names_order_alphabetically(self) -> None:
        """This is the whole point of the change."""
        rows = [{"name": "zulu"}, {"name": "alpha"}, {"name": "mike"}]
        assert names(sort_by_name(rows)) == ["alpha", "mike", "zulu"]

    def test_the_order_ignores_letter_case(self) -> None:
        """A capital letter must not push a name to one end of the list."""
        rows = [{"name": "beta"}, {"name": "Alpha"}, {"name": "Charlie"}]
        assert names(sort_by_name(rows)) == ["Alpha", "beta", "Charlie"]

    def test_an_unnamed_entry_sorts_last(self) -> None:
        """A blank row must never hide a named one at the top of the list."""
        rows = [{"name": ""}, {"name": "alpha"}, {"name": "beta"}]
        assert names(sort_by_name(rows)) == ["alpha", "beta", ""]

    def test_a_missing_name_key_sorts_last(self) -> None:
        """The Mist API can omit the field, and the sort must not raise."""
        rows = [{"id": "x"}, {"name": "alpha"}]
        ordered = sort_by_name(rows)
        assert ordered[0]["name"] == "alpha"
        assert ordered[1]["id"] == "x"

    def test_a_whitespace_name_sorts_last(self) -> None:
        """A name of spaces reads as blank to an operator, so it belongs last."""
        rows = [{"name": "   ", "id": "blank"}, {"name": "alpha", "id": "a"}]
        ordered = sort_by_name(rows)
        assert [row["id"] for row in ordered] == ["a", "blank"]

    def test_an_unnamed_entry_stays_in_the_list(self) -> None:
        """An unnamed device still carries an identifier an operator may need."""
        rows = [{"name": "", "id": "keep-me"}, {"name": "alpha", "id": "a"}]
        assert len(sort_by_name(rows)) == 2
        assert sort_by_name(rows)[1]["id"] == "keep-me"

    def test_an_empty_list_returns_empty(self) -> None:
        """A site with no device must answer with no row, not with a fault."""
        assert sort_by_name([]) == []

    def test_the_caller_list_is_not_mutated(self) -> None:
        """A helper that reordered the caller's list would surprise every caller."""
        rows = [{"name": "zulu"}, {"name": "alpha"}]
        sort_by_name(rows)
        assert names(rows) == ["zulu", "alpha"]


class TestTheSiteDropdown:
    """The site list is the first control an engineer touches."""

    def test_the_sites_arrive_in_name_order(self) -> None:
        """Issue #3083. The API order is not the name order."""
        api = MagicMock()
        api.api.v1.orgs.sites.listOrgSites.return_value = MagicMock(
            data=[
                {"id": "3", "name": "Zulu Site"},
                {"id": "1", "name": "alpha Site"},
                {"id": "2", "name": "Mike Site"},
            ]
        )
        with patch.dict("sys.modules", {"mistapi": api}):
            result = _fetch_org_sites(object(), "org-1")
        assert names(result) == ["alpha Site", "Mike Site", "Zulu Site"]

    def test_an_unnamed_site_sorts_last(self) -> None:
        """A site with no name must not sit above a named one."""
        api = MagicMock()
        api.api.v1.orgs.sites.listOrgSites.return_value = MagicMock(
            data=[{"id": "1", "name": ""}, {"id": "2", "name": "alpha"}]
        )
        with patch.dict("sys.modules", {"mistapi": api}):
            result = _fetch_org_sites(object(), "org-1")
        assert names(result) == ["alpha", ""]

    def test_a_failed_call_returns_no_site(self) -> None:
        """The route reads len() on this result, so it must never be None."""
        api = MagicMock()
        api.api.v1.orgs.sites.listOrgSites.side_effect = RuntimeError("the cloud refused")
        with patch.dict("sys.modules", {"mistapi": api}):
            assert _fetch_org_sites(object(), "org-1") == []


class TestTheDeviceDropdown:
    """A site can hold many switches, so the order matters most here."""

    def test_the_devices_arrive_in_name_order(self) -> None:
        """Issue #3083. A long device list is unreadable in API order."""
        api = MagicMock()
        api.api.v1.sites.devices.listSiteDevices.return_value = MagicMock(
            data=[
                {"id": "3", "name": "SW-EDGE-03"},
                {"id": "1", "name": "sw-core-01"},
                {"id": "2", "name": "SW-DIST-02"},
            ]
        )
        with patch.dict("sys.modules", {"mistapi": api}):
            result = _fetch_site_devices(object(), "site-1", "all")
        assert names(result) == ["sw-core-01", "SW-DIST-02", "SW-EDGE-03"]

    def test_an_unnamed_device_sorts_last_and_keeps_its_mac(self) -> None:
        """An unnamed switch is still reachable by its MAC address.

        The page shows ``device.name || device.mac``, so a device with a MAC
        address is not unlabelled. It sorts by that MAC address instead.
        """
        api = MagicMock()
        api.api.v1.sites.devices.listSiteDevices.return_value = MagicMock(
            data=[{"id": "1", "name": "", "mac": "aabbccddeeff"}, {"id": "2", "name": "SW-01"}]
        )
        with patch.dict("sys.modules", {"mistapi": api}):
            result = _fetch_site_devices(object(), "site-1", "all")
        assert names(result, DEVICE_LABEL_FIELDS) == ["aabbccddeeff", "SW-01"]
        assert len(result) == 2, "The sort dropped a device, so one switch is now unreachable."

    def test_a_device_with_no_label_at_all_sorts_last(self) -> None:
        """A row with neither a name nor a MAC address carries nothing to read."""
        rows = [{"name": "", "mac": ""}, {"name": "SW-01", "mac": "x"}]
        assert names(sort_by_name(rows, DEVICE_LABEL_FIELDS), DEVICE_LABEL_FIELDS) == ["SW-01", ""]


class TestTheClientDropdown:
    """Two client sources feed one list, so a plain join breaks the order.

    A client carries its name in ``hostname`` and not in ``name``. A sort that
    read ``name`` alone would treat every client as unnamed, and the stable sort
    would then leave the wireless list above the wired list unchanged. These
    tests prove the sort reads the field the page actually shows.
    """

    @staticmethod
    def build_api(wireless: list, wired: list) -> MagicMock:
        """Return a stand-in SDK that answers both client searches."""
        api = MagicMock()
        api.api.v1.sites.clients.searchSiteWirelessClients.return_value = MagicMock(data={"results": wireless})
        api.api.v1.sites.clients.searchSiteWiredClients.return_value = MagicMock(data={"results": wired})
        return api

    def test_the_two_client_types_interleave_by_name(self) -> None:
        """Issue #3083. A join put every wireless client above every wired one."""
        api = self.build_api(
            wireless=[{"mac": "w1", "hostname": "zulu-laptop"}, {"mac": "w2", "hostname": "bravo-laptop"}],
            wired=[{"mac": "e1", "hostname": "alpha-printer"}, {"mac": "e2", "hostname": "charlie-printer"}],
        )
        with patch.dict("sys.modules", {"mistapi": api}):
            result = _fetch_site_clients(object(), "site-1")
        ordered = names(result, CLIENT_LABEL_FIELDS)
        assert ordered == sorted(ordered, key=str.casefold), f"The client list is not in name order: {ordered}"

    def test_a_wired_client_can_sort_first(self) -> None:
        """The proof that the order reads the name and not the source list."""
        api = self.build_api(
            wireless=[{"mac": "w1", "hostname": "zulu"}],
            wired=[{"mac": "e1", "hostname": "alpha"}],
        )
        with patch.dict("sys.modules", {"mistapi": api}):
            result = _fetch_site_clients(object(), "site-1")
        assert len(result) == 2, "The stand-in returned the wrong client count, so this test proves nothing."
        assert (
            names(result, CLIENT_LABEL_FIELDS)[0] == "alpha"
        ), "A wired client never reaches the top, so the join still decides the order."

    def test_a_client_without_a_hostname_falls_back_to_its_mac(self) -> None:
        """The page shows the MAC address then, so the sort must read it too."""
        assert display_label({"hostname": "", "mac": "aabb"}, CLIENT_LABEL_FIELDS) == "aabb"

    def test_no_site_returns_no_client(self) -> None:
        """A missing site identifier must answer with no row, not with a fault."""
        assert _fetch_site_clients(object(), "") == []


@pytest.mark.parametrize("count", [0, 1, 2, 50])
def test_the_sort_never_changes_the_row_count(count: int) -> None:
    """A sort that dropped a row would hide a device from the operator."""
    rows = [{"name": f"device-{index:03d}"} for index in range(count)]
    assert len(sort_by_name(rows)) == count


class TestACloudFailureLeavesTheSelectorUsable:
    """The three fetchers call the Mist cloud, which can refuse or fail.

    Warning: the route reads ``len()`` on each result, so a fetcher that raised
    or answered ``None`` would break the whole operations page and not only one
    dropdown. Each case below must answer with an empty list instead.
    """

    @staticmethod
    def raising_api(error: Exception) -> MagicMock:
        """Return a stand-in SDK whose every call raises the supplied error."""
        api = MagicMock()
        api.api.v1.orgs.sites.listOrgSites.side_effect = error
        api.api.v1.sites.devices.listSiteDevices.side_effect = error
        api.api.v1.sites.clients.searchSiteWirelessClients.side_effect = error
        api.api.v1.sites.clients.searchSiteWiredClients.side_effect = error
        return api

    @pytest.mark.parametrize(
        ("status", "reason"),
        [
            (401, "the token expired"),
            (403, "the token lacks the scope"),
            (404, "the organization is gone"),
            (429, "the cloud rate limited the call"),
        ],
    )
    def test_a_client_error_returns_an_empty_site_list(self, status: int, reason: str) -> None:
        """An HTTP 4xx answer must leave the page usable, not raise into the route."""
        error = RuntimeError(f"HTTP {status}: {reason}")
        with patch.dict("sys.modules", {"mistapi": self.raising_api(error)}):
            assert _fetch_org_sites(object(), "org-1") == []

    @pytest.mark.parametrize("status", [500, 502, 503])
    def test_a_server_error_returns_an_empty_site_list(self, status: int) -> None:
        """An HTTP 5xx answer is a cloud fault, and the page must survive it."""
        error = RuntimeError(f"HTTP {status}: the cloud failed")
        with patch.dict("sys.modules", {"mistapi": self.raising_api(error)}):
            assert _fetch_org_sites(object(), "org-1") == []

    @pytest.mark.parametrize("status", [401, 429, 500, 503])
    def test_a_failed_device_call_returns_an_empty_list(self, status: int) -> None:
        """The device selector must answer with no row on any HTTP failure."""
        error = RuntimeError(f"HTTP {status}")
        with patch.dict("sys.modules", {"mistapi": self.raising_api(error)}):
            assert _fetch_site_devices(object(), "site-1", "all") == []

    @pytest.mark.parametrize("status", [403, 500])
    def test_a_failed_client_call_returns_an_empty_list(self, status: int) -> None:
        """Both client searches can fail, and the joined list must stay a list."""
        error = RuntimeError(f"HTTP {status}")
        with patch.dict("sys.modules", {"mistapi": self.raising_api(error)}):
            assert _fetch_site_clients(object(), "site-1") == []

    def test_one_failed_client_source_keeps_the_other(self) -> None:
        """A wired failure must not hide every wireless client as well."""
        api = MagicMock()
        api.api.v1.sites.clients.searchSiteWirelessClients.return_value = MagicMock(
            data={"results": [{"mac": "w1", "hostname": "alpha"}]}
        )
        api.api.v1.sites.clients.searchSiteWiredClients.side_effect = RuntimeError("HTTP 500")
        with patch.dict("sys.modules", {"mistapi": api}):
            result = _fetch_site_clients(object(), "site-1")
        assert names(result, CLIENT_LABEL_FIELDS) == ["alpha"]
