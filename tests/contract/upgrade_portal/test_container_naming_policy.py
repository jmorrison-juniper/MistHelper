"""Guard the container naming policy and the port policy of this project.

Why:
    Issue #1990 asked for one rule. Every container, network, and volume of this
    project carries the `misthelper-` prefix, and every published port sits
    between 1000 and 10000 and is not the vendor default.

    Issue #2059 delivered that rule in `compose.yml`. The rule then leaked. One
    fallback in `src/upgrade_portal/runtime/dependencies.py` still named the
    vendor port 8529, and two host fallbacks still named the unprefixed host
    `arangodb`.

    A fallback that names a vendor default reaches whatever answers on that port.
    `compose.yml` records the case: a container named `truck-arangodb` from
    another project held port 8529, and the portal read that foreign database as
    its own store.

    These tests keep the rule applied in the source and in the compose file at
    the same time.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = REPOSITORY_ROOT / "compose.yml"
SOURCE_FOLDER = REPOSITORY_ROOT / "src"

PREFIX = "misthelper-"  # Every name of this project starts here.
LOWEST_PORT = 1000  # The floor that issue #1990 sets.
HIGHEST_PORT = 10000  # The ceiling that issue #1990 sets.

# The vendor default of each service this project runs. A source file that names
# one of these reaches another project rather than this one.
VENDOR_DEFAULT_PORTS = (8529, 6379)

# The unprefixed host names that a fallback used to carry. The pattern names the
# fallback form on purpose. The bare word `arangodb` is also a backend marker in
# `src/db/router.py`, and that marker names no host.
UNPREFIXED_HOSTS = ('or "arangodb"', "or 'arangodb'", 'or "redis-stack"', "or 'redis-stack'")

PUBLISHED_PORT = re.compile(r"^(\d+):")  # The host side of a compose port mapping.


def code_without_comments(text: str) -> str:
    """Drop every comment from one Python file.

    Why:
        The source explains each port choice in a comment, and several of those
        comments name the vendor default on purpose. A scan that reads a comment
        reports the explanation as the fault it warns about.

    Args:
        text: The whole file.

    Returns:
        The same file with the text after each number sign removed.
    """
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())  # One split for each line.


def compose_document() -> dict:
    """Read the compose file as a mapping.

    Returns:
        The whole compose document.
    """
    return yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))


def source_files() -> list[Path]:
    """List every Python file of the application source.

    Returns:
        The files, sorted, so a failure names the same file every run.
    """
    return sorted(SOURCE_FOLDER.rglob("*.py"))


class TestTheComposeFileKeepsThePolicy:
    """Every name carries the prefix, and every published port sits in range."""

    def test_every_service_and_container_carries_the_prefix(self) -> None:
        """A service name without the prefix can collide with another project."""
        services = compose_document()["services"]
        wrong = [
            name
            for name, body in services.items()  # Every service of the stack.
            if not str(body.get("container_name", "")).startswith(PREFIX)  # The runtime name is what collides.
        ]
        assert not wrong, f"These services name a container without the prefix: {wrong}."

    def test_every_network_and_volume_carries_the_prefix(self) -> None:
        """A shared network or volume name can collide in the same way."""
        document = compose_document()
        named = list(document.get("networks", {}).values()) + list(document.get("volumes", {}).values())
        wrong = [str(body.get("name", "")) for body in named if not str(body.get("name", "")).startswith(PREFIX)]
        assert not wrong, f"These networks or volumes drop the prefix: {wrong}."

    def test_every_published_port_sits_in_the_stated_range(self) -> None:
        """A port outside the range is more likely to meet another project."""
        outside = []
        for name, body in compose_document()["services"].items():  # Every service of the stack.
            for mapping in body.get("ports", []):  # Every published port of that service.
                found = PUBLISHED_PORT.match(str(mapping))  # The host side is the side that collides.
                if found and not LOWEST_PORT <= int(found.group(1)) <= HIGHEST_PORT:
                    outside.append(f"{name} publishes {mapping}")
        assert not outside, f"These ports sit outside {LOWEST_PORT} to {HIGHEST_PORT}: {outside}."

    def test_no_service_publishes_a_vendor_default_port(self) -> None:
        """A vendor default port is the port every other project also publishes."""
        published = []
        for name, body in compose_document()["services"].items():  # Every service of the stack.
            for mapping in body.get("ports", []):  # Every published port of that service.
                found = PUBLISHED_PORT.match(str(mapping))  # Read the host side only.
                if found and int(found.group(1)) in VENDOR_DEFAULT_PORTS:
                    published.append(f"{name} publishes {mapping}")
        assert not published, f"These services publish a vendor default port: {published}."


class TestTheSourceKeepsThePolicy:
    """No fallback in the application may name a vendor port or an unprefixed host."""

    @pytest.mark.parametrize("port", VENDOR_DEFAULT_PORTS)
    def test_no_source_file_names_a_vendor_default_port(self, port: int) -> None:
        """A fallback that names a vendor port reaches another project."""
        naming = [
            str(path.relative_to(REPOSITORY_ROOT))
            for path in source_files()  # Every application file.
            if str(port) in code_without_comments(path.read_text(encoding="utf-8"))  # The code alone.
        ]
        assert not naming, (
            f"These files name the vendor default port {port}. Use the project port instead. See issue #1990. "
            f"Files: {naming}."
        )

    def test_no_source_file_names_an_unprefixed_service_host(self) -> None:
        """A fallback host without the prefix can reach another project."""
        naming = []
        for path in source_files():  # Every application file.
            text = code_without_comments(path.read_text(encoding="utf-8"))  # The code alone.
            if any(host in text for host in UNPREFIXED_HOSTS):  # Any quoted bare host name.
                naming.append(str(path.relative_to(REPOSITORY_ROOT)))
        assert not naming, f"These files name a service host without the prefix: {naming}. See issue #1990."
