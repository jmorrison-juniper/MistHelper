"""Regression tests for runtime-dependent menu 91 and 195 portal answers."""

from __future__ import annotations

import builtins
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.foundation.support.utils.input_utils import InputUtils
from src.mist.resources.site.address_audit.address_corrector import AddressCorrector
from src.mist.resources.site.address_audit.models import AddressRow, AuditResult, MatchedSite
from web_portal.menu_registry import build_static_menu_actions
from web_portal.services.input_hook import InputInterceptor, web_input_context
from web_portal.services.operation import OperationExecutor


def _build_executor() -> OperationExecutor:
    """Build the real portal executor without starting a Mist operation."""
    menu_actions = build_static_menu_actions()
    for menu_number in ("91", "195"):
        menu_actions[menu_number] = replace(menu_actions[menu_number], handler=lambda: None)
    return OperationExecutor(menu_actions, None, None, None)


def test_menu_195_controls_follow_current_files_and_prompt_contexts(monkeypatch, tmp_path: Path) -> None:
    """The browser sees current file choices and independent prompt names."""
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    (data_directory / "primary.csv").write_text("serial,address\n", encoding="utf-8")
    (data_directory / "authority.tsv").write_text("serial\taddress\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUSINESS_NAME", raising=False)
    executor = _build_executor()

    try:
        parameters = executor.get_operation_parameters("195")
    finally:
        executor.shutdown(0)

    controls = {parameter["name"]: parameter for parameter in parameters["parameters"]}
    assert set(controls) == {"primary_csv", "authority_csv", "business_name", "post_table_action", "write_back"}
    assert controls["primary_csv"]["answer_context"] == "address_audit_csv_pick"
    assert controls["authority_csv"]["answer_context"] == "address_audit_business_csv_pick"
    assert controls["business_name"]["answer_context"] == "address_audit_business_name"
    assert controls["post_table_action"]["answer_context"] == "address_audit_post_table"
    assert controls["write_back"]["default"] == "n"
    assert controls["write_back"]["options"] == [{"value": "n", "label": "No (use the CLI to write corrections)"}]


def test_menu_195_single_file_omits_primary_prompt_and_honors_environment(monkeypatch, tmp_path: Path) -> None:
    """One file auto-selects as primary, and a configured business name removes its prompt."""
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    (data_directory / "primary.csv").write_text("serial,address\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUSINESS_NAME", "Northwind")
    executor = _build_executor()

    try:
        parameters = executor.get_operation_parameters("195")
    finally:
        executor.shutdown(0)

    controls = {parameter["name"] for parameter in parameters["parameters"]}
    assert controls == {"authority_csv", "post_table_action", "write_back"}


def test_menu_195_has_no_controls_when_no_file_exists(monkeypatch, tmp_path: Path) -> None:
    """No data file means no form answer can be consumed by the operation."""
    (tmp_path / "data").mkdir()
    monkeypatch.chdir(tmp_path)
    executor = _build_executor()

    try:
        parameters = executor.get_operation_parameters("195")
    finally:
        executor.shutdown(0)

    assert parameters["parameters"] == []


def test_menu_195_rejects_missing_required_context_before_start(monkeypatch, tmp_path: Path) -> None:
    """Missing required file selection fails before a worker can run."""
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    (data_directory / "primary.csv").write_text("serial,address\n", encoding="utf-8")
    (data_directory / "authority.csv").write_text("serial,address\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUSINESS_NAME", raising=False)
    executor = _build_executor()
    executor._execute_operation = lambda *args: None

    try:
        result = executor.start_operation("195", {"input_context_answers": {}})
    finally:
        executor.shutdown(0)

    assert result == {"error": "Required answer missing: address_audit_csv_pick"}


