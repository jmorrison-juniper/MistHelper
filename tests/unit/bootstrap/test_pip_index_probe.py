"""Cover the pip index probe of scripts/bootstrap_worktree.py (issue #2000).

The bootstrap inherits the machine-global pip configuration. An unreachable
index mirror makes pip retry 5 times with a 15 second timeout for each package,
so a 60 second bootstrap costs close to 50 minutes and reads as a hang.

These tests cover the decision that avoids that cost:

- ``PipIndexProbe._parse_index_url``: the global line, the install line, a line
  with no separator, an empty value, and a report that names no index.
- ``PipIndexProbe.reaches``: a host that answers, a host that refuses, and a
  URL that carries no host.
- ``PipIndexProbe.fallback_index``: no configured index, the public index, a
  reachable mirror, and an unreachable mirror.
- ``WorktreeBootstrapper._install_environment``: the retry limits, the index
  override, and the promise that the global pip configuration stays unchanged.

Every test stubs the probe result, so no test opens a real socket to a mirror.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.13.

import logging  # WHY: caplog checks the Caution line that the user reads.
import socket  # WHY: the reaches test replaces socket.create_connection.
from pathlib import Path  # WHY: the bootstrapper takes a Path root.
from typing import Any  # WHY: annotate the monkeypatch stub signatures.

import pytest  # WHY: monkeypatch, caplog, and parametrize fixtures.

from scripts.bootstrap_worktree import (  # WHY: direct imports of the code under test.
    PUBLIC_INDEX_URL,
    PipIndexProbe,
    WorktreeBootstrapper,
)

MIRROR_URL = "http://192.168.1.73:3141/root/pypi/+simple/"  # WHY: the URL that issue #2000 measured.


class TestParseIndexUrl:
    """Cover every branch of the pip config report parser."""

    @pytest.mark.parametrize(
        ("report", "expected"),
        [
            ("global.index-url='http://mirror/simple/'", "http://mirror/simple/"),
            ("install.index-url='https://other/simple/'", "https://other/simple/"),
            ('global.index-url="http://quoted/simple/"', "http://quoted/simple/"),
            ("global.index-url=''", None),
            ("global.trusted-host='192.168.1.73'", None),
            ("a line with no separator", None),
            ("", None),
        ],
    )
    def test_parse_index_url(self, report: str, expected: str | None) -> None:
        """The parser returns the index value, or None when the report names none."""
        assert PipIndexProbe._parse_index_url(report) == expected

    def test_the_parser_reads_the_index_among_other_settings(self) -> None:
        """The parser finds the index line inside a full pip config report."""
        report = "\n".join(  # WHY: reproduce the measured report of issue #2000.
            [
                f"global.index-url='{MIRROR_URL}'",
                "global.extra-index-url='https://pypi.org/simple/'",
                "global.trusted-host='192.168.1.73'",
            ]
        )
        assert PipIndexProbe._parse_index_url(report) == MIRROR_URL


class TestReaches:
    """Cover the TCP probe of the index host."""

    def test_a_host_that_answers_reports_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A mirror that accepts the connection stays in use."""

        class FakeConnection:  # WHY: the probe uses the result as a context manager.
            def __enter__(self) -> FakeConnection:
                return self

            def __exit__(self, *args: Any) -> bool:
                return False

        monkeypatch.setattr(socket, "create_connection", lambda *a, **k: FakeConnection())
        assert PipIndexProbe(Path("python")).reaches(MIRROR_URL) is True

    def test_a_host_that_refuses_reports_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A dead mirror reports false, so the caller can choose the public index."""

        def refuse(*args: Any, **kwargs: Any) -> None:
            raise OSError("connection timed out")  # WHY: the measured failure of issue #2000.

        monkeypatch.setattr(socket, "create_connection", refuse)
        assert PipIndexProbe(Path("python")).reaches(MIRROR_URL) is False

    def test_the_probe_uses_the_short_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The probe waits 3 seconds, not the 15 second pip default."""
        recorded: dict[str, Any] = {}

        def record(address: tuple[str, int], timeout: float | None = None) -> None:
            recorded["address"] = address  # WHY: prove the host and the port that the probe used.
            recorded["timeout"] = timeout  # WHY: prove the probe stays cheap.
            raise OSError("refused")

        monkeypatch.setattr(socket, "create_connection", record)
        PipIndexProbe(Path("python")).reaches(MIRROR_URL)
        assert recorded["address"] == ("192.168.1.73", 3141)
        assert recorded["timeout"] == 3.0

    @pytest.mark.parametrize(
        ("url", "expected_port"),
        [("http://mirror/simple/", 80), ("https://mirror/simple/", 443)],
    )
    def test_the_probe_uses_the_scheme_default_port(
        self, monkeypatch: pytest.MonkeyPatch, url: str, expected_port: int
    ) -> None:
        """A URL with no port uses the default port of its scheme."""
        recorded: dict[str, Any] = {}

        def record(address: tuple[str, int], timeout: float | None = None) -> None:
            recorded["address"] = address
            raise OSError("refused")

        monkeypatch.setattr(socket, "create_connection", record)
        PipIndexProbe(Path("python")).reaches(url)
        assert recorded["address"] == ("mirror", expected_port)

    def test_a_url_with_no_host_reports_true(self) -> None:
        """The script never overrides a value that it cannot read."""
        assert PipIndexProbe(Path("python")).reaches("not-a-url") is True


