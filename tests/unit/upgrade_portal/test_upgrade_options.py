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

from typing import Any

import mistapi
import pytest

from src.firmware.upgrade_service import SCOPE_ORG, SCOPE_SITE, STRATEGY_DEFAULT, UpgradeOptions
from src.upgrade_portal.capture.devices import REASON_READ_FAILED, REASON_UNKNOWN_SHAPE
from src.upgrade_portal.upgrade import options as module

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


class FakeResponse:
    """A stand-in for the answer object that the SDK builds.

    Why:
        ``guard_page_count`` reads the body shape, the reported total, and the
        status. A namespace with those three members is enough, and it keeps the
        test away from the real transport.

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


def record_inventory_call(monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Replace the inventory endpoint and the page helper, and record the call.

    Why:
        The test needs the exact keyword set that the module sends, because the
        rule under test is the absence of one keyword.

    Args:
        monkeypatch: The pytest patcher.
        rows: The records that the page helper returns.

    Returns:
        A map that holds ``args`` and ``kwargs`` after the call.
    """
    seen: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> FakeResponse:
        seen["args"] = args
        seen["kwargs"] = kwargs
        return FakeResponse({"results": rows, "total": len(rows)})

    monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", fake_endpoint)
    monkeypatch.setattr(mistapi, "get_all", lambda mist_session, response: rows)
    monkeypatch.setattr(module, "list_available_versions", lambda *args: VERSION_MAP)
    return seen


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
        """``mistapi.get_all`` answers an unknown shape with an empty list and no error."""
        monkeypatch.setattr(
            mistapi.api.v1.orgs.inventory,
            "getOrgInventory",
            lambda *args, **kwargs: FakeResponse({"devices": []}),
        )
        monkeypatch.setattr(mistapi, "get_all", lambda mist_session, response: [])
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

    def test_read_model_versions_passes_the_site_and_the_devices(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The version read is site-scoped, which the seam already proved."""
        seen: dict[str, Any] = {}

        def fake_list(session: Any, site_id: str, devices: Any) -> dict[str, tuple[str, ...]]:
            seen["site_id"] = site_id
            seen["devices"] = tuple(devices)
            return {"AP45": ("0.14.29076",)}

        monkeypatch.setattr(module, "list_available_versions", fake_list)
        result = module.read_model_versions(fake_mist_session, "site-1", [AP_ROW])
        assert seen == {"site_id": "site-1", "devices": (AP_ROW,)}
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
                "versions": ["24.2R1.17", "23.4R2-S4.11"],
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
        chosen = FIXED_NOW + ONE_WEEK_SECONDS
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
        assert answer == {"targets": [], "versions_by_model": {}}
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