def test_menu_195_rejects_none_context_answers_before_start(monkeypatch, tmp_path: Path) -> None:
    """A null answer object cannot start an operation."""
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    (data_directory / "primary.csv").write_text("serial,address\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    executor = _build_executor()
    executor._execute_operation = lambda *args: pytest.fail("The operation must not start.")

    try:
        result = executor.start_operation("195", {"input_context_answers": None})
    finally:
        executor.shutdown(0)

    assert result == {"error": "Prompt answers must be an object"}


def test_menu_195_rejects_a_stale_file_choice_before_start(monkeypatch, tmp_path: Path) -> None:
    """A file removed after the form loads cannot reach the operation."""
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    (data_directory / "primary.csv").write_text("serial,address\n", encoding="utf-8")
    (data_directory / "authority.csv").write_text("serial,address\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUSINESS_NAME", raising=False)
    executor = _build_executor()
    executor._execute_operation = lambda *args: None

    try:
        result = executor.start_operation(
            "195",
            {
                "input_context_answers": {
                    "address_audit_csv_pick": "file:missing.csv",
                    "address_audit_business_csv_pick": "",
                    "address_audit_business_name": "",
                    "address_audit_post_table": "q",
                    "address_audit_writeback_gate": "n",
                }
            },
        )
    finally:
        executor.shutdown(0)

    assert result == {"error": "Invalid answer for address_audit_csv_pick"}


def test_menu_195_defaults_an_omitted_writeback_answer_to_no(monkeypatch, tmp_path: Path) -> None:
    """An omitted conditional write-back choice is normalized to the safe default."""
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    (data_directory / "primary.csv").write_text("serial,address\n", encoding="utf-8")
    (data_directory / "authority.csv").write_text("serial,address\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUSINESS_NAME", raising=False)
    executor = _build_executor()

    try:
        normalized, error = executor._prepare_context_answers(
            "195",
            {
                "input_context_answers": {
                    "address_audit_csv_pick": "file:primary.csv",
                    "address_audit_business_csv_pick": "",
                    "address_audit_business_name": "",
                    "address_audit_post_table": "q",
                }
            },
        )
    finally:
        executor.shutdown(0)

    assert error is None
    assert normalized["address_audit_writeback_gate"] == "n"


@pytest.mark.parametrize("answer", ["y", "yes", "Y", "YES", " y "])
def test_menu_195_rejects_affirmative_writeback_before_start(monkeypatch, tmp_path: Path, answer: str) -> None:
    """A stale or modified portal form cannot authorize a site write."""
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    (data_directory / "primary.csv").write_text("serial,address\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    executor = _build_executor()
    submit = Mock(side_effect=AssertionError("An affirmative request must not start a worker."))
    monkeypatch.setattr(executor._pool, "submit", submit)

    try:
        result = executor.start_operation("195", {"input_context_answers": {"address_audit_writeback_gate": answer}})
    finally:
        executor.shutdown(0)

    assert result == {"error": "Invalid answer for address_audit_writeback_gate"}
    assert executor._runs == {}
    submit.assert_not_called()


def test_unconfirmed_site_write_fails_even_if_portal_validation_is_bypassed(monkeypatch, tmp_path: Path) -> None:
    """The real per-site prompt aborts a worker without a write or a success result."""
    monkeypatch.chdir(tmp_path)
    corrector = AddressCorrector(None)
    push = Mock(side_effect=AssertionError("A site write requires per-site confirmation."))
    monkeypatch.setattr(corrector, "_push", push)
    result = AuditResult(
        address_row=AddressRow("1", "SSR130", "100 Main St Suite 5", "Town", "FL", "33000"),
        matched_site=MatchedSite(site_id="s1", site_name="Store 181", mist_address={"address": "100 Main St"}),
        issue_type="MISSING_SUITE",
        suggested_address="100 Main St Suite 5",
    )
    executor = _build_executor()
    executor._menu_actions["195"] = replace(
        executor._menu_actions["195"], handler=lambda: corrector.review_and_apply([result])
    )
    run = executor._create_run("195")

    try:
        executor._execute_operation(run, {"input_context_answers": {"address_audit_writeback_gate": "y"}})
    finally:
        executor.shutdown(0)

    assert run["status"] == "failed"
    assert run["error_message"] == "Operation requires interactive input (not available in web portal)"
    assert not run.get("completion_message")
    push.assert_not_called()


def test_context_answers_do_not_shift_when_a_prompt_is_skipped(monkeypatch) -> None:
    """An answer for a later prompt stays tied to its named input context."""
    monkeypatch.setattr(builtins, "input", InputInterceptor._patched_input)
    with web_input_context(
        [],
        context_answers={
            "address_audit_business_csv_pick": "",
            "address_audit_business_name": "Northwind",
            "address_audit_post_table": "q",
        },
    ):
        authority_file = InputUtils.safe_input("Authority file: ", context="address_audit_business_csv_pick")
        business_name = InputUtils.safe_input("Business name: ", context="address_audit_business_name")
        post_table = InputUtils.safe_input("Save or quit: ", context="address_audit_post_table")

    assert authority_file == ""
    assert business_name == "Northwind"
    assert post_table == "q"


def test_none_context_map_preserves_cli_input(monkeypatch) -> None:
    """An absent context map keeps the existing positional input path."""
    monkeypatch.setattr(builtins, "input", lambda prompt: "cli answer")

    with web_input_context([], context_answers=None):
        answer = InputUtils.safe_input("Prompt: ", context="manufacturer_report_selection")

    assert answer == "cli answer"


def test_context_only_answers_do_not_consume_another_queue_on_missing_context(monkeypatch) -> None:
    """A missing named answer fails without reading or clearing a positional queue."""
    monkeypatch.setattr(builtins, "input", InputInterceptor._patched_input)
    InputInterceptor.set_queue(["another operation answer"])

    try:
        with pytest.raises(EOFError, match="No browser answer supplied"):
            with web_input_context([], context_answers={"known_prompt": "browser answer"}):
                InputUtils.safe_input("Prompt: ", context="unknown_prompt")

        answer = InputInterceptor._patched_input("Positional prompt: ")
    finally:
        InputInterceptor.clear_queue()

    assert answer == "another operation answer"
