"""Tests for the CountExporter workflow paths that reach the Mist API.

Why:
    ``tests/unit/export/test_count_exporter.py`` covers the operation table and
    the selection prompt. It does not cover ``_run``, the three scope entry
    points, or the MSP prompt. Those lines hold the API call, the error
    handler, and the abort guards that keep the menu alive. This module covers
    them. Every Mist call is mocked, so no test reaches the live cloud.
"""

from __future__ import annotations

import importlib
from typing import Any
from unittest.mock import MagicMock, patch

import mistapi
import pytest

from src.export.count_exporter import _MSP_OPS, _ORG_OPS, _SITE_OPS, CountExporter, _CountOp
from src.utils.input_utils import InputUtils


@pytest.fixture
def fake_mh() -> Any:
    """Return a MistHelper stand-in with every collaborator the exporter reads.

    Why:
        The exporter resolves ``apisession``, ``InputUtils``, ``ConfigUtils``,
        ``SiteDeviceExporter``, and ``DataExporter`` through a lazy
        ``importlib.import_module("MistHelper")`` call. One stub covers all of
        them and records what the exporter wrote.
    """
    module = MagicMock()  # WHY: a MagicMock auto-creates each attribute the exporter reads.
    module.apisession = MagicMock()  # WHY: the SDK call receives this as its first argument.
    return module  # WHY: each test patches import_module to return this object.


class TestRunErrorHandling:
    """Cover ``_run``, which owns the SDK call and its error handler."""

    def test_run_aborts_when_the_sdk_operation_is_missing(self, fake_mh: Any) -> None:
        """An unresolvable operation must abort before any API call."""
        # WHY: a module path that does not exist forces _resolve to return None.
        missing = _CountOp("countNothing", "mistapi.api.v1.not_a_real_module")
        with patch.object(importlib, "import_module", return_value=fake_mh):
            CountExporter._run(missing, "org-1", "org-1")  # WHY: exercise the guard branch.
        # WHY: the guard must return before the exporter writes anything.
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_run_passes_the_session_and_identifier_to_the_sdk(self, fake_mh: Any) -> None:
        """Every count operation takes the session and one identifier positionally."""
        sdk_callable = MagicMock(return_value={"result": []})  # WHY: stand in for the SDK function.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_resolve", return_value=sdk_callable),
            patch.object(mistapi, "get_all", return_value=[{"count": 2}]),
        ):
            CountExporter._run(_ORG_OPS[0], "org-1", "Org One")  # WHY: run the happy path.
        # WHY: the contract is exactly two positional arguments, session first.
        sdk_callable.assert_called_once_with(fake_mh.apisession, "org-1")

    def test_run_builds_a_filename_from_the_operation_and_label(self, fake_mh: Any) -> None:
        """A label with a space must not produce a filename with a space."""
        sdk_callable = MagicMock(return_value={"result": []})  # WHY: stand in for the SDK function.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_resolve", return_value=sdk_callable),
            patch.object(mistapi, "get_all", return_value=[{"count": 2}]),
        ):
            CountExporter._run(_ORG_OPS[0], "org-1", "Head Office")  # WHY: label carries a space.
        args, _ = fake_mh.DataExporter.write_with_format_selection.call_args  # WHY: read the filename.
        # WHY: the exporter replaces each space so the path stays portable.
        assert args[1] == f"{_ORG_OPS[0].operation}_Head_Office.csv"

    def test_run_swallows_an_sdk_error_so_the_menu_survives(self, fake_mh: Any, caplog: Any) -> None:
        """A network or SDK failure must be logged, not raised into the menu loop."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        # WHY: raise from the SDK callable to drive the except branch.
        sdk_callable = MagicMock(side_effect=RuntimeError("connection reset"))
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_resolve", return_value=sdk_callable),
        ):
            CountExporter._run(_ORG_OPS[0], "org-1", "Org One")  # WHY: must not raise.
        # WHY: the operator needs the cause in the log to triage the failure.
        assert "connection reset" in caplog.text

    def test_run_swallows_a_paging_error(self, fake_mh: Any, caplog: Any) -> None:
        """A failure inside ``get_all`` must reach the same handler as a call failure."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        sdk_callable = MagicMock(return_value={"result": []})  # WHY: the first call succeeds.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_resolve", return_value=sdk_callable),
            # WHY: paging is a second network hop, so it fails independently of the call.
            patch.object(mistapi, "get_all", side_effect=ValueError("bad page")),
        ):
            CountExporter._run(_ORG_OPS[0], "org-1", "Org One")  # WHY: must not raise.
        # WHY: the paging failure must be attributed to the same operation.
        assert "bad page" in caplog.text


