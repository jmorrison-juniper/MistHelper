"""Wave 8 P2 coverage — MspOrgSelector (post-login MSP + org picker)."""

from __future__ import annotations

from types import SimpleNamespace  # WHY: lightweight stand-in for mistapi/SDK responses
from typing import Any  # WHY: matches Selector's state bag typing
from unittest.mock import MagicMock  # WHY: MagicMock(spec=Callable) is mandatory per project standard

import pytest  # WHY: capsys/monkeypatch fixtures for output + state assertions

from src.auth.interactive.msp_org_selector import MspOrgSelector  # WHY: SUT under test


class _EofInput:
    """Callable that raises SystemExit on invocation (safe_input EOF contract)."""

    def __call__(self, *_args: object, **_kwargs: object) -> str:  # WHY: matches Callable[..., str]
        raise SystemExit(0)  # WHY: simulate ctrl-D via the SystemExit contract used by safe_input


def _scripted_input(answers: list[str]) -> MagicMock:
    """Return a MagicMock(spec=callable) that yields each scripted answer in order."""
    mock = MagicMock(spec=lambda prompt, context: prompt)  # WHY: spec=callable to satisfy strict style
    mock.side_effect = answers  # WHY: pop scripted answers on each safe_input call
    return mock  # WHY: caller passes into the selector


def _make_selector(
    state: dict[str, Any] | None = None,
    answers: list[str] | None = None,
    fallback: MagicMock | None = None,
) -> tuple[MspOrgSelector, MagicMock]:
    """Build a selector wired to a fallback mock; return (selector, fallback)."""
    fallback = fallback or MagicMock(spec=lambda: None)  # WHY: default select-org-fallback stub
    safe_input = _scripted_input(answers or [])  # WHY: scripted or empty answer queue
    resolved_state = {} if state is None else state  # WHY: preserve caller's dict ref so cache writes are observable
    selector = MspOrgSelector(resolved_state, safe_input, fallback)  # WHY: construct SUT with shared state ref
    return selector, fallback  # WHY: caller asserts fallback interactions


def test_select_no_msp_delegates_to_fallback() -> None:
    """When no MSP grants are present, selector delegates straight to the direct-org fallback."""
    selector, fallback = _make_selector(state={"msp_privileges": []})  # WHY: empty grants
    selector.select()  # WHY: exercise the empty-msp branch
    fallback.assert_called_once_with()  # WHY: fallback invoked, no other side effects


def test_select_single_msp_autopicks_and_selects_org(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """One MSP auto-picks; then selector prompts for an org and records the pick."""
    apisession = MagicMock()  # WHY: sentinel session passed through to SDK
    mistapi_stub = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                msps=SimpleNamespace(
                    orgs=SimpleNamespace(
                        listMspOrgs=MagicMock(  # WHY: SDK entry: returns SDK-like response
                            return_value=SimpleNamespace(
                                data=[
                                    {"id": "org-A", "name": "Alpha"},  # WHY: two orgs to exercise sort
                                    {"id": "org-B", "name": "beta"},
                                ]
                            )
                        )
                    )
                )
            )
        )
    )
    state: dict[str, Any] = {
        "msp_privileges": [{"msp_id": "m1", "msp_name": "MSP One", "role": "admin"}],  # WHY: single MSP
        "apisession": apisession,  # WHY: required by _select_org_under_msp
        "mistapi": mistapi_stub,  # WHY: avoids the fallback import path
    }
    selector, fallback = _make_selector(state=state, answers=["1"])  # WHY: pick org #1 in the picker
    selector.select()  # WHY: run full workflow
    fallback.assert_not_called()  # WHY: single-MSP path never uses the fallback
    assert state["selected_msp"]["msp_id"] == "m1"  # WHY: MSP recorded
    assert state["org_id"] == "org-A"  # WHY: sorted-first org selected via "1"
    assert "Selected organization: Alpha" in capsys.readouterr().out  # WHY: user confirmation printed


