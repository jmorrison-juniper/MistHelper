"""Tests for the dependency preflight of the upgrade capture portal (issue #2059).

Why:
    The portal used to serve the sign-in page while the document store answered
    nothing, and the operator met the fault three pages later as a 503. These
    tests pin the probe, the auto-start decision, every reading the page can
    show, and the rule that a probe fault never hides the sign-in form.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from src.upgrade_portal.app.config import ArangoSettings, RedisSettings
from src.upgrade_portal.runtime import dependencies
from src.upgrade_portal.runtime.containers import ContainerState
from src.upgrade_portal.runtime.dependencies import (
    AUTOSTART_VARIABLE,
    DOCUMENT_STORE_KEY,
    LOCK_STORE_KEY,
    Dependency,
    DependencyState,
    autostart_allowed,
    build_registry,
    check_dependency,
    reading_rows,
    run_preflight,
    split_arango_address,
)

ARANGO = ArangoSettings(
    host="http://misthelper-arangodb:9529",
    database="misthelper",
    username="root",
    password_variable="ARANGO_ROOT_PASSWORD",
)
REDIS = RedisSettings(host="misthelper-redis", port=9379, password_variable="REDIS_PASSWORD")

ONE = Dependency(key="one", label="One", container="misthelper-one", host="h", port=1)


class TestSplitArangoAddress:
    """Cover the URL split, which turns one driver URL into two probe values."""

    def test_reads_the_host_and_the_port(self) -> None:
        """A full URL carries both values."""
        assert split_arango_address("http://misthelper-arangodb:9529") == ("misthelper-arangodb", 9529)

    def test_falls_back_to_the_arango_port(self) -> None:
        """A URL with no port means the vendor port, which the registry then probes."""
        assert split_arango_address("http://store.example.com") == ("store.example.com", 8529)

    def test_reads_a_bare_host_name(self) -> None:
        """A value with no scheme must still split, because an operator may set one."""
        assert split_arango_address("store:9529") == ("store", 9529)


class TestAutostartAllowed:
    """Cover the switch that decides whether the portal may change the host."""

    def test_defaults_to_on(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A stopped container is the fault this feature repairs, so the default is on."""
        monkeypatch.delenv(AUTOSTART_VARIABLE, raising=False)
        assert autostart_allowed() is True

    @pytest.mark.parametrize("word", ["0", "false", "no", "off", "OFF", " False "])
    def test_reads_every_false_word(self, monkeypatch: pytest.MonkeyPatch, word: str) -> None:
        """An operator who turns the behavior off must have it stay off."""
        monkeypatch.setenv(AUTOSTART_VARIABLE, word)
        assert autostart_allowed() is False


class TestBuildRegistry:
    """Cover the registry, which must read the same addresses the portal uses."""

    def test_names_both_stores_with_the_prefixed_containers(self) -> None:
        """Each container carries the project prefix, per the compose naming policy."""
        registry = build_registry(ARANGO, REDIS)
        assert [entry.key for entry in registry] == [DOCUMENT_STORE_KEY, LOCK_STORE_KEY]
        assert [entry.container for entry in registry] == ["misthelper-arangodb", "misthelper-redis"]

    def test_reads_the_address_from_the_settings(self) -> None:
        """A probe against a different address from the portal would report a false answer."""
        store, lock = build_registry(ARANGO, REDIS)
        assert (store.host, store.port) == ("misthelper-arangodb", 9529)
        assert (lock.host, lock.port) == ("misthelper-redis", 9379)


