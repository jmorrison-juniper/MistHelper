"""Regression tests for issues 1702 and 1712."""

from __future__ import annotations  # WHY: keep annotations cheap on Python 3.13.

import ast  # WHY: inspect declarations without importing implementation details.
import logging  # WHY: action logs help diagnose unit-test failures.
from pathlib import Path  # WHY: build paths without hardcoded separators.
from types import SimpleNamespace  # WHY: create a small fake requests session.
from unittest.mock import MagicMock  # WHY: isolate bootstrap side effects.

import pytest  # WHY: use monkeypatch and tmp_path fixtures.

import MistHelper  # WHY: verify the root module contract after import.
from src.config.config_utils import ConfigUtils  # WHY: verify org resolution edge cases.
from src.refactors.initialize_mist_session import MistSessionConfigurator  # WHY: verify the single session seam.
from src.refactors.main_entrypoint import AppContext, ApplicationBootstrap, MainEntrypoint  # WHY: verify context use.

logger = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.

SESSION_GLOBAL_NAMES = {  # WHY: keep the declaration audit small and explicit.
    "apisession",  # WHY: issue 1702 removes this live module global.
    "org_id",  # WHY: issue 1702 moves this value into AppContext.
    "msp_privileges",  # WHY: issue 1702 moves this list into AppContext.
    "selected_msp",  # WHY: issue 1702 moves this value into AppContext.
}


def test_misthelper_declares_no_live_session_global() -> None:
    """MistHelper exposes context views but stores no live session global."""
    logger.info("Testing that MistHelper stores no live session global")  # WHY: log before the audit.
    module_dict = vars(MistHelper)  # WHY: read the real module dictionary after import.
    present = SESSION_GLOBAL_NAMES.intersection(module_dict)  # WHY: find state names that still store values.
    logger.debug("Live session globals present: %s", sorted(present))  # WHY: report the audit result.
    assert present == set()  # WHY: the context bridge must not place state in the module dictionary.


def test_misthelper_session_names_are_annotations_only() -> None:
    """The symbol table keeps names as annotations for the symbol gate only."""
    logger.info("Parsing MistHelper to audit session declarations")  # WHY: log before reading source.
    source = Path(MistHelper.__file__).read_text(encoding="utf-8")  # WHY: inspect the imported module text.
    tree = ast.parse(source)  # WHY: use Python syntax instead of a brittle text pattern.
    assigned = {node.target.id for node in tree.body if isinstance(node, ast.AnnAssign) and node.value is not None}
    logger.debug("Session names with values: %s", sorted(SESSION_GLOBAL_NAMES & assigned))  # WHY: report result.
    assert not (SESSION_GLOBAL_NAMES & assigned)  # WHY: annotations preserve names without storing state.


def test_two_app_context_instances_do_not_share_state() -> None:
    """Two contexts hold separate session and MSP state."""
    logger.info("Building two application contexts for an isolation check")  # WHY: log before construction.
    first = AppContext()  # WHY: first context represents one process state holder.
    second = AppContext()  # WHY: second context proves default factories do not share state.
    first.apisession = object()  # WHY: set a sentinel session on one context.
    first.msp_privileges.append({"msp_id": "msp-one"})  # WHY: mutate the list that must not be shared.
    logger.debug("Second context session is set: %s", second.apisession is not None)  # WHY: report isolation.
    assert second.apisession is None  # WHY: the second context must not inherit the first session.
    assert second.msp_privileges == []  # WHY: the second context must not share the first list.


def test_session_configurator_runs_once_and_never_adds_mist_get() -> None:
    """The session seam configures the transport once and does not patch methods."""
    logger.info("Building a fake session for the configuration seam")  # WHY: log before fixture setup.
    context = AppContext()  # WHY: the configurator uses the context as its once-only guard.
    inner_session = SimpleNamespace(mount=MagicMock(name="mount"))  # WHY: capture adapter mounts without network.
    session = SimpleNamespace(_session=inner_session, get=lambda *_args, **_kwargs: None)  # WHY: no mist_get exists.
    first = MistSessionConfigurator.configure_once(context, session, {"apitoken": "redacted"})  # WHY: first pass.
    second = MistSessionConfigurator.configure_once(context, session, {"apitoken": "redacted"})  # WHY: second pass.
    logger.debug("Mount calls: %s", inner_session.mount.call_count)  # WHY: prove no second configuration ran.
    assert first is True  # WHY: the get method is a supported read method.
    assert second is True  # WHY: the second validation still succeeds.
    assert inner_session.mount.call_count == 2  # WHY: http and https mount once each on the first pass.
    assert not hasattr(session, "mist_get")  # WHY: the seam must not add an attribute to the third-party object.


