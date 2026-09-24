"""Shared fakes and row factories for the menu 270 Marvis Actions tests.

Why:
    The client, the selector, and the operation all read raw Mist rows. One
    factory builds a realistic row, and one fake session answers the list
    read, the schema read, and the resolve request. Each test then states only
    the values that it checks.

Privacy:
    Every identifier below is synthetic. No value comes from a live organization.
"""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.config import runtime_settings
from src.marvis.actions.client import LIST_PATH, RESOLVE_PATH, SCHEMA_PATH

ORG_ID = "00000000-0000-4000-8000-00000000a001"  # Synthetic organization.
SITE_ID = "00000000-0000-4000-8000-00000000b001"  # Synthetic site.
SITE_NAME = "Lab Site One"  # The name that the fake site list returns.
BASE_START_MS = 1_700_000_000_000  # 2023-11-14T22:13:20+00:00.


@dataclass
class FakeResponse:
    """A stand-in for the mistapi APIResponse object."""

    status_code: int | None
    data: Any = None


def make_raw(number: int = 1, **overrides: Any) -> dict[str, Any]:
    """Return one realistic raw suggestion row with synthetic identifiers.

    Args:
        number: A small number that makes the uuid, the row_key, and the start time unique.
        **overrides: The fields to replace.

    Returns:
        The raw row.
    """
    row: dict[str, Any] = {
        "uuid": f"00000000-0000-4000-8000-{number:012d}",
        "row_key": f"synthetic-row-key-{number:04d}",
        "suggestion_id": f"swoff-{number}",
        "org_id": ORG_ID,
        "site_id": SITE_ID,
        "category": "switch",
        "symptom": "sw_offline",
        "suggestion": "check_switch_power",
        "impact_scope": "device",
        "status": "open",
        "severity": 3,
        "label": None,
        "comment": None,
        "assignee": None,
        "entity_type": "switch",
        "entity_id": f"00000000-0000-0000-1000-0000000000{number:02d}",
        "details": {
            "disconnect_reason": "power loss",
            "impacted_tuple": [{"entity_name": f"SW-LAB-{number:02d}", "entity_mac": f"02000000{number:04d}"}],
        },
        "start_time": BASE_START_MS + number * 60_000,
        "end_time": BASE_START_MS + number * 60_000 + 600_000,
        "suggestion_time": BASE_START_MS + number * 60_000 + 120_000,
        "resolve_time": None,
        "validation_time": None,
        "reoccur_time": None,
        "duration": 600,
        "reoccur_count": None,
        "batch_count": 1,
        "self_drivable": False,
        "self_driven": None,
        "zendesk_ticket": None,
    }
    row.update(overrides)
    return row


class FakeMistSession:
    """Answer the Marvis Actions list, the schema read, and the resolve request.

    Why:
        The fake keeps one row store. A successful resolve request changes the
        stored status, so the verify read of the operation sees the change the
        same way that it sees it in Mist.
    """

    def __init__(self, rows: list[dict[str, Any]], schema_rows: list[dict[str, Any]] | None = None) -> None:
        """Keep a private copy of the rows and the schema entries."""
        self.rows = [dict(row) for row in rows]
        self.schema_rows = schema_rows if schema_rows is not None else []
        self.list_statuses: list[int | None] = []  # One queued status for each list page read. The default is 200.
        self.put_statuses: list[int | None] = []  # One queued status for each resolve request. The default is 200.
        self.schema_status: int | None = 200
        self.apply_puts = True  # False makes Mist accept a request without a status change.
        self.include_total = True  # False removes the total field from each list page.
        self.gets: list[tuple[str, dict[str, str]]] = []
        self.puts: list[tuple[str, dict[str, Any]]] = []

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> FakeResponse:
        """Return the schema or one page of the list."""
        self.gets.append((uri, dict(query or {})))
        if uri == SCHEMA_PATH:
            return FakeResponse(self.schema_status, {"data": self.schema_rows})
        assert uri == LIST_PATH.format(org_id=ORG_ID), uri
        status = self.list_statuses.pop(0) if self.list_statuses else 200
        if status != 200:
            return FakeResponse(status, {"detail": "refused"})
        return FakeResponse(200, self._page(dict(query or {})))

    def mist_put(self, uri: str, body: dict[str, Any] | None = None) -> FakeResponse:
        """Record one resolve request, and apply it when the queued status is a success."""
        assert uri == RESOLVE_PATH.format(org_id=ORG_ID), uri
        request = dict(body or {})
        self.puts.append((uri, request))
        status = self.put_statuses.pop(0) if self.put_statuses else 200
        if status is None or not 200 <= status < 300:
            return FakeResponse(status, {"detail": "the request was refused"} if status else None)
        if self.apply_puts:
            self._apply(request)
        return FakeResponse(status, {})

    def list_gets(self) -> list[dict[str, str]]:
        """Return the query of each list page read, in order."""
        return [query for uri, query in self.gets if uri != SCHEMA_PATH]

    def _page(self, query: dict[str, str]) -> dict[str, Any]:
        """Return one page of the stored rows."""
        limit = int(query["limit"])
        page = int(query["page"])
        chunk = self.rows[(page - 1) * limit : page * limit]
        data: dict[str, Any] = {"results": [dict(row) for row in chunk], "page": page, "limit": limit}
        if self.include_total:
            data["total"] = len(self.rows)
        return data

    def _apply(self, request: dict[str, Any]) -> None:
        """Change the stored row that the request names."""
        for row in self.rows:
            if row.get("row_key") == request.get("row_key"):
                row["status"] = request.get("status")
                row["label"] = request.get("label")
                row["comment"] = request.get("comment")


