"""Guardrail: the documented test-container policy stays true (issue #2540).

Why:
    Issue #2526 added the policy that governs a test container, a debug
    container, and an end-to-end container. That policy lives in Markdown only,
    so nothing holds it true. The port table in the policy names the ports that
    `compose.yml` publishes, and the policy tells a reader to pick an ephemeral
    port in the range 9600 through 9699.

    Both statements go stale on the day a service moves. The document says so
    itself, because it tells the reader that the table can drift. These tests
    read `compose.yml` and the documents, then fail when the two disagree.

    Issue #2059 records the collision that the policy prevents. A second project
    took the vendor default port, and the upgrade portal then read a foreign
    database as its own store.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")  # PyYAML ships with the project requirements.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPOSITORY_ROOT / "compose.yml"
POLICY_PATH = REPOSITORY_ROOT / ".github" / "copilot-instructions.md"
COMPOSE_HELPER_PATH = REPOSITORY_ROOT / "scripts" / "compose.ps1"
CORPORATE_CA_COMPOSE_PATH = (
    REPOSITORY_ROOT / "deploy" / "compose.corporate-ca.yml"
)  # Read the deployment overlay from the existing deployment folder.
LOGGER = logging.getLogger(__name__)

EPHEMERAL_FIRST_PORT = 9600  # The policy tells a reader to start here.
EPHEMERAL_LAST_PORT = 9699  # The policy tells a reader to stop here.

# The name format that an ephemeral container carries. A reader opens the issue
# from the name, so the marker must stay in the authoritative text.
NAME_MARKER = "misthelper-tmp-"

# A command that removes every unused volume, including the two that hold every
# capture and every upgrade run. Neither one may sit in a copy-pasteable block.
DESTRUCTIVE_PATTERNS = ("volume prune", "down -v")
PRODUCTION_STORE_VOLUMES = frozenset(
    {"misthelper-arangodb-data", "misthelper-redis-data"}
)  # These volumes hold production data and must never appear in cleanup commands.
VOLUME_RM_PATTERN = re.compile(r"\bpodman\s+volume\s+rm\s+([^\r\n]+)")  # Match each documented volume cleanup command.

# Every document that states the policy or links to it. A code block in one of
# these files is a command that a reader copies. The `managing-podman` skill
# left this list when the agent skills moved to the user level at
# ~/.copilot/skills, because a repository test cannot read a home directory.
POLICY_DOCUMENTS = (
    Path(".github") / "copilot-instructions.md",
    Path(".github") / "instructions" / "git-flow-multi-agent.instructions.md",
    Path("documentation") / "container-deployment.md",
    Path("documentation") / "development-setup.md",
    Path("documentation") / "wiki" / "Container-Setup.md",
    Path("agents.md"),
    Path("CLAUDE.md"),
    Path("README.md"),
)


def published_port_tokens() -> dict[str, str]:
    """Read every host port that `compose.yml` publishes.

    Returns:
        A mapping of the port token to the service that publishes it. A token
        reads `2200` for TCP and `1161/udp` for UDP, which is the form the
        policy table uses.
    """
    document = dict(yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8")))  # Read the source of truth.
    tokens: dict[str, str] = {}  # Collect one entry for each published mapping.
    for name, service in document["services"].items():  # Walk every service in the file.
        for mapping in service.get("ports", []):  # A service can publish more than one port.
            text = str(mapping)  # A mapping can parse as a string or as a number.
            host_side = text.split(":")[0]  # The host port always sits before the first colon.
            protocol = "/udp" if text.endswith("/udp") else ""  # The policy table marks UDP only.
            tokens[f"{host_side}{protocol}"] = name  # Record the token against its owner.
    return tokens


def code_blocks(text: str) -> list[str]:
    """Return the body of every fenced code block in one Markdown document.

    Args:
        text: The full text of the document.

    Returns:
        The body of each fenced block, without the fence lines.
    """
    return re.findall(r"```[^\n]*\n(.*?)```", text, flags=re.DOTALL)  # Capture the body between the fences.


@pytest.fixture(scope="module")
def policy_text() -> str:
    """Read the authoritative policy document one time for this module.

    Returns:
        The full text of `.github/copilot-instructions.md`.
    """
    return POLICY_PATH.read_text(encoding="utf-8")


class TestPolicyStatesItsRules:
    """The authoritative section names the format and the range that it requires."""

    def test_the_authoritative_section_exists(self, policy_text: str) -> None:
        """Every other document points at this section, so a rename breaks each link."""
        assert "### Test and Debug Containers" in policy_text

    def test_the_section_names_the_container_name_format(self, policy_text: str) -> None:
        """Without the marker a reader cannot learn which name an ephemeral container takes."""
        assert NAME_MARKER in policy_text

    def test_the_section_names_the_ephemeral_range(self, policy_text: str) -> None:
        """The range is the one number pair that keeps a test container off a live port."""
        assert f"{EPHEMERAL_FIRST_PORT} through {EPHEMERAL_LAST_PORT}" in policy_text


class TestPortTableMatchesCompose:
    """The table and the compose file name the same ports."""

    def test_every_published_port_appears_in_the_table(self, policy_text: str) -> None:
        """A missing row lets a reader pick a port that the stack already holds."""
        table = policy_text.split("### Test and Debug Containers")[1]  # Read the policy section only.
        for token, service in published_port_tokens().items():  # Check each port the stack publishes.
            assert f"| {token} |" in table, f"The policy table omits port {token}, which {service} publishes"

    def test_the_ephemeral_range_holds_no_published_port(self) -> None:
        """The policy sends every test container into this range, so it must stay free."""
        for token, service in published_port_tokens().items():  # Check each port the stack publishes.
            host_port = int(token.split("/")[0])  # Drop the protocol suffix before the comparison.
            in_range = EPHEMERAL_FIRST_PORT <= host_port <= EPHEMERAL_LAST_PORT  # Test the policy window.
            assert not in_range, f"{service} publishes {host_port}, inside the ephemeral range"


class TestNoDestructiveCommandInABlock:
    """No document offers a command that removes the two data volumes."""

    @pytest.mark.parametrize("relative_path", POLICY_DOCUMENTS, ids=lambda path: str(path))
    def test_no_code_block_removes_every_volume(self, relative_path: Path) -> None:
        """A reader copies a block without reading the warning under it."""
        document = REPOSITORY_ROOT / relative_path  # Resolve the path against the repository root.
        if not document.exists():  # A document can move, and a missing file is not a policy break.
            pytest.skip(f"{relative_path} is absent")
        for block in code_blocks(document.read_text(encoding="utf-8")):  # Read each fenced block.
            for pattern in DESTRUCTIVE_PATTERNS:  # Check both destructive forms.
                assert pattern not in block, f"{relative_path} offers `{pattern}` in a code block"

    @pytest.mark.parametrize("relative_path", POLICY_DOCUMENTS, ids=lambda path: str(path))
    def test_no_code_block_removes_a_production_store_volume(self, relative_path: Path) -> None:
        """A cleanup block must not name a volume that stores production records."""
        LOGGER.info("Checking cleanup blocks in %s", relative_path)  # Log the document under test.
        document = REPOSITORY_ROOT / relative_path  # Resolve the document path for a stable read.
        if not document.exists():  # Treat an absent optional document as outside the policy set.
            pytest.skip(f"{relative_path} is absent")  # Skip the document that is not in this checkout.
        blocks = code_blocks(document.read_text(encoding="utf-8"))  # Read each copy-paste command block.
        LOGGER.debug("Found %s code blocks in %s", len(blocks), relative_path)  # Record the block count.
        for block in blocks:  # Check each command block because a reader can copy any one block.
            for volume in PRODUCTION_STORE_VOLUMES:  # Check each protected production store volume.
                unsafe = f"podman volume rm {volume}"  # Build the exact unsafe command form.
                assert unsafe not in block, f"{relative_path} removes {volume}"

    @pytest.mark.parametrize("relative_path", POLICY_DOCUMENTS, ids=lambda path: str(path))
    def test_volume_cleanup_commands_target_ephemeral_volumes(self, relative_path: Path) -> None:
        """A volume cleanup command must target only the issue-scoped test volume."""
        LOGGER.info("Checking volume cleanup targets in %s", relative_path)  # Log the document under test.
        document = REPOSITORY_ROOT / relative_path  # Resolve the document path for a stable read.
        if not document.exists():  # Treat an absent optional document as outside the policy set.
            pytest.skip(f"{relative_path} is absent")  # Skip the document that is not in this checkout.
        blocks = code_blocks(document.read_text(encoding="utf-8"))  # Read each copy-paste command block.
        LOGGER.debug("Found %s code blocks in %s", len(blocks), relative_path)  # Record the block count.
        for block in blocks:  # Check each command block because a reader can copy any one block.
            for match in VOLUME_RM_PATTERN.finditer(block):  # Read each documented volume removal.
                target = match.group(1).strip()  # Extract the target name from the command line.
                assert NAME_MARKER in target, f"{relative_path} removes non-ephemeral volume {target}"

    def test_authoritative_cleanup_includes_empty_container_and_volume_checks(self, policy_text: str) -> None:
        """The proof must show that no temporary container or volume remains."""
        LOGGER.info("Checking authoritative cleanup proof commands")  # Log the policy proof check.
        section = policy_text.split("### Test and Debug Containers")[1]  # Limit the check to the policy.
        LOGGER.debug("Authoritative policy section length is %s", len(section))  # Record the checked size.
        assert 'podman ps -a --filter "name=misthelper-tmp-"' in section
        assert 'podman volume ls --filter "name=misthelper-tmp-"' in section


class TestCorporateCaAutomation:
    """The TLS proxy workflow must use the compose helper, not a direct run."""

    def test_compose_helper_supports_the_corporate_ca_overlay(self) -> None:
        """The helper command keeps the certificate workflow inside compose."""
        LOGGER.info("Checking compose helper corporate CA support")  # Log the helper script check.
        script_text = COMPOSE_HELPER_PATH.read_text(encoding="utf-8")  # Read the helper script once.
        LOGGER.debug("Compose helper script length is %s", len(script_text))  # Record the checked size.
        assert "up-corporate-ca" in script_text
        assert "deploy\\compose.corporate-ca.yml" in script_text

    def test_corporate_ca_overlay_mounts_only_the_certificate(self) -> None:
        """The overlay must add the certificate mount and leave store volumes alone."""
        LOGGER.info("Checking corporate CA compose overlay")  # Log the overlay validation.
        document = yaml.safe_load(CORPORATE_CA_COMPOSE_PATH.read_text(encoding="utf-8"))  # Parse the overlay.
        volumes = document["services"]["misthelper"]["volumes"]  # Read the application mounts only.
        LOGGER.debug("Corporate CA overlay has %s mounts", len(volumes))  # Record the mount count.
        assert volumes == [
            {
                "type": "bind",
                "source": "../zscaler-root-ca.crt",
                "target": "/usr/local/share/ca-certificates/corp-root-ca.crt",
                "read_only": True,
            }
        ]
