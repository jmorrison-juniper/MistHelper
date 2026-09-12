"""Test the compose separation that issue #2272 asked for.

The old `compose.yml` held an application build section. Therefore, a plain
`podman-compose up -d` could overwrite the published tag with a local build.

The application build section now lives in `compose.build.yml`. The helper
script reads that file only when an operator requests a local build.

The header of `compose.yml` once stated the opposite. It said that naming the
image stops a local build, and it does not. These tests hold the correction in
place, because a reader who trusts a false comment runs the wrong command.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

# The three files that carry the repair, and the script that enforces it.
_ROOT = Path(__file__).resolve().parents[3]
_COMPOSE = _ROOT / "compose.yml"
_COMPOSE_BUILD = _ROOT / "compose.build.yml"
_GUIDE = _ROOT / "documentation" / "container-deployment.md"
_SCRIPT = _ROOT / "scripts" / "compose.ps1"

# The sentence that the old header carried. It is false under podman-compose, so
# no file may state it again.
_RETIRED_CLAIM = "so a compose run uses it instead of a stale local build"


@pytest.fixture(name="compose_text", scope="module")
def fixture_compose_text() -> str:
    """Read the compose file."""
    logging.info("Reading the compose file at %s", _COMPOSE)  # Report the read before the work.
    text = _COMPOSE.read_text(encoding="utf-8")
    logging.debug("The compose file holds %d characters", len(text))  # Record the size.
    return text


@pytest.fixture(name="guide_text", scope="module")
def fixture_guide_text() -> str:
    """Read the container deployment guide."""
    logging.info("Reading the deployment guide at %s", _GUIDE)  # Report the read before the work.
    text = _GUIDE.read_text(encoding="utf-8")
    logging.debug("The guide holds %d characters", len(text))  # Record the size.
    return text


@pytest.fixture(name="compose_build_text", scope="module")
def fixture_compose_build_text() -> str:
    """Read the build file that holds the build section."""
    logging.info("Reading the build file at %s", _COMPOSE_BUILD)  # Report the read before the work.
    text = _COMPOSE_BUILD.read_text(encoding="utf-8")
    logging.debug("The build file holds %d characters", len(text))  # Record the size.
    return text


@pytest.fixture(name="script_text", scope="module")
def fixture_script_text() -> str:
    """Read the helper script that enforces the split."""
    logging.info("Reading the helper script at %s", _SCRIPT)  # Report the read before the work.
    text = _SCRIPT.read_text(encoding="utf-8")
    logging.debug("The script holds %d characters", len(text))  # Record the size.
    return text


def test_the_compose_header_never_repeats_the_retired_claim(compose_text: str) -> None:
    """The header MUST NOT claim that the image key stops a local build.

    Why:
        The claim is false under podman-compose. A reader who trusts it runs a
        plain `up` and downgrades the running container.
    """
    logging.info("Checking that the retired claim is absent")  # Report the plan.

    assert _RETIRED_CLAIM not in compose_text, "the compose header must not repeat the retired claim"


def test_the_compose_header_warns_about_a_combined_build(compose_text: str) -> None:
    """The header MUST warn that a compose build section can overwrite the tag."""
    logging.info("Checking the rebuild warning of the compose header")  # Report the plan.

    assert "does not stop a rebuild" in compose_text, "the header must state that a rebuild still happens"
    assert "overwrites this" in compose_text, "the header must state that the tag moves"
    assert "#2272" in compose_text, "the header must cite the measurement"


def test_the_compose_header_names_the_safe_command(compose_text: str) -> None:
    """The header MUST name the command pair that never builds."""
    logging.info("Checking the safe command of the compose header")  # Report the plan.

    assert "podman pull ghcr.io/jmorrison-juniper/misthelper:latest" in compose_text
    assert "--no-deps misthelper" in compose_text, "the header must name the service"


def test_the_compose_header_names_the_revision_check(compose_text: str) -> None:
    """The header MUST name the label that reports the commit of a container.

    Why:
        The label is the only reading that tells a local build from the tested
        image. An operator with no such reading has to search inside the image.
    """
    logging.info("Checking the revision check of the compose header")  # Report the plan.

    assert "org.opencontainers.image.revision" in compose_text, "the header must name the label"


def test_the_compose_file_carries_no_build_section(compose_text: str) -> None:
    """The compose file MUST NOT carry a build section.

    Why:
        podman-compose builds every service that holds a build section when a
        plain `up` runs. A build section in this file can therefore overwrite
        the published tag with a local build.
    """
    logging.info("Checking that the compose file holds no build section")  # Report the plan.

    assert "build:" not in compose_text, "the compose file must not hold a build section; move it to compose.build.yml"


def test_the_build_file_holds_the_build_section(compose_build_text: str) -> None:
    """The build file MUST hold the build section that the compose file lost."""
    logging.info("Checking the build section of the build file")  # Report the plan.

    assert "context: ." in compose_build_text, "the build file must name the build context"
    assert "dockerfile: Containerfile" in compose_build_text, "the build file must name the build file"


def test_the_script_builds_only_through_the_build_file(script_text: str) -> None:
    """The script MUST build through the build file, and it MUST offer the revision check."""
    logging.info("Checking the build and revision paths of the helper script")  # Report the plan.

    assert "compose.build.yml" in script_text, "the build subcommand must load the build file"
    assert "check-revision" in script_text, "the script must offer the revision check"
    revision_message = "the revision check must read the label that names the commit"  # Explain the required label.
    assert "org.opencontainers.image.revision" in script_text, revision_message  # Hold the revision check in place.


def test_the_guide_names_the_build_separation(guide_text: str) -> None:
    """The guide MUST state that a plain `up` cannot build the application image."""
    logging.info("Checking the build separation in the guide")  # Report the plan.

    assert "A plain `up`" in guide_text, "the guide must name the default command"
    assert "cannot build the application image" in guide_text, "the guide must state the safe result"
    assert "Warning: a plain `up` rebuilds." not in guide_text, "the guide must not repeat the old behavior"
    assert "#2272" in guide_text, "the guide must cite the measurement"


def test_the_guide_names_the_revision_check(guide_text: str) -> None:
    """The guide MUST show how to read the commit that a container runs."""
    logging.info("Checking the revision check of the guide")  # Report the plan.

    assert "org.opencontainers.image.revision" in guide_text, "the guide must name the label"
    assert "git rev-parse origin/main" in guide_text, "the guide must name the value to compare against"


def test_the_guide_updates_the_checkout_before_the_pull(guide_text: str) -> None:
    """The update recipe MUST pull the code before it pulls the image.

    Why:
        An explicit local build reads the working tree. The recipe updates the
        checkout first, so a later local build does not use old code.
    """
    logging.info("Checking the order of the update recipe")  # Report the plan.
    checkout = guide_text.index("git pull")
    image = guide_text.index("podman pull ghcr.io/jmorrison-juniper/misthelper:latest")
    logging.debug("The checkout step sits at %d and the image step at %d", checkout, image)

    assert checkout < image, "the recipe must update the checkout before it pulls the image"
