"""Unit tests of the smoke command: settings, path rules, exit codes, console lines, evidence, and redaction.

The tests run SmokeCommand with a scripted fake session, or with the real SDK and a patched requests module. No test
sends a request to the network, and each token value is the fake value fake-token-for-tests.
"""

from __future__ import annotations  # Postpone annotation evaluation, as the package does.

import json  # Read the evidence file and write the OpenAPI fixture.
import logging  # Check the state of the SDK logger after the log setup.
from collections.abc import Callable, Iterator  # Type the responder and the cleanup fixture.
from dataclasses import dataclass, field  # Declare the scripted replies.
from pathlib import Path  # Build paths with pathlib, so tests run on Windows, macOS, and Linux.
from types import SimpleNamespace  # Build the request stub that the SDK reads for its headers.
from typing import Any  # Type the scripted replies and the fake session methods.
from urllib.parse import urlsplit  # Read the path of each request that the fake SDK get receives.

import mistapi  # The real SDK class, used by the tests that check the token path.
import pytest  # Parametrize the cases and use the monkeypatch and capsys fixtures.
import requests  # The module that the SDK calls for the token validation, which the tests patch.
import structlog  # Restore the default structlog chain after each command run, which the command replaces.

from scripts.netcool_runbook_smoke.__main__ import (  # Import the command under test, which runs the whole smoke run.
    SmokeCommand,
)
from scripts.netcool_runbook_smoke.client import CallGovernor, PageWalker, ReadOnlyMistClient  # Holders of the session.
from scripts.netcool_runbook_smoke.command import LogSetup  # The log setup and scrub rules under test.
from scripts.netcool_runbook_smoke.documents import EvidenceRedactor  # Holder of the token value.

ORG = "11111111-2222-4333-8444-555555555555"  # Fake organization identifier, never a real one.
SITE = "66666666-7777-4888-8999-aaaaaaaaaaaa"  # Fake site identifier, never a real one.
TOKEN = "fake-token-for-tests"  # nosec B105 - a fake test value, never a credential.
MASKED = (  # Hold the masked token form that the SDK prints for the test token.
    "fake...ests"  # The masked form that the SDK prints for this token: the first four and the last four characters.
)
HOST = "api.mist.com"  # Regional host of the default runs.
PRIVILEGES = [{"scope": "org", "org_id": ORG, "role": "read"}]  # A token that grants the organization read access.


@pytest.fixture(autouse=True)
def release_process_logging() -> (  # Undo the process logging changes after each test, so no test leaks state.
    Iterator[None]
):
    """Undo the logging state that each command run leaves in the process, after each test.

    Why: the command configures structlog and the SDK logger for the whole process.
    It also attaches a stream handler to the stream of the test.
    A later test would then log to a closed stream, or lose the structured events of its own capture.
    Each change is therefore undone after each test.

    Yields:
        None, while the test runs.
    """
    sdk_logger = logging.getLogger("mistapi")  # The SDK logger, which the command silences and detaches.
    sdk_handlers = sdk_logger.handlers[:]  # Handlers before the command, so teardown can restore them.
    sdk_propagate = sdk_logger.propagate  # Propagation before the command, which the command turns off.
    sdk_level = sdk_logger.level  # Level before the command, which the command sets to WARNING.
    yield  # The test runs with the configuration of the command.
    structlog.reset_defaults()  # Restore the default structlog chain, which the command replaces.
    root = logging.getLogger()  # The root logger holds the handler that the command added.
    root.handlers = [item for item in root.handlers if item.get_name() != "netcool-runbook-smoke"]  # Remove it.
    sdk_logger.handlers = sdk_handlers  # Restore the SDK handlers, which the command replaces with a null handler.
    sdk_logger.propagate = sdk_propagate  # Restore propagation, which the command turns off.
    sdk_logger.setLevel(sdk_level)  # Restore the SDK level, which the command sets to WARNING.


@dataclass
class Reply:  # Stand in for the SDK response with the members that the client reads.
    """Scripted response with the attributes that the client reads.

    Why: the fake session returns the attributes of the SDK response, so each reply is classified alike.
    """

    status_code: int | None  # HTTP status of the reply, or None for a connection failure.
    data: Any  # Parsed body of the reply.
    raw_data: str = ""  # Body text of the reply, which the client reads to find an empty body.
    headers: dict[str, str] = field(default_factory=dict)  # Response headers.
    next: Any = None  # The next link the client follows, or None at the end.


def reply(  # Build a scripted reply whose text is the JSON of its data.
    status: int = 200, data: Any = None, next_value: Any = None
) -> Reply:
    """Return a scripted response whose text is the JSON of its data.

    Args:
        status: HTTP status of the response.
        data: Parsed body of the response.
        next_value: Next link of a paged response.

    Returns:
        The scripted response.
    """
    body = {} if data is None else data  # A missing body is an empty object.
    return Reply(  # Return the reply with the same data in its parsed and text forms.
        status_code=status, data=body, raw_data=json.dumps(body), next=next_value
    )


