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
import subprocess
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

# The three files that carry the repair, and the script that enforces it.
_ROOT = Path(__file__).resolve().parents[3]
_COMPOSE = _ROOT / "compose.yml"
_COMPOSE_BUILD = _ROOT / "compose.build.yml"
_GUIDE = _ROOT / "documentation" / "container-deployment.md"
_SCRIPT = _ROOT / "scripts" / "compose.ps1"
_IMAGE_INPUT_PATHS = (
    "Containerfile",
    ".dockerignore",
    "container/scripts/misthelper-session.sh",
    "container/scripts/welcome.sh",
    "container/scripts/start.sh",
    "container/scripts/write-session-env.sh",
    "zscaler-root-ca.crt",
    "requirements.txt",
    "pyproject.toml",
    "MistHelper.py",
    "__init__.py",
    "wsgi.py",
    "wsgi_capture.py",
    "src/",
    "web_portal/",
    "documentation/mist-api-openapi31json.json",
)

# The sentence that the old header carried. It is false under podman-compose, so
# no file may state it again.
_RETIRED_CLAIM = "so a compose run uses it instead of a stale local build"


@pytest.fixture(name="compose_text", scope="module")
def fixture_compose_text() -> str:
    """Read the compose file."""
    logger.info("Reading the compose file at %s", _COMPOSE)  # Report the read before the work.
    text = _COMPOSE.read_text(encoding="utf-8")
    logger.debug("The compose file holds %d characters", len(text))  # Record the size.
    return text


@pytest.fixture(name="guide_text", scope="module")
def fixture_guide_text() -> str:
    """Read the container deployment guide."""
    logger.info("Reading the deployment guide at %s", _GUIDE)  # Report the read before the work.
    text = _GUIDE.read_text(encoding="utf-8")
    logger.debug("The guide holds %d characters", len(text))  # Record the size.
    return text


@pytest.fixture(name="compose_build_text", scope="module")
def fixture_compose_build_text() -> str:
    """Read the build file that holds the build section."""
    logger.info("Reading the build file at %s", _COMPOSE_BUILD)  # Report the read before the work.
    text = _COMPOSE_BUILD.read_text(encoding="utf-8")
    logger.debug("The build file holds %d characters", len(text))  # Record the size.
    return text


@pytest.fixture(name="script_text", scope="module")
def fixture_script_text() -> str:
    """Read the helper script that enforces the split."""
    logger.info("Reading the helper script at %s", _SCRIPT)  # Report the read before the work.
    text = _SCRIPT.read_text(encoding="utf-8")
    logger.debug("The script holds %d characters", len(text))  # Record the size.
    return text


def test_the_compose_header_never_repeats_the_retired_claim(compose_text: str) -> None:
    """The header MUST NOT claim that the image key stops a local build.

    Why:
        The claim is false under podman-compose. A reader who trusts it runs a
        plain `up` and downgrades the running container.
    """
    logger.info("Checking that the retired claim is absent")  # Report the plan.

    assert _RETIRED_CLAIM not in compose_text, "the compose header must not repeat the retired claim"


def test_the_compose_header_warns_about_a_combined_build(compose_text: str) -> None:
    """The header MUST warn that a compose build section can overwrite the tag."""
    logger.info("Checking the rebuild warning of the compose header")  # Report the plan.

    assert "does not stop a rebuild" in compose_text, "the header must state that a rebuild still happens"
    assert "overwrites this" in compose_text, "the header must state that the tag moves"
    assert "#2272" in compose_text, "the header must cite the measurement"


def test_the_compose_header_names_the_safe_command(compose_text: str) -> None:
    """The header MUST name the command pair that never builds."""
    logger.info("Checking the safe command of the compose header")  # Report the plan.

    assert "podman pull ghcr.io/jmorrison-juniper/misthelper:latest" in compose_text
    assert "--no-deps misthelper" in compose_text, "the header must name the service"


def test_the_compose_header_names_the_revision_check(compose_text: str) -> None:
    """The header MUST name the label that reports the commit of a container.

    Why:
        The label is the only reading that tells a local build from the tested
        image. An operator with no such reading has to search inside the image.
    """
    logger.info("Checking the revision check of the compose header")  # Report the plan.

    assert "org.opencontainers.image.revision" in compose_text, "the header must name the label"


