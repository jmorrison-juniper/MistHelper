"""Fake Mist calls and payloads for the EX hardware inventory tests.

Why:
    Every test of the scope and run code must use mocked Mist responses. These
    fakes install in place of the SDK calls, record what the code asked for, and
    build the profile payloads of the three credential kinds. No value here is
    real, and no test needs a credential.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import mistapi
import pytest
import requests


class Payloads:
    """Build the invented profile payloads and SDK response doubles."""

    @staticmethod
    def response(status: int = 200, data: Any = None, next_link: str | None = None) -> SimpleNamespace:
        """Return a double of an SDK response with the three fields that the code reads."""
        return SimpleNamespace(status_code=status, data=data, next=next_link)

    @staticmethod
    def org_grant(org_id: str, name: str | None = "Example Org", scope: str | None = "org") -> dict[str, Any]:
        """Return one organization privilege as ``getSelf`` lists it."""
        grant: dict[str, Any] = {"org_id": org_id, "role": "admin"}  # The fields that the reader uses.
        if scope is not None:  # A missing scope is a legal shape that the reader treats as org.
            grant["scope"] = scope
        if name is not None:  # A missing name makes the reader fall back to the identifier.
            grant["name"] = name
        return grant

    @staticmethod
    def msp_grant(msp_id: str, scope: str | None = "msp") -> dict[str, Any]:
        """Return one MSP privilege as ``getSelf`` lists it."""
        grant: dict[str, Any] = {"msp_id": msp_id, "role": "admin"}  # The fields that the reader uses.
        if scope is not None:  # A missing scope is a legal shape that the reader treats as msp.
            grant["scope"] = scope
        return grant

    @classmethod
    def profile(cls, grants: list[dict[str, Any]], email: str | None = None) -> SimpleNamespace:
        """Return a good ``getSelf`` answer. An organization token has no email."""
        data: dict[str, Any] = {"name": "example", "privileges": grants}  # Invented values.
        if email is not None:  # Only a user account has an email address.
            data["email"] = email
        return cls.response(200, data)


class FakeMist:
    """Install fake SDK calls in place of the real ones and record each call."""

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        profile: Any,
        msp_pages: dict[str, list[Any]] | None = None,
    ) -> None:
        """Patch ``getSelf``, ``listMspOrgs``, and ``get_next``.

        Args:
            monkeypatch: The pytest fixture that restores each patch.
            profile: The ``getSelf`` answer, or an exception to raise.
            msp_pages: For each MSP, the pages in order. The first page answers ``listMspOrgs``.
        """
        self.calls: list[str] = []  # The name of each SDK call in order.
        self.console_levels: list[int] = []  # The SDK console level at each call, to prove the mute.
        self._profile = profile  # The answer or the error of ``getSelf``.
        self._pages = {key: list(value) for key, value in (msp_pages or {}).items()}  # Pages left for each MSP.
        self._current: str | None = None  # The MSP whose pages ``get_next`` serves.
        monkeypatch.setattr(mistapi.api.v1.self.self, "getSelf", self._get_self)
        monkeypatch.setattr(mistapi.api.v1.msps.orgs, "listMspOrgs", self._list_msp_orgs)
        monkeypatch.setattr(mistapi, "get_next", self._get_next)

    def _record(self, name: str) -> None:
        """Remember one call and the SDK console level at that moment."""
        from mistapi.__api_response import console  # The object that the mute changes.

        self.calls.append(name)  # Keep the order of calls.
        self.console_levels.append(console.level)  # Prove that the SDK print is off during the call.

    def _get_self(self, session: Any) -> Any:
        """Answer the profile read, or raise the planned error."""
        self._record("getSelf")
        if isinstance(self._profile, Exception):  # A planned transport fault.
            raise self._profile
        return self._profile

    def _list_msp_orgs(self, session: Any, msp_id: str) -> Any:
        """Answer the first page of one MSP list, or raise the planned error."""
        self._record("listMspOrgs")
        self._current = msp_id  # ``get_next`` serves the pages of this MSP.
        pages = self._pages.get(msp_id, [])  # The pages that the test planned.
        first = pages.pop(0) if pages else Payloads.response(404, {})  # An unplanned MSP is not found.
        if isinstance(first, Exception):  # A planned transport fault.
            raise first
        return first

    def _get_next(self, session: Any, response: Any) -> Any:
        """Answer the next page, or None when none is planned."""
        self._record("get_next")
        pages = self._pages.get(self._current or "", [])  # The pages left for the current MSP.
        return pages.pop(0) if pages else None


class Batches:
    """Build the previews and rows that the batch service returns."""

    ORG = "11111111-1111-4111-8111-111111111111"  # An invented organization.

    @classmethod
    def identity(cls, index: int, org_id: str | None = None, with_key: bool = True) -> dict[str, Any]:
        """Return the identity of one connected EX switch, with its target key for a preview."""
        identity: dict[str, Any] = {
            "org_id": org_id or cls.ORG,
            "site_id": f"site-{index % 2}",
            "site_label": f"Site {index % 2}",
            "target_type": "device",
            "target_id": f"device-{index}",
            "device_id": f"device-{index}",
            "device_type": "ex",
            "status": "connected",
            "map_id": None,
            "client_mac": None,
            "label": f"ex-{index:02d}",
        }
        if with_key:  # A preview adds the key to each identity. A batch row keeps it apart.
            identity["target_key"] = f"key-{index}"
        return identity

    @classmethod
    def payload(
        cls,
        indexes: list[int],
        excluded: dict[str, int] | None = None,
        minutes: float = 5.0,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        """Return the preview payload of the service for the given switches."""
        expires = datetime.now(UTC) + timedelta(minutes=minutes)  # The service writes UTC text.
        return {
            "preview_id": f"preview-{len(indexes)}",
            "expires_at": expires.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "targets": [cls.identity(index, org_id) for index in indexes],
            "target_count": len(indexes),
            "excluded": excluded or {},
            "confirmation": {"required": True, "phrase": f"RUN {len(indexes)} TARGETS", "safety": "shell"},
        }

    @staticmethod
    def row(index: int, state: str = "completed", reason: str | None = None, files: list[str] | None = None) -> dict:
        """Return one target row of the batch, as the progress summary lists it."""
        return {
            "target_key": f"key-{index}",
            "target": Batches.identity(index, with_key=False),
            "state": state,
            "reason_code": reason,
            "files": files if files is not None else ([f"hardware/ex-{index:02d}.xml"] if state == "completed" else []),
        }


class FakeBatchService:
    """Stand in for the portal batch service with scripted answers.

    The service records each call, and it records the ledger organization at each call so a test can prove
    that the binding is active while the run reads Mist.
    """

    def __init__(self, ledger: Any = None) -> None:
        """Start with no script.

        Args:
            ledger: A ledger double whose ``org_id`` the service records at each call, or None.
        """
        self.previews: list[Any] = []  # The preview answers in order. An exception is raised.
        self.rows: list[dict[str, Any]] = []  # The rows that the final summary lists.
        self.polls_until_final = 2  # How many summary calls answer "running".
        self.page_size = 500  # A test sets a small value to prove paging.
        self.start_error: Exception | None = None  # Raised by ``start`` when set.
        self.interrupt_on_poll: list[int] = []  # Summary call numbers that raise KeyboardInterrupt.
        self.calls: list[tuple[str, Any]] = []  # Each call with its argument.
        self.ledger_orgs: list[str | None] = []  # The ledger organization at each call.
        self.stopped = False  # Set by the fake manager.
        self._ledger = ledger  # The ledger to read.
        self._polls = 0  # Summary calls so far.

    def _note(self, name: str, argument: Any = None) -> None:
        """Record one call and the ledger organization."""
        self.calls.append((name, argument))
        self.ledger_orgs.append(getattr(self._ledger, "org_id", None))

    def preview(self, body: Any) -> dict[str, Any]:
        """Return the next scripted preview, or raise it."""
        self._note("preview", body)
        answer = self.previews.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return cast(dict[str, Any], answer)

    def start(self, body: Any) -> dict[str, Any]:
        """Admit the batch, or raise the scripted error."""
        self._note("start", body)
        if self.start_error is not None:
            raise self.start_error
        return {"session_id": "session-1"}

    def summary(self, session_id: str) -> dict[str, Any]:
        """Answer the batch summary. It becomes final after the scripted number of polls."""
        self._polls += 1
        self._note("summary", session_id)
        if self._polls in self.interrupt_on_poll:  # A scripted Ctrl+C.
            raise KeyboardInterrupt
        final = self.stopped or self._polls > self.polls_until_final
        return {
            "batch": {
                "status": "completed" if final else "running",
                "artifact_status": "ready" if final else "writing",
                "run_id": "run-folder-1",
                "target_count": len(self.rows),
            }
        }

    def targets(self, session_id: str, after: int, limit: int) -> dict[str, Any]:
        """Answer one page of rows, with the cursor of the real service."""
        self._note("targets", after)
        page = self.rows[after : after + min(limit, self.page_size)]
        next_after = after + len(page)
        return {"targets": page, "next_after": next_after, "complete": next_after >= len(self.rows)}


class FakeBatchManager:
    """Stand in for the session manager. A stop makes the fake service final."""

    def __init__(self, service: FakeBatchService) -> None:
        """Keep the service that a stop must change."""
        self._service = service
        self.stops: list[str] = []  # The session identifier of each stop.
        self.shutdowns = 0  # The number of shutdown calls.

    def stop(self, session_id: str) -> dict[str, Any]:
        """Record the stop and end the fake batch."""
        self.stops.append(session_id)
        self._service.stopped = True
        return {}

    def shutdown(self) -> None:
        """Record the shutdown."""
        self.shutdowns += 1


class FakeStack:
    """Duck-type of ``BatchStack`` for the tests of the run helpers."""

    def __init__(self, root: Any, ledger: Any = None, concurrency: int = 3) -> None:
        """Build a stack with a fake service, a fake manager, and a session that holds the ledger."""
        self.service = FakeBatchService(ledger)
        self.manager = FakeBatchManager(self.service)
        self.root = root  # The folder of the run folders.
        self.org_id = Batches.ORG  # The organization of the stack.
        self.concurrency = concurrency  # The shells open at the same time.
        self.apisession = ledger_session(ledger)  # A session whose adapter holds the ledger.


def ledger_session(ledger: Any) -> Any:
    """Return an API session double whose HTTP session mounts an adapter that holds the ledger."""
    if ledger is None:  # A session with no admission adapter.
        return SimpleNamespace(_session=requests.Session())
    inner = requests.Session()  # A real session, so the real adapter lookup runs.
    inner.mount("https://", SimpleNamespace(ledger=ledger))  # type: ignore[arg-type]  # The lookup needs only ``ledger``.
    return SimpleNamespace(_session=inner)


class ScriptedOrganizations:
    """Replace the batch stack and the batch driver of the operation with scripted answers.

    A test sets ``previews`` and ``runs`` by organization identifier. The operation then builds one fake stack
    and one fake driver for each organization, and the script records what the operation asked for.
    """

    def __init__(self, concurrency: int = 3) -> None:
        """Start with no script."""
        self.previews: dict[str, Any] = {}  # A BatchPreview, or an exception to raise.
        self.runs: dict[str, Any] = {}  # A BatchRunResult, or an exception to raise.
        self.run_order: list[str] = []  # The organizations that were run, in order.
        self.shutdowns: list[str] = []  # The organizations whose stack was shut down.
        self.concurrency = concurrency  # The value that every stack reports.

    def stack(self, apisession: Any, org_id: str, root: Any, settings: Any) -> SimpleNamespace:
        """Build the fake stack of one organization."""
        return SimpleNamespace(
            org_id=org_id,
            concurrency=self.concurrency,
            shutdown=lambda: self.shutdowns.append(org_id),
        )

    def runner(self, stack: Any, org_name: str) -> SimpleNamespace:
        """Build the fake driver of one organization."""

        def preview() -> Any:
            """Return the scripted preview, or raise it."""
            answer = self.previews[stack.org_id]
            if isinstance(answer, BaseException):
                raise answer
            return answer

        def run(confirmed: Any) -> Any:
            """Return the scripted run result, or raise it."""
            self.run_order.append(stack.org_id)
            answer = self.runs[stack.org_id]
            if isinstance(answer, BaseException):
                raise answer
            return answer

        return SimpleNamespace(preview=preview, run=run)
