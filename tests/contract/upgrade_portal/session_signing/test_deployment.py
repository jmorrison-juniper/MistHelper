"""Require discoverable signing settings and the existing Compose forwarding."""

from __future__ import annotations

import logging
import re
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
import yaml
from dotenv import dotenv_values

from src.upgrade_portal.app.config import SECRET_KEY_VARIABLE

logger = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def read_deployment_inputs(root: Path) -> tuple[str, dict[str, Any]]:
    """Read both required inputs and fail when either input is unreadable."""
    logger.info("Read the two required deployment inputs for session signing.")
    checked = 0
    try:
        template = (root / "deploy" / ".env.example").read_text(encoding="utf-8")
        checked += 1
        composition = (root / "compose.yml").read_text(encoding="utf-8")
        checked += 1
    except OSError:
        logger.exception("The deployment contract read %s of two required inputs.", checked)
        print(f"session_signing_deployment: inputs_attempted=2 inputs_read={checked} status=error")
        raise
    print("session_signing_deployment: inputs_attempted=2 inputs_read=2")
    parsed = yaml.safe_load(composition)
    assert isinstance(parsed, dict), "The Compose input must contain a mapping."
    logger.debug("The contract read and parsed two required deployment inputs.")
    return template, parsed


def assert_deployment_contract(template: str, composition: dict[str, Any]) -> int:
    """Reject a missing variable, an active example key, or a Compose override."""
    assert SECRET_KEY_VARIABLE == "CAPTURE_SECRET_KEY"
    entries = re.findall(r"(?m)^#\s*CAPTURE_SECRET_KEY=([^\r\n]*)$", template)
    assert entries == [""], "The template must name one optional blank CAPTURE_SECRET_KEY."
    assert "CAPTURE_SECRET_KEY" not in dotenv_values(stream=StringIO(template)), "The example key must stay inactive."
    service = composition["services"]["misthelper"]
    assert service["env_file"] == [".env"], "The main service must forward .env."
    environment = service.get("environment", {})
    if isinstance(environment, list):
        names = {entry.partition("=")[0] for entry in environment}
    else:
        assert isinstance(environment, dict), "The Compose environment must contain names."
        names = set(environment)
    assert "CAPTURE_SECRET_KEY" not in names, "The Compose environment must not shadow CAPTURE_SECRET_KEY."
    print("session_signing_deployment: decisions_checked=4 status=pass")
    return 4


class TestSessionSigningDeployment:
    """Prove the live deployment contract and its failure decisions."""

    def test_live_deployment_contract(self) -> None:
        """The actual template and Compose service support a private stable key."""
        template, composition = read_deployment_inputs(REPOSITORY_ROOT)
        assert assert_deployment_contract(template, composition) == 4

    @pytest.mark.parametrize("template", ["", "CAPTURE_SECRET_KEY=\n", "# CAPTURE_SECRET_KEY=not-empty\n"])
    def test_missing_or_active_template_setting_fails(self, template: str) -> None:
        """The same decision rejects missing, active, and nonblank example keys."""
        _, composition = read_deployment_inputs(REPOSITORY_ROOT)
        with pytest.raises(AssertionError, match="one optional blank CAPTURE_SECRET_KEY"):
            assert_deployment_contract(template, composition)
        print("session_signing_deployment: negative_decisions_checked=1 status=pass")

    @pytest.mark.parametrize("environment", [["CAPTURE_SECRET_KEY="], {"CAPTURE_SECRET_KEY": ""}])
    def test_empty_compose_override_fails(self, environment: list[str] | dict[str, str]) -> None:
        """Both Compose environment forms must reject an empty key override."""
        _, composition = read_deployment_inputs(REPOSITORY_ROOT)
        composition["services"]["misthelper"]["environment"] = environment
        with pytest.raises(AssertionError, match="must not shadow CAPTURE_SECRET_KEY"):
            assert_deployment_contract("# CAPTURE_SECRET_KEY=\n", composition)
        print("session_signing_deployment: negative_decisions_checked=1 status=pass")

    @pytest.mark.parametrize("missing", ["template", "compose"])
    def test_missing_required_input_fails(self, tmp_path: Path, missing: str) -> None:
        """An absent required input fails instead of reporting an empty success."""
        if missing == "template":
            (tmp_path / "compose.yml").write_text("services: {}\n", encoding="utf-8")
        else:
            (tmp_path / "deploy").mkdir()
            (tmp_path / "deploy" / ".env.example").write_text("# CAPTURE_SECRET_KEY=\n", encoding="utf-8")
        with pytest.raises(FileNotFoundError):
            read_deployment_inputs(tmp_path)
        print("session_signing_deployment: unreadable_inputs_checked=1 status=pass")

    def test_generation_instruction_names_the_supported_key(self) -> None:
        """The template tells the operator how to generate a private key."""
        template, _ = read_deployment_inputs(REPOSITORY_ROOT)
        assert 'python -c "import secrets; print(secrets.token_urlsafe(32))"' in template
