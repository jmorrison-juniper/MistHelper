"""Unit tests for the upgrade capture assembly module.

Why:
    The stored capture document is the only record that a comparison reads. A
    wrong field, a digest that moves on its own, or a count that drifts would
    make the comparison report a change that never happened. These tests hold
    the document to ``data-model.md`` section 3.1 through section 3.7.

    Every test asserts on a constant of the module, never on message text. A
    message may change for Simplified Technical English at any time, and the
    rule name stays stable.

    No test opens a socket. The pool runs through an injected runner, so no test
    imports MistHelper and no test reaches the cloud.
"""

from __future__ import annotations

import threading
from typing import Any

import pytest

from src.upgrade_portal.capture import assembly, extras
from src.upgrade_portal.capture.clients import ClientAttachment, ClientIdentity, ClientRecord

RUN_ID = "run-0123456789abcdef0123456789abcdef"
RUN_HEX = "0123456789abcdef0123456789abcdef"
ACTOR = "operator@example.com"
STARTED_AT = "2026-08-19T10:00:00+00:00"
FINISHED_AT = "2026-08-19T10:00:12+00:00"

SWITCH_MAC = "5c5b350e0001"
AP_MAC = "5c5b350e0002"
GATEWAY_MAC = "5c5b350e0003"
CLIENT_MAC = "aabbccddeeff"


# ---------------------------------------------------------------------------
# The shared builders
# ---------------------------------------------------------------------------


def _device(mac: str, kind: str, status: str = "connected") -> dict[str, Any]:
    """Build one device record.

    Args:
        mac: The device address.
        kind: The device type name that the cloud reports.
        status: The connection state.

    Returns:
        One device record for the ``devices`` list.
    """
    return {"mac": mac, "type": kind, "status": status, "name": f"{kind}-{mac[-4:]}", "model": "TEST-1"}


def _index_entry(mac: str, kind: str, status: str = "connected") -> dict[str, Any]:
    """Build one device index entry.

    Args:
        mac: The device address.
        kind: The device type name.
        status: The connection state.

    Returns:
        One entry for the ``device_index`` map.
    """
    return {"name": f"{kind}-{mac[-4:]}", "type": kind, "status": status, "model": "TEST-1", "uptime": 4242}


def _sections(**overrides: Any) -> assembly.CaptureSections:
    """Build a section set that holds every validation rule.

    Why:
        Most tests change one part of a good capture. One builder holds the good
        shape, so a test states only its own difference.

    Args:
        **overrides: Any field of ``CaptureSections`` to replace.

    Returns:
        The section set.
    """
    parts: dict[str, Any] = {
        "device_index": {
            SWITCH_MAC: _index_entry(SWITCH_MAC, "switch"),
            AP_MAC: _index_entry(AP_MAC, "ap"),
            GATEWAY_MAC: _index_entry(GATEWAY_MAC, "gateway", "disconnected"),
        },
        "devices": [
            _device(SWITCH_MAC, "switch"),
            _device(AP_MAC, "ap"),
            _device(GATEWAY_MAC, "gateway", "disconnected"),
        ],
        "clients": {
            "wired": [{"mac": CLIENT_MAC, "device_mac": SWITCH_MAC, "port_id": "ge-0/0/1"}],
            "wireless": [{"mac": "112233445566", "device_mac": AP_MAC, "ssid": "corp"}],
            "guest": [],
        },
    }
    parts.update(overrides)
    return assembly.CaptureSections(**parts)


def _document(sections: assembly.CaptureSections | None = None, **overrides: Any) -> dict[str, Any]:
    """Build a capture document that holds every validation rule.

    Args:
        sections: The read sections. None builds the good set.
        **overrides: Top-level fields to replace after assembly.

    Returns:
        The capture document.
    """
    document = assembly.build_capture(
        assembly.CaptureIdentity(run_id=RUN_ID, ordinal=1, actor_email=ACTOR),
        assembly.SiteIdentity("org-1", "Test Org", "site-1", "Test Site"),
        assembly.CaptureWindow(STARTED_AT, FINISHED_AT, 12.5),
        sections if sections is not None else _sections(),
    )
    document.update(overrides)
    return document


