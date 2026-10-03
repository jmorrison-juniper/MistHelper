"""Guard the stable session key required by container deployments."""

from __future__ import annotations

from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPOSITORY_ROOT / "compose.yml"
ENV_EXAMPLE_PATH = REPOSITORY_ROOT / "deploy" / ".env.example"
GUIDE_PATH = REPOSITORY_ROOT / "documentation" / "upgrade_capture_portal.md"


def _application_environment() -> dict[str, str]:
    """Read the application environment from Compose."""
    document = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    entries = document["services"]["misthelper"]["environment"]
    if isinstance(entries, dict):
        return {str(key): str(value) for key, value in entries.items()}
    environment = {}
    for entry in entries:
        name, separator, value = str(entry).partition("=")
        environment[name] = value if separator else ""
    return environment


def test_compose_requires_the_capture_secret_key() -> None:
    """Compose must fail before startup when the session key is absent."""
    environment = _application_environment()
    value = environment["CAPTURE_SECRET_KEY"]

    assert value.startswith("${CAPTURE_SECRET_KEY:?")
    assert "must be set" in value


def test_the_environment_example_documents_secret_key_generation() -> None:
    """The example file must tell operators how to create the key."""
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "CAPTURE_SECRET_KEY=" in text
    assert "secrets.token_urlsafe(32)" in text
    assert "missing value stops" in text


def test_the_portal_guide_documents_container_key_persistence() -> None:
    """The portal guide must state that a missing container key stops startup."""
    text = GUIDE_PATH.read_text(encoding="utf-8")

    assert "required in containers" in text
    assert "A container with no value refuses to start." in text