class TestCheckDependency:
    """Cover every reading one dependency can produce."""

    def test_reports_up_when_the_service_answers(self) -> None:
        """The fast path opens one socket and starts nothing."""
        with patch.object(dependencies, "service_answers", return_value=True):
            reading = check_dependency(ONE, allow_start=True)
        assert reading.state is DependencyState.UP
        assert reading.healthy is True

    def test_reports_down_without_starting_when_start_is_off(self) -> None:
        """An operator who turned auto-start off must see a report and no host change."""
        with (
            patch.object(dependencies, "service_answers", return_value=False),
            patch.object(dependencies, "find_runtime") as runtime_spy,
        ):
            reading = check_dependency(ONE, allow_start=False)
        assert reading.state is DependencyState.DOWN
        runtime_spy.assert_not_called()

    def test_reports_down_when_the_host_runs_no_runtime(self) -> None:
        """A host with no Podman and no Docker leaves the repair to the operator."""
        with (
            patch.object(dependencies, "service_answers", return_value=False),
            patch.object(dependencies, "find_runtime", return_value=None),
        ):
            reading = check_dependency(ONE, allow_start=True)
        assert reading.state is DependencyState.DOWN
        assert "Start the service" in reading.detail

    def test_names_the_compose_command_when_the_container_is_missing(self) -> None:
        """A missing container is the one case the operator must repair, so name the command."""
        with (
            patch.object(dependencies, "service_answers", return_value=False),
            patch.object(dependencies, "find_runtime", return_value="/podman"),
            patch.object(dependencies, "read_container_state", return_value=ContainerState.MISSING),
            patch.object(dependencies, "start_container") as start_spy,
        ):
            reading = check_dependency(ONE, allow_start=True)
        assert reading.state is DependencyState.DOWN
        assert "podman compose up -d misthelper-one" in reading.detail
        start_spy.assert_not_called()  # WHY: the portal never creates a container.

    def test_reports_a_running_container_that_answers_nothing(self) -> None:
        """A container that runs but answers nothing has a fault inside it."""
        with (
            patch.object(dependencies, "service_answers", return_value=False),
            patch.object(dependencies, "find_runtime", return_value="/podman"),
            patch.object(dependencies, "read_container_state", return_value=ContainerState.RUNNING),
            patch.object(dependencies, "start_container") as start_spy,
        ):
            reading = check_dependency(ONE, allow_start=True)
        assert reading.state is DependencyState.DOWN
        assert "runs but answers no client" in reading.detail
        start_spy.assert_not_called()  # WHY: a running container needs no start.

    def test_starts_a_stopped_container_and_reports_started(self) -> None:
        """The one case the portal repairs: the container exists and is stopped."""
        with (
            patch.object(dependencies, "service_answers", side_effect=[False, True]),
            patch.object(dependencies, "find_runtime", return_value="/podman"),
            patch.object(dependencies, "read_container_state", return_value=ContainerState.STOPPED),
            patch.object(dependencies, "start_container", return_value=True) as start_spy,
        ):
            reading = check_dependency(ONE, allow_start=True)
        assert reading.state is DependencyState.STARTED
        assert reading.healthy is True
        start_spy.assert_called_once_with("misthelper-one", "/podman")

    def test_reports_down_when_the_start_is_refused(self) -> None:
        """A refused start must not read as repaired."""
        with (
            patch.object(dependencies, "service_answers", return_value=False),
            patch.object(dependencies, "find_runtime", return_value="/podman"),
            patch.object(dependencies, "read_container_state", return_value=ContainerState.STOPPED),
            patch.object(dependencies, "start_container", return_value=False),
        ):
            reading = check_dependency(ONE, allow_start=True)
        assert reading.state is DependencyState.DOWN
        assert "refused to start" in reading.detail

    def test_reports_down_when_the_started_container_still_answers_nothing(self) -> None:
        """A container that starts slowly must not read as ready before it listens."""
        with (
            patch.object(dependencies, "service_answers", side_effect=[False, False]),
            patch.object(dependencies, "find_runtime", return_value="/podman"),
            patch.object(dependencies, "read_container_state", return_value=ContainerState.STOPPED),
            patch.object(dependencies, "start_container", return_value=True),
        ):
            reading = check_dependency(ONE, allow_start=True)
        assert reading.state is DependencyState.DOWN
        assert "answers no client yet" in reading.detail


