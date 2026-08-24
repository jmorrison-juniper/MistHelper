"""Guardrail tests for TLS certificate verification in the shipped container files.

Issue #1906 recorded a critical defect. The image build files set environment
defaults that turned off TLS certificate verification for every outbound HTTPS
call. The sample environment file shipped the same values to every operator.
An attacker on the network path could present a self-signed certificate and
read the Mist API token.

These tests parse the three shipped files and fail if any file sets an insecure
default again. The supported path for a TLS-inspecting corporate proxy is a
mounted root certificate, never a disabled check.
"""

from __future__ import annotations

import logging  # Report each parse step for test troubleshooting.
import shlex  # Split an ENV instruction and honor the quoting rules.
from pathlib import Path  # Build cross-platform paths to the shipped files.

import pytest  # Provide the parametrize decorator for the file matrix.

logger = logging.getLogger(__name__)  # Module logger keeps the parse steps observable.

# Repository root holds the two image build files at the top level.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# Both image build files must stay secure, because each one builds a published image.
_IMAGE_FILES = ("Dockerfile", "Containerfile")

# Path parts of the sample environment file that operators copy to their own .env file.
_ENV_SAMPLE_PARTS = ("documentation", "sample.env")

# Display name of the sample environment file for the test identifiers.
_ENV_SAMPLE_NAME = "documentation/sample.env"

# An empty value in one of these variables removes the trust store for the related client.
_CA_BUNDLE_VARIABLES = (
    "REQUESTS_CA_BUNDLE",  # The requests library reads this bundle path.
    "CURL_CA_BUNDLE",  # The curl client reads this bundle path.
    "SSL_CERT_FILE",  # The OpenSSL default file lookup reads this path.
    "SSL_CERT_DIR",  # The OpenSSL default directory lookup reads this path.
    "NODE_EXTRA_CA_CERTS",  # The Node.js client reads this extra bundle path.
)

# Values that a shell or a dotenv file treats as "on".
_TRUE_VALUES = frozenset({"true", "1", "yes", "on"})

# Values that a shell or a dotenv file treats as "off".
_FALSE_VALUES = frozenset({"false", "0", "no", "off"})

# The Python standard HTTPS client checks certificates when this variable is absent or set to "1".
_SECURE_HTTPS_VERIFY_VALUES = frozenset({"1"})


class ContainerEnvironmentReader:
    """Read the environment defaults that a shipped container file declares."""

    @staticmethod
    def read_image_environment(path: Path) -> dict[str, str]:
        """Return every variable that a Dockerfile or a Containerfile sets with ENV."""
        logger.info("Reading image environment defaults from %s", path)  # Announce the parse step.
        settings: dict[str, str] = {}  # Collect one entry for each declared variable.
        for line in ContainerEnvironmentReader._logical_lines(path):  # Walk the joined lines.
            stripped = line.strip()  # Remove the surrounding whitespace of the line.
            if not stripped.upper().startswith("ENV "):  # Keep the ENV instructions only.
                continue  # Every other instruction sets no default.
            pairs = ContainerEnvironmentReader._parse_env_instruction(stripped[4:])  # Parse the body.
            settings.update(pairs)  # A later ENV instruction overrides an earlier one.
        logger.debug("Parsed %d image environment defaults from %s", len(settings), path)  # Report the count.
        return settings  # Hand the caller the effective image defaults.

    @staticmethod
    def read_dotenv_environment(path: Path) -> dict[str, str]:
        """Return every active assignment of a dotenv sample file."""
        logger.info("Reading dotenv assignments from %s", path)  # Announce the parse step.
        settings: dict[str, str] = {}  # Collect one entry for each active assignment.
        for line in path.read_text(encoding="utf-8").splitlines():  # Walk the physical lines.
            stripped = line.strip()  # Remove the surrounding whitespace of the line.
            if not stripped or stripped.startswith("#") or "=" not in stripped:  # Skip a comment or a blank line.
                continue  # A commented assignment sets no value.
            key, _, value = stripped.partition("=")  # Split the line at the first equals sign.
            settings[key.strip()] = value.strip().strip("\"'")  # Store the value without the quotes.
        logger.debug("Parsed %d dotenv assignments from %s", len(settings), path)  # Report the count.
        return settings  # Hand the caller the active assignments.

    @staticmethod
    def _logical_lines(path: Path) -> list[str]:
        """Return the lines of a build file with the backslash continuations joined."""
        raw = path.read_text(encoding="utf-8")  # Read the whole build file as text.
        joined = raw.replace("\\\n", " ")  # Join a line that continues on the next line.
        return joined.splitlines()  # Split the joined text into logical lines.

    @staticmethod
    def _parse_env_instruction(body: str) -> dict[str, str]:
        """Return the variables that the body of one ENV instruction declares."""
        pairs: dict[str, str] = {}  # Collect the variables of this single instruction.
        tokens = shlex.split(body, posix=True)  # Split on whitespace and drop the quote characters.
        if tokens and "=" not in tokens[0]:  # Detect the legacy "ENV KEY VALUE" form.
            pairs[tokens[0]] = " ".join(tokens[1:])  # The legacy form declares one variable only.
            return pairs  # Stop, because the legacy form holds no further pairs.
        for token in tokens:  # Walk the tokens of the "ENV KEY=VALUE" form.
            key, separator, value = token.partition("=")  # Split the token at the first equals sign.
            if not separator:  # Ignore a token that carries no assignment.
                continue  # A bare token declares no value.
            pairs[key] = value  # Record the declared value of this variable.
        return pairs  # Hand the caller the variables of this instruction.