def test_the_compose_file_carries_no_build_section(compose_text: str) -> None:
    """The compose file MUST NOT carry a build section.

    Why:
        podman-compose builds every service that holds a build section when a
        plain `up` runs. A build section in this file can therefore overwrite
        the published tag with a local build.
    """
    logger.info("Checking that the compose file holds no build section")  # Report the plan.

    assert "build:" not in compose_text, "the compose file must not hold a build section; move it to compose.build.yml"


def test_the_build_file_holds_the_build_section(compose_build_text: str) -> None:
    """The build file MUST hold the build section that the compose file lost."""
    logger.info("Checking the build section of the build file")  # Report the plan.

    assert "context: ." in compose_build_text, "the build file must name the build context"
    assert "dockerfile: Containerfile" in compose_build_text, "the build file must name the build file"
    assert "image: ${MISTHELPER_BUILD_IMAGE:-ghcr.io/jmorrison-juniper/misthelper:latest}" in compose_build_text


def test_the_script_builds_only_through_the_build_file(script_text: str) -> None:
    """The script MUST build through the build file, and it MUST offer the revision check."""
    logger.info("Checking the build and revision paths of the helper script")  # Report the plan.
    fetch_command = 'fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"'  # Pin the remote destination.
    count_command = 'rev-list --count "HEAD..origin/main"'  # Count commits present only on main.
    refusal = "if ($BehindCommitCount -gt 0 -and -not $AllowStaleBuild)"  # Find the default stale refusal.
    provider_call = "& $Interpreter -m podman_compose -f $ComposeFile -f $BuildFile build"  # Find the image build.
    required_contract = (  # Keep related build and revision checks together.
        "compose.build.yml",
        "check-revision",
        "org.opencontainers.image.revision",
        "git -C $RepositoryRoot diff --name-only",
        "none changes an image input",
        "Changed image inputs:",
        fetch_command,
        'Write-Verbose "Fetched origin/main successfully."',
        count_command,
        'throw "Could not fetch origin/main',
        "Could not compare HEAD with origin/main",
        "commit(s) behind origin/main",
        refusal,
        '$ComposeArguments -contains "--allow-stale"',
        '$BuildImageTag = "misthelper:local"',
        "finally {",
        provider_call,
    )

    assert all(contract in script_text for contract in required_contract), "the script must keep all build contracts"
    assert script_text.index(fetch_command) < script_text.index(count_command) < script_text.index(refusal)
    assert script_text.index(refusal) < script_text.index(provider_call), "the refusal must precede the provider"
    assert f"{provider_call} @ComposeArguments" not in script_text, "the override must not reach the provider"


def _git(repository: Path, *arguments: str) -> str:
    """Run one Git command in a temporary repository."""
    result = subprocess.run(  # Run Git without a container or network.
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )  # Capture output for a direct decision assertion.
    return result.stdout.strip()  # Return only the command result text.


def _make_revision_repository(tmp_path: Path) -> tuple[Path, str, str]:
    """Create two commits with one image input and one unrelated file."""
    repository = tmp_path / "revision-repository"  # Keep Git state inside pytest's temporary directory.
    repository.mkdir()  # Create the isolated repository directory.
    _git(repository, "init", "--initial-branch=main")  # Create the test branch.
    _git(repository, "config", "user.email", "test@example.com")  # Set the test author.
    _git(repository, "config", "user.name", "Test User")  # Set the test author name.
    (repository / "src").mkdir()  # Create an image input directory.
    (repository / "src" / "app.py").write_text("one\n", encoding="utf-8")  # Add an image input.
    (repository / "documentation.md").write_text("one\n", encoding="utf-8")  # Add an unrelated input.
    _git(repository, "add", ".")  # Stage the base files.
    _git(repository, "commit", "-m", "base")  # Record the base revision.
    base = _git(repository, "rev-parse", "HEAD")  # Save the image revision.
    (repository / "documentation.md").write_text("two\n", encoding="utf-8")  # Change only documentation.
    _git(repository, "add", ".")  # Stage the documentation change.
    _git(repository, "commit", "-m", "documentation")  # Record the unrelated revision.
    documentation_head = _git(repository, "rev-parse", "HEAD")  # Save the current revision.
    remote = tmp_path / "origin.git"  # Keep the bare remote beside the checkout.
    _git(tmp_path, "init", "--bare", str(remote))  # Create a remote without network access.
    _git(repository, "remote", "add", "origin", str(remote))  # Connect the temporary checkout.
    _git(repository, "push", "-u", "origin", "main")  # Publish the newer commit.
    return repository, base, documentation_head  # Return both revisions for the test.


