"""Regression tests for issues 1702 and 1712."""

from __future__ import annotations  # WHY: keep annotations cheap on Python 3.13.

import ast  # WHY: inspect declarations without importing implementation details.
import logging  # WHY: action logs help diagnose unit-test failures.
from pathlib import Path  # WHY: build paths without hardcoded separators.
from types import SimpleNamespace  # WHY: create a small fake requests session.
from unittest.mock import MagicMock  # WHY: isolate bootstrap side effects.

import pytest  # WHY: use monkeypatch and tmp_path fixtures.

import MistHelper  # WHY: verify the root module contract after import.
from src.foundation.runtime.config.config_utils import ConfigUtils  # WHY: verify org resolution edge cases.
from src.foundation.support.refactors.initialize_mist_session import (
    MistSessionConfigurator,
)  # WHY: verify the single session seam.
from src.foundation.support.refactors.main_entrypoint import (
    AppContext,
    ApplicationBootstrap,
    MainEntrypoint,
)  # WHY: verify context use.

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


class TestTypedModuleContext:
    """Preserve context routing and policy admission through typed module methods."""

    @pytest.mark.parametrize(
        ("module_name", "context_name"),
        (
            ("apisession", "apisession"),
            ("org_id", "org_id"),
            ("msp_privileges", "msp_privileges"),
            ("selected_msp", "selected_msp"),
            ("OUTPUT_FORMAT", "output_format"),
            ("PROGRESS_EMITTER", "progress_emitter"),
            ("FAST_MODE_ENABLED", "fast_mode_enabled"),
        ),
    )
    def test_context_reads_writes_and_deletes(
        self, monkeypatch: pytest.MonkeyPatch, module_name: str, context_name: str
    ) -> None:
        """Module access must target the current context without storing duplicate state."""
        context = AppContext()  # Isolate all state changes from other tests.
        monkeypatch.setattr(MainEntrypoint, "context", context)  # Select a fresh state owner.
        sentinel = object()  # Distinguish forwarded identity from an accidental copied value.
        setattr(MistHelper, module_name, sentinel)  # Exercise the actual module assignment method.
        assert getattr(context, context_name) is sentinel  # The context must receive the exact supplied value.
        assert getattr(MistHelper, module_name) is sentinel  # Module reads must observe that same state owner.
        assert module_name not in vars(MistHelper)  # The module must not create a second state location.
        delattr(MistHelper, module_name)  # Exercise the historical context-clear operation.
        assert getattr(context, context_name) is None  # Deletion must retain the existing absence value.

    def test_ordinary_attributes_and_missing_names(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Normal module names retain ordinary assignment, deletion, and failure behavior."""
        name = "typed_context_test_attribute"  # Use a unique name outside the context mapping.
        sentinel = object()  # A unique value proves ordinary module storage.
        monkeypatch.setattr(MistHelper, name, sentinel, raising=False)  # Register cleanup before testing deletion.
        assert vars(MistHelper)[name] is sentinel  # Unmapped values must stay on the module.
        delattr(MistHelper, name)  # Remove the ordinary module attribute through the typed method.
        with pytest.raises(AttributeError, match=name):  # Unknown reads must not create context state.
            getattr(MistHelper, name)  # Read the deleted attribute through the actual module.
        with pytest.raises(AttributeError, match=name):  # Repeated deletion must preserve the standard failure.
            delattr(MistHelper, name)  # Delete a name that no longer exists.
        setattr(MistHelper, name, sentinel)  # Let monkeypatch restore the original missing-name state.

    def test_policy_requires_session_before_client_creation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing session must fail before either destructive policy menu constructs its client."""
        monkeypatch.setattr(MainEntrypoint, "context", AppContext())  # Remove authenticated state without credentials.
        client = MagicMock(name="PolicyApi")  # Record construction without any SDK operation.
        monkeypatch.setattr(MistHelper, "PolicyApi", client)  # Keep the failure check entirely local.
        for menu_id in ("305", "306"):  # Both policy handlers use the same validated construction boundary.
            with pytest.raises(RuntimeError, match="Mist API session is not initialized"):  # Require explicit failure.
                MistHelper.menu_actions[menu_id].handler()  # Stop before confirmation, backup, or API work.
        client.assert_not_called()  # Neither menu may construct a client with an absent session.

    def test_policy_preserves_authenticated_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Policy construction must use the exact authenticated context session."""
        context = AppContext(apisession=object())  # An identity sentinel replaces the real SDK session.
        monkeypatch.setattr(MainEntrypoint, "context", context)  # Isolate authenticated state from other tests.
        client = MagicMock(name="PolicyApi")  # Avoid all SDK requests and request-controller setup.
        monkeypatch.setattr(MistHelper, "PolicyApi", client)  # Observe the construction contract only.
        result = MistHelper._build_policy_api()  # Exercise the checked success path.
        client.assert_called_once_with(context.apisession)  # Preserve the session without substitution or copying.
        assert result is client.return_value  # Return the exact client built for that session.

    def test_site_upgrade_selectors_remain_lazy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Menu construction must not resolve an organization before a selector runs."""
        monkeypatch.setattr(MainEntrypoint, "context", AppContext())  # Remove state from other menu tests.
        builder = MagicMock(name="upgrader_builder")  # Replace all organization resolution and SDK access.
        configure = MagicMock(name="configure")  # Capture callback wiring without changing any policy.
        monkeypatch.setattr(MistHelper, "_build_org_ap_upgrader", builder)  # Observe lazy construction.
        monkeypatch.setattr(MistHelper.SiteAutoUpgradeConfigurator, "execute", configure)  # Stop before dispatch.
        MistHelper.menu_actions["168"].handler()  # Assemble the actual menu arguments without running selectors.
        builder.assert_not_called()  # Organization prompts must remain deferred until a selector runs.
        callbacks = configure.call_args.kwargs  # Inspect the callbacks supplied by the actual menu handler.
        callbacks["select_msps_fn"]()  # Exercise public MSP selection only after explicit invocation.
        builder.assert_called_once_with(org_id="")  # Preserve the existing organization override.
        builder.return_value.select_msps.assert_called_once_with()  # Preserve the original selector arguments.
        msp = {"msp_id": "test-msp"}  # Use a noncredential identity record for organization selection.
        callbacks["select_orgs_fn"](msp)  # Exercise the typed callback with the original input object.
        builder.return_value.select_orgs_from_msp.assert_called_once_with(msp)  # Preserve the MSP record.


class TestOptionalSdkLoading:
    """Keep the optional SDK import boundary independent of credentials and network access."""

    def test_existing_sdk_does_not_import_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An existing SDK module must bypass the optional import operation."""
        importer = MagicMock(name="import_module")  # Observe import attempts without loading packages.
        monkeypatch.setattr(MistHelper.importlib, "import_module", importer)  # Isolate the package boundary.
        sdk = object()  # Represent a previously supplied SDK module without starting a session.
        assert MistHelper._load_mistapi_module(sdk) is sdk  # Preserve the supplied module identity.
        importer.assert_not_called()  # An existing module must avoid import side effects.

    def test_available_sdk_is_loaded_by_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing SDK handle must resolve the same package through the optional importer."""
        importer = MagicMock(name="import_module")  # Keep package discovery local and deterministic.
        monkeypatch.setattr(MistHelper.importlib, "import_module", importer)  # Replace package discovery only.
        assert MistHelper._load_mistapi_module(None) is importer.return_value  # Return the resolved package identity.
        importer.assert_called_once_with("mistapi")  # Do not change the required package name.

    def test_absent_sdk_retains_explicit_failure(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unavailable SDK must retain the absence result and its operator error."""
        importer = MagicMock(side_effect=ImportError("optional SDK unavailable"))  # Model a missing package.
        monkeypatch.setattr(MistHelper.importlib, "import_module", importer)  # Prevent any real import or request.
        assert MistHelper._load_mistapi_module(None) is None  # Preserve the existing failure signal.
        importer.assert_called_once_with("mistapi")  # Fail only at the intended SDK boundary.
        assert "Cannot import mistapi: optional SDK unavailable" in caplog.text  # Preserve the visible cause.