def _environment_sources() -> list[tuple[str, dict[str, str]]]:
    """Return the parsed environment defaults of every shipped container file."""
    sources: list[tuple[str, dict[str, str]]] = []  # Collect one entry for each shipped file.
    for image_file in _IMAGE_FILES:  # Read both published image build files.
        image_path = _REPO_ROOT / image_file  # Build the absolute path of the image build file.
        sources.append((image_file, ContainerEnvironmentReader.read_image_environment(image_path)))  # Parse it.
    sample_path = _REPO_ROOT.joinpath(*_ENV_SAMPLE_PARTS)  # Build the absolute path of the sample file.
    sources.append((_ENV_SAMPLE_NAME, ContainerEnvironmentReader.read_dotenv_environment(sample_path)))  # Parse it.
    return sources  # Hand the test matrix one entry for each file.


# Parse the shipped files once at collection time, because the files never change during a run.
_ENVIRONMENT_SOURCES = _environment_sources()

# Test identifiers name the file under test, so a failure reports the exact file.
_SOURCE_IDS = [source_name for source_name, _ in _ENVIRONMENT_SOURCES]


class TestContainerTlsVerification:
    """Verify that no shipped container file turns off TLS certificate verification."""

    @pytest.mark.parametrize(("source_name", "settings"), _ENVIRONMENT_SOURCES, ids=_SOURCE_IDS)
    def test_python_https_verification_stays_on(self, source_name: str, settings: dict[str, str]) -> None:
        """PYTHONHTTPSVERIFY must be absent or set to 1 in every shipped file."""
        value = settings.get("PYTHONHTTPSVERIFY")  # Read the declared value, or None when absent.
        assert value is None or value in _SECURE_HTTPS_VERIFY_VALUES, (  # Any other value drops the check.
            f"{source_name} sets PYTHONHTTPSVERIFY={value!r}. "
            "That value turns off certificate verification in the Python HTTPS client. "
            "Mount a corporate root certificate instead of disabling the check. See issue #1906."
        )

    @pytest.mark.parametrize(("source_name", "settings"), _ENVIRONMENT_SOURCES, ids=_SOURCE_IDS)
    def test_ssl_verify_flag_stays_on(self, source_name: str, settings: dict[str, str]) -> None:
        """SSL_VERIFY must be absent or set to a value that keeps verification on."""
        value = settings.get("SSL_VERIFY")  # Read the declared value, or None when absent.
        assert value is None or value.lower() in _TRUE_VALUES, (  # An off value or an empty value fails.
            f"{source_name} sets SSL_VERIFY={value!r}. "
            "That value tells the application to skip certificate verification. "
            "Mount a corporate root certificate instead of disabling the check. See issue #1906."
        )

    @pytest.mark.parametrize(("source_name", "settings"), _ENVIRONMENT_SOURCES, ids=_SOURCE_IDS)
    def test_skip_ssl_verify_flag_stays_off(self, source_name: str, settings: dict[str, str]) -> None:
        """MIST_SKIP_SSL_VERIFY must be absent or set to a value that keeps verification on."""
        value = settings.get("MIST_SKIP_SSL_VERIFY")  # Read the declared value, or None when absent.
        assert value is None or value.lower() in _FALSE_VALUES, (  # An on value disables the check.
            f"{source_name} sets MIST_SKIP_SSL_VERIFY={value!r}. "
            "That value tells the address audit to skip certificate verification. "
            "Mount a corporate root certificate instead of disabling the check. See issue #1906."
        )

    @pytest.mark.parametrize(("source_name", "settings"), _ENVIRONMENT_SOURCES, ids=_SOURCE_IDS)
    def test_ca_bundle_variables_keep_a_value(self, source_name: str, settings: dict[str, str]) -> None:
        """No shipped file may set a CA bundle variable to an empty value."""
        emptied = [name for name in _CA_BUNDLE_VARIABLES if settings.get(name, "unset") == ""]  # Find empty ones.
        assert not emptied, (  # An empty bundle path removes the trust store of that client.
            f"{source_name} sets {', '.join(emptied)} to an empty value. "
            "An empty bundle path removes the trust store and stops certificate verification. "
            "Point the variable at a mounted root certificate instead. See issue #1906."
        )

    def test_every_shipped_container_file_exists(self) -> None:
        """The guardrail must fail if a shipped file moves and the matrix goes stale."""
        for image_file in _IMAGE_FILES:  # Check both published image build files.
            assert (_REPO_ROOT / image_file).is_file(), f"{image_file} is missing from the repository root."
        sample_path = _REPO_ROOT.joinpath(*_ENV_SAMPLE_PARTS)  # Build the path of the sample file.
        assert sample_path.is_file(), f"{_ENV_SAMPLE_NAME} is missing from the repository."