class TestFallbackIndex:
    """Cover the decision that selects the index for one bootstrap run."""

    @staticmethod
    def _probe(monkeypatch: pytest.MonkeyPatch, index_url: str | None, reachable: bool) -> PipIndexProbe:
        """Build a probe with a stubbed configuration read and a stubbed socket."""
        probe = PipIndexProbe(Path("python"))  # WHY: no test starts a real interpreter.
        monkeypatch.setattr(probe, "read_index_url", lambda: index_url)
        monkeypatch.setattr(probe, "reaches", lambda url: reachable)
        return probe

    def test_no_configured_index_needs_no_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The pip default already points at the public index."""
        assert self._probe(monkeypatch, None, True).fallback_index() is None

    @pytest.mark.parametrize(
        "index_url",
        ["https://pypi.org/simple", "https://pypi.org/simple/", "https://files.pythonhosted.org/simple"],
    )
    def test_the_public_index_needs_no_probe(self, monkeypatch: pytest.MonkeyPatch, index_url: str) -> None:
        """A configured public index needs no override and no socket."""
        probe = PipIndexProbe(Path("python"))
        monkeypatch.setattr(probe, "read_index_url", lambda: index_url)

        def fail(url: str) -> bool:
            raise AssertionError("The probe must not open a socket for the public index.")

        monkeypatch.setattr(probe, "reaches", fail)
        assert probe.fallback_index() is None

    def test_a_reachable_mirror_stays_in_use(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A mirror that answers is faster than the public index, so it stays."""
        assert self._probe(monkeypatch, MIRROR_URL, True).fallback_index() is None

    def test_an_unreachable_mirror_selects_the_public_index(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A dead mirror hands the run to the public index."""
        assert self._probe(monkeypatch, MIRROR_URL, False).fallback_index() == PUBLIC_INDEX_URL

    def test_an_unreachable_mirror_prints_a_caution_that_names_the_host(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The user reads a signal word, the host, and the consequence."""
        with caplog.at_level(logging.WARNING, logger="bootstrap_worktree"):
            self._probe(monkeypatch, MIRROR_URL, False).fallback_index()
        message = caplog.text
        assert "Caution:" in message  # WHY: the writing guide demands a signal word.
        assert "192.168.1.73" in message  # WHY: the message must name the unreachable host.
        assert "not changed" in message  # WHY: the message must state that the change is local.


class TestInstallEnvironment:
    """Cover the environment that the pip subprocess reads."""

    def test_the_environment_bounds_the_retries_and_the_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A partly reachable mirror cannot cost 75 seconds for each package."""
        monkeypatch.delenv("PIP_INDEX_URL", raising=False)
        environment = WorktreeBootstrapper(Path("root"))._install_environment()
        assert environment["PIP_RETRIES"] == "1"
        assert environment["PIP_TIMEOUT"] == "15"

    def test_no_override_leaves_the_index_alone(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A reachable mirror keeps its own index setting."""
        monkeypatch.delenv("PIP_INDEX_URL", raising=False)
        bootstrapper = WorktreeBootstrapper(Path("root"))
        assert "PIP_INDEX_URL" not in bootstrapper._install_environment()

    def test_the_override_replaces_the_index_and_drops_the_extra_index(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The override must beat the inherited extra index of the machine."""
        monkeypatch.setenv("PIP_EXTRA_INDEX_URL", "http://192.168.1.73:3141/simple/")
        bootstrapper = WorktreeBootstrapper(Path("root"))
        bootstrapper.index_override = PUBLIC_INDEX_URL
        environment = bootstrapper._install_environment()
        assert environment["PIP_INDEX_URL"] == PUBLIC_INDEX_URL
        assert "PIP_EXTRA_INDEX_URL" not in environment

    def test_the_override_does_not_change_the_process_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The script must not write the global pip configuration of the user."""
        import os  # WHY: read the real process environment for the comparison.

        monkeypatch.delenv("PIP_INDEX_URL", raising=False)
        bootstrapper = WorktreeBootstrapper(Path("root"))
        bootstrapper.index_override = PUBLIC_INDEX_URL
        bootstrapper._install_environment()
        assert "PIP_INDEX_URL" not in os.environ
