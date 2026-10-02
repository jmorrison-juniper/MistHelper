"""Unit tests for SSR registration command support."""

from __future__ import annotations  # WHY: keep annotations import-safe during test collection.

import logging  # WHY: caplog uses logging levels to capture operation output.
from pathlib import Path  # WHY: tests replace the operation output path with a project-local path.
from typing import Any  # WHY: fake response data has dynamic JSON shape.

import pytest  # WHY: pytest supplies fixtures and assertions for this package.

from src.gateway.ssr_registration.client import SsrRegistrationClient  # WHY: test the raw API path seam.
from src.gateway.ssr_registration.model import RegistrationCommandSet  # WHY: test pure response formatting.
from src.gateway.ssr_registration.operation import SsrRegistrationCommands  # WHY: test the menu operation.

SECRET_CODE = "SECRET-REG-CODE"  # WHY: a stable sentinel proves logs do not leak the code.


class FakeResponse:
    """Small Mist response fake for operation tests."""

    def __init__(self, status_code: int, data: dict[str, Any]) -> None:
        """Store the fake HTTP status and JSON body."""
        self.status_code = status_code  # WHY: operation branches on the Mist status code.
        self.data = data  # WHY: operation formats the Mist response body.


class FakeSession:
    """Small Mist session fake for client tests."""

    def __init__(self, response: FakeResponse | None = None) -> None:
        """Create an empty call record and a configured response."""
        self.calls: list[tuple[str, dict[str, str] | None]] = []  # WHY: tests assert path and query values.
        self.response = response or FakeResponse(200, sample_payload())  # WHY: tests choose success or failure.

    def mist_get(self, path: str, query: dict[str, str] | None = None) -> FakeResponse:
        """Record the GET call and return the configured fake response."""
        self.calls.append((path, query))  # WHY: capture the exact client request.
        return self.response  # WHY: client callers receive the Mist-like response selected by each test.


class FakeClient:
    """Operation client fake that avoids network access."""

    response = FakeResponse(200, {})  # WHY: each test sets the response that fetch_commands returns.

    def __init__(self, apisession: object) -> None:
        """Accept the shared session dependency."""
        self.apisession = apisession  # WHY: keep the constructor shape identical to the real client.

    def fetch_commands(self, org_id: str) -> FakeResponse:
        """Return the configured response for the operation."""
        assert org_id == "org-1"  # WHY: prove the operation uses the resolved organization.
        return self.response  # WHY: tests control success and failure paths.


class FakeConfigUtils:
    """Organization resolver fake for operation tests."""

    @staticmethod
    def get_cached_or_prompted_org_id() -> str:
        """Return the test organization identifier."""
        return "org-1"  # WHY: avoid an interactive organization prompt in unit tests.


class FakeResolver:
    """SourceDependencyResolver fake for operation tests."""

    apisession = object()  # WHY: the operation passes this value to the fake client.
    ConfigUtils = FakeConfigUtils  # WHY: the operation resolves the organization through this attribute.


def sample_payload() -> dict[str, str]:
    """Return a representative Mist registration command response."""
    return {  # WHY: fields match the documented OpenAPI response schema.
        "conductor_cmd": f"register mist {SECRET_CODE}",
        "registration_code": SECRET_CODE,
        "router_shell_cmd": f"128agent register --registration-code {SECRET_CODE}",
    }


