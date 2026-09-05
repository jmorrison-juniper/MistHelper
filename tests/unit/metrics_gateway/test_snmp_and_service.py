"""Tests for the Net-SNMP pass_persist responder and the gateway settings."""

from __future__ import annotations

import io
import os
from typing import Any

import pytest

from src.metrics_gateway.cache import MetricsCache
from src.metrics_gateway.catalog import ROW_IDENTITY_COLUMN, MetricScope
from src.metrics_gateway.collector import MistMetricsCollector, MistStatsReader
from src.metrics_gateway.samples import MetricSnapshot
from src.metrics_gateway.service import (
    ALL_INTERFACES_HOST,
    DEFAULT_HOST,
    DEFAULT_PORT,
    GatewaySettings,
    resolve_host,
)
from src.metrics_gateway.snmp import (
    DEFAULT_BASE_OID,
    GET_REQUEST,
    GETNEXT_REQUEST,
    NO_VALUE_REPLY,
    NOT_WRITABLE_REPLY,
    PING_REPLY,
    PING_REQUEST,
    SET_REQUEST,
    TYPE_COUNTER64,
    TYPE_GAUGE,
    TYPE_STRING,
    OidTree,
    SnmpPassPersistResponder,
    format_oid,
    parse_oid,
)
from tests.unit.metrics_gateway.conftest import ORG_ID, SITE_A, build_overrides

BASE = parse_oid(DEFAULT_BASE_OID)  # The base every test OID starts with.


def _snapshot() -> MetricSnapshot:
    """Run one collector pass over the shared organization.

    Returns:
        The snapshot of the pass.
    """
    reader = MistStatsReader(session=None, overrides=build_overrides())
    return MistMetricsCollector(reader, ORG_ID).collect()


class TestOidText:
    """An OID must survive a trip through text and back."""

    def test_it_parses_a_leading_dot(self) -> None:
        """`snmpd` sends the leading dot, and an empty first part must not become a number."""
        assert parse_oid(".1.3.6") == (1, 3, 6)

    def test_it_parses_without_a_leading_dot(self) -> None:
        """A configuration file may omit the dot."""
        assert parse_oid("1.3.6") == (1, 3, 6)

    def test_a_malformed_oid_becomes_nothing(self) -> None:
        """A bad request must not stop the responder, or `snmpd` loses the whole subtree."""
        assert parse_oid(".1.3.six") == ()

    def test_it_renders_the_leading_dot(self) -> None:
        """`snmpd` expects the leading dot in the reply."""
        assert format_oid((1, 3, 6)) == ".1.3.6"

    def test_a_round_trip_keeps_the_value(self) -> None:
        """The responder parses a request and renders a reply, so both must agree."""
        assert parse_oid(format_oid(BASE)) == BASE


class TestOidTree:
    """The tree must address every reading and walk in true numeric order."""

    def test_the_walk_order_is_numeric(self) -> None:
        """A text sort puts `.10` before `.9`, and a walk built on it skips rows."""
        tree = OidTree(_snapshot())
        walked = []
        current: tuple[int, ...] = BASE
        while True:
            nxt = tree.next_oid(current)
            if nxt is None:
                break
            walked.append(nxt)
            current = nxt
        assert walked == sorted(walked)

    def test_the_walk_reaches_every_reading(self) -> None:
        """A walk that ends early hides a device from the monitoring system."""
        tree = OidTree(_snapshot())
        counted = 0
        current: tuple[int, ...] = BASE
        while (nxt := tree.next_oid(current)) is not None:
            counted += 1
            current = nxt
        assert counted == len(tree)

    def test_an_org_reading_answers_at_instance_zero(self) -> None:
        """An SNMP scalar answers at instance 0, and it is not a table row."""
        tree = OidTree(_snapshot())
        assert tree.get(BASE + (1, 2, 0)) == (TYPE_GAUGE, "2")

    def test_a_site_reading_answers_in_its_table(self) -> None:
        """A table cell answers under the entry node, at its column and its row."""
        tree = OidTree(_snapshot())
        assert tree.get(BASE + (2, 1, 10, 1)) == (TYPE_GAUGE, "42")

    def test_the_identity_column_names_the_row(self) -> None:
        """SNMP has no label, so a poller needs a column that repeats the row identity."""
        tree = OidTree(_snapshot())
        assert tree.get(BASE + (2, 1, ROW_IDENTITY_COLUMN, 1)) == (TYPE_STRING, SITE_A)

    def test_a_counter_uses_the_sixty_four_bit_type(self) -> None:
        """A Mist byte count passes 2^32 in a day, which a 32-bit counter cannot hold."""
        tree = OidTree(_snapshot())
        found = tree.get(BASE + (3, 1, 11, 2))
        assert found is not None
        assert found[0] == TYPE_COUNTER64
        assert found[1] == "5000000000"

    def test_a_ratio_takes_its_scale(self) -> None:
        """SNMP carries no fraction, so a ratio of 0.97 would otherwise arrive as 0."""
        tree = OidTree(_snapshot())
        assert tree.get(BASE + (4, 1, 3, 1)) == (TYPE_GAUGE, "9700")

    def test_an_info_reading_answers_as_text(self) -> None:
        """An informational reading carries its facts in text, because SNMP has no label."""
        tree = OidTree(_snapshot())
        assert tree.get(BASE + (2, 1, 1, 1)) == (TYPE_STRING, 'Branch "A"')

    def test_an_unknown_oid_holds_nothing(self) -> None:
        """A request outside the tree must return nothing rather than a wrong reading."""
        assert OidTree(_snapshot()).get(BASE + (9, 9, 9)) is None

    def test_an_operator_base_replaces_the_default(self) -> None:
        """The operator owns the base OID, so no unregistered number is baked in."""
        tree = OidTree(_snapshot(), base_oid=".1.3.6.1.4.1.9999")
        assert tree.get((1, 3, 6, 1, 4, 1, 9999, 1, 2, 0)) == (TYPE_GAUGE, "2")

    def test_an_empty_snapshot_builds_an_empty_tree(self) -> None:
        """A gateway that has read nothing must still answer a walk."""
        assert len(OidTree(MetricSnapshot())) == 0


