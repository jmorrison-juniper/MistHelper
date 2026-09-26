"""Unit tests for ``src/upgrade_portal/upgrade/options.py``.

Why:
    Three rules of this module are silent when they break, so each one needs a
    test that fails loudly.

    First, the upgrade inventory read must omit the virtual chassis parameter.
    ``getOrgInventory`` builds its query with ``if vc:``, so a ``vc=True`` value
    would return one row for each stack member. The portal would then offer four
    rows for one logical switch and send four upgrades to one device. Nothing in
    the answer says that this happened.

    Second, a session smart router must carry the organization scope. The cancel
    call for that family exists at organization scope alone, so a run that
    recorded the site scope would find no cancel path at the moment of a stop.

    Third, ``uptime_before`` must stay null when the record holds no reading. A
    stored zero would make every later reading look larger, and the settle gate
    would never see the reboot.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import mistapi
import pytest
from mistapi.__api_response import APIResponse

from src.firmware.upgrade_service import SCOPE_ORG, SCOPE_SITE, STRATEGY_DEFAULT, UpgradeOptions
from src.upgrade_portal.capture.devices import REASON_READ_FAILED, REASON_SHORT_READ, REASON_UNKNOWN_SHAPE
from src.upgrade_portal.upgrade import options as module
from tests.support.sdk_pages import HTML_TYPE, JSON_TYPE, PagedSession, build_sdk_answer

PAGE_LIMIT = 100

# A fixed moment, so no test of the start time window reads the clock of the
# machine that runs it. An epoch written into a test ages into the past, and the
# window check would then fail on a day that nobody chose.
FIXED_NOW = 1_780_000_000
ONE_WEEK_SECONDS = 7 * 24 * 60 * 60


def fixed_clock() -> int:
    """Report the fixed moment that the start time tests measure against.

    Why:
        ``build_options`` takes the clock as an argument, so a test supplies this
        function and the window check reads a moment that never moves.

    Returns:
        The fixed moment in epoch seconds.
    """
    return FIXED_NOW


SWITCH_ROW: dict[str, Any] = {
    "mac": "5C:5B:35:0E:00:01",
    "name": "bld1-idf2-sw01",
    "type": "switch",
    "model": "EX4400-48P",
    "version": "23.4R2-S3.9",
    "uptime": 1832140,
}
JUNOS_ROW: dict[str, Any] = {
    "mac": "5c5b350e0002",
    "name": "bld1-gw01",
    "type": "gateway",
    "model": "SRX345",
    "version": "23.4R2-S3.9",
}
SSR_ROW: dict[str, Any] = {
    "mac": "5c5b350e0003",
    "name": "bld1-gw02",
    "type": "gateway",
    "model": "SSR120",
    "version": "6.2.5",
}
AP_ROW: dict[str, Any] = {
    "mac": "5c5b350e0004",
    "name": "bld1-ap01",
    "type": "ap",
    "model": "AP45",
    "version": "0.14.29076",
}

ORG_ID = "org-1"  # The organization that the two composition builders read.
SITE_ID = "site-1"  # The site that the two composition builders read.
VERSION_MAP: dict[str, tuple[str, ...]] = {
    "EX4400-48P": ("23.4R2-S4.11", "24.2R1.17"),
    "AP45": ("0.14.29216",),
}
THIN_BODY: dict[str, Any] = {"targets": [{"mac": "5c5b350e0001", "version_target": "24.2R1.17"}]}
SHORT_REASON: dict[str, Any] = {  # Issue #3424: the reason of a read that stops after the first page.
    "section": module.SECTION_UPGRADE_INVENTORY,  # The upgrade inventory read owns the reason.
    "reason": REASON_SHORT_READ,  # The row count is less than the reported total.
    "http_status": 200,  # The cloud answered the first page.
}
READ_FAILED_REASON: dict[str, Any] = {  # Issue #3424: the reason of a read that raised.
    "section": module.SECTION_UPGRADE_INVENTORY,  # The upgrade inventory read owns the reason.
    "reason": REASON_READ_FAILED,  # The read raised before a page answered.
    "http_status": 0,  # No answer, so no status.
}

# Issue #3424 review. The real endpoint answers a JSON list and sends the total
# in the X-Page-Total header. The SDK builds the link to page two from the three
# page headers. These values give a read of three rows with two rows on page one.
SMALL_PAGE_LIMIT = 2  # Two rows for each page, so three rows need two pages.
FIRST_PAGE_URL = "https://api.mist.com/api/v1/orgs/org-1/inventory?site_id=site-1&limit=2"  # Page one.
SECOND_PAGE_LINK = "/api/v1/orgs/org-1/inventory?site_id=site-1&limit=2&page=2"  # The link that the SDK builds.
SECOND_PAGE_URL = f"https://api.mist.com{SECOND_PAGE_LINK}"  # The full address of page two.
PAGE_ONE_HEADERS = {**JSON_TYPE, "X-Page-Total": "3", "X-Page-Limit": "2", "X-Page-Page": "1"}  # Three rows in all.
PAGE_TWO_HEADERS = {**JSON_TYPE, "X-Page-Total": "3", "X-Page-Limit": "2", "X-Page-Page": "2"}  # The last page.
LOST_PAGES = [  # Two ways that page two never arrives. The SDK catches each fault and builds an answer.
    pytest.param(502, b"<html><body>502 Bad Gateway</body></html>", HTML_TYPE, id="html-502"),
    pytest.param(429, b'{"detail": "Too Many Requests"}', JSON_TYPE, id="json-429"),
]


class FakeResponse:
    """A stand-in for the answer object that the SDK builds.

    Why:
        ``guard_page_count`` reads the body shape, the reported total, and the
        status. A namespace with those three members is enough, and it keeps the
        test away from the real transport. The page walk reads ``next`` with a
        default of None, so this stand-in names no later page.

    Attributes:
        data: The parsed body.
        status_code: The HTTP status.
    """

    def __init__(self, data: Any, status_code: int = 200) -> None:
        """Build one stand-in answer.

        Args:
            data: The parsed body.
            status_code: The HTTP status.
        """
        self.data = data
        self.status_code = status_code


def record_inventory_call(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[dict[str, Any]],
    total: int | None = None,
) -> dict[str, Any]:
    """Replace the inventory endpoint and the version read, and record the call.

    Why:
        The test needs the exact keyword set that the module sends, because the
        rule under test is the absence of one keyword. The stand-in page holds
        its rows under ``results`` and names no next page, so the page walk
        reads the rows from the body. ``plan_paged_read`` covers the list
        answer and the page headers of the real endpoint (issue #3424).

    Args:
        monkeypatch: The pytest patcher.
        rows: The records that the first page holds.
        total: The count that the first page reports. None reports the row
            count, so the read is complete. A larger count gives a short read
            (issue #3424).

    Returns:
        A map that holds ``args`` and ``kwargs`` after the call.
    """
    seen: dict[str, Any] = {}  # The arguments of the one endpoint call.
    reported = len(rows) if total is None else total  # A total above the row count makes a short read.

    def fake_endpoint(*args: Any, **kwargs: Any) -> FakeResponse:
        seen["args"] = args  # The session and the organization, by position.
        seen["kwargs"] = kwargs  # The site and the page size, by keyword.
        return FakeResponse({"results": rows, "total": reported})  # The first page and its reported total.

    monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", fake_endpoint)  # No cloud call.
    monkeypatch.setattr(module, "list_available_versions", lambda *args: VERSION_MAP)  # No version read.
    return seen  # The test reads the recorded call.


class TestReadUpgradeInventory:
    """The upgrade inventory read and its partial reasons."""

    def test_the_call_omits_the_virtual_chassis_parameter(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """Decision D11 sends no ``vc`` value on the upgrade path."""
        seen = record_inventory_call(monkeypatch, [SWITCH_ROW])
        module.read_upgrade_inventory(fake_mist_session, "org-1", "site-1", page_limit=PAGE_LIMIT)
        assert "vc" not in seen["kwargs"]

    def test_the_call_names_the_site_and_the_page_size(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The read passes the organization by position and the site by keyword."""
        seen = record_inventory_call(monkeypatch, [SWITCH_ROW])
        module.read_upgrade_inventory(fake_mist_session, "org-1", "site-1", page_limit=PAGE_LIMIT)
        assert seen["args"][1] == "org-1"
        assert seen["kwargs"] == {"site_id": "site-1", "limit": PAGE_LIMIT}

    def test_a_whole_read_reports_no_partial_reason(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A read that matches the reported total is complete."""
        record_inventory_call(monkeypatch, [SWITCH_ROW, AP_ROW])
        result = module.read_upgrade_inventory(fake_mist_session, "org-1", "site-1", page_limit=PAGE_LIMIT)
        assert len(result.records) == 2
        assert result.partial_reasons == []

    def test_an_unknown_body_shape_becomes_a_partial_reason(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A body with no readable list gives no row and no error, so the guard names the shape."""
        monkeypatch.setattr(
            mistapi.api.v1.orgs.inventory,
            "getOrgInventory",
            lambda *args, **kwargs: FakeResponse({"devices": []}),
        )
        result = module.read_upgrade_inventory(fake_mist_session, "org-1", "site-1", page_limit=PAGE_LIMIT)
        assert result.records == []
        assert result.partial_reasons[0]["reason"] == REASON_UNKNOWN_SHAPE
        assert result.partial_reasons[0]["section"] == module.SECTION_UPGRADE_INVENTORY

    def test_a_cloud_fault_becomes_a_partial_reason(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A raised error never stops the run and never returns a silent empty list."""

        def raise_error(*args: Any, **kwargs: Any) -> FakeResponse:
            raise RuntimeError("the cloud refused the read")

        monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", raise_error)
        result = module.read_upgrade_inventory(fake_mist_session, "org-1", "site-1", page_limit=PAGE_LIMIT)
        assert result.records == []
        assert result.partial_reasons == [
            {"section": module.SECTION_UPGRADE_INVENTORY, "reason": REASON_READ_FAILED, "http_status": 0}
        ]


class TestVersionOptions:
    """The model list and the version choice rows."""

    def test_collect_models_drops_a_repeat_and_sorts(self) -> None:
        """One read serves every model, so a repeated model spends the quota twice."""
        rows = [SWITCH_ROW, AP_ROW, dict(SWITCH_ROW), {"model": "  "}]
        assert module.collect_models(rows) == ("AP45", "EX4400-48P")

    def test_read_model_versions_passes_the_site_devices_and_organization(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The version read receives the organization needed for SSR discovery."""
        seen: dict[str, Any] = {}

        def fake_list(
            session: Any,
            site_id: str,
            devices: Any,
            org_id: str | None,
        ) -> dict[str, tuple[str, ...]]:
            seen["site_id"] = site_id
            seen["devices"] = tuple(devices)
            seen["org_id"] = org_id
            return {"AP45": ("0.14.29076",)}

        monkeypatch.setattr(module, "list_available_versions", fake_list)
        result = module.read_model_versions(fake_mist_session, "site-1", [AP_ROW], "org-1")
        assert seen == {"site_id": "site-1", "devices": (AP_ROW,), "org_id": "org-1"}
        assert result == {"AP45": ("0.14.29076",)}

    def test_build_version_options_joins_the_device_to_its_versions(self) -> None:
        """The options page needs one control for each device."""
        by_model = {"EX4400-48P": ("23.4R2-S4.11", "24.2R1.17")}
        rows = module.build_version_options([SWITCH_ROW], by_model)
        assert rows == [
            {
                "mac": "5c5b350e0001",
                "name": "bld1-idf2-sw01",
                "device_type": "switch",
                "model": "EX4400-48P",
                "version_before": "23.4R2-S3.9",
                "version_target": "24.2R1.17",
                "safe_target": "24.2R1.17",
                "target_source": "model_fallback",
                "firmware_mismatch": True,
                "versions": ["24.2R1.17", "23.4R2-S4.11"],
                # Issue #2211 marks the row that the portal cannot upgrade. A
                # switch is a modeled type, so the row reads true.
                "type_supported": True,
                # Issue #2157 shows the router controls only for a router row,
                # so every row names its gateway family. A switch has none.
                "gateway_family": "",
            }
        ]

    def test_build_version_options_falls_back_to_the_model_highest_version(self) -> None:
        """A type default that a model lacks must not leave that device unselected."""
        selections = {"ap": {"selected_version": "0.15.34994"}}
        rows = module.build_version_options(
            [AP_ROW],
            {"AP45": ("0.14.29076", "0.15.34533")},
            selections,
        )
        assert rows[0]["version_target"] == "0.15.34533"

    def test_a_model_with_no_version_list_gets_an_empty_list(self) -> None:
        """A missing model must not raise, because the operator still sees the row."""
        rows = module.build_version_options([AP_ROW], {})
        assert rows[0]["versions"] == []

    def test_an_unmodeled_device_type_never_ends_the_page(self) -> None:
        """Issue #2211: one router row made the whole site inventory answer 500."""
        router_row = {"mac": "5c5b350e0002", "name": "ssr-01", "type": "router", "model": "SSR130", "version": "6.2.5"}
        rows = module.build_version_options([router_row], {})
        assert rows[0]["device_type"] == "router"
        assert rows[0]["type_supported"] is False

    def test_an_unmodeled_device_type_reads_no_version_override(self) -> None:
        """The portal names no environment variable for a type it does not model."""
        assert module._configured_override("router", {"CAPTURE_DEFAULT_AP_VERSION": "0.14.29076"}) == ""

    def test_a_modeled_device_type_still_reads_its_override(self) -> None:
        """The guard must not remove the override that a modeled type carries."""
        assert module._configured_override("ap", {"CAPTURE_DEFAULT_AP_VERSION": "0.14.29076"}) == "0.14.29076"


class TestBuildOptions:
    """The map from the interface controls onto the seam option record."""

    def test_an_empty_body_takes_every_default(self) -> None:
        """FR-018 asks the portal to preselect the bulk flow default."""
        assert module.build_options({}) == UpgradeOptions()

    def test_the_default_strategy_comes_from_the_seam(self) -> None:
        """One term, one meaning: the module repeats no default of its own."""
        assert module.build_options({}).strategy == STRATEGY_DEFAULT

    @pytest.mark.parametrize(
        ("posted", "expected"),
        [
            (True, True),
            (False, False),
            ("true", True),
            ("false", False),
            ("yes", True),
            ("no", False),
            ("on", True),
            ("off", False),
            ("1", True),
            ("0", False),
            (" TRUE ", True),
        ],
    )
    def test_a_radio_group_value_maps_onto_a_boolean(self, posted: Any, expected: bool) -> None:
        """A radio group posts text and a JSON client posts a boolean."""
        assert module.build_options({"reboot": posted}).reboot is expected

    def test_an_absent_boolean_takes_the_default(self) -> None:
        """A missing control means the operator changed nothing."""
        assert module.build_options({"reboot": None}).reboot is module.DEFAULT_OPTIONS.reboot

    @pytest.mark.parametrize("field", ["reboot", "junos_file_action"])
    def test_an_unmapped_boolean_word_is_refused(self, field: str) -> None:
        """The portal refuses a value instead of guessing at real hardware."""
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options({field: "maybe"})
        assert caught.value.code == module.ERROR_BAD_OPTION
        assert caught.value.field == field

    def test_the_refusal_message_never_repeats_the_refused_value(self) -> None:
        """A refused value comes straight from the browser."""
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options({"reboot": "drop table"})
        assert "drop table" not in str(caught.value)

    @pytest.mark.parametrize("strategy", module.STRATEGY_CHOICES)
    def test_each_offered_strategy_is_accepted(self, strategy: str) -> None:
        """FR-016 asks for the same list that the bulk flow prompts for."""
        assert module.build_options({"strategy": strategy}).strategy == strategy

    def test_an_unknown_strategy_is_refused(self) -> None:
        """The cloud refuses the whole call and names no field."""
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options({"strategy": "fastest"})
        assert caught.value.field == "strategy"

    def test_a_start_time_of_digits_becomes_epoch_seconds(self) -> None:
        """The cloud reads ``start_time`` as epoch seconds."""
        chosen = FIXED_NOW + 8 * 60 * 60  # WHY: The epoch must sit inside the safe site lock window.
        assert module.build_options({"start_time": str(chosen)}, now=fixed_clock).start_time == chosen

    @pytest.mark.parametrize("posted", ["", "   ", None])
    def test_an_empty_start_time_means_an_immediate_start(self, posted: Any) -> None:
        """An empty date control must not schedule anything."""
        assert module.build_options({"start_time": posted}).start_time is None

    @pytest.mark.parametrize("posted", ["tomorrow", "-100", "17.5", True])
    def test_a_start_time_that_is_not_a_whole_second_is_refused(self, posted: Any) -> None:
        """A bad value would schedule the upgrade at a moment that nobody chose."""
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options({"start_time": posted})
        assert caught.value.field == "start_time"

    def test_a_start_time_that_is_already_past_is_refused(self) -> None:
        """The cloud starts the upgrade at once when the moment is already past.

        Why:
            The operator believes they scheduled the work for later, so nobody
            watches the site while the firmware writes. Every earlier check
            passes, because a stale epoch is a whole number of seconds.
        """
        stale = FIXED_NOW - module.START_TIME_GRACE_SECONDS - 1
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options({"start_time": str(stale)}, now=fixed_clock)
        assert caught.value.field == "start_time"

    def test_a_moment_a_few_seconds_past_is_accepted(self) -> None:
        """The clock of the browser and the clock of the portal rarely agree."""
        near = FIXED_NOW - 30
        assert module.build_options({"start_time": str(near)}, now=fixed_clock).start_time == near

    def test_a_millisecond_epoch_is_refused(self) -> None:
        """A millisecond value names a moment tens of thousands of years ahead.

        Why:
            The cloud accepts the value and the upgrade never runs, so the
            operator waits for work that can never start.
        """
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options({"start_time": str(FIXED_NOW * 1000)}, now=fixed_clock)
        assert caught.value.field == "start_time"

    def test_a_stored_choice_replays_without_the_window(self) -> None:
        """``app/wiring.py`` rebuilds the options of a run that already waited.

        Why:
            The operator chose the moment at the save call, and that call bounded
            it. A run that waits for confirmation past its own start time must
            still upgrade. A refusal here would fail the whole run instead.
        """
        stale = FIXED_NOW - ONE_WEEK_SECONDS
        assert module.build_options({"start_time": str(stale)}, now=None).start_time == stale


class TestResolveFamilyScope:
    """The gateway family split and the cloud scope of one device."""

    @pytest.mark.parametrize("device_type", ["ap", "switch"])
    def test_a_device_that_is_not_a_gateway_carries_no_family(self, device_type: str) -> None:
        """A switch never carries a gateway word."""
        assert module.resolve_family_scope(device_type, SWITCH_ROW) == (None, SCOPE_SITE)

    def test_a_junos_gateway_uses_the_site_scope(self) -> None:
        """A Junos gateway rides the same site call that a switch rides."""
        assert module.resolve_family_scope("gateway", JUNOS_ROW) == ("junos", SCOPE_SITE)

    def test_a_session_smart_router_uses_the_organization_scope(self) -> None:
        """The cancel path for that family exists at organization scope alone."""
        assert module.resolve_family_scope("gateway", SSR_ROW) == ("ssr", SCOPE_ORG)

    def test_the_router_test_reads_the_model_and_not_the_name(self) -> None:
        """``classify_gateway`` reads ``type`` and ``model`` only."""
        row = {"type": "gateway", "model": "128T-1000", "name": "srx-lookalike"}
        assert module.resolve_family_scope("gateway", row) == ("ssr", SCOPE_ORG)


class TestBuildTargetEntry:
    """The fields of one ``targets`` entry."""

    def test_the_entry_holds_every_field_of_the_data_model(self) -> None:
        """A missing key would break the status view at the first read."""
        entry = module.build_target_entry(SWITCH_ROW, "24.2R1.17")
        assert set(entry) == {
            "mac",
            "name",
            "device_type",
            "gateway_family",
            "model",
            "version_before",
            "version_target",
            "version_after",
            "upgrade_id",
            "scope",
            "state",
            "uptime_before",
            "last_seen_before",
            "reboot_seen_at",
            "settled_at",
        }

    def test_every_progress_field_starts_empty(self) -> None:
        """The run driver and the settle gate fill them later."""
        entry = module.build_target_entry(SWITCH_ROW, "24.2R1.17")
        assert entry["version_after"] is None
        assert entry["upgrade_id"] is None
        assert entry["reboot_seen_at"] is None
        assert entry["settled_at"] is None
        assert entry["state"] == module.STATE_PENDING

    def test_the_mac_address_is_lower_case_with_no_separator(self) -> None:
        """The gate matches the event MAC address against this value."""
        assert module.build_target_entry(SWITCH_ROW, "24.2R1.17")["mac"] == "5c5b350e0001"

    def test_a_present_uptime_is_stored_as_whole_seconds(self) -> None:
        """The gate compares a later reading against this value."""
        assert module.build_target_entry(SWITCH_ROW, "24.2R1.17")["uptime_before"] == 1832140

    def test_an_absent_uptime_stays_null(self) -> None:
        """A stored zero would make every later reading look larger."""
        assert module.build_target_entry(AP_ROW, "0.14.29076")["uptime_before"] is None

    @pytest.mark.parametrize("posted", ["1832140", True, None, {"seconds": 5}])
    def test_an_uptime_that_is_not_a_number_stays_null(self, posted: Any) -> None:
        """A text reading or a flag is not a second count."""
        row = dict(SWITCH_ROW, uptime=posted)
        assert module.build_target_entry(row, "24.2R1.17")["uptime_before"] is None

    def test_a_float_uptime_becomes_a_whole_number(self) -> None:
        """The cloud sometimes reports a fraction of a second."""
        row = dict(SWITCH_ROW, uptime=1832140.75)
        assert module.build_target_entry(row, "24.2R1.17")["uptime_before"] == 1832140


class TestBuildTargets:
    """The run ``targets`` list built from the browser choices."""

    def test_each_choice_becomes_one_entry_in_request_order(self) -> None:
        """The operator reads the table in the order that they built it."""
        choices = [
            {"mac": "5c5b350e0004", "version_target": "0.14.29076"},
            {"mac": "5C:5B:35:0E:00:01", "version_target": "24.2R1.17"},
        ]
        entries = module.build_targets([SWITCH_ROW, AP_ROW], choices)
        assert [entry["mac"] for entry in entries] == ["5c5b350e0004", "5c5b350e0001"]

    def test_an_unknown_mac_address_is_refused(self) -> None:
        """An upgrade of an unknown device would reach the wrong site."""
        with pytest.raises(module.BadOptionError) as caught:
            module.build_targets([SWITCH_ROW], [{"mac": "aabbccddeeff", "version_target": "24.2R1.17"}])
        assert caught.value.field == "mac"

    def test_an_empty_version_is_refused(self) -> None:
        """The cloud would then choose the version itself."""
        with pytest.raises(module.BadOptionError) as caught:
            module.build_targets([SWITCH_ROW], [{"mac": "5c5b350e0001", "version_target": "  "}])
        assert caught.value.field == "version_target"

    def test_a_gateway_choice_carries_its_family_and_scope(self) -> None:
        """The stop path reads these two fields with no second lookup."""
        choices = [{"mac": "5c5b350e0003", "version_target": "6.3.0"}]
        entry = module.build_targets([SSR_ROW], choices)[0]
        assert entry["gateway_family"] == "ssr"
        assert entry["scope"] == SCOPE_ORG

    def test_selected_types_limit_the_target_rows(self) -> None:
        """A selected switch plan cannot also prepare an access point."""
        choices = [
            {"mac": SWITCH_ROW["mac"], "version_target": "24.2R1.17"},
            {"mac": AP_ROW["mac"], "version_target": "0.14.29216"},
        ]
        entries = module.build_targets([SWITCH_ROW, AP_ROW], choices, selected_types=("switch",))
        assert [entry["device_type"] for entry in entries] == ["switch"]

    def test_a_target_of_an_unselected_type_is_refused(self) -> None:
        """A crafted request cannot add a type the operator did not select."""
        choice = [{"mac": AP_ROW["mac"], "version_target": "0.14.29216"}]
        with pytest.raises(module.BadOptionError) as caught:
            module.build_targets([AP_ROW], choice, selected_types=("switch",))
        assert caught.value.field == "targets"


class TestSelectedDeviceTypes:
    """The selected device types of one submitted option record."""

    def test_all_supported_types_are_the_default_selection(self) -> None:
        """A legacy body keeps its existing all-supported-types behavior."""
        assert module.selected_device_types({}) == ("ap", "switch", "gateway")

    def test_a_selected_type_list_rejects_duplicates_and_unknown_types(self) -> None:
        """A request must name each supported type once at most."""
        with pytest.raises(module.BadOptionError) as duplicate:
            module.selected_device_types({"selected_types": ["switch", "switch"]})
        assert duplicate.value.field == "selected_types"
        with pytest.raises(module.BadOptionError) as unsupported:
            module.selected_device_types({"selected_types": ["router"]})
        assert unsupported.value.field == "selected_types"


class TestTargetWarnings:
    """The plain sentences that the operator reads before the start."""

    def test_one_family_needs_no_word(self) -> None:
        """A single family reports one result."""
        entries = module.build_targets([JUNOS_ROW], [{"mac": "5c5b350e0002", "version_target": "24.2R1.17"}])
        assert module.target_warnings(entries) == ()

    def test_two_gateway_families_report_a_warning(self) -> None:
        """FR-020 asks the portal to report each family on its own."""
        choices = [
            {"mac": "5c5b350e0002", "version_target": "24.2R1.17"},
            {"mac": "5c5b350e0003", "version_target": "6.3.0"},
        ]
        entries = module.build_targets([JUNOS_ROW, SSR_ROW], choices)
        assert module.WARNING_MIXED_FAMILY in module.target_warnings(entries)

    def test_a_device_that_already_runs_the_version_reports_a_warning(self) -> None:
        """The operator may have picked the wrong row."""
        choices = [{"mac": "5c5b350e0001", "version_target": "23.4R2-S3.9"}]
        entries = module.build_targets([SWITCH_ROW], choices)
        assert module.target_warnings(entries) == (module.WARNING_SAME_VERSION,)


class TestTypedVersionSelections:
    """The safe, type-specific candidates that the options page uses."""

    def test_the_selector_intersects_normalized_versions_and_ranks_them_numerically(self) -> None:
        """A type default must be common to every device and use numeric ordering."""
        devices = [
            dict(AP_ROW, model="AP45"),
            dict(AP_ROW, mac="5c5b350e0005", model="AP32"),
            dict(SWITCH_ROW),
        ]
        versions = {
            "AP45": (" 0.14.9 ", "0.14.12", "0.14.20"),
            "AP32": ("0.14.9", "0.14.12"),
            "EX4400-48P": ("24.2R1.17",),
        }
        selections = module.TypedVersionSelector().select(devices, versions)
        assert selections["ap"]["candidates"] == ["0.14.12", "0.14.9"]
        assert selections["ap"]["selected_version"] == "0.14.12"
        assert selections["switch"]["selected_version"] == "24.2R1.17"

    def test_the_selector_warns_when_a_type_has_no_common_candidate(self) -> None:
        """The page must leave an incompatible type unselected."""
        devices = [dict(AP_ROW, model="AP45"), dict(AP_ROW, mac="5c5b350e0005", model="AP32")]
        selections = module.TypedVersionSelector().select(devices, {"AP45": ("0.14.12",), "AP32": ("0.14.9",)})
        assert selections["ap"]["selected_version"] is None
        assert selections["ap"]["warning"] == module.WARNING_NO_COMMON_CANDIDATE.format(device_type="access point")


class TestSaveTimeVersionValidation:
    """The save builder rejects targets that current availability no longer offers."""

    def test_a_stale_target_is_refused_before_any_plan_is_built(
        self, monkeypatch: pytest.MonkeyPatch, fake_mist_session: Any
    ) -> None:
        """A page-time version is unsafe when the current read no longer returns it."""
        monkeypatch.setattr(module, "read_upgrade_inventory", lambda *args: module.InventoryRead([AP_ROW], []))
        monkeypatch.setattr(module, "read_model_versions", lambda *args: {"AP45": ("0.14.29216",)})
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options_record(
                fake_mist_session,
                ORG_ID,
                SITE_ID,
                {"targets": [{"mac": AP_ROW["mac"], "version_target": "0.14.99999"}]},
            )
        assert caught.value.field == "version_target"


class TestTypeVersionOverrides:
    """The three operational overrides remain isolated and must be compatible."""

    @pytest.mark.parametrize(
        ("variable", "device_type", "model", "version"),
        [
            ("CAPTURE_DEFAULT_AP_VERSION", "ap", "AP45", "0.14.9"),
            ("CAPTURE_DEFAULT_SWITCH_VERSION", "switch", "EX4400-48P", "24.2R1.17"),
            ("CAPTURE_DEFAULT_GATEWAY_VERSION", "gateway", "SRX345", "23.4R2-S4.11"),
        ],
    )
    def test_a_compatible_override_applies_only_to_its_type(
        self, variable: str, device_type: str, model: str, version: str
    ) -> None:
        """An approved exact common candidate outranks only its own default."""
        devices = [dict(AP_ROW), dict(SWITCH_ROW), dict(JUNOS_ROW)]
        versions = {"AP45": ("0.14.9", "0.14.12"), "EX4400-48P": ("24.2R1.17",), "SRX345": ("23.4R2-S4.11",)}
        selections = module.TypedVersionSelector().select(devices, versions, {variable: version})
        assert selections[device_type]["selected_version"] == version

    def test_a_device_with_no_version_before_reports_no_repeat_warning(self) -> None:
        """An empty reading must not look like a match."""
        row = dict(AP_ROW, version="")
        entries = module.build_targets([row], [{"mac": "5c5b350e0004", "version_target": "0.14.29076"}])
        assert module.target_warnings(entries) == ()


class TestToDeviceTargets:
    """The bridge from the stored mapping onto the seam record."""

    def test_each_entry_becomes_one_seam_record(self) -> None:
        """``plan_upgrade`` groups ``DeviceTarget`` values, never mappings."""
        entries = module.build_targets([SWITCH_ROW], [{"mac": "5c5b350e0001", "version_target": "24.2R1.17"}])
        targets = module.to_device_targets(entries, "site-1")
        assert len(targets) == 1
        assert targets[0].mac == "5c5b350e0001"
        assert targets[0].device_type == "switch"
        assert targets[0].version_target == "24.2R1.17"
        assert targets[0].site_id == "site-1"

    def test_the_seam_record_carries_no_progress_field(self) -> None:
        """The seam holds the seven fields of the contract and nothing more."""
        entries = module.build_targets([SWITCH_ROW], [{"mac": "5c5b350e0001", "version_target": "24.2R1.17"}])
        target = module.to_device_targets(entries, "site-1")[0]
        assert not hasattr(target, "state")
        assert not hasattr(target, "uptime_before")


class TestBuildOptionsView:
    """The two halves that the options page draws for one run."""

    def test_a_good_read_answers_one_row_for_each_device(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The page drew only the rows the run record held, and a new run holds none."""
        record_inventory_call(monkeypatch, [SWITCH_ROW, AP_ROW])
        monkeypatch.setattr(module, "list_available_versions", lambda *args: VERSION_MAP)
        answer = module.build_options_view(fake_mist_session, ORG_ID, SITE_ID)
        assert [row["mac"] for row in answer["targets"]] == ["5c5b350e0001", "5c5b350e0004"]

    def test_the_version_map_carries_a_plain_list_for_each_model(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The page reads ``versions_map.get(model)``, and a tuple renders no option."""
        record_inventory_call(monkeypatch, [SWITCH_ROW])
        monkeypatch.setattr(module, "list_available_versions", lambda *args: VERSION_MAP)
        answer = module.build_options_view(fake_mist_session, ORG_ID, SITE_ID)
        assert answer["versions_by_model"]["EX4400-48P"] == ["23.4R2-S4.11", "24.2R1.17"]

    def test_an_empty_read_spends_no_second_call(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A failed read must never spend the version call for no gain."""
        record_inventory_call(monkeypatch, [])
        calls: list[Any] = []

        def fake_list(*args: Any) -> dict[str, tuple[str, ...]]:
            calls.append(args)
            return {}

        monkeypatch.setattr(module, "list_available_versions", fake_list)
        answer = module.build_options_view(fake_mist_session, ORG_ID, SITE_ID)
        assert answer == {"targets": [], "versions_by_model": {}, "partial_reasons": []}  # Issue #3424: no reason.
        assert calls == []


class TestBuildOptionsRecord:
    """The stored run record built from the thin browser choices."""

    def test_a_thin_choice_becomes_a_full_target_row(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """``to_device_targets`` reads ``device_type``, which the browser never sends."""
        record_inventory_call(monkeypatch, [SWITCH_ROW])
        answer = module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY)
        entry = answer["targets"][0]
        assert entry["device_type"] == "switch"
        assert entry["uptime_before"] == 1832140
        assert entry["state"] == module.STATE_PENDING

    def test_the_stored_row_reaches_the_seam_record(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """``app/wiring.py`` maps the stored rows, and a thin row raises there instead."""
        record_inventory_call(monkeypatch, [SWITCH_ROW])
        answer = module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY)
        targets = module.to_device_targets(answer["targets"], SITE_ID)
        assert targets[0].version_target == "24.2R1.17"

    def test_the_option_record_reads_back_as_the_seam_record(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """``app/wiring.py`` parses the stored options again, so the shape must survive."""
        record_inventory_call(monkeypatch, [SWITCH_ROW])
        answer = module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY)
        assert module.build_options(answer["options"]) == UpgradeOptions()

    def test_a_matching_version_reaches_the_warning_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The operator may have picked the row above the one they meant."""
        current = dict(SWITCH_ROW, version="24.2R1.17")
        record_inventory_call(monkeypatch, [current])
        body = {"targets": [{"mac": "5c5b350e0001", "version_target": "24.2R1.17"}]}
        answer = module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, body)
        assert answer["warnings"] == [module.WARNING_SAME_VERSION]

    def test_an_empty_read_answers_an_empty_mapping(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A cloud fault must read as no answer, never as a refused choice."""
        record_inventory_call(monkeypatch, [])
        assert module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY) == {}

    def test_an_unknown_device_is_refused(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """An upgrade of an unknown device would reach the wrong site."""
        record_inventory_call(monkeypatch, [AP_ROW])
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY)
        assert caught.value.field == "mac"

    def test_a_refused_strategy_reaches_the_caller(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The route answers 400 for a refused option, so the fault must not be held."""
        record_inventory_call(monkeypatch, [SWITCH_ROW])
        body = dict(THIN_BODY, strategy="fastest")
        with pytest.raises(module.BadOptionError) as caught:
            module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, body)
        assert caught.value.field == "strategy"

    def test_a_body_with_no_target_list_stores_no_row(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A save of the three controls alone must never raise."""
        record_inventory_call(monkeypatch, [SWITCH_ROW])
        answer = module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, {"reboot": False})
        assert answer["targets"] == []
        assert answer["options"]["reboot"] is False


def raise_cloud_fault(*args: Any, **kwargs: Any) -> FakeResponse:
    """Fail the inventory read the way a cloud fault does.

    Raises:
        RuntimeError: Always. ``_read_paged`` turns the fault into a reason.
    """
    raise RuntimeError("the cloud refused the read")  # The read holds no row after this fault.


class TestShortReadView:
    """Issue #3424: the options view reports each partial reason of its read."""

    @pytest.mark.parametrize(
        ("records", "reasons", "short"),
        [
            ([SWITCH_ROW], [SHORT_REASON], True),
            ([SWITCH_ROW], [], False),
            ([], [READ_FAILED_REASON], False),
            ([], [], False),
        ],
        ids=["short-read", "whole-read", "failed-read", "empty-site"],
    )
    def test_a_read_is_short_only_with_rows_and_a_reason(
        self,
        records: list[dict[str, Any]],
        reasons: list[dict[str, Any]],
        short: bool,
    ) -> None:
        """A failed read and an empty site keep the empty-record rule of issue #3389."""
        read = module.InventoryRead([dict(row) for row in records], list(reasons))  # One read of one site.
        assert read.is_short is short  # Only rows with a reason make a short read.

    def test_a_short_read_keeps_its_rows_and_reports_its_reason(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """FR-001: the page shows each device that the read found, beside the reason."""
        record_inventory_call(monkeypatch, [SWITCH_ROW, AP_ROW], total=5)  # The read stops after the first page.
        answer = module.build_options_view(fake_mist_session, ORG_ID, SITE_ID)  # The view of the options page.
        assert [row["mac"] for row in answer["targets"]] == ["5c5b350e0001", "5c5b350e0004"]  # The rows stay.
        assert answer["partial_reasons"] == [SHORT_REASON]  # The old view dropped this reason.

    def test_a_whole_read_reports_an_empty_reason_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """FR-001: a complete read reports no reason, so the page shows no banner."""
        record_inventory_call(monkeypatch, [SWITCH_ROW])  # The reported total equals the row count.
        answer = module.build_options_view(fake_mist_session, ORG_ID, SITE_ID)  # The view of the options page.
        assert answer["partial_reasons"] == []  # No banner.

    def test_a_failed_read_reports_its_reason(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """US1 scenario 3: a failed read shows the same banner as a short read."""
        monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", raise_cloud_fault)  # The read fails.
        answer = module.build_options_view(fake_mist_session, ORG_ID, SITE_ID)  # The view of the options page.
        assert answer == {"targets": [], "versions_by_model": {}, "partial_reasons": [READ_FAILED_REASON]}


class TestShortReadSave:
    """Issue #3424: the save refuses a short read before a version read."""

    def test_a_short_read_refuses_the_save(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """FR-003: the save must not store a plan that leaves out the devices of a lost page."""
        record_inventory_call(monkeypatch, [SWITCH_ROW], total=2)  # The read stops after the first page.
        with pytest.raises(module.PartialInventoryError) as caught:  # The save stops.
            module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY)
        assert caught.value.code == module.ERROR_PARTIAL_INVENTORY  # A machine code for a caller.
        assert caught.value.site_id == SITE_ID  # The multi-site route names this site.
        assert caught.value.reasons == [SHORT_REASON]  # The reason of the read.
        assert str(caught.value) == module.PARTIAL_INVENTORY_MESSAGE  # The text that the flash region shows.

    def test_a_short_read_spends_no_version_read(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """FR-011: a refused save must not spend the version call for no gain."""
        record_inventory_call(monkeypatch, [SWITCH_ROW], total=2)  # The read stops after the first page.
        calls: list[Any] = []  # Each version read.

        def fake_list(*args: Any) -> dict[str, tuple[str, ...]]:
            """Record the version read."""
            calls.append(args)  # The test reads this list.
            return VERSION_MAP  # The versions of each model.

        monkeypatch.setattr(module, "list_available_versions", fake_list)  # Count the version reads.
        with pytest.raises(module.PartialInventoryError):  # The save stops.
            module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY)
        assert calls == []  # The refusal came before the version read.

    def test_a_failed_read_keeps_the_empty_record_rule(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """FR-005: a read with no row and a reason keeps the empty record of issue #3389."""
        monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", raise_cloud_fault)  # The read fails.
        assert module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY) == {}  # No refusal.

    def test_the_log_names_the_site_and_the_reason_and_no_device(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """FR-012: the log records the site and the reason codes, and no device address."""
        record_inventory_call(monkeypatch, [SWITCH_ROW], total=2)  # The read stops after the first page.
        with caplog.at_level(logging.DEBUG), pytest.raises(module.PartialInventoryError):  # Keep each record.
            module.build_options_record(fake_mist_session, ORG_ID, SITE_ID, THIN_BODY)
        lines = [record.getMessage() for record in caplog.records]  # Each log line of the save.
        refusal_lines = [line for line in lines if REASON_SHORT_READ in line]  # The lines that name the reason.
        assert refusal_lines, lines  # The save logs the reason code of the short read.
        assert all(SITE_ID in line for line in refusal_lines)  # The same line names the site.
        assert not any("5c5b350e0001" in line for line in lines)  # The log holds no device address.
        assert not any(str(SWITCH_ROW["mac"]) in line for line in lines)  # Not in the form of the cloud either.


class TestPartialInventoryError:
    """Issue #3424: the refusal of a single-site save after a short read."""

    def test_the_refusal_is_a_value_error_and_not_a_bad_option(self) -> None:
        """D3: the single-site route answers each `ValueError` with `bad_option`, and no control is at fault."""
        error = module.PartialInventoryError(SITE_ID, [SHORT_REASON])  # One refusal.
        assert isinstance(error, ValueError)  # The single-site route catches this family.
        assert not isinstance(error, module.BadOptionError)  # The multi-site route must not name a control.

    def test_the_refusal_holds_a_detached_copy_of_the_reasons(self) -> None:
        """A later change of the read must not change the refusal."""
        reasons = [dict(SHORT_REASON)]  # The reasons of one read.
        error = module.PartialInventoryError(SITE_ID, reasons)  # One refusal.
        reasons[0]["reason"] = "changed"  # Change the entry of the read.
        reasons.append(dict(SHORT_REASON))  # Add an entry to the read.
        assert error.reasons == [SHORT_REASON]  # The refusal keeps its own copy.


def lost_page_reason(http_status: int) -> dict[str, Any]:
    """Return the reason of an upgrade inventory read that lost page two.

    Args:
        http_status: The HTTP status of the lost page.

    Returns:
        One partial reason entry.
    """
    return {"section": module.SECTION_UPGRADE_INVENTORY, "reason": REASON_SHORT_READ, "http_status": http_status}


def plan_paged_read(monkeypatch: pytest.MonkeyPatch, later_page: APIResponse) -> PagedSession:
    """Answer page one with two rows of three, and plan the answer for page two.

    Why:
        Issue #3424 review. The stand-in answer of ``record_inventory_call``
        carries a ``total`` field that this endpoint never sends. This plan
        uses the real SDK answer, so the SDK builds the link to page two from
        the page headers, as it does for the live cloud.

    Args:
        monkeypatch: The pytest patcher.
        later_page: The SDK answer for page two.

    Returns:
        The session that answers page two and records the link.
    """
    body = json.dumps([SWITCH_ROW, AP_ROW]).encode("utf-8")  # Two rows of three.
    first = build_sdk_answer(200, body, PAGE_ONE_HEADERS, FIRST_PAGE_URL)  # Page one, as the SDK builds it.
    monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", lambda *args, **kwargs: first)  # No cloud.
    monkeypatch.setattr(module, "list_available_versions", lambda *args: VERSION_MAP)  # No version read.
    return PagedSession([later_page])  # The session answers page two.


class TestLostLaterPage:
    """Issue #3424 review: a lost later page of a list answer is a short read."""

    @pytest.mark.parametrize(("status", "body", "headers"), LOST_PAGES)
    def test_a_lost_later_page_is_a_short_read(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: int,
        body: bytes,
        headers: dict[str, str],
    ) -> None:
        """Page one holds two rows of three, and page two never arrives."""
        session = plan_paged_read(monkeypatch, build_sdk_answer(status, body, headers, SECOND_PAGE_URL))
        read = module.read_upgrade_inventory(session, ORG_ID, SITE_ID, page_limit=SMALL_PAGE_LIMIT)
        assert session.links == [SECOND_PAGE_LINK]  # The read asked for page two one time.
        assert [row["mac"] for row in read.records] == [SWITCH_ROW["mac"], AP_ROW["mac"]]  # Page one stays.
        assert read.partial_reasons == [lost_page_reason(status)]  # The old read named no reason.
        assert read.is_short is True  # The options page shows the banner.

    def test_a_whole_paged_read_reports_no_reason(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Every page arrives, so the read names no loss."""
        body = json.dumps([JUNOS_ROW]).encode("utf-8")  # The third row.
        session = plan_paged_read(monkeypatch, build_sdk_answer(200, body, PAGE_TWO_HEADERS, SECOND_PAGE_URL))
        read = module.read_upgrade_inventory(session, ORG_ID, SITE_ID, page_limit=SMALL_PAGE_LIMIT)
        assert [row["mac"] for row in read.records] == [SWITCH_ROW["mac"], AP_ROW["mac"], JUNOS_ROW["mac"]]
        assert read.partial_reasons == []  # No banner and no refusal.

    @pytest.mark.parametrize(("status", "body", "headers"), LOST_PAGES)
    def test_the_view_reports_a_lost_later_page(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: int,
        body: bytes,
        headers: dict[str, str],
    ) -> None:
        """FR-001: the options page names the loss. It must not answer HTTP 500."""
        session = plan_paged_read(monkeypatch, build_sdk_answer(status, body, headers, SECOND_PAGE_URL))
        answer = module.build_options_view(session, ORG_ID, SITE_ID)  # The view of the options page.
        assert answer["partial_reasons"] == [lost_page_reason(status)]  # The banner names the loss.

    @pytest.mark.parametrize(("status", "body", "headers"), LOST_PAGES)
    def test_the_save_refuses_a_read_that_lost_a_later_page(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: int,
        body: bytes,
        headers: dict[str, str],
    ) -> None:
        """FR-003: the save must not store a plan that holds the rows of page one only."""
        session = plan_paged_read(monkeypatch, build_sdk_answer(status, body, headers, SECOND_PAGE_URL))
        with pytest.raises(module.PartialInventoryError) as caught:  # The save stops.
            module.build_options_record(session, ORG_ID, SITE_ID, THIN_BODY)
        assert caught.value.reasons == [lost_page_reason(status)]  # The refusal names the lost page.

    def test_a_record_that_is_not_a_map_fails_the_read_without_a_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A malformed row marks the read failed, so the page does not answer HTTP 500."""
        body = json.dumps([SWITCH_ROW, "not a map"]).encode("utf-8")  # One row is text, not a map.
        first = build_sdk_answer(200, body, JSON_TYPE, FIRST_PAGE_URL)  # No page headers, so no page two.
        monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", lambda *args, **kwargs: first)
        read = module.read_upgrade_inventory(PagedSession([]), ORG_ID, SITE_ID, page_limit=SMALL_PAGE_LIMIT)
        assert (read.records, read.partial_reasons) == ([], [READ_FAILED_REASON])  # The read failed as one unit.


class TestModuleProhibitions:
    """Rules that the whole package obeys."""

    def test_the_module_calls_no_console_function(self) -> None:
        """A source module never reads the console and never prints."""
        source = (module.__file__ or "").strip()
        assert source
        with open(source, encoding="utf-8") as handle:
            text = handle.read()
        for forbidden in ("print(", "input(", "safe_input("):
            assert forbidden not in text

    def test_every_public_name_is_exported(self) -> None:
        """A caller reads ``__all__`` to find the surface."""
        for name in module.__all__:
            assert hasattr(module, name)
