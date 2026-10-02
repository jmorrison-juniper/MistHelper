"""Test Maps collection with and without the browser package."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_TITLE_MODULE = "tests/e2e/test_map_title_contrast.py"
_COLLECTION_PROBE = """
import importlib.abc
import json
import sys

class MissingBrowser(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "playwright" or fullname.startswith("playwright."):
            raise ModuleNotFoundError("No module named 'playwright'")

if sys.argv[1] == "absent":
    sys.meta_path.insert(0, MissingBrowser())

import pytest

class CollectionEvidence:
    def __init__(self):
        self.nodeids = []
        self.skip_ids = []
        self.error_ids = []
        self.error_messages = []
        self.timeout_loaded = False

    def pytest_configure(self, config):
        self.timeout_loaded = config.pluginmanager.hasplugin("timeout")

    def pytest_collectreport(self, report):
        if report.skipped:
            self.skip_ids.append(report.nodeid)
        if report.failed:
            self.error_ids.append(report.nodeid)
            self.error_messages.append(str(report.longrepr))

    def pytest_collection_finish(self, session):
        self.nodeids = [item.nodeid for item in session.items]

evidence = CollectionEvidence()
status = pytest.main(
    [sys.argv[2], "--collect-only", "-q", "-rs", "-p", "no:cacheprovider", "-p", "timeout"],
    plugins=[evidence],
)
title = sys.modules.get("tests.e2e.test_map_title_contrast")
browser = sys.modules.get("playwright.sync_api")
root_fixture = sys.modules.get("tests.e2e.conftest")
print("MAP_TITLE_CAPABILITY=" + json.dumps({
    "collected": len(evidence.nodeids),
    "skipped": len(evidence.skip_ids),
    "errors": len(evidence.error_ids),
    "skip_ids": evidence.skip_ids,
    "error_ids": evidence.error_ids,
    "title_count": sum(nodeid.startswith("tests/e2e/test_map_title_contrast.py::") for nodeid in evidence.nodeids),
    "image_count": sum(nodeid.startswith("tests/e2e/test_map_viewer_image.py::") for nodeid in evidence.nodeids),
    "strict_reason": any(
        "The Playwright package is not installed, and UPGRADE_PORTAL_E2E_STRICT=1 forbids a skip." in message
        for message in evidence.error_messages
    ),
    "runtime_error_matches": title is not None and browser is not None and title.BrowserError is browser.Error,
    "timeout_loaded": evidence.timeout_loaded,
    "root_fixture": getattr(root_fixture, "__file__", None),
}))
raise SystemExit(status)
"""


class TestMapTitleBrowserCapability:
    """Check collection in four child processes."""

    @pytest.mark.parametrize(
        ("installed", "strict", "expected_exit"),
        [(True, False, 0), (True, True, 0), (False, False, 0), (False, True, 2)],
        ids=("installed-normal", "installed-strict", "absent-normal", "absent-strict"),
    )
    def test_collection_decisions(self, installed: bool, strict: bool, expected_exit: int) -> None:
        """If Playwright is absent, preserve the normal skip and the strict failure."""
        environment = self._environment(strict)
        logger.info("Checking Maps collection with installed=%s and strict=%s", installed, strict)
        process = subprocess.run(
            [sys.executable, "-B", "-c", _COLLECTION_PROBE, "installed" if installed else "absent", "tests/e2e/"],
            cwd=_REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        line = next(line for line in process.stdout.splitlines() if line.startswith("MAP_TITLE_CAPABILITY="))
        report: dict[str, object] = json.loads(line.removeprefix("MAP_TITLE_CAPABILITY="))
        logger.debug("Checked one Maps collection decision with exit %s: %s", process.returncode, report)
        print(
            f"Checked 1 collection decision: installed={installed} strict={strict} collected={report['collected']} "
            f"skipped={report['skipped']} errors={report['errors']} error_ids={report['error_ids']} "
            f"exit={process.returncode}."
        )
        assert process.returncode == expected_exit, process.stdout + process.stderr
        self._check_decision(report, installed, strict)

    @staticmethod
    def _environment(strict: bool) -> dict[str, str]:
        """The child process uses its own policy. It receives no credentials."""
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "HOME", "TMPDIR", "SYSTEMROOT", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT"}
        }
        environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", UPGRADE_PORTAL_E2E_STRICT="1" if strict else "0")
        return environment

    @staticmethod
    def _check_decision(report: dict[str, object], installed: bool, strict: bool) -> None:
        """Reject a missing measurement, a changed fixture, or a hidden failure."""
        skip_ids = report["skip_ids"]
        assert isinstance(skip_ids, list)
        assert report["skipped"] == len(skip_ids)
        if installed:
            assert report["skipped"] == 0
        assert report["title_count"] == (17 if installed else 0)
        assert report["image_count"] == (5 if installed else 0)
        assert (_TITLE_MODULE in skip_ids) is (not installed)
        assert report["error_ids"] == (["tests/e2e/upgrade_portal"] if strict and not installed else [])
        assert report["errors"] == int(strict and not installed)
        assert report["strict_reason"] is (strict and not installed)
        assert report["runtime_error_matches"] is installed
        assert report["timeout_loaded"] is True
        assert report["root_fixture"] == str(_REPOSITORY_ROOT / "tests" / "e2e" / "conftest.py")