def test_prompt_msp_blank_input_skips() -> None:
    """Blank MSP prompt input skips the MSP selection and defers to fallback."""
    state = {
        "msp_privileges": [
            {"msp_id": "m1", "msp_name": "MSP One", "role": "admin"},
            {"msp_id": "m2", "msp_name": "MSP Two", "role": "admin"},
        ]
    }
    selector, fallback = _make_selector(state=state, answers=[""])  # WHY: blank => skip
    selector.select()  # WHY: exercise multi-MSP + blank branch
    fallback.assert_called_once_with()  # WHY: fallback invoked after skip


def test_prompt_msp_invalid_string_falls_back() -> None:
    """Non-numeric input triggers the invalid-selection branch and defers to fallback."""
    state = {
        "msp_privileges": [
            {"msp_id": "m1", "msp_name": "MSP One", "role": "admin"},
            {"msp_id": "m2", "msp_name": "MSP Two", "role": "admin"},
        ]
    }
    selector, fallback = _make_selector(state=state, answers=["notanumber"])  # WHY: ValueError branch
    selector.select()  # WHY: exercise invalid-input branch
    fallback.assert_called_once_with()  # WHY: fallback triggered


def test_prompt_msp_out_of_range_falls_back() -> None:
    """Out-of-range MSP index falls back to direct org select."""
    state = {
        "msp_privileges": [
            {"msp_id": "m1", "msp_name": "MSP One", "role": "admin"},
            {"msp_id": "m2", "msp_name": "MSP Two", "role": "admin"},
        ]
    }
    selector, fallback = _make_selector(state=state, answers=["99"])  # WHY: out-of-range index
    selector.select()  # WHY: exercise range-check branch
    fallback.assert_called_once_with()  # WHY: fallback triggered


def test_prompt_msp_valueerror_from_safe_input_falls_back() -> None:
    """A safe_input ValueError falls into the legacy skip path."""

    def _raise_value_error(*_args: object, **_kwargs: object) -> str:  # WHY: injected safe_input impl
        raise ValueError("bad")  # WHY: match the ValueError branch of _prompt_msp

    state = {
        "msp_privileges": [
            {"msp_id": "m1", "msp_name": "MSP One", "role": "admin"},
            {"msp_id": "m2", "msp_name": "MSP Two", "role": "admin"},
        ]
    }
    fallback = MagicMock(spec=lambda: None)  # WHY: fallback should fire after invalid path
    selector = MspOrgSelector(state, _raise_value_error, fallback)  # WHY: build SUT with raising input
    selector.select()  # WHY: exercise the ValueError branch of _prompt_msp
    fallback.assert_called_once_with()  # WHY: fallback triggered by exception handler


def test_msp_org_selector_missing_apisession(capsys: pytest.CaptureFixture[str]) -> None:
    """Missing apisession in state prints an error and returns without selecting an org."""
    state = {
        "msp_privileges": [{"msp_id": "m1", "msp_name": "MSP One", "role": "admin"}],  # WHY: single MSP
    }  # WHY: apisession intentionally missing
    selector, fallback = _make_selector(state=state)  # WHY: no scripted input needed; fallback not used
    selector.select()  # WHY: run and hit the missing-session guard
    assert "API session not initialized" in capsys.readouterr().out  # WHY: legacy error preserved
    assert "org_id" not in state  # WHY: no org selection performed


def test_msp_org_selector_fetch_exception(capsys: pytest.CaptureFixture[str]) -> None:
    """Exception during listMspOrgs is caught and printed; no org is selected."""
    apisession = MagicMock()  # WHY: passed through to the SDK
    mistapi_stub = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                msps=SimpleNamespace(
                    orgs=SimpleNamespace(
                        listMspOrgs=MagicMock(side_effect=RuntimeError("kaboom"))  # WHY: forced failure
                    )
                )
            )
        )
    )
    state: dict[str, Any] = {
        "msp_privileges": [{"msp_id": "m1", "msp_name": "MSP One", "role": "admin"}],
        "apisession": apisession,
        "mistapi": mistapi_stub,
    }
    selector, _ = _make_selector(state=state)  # WHY: exception path needs no scripted answer
    selector.select()  # WHY: run the failing SDK call
    assert "Error fetching MSP organizations" in capsys.readouterr().out  # WHY: legacy error message
    assert "org_id" not in state  # WHY: no selection recorded


