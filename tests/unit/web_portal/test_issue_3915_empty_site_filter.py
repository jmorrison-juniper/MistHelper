"""Tests for the shared empty-site filter of the operations portal.

Issue #3915 moved the empty-site rule of issue #3840 into one class and gave
the map viewer site list the same behavior. These tests prove the class rules
and prove that the map route answers with the filtered rows and the hidden
count.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from flask import Flask

from web_portal.routes import maps as maps_module
from web_portal.routes import operations as operations_module
from web_portal.routes.maps import maps_bp
from web_portal.routes.site_filtering import EmptySiteFilter

FULL_SITE_ID = "11111111-1111-1111-1111-111111111111"  # The site that holds hardware.
EMPTY_SITE_ID = "22222222-2222-2222-2222-222222222222"  # The site that holds no hardware.


class FakeResponse:
    """Carry a row list the way the Mist SDK answer carries it."""

    def __init__(self, data: list[dict]) -> None:
        """Hold the successful response that the fake endpoint returns."""
        self.status_code = 200  # The picker accepts rows only after a successful HTTP response.
        self.data = data  # The route reads the rows through the data attribute.


@pytest.fixture
def site_rows() -> list[dict]:
    """Return one full site and one empty site in picker row shape."""
    return [
        {"id": FULL_SITE_ID, "name": "Morrison House"},  # This site holds hardware.
        {"id": EMPTY_SITE_ID, "name": "Planning Only"},  # This site holds no hardware.
    ]


@pytest.fixture
def stat_rows() -> list[dict]:
    """Return the site statistics rows that match the picker rows."""
    return [
        {"id": FULL_SITE_ID, "num_devices": 4},  # The full site reports four devices.
        {"id": EMPTY_SITE_ID, "num_devices": 0},  # The empty site reports no device.
    ]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, site_rows: list[dict], stat_rows: list[dict]) -> Any:
    """Serve the maps blueprint from a bare Flask app with fake Mist endpoints."""
    # The route reads the org site list through this endpoint.
    monkeypatch.setattr("mistapi.api.v1.orgs.sites.listOrgSites", lambda *_a, **_k: FakeResponse(site_rows))
    # The filter reads the device counts through this endpoint.
    monkeypatch.setattr("mistapi.api.v1.orgs.stats.listOrgSiteStats", lambda *_a, **_k: FakeResponse(stat_rows))
    app = Flask(__name__)  # A bare app avoids the portal factory and its threads.
    app.config["APISESSION"] = SimpleNamespace()  # The route only tests that a session exists.
    app.config["ORG_ID"] = "test-org"  # The site read needs an organization.
    app.register_blueprint(maps_bp)  # Register the routes under test only.
    return app.test_client()


class TestTheFilterReadsTheOverrideFlag:
    """The portal must accept the documented show_empty values."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (None, False),  # An absent argument hides the empty sites.
            ("1", True),  # The documented numeric value turns the filter off.
            ("TRUE", True),  # The read ignores the letter case.
            (" yes ", True),  # The read ignores the surrounding space.
            ("on", True),  # The fourth documented value also works.
            ("0", False),  # An explicit zero keeps the filter on.
            ("maybe", False),  # An unknown value keeps the filter on.
        ],
    )
    def test_the_read_accepts_the_documented_values(self, raw: str | None, expected: bool) -> None:
        """FR-3915-1: the override accepts 1, true, yes, and on only."""
        assert EmptySiteFilter.read_show_empty(raw) is expected  # The read must match the table.


class TestTheFilterReadsOneDeviceCount:
    """The statistics record names a total or the per-type counts."""

    def test_the_total_field_wins(self) -> None:
        """FR-3915-2: the record total names the device count."""
        record = {"num_devices": 7, "num_ap": 1}  # The total disagrees with the part on purpose.
        assert EmptySiteFilter.read_site_device_count(record) == 7  # The total must win.

    def test_the_parts_sum_when_no_total_exists(self) -> None:
        """FR-3915-3: the per-type counts sum when the record names no total."""
        record = {"num_ap": 2, "num_switch": 3, "num_gateway": 1}  # Three parts, no total.
        assert EmptySiteFilter.read_site_device_count(record) == 6  # The sum must be six.

    def test_a_non_integer_part_is_ignored(self) -> None:
        """FR-3915-4: a strange part value must not raise."""
        record = {"num_ap": "two", "num_switch": 3}  # One part carries text instead of a number.
        assert EmptySiteFilter.read_site_device_count(record) == 3  # Only the integer part counts.

    def test_an_empty_record_counts_zero(self) -> None:
        """FR-3915-5: a record with no count field reports zero."""
        assert EmptySiteFilter.read_site_device_count({}) == 0  # No field means no device.


