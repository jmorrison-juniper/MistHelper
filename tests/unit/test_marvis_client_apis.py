"""Unit tests for Org Marvis Client API handlers (menus 211-215)."""

import MistHelper


class _Response:
    """Simple APIResponse stand-in used by handler tests."""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code


def test_validate_duration_input_accepts_valid_patterns():
    assert MistHelper._validate_duration_input("10m") is True
    assert MistHelper._validate_duration_input("2h") is True
    assert MistHelper._validate_duration_input("7d") is True
    assert MistHelper._validate_duration_input("2w") is True
    assert MistHelper._validate_duration_input("") is True


def test_validate_duration_input_rejects_invalid_patterns(capsys):
    assert MistHelper._validate_duration_input("abc") is False
    assert MistHelper._validate_duration_input("1x") is False
    assert "Invalid duration format" in capsys.readouterr().out


def test_handle_search_after_pagination_collects_rows_without_token_support(monkeypatch):
    calls = {"count": 0}

    def _search(_session, org_id, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return _Response({"results": [{"id": "r1"}, {"id": "r2"}], "search_after": "next-token"})
        return _Response({"results": []})

    monkeypatch.setitem(
        MistHelper._handle_search_after_pagination.__globals__,
        "safe_input",
        lambda *args, **kwargs: "",
    )

    rows = MistHelper._handle_search_after_pagination(_search, {"org_id": "org-1"}, page_limit=100)

    assert len(rows) == 2
    assert calls["count"] == 1


def test_export_org_marvis_client_insights_exports(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._export_org_marvis_client_insights.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    responses = iter(["client-1", "1d", "", "", ""])
    monkeypatch.setitem(
        MistHelper._export_org_marvis_client_insights.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(responses),
    )

    endpoints = {
        "insights": lambda *_args, **_kwargs: _Response([{"id": "ins-1", "status": "ok"}]),
    }
    monkeypatch.setitem(
        MistHelper._export_org_marvis_client_insights.__globals__,
        "_resolve_org_marvis_client_endpoints",
        lambda: endpoints,
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["rows"] = data
        captured["filename"] = filename
        captured["api"] = api_function_name
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper._export_org_marvis_client_insights()

    assert captured["filename"] == "OrgMarvisClientInsights.csv"
    assert captured["api"] == "getOrgMarvisClientInsights"
    assert captured["rows"][0]["org_id"] == "org-1"


def test_count_org_marvis_client_events_exports(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._count_org_marvis_client_events.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    responses = iter(["1d", "", "", "", "", ""])
    monkeypatch.setitem(
        MistHelper._count_org_marvis_client_events.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(responses),
    )

    endpoints = {
        "events_count": lambda *_args, **_kwargs: _Response({"total": 3, "type": "roam"}),
    }
    monkeypatch.setitem(
        MistHelper._count_org_marvis_client_events.__globals__,
        "_resolve_org_marvis_client_endpoints",
        lambda: endpoints,
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["filename"] = filename
        captured["api"] = api_function_name
        captured["rows"] = data
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper._count_org_marvis_client_events()

    assert captured["filename"] == "OrgMarvisClientEventsCount.csv"
    assert captured["api"] == "countOrgMarvisClientEvents"
    assert captured["rows"][0]["org_id"] == "org-1"


def test_search_org_marvis_client_events_exports(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_events.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    responses = iter(["1d", "", "", "", "", ""])
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_events.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(responses),
    )

    endpoints = {"events_search": lambda *_args, **_kwargs: _Response([])}
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_events.__globals__,
        "_resolve_org_marvis_client_endpoints",
        lambda: endpoints,
    )
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_events.__globals__,
        "_handle_search_after_pagination",
        lambda *_args, **_kwargs: [{"id": "ev-1"}, {"id": "ev-2"}],
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["filename"] = filename
        captured["api"] = api_function_name
        captured["rows"] = data
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper._search_org_marvis_client_events()

    assert captured["filename"] == "OrgMarvisClientEventsSearch.csv"
    assert captured["api"] == "searchOrgMarvisClientEvents"
    assert len(captured["rows"]) == 2


def test_count_org_marvis_client_stats_exports(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._count_org_marvis_client_stats.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    responses = iter(["1d", "", "", "", "", ""])
    monkeypatch.setitem(
        MistHelper._count_org_marvis_client_stats.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(responses),
    )

    endpoints = {
        "stats_count": lambda *_args, **_kwargs: _Response({"total": 2, "model": "ios"}),
    }
    monkeypatch.setitem(
        MistHelper._count_org_marvis_client_stats.__globals__,
        "_resolve_org_marvis_client_endpoints",
        lambda: endpoints,
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["filename"] = filename
        captured["api"] = api_function_name
        captured["rows"] = data
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper._count_org_marvis_client_stats()

    assert captured["filename"] == "OrgMarvisClientStatsCount.csv"
    assert captured["api"] == "countOrgMarvisClientsStats"


def test_search_org_marvis_client_stats_exports(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_stats.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    responses = iter(["1d", "", "", "", "", ""])
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_stats.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(responses),
    )

    endpoints = {"stats_search": lambda *_args, **_kwargs: _Response([])}
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_stats.__globals__,
        "_resolve_org_marvis_client_endpoints",
        lambda: endpoints,
    )
    monkeypatch.setitem(
        MistHelper._search_org_marvis_client_stats.__globals__,
        "_handle_search_after_pagination",
        lambda *_args, **_kwargs: [{"id": "st-1"}],
    )

    captured = {}

    def _save(data, filename, api_function_name=None):
        captured["filename"] = filename
        captured["api"] = api_function_name
        captured["rows"] = data
        return True

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _save)

    MistHelper._search_org_marvis_client_stats()

    assert captured["filename"] == "OrgMarvisClientStatsSearch.csv"
    assert captured["api"] == "searchOrgMarvisClientsStats"
    assert len(captured["rows"]) == 1


def test_search_after_prompt_degrades_safely_when_not_supported(monkeypatch, capsys):
    """When SDK search fn lacks search_after parameter, helper degrades with guidance."""
    calls = {"count": 0}

    def _search(_session, org_id, **kwargs):
        calls["count"] += 1
        return _Response({"results": [{"id": "r1"}], "search_after": "next"})

    monkeypatch.setitem(
        MistHelper._handle_search_after_pagination.__globals__,
        "safe_input",
        lambda *args, **kwargs: "token-from-operator",
    )

    rows = MistHelper._handle_search_after_pagination(_search, {"org_id": "org-1"}, page_limit=100)

    out = capsys.readouterr().out
    assert "does not accept search_after" in out
    assert len(rows) == 1
    assert calls["count"] == 1


def test_export_failure_surfaces_actionable_message(monkeypatch, tmp_path, capsys):
    """Exporter write failure should surface an actionable error message to operators."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(
        MistHelper._export_org_marvis_client_insights.__globals__,
        "get_cached_or_prompted_org_id",
        lambda: "org-1",
    )
    responses = iter(["client-1", "1d", "", "", ""])
    monkeypatch.setitem(
        MistHelper._export_org_marvis_client_insights.__globals__,
        "safe_input",
        lambda *args, **kwargs: next(responses),
    )
    endpoints = {
        "insights": lambda *_args, **_kwargs: _Response([{"id": "ins-1", "status": "ok"}]),
    }
    monkeypatch.setitem(
        MistHelper._export_org_marvis_client_insights.__globals__,
        "_resolve_org_marvis_client_endpoints",
        lambda: endpoints,
    )

    def _failing_save(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", _failing_save)

    MistHelper._export_org_marvis_client_insights()

    out = capsys.readouterr().out
    assert "Insights export failed" in out