class TestServiceAnswers:
    """Cover the probe itself, which must never raise into the page."""

    def test_returns_true_when_the_socket_opens(self) -> None:
        """An open socket means a service listens."""
        with patch.object(dependencies.socket, "create_connection"):
            assert dependencies.service_answers("h", 1) is True

    def test_returns_false_on_any_socket_error(self) -> None:
        """A refused connection and an unknown name both mean the service is down."""
        with patch.object(dependencies.socket, "create_connection", side_effect=OSError("refused")):
            assert dependencies.service_answers("h", 1) is False

    def test_carries_a_timeout(self) -> None:
        """A host that drops packets must not hold the sign-in page open."""
        with patch.object(dependencies.socket, "create_connection") as connect_spy:
            dependencies.service_answers("h", 1)
        assert connect_spy.call_args.kwargs["timeout"] == dependencies.PROBE_TIMEOUT_SECONDS


class TestRunPreflight:
    """Cover the report that the sign-in page reads."""

    def test_reports_healthy_when_every_service_answers(self) -> None:
        """A healthy portal shows a panel with no warning."""
        with patch.object(dependencies, "service_answers", return_value=True):
            report = run_preflight(ARANGO, REDIS, allow_start=False)
        assert report.healthy is True
        assert report.failures == ()

    def test_lists_every_failure(self) -> None:
        """The operator needs to know which service to repair, not just that one failed."""
        with patch.object(dependencies, "service_answers", return_value=False):
            report = run_preflight(ARANGO, REDIS, allow_start=False)
        assert report.healthy is False
        assert len(report.failures) == 2

    def test_the_caller_flag_wins_over_the_switch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A test and a launcher both need to force the decision."""
        monkeypatch.delenv(AUTOSTART_VARIABLE, raising=False)  # WHY: the switch would otherwise allow a start.
        with (
            patch.object(dependencies, "service_answers", return_value=False),
            patch.object(dependencies, "find_runtime") as runtime_spy,
        ):
            run_preflight(ARANGO, REDIS, allow_start=False)
        runtime_spy.assert_not_called()


class TestReadingRows:
    """Cover the flat form the template renders."""

    def test_builds_one_row_for_each_reading(self) -> None:
        """The page shows one line for each service."""
        with patch.object(dependencies, "service_answers", return_value=True):
            rows = reading_rows(run_preflight(ARANGO, REDIS, allow_start=False))
        assert [row["key"] for row in rows] == [DOCUMENT_STORE_KEY, LOCK_STORE_KEY]
        assert rows[0]["address"] == "misthelper-arangodb:9529"
        assert rows[0]["state"] == "up"

    def test_a_row_carries_no_credential(self) -> None:
        """A row reaches the markup, so it must never hold a password or a variable value."""
        with patch.object(dependencies, "service_answers", return_value=False):
            rows = reading_rows(run_preflight(ARANGO, REDIS, allow_start=False))
        joined = " ".join(value for row in rows for value in row.values())
        assert "password" not in joined.lower()
        assert ARANGO.password_variable not in joined


class TestSigninPanel:
    """Cover the route seam, which must never let a probe fault hide the form."""

    def test_dependency_rows_returns_an_empty_list_on_any_fault(self) -> None:
        """An operator who cannot sign in cannot repair anything, so the form always renders."""
        from src.upgrade_portal.app.routes.auth import dependency_rows

        with patch("src.upgrade_portal.app.routes.auth.load_settings", side_effect=RuntimeError("no settings")):
            assert dependency_rows() == []

    def test_signin_context_marks_an_unhealthy_report(self) -> None:
        """The banner tone comes from this flag, so a down service must set it false."""
        from src.upgrade_portal.app.routes import auth

        rows: list[dict[str, Any]] = [{"key": "k", "label": "L", "address": "a:1", "state": "down", "detail": "d"}]
        with (
            patch.object(auth, "dependency_rows", return_value=rows),
            patch.object(auth, "cloud_catalog", return_value=[("Global 01", "api.mist.com")]),
            patch.object(auth.identity, "environment_token_present", return_value=False),
        ):
            context = auth.signin_context()
        assert context["dependencies_healthy"] is False
        assert context["dependencies"] == rows