def default_body(path: str) -> Any:  # Return a healthy body for each path, so a default run only passes or warns.
    """Return the body of a healthy organization for one path, so a default run passes or warns only.

    Args:
        path: Request path without the query.

    Returns:
        The parsed body for the path.
    """
    if path.endswith("/self/usage"):  # The hourly budget with the documented limit.
        return {  # Return a usage body with the documented limit and enough budget.
            "requests": 10,
            "request_limit": 5000,
            "seconds": 100,
        }
    if path.endswith("/self"):  # The token owner with a read grant on the organization.
        return {"privileges": PRIVILEGES}  # Return a self body with the read grant on the organization.
    if "/const/" in path:  # Each catalog holds one key that the runbook would name.
        name = path.rsplit("/", 1)[-1]  # The catalog key is the last path segment.
        return [  # Return one catalog item with a key, a display name, and an example.
            {"key": f"{name}-key", "display": name, "example": {"x": 1}}
        ]
    if path.endswith("/count"):  # Counts agree with the empty searches.
        return {"results": [{"count": 0}], "total": 0}  # Return a zero count, which agrees with the empty searches.
    if path.endswith("/sites"):  # One site, so SMK-08 reads it.
        return [{"id": SITE}]  # Return one site, so SMK-08 reads it.
    if path.endswith(("/mxedges", "/stats/devices", "/webhooks")):  # Empty arrays give INFO or WARN, never FAIL.
        return []  # Return an empty array for the list endpoints.
    if path.endswith("/search"):  # Empty searches with a total of zero.
        return {  # Return an empty search page with a total of zero.
            "results": [],
            "total": 0,
            "start": 1000,
            "end": 2000,
        }
    return {}  # Return an empty object for any other path.


class ResponderSession:  # Replace the SDK session with a responder that picks the reply by path.
    """Fake SDK session whose replies come from a responder, with one request list.

    Why: each command test chooses the replies of the paths it cares about, and the default replies cover the rest.
    """

    def __init__(  # Store the responder and an empty list of requested paths.
        self, responder: Callable[[str], Reply]
    ) -> None:
        """Keep the responder and an empty request list.

        Args:
            responder: Function that returns the reply for one request path.
        """
        self.responder: Callable[[str], Reply] = responder  # Chooses the reply of each path.
        self.uris: list[str] = []  # Each path that the session received, in order.

    def mist_get(  # Record the path and return the reply that the responder picks.
        self, uri: str, query: dict[str, str]
    ) -> Reply:
        """Record the path and return its scripted reply.

        Args:
            uri: Path of the request.
            query: Query of the request, which the tests do not check here.

        Returns:
            The scripted reply.
        """
        self.uris.append(uri)  # Count the request.
        return self.responder(uri)  # The reply of this path.


def healthy(  # Build a responder that answers healthy bodies, except the overridden suffixes.
    overrides: dict[str, Any] | None = None,
) -> Callable[[str], Reply]:
    """Return a responder that answers healthy bodies, with the overrides for the suffixes that a test names.

    Args:
        overrides: Body per path suffix. A body of the value Reply is returned as it is.

    Returns:
        The responder function.
    """
    table = overrides or {}  # The suffixes that this test changes.

    def respond(path: str) -> Reply:  # Return the override for the path, or the healthy reply when none matches.
        """Return the override for the first matching suffix, or the healthy reply."""
        for suffix, value in table.items():  # Overrides come first.
            if path.endswith(suffix):  # The override names this path.
                return value if isinstance(value, Reply) else reply(data=value)  # A reply or a body.
        return reply(data=default_body(path))  # The healthy body of the organization.

    return respond  # Return the responder function to the caller.


def make_root(  # Build a fake repository root with the default OpenAPI file and the output folder.
    tmp_path: Path,
) -> Path:
    """Create a repository-like root with the default OpenAPI file and the output folder.

    Args:
        tmp_path: Test folder.

    Returns:
        The root folder of the test run.
    """
    root = tmp_path / "repo"  # The fake repository root.
    (root / "documentation").mkdir(parents=True)  # The default OpenAPI file lives here.
    document = {  # Build an OpenAPI document with the self path and two regional servers.
        "openapi": "3.1.0",
        "paths": {"/api/v1/self": {"get": {"operationId": "getSelf"}}},
        "servers": [{"url": f"https://{HOST}"}, {"url": "https://api.gc1.mist.com"}],
    }
    (root / "documentation" / "mist-api-openapi31json.json").write_text(  # Write the default OpenAPI file for the run.
        json.dumps(document), encoding="utf-8"
    )
    (root / "test-artifacts").mkdir()  # The only folder that the evidence may use.
    return root  # Return the root folder of the fake repository.


