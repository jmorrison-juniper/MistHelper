"""Tests for exact destructive confirmation."""

from dataclasses import dataclass, field  # WHY: fakes need small state bundles for assertions.
from typing import Any  # WHY: fakes accept the same broad session object as mistapi.

from src.device.client_session_control.handler import ClientSessionControl, HandlerDependencies  # WHY: run flow.
from src.device.client_session_control.models import confirmation_matches  # WHY: pure confirmation check.


@dataclass
class FakeApiClient:  # WHY: fake prevents live Mist requests during confirmation tests.
    calls: list[tuple[str, str, str, str]] = field(default_factory=list)  # WHY: store calls for no-network proof.

    def send(self, session: Any, site_id: str, action_key: str, target: str) -> object:  # WHY: mimic API client.
        self.calls.append((str(session), site_id, action_key, target))  # WHY: record the exact request attempt.
        return {"status": "ok"}  # WHY: handler only needs a success shaped result for this test.


@dataclass
class FakeAuditWriter:  # WHY: fake audit writer captures rows without touching data/.
    rows: list[object] = field(default_factory=list)  # WHY: one row per request attempt is required.

    def write(self, row: object) -> None:  # WHY: mimic durable audit write boundary.
        self.rows.append(row)  # WHY: preserve the row so assertions can inspect it.


def test_confirmation_uses_exact_normalized_target() -> None:  # WHY: confirmation accepts equivalent input forms only.
    matched = confirmation_matches("aabbccddeeff", "AA:BB:CC:DD:EE:FF")  # WHY: normalize confirmation first.
    assert matched is True  # WHY: exact normalized value must approve the destructive request.


def test_confirmation_mismatch_sends_no_request() -> None:  # WHY: mismatch must stop before the Mist call.
    fake_api = FakeApiClient()  # WHY: records whether a live call would have happened.
    fake_audit = FakeAuditWriter()  # WHY: records the failure audit row in memory.
    answers = iter(["wired_reauthenticate", "AA:BB:CC:DD:EE:FF", "00:11:22:33:44:55"])  # WHY: mismatch.
    dependencies = HandlerDependencies(  # WHY: inject all operator and side effect boundaries.
        select_site_fn=lambda _session, _org_id: {"id": "site-1", "name": "Site One"},  # WHY: fake site.
        safe_input_fn=lambda _prompt, context="": next(answers),  # WHY: scripted prompts avoid stdin.
        print_fn=lambda _message: None,  # WHY: suppress output while preserving print boundary.
        audit_writer=fake_audit,  # WHY: capture audit instead of writing a file.
        api_client=fake_api,  # WHY: capture Mist calls instead of sending them.
    )
    result = ClientSessionControl.run("session", "org-1", dry_run=False, dependencies=dependencies)  # WHY: run flow.
    assert result == "confirmation_failed"  # WHY: operator must see a clear failure result.
    assert fake_api.calls == []  # WHY: no Mist request is allowed after mismatch.
    assert len(fake_audit.rows) == 1  # WHY: failed confirmation is still one request attempt.