def _window_of(window: assembly.CaptureWindow) -> dict[str, Any]:
    """Return the three time fields of one measured window.

    Args:
        window: The measured window.

    Returns:
        The two stamps and the duration, ready as document overrides.
    """
    return {
        "started_at": window.started_at,
        "finished_at": window.finished_at,
        "duration_seconds": window.duration_seconds,
    }


def _extra_sections() -> dict[str, list[dict[str, Any]]]:
    """Build a small tier 3 section map.

    Returns:
        The six tier 3 section names with a record in one of them.
    """
    ports = [{"mac": SWITCH_MAC, "port_id": "ge-0/0/1"}]
    return {name: (ports if name == extras.SECTION_SWITCH_PORTS else []) for name in extras.SECTION_NAMES}


def _sequential_executor(
    work_items: list[Any], worker_function: Any, batch_description: str
) -> tuple[list[Any], list[Any]]:
    """Run every call group in this thread.

    Why:
        The real pool reads the thread settings of MistHelper, and that import
        pulls the whole application into a unit test. This runner keeps the
        contract of the pool and runs nothing in the background.

    Args:
        work_items: The call groups.
        worker_function: The worker that the module supplies.
        batch_description: The label that the pool logs.

    Returns:
        The finished outcomes and the lost work items.
    """
    del batch_description
    budget = threading.Semaphore(1)
    finished = [worker_function(item, budget) for item in work_items]
    return finished, []


# ---------------------------------------------------------------------------
# The document shape
# ---------------------------------------------------------------------------


def test_capture_key_uses_the_run_hex_and_the_ordinal() -> None:
    """The key follows the form of data-model.md section 3.1."""
    assert assembly.capture_key(RUN_ID, 1) == f"cap-{RUN_HEX}-01"
    assert assembly.capture_key(RUN_ID, 2) == f"cap-{RUN_HEX}-02"
    assert assembly.capture_key(RUN_HEX, 12) == f"cap-{RUN_HEX}-12"


def test_capture_key_holds_no_slash_and_no_colon() -> None:
    """The key survives the key sanitizer of the database."""
    key = assembly.capture_key(RUN_ID, 1)
    assert "/" not in key
    assert ":" not in key


def test_capture_id_matches_the_key() -> None:
    """The document names the same value twice, as the data model asks."""
    document = _document()
    assert document["capture_id"] == document["_key"]
    assert document["_key"] == f"cap-{RUN_HEX}-01"


def test_schema_version_is_the_integer_one() -> None:
    """The stored version is a number, never text."""
    document = _document()
    assert document["schema_version"] == assembly.SCHEMA_VERSION
    assert document["schema_version"] == 1
    assert isinstance(document["schema_version"], int)


def test_document_holds_every_top_level_field() -> None:
    """The document carries all of data-model.md section 3.1 at tier 2."""
    document = _document()
    expected = {
        "_key",
        "capture_id",
        "schema_version",
        "run_id",
        "ordinal",
        "role",
        "org_id",
        "org_name",
        "site_id",
        "site_name",
        "tier",
        "started_at",
        "finished_at",
        "duration_seconds",
        "actor_email",
        "capture_status",
        "partial_reasons",
        "stored_size_bytes",
        "digests",
        "device_index",
        "devices",
        "clients",
        "counts",
    }
    assert expected <= set(document)


def test_document_names_the_site_and_the_operator() -> None:
    """The document stores a name beside each identifier."""
    document = _document()
    assert document["org_id"] == "org-1"
    assert document["org_name"] == "Test Org"
    assert document["site_id"] == "site-1"
    assert document["site_name"] == "Test Site"
    assert document["actor_email"] == ACTOR


def test_role_is_pre_for_the_first_ordinal() -> None:
    """Validation rule 2 ties the role to the ordinal."""
    assert assembly.role_for_ordinal(1) == assembly.ROLE_PRE
    assert _document()["role"] == assembly.ROLE_PRE


def test_role_is_post_for_a_later_ordinal() -> None:
    """A second capture and a repeat both read as the post-check."""
    assert assembly.role_for_ordinal(2) == assembly.ROLE_POST
    assert assembly.role_for_ordinal(3) == assembly.ROLE_POST


