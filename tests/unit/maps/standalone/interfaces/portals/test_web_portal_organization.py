"""Unit tests for the organization of the local web portal in MistHelper.py (issue #4929).

`python MistHelper.py --web-portal` built the portal with an empty organization, so the WebSockets tab said
that the portal had no Mist session or organization. The launcher now resolves the organization first, in the
same way as the interactive mode: the context, the cache, the environment, the .env file, then one prompt.
"""

from __future__ import annotations  # WHY: keep the annotation style equal to the rest of the suite.

from types import SimpleNamespace  # WHY: stand-ins for the parsed arguments, the portal factory, and the config.
from typing import Any  # WHY: the doubles have no public type.

import pytest  # WHY: the tests use the monkeypatch fixture.

import MistHelper  # WHY: the launcher under test is a module-level function of the script.
from web_portal.app import WebPortalApp  # WHY: the test replaces the factory so that no server starts.
from web_portal.services.config import PortalConfigLoader  # WHY: the launcher reads the port from it.

ORG = "11111111-1111-4111-8111-111111111111"  # WHY: an invented organization identifier.
SESSION = object()  # WHY: an opaque stand-in for the Mist session.


class Recorder:
    """Record the organization that the launcher gives to the portal factory and to the server."""

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self.created: dict[str, Any] = {}  # The keyword arguments of the factory call.
        self.served: list[tuple[Any, str, int, bool]] = []  # The arguments of each server start.
        self.prompts = 0  # How many times the resolver ran.

    def create_app(self, **kwargs: Any) -> object:
        """Stand in for ``WebPortalApp.create_app``."""
        self.created = kwargs  # Keep the call for the assertions.
        return SimpleNamespace(name="app")  # A fake app.

    def serve(self, app: Any, host: str, port: int, debug: bool) -> None:
        """Stand in for the server start."""
        self.served.append((app, host, port, debug))  # Keep the call for the assertions.


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    """Replace the portal factory, the server, and the config so that the launcher runs without a server."""
    seen = Recorder()
    monkeypatch.setattr(WebPortalApp, "create_app", staticmethod(seen.create_app))  # No Flask app is built.
    monkeypatch.setattr(MistHelper, "_run_web_portal_server", seen.serve)  # No server starts.
    monkeypatch.setattr(PortalConfigLoader, "load_config", lambda self: {"web_port": 9611})  # A fixed port.
    monkeypatch.setattr(MistHelper, "_resolve_web_portal_host", lambda: "127.0.0.1")  # The loopback address.
    monkeypatch.setattr(MistHelper.MainEntrypoint.context, "apisession", SESSION)  # The shared session.
    return seen


class TestLaunchWebPortalOrganization:
    """The portal gets an organization before the app is built."""

    def test_an_empty_organization_is_resolved_and_shared(
        self, monkeypatch: pytest.MonkeyPatch, recorder: Recorder
    ) -> None:
        """With no organization in the context, the launcher asks the resolver and keeps the answer."""
        monkeypatch.setattr(MistHelper.MainEntrypoint.context, "org_id", None)  # The state of --web-portal.

        def resolve() -> str:
            """Count the call and give the organization."""
            recorder.prompts += 1
            return ORG

        monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", staticmethod(resolve))
        MistHelper._launch_web_portal(SimpleNamespace(debug=False))
        assert recorder.created["org_id"] == ORG and recorder.created["apisession"] is SESSION
        assert MistHelper.MainEntrypoint.context.org_id == ORG  # The rest of the process sees the same value.
        assert recorder.prompts == 1 and recorder.served[0][1:] == ("127.0.0.1", 9611, False)

    def test_a_known_organization_is_not_resolved_again(
        self, monkeypatch: pytest.MonkeyPatch, recorder: Recorder
    ) -> None:
        """With an organization in the context, the launcher never calls the resolver, so it never prompts."""
        monkeypatch.setattr(MistHelper.MainEntrypoint.context, "org_id", ORG)

        def resolve() -> str:
            """Fail the test when the launcher calls the resolver."""
            raise AssertionError("The launcher must not resolve an organization that the context holds.")

        monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", staticmethod(resolve))
        MistHelper._launch_web_portal(SimpleNamespace(debug=True))
        assert recorder.created["org_id"] == ORG and recorder.served[0][3] is True  # The debug flag passes through.

    def test_a_failed_resolution_stops_the_launch_before_any_app_exists(
        self, monkeypatch: pytest.MonkeyPatch, recorder: Recorder
    ) -> None:
        """When the resolver exits, as it does without a session, no app and no server start."""
        monkeypatch.setattr(MistHelper.MainEntrypoint.context, "org_id", "")  # An empty text value.

        def resolve() -> str:
            """Model the exit of the resolver."""
            raise SystemExit(1)

        monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", staticmethod(resolve))
        with pytest.raises(SystemExit):
            MistHelper._launch_web_portal(SimpleNamespace(debug=False))
        assert recorder.created == {} and recorder.served == []
