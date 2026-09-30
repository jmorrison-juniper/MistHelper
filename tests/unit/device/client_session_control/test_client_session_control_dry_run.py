"""Tests for dry run client session control behavior."""

from dataclasses import dataclass, field  # WHY: fakes keep test state explicit.
from typing import Any  # WHY: fake API signature accepts a broad session object.

from src.device.client_session_control.handler import ClientSessionControl, HandlerDependencies  # WHY: exercise run().


@dataclass
class FakeApiClient:  # WHY: fake proves dry run sends no Mist request.
    calls: list[tuple[str, str, str, str]] = field(default_factory=list)  # WHY: captured call list must stay empty.

    def send(self, session: Any, site_id: str, action_key: str, target: str) -> object:  # WHY: mimic API client.
        self.calls.append((str(session), site_id, action_key, target))  # WHY: any call fails the dry run contract.
        return {"status": "ok"}  # WHY: keep method shape compatible with live client.


@dataclass
class FakeAuditWriter:  # WHY: fake avoids writes outside the test temp area.
    rows: list[object] = field(default_factory=list)  # WHY: dry run must still write one audit row.

    def write(self, row: object) -> None:  # WHY: mimic audit writer.
        self.rows.append(row)  # WHY: capture row for assertions.


def test_dry_run_prints_preview_and_sends_nothing() -> None:  # WHY: dry run is a safety requirement.
    fake_api = FakeApiClient()  # WHY: proves no API call is made.
    fake_audit = FakeAuditWriter()  # WHY: proves audit row creation.
    printed: list[str] = []  # WHY: capture the operator preview text.
    answers = iter(["disconnect", "AA-BB-CC-DD-EE-FF", "aabbccddeeff"])  # WHY: valid dry run inputs.
    dependencies = HandlerDependencies(  # WHY: inject all side effects into fakes.
        select_site_fn=lambda _session, _org_id: {"id": "site-1", "name": "Site One"},  # WHY: fake site.
        safe_input_fn=lambda _prompt, context="": next(answers),  # WHY: scripted operator input.
        print_fn=printed.append,  # WHY: collect preview and final result lines.
        audit_writer=fake_audit,  # WHY: capture audit row.
        api_client=fake_api,  # WHY: fake Mist client.
    )
    result = ClientSessionControl.run("session", "org-1", dry_run=True, dependencies=dependencies)  # WHY: run dry.
    preview = "\n".join(printed)  # WHY: simplify preview content assertions.
    assert result == "dry_run"  # WHY: clear result distinguishes dry run from live success.
    assert fake_api.calls == []  # WHY: dry run must not send a Mist request.
    assert "disconnectSiteWirelessClient" in preview  # WHY: operator must see the operation ID.
    assert "aabbccddeeff" in preview  # WHY: operator must see the normalized target.
    assert len(fake_audit.rows) == 1  # WHY: dry run must write one audit row.
