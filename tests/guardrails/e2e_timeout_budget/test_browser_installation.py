"""Protect equivalent browser installation without the slow apt route (issue #4613)."""

import copy
import logging  # Record each shell run, so a failed setup shows its context.
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.unit.prod_readiness.operations.exporting.container.build_support.bash_support import (
    BASH_PATH,  # The bash that opens Windows paths, which the capability probe selected.
    BASH_SKIP_REASON,  # None when this machine has such a bash.
)

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"
MIRRORS = (
    b"http://azure.archive.ubuntu.com/ubuntu/\tpriority:1\n"
    b"https://archive.ubuntu.com/ubuntu/\tpriority:2\n"
    b"https://security.ubuntu.com/ubuntu/\tpriority:3\n"
)
REQUIRES_BASH = pytest.mark.skipif(  # Skip with the cause when no bash can open a Windows path.
    BASH_SKIP_REASON is not None,  # The probe found no usable bash on this machine.
    reason=BASH_SKIP_REASON or "",  # Print the missing capability in the skip record.
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
        steps = cls.workflow()["jobs"]["playwright_shards"]["steps"]  # Read the shipped steps.
        command = next(  # Take the shipped mirror script, so the guard runs the text that CI runs.
            step["run"] for step in steps if step.get("name") == "Prepare Ubuntu package mirrors"
        )
        mirror_file = (directory / "apt-mirrors.txt").as_posix()  # Forward slashes stay valid in bash and Python.
        command = command.replace("/etc/apt/apt-mirrors.txt", mirror_file)  # Point the script at the temp file.
        interpreter = shlex.quote(Path(sys.executable).as_posix())  # Quote the path, which can hold spaces.
        command = command.replace("sudo python3", interpreter)  # Run the test interpreter, not sudo.
        logger.info("Running the Ubuntu mirror setup script in %s", directory)  # Log before the shell starts.
        completed = subprocess.run(  # Run the script with the bash that opens Windows paths.
            [str(BASH_PATH), "-e", "-c", command],  # Keep -e, the flag that GitHub Actions uses.
            capture_output=True,  # Keep both streams, because the cases assert on them.
            text=True,  # Decode the output as text for the assertions.
            timeout=10,  # Stop a stuck shell, so one case cannot block the suite.
            check=False,  # Keep the status, because the failure cases assert on it.
        )
        logger.debug("The mirror setup script exited with status %s", completed.returncode)  # Log the status.
        return completed  # Hand the measured result to the caller.


def test_browser_setup_preserves_the_installer_contract() -> None:
    """Require the same browser and package installation with strict missing-browser handling."""
    assert BrowserInstallation.check(BrowserInstallation.workflow()) == 4


@REQUIRES_BASH
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
    assert "Inspected 5 Ubuntu mirror lines." in result.stdout
    assert mirrors.read_bytes() == original.split(b"\n", 1)[1]
    assert mirrors.with_suffix(".txt.issue-4613.bak").read_bytes() == original
    assert "Preserved the remaining Ubuntu package mirrors." in result.stdout
    repeated = BrowserInstallation.execute(tmp_path)
    assert repeated.returncode == 0, repeated.stderr
    assert "No file was changed." in repeated.stdout
    assert mirrors.with_suffix(".txt.issue-4613.bak").read_bytes() == original
    assert mirrors.read_bytes() == original.split(b"\n", 1)[1]


@REQUIRES_BASH
def test_setup_accepts_layout_variations_and_preserves_other_bytes(tmp_path: Path) -> None:
    """Accept priority changes and missing priority metadata without changing other bytes."""
    mirrors = tmp_path / "apt-mirrors.txt"
    azure = b"  http://azure.archive.ubuntu.com/ubuntu/ \r\n"
    original = (
        b"# runner comment\r\n"
        b"https://security.ubuntu.com/ubuntu/ priority:99\r\n"
        + azure
        + b"https://archive.ubuntu.com/ubuntu/\tpriority:7\r\n"
        + b"https://example.invalid/ubuntu/\tpriority:4\r\n"
    )
    mirrors.write_bytes(original)
    result = BrowserInstallation.execute(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Inspected 5 Ubuntu mirror lines." in result.stdout
    assert mirrors.read_bytes() == original.replace(azure, b"", 1)
    assert mirrors.with_suffix(".txt.issue-4613.bak").read_bytes() == original


@REQUIRES_BASH
def test_missing_azure_mirror_is_a_safe_no_op(tmp_path: Path) -> None:
    """Leave official mirrors unchanged and create no backup when Azure is already absent."""
    mirrors = tmp_path / "apt-mirrors.txt"
    original = (
        b"https://security.ubuntu.com/ubuntu/ priority:99\r\n"
        b"https://archive.ubuntu.com/ubuntu/\tpriority:7\r\n"
        b"https://example.invalid/ubuntu/\tpriority:4\r\n"
    )
    mirrors.write_bytes(original)
    result = BrowserInstallation.execute(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Inspected 3 Ubuntu mirror lines." in result.stdout
    assert "No file was changed." in result.stdout
    assert mirrors.read_bytes() == original
    assert not mirrors.with_suffix(".txt.issue-4613.bak").exists()


@REQUIRES_BASH
@pytest.mark.parametrize(
    "content",
    [
        None,
        b"",
        MIRRORS.replace(b"https://archive.ubuntu.com/ubuntu/", b"https://example.invalid/ubuntu/"),
        MIRRORS.replace(b"https://security.ubuntu.com/ubuntu/", b"https://example.invalid/ubuntu/"),
        MIRRORS + b"https://archive.ubuntu.com/ubuntu/ priority:8\n",
        MIRRORS + b"https://security.ubuntu.com/ubuntu/ priority:8\n",
        MIRRORS + b"http://azure.archive.ubuntu.com/ubuntu/ priority:8\n",
    ],
)
def test_invalid_mirror_configuration_fails_without_a_write(tmp_path: Path, content: bytes | None) -> None:
    """Refuse absent or duplicate official mirrors and duplicate Azure routes."""
    mirrors = tmp_path / "apt-mirrors.txt"
    if content is not None:
        mirrors.write_bytes(content)
    result = BrowserInstallation.execute(tmp_path)
    assert result.returncode != 0
    assert result.stderr.strip() != ""
    assert not mirrors.with_suffix(".txt.issue-4613.bak").exists()
    if content is not None:
        assert f"Inspected {len(content.splitlines())} Ubuntu mirror lines." in result.stdout
        assert mirrors.read_bytes() == content
    else:
        assert not mirrors.exists()


@REQUIRES_BASH
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


def test_wan_performance_evidence_upload_keeps_its_shard_and_path() -> None:
    """Keep the pending browser evidence artifact scoped to its owning shard."""
    steps = BrowserInstallation.workflow()["jobs"]["playwright_shards"]["steps"]
    upload = next(step for step in steps if step.get("name") == "Upload WAN Performance browser evidence")
    assert upload["if"] == "${{ !cancelled() && matrix.shard == 'web-portal' }}"
    assert upload["with"]["path"] == "test-artifacts/wan-performance/*.png"
    assert upload["with"]["if-no-files-found"] == "warn"


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