def run(  # Run the command with a fake session and return its exit code.
    root: Path, argv: list[str], session: ResponderSession | None, environment: dict[str, str] | None = None
) -> int:
    """Run the command with a fake session, and return the exit code.

    Args:
        root: Repository root of the test.
        argv: Command line arguments.
        session: Fake session whose requests the run uses, or None when no session may be built.
        environment: Process environment of the run, or None for the default token and organization.

    Returns:
        The exit code of the run.
    """
    env = {"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG} if environment is None else environment  # Default source.

    def factory(**kwargs: Any) -> ResponderSession:  # Return the fake session in place of a real SDK session.
        """Return the fake session, and never a real SDK session."""
        if session is None:  # A run that must not build a session fails the test.
            raise AssertionError(  # Fail the test when a refused run tries to build a session.
                "the session must not be built"
            )
        return session  # Return the fake session, so the command never reaches the SDK.

    command = SmokeCommand(root=root, environment=env, session_factory=factory)  # The command under test.
    return command.run(argv)  # Run the command with the given arguments and return its exit code.


def evidence_file(root: Path) -> dict[str, Any]:  # Read the only evidence file of the run, as parsed JSON.
    """Return the only evidence file of the run, as parsed JSON.

    Args:
        root: Repository root of the test.

    Returns:
        The evidence record.
    """
    files = sorted((root / "test-artifacts" / "netcool-runbook-smoke").glob("*.json"))  # Default evidence names.
    assert len(files) == 1  # Exactly one record was written.
    record: dict[str, Any] = json.loads(files[0].read_text(encoding="utf-8"))  # The parsed record.
    return record  # Return the parsed evidence record to the test.


def lines(text: str) -> list[str]:  # Split the console text into its non-empty lines.
    """Split the console text into lines, without the trailing empty line.

    Args:
        text: Console text.

    Returns:
        The lines of the text.
    """
    return [line for line in text.splitlines() if line]  # Empty lines are not part of the output.


# Settings, path rules, and the env file: each refusal stops the run before any request.


def test_a_clean_run_prints_one_line_per_check_then_summary_outcome_and_evidence(  # Confirm the healthy console output.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A healthy run prints ten check lines, the summary, the outcome, and the evidence path, and exits 0."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.
    code = run(root, [], session)  # Run the command with no options and keep its exit code.
    out = capsys.readouterr().out.splitlines()  # Read the console lines that the run printed.
    assert code == 0  # Warnings and information do not fail the run.
    assert [line[:6] for line in out[:10]] == [f"SMK-{n:02d}" for n in range(1, 11)]  # Ten checks in order.
    assert out[10].startswith("Checks examined: 8. Passed: 3. Warnings: 4. Info: 1. Failed: 0. Skipped: 2.")  # Summary.
    assert out[11] == "Outcome: Pass (exit code 0)."  # Outcome line.
    assert out[12].startswith("Evidence: test-artifacts/netcool-runbook-smoke/") and out[  # Confirm the evidence path.
        12
    ].endswith(
        ".json"
    )  # Evidence.
    record = evidence_file(root)  # Read the evidence record that the run wrote.
    assert len(record) == 14 and record["exit_code"] == 0 and record["outcome_class"] == "Pass"  # Fourteen keys.


def test_the_console_and_the_logs_hold_ascii_text_only(  # Confirm that the console and the logs print ASCII text only.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Standard output and standard error hold ASCII characters only."""
    run(make_root(tmp_path), [], ResponderSession(healthy()))  # Run a healthy command, so its output can be checked.
    captured = capsys.readouterr()  # Capture the standard output and the standard error of the run.
    assert captured.out.isascii() and captured.err.isascii()  # Both streams are ASCII.


def test_the_evidence_catalogs_keep_each_item_without_its_example(  # Confirm each catalog item keeps no example.
    tmp_path: Path,
) -> None:
    """The evidence keeps the catalog items, and no item keeps its example member."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    run(root, [], ResponderSession(healthy()))  # Run a healthy command that writes the evidence record.
    items = evidence_file(root)["catalogs"]["alarm_defs"][  # Read the alarm catalog items from the evidence record.
        "items"
    ]
    assert items and all("example" not in item and "key" in item for item in items)  # Keys stay, examples go.


def test_the_evidence_keeps_the_q8_observation(  # Confirm that the evidence keeps observation q8.
    tmp_path: Path,
) -> None:
    """The evidence record keeps observation q8, which the contract lists as a key."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    run(root, [], ResponderSession(healthy()))  # Run a healthy command that writes the evidence record.
    assert "q8_alarm_status_values" in evidence_file(root)["observations"]  # The allowlist keeps the q8 key.


def test_a_run_without_a_token_sends_zero_requests_and_exits_2(  # Confirm that a missing token sends no request.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing token stops the run before the session exists, so the SDK authentication case sends no request."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    code = run(root, [], None, environment={"MIST_ORG_ID": ORG})  # No token variable at all.
    out = capsys.readouterr().out  # Read the console text of the run that stops before SMK-01.
    assert code == 2  # Configuration error.
    assert (  # Confirm that the summary shows zero checks and zero requests.
        "Checks examined: 0. Passed: 0. Warnings: 0. Info: 0. Failed: 0. Skipped: 0. Requests sent: 0 of 60." in out
    )
    assert "Outcome: Configuration error (exit code 2)." in out  # The outcome line of a run before SMK-01.
    assert evidence_file(root)["checks"] == []  # The record holds no check before SMK-01.


@pytest.mark.parametrize(
    ("environment", "message"),
    [
        ({"MIST_API_TOKEN": TOKEN, "MIST_APITOKEN": "other-fake-token", "MIST_ORG_ID": ORG}, "different values"),
        ({"MIST_API_TOKEN": "fake-one,fake-two", "MIST_ORG_ID": ORG}, "holds a comma"),
        ({"MIST_API_TOKEN": TOKEN}, "not a UUID"),
        ({"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": "not-a-uuid"}, "not a UUID"),
        ({"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG, "MIST_HOST": "https://api.mist.com/x"}, "bare host name"),
    ],
)
def test_bad_token_or_identifier_values_exit_2_before_any_request(  # Confirm that a bad token or identifier exits 2.
    tmp_path: Path, capsys: pytest.CaptureFixture[str], environment: dict[str, str], message: str
) -> None:
    """Conflicting or comma tokens, and missing or bad identifiers, exit 2 with zero requests."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    code = run(  # Run the command with the bad environment, which must refuse to build a session.
        root, [], None, environment=environment
    )
    captured = capsys.readouterr()  # Capture the output of the refused run.
    assert code == 2  # Configuration error.
    assert message in captured.err  # The cause is logged.
    assert (  # Confirm that the output holds no token value.
        TOKEN not in captured.out + captured.err and "other-fake-token" not in captured.out + captured.err
    )  # No token.


def test_the_org_identifier_option_wins_over_the_environment(  # Confirm that --org-id wins over the environment.
    tmp_path: Path,
) -> None:
    """--org-id is the first source of the organization, so it wins over MIST_ORG_ID."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    other = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"  # A different valid identifier from the environment.
    grant = [{"scope": "org", "org_id": other, "role": "read"}]  # The token grants the argument organization.
    session = ResponderSession(  # Script a self reply that grants the organization named by the option.
        healthy({"/self": {"privileges": grant}})
    )
    code = run(  # Run with the option in upper case and a different organization in the environment.
        root, ["--org-id", other.upper()], session, environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG}
    )
    assert code == 0 and any(uri.endswith(f"/orgs/{other}/sites") for uri in session.uris)  # The argument org is used.


def test_the_process_environment_wins_over_the_env_file(  # Confirm that the process environment wins over the env file.
    tmp_path: Path,
) -> None:
    """A name in the process environment wins over the same name in the env file, as the source order says."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    env_file = tmp_path / "outside.env"  # Outside the repository, so the rule allows it.
    env_file.write_text(  # Write an env file with a different token, which the process must override.
        f"MIST_API_TOKEN=file-token-value\nMIST_ORG_ID={ORG}\n", encoding="utf-8"
    )
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.
    code = run(  # Run with the env file and a process token, so the process token must win.
        root, ["--env-file", str(env_file)], session, environment={"MIST_API_TOKEN": TOKEN}
    )
    assert code == 0  # The process token is used, so no conflict exists.
    assert session.uris and all(uri.startswith("/api/v1/") or "/orgs/" in uri for uri in session.uris)  # Requests ran.


def test_an_env_file_value_is_used_when_the_process_has_none(  # Confirm that the env file supplies missing values.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The env file supplies the token and the organization when the process environment has neither."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    env_file = tmp_path / "outside.env"  # Outside the repository.
    env_file.write_text(  # Write an env file with the token and the organization.
        f"MIST_API_TOKEN={TOKEN}\nMIST_ORG_ID={ORG}\n", encoding="utf-8"
    )
    code = run(  # Run with an empty process environment, so the env file must supply both values.
        root, ["--env-file", str(env_file)], ResponderSession(healthy()), environment={}
    )
    out = capsys.readouterr().out  # Read the console text of the run.
    assert code == 0 and str(env_file) not in out  # The run works, and the env file path is never printed.
    assert evidence_file(root)["settings"]["env_file_given"] is True  # Only the flag is recorded.


@pytest.mark.parametrize(
    "argv",
    [
        ["--output", "../escaped.json"],  # Output outside test-artifacts.
        ["--output", "test-artifacts/../../escaped.json"],  # A traversal that lands outside the folder.
        ["--runbook", "../escaped.md"],  # Runbook outside the repository.
        ["--openapi", "../escaped.json"],  # OpenAPI outside the repository.
        ["--output", "documentation/inside.json"],  # Output inside the repository but outside test-artifacts.
    ],
)
def test_a_path_that_leaves_its_folder_exits_2_and_writes_nothing(  # Confirm that the path refusal writes nothing.
    tmp_path: Path, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    """A path that resolves outside its folder exits 2, sends no request, and writes no file."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.
    code = run(root, argv, session)  # Run with the path that must be refused.
    out = capsys.readouterr().out  # Read the console text of the refused run.
    assert code == 2 and session.uris == []  # Refused before the first request.
    if argv[0] == "--output":  # A refused output path has no evidence file, so the line says so.
        assert "Evidence: not written" in out  # Confirm that the output says the evidence was not written.
    else:  # The default output is valid, so the record is still written.
        assert (  # Confirm that the default evidence path is still printed.
            "Evidence: test-artifacts/netcool-runbook-smoke/" in out
        )
    assert (  # Confirm that no file was written outside the folder.
        not (tmp_path / "escaped.json").exists() and not (root / "documentation" / "inside.json").exists()
    )


def test_an_env_file_inside_the_repository_that_is_not_the_root_dot_env_exits_2(  # Only the root .env is allowed.
    tmp_path: Path,
) -> None:
    """An env file inside the repository is refused unless it is exactly the root .env file."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    inside = root / "scripts-config.env"  # Inside the repository, and not .env.
    inside.write_text(  # Write an env file inside the repository, which the rule must refuse.
        f"MIST_API_TOKEN={TOKEN}\nMIST_ORG_ID={ORG}\n", encoding="utf-8"
    )
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.
    assert run(root, ["--env-file", str(inside)], session, environment={}) == 2 and session.uris == []  # Refused.


def test_a_missing_env_file_exits_2(tmp_path: Path) -> None:  # Confirm that a missing env file exits 2.
    """A missing --env-file path exits 2 before any value is read."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    session = ResponderSession(healthy())  # Build a session that must not receive any request.
    assert run(root, ["--env-file", str(tmp_path / "missing.env")], session, environment={}) == 2  # Refused.


def test_the_root_dot_env_is_accepted_as_the_env_file(  # Confirm that the root .env file is accepted as the env file.
    tmp_path: Path,
) -> None:
    """The root .env file is the one file inside the repository that the rule accepts."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    (root / ".env").write_text(  # Write the root .env file with the token and the organization.
        f"MIST_API_TOKEN={TOKEN}\nMIST_ORG_ID={ORG}\n", encoding="utf-8"
    )
    assert run(root, ["--env-file", str(root / ".env")], ResponderSession(healthy()), environment={}) == 0  # Accepted.


def test_an_explicit_missing_runbook_exits_2_and_a_default_missing_runbook_skips(  # Confirm both missing-runbook cases.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An explicit --runbook that is missing exits 2, while the default runbook that is missing skips SMK-02."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    assert run(root, ["--runbook", "documentation/missing.md"], ResponderSession(healthy())) == 2  # Explicit: refused.
    capsys.readouterr()  # Drop the first run's lines.
    code = run(root, [], ResponderSession(healthy()))  # Default: the run continues.
    out = capsys.readouterr().out  # Read the console text of the default run.
    assert code == 0 and "SMK-02 SKIP Runbook structure: runbook not found" in out  # The run goes on.


def test_an_unreadable_openapi_file_exits_2(tmp_path: Path) -> None:  # Confirm that an unreadable OpenAPI file exits 2.
    """A default OpenAPI file that is not JSON exits 2 before any request."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    (root / "documentation" / "mist-api-openapi31json.json").write_text(  # Replace the OpenAPI file with bad JSON.
        "{bad", encoding="utf-8"
    )
    session = ResponderSession(healthy())  # Build a session that must not receive any request.
    assert run(root, [], session) == 2 and session.uris == []  # Refused before the session.


def test_a_host_outside_the_servers_list_exits_2(  # Confirm that a host outside the servers list exits 2 at SMK-01.
    tmp_path: Path,
) -> None:
    """A regional host that the OpenAPI file does not list exits 2 at SMK-01."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.
    assert (  # Confirm that the run exits 2 for the host outside the servers list.
        run(
            root, [], session, environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG, "MIST_HOST": "api.eu.mist.com"}
        )
        == 2
    )


@pytest.mark.parametrize(
    "argv",
    [
        ["--max-retries", "3"],
        ["--window-minutes", "0"],
        ["--delay-minutes", "60"],
        ["--max-pages", "0"],
        ["--call-timeout", "x"],
    ],
)
def test_an_out_of_range_option_exits_2_with_the_summary_lines(  # Confirm that an out-of-range option exits 2.
    tmp_path: Path, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    """An option outside its range exits 2 before any request, and the run still prints both summary lines."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.
    code = run(root, argv, session)  # Run with the out-of-range option.
    out = capsys.readouterr().out  # Read the console text of the refused run.
    assert code == 2 and session.uris == []  # Refused before the first request.
    assert "Checks examined: 0." in out and "Outcome: Configuration error (exit code 2)." in out  # Both lines.


# Exit codes 0 to 6, each from its own rule.


def test_check_failure_exits_1_when_a_catalog_is_empty(  # Confirm that a failed check exits 1 and the run goes on.
    tmp_path: Path,
) -> None:
    """A FAIL result exits 1, and the later checks still run because a check failure is not a run stop."""
    session = ResponderSession(healthy({"/const/alarm_defs": []}))  # Script an empty alarm catalog, which fails SMK-05.
    assert run(make_root(tmp_path), [], session) == 1  # Confirm that the run exits 1 for the failed check.
    assert f"/api/v1/orgs/{ORG}/sites" in session.uris  # SMK-08 still ran after the failed catalog.


def test_rate_limit_stop_exits_3_and_skips_the_later_checks(  # Confirm that a rate-limit stop exits 3.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Low hourly usage stops the run with exit code 3, and each later check prints its cause as SKIP."""
    session = ResponderSession(  # Script the usage reply with 50 requests left, which stops the run.
        healthy({"/self/usage": {"requests": 4950, "request_limit": 5000, "seconds": 5}})
    )
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    assert run(root, [], session) == 3  # Confirm that the run exits 3 on the low budget.
    out = capsys.readouterr().out  # Read the console text of the stopped run.
    assert "SMK-05 SKIP Definition catalogs: not run: rate-limit stop" in out  # The cause of the skip.
    assert "SMK-04 FAIL Hourly request budget" in out  # The stopping check keeps its own FAIL result.
    assert "Outcome: Rate-limit stop (exit code 3)." in out and "Checks examined: 3." in out  # Three checks ran.


def test_budget_stop_exits_4_when_the_budget_is_spent(tmp_path: Path) -> None:  # Confirm that a spent budget exits 4.
    """A request after the last unit of the budget exits 4 before the request is sent."""
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.
    code = run(  # Run with a budget of three requests, which runs out during the catalogs.
        make_root(tmp_path), ["--max-requests", "3"], session
    )
    assert code == 4  # The budget ran out during the catalogs.
    assert len(session.uris) == 2  # Only the token validation and SMK-03 used the budget, plus SMK-04.


def test_unsafe_paging_stop_exits_5_on_a_foreign_next_link(  # Confirm that a foreign next link exits 5.
    tmp_path: Path,
) -> None:
    """A next link to another host exits 5, and no request uses that link."""
    foreign = reply(  # Script an alarm page whose next link leaves the approved origin.
        data={"results": [{"id": "a"}], "total": 2}, next_value="https://evil.example/api/v1/x"
    )
    session = ResponderSession(healthy({"/alarms/search": foreign}))  # Route the alarm search to the foreign page.
    assert run(make_root(tmp_path), [], session) == 5  # Confirm that the run exits 5 on the foreign link.
    assert not any("evil.example" in uri for uri in session.uris)  # The foreign link was never requested.


def test_an_unexpected_fault_exits_6_and_logs_a_traceback(  # Confirm that an unexpected fault exits 6.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An unexpected exception exits 6, logs a traceback, and prints the cause as a class name."""

    def broken_factory(**kwargs: Any) -> ResponderSession:  # Build a session factory that raises an unexpected error.
        """Raise an error that is not an SDK authentication error."""
        raise RuntimeError("fault in the factory")  # Raise an error that is not an SDK authentication error.

    command = SmokeCommand(  # Build the command with the broken session factory.
        root=make_root(tmp_path),
        environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG},
        session_factory=broken_factory,
    )
    code = command.run([])  # Run the command, which must hit the unexpected fault.
    captured = capsys.readouterr()  # Capture the output of the faulted run.
    assert code == 6  # Internal error.
    assert "Traceback" in captured.err  # The full traceback is logged.
    assert (  # Confirm that the outcome and the cause name the internal error.
        "Outcome: Internal error (exit code 6)." in captured.out and "Cause: unexpected RuntimeError" in captured.out
    )


def test_an_evidence_write_failure_alone_exits_2(  # Confirm that an evidence write failure alone exits 2.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A run that passes but cannot write its evidence exits 2, and the evidence line says so."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    (root / "test-artifacts" / "blocked.json").mkdir()  # A folder where the file must go.
    code = run(  # Run with an output path that is a folder, so the write fails.
        root, ["--output", "test-artifacts/blocked.json"], ResponderSession(healthy())
    )
    out = capsys.readouterr().out  # Read the console text of the run.
    assert code == 2 and "Evidence: not written" in out  # The write failure is the outcome.
    assert (  # Confirm that the failed write sets the outcome to exit code 2.
        "Outcome: Configuration error (exit code 2)." in out
    )


def test_an_internal_error_with_a_failed_evidence_write_keeps_exit_code_6(  # Confirm exit code 6 is kept.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An internal error keeps exit code 6 when the evidence write also fails, and both causes are printed."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    (  # Create a folder where the evidence file must go, so the write fails.
        root / "test-artifacts" / "blocked.json"
    ).mkdir()

    def broken_factory(**kwargs: Any) -> ResponderSession:  # Build a session factory that raises an unexpected error.
        """Raise an error that is not an SDK authentication error."""
        raise RuntimeError("fault in the factory")  # Raise an error that is not an SDK authentication error.

    command = SmokeCommand(  # Build the command with the broken factory and the blocked output.
        root=root, environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG}, session_factory=broken_factory
    )
    code = command.run(  # Run the command, which hits the fault and then the write failure.
        ["--output", "test-artifacts/blocked.json"]
    )
    out = capsys.readouterr().out  # Read the console text of the faulted run.
    assert code == 6 and "Outcome: Internal error (exit code 6)." in out  # The internal error keeps its code.
    assert (  # Confirm that both causes of the failed run are printed.
        "Cause: the evidence file cannot be written (OSError)" in out
        or "Cause: the evidence file cannot be written" in out
    )


def test_the_check_items_are_skipped_with_the_cause_of_a_run_stop(  # Confirm each check after a stop is SKIP.
    tmp_path: Path,
) -> None:
    """Every check after a run stop is in the evidence as SKIP, so the record holds ten check items."""
    session = ResponderSession(  # Script the usage reply with 50 requests left, which stops the run.
        healthy({"/self/usage": {"requests": 4950, "request_limit": 5000, "seconds": 5}})
    )
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    run(root, [], session)  # Run the command that stops at SMK-04.
    checks = evidence_file(root)["checks"]  # Read the check items from the evidence record.
    assert [item["check_id"] for item in checks] == [f"SMK-{n:02d}" for n in range(1, 11)]  # Ten items, in order.
    assert {item["status"] for item in checks[4:]} == {"SKIP"}  # SMK-05 onward did not run.


# Redaction and logs: the token and identifiers never reach an output.


def test_the_token_never_appears_in_stdout_stderr_or_the_evidence(  # Confirm that the token reaches no output.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A healthy run prints and writes no token, no masked token, and no organization identifier."""
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    run(root, [], ResponderSession(healthy()))  # Run a healthy command, so every output is checked.
    captured = capsys.readouterr()  # Capture the output of the healthy run.
    text = (  # Join the console output and the evidence file text for the search.
        captured.out
        + captured.err
        + (root / "test-artifacts" / "netcool-runbook-smoke")
        .joinpath(next((root / "test-artifacts" / "netcool-runbook-smoke").glob("*.json")).name)
        .read_text(encoding="utf-8")
    )
    for secret in (TOKEN, MASKED, ORG):  # Check each secret value against all of the output text.
        assert secret not in text  # No secret or identifier in any output.
    assert "org-1" in text  # The label that replaces the identifier.


class RejectedReply:  # Stand in for a rejected token validation reply.
    """Fake token-validation response with HTTP 401, which the SDK reads as a rejected token.

    Why: the real SDK checks the status of the validation reply, so the fake reply needs only the status and the body.
    """

    status_code = 401  # HTTP status that the SDK maps to a rejected token.

    def json(self) -> dict[str, str]:  # The SDK reads this body when it reports a rejected token.
        """Return the error body of the rejected token."""
        return {"detail": "invalid token"}  # Return the detail text of a rejected token.


def reject_token_validation(  # Reject each token validation request with HTTP 401, without a network call.
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    """Patch the SDK validation request so that each token is rejected with HTTP 401.

    Why: the real SDK validates the token with requests.get, so the patch keeps the SDK code path under test
    and replaces only its network call.

    Args:
        monkeypatch: Fixture that restores the patched function after the test.

    Returns:
        The list that receives the URL of each validation request, in order.
    """
    calls: list[str] = []  # Each validation URL of the run.

    def fake_validation(  # Stand in for the validation request of the SDK.
        url: str, *args: Any, **kwargs: Any
    ) -> RejectedReply:
        """Record the validation request and reject the token."""
        calls.append(url)  # The validation is the only request of the run.
        return RejectedReply()  # Return the rejected reply to the SDK.

    monkeypatch.setattr(requests, "get", fake_validation)  # The SDK validates with requests.get.
    return calls  # Return the list of validation URLs to the test.


def test_a_401_from_the_real_sdk_prints_no_token_and_exits_2(  # Confirm that a real SDK 401 prints no token.
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real SDK rejects the token with HTTP 401, prints a masked token internally, and the command hides it."""

    calls = reject_token_validation(monkeypatch)  # The one validation request is rejected.
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    command = SmokeCommand(  # Build the command with the real SDK session factory.
        root=root, environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG}, session_factory=mistapi.APISession
    )
    code = command.run([])  # Run the command, which the rejected validation must stop.
    captured = capsys.readouterr()  # Capture the output of the rejected run.
    assert code == 2  # HTTP 401 at the token validation.
    assert len(calls) == 1  # The validation request is the one counted request.
    assert "Requests sent: 1 of 60." in captured.out  # The validation counted once.
    assert TOKEN not in captured.out + captured.err and MASKED not in captured.out + captured.err  # Nothing leaks.
    assert TOKEN not in (root / "test-artifacts").as_posix()  # The token is not in the path either.


PROBE_TOKEN = "Qz7v-probe-value-Tx9m"  # nosec B105 - a fake test value, never a credential.
PROBE_FIRST_FOUR = "Qz7v"  # The first four characters, which the SDK prints in its masked form.
PROBE_LAST_FOUR = "Tx9m"  # The last four characters, which the SDK prints in its masked form.


def test_a_401_leaves_no_part_of_the_token_in_any_output(  # Confirm that no token part reaches any output.
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The SDK masks a rejected token to four characters at each end, and no output shows either end."""
    calls = reject_token_validation(monkeypatch)  # The SDK builds its masked message from this rejection.
    root = make_root(tmp_path)  # Build a fake repository root, so the run never reads the real checkout.
    command = SmokeCommand(  # Build the command with the probe token and the real SDK factory.
        root=root, environment={"MIST_API_TOKEN": PROBE_TOKEN, "MIST_ORG_ID": ORG}, session_factory=mistapi.APISession
    )
    code = command.run([])  # Run the command, which the rejected validation must stop.
    captured = capsys.readouterr()  # Capture the output of the rejected run.
    written = [path for path in (root / "test-artifacts").rglob("*") if path.is_file()]  # Every file the run wrote.
    text = captured.out + captured.err + "".join(path.read_text(encoding="utf-8") for path in written)  # All outputs.
    assert code == 2 and len(calls) == 1  # One rejected validation ends the run with exit code 2.
    assert "Invalid API Token" not in captured.out  # The SDK console message is not printed.
    assert "rejected by the API" in captured.err  # The structured log line ran, so its output was checked.
    assert len(written) == 1  # The evidence file is the only file that the run wrote.
    for fragment in (PROBE_TOKEN, PROBE_FIRST_FOUR, PROBE_LAST_FOUR):  # The token and each end of its masked form.
        assert fragment not in text  # No output shows the fragment.


def test_the_sdk_session_is_built_above_the_critical_console_level(  # Confirm the SDK session is above CRITICAL.
    tmp_path: Path,
) -> None:
    """The SDK prints a message only at CRITICAL or below, so the command builds the session above CRITICAL."""
    recorded: list[dict[str, Any]] = []  # The options of each session that the command builds.
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.

    def factory(**kwargs: Any) -> ResponderSession:  # Record the session options and return the fake session.
        """Record the options of the session and return the fake session."""
        recorded.append(kwargs)  # The options that the command passes to the SDK.
        return session  # Return the fake session, so the command never reaches the SDK.

    command = SmokeCommand(  # Build the command with the recording factory.
        root=make_root(tmp_path), environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG}, session_factory=factory
    )
    assert command.run([]) == 0  # A healthy run, so the session is built once.
    assert len(recorded) == 1  # One session for the run.
    assert recorded[0]["console_log_level"] > logging.CRITICAL  # Above CRITICAL, so the SDK console prints nothing.
    assert recorded[0]["logging_log_level"] == logging.WARNING  # The SDK logger level of the contract.
    assert recorded[0]["apitoken"] == TOKEN  # The token is an argument, so the SDK does not read the environment.


def test_the_sdk_logger_writes_nowhere_during_the_run(  # Confirm that SDK log records reach neither output stream.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """During the run the mistapi logger has a null handler and no propagation, so an SDK record prints nothing."""
    sdk_logger = logging.getLogger("mistapi")  # The logger that the SDK writes to.
    session = ResponderSession(healthy())  # Healthy replies, so each test changes only the path it names.

    def factory(  # Write one SDK warning during the session build, then return the session.
        **kwargs: Any,
    ) -> ResponderSession:
        """Write one SDK warning while the session opens, then return the fake session."""
        sdk_logger.warning("sdk probe record %s", "SDK-PROBE-TEXT")  # A record that the SDK could write during the run.
        return session  # Return the fake session, so the command never reaches the SDK.

    command = SmokeCommand(  # Build the command with the factory that writes the SDK record.
        root=make_root(tmp_path), environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG}, session_factory=factory
    )
    assert command.run([]) == 0  # A healthy run that writes the SDK record.
    captured = capsys.readouterr()  # Capture the output of the run.
    assert "SDK-PROBE-TEXT" not in captured.out + captured.err  # The record reaches neither stream.
    assert sdk_logger.propagate is False  # The record never reaches the root handler.
    assert any(isinstance(handler, logging.NullHandler) for handler in sdk_logger.handlers)  # The record is discarded.


def test_the_sdk_validation_runs_once_even_when_the_process_has_the_token_variable(  # Confirm one validation runs.
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The SDK reads MIST_APITOKEN from the process, so the command hides it. One validation request runs."""

    class Accepted:  # Stand in for an accepted token validation reply.
        """Fake token-validation response with HTTP 200 and one privilege."""

        status_code = 200  # Set the HTTP status of the accepted reply.

        def json(self) -> dict[str, Any]:  # Return the privileges that the SDK reads from the accepted reply.
            """Return the privileges of the token."""
            return {"privileges": PRIVILEGES}  # Return the read grant on the organization.

    validations: list[str] = []  # Collect the URL of each validation request.

    def fake_validation(  # Stand in for the validation request and accept the token.
        url: str, *args: Any, **kwargs: Any
    ) -> Accepted:
        """Count the validation request and accept the token."""
        validations.append(url)  # Each validation request is recorded.
        return Accepted()  # Return the accepted reply to the SDK.

    monkeypatch.setenv("MIST_APITOKEN", TOKEN)  # The SDK would read this variable at construction.
    monkeypatch.setattr(requests, "get", fake_validation)  # The validation request.

    def fake_get(  # Answer each organization request with the healthy body of its path.
        self: Any, url: str, *args: Any, **kwargs: Any
    ) -> Any:
        """Answer each organization request with the healthy body of its path."""
        path = urlsplit(url).path  # The path of the request, without the host.
        return SimpleNamespace(  # Build a response object with the members that the SDK reads.
            status_code=200,
            headers={},
            text=json.dumps(default_body(path)),
            json=lambda: default_body(path),
            raise_for_status=lambda: None,
            request=SimpleNamespace(headers={}, body=None),
        )

    monkeypatch.setattr(requests.Session, "get", fake_get)  # The checks use the session GET of the SDK.
    command = SmokeCommand(  # Build the command with the real SDK factory and the token variable.
        root=make_root(tmp_path),
        environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG},
        session_factory=mistapi.APISession,
    )
    assert command.run([]) == 0  # A healthy run through the real SDK.
    assert len(validations) == 1  # Exactly one validation request, not two.


def test_the_log_filter_removes_identifiers_and_contact_values() -> None:  # Confirm the log filter removes identifiers.
    """The log filter replaces a UUID, a MAC address, and an e-mail address, and keeps the rest of the text."""
    scrubbed = LogSetup().scrub_text(  # Scrub a line that holds an identifier, a MAC address, and an email address.
        f"org {ORG} device aa:bb:cc:dd:ee:ff mail user@example.com ok"
    )
    assert (  # Confirm that none of the three values remains in the line.
        ORG not in scrubbed and "aa:bb:cc:dd:ee:ff" not in scrubbed and "user@example.com" not in scrubbed
    )
    assert scrubbed.count("[redacted]") == 3 and scrubbed.endswith("ok")  # Three values, and the rest stays.


def test_the_log_filter_replaces_a_token_and_its_masked_form() -> (  # Confirm the token and masked form are replaced.
    None
):
    """A token value and the masked form that the SDK prints are both replaced."""
    setup = LogSetup()  # Create the log setup that holds the scrub list.
    setup.protect(TOKEN)  # Add the token to the scrub list.
    assert (  # Confirm that the token and its masked form are both replaced.
        setup.scrub_text(f"token {TOKEN} shown as {MASKED}") == "token [redacted] shown as [redacted]"
    )


def test_configure_silences_the_sdk_logger_and_sets_warning_level() -> None:  # Confirm the SDK logger is silenced.
    """After configure, the mistapi logger has a NullHandler, does not propagate, and is at WARNING."""
    LogSetup().configure()  # Configure the process logging, as the command does at start.
    sdk_logger = logging.getLogger("mistapi")  # Read the SDK logger that the configuration changed.
    assert sdk_logger.level == logging.WARNING  # The contract level.
    assert sdk_logger.propagate is False  # No record reaches the root handler.
    assert any(isinstance(handler, logging.NullHandler) for handler in sdk_logger.handlers)  # Records are discarded.


class TokenBearingSession:  # Stand in for an SDK session whose repr names the token.
    """Fake SDK session whose repr names the token, as a real session repr can name its authorization header.

    Why: the repr test needs a session that prints the token, so a holder that shows its session would fail the test.
    """

    def __repr__(self) -> str:  # Return a repr that names the token, to test the hiding rule.
        """Return a repr that names the token."""
        return f"TokenBearingSession(authorization='Token {TOKEN}')"  # Return the text that would leak the token.


def test_each_object_that_holds_the_token_or_the_session_hides_it_from_repr_and_str(  # Confirm holders hide the token.
    tmp_path: Path,
) -> None:
    """The repr and the str of each token holder show neither the token nor its masked form."""
    command = SmokeCommand(  # Build the command with the fake session factory.
        root=make_root(tmp_path),
        environment={"MIST_API_TOKEN": TOKEN, "MIST_ORG_ID": ORG},
        session_factory=lambda **kwargs: ResponderSession(healthy()),
    )
    assert command.run([]) == 0  # A healthy run, which fills the context, the loader, and the log setup.
    assert command.context is not None and command.loader is not None  # Each run object exists for the check below.
    governor = CallGovernor(  # Build a governor that holds a session whose repr names the token.
        session=TokenBearingSession(), request_budget=60, call_timeout_seconds=1.0, max_retries=0
    )
    holders: dict[str, object] = {  # Collect each object that can reach the token or the session.
        "SmokeCommand": command,  # Holds the environment, the loader, the context, and the log setup.
        "CheckContext": command.context,  # Holds the token and the redactor.
        "SettingsLoader": command.loader,  # Holds the token and the secrets.
        "LogSetup": command.log_setup,  # Holds the secrets of the scrub list.
        "EvidenceRedactor": EvidenceRedactor(organization_id=ORG, site_ids=(), token_value=TOKEN),  # Holds the token.
        "CallGovernor": governor,  # Holds the session.
        "PageWalker": PageWalker(governor=governor, approved_host=HOST),  # Holds the governor, so the session.
        "ReadOnlyMistClient": ReadOnlyMistClient(approved_host=HOST, governor=governor),  # Holds the governor.
    }
    for label, holder in holders.items():  # Each object that can reach the token or the session.
        for text in (repr(holder), str(holder)):  # Both printed forms of the object.
            assert TOKEN not in text and MASKED not in text, label  # Neither the token nor its masked form is printed.


def test_the_summary_counts_skipped_checks_on_their_own(  # Confirm that skipped checks are counted apart.
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Skipped checks are counted apart from the checks that ran."""
    session = ResponderSession(  # Script the usage reply with 50 requests left, which stops the run.
        healthy({"/self/usage": {"requests": 4950, "request_limit": 5000, "seconds": 5}})
    )
    run(make_root(tmp_path), [], session)  # Run the command that stops at SMK-04.
    summary = [  # Read the summary line of the run.
        line for line in capsys.readouterr().out.splitlines() if line.startswith("Checks examined")
    ][0]
    assert "Checks examined: 3." in summary and "Skipped: 7." in summary  # Three ran, seven were skipped.