class TestTheFilterFailsOpen:
    """A missing count is not proof that a site is empty."""

    def test_an_empty_count_map_hides_no_site(self, site_rows: list[dict]) -> None:
        """FR-3915-6: an unreadable count must hide no site."""
        kept, hidden = EmptySiteFilter.drop_empty_sites(site_rows, {})  # No count was observed.
        assert kept == site_rows  # Every row must survive.
        assert hidden == 0  # The route must report no hidden site.

    def test_a_statistics_fault_hides_no_site(self, monkeypatch: pytest.MonkeyPatch, site_rows: list[dict]) -> None:
        """FR-3915-7: a failed statistics read must hide no site."""

        def raise_error(*_args: Any, **_kwargs: Any) -> None:
            """Fail the way a transport fault fails."""
            raise RuntimeError("the statistics read failed")  # Any class must be caught.

        # The filter must survive the fault.
        monkeypatch.setattr("mistapi.api.v1.orgs.stats.listOrgSiteStats", raise_error)
        site_filter = EmptySiteFilter(SimpleNamespace(), "test-org")  # Build the filter under test.
        kept, hidden = site_filter.apply(site_rows)  # Run the filter against the faulty read.
        assert kept == site_rows  # Every row must survive the fault.
        assert hidden == 0  # The route must report no hidden site.


class TestTheOverrideSkipsTheStatisticsRead:
    """The override must cost no Mist API call."""

    def test_the_override_never_reads_the_counts(self, monkeypatch: pytest.MonkeyPatch, site_rows: list[dict]) -> None:
        """FR-3915-8: show_empty returns every row without a statistics read."""
        reads: list[str] = []  # Record each statistics read attempt.

        def record_read(*_args: Any, **_kwargs: Any) -> FakeResponse:
            """Record the call, then answer with no row."""
            reads.append("read")  # One entry for each call.
            return FakeResponse([])  # The answer does not matter here.

        # Watch the endpoint that the filter would call.
        monkeypatch.setattr("mistapi.api.v1.orgs.stats.listOrgSiteStats", record_read)
        site_filter = EmptySiteFilter(SimpleNamespace(), "test-org")  # Build the filter under test.
        kept, hidden = site_filter.apply(site_rows, show_empty=True)  # Ask for every site.
        assert kept == site_rows  # Every row must survive.
        assert hidden == 0  # No site was hidden.
        assert reads == []  # The override must skip the statistics read.


class TestTheMapSiteListHidesAnEmptySite:
    """The map viewer dropdown must obey the same rule as the other pickers."""

    def test_the_default_answer_hides_the_empty_site(self, client: Any) -> None:
        """FR-3915-9: the map site list hides a site that holds no hardware."""
        answer = client.get("/api/maps/sites")  # Read the dropdown source.
        assert answer.status_code == 200  # The route must answer.
        payload = answer.get_json()  # Read the JSON body.
        assert [site["id"] for site in payload["sites"]] == [FULL_SITE_ID]  # Only the full site.
        assert payload["empty_sites_hidden"] == 1  # The route must report the hidden count.

    def test_the_override_lists_every_site(self, client: Any) -> None:
        """FR-3915-10: show_empty=1 lists the empty site again."""
        answer = client.get("/api/maps/sites?show_empty=1")  # Ask for every site.
        payload = answer.get_json()  # Read the JSON body.
        assert [site["id"] for site in payload["sites"]] == [
            FULL_SITE_ID,
            EMPTY_SITE_ID,
        ]  # Both sites must appear.
        assert payload["empty_sites_hidden"] == 0  # No site was hidden.

    def test_an_absent_session_answers_with_no_site(self, client: Any) -> None:
        """FR-3915-11: a portal with no session must not raise."""
        client.application.config["APISESSION"] = None  # Drop the session of the live app.
        payload = client.get("/api/maps/sites").get_json()  # Read the answer.
        assert payload["sites"] == []  # The route must answer with no site.
        assert payload["error"] == "Not authenticated"  # The route must name the reason.


