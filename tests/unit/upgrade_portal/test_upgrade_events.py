"""Unit tests for ``src/upgrade_portal/upgrade/events.py``.

Why:
    Three rules of the event read fail in silence, so each one needs a test that
    fails loudly.

    First, the reconnect key list must come from the cloud. Only ``AP_RESTARTED``
    and ``AP_CONNECTED`` are vendor confirmed. A hard-coded ``SW_CONNECTED`` that
    the cloud never sends would hold the switch phase open until the timeout.

    Second, ``searchOrgDeviceEvents`` defaults ``device_type`` to ``ap``. A poll
    that omits the parameter reads access point events during a switch phase,
    matches nothing, and reports no error at all.

    Third, the cursor is ``search_after``. Both vendored event search documents
    advise ``page`` under their pagination heading, and the installed SDK has no
    ``page`` parameter. A poll that sent ``page`` would raise a type error at the
    first busy site.
"""

from __future__ import annotations

from typing import Any

import mistapi
import pytest

from src.upgrade_portal.upgrade import events as module

ORG_ID = "org-1"

CATALOGUE_ROWS: list[dict[str, Any]] = [
    {"key": "AP_CONNECTED", "display": "AP Connected"},
    {"key": "AP_RESTARTED", "display": "AP Restarted"},
    {"key": "SW_CONNECTED", "display": "Switch Connected"},
    {"key": "GW_RESTARTED", "display": "Gateway Restarted"},
    {"key": "AP_CONFIG_CHANGED_BY_USER", "display": "AP Config Changed"},
    {"key": "SW_PORT_UP", "display": "Port Up"},
]


class FakeResponse:
    """A stand-in for the answer object that the SDK builds.

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


def search_body(rows: list[dict[str, Any]], next_url: str | None = None) -> dict[str, Any]:
    """Build one event search body in the documented envelope.

    Why:
        ``research/settle-gate-apis.md`` fixes the six keys of the envelope. One
        builder keeps every test on the same shape.

    Args:
        rows: The event records of the page.
        next_url: The ``next`` URL, or None at the end of the result set.

    Returns:
        The answer body.
    """
    body: dict[str, Any] = {"start": 0, "end": 0, "limit": len(rows), "total": len(rows), "results": rows}
    if next_url is not None:
        body["next"] = next_url
    return body


def record_search(monkeypatch: pytest.MonkeyPatch, bodies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replace the event search endpoint and record each call.

    Args:
        monkeypatch: The pytest patcher.
        bodies: One answer body for each call, in order.

    Returns:
        The keyword set of each call, in order.
    """
    seen: list[dict[str, Any]] = []
    remaining = list(bodies)

    def fake_search(*args: Any, **kwargs: Any) -> FakeResponse:
        seen.append({"args": args, "kwargs": kwargs})
        return FakeResponse(remaining.pop(0) if remaining else search_body([]))

    monkeypatch.setattr(mistapi.api.v1.orgs.devices, "searchOrgDeviceEvents", fake_search)
    return seen


class TestFilterEventKeys:
    """The suffix rule that finds the reconnect keys."""

    def test_a_connected_key_and_a_restart_key_land_in_different_groups(self) -> None:
        """A restart and a reconnect are two different signals."""
        keys = module.filter_event_keys(CATALOGUE_ROWS)
        assert keys.connected == frozenset({"AP_CONNECTED", "SW_CONNECTED"})
        assert keys.restarted == frozenset({"AP_RESTARTED", "GW_RESTARTED"})

    def test_an_unrelated_key_is_dropped(self) -> None:
        """The catalogue holds hundreds of keys that say nothing about a reboot."""
        keys = module.filter_event_keys(CATALOGUE_ROWS)
        assert "AP_CONFIG_CHANGED_BY_USER" not in keys.connected
        assert "SW_PORT_UP" not in keys.restarted

    def test_the_rule_reads_the_suffix_and_never_the_family_prefix(self) -> None:
        """A vendor rename of the prefix must cost nothing."""
        keys = module.filter_event_keys([{"key": "MXEDGE_CONNECTED"}, {"key": "SSR_RESTARTED"}])
        assert keys.connected == frozenset({"MXEDGE_CONNECTED"})
        assert keys.restarted == frozenset({"SSR_RESTARTED"})

    def test_a_lower_case_key_is_folded(self) -> None:
        """A later release may change the case of the catalogue."""
        assert module.filter_event_keys([{"key": " sw_connected "}]).connected == frozenset({"SW_CONNECTED"})

    def test_an_empty_catalogue_gives_an_empty_record(self) -> None:
        """The gate must then say so instead of waiting for ever."""
        assert module.filter_event_keys([]).is_empty