class ScriptedInput:
    """Answer each prompt from a list, and record every prompt text.

    Why:
        The operation reads every value through ``InputUtils.safe_input``, which
        calls ``input``. A scripted ``input`` tests the real prompt path,
        including the default for a blank answer.
    """

    def __init__(self, answers: list[str | BaseException]) -> None:
        """Keep the answers in prompt order."""
        self.answers = list(answers)
        self.prompts: list[str] = []

    def __call__(self, prompt: str = "") -> str:
        """Return the next answer. A missing answer acts as a closed stream."""
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer


@pytest.fixture
def scripted_input(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """Return a function that installs the scripted answers for one test."""

    def install(*answers: str | BaseException) -> ScriptedInput:
        scripted = ScriptedInput(list(answers))
        monkeypatch.setattr(builtins, "input", scripted)
        return scripted

    yield install


@pytest.fixture
def site_api() -> Iterator[MagicMock]:
    """Replace the mistapi module of the client, so the site read needs no network."""
    with patch("src.marvis.actions.client.mistapi") as mistapi_module:
        mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = FakeResponse(200, [])
        mistapi_module.get_all.return_value = [{"id": SITE_ID, "name": SITE_NAME}]
        yield mistapi_module


@dataclass
class OperationHarness:
    """The fakes that one operation test controls."""

    session: FakeMistSession
    resolver: MagicMock
    pacer: MagicMock
    input: ScriptedInput | None = None

    def exports(self) -> list[Any]:
        """Return the call arguments of every export write."""
        return list(self.resolver.DataExporter.write_with_format_selection.call_args_list)


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch, site_api: MagicMock, scripted_input: Any) -> Iterator[Any]:
    """Return a function that builds the fakes of one operation run.

    The function takes the raw rows and the scripted answers. It patches the
    shared dependency resolver, the pacer, the verify wait, and the page size.
    """
    monkeypatch.setattr(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 1000)
    monkeypatch.setattr("src.marvis.actions.operation.VERIFY_DELAY_SECONDS", 0)
    monkeypatch.delenv("MARVIS_RESOLVE_MAX_ACTIONS", raising=False)
    with (
        patch("src.marvis.actions.operation.SourceDependencyResolver") as resolver,
        patch("src.marvis.actions.operation.AdaptivePacer") as pacer_class,
    ):

        def build(rows: list[dict[str, Any]], *answers: str | BaseException) -> OperationHarness:
            session = FakeMistSession(rows)
            resolver.apisession = session
            resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = ORG_ID
            resolver.ConfigUtils.check_stop_signal.return_value = False
            resolver.DataExporter.write_with_format_selection.return_value = True
            built = OperationHarness(session, resolver, pacer_class.return_value)
            built.input = scripted_input(*answers)
            return built

        yield build