def test_credential_problem_edges_do_not_build_a_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Missing, placeholder, and absent file inputs fail locally."""
    logger.info("Clearing credential environment variables for edge checks")  # WHY: avoid host credential leakage.
    monkeypatch.delenv("MIST_APITOKEN", raising=False)  # WHY: force the missing-token branch.
    monkeypatch.delenv("MIST_API_TOKEN", raising=False)  # WHY: force the missing-token branch.
    monkeypatch.setenv("MIST_HOST", "api.mist.com")  # WHY: keep host valid so only token logic is tested.
    missing = MistHelper._collect_credential_problems(True)  # WHY: run local validation only.
    monkeypatch.setenv("MIST_APITOKEN", "your_token_here")  # WHY: force the placeholder-token branch.
    placeholder = MistHelper._collect_credential_problems(True)  # WHY: run local validation only.
    monkeypatch.chdir(tmp_path)  # WHY: make the .env lookup hermetic and absent.
    ConfigUtils._org_id_cache = None  # WHY: clear the cache before the file lookup.
    dotenv_value = ConfigUtils._resolve_org_id_from_dotenv()  # WHY: verify absent .env returns no value.
    logger.debug("Credential edge results: %s %s %s", missing, placeholder, dotenv_value)  # WHY: report summary.
    assert any("no API token found" in problem for problem in missing)  # WHY: missing token must fail local checks.
    assert any("placeholder" in problem for problem in placeholder)  # WHY: placeholder token must fail local checks.
    assert dotenv_value is None  # WHY: an absent .env file must not supply an organization.


def test_second_web_bootstrap_call_uses_separate_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """A second default bootstrap call in one process receives a separate context."""
    logger.info("Patching bootstrap side effects for a two-call check")  # WHY: no file, network, or dependency work.
    startup = MagicMock(name="startup")  # WHY: count common startup calls.
    monkeypatch.setattr(ApplicationBootstrap, "_run_common_startup", startup)  # WHY: isolate bootstrap behavior.
    monkeypatch.setattr(MistHelper, "_setup_runtime_flags", MagicMock(name="flags"), raising=False)  # WHY: avoid flags.
    dependency_mock = MagicMock(name="deps")  # WHY: avoid real dependency imports during the context test.
    monkeypatch.setattr(MistHelper, "_initialize_dependencies", dependency_mock, raising=False)  # WHY: no imports.
    first = ApplicationBootstrap(parse_cli=False)  # WHY: build the first web bootstrap.
    second = ApplicationBootstrap(parse_cli=False)  # WHY: build the second web bootstrap.
    first.context.apisession = object()  # WHY: a session on one bootstrap must not leak to another.
    first.bootstrap_for_web()  # WHY: run the first explicit startup.
    second.bootstrap_for_web()  # WHY: run the second explicit startup.
    logger.debug("Bootstrap startup call count: %s", startup.call_count)  # WHY: report the two-call result.
    assert first.context is not second.context  # WHY: default bootstrap contexts must isolate invocation state.
    assert second.context.apisession is None  # WHY: the second bootstrap must not inherit the first session.
    assert second.context is MainEntrypoint.context  # WHY: the active bridge must point to the latest bootstrap.
    assert startup.call_count == 2  # WHY: each explicit bootstrap call runs its side-effect boundary.


def test_bootstrap_can_share_explicit_context() -> None:
    """An explicit context remains shared when the caller asks for that behavior."""
    logger.info("Building two bootstraps with an explicit context")  # WHY: test the allowed sharing path.
    context = AppContext()  # WHY: explicit callers can own one context outside the bootstrap.
    first = ApplicationBootstrap(context=context, parse_cli=False)  # WHY: first owner receives caller state.
    second = ApplicationBootstrap(context=context, parse_cli=False)  # WHY: second owner receives same caller state.
    logger.debug("Explicit context was reused: %s", first.context is second.context)  # WHY: report sharing status.
    assert first.context is context  # WHY: the constructor must respect an explicit context.
    assert second.context is context  # WHY: no hidden context is allowed when the caller passes one.


def test_observable_failure_mode_contracts() -> None:
    """Failure-mode contracts stay explicit for this test module."""
    from tests.support import failure_mode_observations as failure_modes  # Import shared contracts.

    failure_modes.assert_http_status_observation(400)  # HTTP 4xx status stays observable.
    failure_modes.assert_http_status_observation(500)  # HTTP 5xx status stays observable.