class TestEventKeys:
    """The match test of one event record."""

    def test_a_connected_key_matches(self) -> None:
        """The gate reads one signal from the event stream."""
        assert module.filter_event_keys(CATALOGUE_ROWS).matches("SW_CONNECTED")

    def test_a_restart_key_matches(self) -> None:
        """A restart event is also a reconnect signal."""
        assert module.filter_event_keys(CATALOGUE_ROWS).matches("gw_restarted")

    def test_an_unrelated_key_does_not_match(self) -> None:
        """A configuration change is not a reboot."""
        assert not module.filter_event_keys(CATALOGUE_ROWS).matches("AP_CONFIG_CHANGED_BY_USER")


class TestReadEventDefinitions:
    """The catalogue read and its faults."""

    def test_the_call_passes_the_session_alone(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The endpoint takes no organization value and no page value."""
        seen: dict[str, Any] = {}

        def fake_list(*args: Any, **kwargs: Any) -> FakeResponse:
            seen["args"] = args
            seen["kwargs"] = kwargs
            return FakeResponse(CATALOGUE_ROWS)

        monkeypatch.setattr(mistapi.api.v1.const.device_events, "listDeviceEventsDefinitions", fake_list)
        module.read_event_definitions(fake_mist_session)
        assert seen["args"] == (fake_mist_session,)
        assert seen["kwargs"] == {}

    def test_a_plain_list_body_is_read(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The constants endpoint answers with a plain list."""
        monkeypatch.setattr(
            mistapi.api.v1.const.device_events,
            "listDeviceEventsDefinitions",
            lambda session: FakeResponse(CATALOGUE_ROWS),
        )
        assert len(module.read_event_definitions(fake_mist_session)) == len(CATALOGUE_ROWS)

    def test_a_results_body_is_read(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A later release may wrap the catalogue in the search envelope."""
        monkeypatch.setattr(
            mistapi.api.v1.const.device_events,
            "listDeviceEventsDefinitions",
            lambda session: FakeResponse({"results": CATALOGUE_ROWS}),
        )
        assert len(module.read_event_definitions(fake_mist_session)) == len(CATALOGUE_ROWS)

    def test_a_failed_read_returns_no_record(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A failed catalogue read must not stop the run."""

        def raise_error(session: Any) -> FakeResponse:
            raise RuntimeError("the cloud refused the read")

        monkeypatch.setattr(mistapi.api.v1.const.device_events, "listDeviceEventsDefinitions", raise_error)
        assert module.read_event_definitions(fake_mist_session) == ()

    def test_an_unknown_body_shape_returns_no_record(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The reader names the case instead of returning an empty list in silence."""
        monkeypatch.setattr(
            mistapi.api.v1.const.device_events,
            "listDeviceEventsDefinitions",
            lambda session: FakeResponse({"definitions": []}),
        )
        assert module.read_event_definitions(fake_mist_session) == ()


class TestEventCatalogue:
    """The cache that holds the discovered key list.

    Why:
        The module hard-codes no key. A test that proved the cache with a hard
        coded list would defeat the rule under test, so each test below counts
        the cloud reads instead.
    """

    def test_the_first_load_reads_the_cloud(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The catalogue is unknown until the portal asks for it."""
        monkeypatch.setattr(module, "read_event_definitions", lambda session: tuple(CATALOGUE_ROWS))
        catalogue = module.EventCatalogue()
        assert catalogue.cached is None
        assert catalogue.load(fake_mist_session).connected == frozenset({"AP_CONNECTED", "SW_CONNECTED"})

    def test_a_second_load_reads_nothing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The catalogue changes only with a cloud release."""
        calls: list[int] = []

        def counted(session: Any) -> tuple[dict[str, Any], ...]:
            calls.append(1)
            return tuple(CATALOGUE_ROWS)

        monkeypatch.setattr(module, "read_event_definitions", counted)
        catalogue = module.EventCatalogue()
        first = catalogue.load(fake_mist_session)
        second = catalogue.load(fake_mist_session)
        assert calls == [1]
        assert first is second

    def test_a_failed_read_is_cached_and_reported_as_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The module offers no fallback key list, because none is confirmed."""
        monkeypatch.setattr(module, "read_event_definitions", lambda session: ())
        catalogue = module.EventCatalogue()
        assert catalogue.load(fake_mist_session).is_empty

    def test_a_reset_reads_the_cloud_again(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A test builds a fresh holder, and an operator may force a reload."""
        calls: list[int] = []

        def counted(session: Any) -> tuple[dict[str, Any], ...]:
            calls.append(1)
            return tuple(CATALOGUE_ROWS)

        monkeypatch.setattr(module, "read_event_definitions", counted)
        catalogue = module.EventCatalogue()
        catalogue.load(fake_mist_session)
        catalogue.reset()
        assert catalogue.cached is None
        catalogue.load(fake_mist_session)
        assert calls == [1, 1]


class TestBuildWindow:
    """The time window of one poll."""

    def test_the_window_ends_at_the_moment_that_the_caller_passed(self) -> None:
        """The module owns no clock, so a test needs no patched time."""
        window = module.build_window(1770000000.6, 300)
        assert window.end == 1770000000
        assert window.start == 1769999700

    def test_the_page_size_is_clamped_to_the_cloud_ceiling(self) -> None:
        """A larger value would make the cloud refuse the call."""
        assert module.build_window(1770000000, 300, 99999).limit == module.MAX_EVENT_LIMIT

    def test_the_page_size_is_clamped_to_one(self) -> None:
        """A zero page size would return nothing for ever."""
        assert module.build_window(1770000000, 300, 0).limit == module.MIN_EVENT_LIMIT

    def test_a_look_back_of_zero_is_refused(self) -> None:
        """An empty window would match no event and report no fault."""
        with pytest.raises(ValueError, match="positive look-back"):
            module.build_window(1770000000, 0)


class TestPollDeviceEvents:
    """The organization event poll and its parameters."""

    def test_the_call_passes_the_device_type(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The parameter defaults to ``ap``, so a switch gate would wait for ever."""
        seen = record_search(monkeypatch, [search_body([])])
        window = module.build_window(1770000000, 300)
        module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_SWITCH, window)
        assert seen[0]["kwargs"]["device_type"] == "switch"

    @pytest.mark.parametrize("device_type", module.DEVICE_TYPES)
    def test_each_family_reaches_the_cloud_by_name(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
        device_type: str,
    ) -> None:
        """The cascade runs one phase for each family."""
        seen = record_search(monkeypatch, [search_body([])])
        window = module.build_window(1770000000, 300)
        module.poll_device_events(fake_mist_session, ORG_ID, device_type, window)
        assert seen[0]["kwargs"]["device_type"] == device_type

    def test_the_call_sends_no_page_parameter(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """Both vendored documents advise ``page``, and no such parameter exists."""
        seen = record_search(monkeypatch, [search_body([])])
        window = module.build_window(1770000000, 300)
        module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window)
        assert "page" not in seen[0]["kwargs"]

    def test_the_call_sends_the_window_as_text(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The installed SDK types ``start`` and ``end`` as text."""
        seen = record_search(monkeypatch, [search_body([])])
        window = module.build_window(1770000000, 300)
        module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window)
        assert seen[0]["kwargs"]["start"] == "1769999700"
        assert seen[0]["kwargs"]["end"] == "1770000000"
        assert seen[0]["kwargs"]["limit"] == module.DEFAULT_EVENT_LIMIT

    def test_the_call_names_the_organization_by_position(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The gate reads the organization scope, so one call covers every site."""
        seen = record_search(monkeypatch, [search_body([])])
        window = module.build_window(1770000000, 300)
        module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window)
        assert seen[0]["args"] == (fake_mist_session, ORG_ID)

    def test_an_unknown_device_type_is_refused(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A typing mistake would read the wrong family with no error."""
        record_search(monkeypatch, [search_body([])])
        window = module.build_window(1770000000, 300)
        with pytest.raises(ValueError, match="event poll needs one of"):
            module.poll_device_events(fake_mist_session, ORG_ID, "aps", window)

    def test_the_page_holds_the_returned_events(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The gate reads the records of the page."""
        rows = [{"mac": "5c5b350e0001", "type": "SW_CONNECTED", "timestamp": 1770000000}]
        record_search(monkeypatch, [search_body(rows)])
        window = module.build_window(1770000000, 300)
        page = module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_SWITCH, window)
        assert page.events == tuple(rows)
        assert page.cursor is None
        assert page.truncated is False


class TestCursor:
    """The ``search_after`` cursor of the event search."""

    def test_a_direct_field_is_read(self) -> None:
        """A later release may report the cursor as its own field."""
        assert module.read_cursor(FakeResponse({"results": [], "search_after": "abc123"})) == "abc123"

    def test_the_cursor_is_read_out_of_the_next_url(self) -> None:
        """The cloud reports the cursor inside the ``next`` URL."""
        body = search_body([], "/api/v1/orgs/x/devices/events/search?limit=100&search_after=1770000000123")
        assert module.read_cursor(FakeResponse(body)) == "1770000000123"

    def test_a_next_url_with_no_cursor_gives_none(self) -> None:
        """A URL that carries no cursor is the end of the result set."""
        assert module.read_cursor(FakeResponse(search_body([], "/api/v1/orgs/x/events?limit=100"))) is None

    def test_an_absent_next_url_gives_none(self) -> None:
        """The last page carries no ``next`` field."""
        assert module.read_cursor(FakeResponse(search_body([]))) is None

    def test_a_list_body_gives_none(self) -> None:
        """A plain list carries no cursor at all."""
        assert module.read_cursor(FakeResponse([])) is None

    def test_the_cursor_is_never_computed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """The vendor states that a caller must copy the value, never build one."""
        body = search_body([{"mac": "a"}], "https://api.mist.com/x?search_after=99")
        seen = record_search(monkeypatch, [body, search_body([])])
        window = module.build_window(1770000000, 300)
        first = module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window)
        module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window, first.cursor)
        assert seen[1]["kwargs"]["search_after"] == "99"


class TestTruncationGuard:
    """The guard that names a lost page."""

    def test_a_full_page_with_no_cursor_is_named(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A full page with no cursor means that the rest of the window is lost."""
        rows = [{"mac": f"5c5b350e00{index:02d}", "type": "AP_CONNECTED"} for index in range(3)]
        record_search(monkeypatch, [search_body(rows)])
        window = module.build_window(1770000000, 300, 3)
        page = module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window)
        assert page.truncated is True

    def test_a_full_page_with_a_cursor_is_not_named(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A cursor means that the caller may still read the rest."""
        rows = [{"mac": f"5c5b350e00{index:02d}", "type": "AP_CONNECTED"} for index in range(3)]
        record_search(monkeypatch, [search_body(rows, "/x?search_after=7")])
        window = module.build_window(1770000000, 300, 3)
        page = module.poll_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window)
        assert page.truncated is False


class TestDrainDeviceEvents:
    """The loop that reads every page of one window."""

    def test_the_loop_follows_the_cursor_to_the_last_page(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A busy site returns more events than one page holds."""
        bodies = [
            search_body([{"mac": "5c5b350e0001", "type": "AP_CONNECTED"}], "/x?search_after=1"),
            search_body([{"mac": "5c5b350e0002", "type": "AP_CONNECTED"}]),
        ]
        seen = record_search(monkeypatch, bodies)
        window = module.build_window(1770000000, 300)
        collected = module.drain_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window)
        assert len(collected) == 2
        assert seen[0]["kwargs"]["search_after"] is None
        assert seen[1]["kwargs"]["search_after"] == "1"

    def test_the_loop_stops_at_the_page_ceiling(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_mist_session: Any,
    ) -> None:
        """A cloud that always answers with a cursor must not hold the thread."""
        bodies = [search_body([{"mac": "5c5b350e0001"}], "/x?search_after=1") for _ in range(6)]
        seen = record_search(monkeypatch, bodies)
        window = module.build_window(1770000000, 300)
        module.drain_device_events(fake_mist_session, ORG_ID, module.DEVICE_TYPE_AP, window, max_pages=3)
        assert len(seen) == 3


class TestSelectReconnectEvents:
    """The match between the event stream and the target list."""

    def test_only_a_reconnect_event_is_kept(self) -> None:
        """A configuration change says nothing about a reboot."""
        keys = module.filter_event_keys(CATALOGUE_ROWS)
        rows = [
            {"mac": "5c5b350e0001", "type": "SW_CONNECTED"},
            {"mac": "5c5b350e0002", "type": "AP_CONFIG_CHANGED_BY_USER"},
        ]
        assert module.select_reconnect_events(rows, keys) == (rows[0],)

    def test_an_empty_key_record_matches_nothing(self) -> None:
        """A failed catalogue read must not look like a settled phase."""
        empty = module.EventKeys(frozenset(), frozenset())
        assert module.select_reconnect_events([{"mac": "a", "type": "AP_CONNECTED"}], empty) == ()

    def test_the_mac_addresses_are_normalized(self) -> None:
        """The gate compares this set against the target list."""
        keys = module.filter_event_keys(CATALOGUE_ROWS)
        rows = [{"mac": "5C:5B:35:0E:00:01", "type": "AP_RESTARTED"}]
        assert module.reconnect_macs(rows, keys) == frozenset({"5c5b350e0001"})

    def test_an_unreadable_mac_address_is_dropped(self) -> None:
        """An empty key would match every other malformed record."""
        keys = module.filter_event_keys(CATALOGUE_ROWS)
        rows = [{"mac": "not-an-address", "type": "AP_RESTARTED"}]
        assert module.reconnect_macs(rows, keys) == frozenset()


class TestPollCadence:
    """The 20-second cadence of the event poll."""

    def test_the_wait_is_the_whole_interval_right_after_a_poll(self) -> None:
        """T138 fixes the cadence at 20 seconds."""
        assert module.seconds_until_next_poll(1770000000, 1770000000) == module.POLL_INTERVAL_SECONDS

    def test_the_wait_shrinks_as_time_passes(self) -> None:
        """The driver owns the sleep, so this function only reports the wait."""
        assert module.seconds_until_next_poll(1770000000, 1770000005) == 15

    def test_a_late_poll_waits_nothing(self) -> None:
        """A slow poll must never build a backlog."""
        assert module.seconds_until_next_poll(1770000000, 1770000090) == 0


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

    def test_the_module_sleeps_in_no_function(self) -> None:
        """A sleep inside a read module would block every test that calls it."""
        source = (module.__file__ or "").strip()
        with open(source, encoding="utf-8") as handle:
            text = handle.read()
        assert "time.sleep" not in text
        assert "import time" not in text

    def test_the_module_hard_codes_no_reconnect_key(self) -> None:
        """T137 forbids a key list, because only the access point keys are confirmed."""
        source = (module.__file__ or "").strip()
        with open(source, encoding="utf-8") as handle:
            code = "".join(line for line in handle if not line.lstrip().startswith("#"))
        body = code.split('"""', 2)[-1]
        for forbidden in ("SW_CONNECTED", "GW_CONNECTED", "GW_RESTARTED"):
            assert forbidden not in body

    def test_every_public_name_is_exported(self) -> None:
        """A caller reads ``__all__`` to find the surface."""
        for name in module.__all__:
            assert hasattr(module, name)