def test_duration_is_measured_and_not_estimated() -> None:
    """The timer reads a monotonic clock, so the duration cannot go negative."""
    timer = assembly.CaptureTimer()
    window = timer.finish()
    assert window.duration_seconds >= 0.0
    assert window.started_at == timer.started_at
    assert window.finished_at.endswith("+00:00")
    assert assembly.validate_capture(_document(**_window_of(window))) == []


def test_tier_two_document_holds_no_extras() -> None:
    """An absent extras set means tier 2."""
    document = _document()
    assert document["tier"] == assembly.TIER_STANDARD
    assert assembly.SECTION_EXTRAS not in document


def test_tier_three_document_holds_the_extras() -> None:
    """A present extras set means tier 3."""
    document = _document(_sections(extras=_extra_sections()))
    assert document["tier"] == assembly.TIER_EXTRA
    assert set(document[assembly.SECTION_EXTRAS]) == set(extras.SECTION_NAMES)


def test_stored_size_is_above_zero() -> None:
    """Validation rule 6 needs a measured size."""
    document = _document()
    assert document["stored_size_bytes"] > 0
    assert isinstance(document["stored_size_bytes"], int)


def test_stored_size_settles_on_its_own_width() -> None:
    """The stamp measures the document that already holds the number."""
    document = _document()
    assert document["stored_size_bytes"] == assembly.measure_size_bytes(document)


def test_stored_size_measures_the_body_and_not_the_driver_fields() -> None:
    """The store drops every underscore field, and this measurement does too."""
    document = _document()
    plain = {key: value for key, value in document.items() if not key.startswith("_")}
    assert assembly.measure_size_bytes(document) == assembly.measure_size_bytes(plain)
    assert assembly.measure_size_bytes(dict(document, _rev="server-added")) == document["stored_size_bytes"]


def test_clients_hold_the_three_named_lists() -> None:
    """The document always names wired, wireless, and guest."""
    document = _document(_sections(clients={}))
    assert set(document["clients"]) == {"wired", "wireless", "guest"}
    assert document["clients"]["guest"] == []


# ---------------------------------------------------------------------------
# The digests
# ---------------------------------------------------------------------------


def test_digest_map_holds_six_keys_at_tier_three() -> None:
    """Data-model.md section 3.2 names six digests."""
    digests = assembly.build_digests(_sections(extras=_extra_sections()))
    assert set(digests) == {
        assembly.SECTION_DEVICES,
        assembly.SECTION_WIRED,
        assembly.SECTION_WIRELESS,
        assembly.SECTION_GUEST,
        assembly.SECTION_EXTRAS,
        assembly.DIGEST_WHOLE,
    }


def test_digest_map_drops_extras_at_tier_two() -> None:
    """The extras digest is absent when no extras were read."""
    digests = assembly.build_digests(_sections())
    assert assembly.SECTION_EXTRAS not in digests
    assert len(digests) == len(assembly.BASE_DIGEST_SECTIONS) + 1


def test_is_volatile_names_every_listed_field() -> None:
    """The volatile list of data-model.md section 3.2 holds four names."""
    for name in ("timestamp", "last_seen", "uptime", "_ts"):
        assert assembly.is_volatile(name) is True
    assert assembly.is_volatile("model") is False
    assert assembly.is_volatile("status") is False


def test_is_volatile_names_a_counter_of_bytes_or_packets() -> None:
    """A counter changes without a real change in the site."""
    assert assembly.is_volatile("tx_bytes") is True
    assert assembly.is_volatile("rx_pkts") is True
    assert assembly.is_volatile("num_packets") is True


def test_strip_volatile_removes_a_nested_field() -> None:
    """A volatile field inside a list of records must also go."""
    body = {"mac": SWITCH_MAC, "ports": [{"id": "ge-0/0/1", "uptime": 90, "tx_bytes": 12}]}
    assert assembly.strip_volatile(body) == {"mac": SWITCH_MAC, "ports": [{"id": "ge-0/0/1"}]}


