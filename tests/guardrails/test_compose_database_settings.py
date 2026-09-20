"""Guard the database settings the compose file must supply.

Issue #3113: `src/db` requires `ARANGO_USERNAME` whenever MistHelper is not
standalone, and `compose.yml` never set it. The router therefore refused to
build inside the container, the exporter caught the error, and every operation
kept the CSV file as its only copy. Both stores were healthy the whole time,
so no reader saw a reason to look.

This test reads the required field names out of the source module instead of
repeating them, so a new required setting fails here until compose supplies it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

import src.db as db_package

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPOSITORY_ROOT / "compose.yml"
ENV_EXAMPLE_PATH = REPOSITORY_ROOT / "deploy" / ".env.example"
APP_SERVICE = "misthelper"


def _required_field_names() -> set[str]:
    """Return every environment name the database config demands when not standalone."""
    source = Path(db_package.__file__).read_text(encoding="utf-8")
    # Each required read looks like `_required_env(ARANGO_USERNAME_FIELD)`.
    constants = set(re.findall(r"_required_env\((\w+)\)", source))
    assert constants, "The database config must read at least one required setting."
    return {getattr(db_package, name) for name in constants}


def _app_environment() -> dict[str, str]:
    """Return the environment mapping the compose file gives the application service."""
    document = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    entries = document["services"][APP_SERVICE]["environment"]
    if isinstance(entries, dict):  # Compose accepts a mapping as well as a list.
        return {str(key): str(value) for key, value in entries.items()}
    pairs = {}
    for entry in entries:
        name, _, value = str(entry).partition("=")
        pairs[name] = value
    return pairs


class TestComposeSuppliesDatabaseSettings:
    """The container must receive every setting the database config requires."""

    def test_required_names_are_discovered(self):
        """The test must read real field names, so an empty set cannot pass silently."""
        names = _required_field_names()
        assert "ARANGO_USERNAME" in names  # This is the setting that issue #3113 lost.
        assert len(names) >= 3  # The config also requires a password for each store.

    @pytest.mark.parametrize("field", sorted(_required_field_names()))
    def test_compose_sets_each_required_setting(self, field):
        """Compose must pass each required setting, or the router refuses to build."""
        environment = _app_environment()
        assert field in environment, f"compose.yml must set {field} for the {APP_SERVICE} service"
        assert environment[field] != "", f"compose.yml must give {field} a value"

    def test_arango_username_defaults_to_the_arangodb_account(self):
        """The default must name the account ArangoDB creates on first boot."""
        assert _app_environment()["ARANGO_USERNAME"] == "${ARANGO_USERNAME:-root}"

    def test_env_example_documents_each_required_setting(self):
        """An operator who copies the example file must find every required name."""
        text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
        missing = [field for field in _required_field_names() if field not in text]
        assert missing == []  # A missing name leaves the operator without the setting.
