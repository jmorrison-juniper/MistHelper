"""Unit tests for Site Marvis Config Action helpers and US1 handlers (menus 216-217)."""

import MistHelper


class _Response:
    """Simple response stand-in with data/status_code attributes."""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code


def test_validate_site_marvis_time_window_rejects_inverted_bounds(capsys):
    assert MistHelper._validate_site_marvis_time_window("200", "100") is False
    assert "Invalid time window" in capsys.readouterr().out


def test_validate_site_marvis_action_id_rejects_blank(capsys):
    assert MistHelper._validate_site_marvis_action_id("  ") is False
    assert "Action ID is required" in capsys.readouterr().out


def test_validate_site_marvis_feedback_type_allowlist(capsys):
    assert MistHelper._validate_site_marvis_feedback_type("helpful") is True
    assert MistHelper._validate_site_marvis_feedback_type("bad-value") is False
    assert "Invalid feedback type" in capsys.readouterr().out


def test_handle_site_marvis_config_pagination_collects_rows(monkeypatch):
    responses = iter(["", ""])
    monkeypatch.setitem(
        MistHelper._handle_site_marvis_config_pagination.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(responses),
    )

    def _search(_session, _site_id, **kwargs):
        if "search_after" not in kwargs:
            return _Response({"results": [{"id": "a1"}], "search_after": "tok1"})
        return _Response({"results": [{"id": "a2"}]})

    def _sig(_fn):
        class _S:
            parameters = {"search_after": None}

        return _S()

    monkeypatch.setitem(
        MistHelper._handle_site_marvis_config_pagination.__globals__,
        "inspect",
        type("_I", (), {"signature": staticmethod(_sig)}),
    )

    rows = MistHelper._handle_site_marvis_config_pagination(_search, "site-1", {}, page_limit=100)

    assert len(rows) == 2


def test_count_site_marvis_config_actions_exports(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._count_site_marvis_config_actions.__globals__,
        "_prompt_site_marvis_scope_input",
        lambda *args, **kwargs: {
            "org_id": "org-1",
            "site_id": "site-1",
            "duration": "1d",
            "start": "",
            "end": "",
            "filters": {"distinct": "type"},
        },
    )
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.marvis_configs,
        "countSiteMarvisConfigActions",
        lambda *_args, **_kwargs: _Response({"count": 3, "distinct": "type"}),
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["rows"] = data
        captured["filename"] = filename
        captured["api"] = api_function_name
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper._count_site_marvis_config_actions()

    assert captured["filename"] == "SiteMarvisConfigActionsCount.csv"
    assert captured["api"] == "countSiteMarvisConfigActions"
    assert captured["rows"][0]["site_id"] == "site-1"
    assert "filters_hash_duration" in captured["rows"][0]


def test_search_site_marvis_config_actions_exports(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._search_site_marvis_config_actions.__globals__,
        "_prompt_site_marvis_scope_input",
        lambda *args, **kwargs: {
            "org_id": "org-1",
            "site_id": "site-1",
            "duration": "1d",
            "start": "",
            "end": "",
            "filters": {},
        },
    )
    monkeypatch.setitem(
        MistHelper._search_site_marvis_config_actions.__globals__,
        "_handle_site_marvis_config_pagination",
        lambda *_args, **_kwargs: [{"id": "act-1", "status": "open"}, {"id": "act-2", "status": "done"}],
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["rows"] = data
        captured["filename"] = filename
        captured["api"] = api_function_name
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper._search_site_marvis_config_actions()

    assert captured["filename"] == "SiteMarvisConfigActionsSearch.csv"
    assert captured["api"] == "searchSiteMarvisConfigActions"
    assert len(captured["rows"]) == 2
    assert captured["rows"][0]["site_id"] == "site-1"