def test_fetch_msp_orgs_invalid_response(capsys: pytest.CaptureFixture[str]) -> None:
    """Response without .data returns None and prints the legacy error message."""
    mistapi_stub = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                msps=SimpleNamespace(
                    orgs=SimpleNamespace(listMspOrgs=MagicMock(return_value=None))  # WHY: falsy response triggers guard
                )
            )
        )
    )
    state: dict[str, Any] = {"mistapi": mistapi_stub}  # WHY: SDK stub is enough for this path
    selector, _ = _make_selector(state=state)  # WHY: no user input needed
    result = selector._fetch_msp_orgs(MagicMock(), "m1")  # WHY: direct method to isolate branch
    assert result is None  # WHY: falsy-response guard returns None
    assert "Failed to retrieve MSP organizations" in capsys.readouterr().out  # WHY: legacy warning


def test_fetch_msp_orgs_empty_data_returns_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty MSP org list prints the 'no organizations' message and returns []."""
    mistapi_stub = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                msps=SimpleNamespace(
                    orgs=SimpleNamespace(
                        listMspOrgs=MagicMock(return_value=SimpleNamespace(data=[]))  # WHY: empty list
                    )
                )
            )
        )
    )
    state: dict[str, Any] = {"mistapi": mistapi_stub}  # WHY: minimal state
    selector, _ = _make_selector(state=state)  # WHY: no input needed
    result = selector._fetch_msp_orgs(MagicMock(), "m1")  # WHY: exercise empty-list branch
    assert result == []  # WHY: empty branch returns []
    assert "No organizations found under this MSP" in capsys.readouterr().out  # WHY: legacy message


def test_fetch_msp_orgs_single_org_normalizes_to_list() -> None:
    """A single-dict response is normalized to a list for downstream pagination."""
    mistapi_stub = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                msps=SimpleNamespace(
                    orgs=SimpleNamespace(
                        listMspOrgs=MagicMock(  # WHY: dict-shaped .data forces normalization branch
                            return_value=SimpleNamespace(data={"id": "org-1", "name": "Solo"})
                        )
                    )
                )
            )
        )
    )
    state: dict[str, Any] = {"mistapi": mistapi_stub}  # WHY: minimal state
    selector, _ = _make_selector(state=state)  # WHY: no input needed
    result = selector._fetch_msp_orgs(MagicMock(), "m1")  # WHY: exercise dict-normalization branch
    assert result == [{"id": "org-1", "name": "Solo"}]  # WHY: dict wrapped into list


def test_resolve_mistapi_fallback_import() -> None:
    """When mistapi is absent from state, the fallback import populates state and returns it."""
    state: dict[str, Any] = {}  # WHY: empty state forces the fallback import branch
    selector, _ = _make_selector(state=state)  # WHY: fallback callback unused here
    module = selector._resolve_mistapi()  # WHY: trigger the deferred import
    assert module is not None  # WHY: mistapi module resolved
    assert state["mistapi"] is module  # WHY: cached in state for later reuse


def test_paginated_pick_quit_shortcut(capsys: pytest.CaptureFixture[str]) -> None:
    """Entering 'q' in the org picker returns None and prints the skip message."""
    orgs = [{"id": "org-1", "name": "Alpha"}]  # WHY: any non-empty org list satisfies the picker
    selector, _ = _make_selector(answers=["q"])  # WHY: scripted 'q' triggers quit path
    result = selector._paginated_pick(orgs)  # WHY: exercise the quit branch directly
    assert result is None  # WHY: quit returns None
    assert "Skipping org selection" in capsys.readouterr().out  # WHY: legacy skip message printed


def test_paginated_pick_eof_returns_none() -> None:
    """EOF (SystemExit) from safe_input is treated as a silent skip."""
    orgs = [{"id": "org-1", "name": "Alpha"}]  # WHY: non-empty list to enter the loop
    fallback = MagicMock(spec=lambda: None)  # WHY: fallback shouldn't fire from this method
    selector = MspOrgSelector({}, _EofInput(), fallback)  # WHY: EOF input callable
    result = selector._paginated_pick(orgs)  # WHY: exercise EOF branch
    assert result is None  # WHY: EOF returns None silently


def test_paginated_pick_invalid_then_valid(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-numeric input reprompts; a valid numeric selection returns the picked org."""
    orgs = [
        {"id": "org-A", "name": "Alpha"},
        {"id": "org-B", "name": "Beta"},
    ]  # WHY: two orgs so index 2 is valid
    selector, _ = _make_selector(answers=["not-a-number", "2"])  # WHY: first invalid, then valid
    result = selector._paginated_pick(orgs)  # WHY: exercise the invalid+retry branches
    assert result == orgs[1]  # WHY: index "2" maps to orgs[1]
    assert "Invalid input" in capsys.readouterr().out  # WHY: legacy invalid-input message printed


