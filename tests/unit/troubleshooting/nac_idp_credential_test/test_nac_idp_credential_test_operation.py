"""Tests for the NAC identity provider credential operation."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

import logging  # WHY: caplog checks that passwords do not reach logs.
from typing import Any  # WHY: fake classes accept dynamic runtime values.

from src.troubleshooting.nac_idp_credential_test import operation as operation_module  # WHY: patch operation seams.
from src.troubleshooting.nac_idp_credential_test.model import CredentialTestResult, IdentityProviderChoice
from src.troubleshooting.nac_idp_credential_test.prompts import NacIdpCredentialPrompts


class FakeDataExporter:
    """Capture export calls from the operation."""

    calls: list[dict[str, Any]] = []  # WHY: tests inspect the export request.

    @classmethod
    def write_with_format_selection(cls, rows: list[dict[str, str]], filename: str, **kwargs: Any) -> bool:
        """Capture one export call and report success."""
        cls.calls.append({"rows": rows, "filename": filename, "kwargs": kwargs})  # WHY: no real file write.
        return True  # WHY: operation should proceed as a successful export.


class FailingDataExporter(FakeDataExporter):
    """Capture export calls and report a write failure."""

    @classmethod
    def write_with_format_selection(cls, rows: list[dict[str, str]], filename: str, **kwargs: Any) -> bool:
        """Capture one export call and report failure."""
        cls.calls.append({"rows": rows, "filename": filename, "kwargs": kwargs})  # WHY: inspect failed writes.
        return False  # WHY: operation must log the failed export without raising.


class FakeClient:
    """Fake the Mist client used by the operation."""

    last_instance: FakeClient | None = None  # WHY: tests inspect the request after `run()`.

    def __init__(self, session: Any, org_id: str) -> None:
        """Store the session and organization values."""
        self.session = session  # WHY: verify operation passed the active session.
        self.org_id = org_id  # WHY: verify operation passed the organization identifier.
        self.requests: list[Any] = []  # WHY: tests assert whether a credential was sent.
        FakeClient.last_instance = self  # WHY: expose this fake instance to tests.

    def list_identity_providers(self) -> list[IdentityProviderChoice]:
        """Return one selectable provider."""
        return [IdentityProviderChoice("idp-1", "Corp LDAP", "ldap")]  # WHY: success path needs one provider.

    def validate_credential(self, request: Any, provider: IdentityProviderChoice) -> CredentialTestResult:
        """Return a success result after capturing the request."""
        self.requests.append(request)  # WHY: prove the operation sent one credential.
        return CredentialTestResult.from_response(provider, request.username, 200, {"status": "success"})


class FakePrompts:
    """Return successful prompt answers for operation tests."""

    @staticmethod
    def choose_provider(providers: list[IdentityProviderChoice]) -> IdentityProviderChoice:
        """Choose the first provider."""
        return providers[0]  # WHY: deterministic provider selection.

    @staticmethod
    def ask_username() -> str:
        """Return a safe test username."""
        return "user@example.net"  # WHY: operation must pass this value into the request.

    @staticmethod
    def ask_password() -> str:
        """Return a fake secret value."""
        return "hidden-value"  # WHY: tests verify this value never reaches logs or rows.

    @staticmethod
    def ask_confirmation() -> bool:
        """Confirm the send prompt."""
        return True  # WHY: success path should send the credential.


class FailureClient(FakeClient):
    """Fake a rejected credential validation."""

    def validate_credential(self, request: Any, provider: IdentityProviderChoice) -> CredentialTestResult:
        """Return a failure result with the API reason."""
        self.requests.append(request)  # WHY: failed validation still sends one confirmed request.
        return CredentialTestResult.from_response(  # WHY: model normalizes failure reason.
            provider,
            request.username,
            200,
            {"status": "failure", "error": "Invalid Credentials"},
        )


class DeclinePrompts(FakePrompts):
    """Fake a declined final confirmation."""

    @staticmethod
    def ask_confirmation() -> bool:
        """Decline the send prompt."""
        return False  # WHY: operation must not send a credential.


class CountingPrompts(FakePrompts):
    """Count each prompt seam used by the happy path."""

    prompt_count = 0  # WHY: acceptance criteria limit the number of prompts.

    @staticmethod
    def choose_provider(providers: list[IdentityProviderChoice]) -> IdentityProviderChoice:
        """Count the provider prompt and choose the first provider."""
        CountingPrompts.prompt_count += 1  # WHY: provider choice is one operator prompt.
        return providers[0]  # WHY: deterministic provider selection.

    @staticmethod
    def ask_username() -> str:
        """Count the username prompt and return a safe user."""
        CountingPrompts.prompt_count += 1  # WHY: username is one operator prompt.
        return "user@example.net"  # WHY: operation must pass this value into the request.

    @staticmethod
    def ask_password() -> str:
        """Count the password prompt and return a fake secret."""
        CountingPrompts.prompt_count += 1  # WHY: password is one hidden operator prompt.
        return "hidden-value"  # WHY: tests verify this value never reaches logs or rows.

    @staticmethod
    def ask_confirmation() -> bool:
        """Count the confirmation prompt and allow the send."""
        CountingPrompts.prompt_count += 1  # WHY: confirmation is one operator prompt.
        return True  # WHY: success path should send the credential.


def install_operation_fakes(
    monkeypatch: Any,
    client_class: type[FakeClient],
    prompts_class: type[Any],
    exporter_class: type[FakeDataExporter] = FakeDataExporter,
) -> None:
    """Install fake dependencies for one operation test."""
    FakeDataExporter.calls = []  # WHY: isolate export calls between tests.
    FailingDataExporter.calls = []  # WHY: isolate failed export calls between tests.
    FakeClient.last_instance = None  # WHY: isolate client state between tests.
    monkeypatch.setattr(operation_module.NacIdpCredentialTest, "_resolve_org_id", lambda: "org-1")  # WHY: no prompt.
    monkeypatch.setattr(
        operation_module.NacIdpCredentialTest, "_resolve_session", lambda: "session"
    )  # WHY: use a fake session.
    monkeypatch.setattr(
        operation_module.NacIdpCredentialTest, "_data_exporter", lambda: exporter_class
    )  # WHY: capture.
    monkeypatch.setattr(operation_module, "NacIdpCredentialClient", client_class)  # WHY: block live API calls.
    monkeypatch.setattr(operation_module, "NacIdpCredentialPrompts", prompts_class)  # WHY: avoid real prompts.


def test_nac_idp_credential_test_operation_writes_safe_csv(monkeypatch: Any, caplog: Any) -> None:
    """Run a successful credential test and export one safe row."""
    install_operation_fakes(monkeypatch, FakeClient, FakePrompts)  # WHY: no live prompts or API calls.
    caplog.set_level(logging.DEBUG)  # WHY: inspect all log messages for the fake password.

    operation_module.NacIdpCredentialTest.run()  # WHY: exercise the menu handler.

    assert FakeClient.last_instance is not None  # WHY: operation must create the client.
    assert len(FakeClient.last_instance.requests) == 1  # WHY: confirmed flow sends one credential.
    assert FakeDataExporter.calls[0]["filename"] == "NacIdpCredentialTest.csv"  # WHY: required output file.
    assert "hidden-value" not in caplog.text  # WHY: password must not reach logs.
    assert "hidden-value" not in str(FakeDataExporter.calls)  # WHY: password must not reach exports.


def test_nac_idp_credential_test_hidden_password_prompt() -> None:
    """Use the injected hidden prompt to read the password."""
    seen_prompts: list[str] = []  # WHY: verify the hidden prompt text was used.

    def fake_hidden(prompt: str) -> str:
        """Capture the hidden prompt and return a fake secret."""
        seen_prompts.append(prompt)  # WHY: test proves the hidden input seam was used.
        return "hidden-value"  # WHY: representative secret for prompt behavior.

    password = NacIdpCredentialPrompts.ask_password(fake_hidden)  # WHY: exercise hidden prompt helper.

    assert password == "hidden-value"  # WHY: caller receives the entered secret.
    assert seen_prompts == ["Enter test password: "]  # WHY: prompt came from hidden input function.


def test_nac_idp_credential_test_failure_prints_reason(monkeypatch: Any, caplog: Any) -> None:
    """Log the API failure reason without a traceback."""
    install_operation_fakes(monkeypatch, FailureClient, FakePrompts)  # WHY: no live prompts or API calls.
    caplog.set_level(logging.INFO)  # WHY: operator-facing failure reason uses info logs.

    operation_module.NacIdpCredentialTest.run()  # WHY: exercise the failed validation path.

    assert "Invalid Credentials" in caplog.text  # WHY: operator must see the API reason.
    assert "Traceback" not in caplog.text  # WHY: handled validation failures must not show tracebacks.


def test_nac_idp_credential_test_decline_sends_no_credential(monkeypatch: Any) -> None:
    """Stop before the API call when the operator declines confirmation."""
    install_operation_fakes(monkeypatch, FakeClient, DeclinePrompts)  # WHY: no live prompts or API calls.

    operation_module.NacIdpCredentialTest.run()  # WHY: exercise the declined confirmation path.

    assert FakeClient.last_instance is not None  # WHY: operation still reads providers before confirmation.
    assert FakeClient.last_instance.requests == []  # WHY: declined confirmation sends no credential.
    assert FakeDataExporter.calls == []  # WHY: no API result means no export row.


def test_nac_idp_credential_test_export_failure_logs_error(monkeypatch: Any, caplog: Any) -> None:
    """Log an export failure after the credential validation completes."""
    install_operation_fakes(monkeypatch, FakeClient, FakePrompts, FailingDataExporter)  # WHY: fail only export.
    caplog.set_level(logging.DEBUG)  # WHY: inspect the failure path for secrets and tracebacks.

    operation_module.NacIdpCredentialTest.run()  # WHY: exercise validation followed by export failure.

    assert FakeClient.last_instance is not None  # WHY: operation must still create the client.
    assert len(FakeClient.last_instance.requests) == 1  # WHY: export failure happens after validation.
    assert FailingDataExporter.calls[0]["filename"] == "NacIdpCredentialTest.csv"  # WHY: required output name.
    assert "MistHelper could not write NacIdpCredentialTest.csv" in caplog.text  # WHY: operator sees failure.
    assert "Traceback" not in caplog.text  # WHY: export failure must not create an unhandled exception.
    assert "hidden-value" not in caplog.text  # WHY: export failure logs must not expose the password.


def test_nac_idp_credential_test_happy_path_uses_five_or_fewer_prompts(monkeypatch: Any) -> None:
    """Keep the credential validation prompt flow within the acceptance limit."""
    CountingPrompts.prompt_count = 0  # WHY: isolate the prompt count for this run.
    install_operation_fakes(monkeypatch, FakeClient, CountingPrompts)  # WHY: count prompts without real input.

    operation_module.NacIdpCredentialTest.run()  # WHY: exercise the happy-path interaction flow.

    assert CountingPrompts.prompt_count <= 5  # WHY: SC-001 caps the menu flow at five prompts.