def test_strip_volatile_keeps_a_plain_value() -> None:
    """The strip leaves a value that is not a record or a list."""
    assert assembly.strip_volatile("text") == "text"
    assert assembly.strip_volatile(7) == 7


def test_digest_ignores_a_volatile_field() -> None:
    """A digest that kept uptime would report a change on every capture."""
    quiet = assembly.build_digests(_sections())
    noisy = assembly.build_digests(
        _sections(
            devices=[
                dict(_device(SWITCH_MAC, "switch"), uptime=10),
                dict(_device(AP_MAC, "ap"), last_seen=1),
                dict(_device(GATEWAY_MAC, "gateway", "disconnected"), timestamp=2),
            ]
        )
    )
    assert noisy[assembly.SECTION_DEVICES] == quiet[assembly.SECTION_DEVICES]


def test_digest_ignores_a_volatile_field_inside_a_list() -> None:
    """The strip runs at every depth, not at the top only."""
    plain = _device(SWITCH_MAC, "switch")
    plain["ports"] = [{"id": "ge-0/0/1"}]
    noisy = _device(SWITCH_MAC, "switch")
    noisy["ports"] = [{"id": "ge-0/0/1", "uptime": 900, "_ts": 5}]
    assert assembly.section_digest([plain]) == assembly.section_digest([noisy])


def test_digest_ignores_a_byte_counter() -> None:
    """A traffic counter never enters a digest."""
    plain = [{"mac": CLIENT_MAC}]
    counted = [{"mac": CLIENT_MAC, "tx_bytes": 8192, "rx_packets": 40}]
    assert assembly.section_digest(plain) == assembly.section_digest(counted)


def test_digest_changes_on_a_real_change() -> None:
    """A lost device must move the device digest."""
    full = assembly.build_digests(_sections())
    short = assembly.build_digests(_sections(devices=[_device(SWITCH_MAC, "switch")]))
    assert short[assembly.SECTION_DEVICES] != full[assembly.SECTION_DEVICES]


def test_canonical_text_ignores_the_key_order() -> None:
    """Two answers with the same content produce the same text."""
    first = assembly.canonical_text({"b": 1, "a": 2})
    second = assembly.canonical_text({"a": 2, "b": 1})
    assert first == second
    assert first == '{"a":2,"b":1}'


def test_whole_digest_covers_every_section() -> None:
    """Validation rule 8 reads the whole digest over the section digests."""
    digests = assembly.build_digests(_sections(extras=_extra_sections()))
    covered = {name: value for name, value in digests.items() if name != assembly.DIGEST_WHOLE}
    assert digests[assembly.DIGEST_WHOLE] == assembly.whole_digest(covered)


def test_whole_digest_moves_when_one_section_moves() -> None:
    """A change in any section reaches the whole digest."""
    full = assembly.build_digests(_sections())
    short = assembly.build_digests(_sections(clients={"wired": [], "wireless": [], "guest": []}))
    assert short[assembly.DIGEST_WHOLE] != full[assembly.DIGEST_WHOLE]


# ---------------------------------------------------------------------------
# The counts
# ---------------------------------------------------------------------------


def test_counts_hold_the_nine_keys_and_no_others() -> None:
    """Data-model.md section 3.6 names nine counts."""
    counts = assembly.build_counts(_sections())
    assert set(counts) == set(assembly.COUNT_KEYS)
    assert len(assembly.COUNT_KEYS) == 9
    assert all(isinstance(value, int) for value in counts.values())


def test_counts_split_the_connected_and_the_disconnected() -> None:
    """The two state counts add to the total."""
    counts = assembly.build_counts(_sections())
    assert counts["devices_total"] == 3
    assert counts["devices_connected"] == 2
    assert counts["devices_disconnected"] == 1


def test_counts_name_each_device_type() -> None:
    """The three type counts read the device index."""
    counts = assembly.build_counts(_sections())
    assert counts["gateways"] == 1
    assert counts["switches"] == 1
    assert counts["access_points"] == 1


def test_counts_name_each_client_list() -> None:
    """The three client counts read the three lists."""
    counts = assembly.build_counts(_sections())
    assert counts["clients_wired"] == 1
    assert counts["clients_wireless"] == 1
    assert counts["clients_guest"] == 0


