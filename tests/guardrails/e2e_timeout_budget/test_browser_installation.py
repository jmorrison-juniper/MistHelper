"""Protect equivalent browser installation without the slow apt route (issue #4613)."""

import copy
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"
MIRRORS = (
    b"http://azure.archive.ubuntu.com/ubuntu/\tpriority:1\n"
    b"https://archive.ubuntu.com/ubuntu/\tpriority:2\n"
    b"https://security.ubuntu.com/ubuntu/\tpriority:3\n"
)


class BrowserInstallation:
    """Execute the shipped setup without administrator access or external requests."""

    @staticmethod
    def workflow() -> dict[str, Any]:
        """Read the real workflow so missing input cannot produce a passing guard."""
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        if not isinstance(workflow, dict):
            raise ValueError("The workflow must contain a job mapping.")
        return workflow

    @staticmethod
    def check(workflow: dict[str, Any]) -> int:
        """Require unconditional setup before the unchanged dependency installer."""
        job = workflow["jobs"]["playwright_shards"]
        steps = job["steps"]
        names = [step.get("name") for step in steps]
        preparation = names.index("Prepare Ubuntu package mirrors")
        installation = names.index("Download the browser")
        assert preparation + 1 == installation, "Mirror preparation must precede browser installation"
        assert steps[installation]["run"] == "python -m playwright install --with-deps chromium"
        BrowserInstallation.check_required_steps([steps[preparation], steps[installation]])
        assert job["timeout-minutes"] == 20
        execution = next(step for step in steps if step.get("name") == "Run E2E smoke tests")
        assert execution["env"]["UPGRADE_PORTAL_E2E_STRICT"] == "1"
        print("browser_installation: checked 2 setup steps and 2 execution requirements")
        return 4

    @staticmethod
    def check_required_steps(steps: list[dict[str, Any]]) -> None:
        """Refuse conditional setup or failure suppression on either required step."""
        for step in steps:
            assert "if" not in step, "Required browser setup cannot be conditional"
            assert not step.get("continue-on-error", False), "Required browser setup must fail on errors"

    @classmethod
    def execute(cls, directory: Path) -> subprocess.CompletedProcess[str]:
        """Execute the workflow shell with only its privileged path and interpreter replaced."""
        steps = cls.workflow()["jobs"]["playwright_shards"]["steps"]
        command = next(step["run"] for step in steps if step.get("name") == "Prepare Ubuntu package mirrors")
        command = command.replace("/etc/apt/apt-mirrors.txt", str(directory / "apt-mirrors.txt"))
        command = command.replace("sudo python3", shlex.quote(sys.executable))
        return subprocess.run(["bash", "-e", "-c", command], capture_output=True, text=True, timeout=10, check=False)


def test_browser_setup_preserves_the_installer_contract() -> None:
    """Require the same browser and package installation with strict missing-browser handling."""
    assert BrowserInstallation.check(BrowserInstallation.workflow()) == 4


def test_setup_removes_only_the_slow_route_and_preserves_a_backup(tmp_path: Path) -> None:
    """Keep unknown mirror entries and signed-package configuration outside the edited file."""
    mirrors = tmp_path / "apt-mirrors.txt"
    original = (
        MIRRORS
        + b"# http://azure.archive.ubuntu.com/ubuntu/\tpriority:1\nhttps://example.invalid/ubuntu/\tpriority:4\n"
    )
    mirrors.write_bytes(original)
    result = BrowserInstallation.execute(tmp_path)
    assert result.returncode == 0, result.stderr
    assert mirrors.read_bytes() == original.split(b"\n", 1)[1]
    assert mirrors.with_suffix(".txt.issue-4613.bak").read_bytes() == original
    assert "Preserved the remaining Ubuntu package mirrors." in result.stdout
    repeated = BrowserInstallation.execute(tmp_path)
    assert repeated.returncode != 0
    assert mirrors.with_suffix(".txt.issue-4613.bak").read_bytes() == original
    assert mirrors.read_bytes() == original.split(b"\n", 1)[1]


@pytest.mark.parametrize(
    "content",
    [None, b"", MIRRORS.split(b"\n", 1)[1], MIRRORS + MIRRORS, MIRRORS.replace(b"https://", b"http://")],
)
def test_an_unknown_mirror_configuration_fails_without_a_write(tmp_path: Path, content: bytes | None) -> None:
    """Refuse absent, empty, changed, duplicated, and insecure runner inputs."""
    mirrors = tmp_path / "apt-mirrors.txt"
    if content is not None:
        mirrors.write_bytes(content)
    result = BrowserInstallation.execute(tmp_path)
    assert result.returncode != 0
    assert result.stderr.strip() != ""
    assert not mirrors.with_suffix(".txt.issue-4613.bak").exists()
    if content is not None:
        assert mirrors.read_bytes() == content
    else:
        assert not mirrors.exists()


def test_a_failed_backup_prevents_the_mirror_rewrite(tmp_path: Path) -> None:
    """An existing recovery record must not be overwritten to make setup continue."""
    mirrors = tmp_path / "apt-mirrors.txt"
    mirrors.write_bytes(MIRRORS)
    backup = mirrors.with_suffix(".txt.issue-4613.bak")
    backup.write_bytes(b"earlier recovery content")
    result = BrowserInstallation.execute(tmp_path)
    assert result.returncode != 0
    assert "FileExistsError" in result.stderr
    assert mirrors.read_bytes() == MIRRORS
    assert backup.read_bytes() == b"earlier recovery content"


@pytest.mark.parametrize("mutation", ["installer", "conditional", "ignored-error", "order", "budget", "strict"])
def test_a_weaker_browser_installation_contract_fails(mutation: str) -> None:
    """Prove that the guard rejects installer, ordering, timeout, and failure-policy changes."""
    workflow = copy.deepcopy(BrowserInstallation.workflow())
    job = workflow["jobs"]["playwright_shards"]
    steps = job["steps"]
    installation = next(step for step in steps if step.get("name") == "Download the browser")
    if mutation == "installer":
        installation["run"] = "python -m playwright install chromium"
    elif mutation in ("conditional", "ignored-error"):
        installation["if" if mutation == "conditional" else "continue-on-error"] = True
    elif mutation == "order":
        steps.reverse()
    elif mutation == "budget":
        job["timeout-minutes"] = 30
    else:
        execution = next(step for step in steps if step.get("name") == "Run E2E smoke tests")
        execution["env"]["UPGRADE_PORTAL_E2E_STRICT"] = "0"
    with pytest.raises(AssertionError):
        BrowserInstallation.check(workflow)