class TestOrgCounts:
    """Cover ``org_counts``, the menu 235 entry point."""

    def test_org_counts_returns_when_the_operator_declines_the_operation(self, fake_mh: Any) -> None:
        """A declined operation must abort before the org prompt runs."""
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=None),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.org_counts()  # WHY: drive the first guard branch.
        run_spy.assert_not_called()  # WHY: no operation means no API call.
        # WHY: the org resolver must not run once the operator has declined.
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.assert_not_called()

    def test_org_counts_returns_when_no_org_resolves(self, fake_mh: Any) -> None:
        """An empty org identifier must abort before the API call."""
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = ""  # WHY: empty means declined.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=_ORG_OPS[0]),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.org_counts()  # WHY: drive the empty-org guard.
        run_spy.assert_not_called()  # WHY: the API path needs a real identifier.

    def test_org_counts_runs_the_chosen_operation(self, fake_mh: Any) -> None:
        """A resolved org must reach ``_run`` as both the identifier and the label."""
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-42"  # WHY: resolved org.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=_ORG_OPS[0]),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.org_counts()  # WHY: drive the happy path.
        # WHY: the org path has no friendly name, so the identifier doubles as the label.
        run_spy.assert_called_once_with(_ORG_OPS[0], "org-42", "org-42")


class TestSiteCounts:
    """Cover ``site_counts``, the menu 236 entry point."""

    def test_site_counts_returns_when_the_operator_declines_the_operation(self, fake_mh: Any) -> None:
        """A declined operation must abort before the shared site resolver runs."""
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=None),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.site_counts()  # WHY: drive the first guard branch.
        run_spy.assert_not_called()  # WHY: no operation means no API call.
        # WHY: the site resolver prompts the operator, so it must stay unused here.
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.assert_not_called()

    def test_site_counts_returns_when_the_site_does_not_resolve(self, fake_mh: Any) -> None:
        """A ``None`` from the shared site resolver must abort before the API call."""
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = None  # WHY: declined site.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=_SITE_OPS[0]),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.site_counts()  # WHY: drive the unresolved-site guard.
        run_spy.assert_not_called()  # WHY: the API path needs a real site identifier.

    def test_site_counts_passes_the_site_name_as_the_label(self, fake_mh: Any) -> None:
        """The site name becomes the label, which shapes the output filename."""
        # WHY: the shared resolver returns the identifier and the friendly name together.
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-7", "Branch Two")
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=_SITE_OPS[0]),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.site_counts()  # WHY: drive the happy path.
        # WHY: the site path has a friendly name, so the label differs from the identifier.
        run_spy.assert_called_once_with(_SITE_OPS[0], "site-7", "Branch Two")


class TestMspCounts:
    """Cover ``msp_counts``, the menu 237 entry point.

    The identifier prompt now lives in ``InputUtils.prompt_msp_id``, because
    menu 238 asks for the same value. ``tests/unit/utils/test_input_utils_wave9.py``
    covers the prompt itself, so these tests patch it and cover the routing only.
    """

    def test_msp_counts_returns_when_the_operator_declines_the_operation(self, fake_mh: Any) -> None:
        """A declined operation must abort before the identifier prompt runs."""
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=None),
            patch.object(InputUtils, "prompt_msp_id") as prompt_spy,
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.msp_counts()  # WHY: drive the first guard branch.
        prompt_spy.assert_not_called()  # WHY: no operation means no prompt.
        run_spy.assert_not_called()  # WHY: no operation means no API call.

    def test_msp_counts_returns_when_the_identifier_prompt_aborts(self, fake_mh: Any) -> None:
        """A ``None`` identifier must abort before the API call."""
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=_MSP_OPS[0]),
            patch.object(InputUtils, "prompt_msp_id", return_value=None),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.msp_counts()  # WHY: drive the declined-identifier guard.
        run_spy.assert_not_called()  # WHY: the API path needs a real identifier.

    def test_msp_counts_runs_the_chosen_operation(self, fake_mh: Any) -> None:
        """A supplied identifier must reach ``_run`` as both the identifier and the label."""
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(CountExporter, "_choose", return_value=_MSP_OPS[0]),
            patch.object(InputUtils, "prompt_msp_id", return_value="msp-9"),
            patch.object(CountExporter, "_run") as run_spy,
        ):
            CountExporter.msp_counts()  # WHY: drive the happy path.
        # WHY: the MSP path has no friendly name, so the identifier doubles as the label.
        run_spy.assert_called_once_with(_MSP_OPS[0], "msp-9", "msp-9")