def test_counts_are_zero_for_an_empty_capture() -> None:
    """An empty read still reports the nine names."""
    counts = assembly.build_counts(assembly.CaptureSections())
    assert set(counts) == set(assembly.COUNT_KEYS)
    assert set(counts.values()) == {0}


# ---------------------------------------------------------------------------
# The validation rules of data-model.md section 3.7
# ---------------------------------------------------------------------------


def test_a_good_document_breaks_no_rule() -> None:
    """The builder produces a document that holds all eight rules."""
    assert assembly.validate_capture(_document()) == []


def test_rule_one_catches_an_ordinal_below_one() -> None:
    """Rule 1 asks for an ordinal of 1 or greater."""
    broken = assembly.validate_capture(_document(ordinal=0, role=assembly.ROLE_POST))
    assert assembly.RULE_ORDINAL in broken


def test_rule_two_catches_a_first_capture_that_is_not_pre() -> None:
    """Rule 2 asks the first capture for the pre role."""
    broken = assembly.validate_capture(_document(role=assembly.ROLE_POST))
    assert assembly.RULE_ROLE in broken


def test_rule_two_allows_post_for_a_later_ordinal() -> None:
    """Rule 2 says nothing about a second capture."""
    broken = assembly.validate_capture(_document(ordinal=2, role=assembly.ROLE_POST))
    assert assembly.RULE_ROLE not in broken


def test_rule_three_catches_a_finish_before_the_start() -> None:
    """Rule 3 asks the finish to sit at or after the start."""
    broken = assembly.validate_capture(_document(finished_at="2026-08-19T09:59:00+00:00"))
    assert assembly.RULE_ORDER in broken


def test_rule_three_catches_a_stamp_that_holds_no_moment() -> None:
    """A stamp that cannot be read is not a valid window."""
    broken = assembly.validate_capture(_document(started_at="not-a-moment"))
    assert assembly.RULE_ORDER in broken


def test_rule_four_catches_partial_without_a_reason() -> None:
    """Rule 4 allows partial only beside a reason."""
    broken = assembly.validate_capture(_document(capture_status=assembly.STATUS_PARTIAL, partial_reasons=[]))
    assert assembly.RULE_PARTIAL_REASONS in broken


def test_rule_four_catches_complete_beside_a_reason() -> None:
    """A complete capture carries an empty reason list."""
    reason = assembly.partial_reason("alarms", "cloud_call_failed", 503)
    broken = assembly.validate_capture(_document(capture_status=assembly.STATUS_COMPLETE, partial_reasons=[reason]))
    assert assembly.RULE_PARTIAL_REASONS in broken


def test_rule_five_catches_a_reason_that_drops_a_field() -> None:
    """Rule 5 asks each reason for the three named fields."""
    broken = assembly.validate_capture(
        _document(capture_status=assembly.STATUS_PARTIAL, partial_reasons=[{"section": "alarms"}])
    )
    assert assembly.RULE_REASON_FIELDS in broken


def test_rule_six_catches_a_size_that_is_not_positive() -> None:
    """Rule 6 asks for a size above zero after a write."""
    broken = assembly.validate_capture(_document(stored_size_bytes=0))
    assert assembly.RULE_SIZE in broken


def test_rule_seven_catches_a_device_that_the_list_misses() -> None:
    """Every key of the device index appears in the device list."""
    sections = _sections(devices=[_device(SWITCH_MAC, "switch"), _device(AP_MAC, "ap")])
    broken = assembly.validate_capture(_document(sections))
    assert assembly.RULE_INDEX_MATCH in broken


def test_rule_seven_catches_a_device_that_the_index_misses() -> None:
    """The reverse of rule 7 is also true."""
    sections = _sections(device_index={SWITCH_MAC: _index_entry(SWITCH_MAC, "switch")})
    broken = assembly.validate_capture(_document(sections))
    assert assembly.RULE_INDEX_MATCH in broken


