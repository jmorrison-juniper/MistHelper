"""Own the shipped general portal, exact request ledger, and localhost lifecycle."""

from __future__ import annotations

import logging
import re
import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from urllib.request import urlopen

from flask import Response, request
from werkzeug.serving import BaseWSGIServer, make_server

from tests.support.upgrade_portal_e2e.owner import RunOwnerHeaderCheck
from tests.support.wip_target_controls.native import NativeMistSession, NativeScenario
from web_portal.app import WebPortalApp
from web_portal.routes.operations import _get_executor
from web_portal.services.operation import OperationExecutor

logger = logging.getLogger(__name__)


@dataclass
class PortalLedger:
    """Retain exact requests, owned threads, and bounded HTTP fault controls."""

    calls: list[dict[str, Any]] = field(default_factory=list)
    workers: set[threading.Thread] = field(default_factory=set)
    answers: dict[str, tuple[str | bytes, int]] = field(default_factory=dict)
    holds: dict[str, NativeMistSession.HeldResponse] = field(default_factory=dict)


class ControlledPortal:
    """Create the real application with controlled native transport only."""

    def __init__(self, scenario: NativeScenario) -> None:
        """Create an app and initialize its real executor before concurrent browser requests."""
        self.scenario = scenario
        self.owner = uuid.uuid4().hex
        self.ledger = PortalLedger()
        self.app = WebPortalApp.create_app(scenario.session, scenario.actions(), "controlled-org")
        self.app.before_request(self.record_request)
        self.app.after_request(self.name_owner)
        with self.app.app_context():
            self.executor: OperationExecutor = _get_executor()

    def record_request(self) -> Response | None:
        """Count actual shipped routes and apply only an exact requested HTTP fault."""
        self.ledger.workers.add(threading.current_thread())
        if request.path.startswith("/api/operations"):
            self.ledger.calls.append(
                dict(
                    method=request.method,
                    path=request.path,
                    query=request.query_string.decode(),
                    body=request.get_json(silent=True),
                )
            )
        held = self.ledger.holds.get(request.path)
        if held is not None:
            held.wait()
        answer = self.ledger.answers.get(request.path)
        if answer is not None:
            body, status = answer
            return Response(body, status=status, content_type="application/json")
        return None

    def name_owner(self, response: Response) -> Response:
        """Require each served response to identify this exact test app."""
        response.headers[RunOwnerHeaderCheck.HEADER] = self.owner
        return response

    def run(self, number: str, answers: list[str]) -> dict[str, Any]:
        """Submit the existing run request through its real Flask route."""
        logger.info("Submitting menu %s through the actual run route with %d answers", number, len(answers))
        client = self.app.test_client()
        document = client.get("/operations").get_data(as_text=True)
        token = re.search(r'<meta name="csrf-token" content="([^"]+)">', document)
        assert token is not None, "The shipped page did not supply its required CSRF control."
        response = client.post(
            "/api/operations/run",
            json={"menu_number": number, "parameters": {"input_answers": answers}},
            headers={"X-CSRFToken": token.group(1)},
        )
        RunOwnerHeaderCheck(self.owner).require(response.headers)
        assert response.status_code == 202, response.get_json()
        result = self.wait(response.get_json()["run_id"])
        logger.debug("Menu %s returned status %s through its actual handler", number, result["status"])
        return result

    def wait(self, run_id: str) -> dict[str, Any]:
        """Join only this actual run and return the real status evidence."""
        self.executor._runs[run_id]["_future"].result(timeout=15)
        result = self.executor.get_run_status(run_id)
        assert result is not None, "The real executor lost its run record."
        assert result["status"] not in ("pending", "running"), "The bounded real handler did not finish."
        return result


class LocalPortalServer:
    """Keep one localhost server and verify its response owner and shutdown."""

    def __init__(self, portal: ControlledPortal) -> None:
        """Bind a fresh operating-system port, never a production port."""
        self.portal = portal
        self.server: BaseWSGIServer = make_server("127.0.0.1", 0, portal.app, threaded=True)
        self.thread = threading.Thread(
            target=self.server.serve_forever, name="issue3158-http-" + portal.owner, daemon=False
        )
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.owner = RunOwnerHeaderCheck(portal.owner)

    def start(self) -> None:
        """Verify the owned listener before any browser journey."""
        logger.info("Starting 1 owned issue 3158 localhost server")
        self.thread.start()
        with urlopen(self.url + "/api/operations/parameters/63", timeout=10) as response:
            self.owner.require(response.headers)
            assert response.status == 200, "The owned shipped parameter route is not ready."
        logger.debug("Started 1 responsive owned server with the exact response owner")

    def close(self) -> None:
        """Stop the app, socket, executor, and only this server's threads."""
        logger.info("Stopping the owned issue 3158 localhost server")
        for held in list(self.portal.ledger.holds.values()) + list(self.portal.scenario.session.replies.values()):
            if isinstance(held, NativeMistSession.HeldResponse):
                held.release.set()
        WebPortalApp.shutdown_app(self.portal.app)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=10)
        self.portal.executor._pool.shutdown(wait=True)
        for worker in self.portal.ledger.workers:
            if worker is not threading.current_thread():
                worker.join(timeout=10)
                assert not worker.is_alive(), f"The owned request thread remains: {worker.name}"
        assert not self.thread.is_alive(), "The owned localhost server thread remains."
        assert self.server.socket.fileno() == -1, "The owned localhost socket remains open."
        assert not self.portal.app.config["EVENT_BUS"]._subscribers, "An owned SSE subscription remains."
        assert self.portal.scenario.network.calls == [], "A forbidden live HTTP call reached the guard."
        logger.debug("Stopped 1 server and cleared every owned request thread, pool, socket, and subscription")

    def resources(self) -> Iterator[threading.Thread]:
        """Expose exact owned threads for independent teardown assertions."""
        yield self.thread
        yield from self.portal.ledger.workers
        yield from self.portal.executor._pool._threads


class OwnedOutputLifecycle:
    """Remove only files under the exact temporary data directory of this proof."""

    @staticmethod
    def close(scenario: NativeScenario) -> None:
        """Count and remove owned output files without recursive or broad cleanup."""
        data = scenario.root / "data"
        logger.info("Removing the owned temporary output directory %s", data)
        assert data.resolve().parent == scenario.root.resolve(), "The owned data path changed."
        files = list(data.iterdir())
        for output in files:
            assert output.is_file() and not output.is_symlink(), "An unexpected output needs explicit cleanup review."
            output.unlink()
        data.rmdir()
        assert not data.exists(), "The owned temporary output directory remains."
        logger.debug("Removed %d owned files and 1 exact temporary output directory", len(files))
