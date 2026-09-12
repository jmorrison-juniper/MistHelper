"""Guardrail: the compose file keeps the project naming and port policy (issue #2059).

Why:
    `compose.yml` used to name two containers `arangodb` and `redis-stack` and
    publish them on the vendor default ports. A different project on the same
    workstation took port 8529 with a container named `truck-arangodb`, so the
    MistHelper container could not bind and the upgrade portal read the foreign
    database as its own store.

    A comment cannot hold that policy. These tests read the file and fail when a
    later edit reintroduces a generic name, a vendor default port, or a bridge
    with no subnet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")  # PyYAML ships with the project requirements.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPOSITORY_ROOT / "compose.yml"

PREFIX = "misthelper"  # Every service, container, network, and volume starts with this word.

LOWEST_ALLOWED_PORT = 1000  # The policy floor. Below it sits the well-known range.
HIGHEST_ALLOWED_PORT = 10000  # The policy ceiling.

# The vendor default of each service this project runs. A published port that
# equals one of these numbers is the collision the policy removes.
VENDOR_DEFAULT_PORTS = frozenset({8529, 6379, 8001, 11434})

# The three ports that predate the policy and already satisfy it. None is a
# vendor default, and each one is named in the README and in the browser tests.
GRANDFATHERED_PORTS = frozenset({2200, 8055, 8056})


@pytest.fixture(scope="module")
def compose() -> dict[str, Any]:
    """Read the compose file once for every test in this module.

    Returns:
        The parsed document.
    """
    return dict(yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8")))


def published_ports(service: dict[str, Any]) -> list[int]:
    """Return the host-side port of every mapping one service publishes.

    Args:
        service: One service block from the compose document.

    Returns:
        The host port of each mapping, as an integer.
    """
    return [int(str(mapping).split(":")[0]) for mapping in service.get("ports", [])]


class TestServiceNaming:
    """Every name carries the project prefix, so no second project can take it."""

    def test_every_service_name_carries_the_prefix(self, compose: dict[str, Any]) -> None:
        """A service name is also the DNS name on the network, so it needs the prefix."""
        for name in compose["services"]:
            assert name.startswith(PREFIX), f"The service {name} does not start with {PREFIX}"

    def test_every_container_name_carries_the_prefix(self, compose: dict[str, Any]) -> None:
        """A container name is global to the runtime, so a generic name collides."""
        for name, service in compose["services"].items():
            container = service.get("container_name", "")
            assert container.startswith(PREFIX), f"The container of {name} is named {container!r}"

    def test_no_generic_name_returns(self, compose: dict[str, Any]) -> None:
        """These two names caused the reported collision, so neither may return."""
        names = set(compose["services"]) | {s.get("container_name") for s in compose["services"].values()}
        assert "arangodb" not in names
        assert "redis-stack" not in names

    def test_every_volume_carries_the_prefix(self, compose: dict[str, Any]) -> None:
        """A volume holds the data, so a shared name would let a second project write into it."""
        for key, volume in compose["volumes"].items():
            assert key.startswith(PREFIX), f"The volume key {key} does not start with {PREFIX}"
            assert str(volume.get("name", "")).startswith(PREFIX), f"The volume {key} has no prefixed name"


class TestPortPolicy:
    """Every published port sits in range and is not a vendor default."""

    def test_no_service_publishes_a_vendor_default_port(self, compose: dict[str, Any]) -> None:
        """A vendor default is the port every other project publishes too."""
        for name, service in compose["services"].items():
            for port in published_ports(service):
                assert port not in VENDOR_DEFAULT_PORTS, f"The service {name} publishes the vendor port {port}"

    def test_every_published_port_sits_in_the_allowed_range(self, compose: dict[str, Any]) -> None:
        """The policy fixes the range at 1000 through 10000."""
        for name, service in compose["services"].items():
            for port in published_ports(service):
                if port in GRANDFATHERED_PORTS:
                    continue  # WHY: named in the README and the browser tests, and already compliant.
                assert LOWEST_ALLOWED_PORT <= port <= HIGHEST_ALLOWED_PORT, f"{name} publishes {port}"

    def test_no_two_services_publish_the_same_port(self, compose: dict[str, Any]) -> None:
        """Two services on one host port cannot both bind, so one would fail to start."""
        seen = [port for service in compose["services"].values() for port in published_ports(service)]
        assert len(seen) == len(set(seen)), f"A host port is published twice: {sorted(seen)}"


class TestStoreAddresses:
    """The application reads the same ports the stores bind."""

    def test_the_application_points_at_the_prefixed_stores(self, compose: dict[str, Any]) -> None:
        """A stale address here would send the portal to a foreign database."""
        environment = compose["services"]["misthelper"]["environment"]
        assert "ARANGO_HOST=http://misthelper-arangodb:9529" in environment
        assert "REDIS_HOST=misthelper-redis" in environment
        assert "REDIS_PORT=9379" in environment

    def test_the_container_never_starts_a_sibling(self, compose: dict[str, Any]) -> None:
        """A container cannot start its sibling, so auto-start is off inside one."""
        assert "CAPTURE_AUTOSTART=0" in compose["services"]["misthelper"]["environment"]

    def test_each_store_health_check_names_the_project_port(self, compose: dict[str, Any]) -> None:
        """Both client tools default to the vendor port, so each probe must name the real one."""
        arango_probe = " ".join(compose["services"]["misthelper-arangodb"]["healthcheck"]["test"])
        assert "9529" in arango_probe
        redis_probe = " ".join(compose["services"]["misthelper-redis"]["healthcheck"]["test"])
        assert "9379" in redis_probe


class TestNetwork:
    """The project network holds its own address range."""

    def test_the_network_pins_a_subnet(self, compose: dict[str, Any]) -> None:
        """A bridge with no subnet takes a pool range, which a second project can also take."""
        network = compose["networks"]["misthelper-network"]
        subnets = [entry["subnet"] for entry in network["ipam"]["config"]]
        assert subnets, "The project network pins no subnet"

    def test_the_network_carries_an_explicit_name(self, compose: dict[str, Any]) -> None:
        """Without a name the runtime prefixes the directory, so the name changes per checkout."""
        assert compose["networks"]["misthelper-network"]["name"] == "misthelper-network"

    def test_every_service_joins_the_project_network(self, compose: dict[str, Any]) -> None:
        """A service outside the network would reach the others only through the host."""
        for name, service in compose["services"].items():
            assert "misthelper-network" in service.get("networks", []), f"{name} is off the project network"
