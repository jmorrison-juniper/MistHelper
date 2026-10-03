"""Operation tests for the guest portal SMS provider test operation."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

from types import SimpleNamespace  # WHY: fake exporter object needs one method.

import pytest  # WHY: monkeypatch and caplog fixtures validate side effects.

from src.mist.intelligence.troubleshooting.sms_provider_test import inputs as input_module
from src.mist.intelligence.troubleshooting.sms_provider_test import operation as operation_module
from src.mist.intelligence.troubleshooting.sms_provider_test.inputs import SmsProviderPrompts, SmsProviderSecretPrompt
from src.mist.intelligence.troubleshooting.sms_provider_test.model import (
    SMSGLOBAL_PROVIDER,
    TWILIO_PROVIDER,
    SmsProviderApiResult,
)
from src.mist.intelligence.troubleshooting.sms_provider_test.operation import SmsProviderTest


@pytest.fixture(autouse=True)
def interactive_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make operation tests run as if a terminal is attached."""
    fake_stdin = SimpleNamespace(isatty=lambda: True)  # WHY: most operation tests exercise the interactive path.
    monkeypatch.setattr(operation_module.sys, "stdin", fake_stdin)  # WHY: pytest may not provide a real TTY.


class FakePrompts:
    """Prompt stand-in for operation tests."""

    def __init__(self, confirmed: bool, provider_values: dict[str, str]) -> None:
        """Keep the confirmation and provider values for the test."""
        self.confirmed = confirmed  # WHY: test controls whether an API call can happen.
        self.provider_values = provider_values  # WHY: operation reads these values as prompt answers.

    def ask_provider(self) -> object:
        """Return Twilio as the selected provider."""
        return TWILIO_PROVIDER  # WHY: all operation tests use one provider unless stated otherwise.

    def ask_values(self, _provider: object) -> dict[str, str]:
        """Return the configured prompt values."""
        return self.provider_values  # WHY: operation builds the request body from these values.

    def ask_confirmation(self, _provider: object, _destination: str) -> bool:
        """Return the configured confirmation answer."""
        return self.confirmed  # WHY: operation sends only when this value is True.


class FakeClient:
    """Client stand-in that returns a configured response."""

    calls: list[dict[str, str]] = []  # WHY: tests assert when an API request was sent.
    response = SmsProviderApiResult(200, "OK")  # WHY: default accepted response.

    def __init__(self, _session: object) -> None:
        """Accept the session argument used by the real client."""
        self.session_seen = True  # WHY: keep the constructor side effect simple.

    def test_provider(self, _provider: object, body: dict[str, str]) -> SmsProviderApiResult:
        """Record the body and return the configured response."""
        assert "to" in body  # WHY: every provider request must carry the destination field.
        self.calls.append(body)  # WHY: test can assert whether the request was sent.
        return self.response  # WHY: operation builds the result row from this value.