def test_rule_seven_holds_across_two_address_forms() -> None:
    """The rule compares one address form on both sides."""
    sections = _sections(
        device_index={
            "5C:5B:35:0E:00:01": _index_entry(SWITCH_MAC, "switch"),
            "5C-5B-35-0E-00-02": _index_entry(AP_MAC, "ap"),
            "5c5b35.0e0003": _index_entry(GATEWAY_MAC, "gateway", "disconnected"),
        }
    )
    assert assembly.RULE_INDEX_MATCH not in assembly.validate_capture(_document(sections))


def test_rule_eight_catches_a_missing_section_digest() -> None:
    """Rule 8 asks the whole digest to cover every present section."""
    document = _document()
    digests = dict(document["digests"])
    del digests[assembly.SECTION_GUEST]
    broken = assembly.validate_capture(_document(digests=digests))
    assert assembly.RULE_DIGEST_COVER in broken


def test_rule_eight_catches_a_stale_whole_digest() -> None:
    """A whole digest that no longer matches its sections is stale."""
    document = _document()
    digests = dict(document["digests"])
    digests[assembly.DIGEST_WHOLE] = "0" * 64
    broken = assembly.validate_capture(_document(digests=digests))
    assert assembly.RULE_DIGEST_COVER in broken


def test_rule_eight_reads_the_extras_digest_at_tier_three() -> None:
    """A tier 3 document must also carry an extras digest."""
    assert assembly.validate_capture(_document(_sections(extras=_extra_sections()))) == []


# ---------------------------------------------------------------------------
# The partial path
# ---------------------------------------------------------------------------


def test_guarded_call_returns_the_read_value() -> None:
    """A good read reports no reason."""
    value, reasons = assembly.guarded_call("devices", lambda: [1, 2])
    assert value == [1, 2]
    assert reasons == []


def test_guarded_call_turns_a_failure_into_one_reason() -> None:
    """A failed section produces exactly one reason entry."""

    def _boom() -> None:
        raise RuntimeError("the cloud said no")

    value, reasons = assembly.guarded_call("alarms", _boom)
    assert value is None
    assert len(reasons) == 1
    assert reasons[0]["section"] == "alarms"
    assert reasons[0]["reason"] == assembly.REASON_READ_FAILED


def test_guarded_call_reads_the_http_status() -> None:
    """The reason carries the status of the cloud call."""

    class _Failure(RuntimeError):
        """An error that carries a status code."""

        status_code = 503

    def _boom() -> None:
        raise _Failure("the cloud refused")

    value, reasons = assembly.guarded_call("alarms", _boom)
    assert value is None
    assert reasons[0]["http_status"] == 503


def test_http_status_of_reads_a_response_attribute() -> None:
    """Some clients hold the status on a response object."""

    class _Response:
        """A small stand-in for a cloud answer."""

        status_code = 404

    error = RuntimeError("not found")
    error.response = _Response()  # type: ignore[attr-defined]
    assert assembly.http_status_of(error) == 404
    assert assembly.http_status_of(RuntimeError("plain")) == assembly.HTTP_STATUS_NONE


def test_a_failed_section_does_not_abort_the_capture() -> None:
    """The capture still holds every section that did read."""

    def _boom() -> None:
        raise RuntimeError("the guest call failed")

    _value, reasons = assembly.guarded_call(assembly.SECTION_GUEST, _boom)
    document = assembly.build_capture(
        assembly.CaptureIdentity(RUN_ID, 1, ACTOR),
        assembly.SiteIdentity("org-1", "Test Org", "site-1", "Test Site"),
        assembly.CaptureWindow(STARTED_AT, FINISHED_AT, 1.0),
        _sections(),
        reasons,
    )
    assert document["capture_status"] == assembly.STATUS_PARTIAL
    assert len(document["devices"]) == 3
    assert document["counts"]["devices_total"] == 3
    assert assembly.validate_capture(document) == []


def test_partial_reasons_is_empty_when_the_capture_is_complete() -> None:
    """A complete capture carries an empty list, never a null."""
    document = _document()
    assert document["capture_status"] == assembly.STATUS_COMPLETE
    assert document["partial_reasons"] == []


