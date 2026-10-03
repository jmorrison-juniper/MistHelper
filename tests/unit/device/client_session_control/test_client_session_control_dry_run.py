"""Tests for dry run client session control behavior."""

from dataclasses import dataclass, field  # WHY: fakes keep test state explicit.
from typing import Any  # WHY: fake API signature accepts a broad session object.

from src.mist.resources.device.client_session_control import handler  # WHY: monkeypatch the default site prompt path.
from src.mist.resources.device.client_session_control.handler import (
    ClientSessionControl,
    HandlerDependencies,
)  # WHY: exercise run().


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
    prompts: list[str] = []  # WHY: bounded prompt count proves the known-target flow is short.
    answers = iter(["disconnect", "AA-BB-CC-DD-EE-FF", "aabbccddeeff"])  # WHY: valid dry run inputs.

    def scripted_input(prompt: str, context: str = "") -> str:  # WHY: capture prompt count and return fake input.
        prompts.append(prompt)  # WHY: each prompt is one operator step in the bounded flow.
        return next(answers)  # WHY: provide the next scripted operator answer.

    dependencies = HandlerDependencies(  # WHY: inject all side effects into fakes.
        select_site_fn=lambda _session, _org_id: {"id": "site-1", "name": "Site One"},  # WHY: fake site.
        safe_input_fn=scripted_input,  # WHY: scripted operator input with prompt count tracking.
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
    assert len(prompts) == 3  # WHY: known site flow prompts only for action, target, and confirmation.


def test_default_site_prompt_returns_site_name_from_site_list(monkeypatch: Any) -> None:
    """Default site selection preserves the name from SiteList.csv."""
    site_id = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"  # WHY: match the live site id shape.
    site_row = {"id": site_id, "name": "Morrison House Site"}  # WHY: match the SiteList.csv row shape.
    monkeypatch.setattr(
        handler.PromptUtils, "select_site_with_logging", staticmethod(lambda: site_id)
    )  # WHY: simulate the live selector returning only an id.
    monkeypatch.setattr(
        handler.PromptUtils, "_load_site_csv_maps", staticmethod(lambda _csv: ({85: site_row}, {}))
    )  # WHY: provide the selected site name without file I/O.
    selected = ClientSessionControl._select_site_from_prompt("session", "org-1")  # WHY: exercise default selector.
    coerced = ClientSessionControl._coerce_site(selected)  # WHY: use the same normalization as run().
    assert coerced == (site_id, "Morrison House Site")  # WHY: preview and CSV must show the readable name.