def test_hidden_prompt_collects_secret_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Credential fields must use hidden input."""
    visible_answers = iter(["+911122334455"])  # WHY: SMSGlobal has one visible destination field.
    hidden_prompts: list[str] = []  # WHY: record which credential prompts used getpass.

    def fake_safe_input(*_args: object, **_kwargs: object) -> str:
        return next(visible_answers)  # WHY: visible prompt returns the destination number.

    def fake_secret(prompt: str) -> str:
        hidden_prompts.append(prompt)  # WHY: prove hidden input handled the credential prompt.
        return "secret-value"  # WHY: non-empty credential lets validation pass.

    monkeypatch.setattr(input_module.InputUtils, "safe_input", fake_safe_input)  # WHY: avoid terminal input.
    prompts = SmsProviderPrompts(SmsProviderSecretPrompt(fake_secret))  # WHY: inject fake hidden input.
    values = prompts.ask_values(SMSGLOBAL_PROVIDER)  # WHY: collect values for the provider schema.
    assert values == {  # WHY: all OpenAPI fields must be collected.
        "smsglobal_api_key": "secret-value",
        "smsglobal_api_secret": "secret-value",
        "to": "+911122334455",
    }
    assert len(hidden_prompts) == 2  # WHY: both SMSGlobal credential fields must be hidden.


def test_confirmation_refusal_sends_no_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """A refusal at the confirmation prompt must stop before the API call."""
    FakeClient.calls = []  # WHY: reset the class-level call recorder.
    prompt_values = {  # WHY: provide complete Twilio values so only confirmation controls the send.
        "from": "+185051234567",
        "to": "+19999999999",
        "twilio_auth_token": "token-secret",
        "twilio_sid": "sid-secret",
    }
    monkeypatch.setattr(operation_module, "SmsProviderPrompts", lambda: FakePrompts(False, prompt_values))
    monkeypatch.setattr(operation_module, "SmsProviderTestClient", FakeClient)  # WHY: fail if operation sends.
    SmsProviderTest.run()  # WHY: run the menu flow with confirmation refused.
    assert FakeClient.calls == []  # WHY: no API request may be sent after refusal.


def test_non_tty_stops_before_hidden_prompt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """A piped run must stop before hidden provider prompts."""
    FakeClient.calls = []  # WHY: reset the class-level call recorder.
    fake_stdin = SimpleNamespace(isatty=lambda: False)  # WHY: simulate a pipe or scheduled job.
    monkeypatch.setattr(operation_module.sys, "stdin", fake_stdin)  # WHY: avoid the real terminal state.
    monkeypatch.setattr(operation_module, "SmsProviderTestClient", FakeClient)  # WHY: prove no request is sent.
    caplog.set_level("ERROR")  # WHY: capture the guard log line.

    SmsProviderTest.run()  # WHY: exercise the non-interactive guard.

    message = SmsProviderTest._non_interactive_message()  # WHY: assert the exact operator output.
    assert capsys.readouterr().out.strip() == message  # WHY: piped operators must see one clear sentence.
    assert message in caplog.text  # WHY: the stop reason must be logged.
    assert FakeClient.calls == []  # WHY: no SMS provider API request may be sent.


def test_non_2xx_response_is_exported_without_secret(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed response must be logged and exported without credentials."""
    FakeClient.calls = []  # WHY: reset the class-level call recorder.
    FakeClient.response = SmsProviderApiResult(403, "token-secret refused")  # WHY: simulate an echoing error.
    exported_rows: list[dict[str, str | int | None]] = []  # WHY: capture the export row for assertions.
    prompt_values = {  # WHY: provide complete Twilio values for a confirmed run.
        "from": "+185051234567",
        "to": "+19999999999",
        "twilio_auth_token": "token-secret",
        "twilio_sid": "sid-secret",
    }

    def fake_write(rows: list[dict[str, str | int | None]], *_args: object, **_kwargs: object) -> bool:
        exported_rows.extend(rows)  # WHY: inspect exactly what would be written to the data file.
        return True  # WHY: keep focus on the row content.

    monkeypatch.setattr(operation_module, "SmsProviderPrompts", lambda: FakePrompts(True, prompt_values))
    monkeypatch.setattr(operation_module, "SmsProviderTestClient", FakeClient)  # WHY: use a no-network client.
    monkeypatch.setattr(  # WHY: route export through a fake writer.
        SmsProviderTest,
        "_data_exporter",
        staticmethod(lambda: SimpleNamespace(write_with_format_selection=fake_write)),
    )
    caplog.set_level("DEBUG")  # WHY: capture all operation and client log messages.
    SmsProviderTest.run()  # WHY: run the confirmed non-2xx path.
    assert len(FakeClient.calls) == 1  # WHY: confirmation allowed exactly one API request.
    assert exported_rows[0]["verdict"] == "failed"  # WHY: non-2xx response must be a failed verdict.
    assert exported_rows[0]["http_status"] == 403  # WHY: output must include the status code.
    assert "token-secret" not in str(exported_rows)  # WHY: credentials must not reach the output row.
    assert "sid-secret" not in str(exported_rows)  # WHY: every credential value must be absent.
    assert "token-secret" not in caplog.text  # WHY: credentials must not reach log messages.