class TestPassPersistProtocol:
    """The responder must speak exactly the protocol that `snmpd` expects."""

    def _responder(self) -> SnmpPassPersistResponder:
        """Build a responder over a cache that holds the shared organization.

        Returns:
            The responder.
        """
        reader = MistStatsReader(session=None, overrides=build_overrides())
        cache = MetricsCache(MistMetricsCollector(reader, ORG_ID))
        return SnmpPassPersistResponder(cache)

    def test_it_answers_a_ping(self) -> None:
        """`snmpd` tests the responder before it trusts the subtree."""
        assert self._responder().handle(PING_REQUEST, "") == [PING_REPLY]

    def test_it_refuses_a_set(self) -> None:
        """The gateway never changes Mist Cloud, so every write must be refused."""
        assert self._responder().handle(SET_REQUEST, ".1.2.3") == [NOT_WRITABLE_REPLY]

    def test_a_get_returns_three_lines(self) -> None:
        """`snmpd` reads the OID, then the type, then the value."""
        reply = self._responder().handle(GET_REQUEST, format_oid(BASE + (1, 2, 0)))
        assert reply == [format_oid(BASE + (1, 2, 0)), TYPE_GAUGE, "2"]

    def test_a_get_of_an_empty_oid_returns_nothing(self) -> None:
        """A request outside the tree must not invent a reading."""
        assert self._responder().handle(GET_REQUEST, format_oid(BASE + (7, 7, 7))) == [NO_VALUE_REPLY]

    def test_a_getnext_moves_forward(self) -> None:
        """A walk depends on `getnext` returning a strictly larger OID."""
        reply = self._responder().handle(GETNEXT_REQUEST, format_oid(BASE))
        assert parse_oid(reply[0]) > BASE

    def test_a_getnext_past_the_end_returns_nothing(self) -> None:
        """The end of the tree is how a walk knows to stop."""
        assert self._responder().handle(GETNEXT_REQUEST, ".2.3.4.5.6.7.8.9") == [NO_VALUE_REPLY]

    def test_a_malformed_oid_returns_nothing(self) -> None:
        """A bad request must not stop the responder."""
        assert self._responder().handle(GET_REQUEST, "not-an-oid") == [NO_VALUE_REPLY]

    def test_an_unknown_command_returns_nothing(self) -> None:
        """A future net-snmp verb must not stop the walk."""
        assert self._responder().handle("getbulk", ".1.2.3") == [NO_VALUE_REPLY]

    def test_the_stream_loop_answers_a_ping(self) -> None:
        """A ping is one line, so the reader must not wait for a second one."""
        stdout = io.StringIO()
        self._responder().run(io.StringIO("PING\n"), stdout)
        assert stdout.getvalue() == "PONG\n"

    def test_the_stream_loop_answers_a_get(self) -> None:
        """A get is two lines, and the OID is the second one."""
        stdout = io.StringIO()
        request = f"{GET_REQUEST}\n{format_oid(BASE + (1, 2, 0))}\n"
        self._responder().run(io.StringIO(request), stdout)
        assert stdout.getvalue().splitlines() == [format_oid(BASE + (1, 2, 0)), TYPE_GAUGE, "2"]

    def test_the_stream_loop_reads_the_third_line_of_a_set(self) -> None:
        """A set has three lines, and a reader that skips one falls out of step."""
        stdout = io.StringIO()
        request = f"{SET_REQUEST}\n.1.2.3\ninteger 5\n{PING_REQUEST}\n"
        self._responder().run(io.StringIO(request), stdout)
        assert stdout.getvalue().splitlines() == [NOT_WRITABLE_REPLY, PING_REPLY]

    def test_the_stream_loop_skips_a_blank_line(self) -> None:
        """A blank line carries no request."""
        stdout = io.StringIO()
        self._responder().run(io.StringIO("\n\nPING\n"), stdout)
        assert stdout.getvalue() == "PONG\n"

    def test_a_full_walk_returns_every_reading(self) -> None:
        """This is the request sequence that `snmpwalk` actually sends."""
        responder = self._responder()
        expected = len(responder.tree())  # The cache adds its own health readings.
        current = format_oid(BASE)
        seen = 0
        while True:
            reply = responder.handle(GETNEXT_REQUEST, current)
            if reply == [NO_VALUE_REPLY]:
                break
            current = reply[0]
            seen += 1
        assert seen == expected