class TestBothRouteModulesCallTheFilterCorrectly:
    """The web_portal package has no Ruff gate and no mypy gate."""

    def test_the_map_helper_takes_three_arguments(self, client: Any) -> None:
        """FR-3915-12: a signature drift in the map helper must fail here."""
        with client.application.app_context():  # The helper logs through the app logger.
            sites, hidden = maps_module._fetch_sites(
                SimpleNamespace(), "test-org", False
            )  # Call the helper the way the route calls it.
        assert [site["id"] for site in sites] == [FULL_SITE_ID]  # The filter must run.
        assert hidden == 1  # The helper must report the hidden count.

    def test_the_operations_helper_reports_the_hidden_count(self, client: Any) -> None:
        """FR-3915-13: a stale helper name in the operations route must fail here."""
        picks = operations_module._fetch_org_sites(
            SimpleNamespace(), "test-org", False
        )  # Call the helper the way the route calls it.
        assert [pick["id"] for pick in picks] == [FULL_SITE_ID]  # The filter must run.
        assert getattr(picks, "empty_hidden", 0) == 1  # The route reads this count.


class TestTheMapImageSourceAnswersAFailure:
    """Prove the image source answers a client fault and a server fault."""

    def test_a_missing_map_record_answers_404(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-3915-14: a map read that finds no record must answer HTTP 404."""

        def read_no_record(_session: Any, _site_id: str, _map_id: str) -> None:
            """Answer no record, the shape a failed Mist API read produces."""
            return None  # The source treats a None record as a missing map.

        # Replace the record read so no Mist API call happens in this test.
        monkeypatch.setattr("web_portal.routes.maps.MapImageSource.read_record", read_no_record)
        # Call the source the way the route calls it, with a session, a site, and a map.
        result = maps_module.MapImageSource.fetch(SimpleNamespace(), FULL_SITE_ID, FULL_SITE_ID)
        assert result.status == 404  # The client fault must answer 404.
        assert result.error == maps_module.MAP_NOT_FOUND_MESSAGE  # The message must stay stable.

    def test_an_unusable_image_answers_502(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-3915-15: bytes that are not a raster image must answer HTTP 502."""

        def read_one_record(_session: Any, _site_id: str, _map_id: str) -> dict[str, Any]:
            """Answer a map record that carries a usable https image link."""
            return {"type": "image", "url": "https://example.invalid/plan.png"}  # The source reads both keys.

        def download_html(_url: str) -> bytes:
            """Answer bytes that no raster signature matches."""
            return b"<html>an error page</html>"  # A failed download often returns a page, not an image.

        # Replace the record read so the source reaches the download step.
        monkeypatch.setattr("web_portal.routes.maps.MapImageSource.read_record", read_one_record)
        # Replace the download so no network read happens in this test.
        monkeypatch.setattr("web_portal.routes.maps.MapImageDownloader.download", download_html)
        # Call the source the way the route calls it, with a session, a site, and a map.
        result = maps_module.MapImageSource.fetch(SimpleNamespace(), FULL_SITE_ID, FULL_SITE_ID)
        assert result.status == 502  # The server fault must answer 502.
        assert result.error == maps_module.MapImageSource.DOWNLOAD_FAILED_MESSAGE  # The reason must stay stable.

    def test_a_map_with_no_image_link_answers_404(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-3915-16: a map record with no https image link must answer HTTP 404."""

        def read_google_record(_session: Any, _site_id: str, _map_id: str) -> dict[str, Any]:
            """Answer a map record that holds no floor plan file."""
            return {"type": "google"}  # A Google map carries no image file.

        # Replace the record read so no Mist API call happens in this test.
        monkeypatch.setattr("web_portal.routes.maps.MapImageSource.read_record", read_google_record)
        # Call the source the way the route calls it, with a session, a site, and a map.
        result = maps_module.MapImageSource.fetch(SimpleNamespace(), FULL_SITE_ID, FULL_SITE_ID)
        assert result.status == 404  # A map with no image is a client fault, not a server fault.
        assert result.error == maps_module.MapImageSource.NO_IMAGE_MESSAGE  # The message must stay stable.