@pytest.fixture(autouse=True)
def restore_operation_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install operation fakes and restore mutable class state for each test."""
    output_path = Path("tests") / "unit" / "gateway" / "ssr_registration" / "artifacts" / "commands.txt"
    if output_path.exists():  # WHY: each test starts without a prior output file.
        output_path.unlink()  # WHY: stale output would hide write-guard defects.
    monkeypatch.setattr(SsrRegistrationCommands, "client_class", FakeClient)  # WHY: avoid network access.
    monkeypatch.setattr(SsrRegistrationCommands, "output_path", output_path)  # WHY: write under owned tests path.
    monkeypatch.setattr(
        "src.gateway.ssr_registration.operation.SourceDependencyResolver", FakeResolver
    )  # WHY: avoid real resolver prompts and sessions.
    yield  # WHY: let the test run with the fakes installed.
    if output_path.exists():  # WHY: remove project-local test artifacts after each run.
        output_path.unlink()  # WHY: leave no sensitive command artifact behind.
    if output_path.parent.exists():  # WHY: remove the empty artifact directory created by write tests.
        output_path.parent.rmdir()  # WHY: keep the working tree clean after tests.


def test_model_formats_registration_commands() -> None:
    """The model prints every command field returned by Mist."""
    command_set = RegistrationCommandSet.from_payload(sample_payload())  # WHY: normalize the documented payload.
    text = command_set.to_text()  # WHY: render the operator-facing text.
    assert "Conductor command" in text  # WHY: conductor command guidance must be visible.
    assert "Router shell command" in text  # WHY: router shell command guidance must be visible.
    assert SECRET_CODE in text  # WHY: console and file output intentionally include the code.


def test_client_uses_raw_registration_path_with_ttl() -> None:
    """The client calls the raw path because the installed SDK lacks the helper."""
    session = FakeSession()  # WHY: capture the raw API call.
    client = SsrRegistrationClient(session)  # WHY: use the real client against the fake session.
    client.fetch_commands("org-1", ttl=30)  # WHY: exercise the optional ttl query path.
    assert session.calls == [("/api/v1/orgs/org-1/128routers/register_cmd", {"ttl": "30"})]


def test_client_returns_4xx_response_for_operation_handling() -> None:
    """The client returns a 4xx response so the operation can report it."""
    response = FakeResponse(403, {"detail": "permission denied"})  # WHY: simulate a client-side API refusal.
    session = FakeSession(response)  # WHY: provide the 4xx response through the Mist session seam.
    client = SsrRegistrationClient(session)  # WHY: exercise the real client against the fake session.
    result = client.fetch_commands("org-1")  # WHY: read the response without network access.
    assert result.status_code == 403  # WHY: the caller must receive the exact HTTP failure status.
    assert result.data == {"detail": "permission denied"}  # WHY: error detail must remain available to the caller.
    assert session.calls == [("/api/v1/orgs/org-1/128routers/register_cmd", None)]


def test_client_returns_5xx_response_for_operation_handling() -> None:
    """The client returns a 5xx response so the operation can report it."""
    response = FakeResponse(503, {"detail": "service unavailable"})  # WHY: simulate a server-side API failure.
    session = FakeSession(response)  # WHY: provide the 5xx response through the Mist session seam.
    client = SsrRegistrationClient(session)  # WHY: exercise the real client against the fake session.
    result = client.fetch_commands("org-1")  # WHY: read the response without network access.
    assert result.status_code == 503  # WHY: the caller must receive the exact HTTP failure status.
    assert result.data == {"detail": "service unavailable"}  # WHY: error detail must remain available to the caller.
    assert session.calls == [("/api/v1/orgs/org-1/128routers/register_cmd", None)]


def test_operation_prints_and_writes_only_after_yes(monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    """The operation prints after the show answer and writes after the write answer."""
    prompts: list[str] = []  # WHY: record prompt order without using stdin.
    FakeClient.response = FakeResponse(200, sample_payload())  # WHY: provide successful command text.
    monkeypatch.setattr(
        "src.gateway.ssr_registration.operation.InputUtils.safe_input",
        lambda prompt, **_: prompts.append(prompt) or "y",
    )
    SsrRegistrationCommands.run()  # WHY: execute the full menu handler.
    output = capsys.readouterr().out  # WHY: capture console text and prompt-free read behavior.
    assert output.index("SSR registration commands") < len(output)  # WHY: command text reached the console.
    assert prompts == [  # WHY: the show consent comes first, and the write consent is a separate gate.
        "The registration commands hold a sensitive code. Print them to the console? (y/N): ",
        "Write registration commands to data/SsrRegistrationCommands.txt? (y/N): ",
    ]
    assert SsrRegistrationCommands.output_path.read_text(encoding="utf-8").count(SECRET_CODE) == 3


def test_operation_prints_without_writing_when_only_show_is_approved(
    monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    """The operator can read the code on the console and still refuse the file."""
    answers = iter(["y", "N"])  # WHY: approve the console print, decline the file write.
    FakeClient.response = FakeResponse(200, sample_payload())  # WHY: provide successful command text.
    monkeypatch.setattr(
        "src.gateway.ssr_registration.operation.InputUtils.safe_input", lambda prompt, **_: next(answers)
    )
    SsrRegistrationCommands.run()  # WHY: execute the show-only path.
    output = capsys.readouterr().out  # WHY: capture the console copy.
    assert output.count(SECRET_CODE) == 3  # WHY: the console copy is the reason the operation exists.
    assert not SsrRegistrationCommands.output_path.exists()  # WHY: a declined write answer leaves no file.


def test_operation_skips_write_when_answer_is_no(monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    """The operation leaves the file absent when the answer is not yes."""
    FakeClient.response = FakeResponse(200, sample_payload())  # WHY: provide successful command text.
    monkeypatch.setattr("src.gateway.ssr_registration.operation.InputUtils.safe_input", lambda prompt, **_: "N")
    SsrRegistrationCommands.run()  # WHY: execute the declined write path.
    output = capsys.readouterr().out  # WHY: prove the console did not expose the commands.
    assert SECRET_CODE not in output  # WHY: a declined answer must not expose the registration code.
    assert "sensitive code" in output  # WHY: footer explains why command text was withheld.
    assert not SsrRegistrationCommands.output_path.exists()  # WHY: no answer other than y may write the file.


def test_operation_handles_non_2xx_without_traceback(capsys: Any) -> None:
    """The operation prints a status code and exits cleanly on non-2xx."""
    FakeClient.response = FakeResponse(403, {"detail": "denied"})  # WHY: simulate a forbidden API response.
    SsrRegistrationCommands.run()  # WHY: execute the failed read path.
    output = capsys.readouterr().out  # WHY: capture the operator-facing error.
    assert "The API returned HTTP 403." in output  # WHY: the operator needs the status code.
    assert "Traceback" not in output  # WHY: failures must not expose a stack trace.


def test_operation_logs_no_registration_code(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """The operation logs no registration code while writing the sensitive file."""
    FakeClient.response = FakeResponse(200, sample_payload())  # WHY: provide command text that holds the code.
    monkeypatch.setattr("src.gateway.ssr_registration.operation.InputUtils.safe_input", lambda prompt, **_: "y")
    caplog.set_level(logging.DEBUG)  # WHY: capture the most verbose logs for leak detection.
    SsrRegistrationCommands.run()  # WHY: execute the write path.
    assert SECRET_CODE not in caplog.text  # WHY: logs must never hold the registration code.
    assert str(SsrRegistrationCommands.output_path) in caplog.text  # WHY: path logging is required.