class TestGatewaySettings:
    """A setting must fall back to a documented default rather than stop the tool."""

    def test_a_workstation_binds_loopback(self) -> None:
        """The endpoint asks for no password, so it must not answer the whole network."""
        assert resolve_host(None, in_container=False) == DEFAULT_HOST

    def test_a_container_binds_every_address(self) -> None:
        """A published port cannot reach a loopback bind."""
        assert resolve_host(None, in_container=True) == ALL_INTERFACES_HOST

    def test_an_operator_address_always_wins(self) -> None:
        """A reverse proxy needs a bind that neither default describes."""
        assert resolve_host("10.0.0.5", in_container=True) == "10.0.0.5"

    def test_a_blank_address_reads_as_unset(self) -> None:
        """An empty environment variable and an unset one mean the same thing."""
        assert resolve_host("   ", in_container=False) == DEFAULT_HOST

    def test_it_reads_the_organization_and_the_sites(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The site filter arrives as a comma list."""
        monkeypatch.setenv("METRICS_ORG_ID", ORG_ID)
        monkeypatch.setenv("METRICS_SITE_IDS", f" {SITE_A} , , site-c ")
        settings = GatewaySettings.from_environment()
        assert settings.org_id == ORG_ID
        assert settings.site_ids == (SITE_A, "site-c")

    def test_a_bad_port_keeps_the_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One typo must not stop an operations tool."""
        monkeypatch.setenv("METRICS_PORT", "eight-thousand")
        assert GatewaySettings.from_environment().port == DEFAULT_PORT

    def test_it_falls_back_to_the_shared_org_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The rest of MistHelper already sets `MIST_ORG_ID`."""
        monkeypatch.delenv("METRICS_ORG_ID", raising=False)
        monkeypatch.setenv("MIST_ORG_ID", "org-shared")
        assert GatewaySettings.from_environment().org_id == "org-shared"

    def test_the_default_base_oid_needs_no_registration(self) -> None:
        """The upstream README warns that its own unregistered number can collide."""
        assert DEFAULT_BASE_OID.startswith(".1.3.6.1.4.1.8072")

    def test_the_default_port_avoids_the_other_portals(self) -> None:
        """Port 8055 serves the data browser and port 8056 serves the upgrade portal."""
        assert DEFAULT_PORT not in (8055, 8056)


def test_the_web_application_serves_the_two_routes() -> None:
    """A scraper reads `/metrics`, and a container health probe reads `/healthz`."""
    from src.metrics_gateway.web import create_app

    reader = MistStatsReader(session=None, overrides=build_overrides())
    cache = MetricsCache(MistMetricsCollector(reader, ORG_ID))
    client = create_app(cache).test_client()
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert b'mist_org_sites{org_id="org-1111"} 2' in metrics.data
    assert client.get("/healthz").status_code == 200


def test_the_scrape_names_the_media_type_once() -> None:
    """Flask appends its own charset to a `mimetype`, which names `charset` twice."""
    from src.metrics_gateway.prometheus import CONTENT_TYPE
    from src.metrics_gateway.web import create_app

    reader = MistStatsReader(session=None, overrides=build_overrides())
    cache = MetricsCache(MistMetricsCollector(reader, ORG_ID))
    header = create_app(cache).test_client().get("/metrics").headers["Content-Type"]
    assert header == CONTENT_TYPE
    assert header.count("charset") == 1


def test_the_health_route_never_reads_mist_cloud() -> None:
    """A probe that calls a cloud API reports the health of the cloud, not the container."""

    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("The health route must not read Mist Cloud.")

    from src.metrics_gateway.web import create_app

    reader = MistStatsReader(session=None, overrides={"getOrgStats": _boom})
    cache = MetricsCache(MistMetricsCollector(reader, ORG_ID))
    assert create_app(cache).test_client().get("/healthz").status_code == 200


def test_the_package_exports_stay_importable() -> None:
    """A caller outside the package reads these names, so they must resolve."""
    import src.metrics_gateway as package

    for name in package.__all__:
        assert hasattr(package, name), f"The package does not export {name}."


def test_the_scope_set_covers_every_subtree() -> None:
    """A scope without a subtree number would raise during a walk."""
    from src.metrics_gateway.catalog import SUBTREE_BY_SCOPE

    assert set(SUBTREE_BY_SCOPE) == set(MetricScope)
    assert len(set(SUBTREE_BY_SCOPE.values())) == len(MetricScope)


def test_no_metrics_variable_leaks_a_credential() -> None:
    """The Mist token stays in `.env` and must never reach the monitoring system."""
    from src.metrics_gateway import service

    for name in dir(service):
        if name.endswith("_VARIABLE"):
            assert "TOKEN" not in str(getattr(service, name)).upper()
    assert "MIST_APITOKEN" not in os.environ.get("METRICS_SITE_IDS", "")