def test_one_reason_joins_the_document_for_each_failed_section() -> None:
    """Two failed sections produce two entries and no more."""
    reasons = [
        assembly.partial_reason(extras.SECTION_ALARMS, extras.REASON_CALL_FAILED, 503),
        assembly.partial_reason(extras.SECTION_TUNNELS, extras.REASON_ERROR_STATUS, 500),
    ]
    document = _document(partial_reasons=reasons)
    assert len(document["partial_reasons"]) == 2
    assert {entry["section"] for entry in document["partial_reasons"]} == {
        extras.SECTION_ALARMS,
        extras.SECTION_TUNNELS,
    }


def test_a_reason_holds_the_three_named_fields() -> None:
    """The builder writes section, reason, and http_status."""
    entry = assembly.partial_reason("devices", assembly.REASON_READ_FAILED, 429)
    assert set(entry) == {"section", "reason", "http_status"}
    assert entry["http_status"] == 429


def test_extra_reasons_names_each_failed_tier_three_section() -> None:
    """A good tier 3 section produces no reason."""
    sections = {
        extras.SECTION_ALARMS: extras.ExtraSection(extras.SECTION_ALARMS, (), extras.REASON_CALL_FAILED, 503),
        extras.SECTION_RADIOS: extras.ExtraSection(extras.SECTION_RADIOS, (), extras.REASON_READ, 0),
    }
    reasons = assembly.extra_reasons(sections)
    assert len(reasons) == 1
    assert reasons[0]["section"] == extras.SECTION_ALARMS
    assert reasons[0]["reason"] == extras.REASON_CALL_FAILED
    assert reasons[0]["http_status"] == 503


def test_status_is_failed_when_no_section_read() -> None:
    """A capture that read nothing is not partial. It is failed."""
    empty = assembly.CaptureSections()
    reasons = [assembly.partial_reason("devices", assembly.REASON_READ_FAILED, 500)]
    assert assembly.resolve_status(empty, reasons) == assembly.STATUS_FAILED
    assert assembly.resolve_status(_sections(), reasons) == assembly.STATUS_PARTIAL
    assert assembly.resolve_status(empty, []) == assembly.STATUS_COMPLETE


# ---------------------------------------------------------------------------
# The call groups
# ---------------------------------------------------------------------------


def test_the_module_names_six_call_groups() -> None:
    """The capture fans out over six groups."""
    assert len(assembly.CALL_GROUPS) == 6
    assert assembly.GROUP_DEVICES in assembly.CALL_GROUPS
    assert assembly.GROUP_TIER_THREE in assembly.CALL_GROUPS


def test_run_call_groups_uses_the_injected_pool() -> None:
    """Every group runs through the pool seam and reports its result."""
    seen: list[Any] = []

    def _runner(work_items: list[Any], worker_function: Any, batch_description: str) -> tuple[list[Any], list[Any]]:
        seen.append(list(work_items))
        return _sequential_executor(work_items, worker_function, batch_description)

    groups = [assembly.CallGroup(name, lambda name=name: f"read-{name}") for name in assembly.CALL_GROUPS]
    results = assembly.run_call_groups(groups, _runner)
    assert len(seen[0]) == 6
    assert set(results) == set(assembly.CALL_GROUPS)
    assert results[assembly.GROUP_DEVICES].value == f"read-{assembly.GROUP_DEVICES}"


def test_the_pages_of_one_group_stay_sequential() -> None:
    """A cursor page must never run beside another page of the same call."""
    order: list[str] = []

    def _reader(page: str) -> Any:
        """Build one page read that records its own order."""

        def _read() -> str:
            order.append(page)
            return page

        return _read

    results = assembly.sequential_reads([_reader(page) for page in ("page-1", "page-2", "page-3")])
    assert order == ["page-1", "page-2", "page-3"]
    assert results == ["page-1", "page-2", "page-3"]


def test_a_failed_read_inside_a_group_becomes_a_partial_reason() -> None:
    """The group finishes and names the loss."""

    def _boom() -> None:
        raise RuntimeError("the port call failed")

    groups = [assembly.CallGroup(assembly.GROUP_PORTS, _boom)]
    results = assembly.run_call_groups(groups, _sequential_executor)
    assert results[assembly.GROUP_PORTS].value is None
    assert results[assembly.GROUP_PORTS].reasons[0]["reason"] == assembly.REASON_READ_FAILED