def test_paginated_pick_out_of_range_then_valid(capsys: pytest.CaptureFixture[str]) -> None:
    """Out-of-range index reprompts; the next valid index returns the picked org."""
    orgs = [{"id": "org-A", "name": "Alpha"}]  # WHY: single org so "5" is out of range
    selector, _ = _make_selector(answers=["5", "1"])  # WHY: out-of-range then valid
    result = selector._paginated_pick(orgs)  # WHY: exercise the range-guard branch
    assert result == orgs[0]  # WHY: index "1" maps to orgs[0]
    assert "Invalid number" in capsys.readouterr().out  # WHY: legacy range-error message printed


def test_interpret_choice_navigation() -> None:
    """'n' and 'p' navigation return the incremented/decremented page index."""
    orgs = [{"id": "o", "name": "n"}]  # WHY: any org list; navigation only cares about page count
    action, next_page, picked = MspOrgSelector._interpret_choice("n", 0, 3, orgs)  # WHY: 'n' with room
    assert (action, next_page, picked) == ("nav", 1, None)  # WHY: paged forward
    action, next_page, picked = MspOrgSelector._interpret_choice("p", 2, 3, orgs)  # WHY: 'p' with room
    assert (action, next_page, picked) == ("nav", 1, None)  # WHY: paged backward


def test_render_msp_menu_prints_all_msps(capsys: pytest.CaptureFixture[str]) -> None:
    """_render_msp_menu prints one line per MSP with role annotation."""
    MspOrgSelector._render_msp_menu(
        [
            {"msp_name": "MSP One", "role": "admin"},  # WHY: full-shape row
            {},  # WHY: missing fields exercises the fallback labels
        ]
    )  # WHY: static method call — no instance state required
    out = capsys.readouterr().out  # WHY: capture printed menu
    assert "MSP One" in out  # WHY: named MSP surfaced
    assert "Unknown" in out  # WHY: fallback name label used for the empty dict
    assert "unknown" in out  # WHY: fallback role label used for the empty dict


def test_render_page_shows_multi_page_hint(capsys: pytest.CaptureFixture[str]) -> None:
    """When total_pages > 1 the multi-page hint is printed."""
    selector, _ = _make_selector()  # WHY: build a bare selector to reach the instance method
    selector._render_page([{"id": "org-A", "name": "A"}], 0, 2)  # WHY: total_pages=2 triggers hint
    assert "Page 1/2" in capsys.readouterr().out  # WHY: multi-page hint surfaced