def test_revision_check_ignores_commits_outside_image_inputs(tmp_path: Path) -> None:
    """Documentation does not stale the image, but a remote-only commit counts as behind."""
    repository, base, documentation_head = _make_revision_repository(tmp_path)

    changed_inputs = _git(
        repository,
        "diff",
        "--name-only",
        base,
        documentation_head,
        "--",
        *_IMAGE_INPUT_PATHS,
    )

    assert changed_inputs == ""
    _git(repository, "update-ref", "refs/heads/main", base)  # Move the local branch behind the test remote.
    _git(repository, "fetch", "--no-tags", "origin", "+refs/heads/main:refs/remotes/origin/main")  # Refresh main.
    behind_count = _git(repository, "rev-list", "--count", "HEAD..origin/main")  # Count commits missing locally.

    assert behind_count == "1", "the count must include the one remote-only commit"


def test_revision_check_finds_changed_image_inputs(tmp_path: Path) -> None:
    """A later source commit must make the image stale and name the source."""
    repository, base, _ = _make_revision_repository(tmp_path)
    (repository / "src" / "app.py").write_text("two\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "application")
    application_head = _git(repository, "rev-parse", "HEAD")

    changed_inputs = _git(
        repository,
        "diff",
        "--name-only",
        base,
        application_head,
        "--",
        *_IMAGE_INPUT_PATHS,
    )

    assert changed_inputs == "src/app.py"


def test_the_guide_names_the_build_separation(guide_text: str) -> None:
    """The guide MUST state that a plain `up` cannot build the application image."""
    logger.info("Checking the build separation in the guide")  # Report the plan.
    wiki_guide = _GUIDE.parent / "wiki" / "Container-Setup.md"  # Locate the operator wiki beside the source guide.
    logger.info("Reading the wiki guide at %s", wiki_guide)  # Report the read before the work.
    wiki_guide_text = wiki_guide.read_text(encoding="utf-8")  # Load the second operator guide.
    logger.debug("The wiki guide holds %d characters", len(wiki_guide_text))  # Record the read result.

    assert "A plain `up`" in guide_text, "the guide must name the default command"
    assert "cannot build the application image" in guide_text, "the guide must state the safe result"
    assert "Warning: a plain `up` rebuilds." not in guide_text, "the guide must not repeat the old behavior"
    assert "#2272" in guide_text, "the guide must cite the measurement"
    assert r".\scripts\compose.ps1 build" in wiki_guide_text, "the wiki must use the guarded build helper"
    assert "build --allow-stale" in wiki_guide_text, "the wiki must document the explicit stale override"
    assert "misthelper:local" in wiki_guide_text, "the wiki must name the local-only image"
    assert "podman compose -f compose.yml -f compose.build.yml build" not in wiki_guide_text


def test_the_guide_names_the_revision_check(guide_text: str) -> None:
    """The guide MUST show how to read the commit that a container runs."""
    logger.info("Checking the revision check of the guide")  # Report the plan.

    assert "org.opencontainers.image.revision" in guide_text, "the guide must name the label"
    assert "git rev-parse origin/main" in guide_text, "the guide must name the value to compare against"


def test_the_guide_updates_the_checkout_before_the_pull(guide_text: str) -> None:
    """The update recipe MUST pull the code before it pulls the image.

    Why:
        An explicit local build reads the working tree. The recipe updates the
        checkout first, so a later local build does not use old code.
    """
    logger.info("Checking the order of the update recipe")  # Report the plan.
    checkout = guide_text.index("git pull")
    image = guide_text.index("podman pull ghcr.io/jmorrison-juniper/misthelper:latest")
    logger.debug("The checkout step sits at %d and the image step at %d", checkout, image)

    assert checkout < image, "the recipe must update the checkout before it pulls the image"