def test_a_lost_group_becomes_a_partial_reason() -> None:
    """A group that the pool never finished still reaches the document."""
    group = assembly.CallGroup(assembly.GROUP_WIRELESS_SEARCH, lambda: "unused")

    def _loses_everything(
        work_items: list[Any], worker_function: Any, batch_description: str
    ) -> tuple[list[Any], list[Any]]:
        del worker_function, batch_description
        return [], list(work_items)

    results = assembly.run_call_groups([group], _loses_everything)
    reasons = assembly.group_reasons(results)
    assert len(reasons) == 1
    assert reasons[0]["section"] == assembly.GROUP_WIRELESS_SEARCH
    assert reasons[0]["reason"] == assembly.REASON_GROUP_FAILED


def test_group_reasons_collects_every_reason() -> None:
    """Two failed groups produce two reasons."""

    def _boom() -> None:
        raise RuntimeError("no")

    groups = [assembly.CallGroup(assembly.GROUP_PORTS, _boom), assembly.CallGroup(assembly.GROUP_TIER_THREE, _boom)]
    results = assembly.run_call_groups(groups, _sequential_executor)
    assert len(assembly.group_reasons(results)) == 2


def test_group_value_returns_the_default_after_a_failure() -> None:
    """A caller reads an empty list instead of a null."""

    def _boom() -> None:
        raise RuntimeError("no")

    results = assembly.run_call_groups([assembly.CallGroup(assembly.GROUP_DEVICES, _boom)], _sequential_executor)
    assert assembly.group_value(results, assembly.GROUP_DEVICES, []) == []
    assert assembly.group_value(results, "absent", "fallback") == "fallback"


# ---------------------------------------------------------------------------
# The client rows
# ---------------------------------------------------------------------------


def test_fill_device_names_reads_the_device_index() -> None:
    """The client reader leaves the name empty and the assembly fills it."""
    record = ClientRecord(
        mac=CLIENT_MAC,
        identity=ClientIdentity(hostname="desk-1"),
        attachment=ClientAttachment(device_mac=SWITCH_MAC, port_id="ge-0/0/1"),
    )
    rows = assembly.fill_device_names([record], {SWITCH_MAC: _index_entry(SWITCH_MAC, "switch")})
    assert rows[0]["device_name"] == f"switch-{SWITCH_MAC[-4:]}"
    assert rows[0]["mac"] == CLIENT_MAC


def test_fill_device_names_matches_across_two_address_forms() -> None:
    """The index key and the client address may arrive in different forms."""
    record = ClientRecord(mac=CLIENT_MAC, attachment=ClientAttachment(device_mac=SWITCH_MAC))
    rows = assembly.fill_device_names([record], {"5C:5B:35:0E:00:01": _index_entry(SWITCH_MAC, "switch")})
    assert rows[0]["device_name"] == f"switch-{SWITCH_MAC[-4:]}"


def test_fill_device_names_leaves_an_unknown_device_without_a_name() -> None:
    """A client on a device outside the index keeps no name."""
    record = ClientRecord(mac=CLIENT_MAC, attachment=ClientAttachment(device_mac="000000000000"))
    rows = assembly.fill_device_names([record], {SWITCH_MAC: _index_entry(SWITCH_MAC, "switch")})
    assert "device_name" not in rows[0]


@pytest.mark.parametrize("ordinal", [1, 2, 3, 12])
def test_every_ordinal_produces_a_valid_document(ordinal: int) -> None:
    """The builder holds the rules for a pre-check, a post-check, and a repeat."""
    document = assembly.build_capture(
        assembly.CaptureIdentity(RUN_ID, ordinal, ACTOR),
        assembly.SiteIdentity("org-1", "Test Org", "site-1", "Test Site"),
        assembly.CaptureWindow(STARTED_AT, FINISHED_AT, 1.0),
        _sections(),
    )
    assert assembly.validate_capture(document) == []
    assert document["_key"] == f"cap-{RUN_HEX}-{ordinal:02d}"
