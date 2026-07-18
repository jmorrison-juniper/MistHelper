"""Unit tests for src.export.const_definitions_exporter.ConstDefinitionsExporter.

Tranche 14 of initiative #878: un-omit `const_definitions_exporter.py` and drive
it to 100% line coverage.

Why:
    ConstDefinitionsExporter dynamically discovers all const endpoints in the
    ``mistapi.api.v1.const`` package, dispatches per-endpoint API calls with
    special handling for gateway models, country states, and AP channels, and
    writes freshness-checked CSVs via a lazily-loaded ``MistHelper`` module. All
    filesystem, network, pkgutil, and importlib interactions are mocked so tests
    exercise pure logic without touching real IO or the real mistapi library.
"""

from __future__ import annotations

import inspect
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from src.dataclasses.endpoint_config import EndpointConfig
from src.export.const_definitions_exporter import ConstDefinitionsExporter


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake ``MistHelper`` module so lazy importlib lookups resolve here.

    Why:
        ConstDefinitionsExporter reaches ``DataExporter`` and
        ``DataProcessingUtils`` via ``importlib.import_module("MistHelper")`` at
        call time. Registering a synthetic module in ``sys.modules`` lets each
        test verify write-side behavior without depending on real MistHelper.
    """
    module = types.ModuleType("MistHelper")
    module.DataExporter = MagicMock()
    module.DataProcessingUtils = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", module)
    return module


@pytest.fixture
def exporter():
    """Return a ConstDefinitionsExporter with a MagicMock session."""
    return ConstDefinitionsExporter(api_session=MagicMock())


def _endpoint_config(**overrides) -> EndpointConfig:
    """Build an EndpointConfig with sensible defaults; per-test overrides."""
    defaults = {
        "endpoint_name": "test_endpoint",
        "module": MagicMock(),
        "function_name": "listStuff",
        "filename": "ConstTestEndpoint.csv",
        "description": "Test Endpoint Definitions",
        "modname": "mistapi.api.v1.const.test_endpoint",
        "special_handling": None,
    }
    defaults.update(overrides)
    return EndpointConfig(**defaults)


class TestInit:
    def test_initializes_counters_and_state(self):
        session = MagicMock()
        exp = ConstDefinitionsExporter(session)
        assert exp.api_session is session
        assert exp.discovered_endpoints == {}
        assert exp.endpoints_processed == 0
        assert exp.endpoints_skipped_fresh == 0
        assert exp.endpoints_updated == 0
        assert exp.endpoints_failed == 0


class TestExportAll:
    def test_no_endpoints_discovered_returns_early(self, exporter, capsys):
        with patch.object(exporter, "_discover_endpoints"):
            exporter.discovered_endpoints = {}
            exporter.export_all()
        assert "No const endpoints discovered" in capsys.readouterr().out

    def test_processes_and_summarizes_when_endpoints_found(self, exporter):
        exporter.discovered_endpoints = {"foo": _endpoint_config()}
        with (
            patch.object(exporter, "_discover_endpoints"),
            patch.object(exporter, "_process_all_endpoints") as proc,
            patch.object(exporter, "_print_summary") as summary,
        ):
            exporter.export_all()
        proc.assert_called_once()
        summary.assert_called_once()

    def test_catches_exception_from_discovery(self, exporter, capsys):
        with patch.object(exporter, "_discover_endpoints", side_effect=RuntimeError("boom")):
            exporter.export_all()
        assert "Critical error" in capsys.readouterr().out


class TestDiscoverEndpoints:
    def test_iterates_modules_and_skips_subpackages(self, exporter):
        fake_pkg = types.ModuleType("mistapi.api.v1.const")
        fake_pkg.__path__ = ["/fake/path"]
        fake_pkg.__name__ = "mistapi.api.v1.const"
        fake_modules = [
            types.SimpleNamespace(name="mistapi.api.v1.const.foo", ispkg=False),
            types.SimpleNamespace(name="mistapi.api.v1.const.sub", ispkg=True),
        ]
        with (
            patch.dict(sys.modules, {"mistapi.api.v1.const": fake_pkg}),
            patch("pkgutil.iter_modules", return_value=iter(fake_modules)),
            patch.object(exporter, "_inspect_module") as inspect_mod,
        ):
            exporter._discover_endpoints()
        inspect_mod.assert_called_once_with("mistapi.api.v1.const.foo")


class TestInspectModule:
    def test_skips_private_module(self, exporter):
        with patch("importlib.import_module") as imp:
            exporter._inspect_module("mistapi.api.v1.const._private")
        imp.assert_not_called()

    def test_delegates_to_inspect_module_functions(self, exporter):
        fake_mod = MagicMock()
        with (
            patch("importlib.import_module", return_value=fake_mod),
            patch.object(exporter, "_inspect_module_functions") as insp,
        ):
            exporter._inspect_module("mistapi.api.v1.const.foo")
        insp.assert_called_once_with(fake_mod, "foo", "mistapi.api.v1.const.foo")

    def test_handles_import_error(self, exporter, capsys):
        with patch("importlib.import_module", side_effect=ImportError("nope")):
            exporter._inspect_module("mistapi.api.v1.const.bar")
        assert "Error inspecting bar" in capsys.readouterr().out

    def test_handles_import_error_with_empty_modname(self, exporter, capsys):
        # WHY: covers the `modname or "unknown"` fallback branch
        with patch("importlib.import_module", side_effect=ImportError("nope")):
            exporter._inspect_module("")
        assert "Error inspecting" in capsys.readouterr().out


class TestInspectModuleFunctions:
    def test_no_functions_found_logs_and_returns(self, exporter, capsys):
        with patch.object(exporter, "_find_api_functions", return_value=[]):
            exporter._inspect_module_functions(MagicMock(), "foo", "modname")
        assert "No API functions found" in capsys.readouterr().out

    def test_no_suitable_function_logs_and_returns(self, exporter, capsys):
        with (
            patch.object(exporter, "_find_api_functions", return_value=["fn"]),
            patch.object(exporter, "_select_best_function", return_value=None),
        ):
            exporter._inspect_module_functions(MagicMock(), "foo", "modname")
        assert "No suitable API functions" in capsys.readouterr().out

    def test_registers_when_suitable_function_found(self, exporter):
        with (
            patch.object(exporter, "_find_api_functions", return_value=["listFoo"]),
            patch.object(exporter, "_select_best_function", return_value="listFoo"),
            patch.object(exporter, "_register_endpoint") as reg,
        ):
            mod = MagicMock()
            exporter._inspect_module_functions(mod, "foo", "modname")
        reg.assert_called_once_with("foo", mod, "listFoo", "modname")


class TestIsSessionApiFunction:
    def test_rejects_non_function(self):
        assert ConstDefinitionsExporter._is_session_api_function("not a fn") is False

    def test_rejects_function_with_no_params(self):
        def fn():
            pass

        assert ConstDefinitionsExporter._is_session_api_function(fn) is False

    def test_accepts_function_with_mist_session_param(self):
        def fn(mist_session):
            pass

        assert ConstDefinitionsExporter._is_session_api_function(fn) is True

    def test_accepts_function_with_apisession_param(self):
        def fn(apisession):
            pass

        assert ConstDefinitionsExporter._is_session_api_function(fn) is True

    def test_rejects_function_with_wrong_param(self):
        def fn(some_other_param):
            pass

        assert ConstDefinitionsExporter._is_session_api_function(fn) is False


class TestFindApiFunctions:
    def test_finds_functions_with_session_param(self, exporter):
        def listFoo(mist_session):
            pass

        def _hidden(mist_session):
            pass

        def bad():
            pass

        mod = types.SimpleNamespace(listFoo=listFoo, _hidden=_hidden, bad=bad)
        result = exporter._find_api_functions(mod, "foo")
        assert "listFoo" in result
        assert "_hidden" not in result
        assert "bad" not in result


class TestSelectBestFunction:
    def test_prefers_list_prefix(self, exporter):
        assert exporter._select_best_function(["getFoo", "listFoo", "otherFoo"]) == "listFoo"

    def test_falls_back_to_get(self, exporter):
        assert exporter._select_best_function(["getFoo", "otherFoo"]) == "getFoo"

    def test_returns_first_when_no_prefix_match(self, exporter):
        assert exporter._select_best_function(["fooBar", "bazQux"]) == "fooBar"

    def test_returns_none_when_empty(self, exporter):
        assert exporter._select_best_function([]) is None


class TestFirstFunctionWithPrefix:
    def test_returns_first_match(self):
        result = ConstDefinitionsExporter._first_function_with_prefix(["getFoo", "listBar"], "list")
        assert result == "listBar"

    def test_returns_none_when_no_match(self):
        result = ConstDefinitionsExporter._first_function_with_prefix(["fooBar"], "list")
        assert result is None


class TestAnalyzeApiSignature:
    def test_returns_required_and_optional(self, exporter):
        def fn(mist_session, req_a, opt_b="default"):
            pass

        mod = types.SimpleNamespace(fn=fn)
        required, optional = exporter._analyze_api_signature(mod, "fn")
        assert [p.name for p in required] == ["req_a"]
        assert optional == ["opt_b"]


class TestRegisterEndpoint:
    def test_registers_standard_endpoint(self, exporter):
        mod = MagicMock()
        with (
            patch.object(exporter, "_analyze_api_signature", return_value=([], [])),
            patch.object(exporter, "_determine_special_handling", return_value=None),
        ):
            exporter._register_endpoint("foo_bar", mod, "listFooBar", "modname")
        assert "foo_bar" in exporter.discovered_endpoints
        assert exporter.discovered_endpoints["foo_bar"].filename == "ConstFooBar.csv"

    def test_skip_special_handling_does_not_register(self, exporter):
        mod = MagicMock()
        with (
            patch.object(exporter, "_analyze_api_signature", return_value=([], [])),
            patch.object(exporter, "_determine_special_handling", return_value="skip"),
        ):
            exporter._register_endpoint("foo", mod, "listFoo", "modname")
        assert "foo" not in exporter.discovered_endpoints


class TestBuildFilename:
    def test_single_word(self, exporter):
        assert exporter._build_filename("countries") == "ConstCountries.csv"

    def test_multi_word_underscore(self, exporter):
        assert exporter._build_filename("device_models") == "ConstDeviceModels.csv"


class TestGetRequiredParams:
    def test_excludes_session_and_defaults(self, exporter):
        def fn(mist_session, req_a, opt_b="x"):
            pass

        sig = inspect.signature(fn)
        result = exporter._get_required_params(sig)
        assert [p.name for p in result] == ["req_a"]


class TestGetOptionalParams:
    def test_excludes_session_returns_defaults_only(self, exporter):
        def fn(apisession, req_a, opt_b="x"):
            pass

        sig = inspect.signature(fn)
        assert exporter._get_optional_params(sig) == ["opt_b"]


class TestClassifyRequiredParam:
    def test_default_gateway_config_all_models(self, exporter):
        result = exporter._classify_required_param("default_gateway_config", "getConfig", ["model"], "Const.csv")
        assert result == "all_models"

    def test_states_all_countries(self, exporter):
        result = exporter._classify_required_param("states", "getStates", ["country_code"], "Const.csv")
        assert result == "all_countries"

    def test_other_endpoint_skipped(self, exporter):
        result = exporter._classify_required_param("other", "getOther", ["extra"], "Const.csv")
        assert result == "skip"


class TestDetermineSpecialHandling:
    def test_ap_channels_optional_country(self, exporter):
        result = exporter._determine_special_handling("ap_channels", "listChannels", [], ["country_code"], "Const.csv")
        assert result == "all_countries_channels"

    def test_no_required_params_returns_none(self, exporter):
        result = exporter._determine_special_handling("foo", "listFoo", [], [], "Const.csv")
        assert result is None

    def test_required_params_delegates_to_classify(self, exporter):
        p = MagicMock()
        p.name = "model"
        result = exporter._determine_special_handling("default_gateway_config", "getConfig", [p], [], "Const.csv")
        assert result == "all_models"


class TestProcessAllEndpoints:
    def test_iterates_endpoints(self, exporter):
        exporter.discovered_endpoints = {"a": _endpoint_config(endpoint_name="a")}
        with patch.object(exporter, "_process_single_endpoint") as proc:
            exporter._process_all_endpoints()
        assert proc.call_count == 1


class TestProcessSingleEndpoint:
    def test_fresh_file_skipped(self, exporter):
        cfg = _endpoint_config()
        with patch.object(exporter, "_is_file_fresh", return_value=True):
            exporter._process_single_endpoint(cfg)
        assert exporter.endpoints_skipped_fresh == 1
        assert exporter.endpoints_processed == 1

    def test_stale_file_fetches(self, exporter):
        cfg = _endpoint_config()
        with (
            patch.object(exporter, "_is_file_fresh", return_value=False),
            patch.object(exporter, "_fetch_and_export_endpoint") as fetch,
        ):
            exporter._process_single_endpoint(cfg)
        fetch.assert_called_once_with(cfg)
        assert exporter.endpoints_processed == 1

    def test_exception_counts_failed(self, exporter):
        cfg = _endpoint_config()
        with patch.object(exporter, "_is_file_fresh", side_effect=RuntimeError("boom")):
            exporter._process_single_endpoint(cfg)
        assert exporter.endpoints_failed == 1
        assert exporter.endpoints_processed == 1


class TestEvaluateCacheWindow:
    def test_fresh_within_window(self, exporter):
        cfg = _endpoint_config()
        assert exporter._evaluate_cache_window(cfg, 1.0, "2026-01-01 00:00:00") is True

    def test_stale_beyond_window(self, exporter):
        cfg = _endpoint_config()
        assert exporter._evaluate_cache_window(cfg, 999.0, "2026-01-01 00:00:00") is False


class TestIsFileFresh:
    def test_missing_file_returns_false(self, exporter):
        cfg = _endpoint_config()
        with patch("os.path.exists", return_value=False):
            assert exporter._is_file_fresh(cfg) is False

    def test_fresh_file_returns_true(self, exporter):
        cfg = _endpoint_config()
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=1000.0),
            patch("time.time", return_value=1000.0),
        ):
            assert exporter._is_file_fresh(cfg) is True

    def test_exception_returns_false(self, exporter, capsys):
        cfg = _endpoint_config()
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", side_effect=OSError("boom")),
        ):
            assert exporter._is_file_fresh(cfg) is False
        assert "Error checking file timestamp" in capsys.readouterr().out


class TestFetchAndExportEndpoint:
    def test_happy_path(self, exporter):
        cfg = _endpoint_config()
        with (
            patch.object(exporter, "_fetch_endpoint_data", return_value={"a": 1}),
            patch.object(exporter, "_export_data") as export,
        ):
            exporter._fetch_and_export_endpoint(cfg)
        export.assert_called_once_with(cfg, {"a": 1})

    def test_error_writes_empty_and_counts_failure(self, exporter, fake_mh):
        cfg = _endpoint_config()
        with patch.object(exporter, "_fetch_endpoint_data", side_effect=RuntimeError("boom")):
            exporter._fetch_and_export_endpoint(cfg)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], cfg.filename)
        assert exporter.endpoints_failed == 1


class TestFetchEndpointData:
    @pytest.mark.parametrize(
        "handling,method_name",
        [
            ("all_models", "_fetch_all_gateway_models"),
            ("all_countries", "_fetch_all_country_states"),
            ("all_countries_channels", "_fetch_all_country_channels"),
            (None, "_fetch_standard_endpoint"),
        ],
    )
    def test_dispatches_by_handling(self, exporter, handling, method_name):
        cfg = _endpoint_config(special_handling=handling)
        with patch.object(exporter, method_name, return_value=["x"]) as m:
            result = exporter._fetch_endpoint_data(cfg)
        m.assert_called_once_with(cfg)
        assert result == ["x"]


class TestFetchStandardEndpoint:
    def test_returns_data_attribute(self, exporter):
        response = types.SimpleNamespace(data={"a": 1})
        mod = types.SimpleNamespace(listFoo=lambda session: response)
        cfg = _endpoint_config(module=mod, function_name="listFoo")
        assert exporter._fetch_standard_endpoint(cfg) == {"a": 1}

    def test_falls_back_to_response_and_empty(self, exporter):
        mod = types.SimpleNamespace(listFoo=lambda session: None)
        cfg = _endpoint_config(module=mod, function_name="listFoo")
        assert exporter._fetch_standard_endpoint(cfg) == {}


class TestFetchOneGatewayModel:
    def test_returns_normalized_records(self, exporter):
        response = types.SimpleNamespace(data={"port": 1})
        mod = types.SimpleNamespace(getConfig=lambda session, model: response)
        cfg = _endpoint_config(module=mod, function_name="getConfig")
        result = exporter._fetch_one_gateway_model(cfg, "SRX300")
        assert result == [{"model": "SRX300", "port": 1}]

    def test_returns_empty_when_no_data(self, exporter):
        mod = types.SimpleNamespace(getConfig=lambda session, model: types.SimpleNamespace(data=None))
        cfg = _endpoint_config(module=mod, function_name="getConfig")
        assert exporter._fetch_one_gateway_model(cfg, "SRX300") == []

    def test_reraises_on_api_error(self, exporter):
        def broken(session, model):
            raise RuntimeError("boom")

        mod = types.SimpleNamespace(getConfig=broken)
        cfg = _endpoint_config(module=mod, function_name="getConfig")
        with pytest.raises(RuntimeError):
            exporter._fetch_one_gateway_model(cfg, "SRX300")


class TestFetchAllGatewayModels:
    def test_aggregates_and_counts_failures(self, exporter):
        cfg = _endpoint_config()
        with (
            patch.object(exporter, "_get_gateway_models_list", return_value=["A", "B", "C"]),
            patch.object(
                exporter,
                "_fetch_one_gateway_model",
                side_effect=[[{"model": "A"}], RuntimeError("boom"), []],
            ),
        ):
            result = exporter._fetch_all_gateway_models(cfg)
        assert result == [{"model": "A"}]


class TestGetGatewayModelsList:
    def test_returns_gateway_models_from_api(self, exporter):
        response = types.SimpleNamespace(data=[{"model": "SRX300", "type": "gateway"}])
        fake_mod = types.SimpleNamespace(listDeviceModels=lambda s: response)
        with patch("importlib.import_module", return_value=fake_mod):
            result = exporter._get_gateway_models_list()
        assert result == ["SRX300"]

    def test_falls_back_when_api_fails(self, exporter):
        with patch("importlib.import_module", side_effect=RuntimeError("boom")):
            result = exporter._get_gateway_models_list()
        assert result == ConstDefinitionsExporter.FALLBACK_GATEWAY_MODELS

    def test_falls_back_when_no_gateways_found(self, exporter):
        response = types.SimpleNamespace(data=[])
        fake_mod = types.SimpleNamespace(listDeviceModels=lambda s: response)
        with patch("importlib.import_module", return_value=fake_mod):
            result = exporter._get_gateway_models_list()
        assert result == ConstDefinitionsExporter.FALLBACK_GATEWAY_MODELS


class TestFilterGatewayModelsFromDict:
    def test_keeps_only_gateways(self):
        data = {"SRX300": {"type": "gateway"}, "EX3400": {"type": "switch"}, "bad": "not-dict"}
        assert ConstDefinitionsExporter._filter_gateway_models_from_dict(data) == ["SRX300"]


class TestFilterGatewayModelsFromList:
    def test_keeps_only_gateways_with_names(self):
        data = [
            {"model": "SRX300", "type": "gateway"},
            {"name": "EX3400", "type": "switch"},
            {"type": "gateway"},  # No name — skipped
            "not-dict",
        ]
        assert ConstDefinitionsExporter._filter_gateway_models_from_list(data) == ["SRX300"]


class TestExtractGatewayModels:
    def test_handles_dict(self, exporter):
        assert exporter._extract_gateway_models({"SRX": {"type": "gateway"}}) == ["SRX"]

    def test_handles_list(self, exporter):
        assert exporter._extract_gateway_models([{"model": "SRX", "type": "gateway"}]) == ["SRX"]

    def test_returns_empty_for_unknown(self, exporter):
        assert exporter._extract_gateway_models("weird") == []


class TestNormalizeModelData:
    def test_dict_becomes_single_row(self, exporter):
        result = exporter._normalize_model_data("SRX", {"port": 1})
        assert result == [{"model": "SRX", "port": 1}]

    def test_list_of_dicts_tagged(self, exporter):
        result = exporter._normalize_model_data("SRX", [{"a": 1}, {"b": 2}])
        assert result == [{"a": 1, "model": "SRX"}, {"b": 2, "model": "SRX"}]

    def test_scalar_becomes_config_row(self, exporter):
        result = exporter._normalize_model_data("SRX", "raw")
        assert result == [{"model": "SRX", "config": "raw"}]


class TestFetchAllCountryStates:
    def test_aggregates_states(self, exporter):
        response = types.SimpleNamespace(data={"CA": {"name": "California"}})
        mod = types.SimpleNamespace(getStates=lambda s, country_code: response)
        cfg = _endpoint_config(module=mod, function_name="getStates")
        with patch.object(exporter, "_get_country_codes_list", return_value=["US"]):
            result = exporter._fetch_all_country_states(cfg)
        assert len(result) == 1
        assert result[0]["country_code"] == "US"

    def test_handles_failure(self, exporter):
        def broken(s, country_code):
            raise RuntimeError("boom")

        mod = types.SimpleNamespace(getStates=broken)
        cfg = _endpoint_config(module=mod, function_name="getStates")
        with patch.object(exporter, "_get_country_codes_list", return_value=["US"]):
            result = exporter._fetch_all_country_states(cfg)
        assert result == []

    def test_skips_when_no_data(self, exporter):
        mod = types.SimpleNamespace(getStates=lambda s, country_code: types.SimpleNamespace(data=None))
        cfg = _endpoint_config(module=mod, function_name="getStates")
        with patch.object(exporter, "_get_country_codes_list", return_value=["US"]):
            result = exporter._fetch_all_country_states(cfg)
        assert result == []


class TestCallCountriesApi:
    def test_returns_data(self, exporter):
        response = types.SimpleNamespace(data={"US": "United States"})
        fake_mod = types.SimpleNamespace(listCountryCodes=lambda s: response)
        with patch("importlib.import_module", return_value=fake_mod):
            assert exporter._call_countries_api() == {"US": "United States"}

    def test_returns_empty_on_failure(self, exporter):
        with patch("importlib.import_module", side_effect=RuntimeError("boom")):
            assert exporter._call_countries_api() == {}


class TestIsValidAlpha2:
    def test_valid(self):
        assert ConstDefinitionsExporter._is_valid_alpha2("US") is True

    def test_wrong_length(self):
        assert ConstDefinitionsExporter._is_valid_alpha2("USA") is False

    def test_empty(self):
        assert ConstDefinitionsExporter._is_valid_alpha2("") is False

    def test_non_alpha(self):
        assert ConstDefinitionsExporter._is_valid_alpha2("12") is False


class TestFilterValidAlpha2Codes:
    def test_filters_invalid_codes(self):
        result = ConstDefinitionsExporter._filter_valid_alpha2_codes(["US", "USA", "12"])
        assert result == ["US"]


class TestFetchValidCountryCodesFromApi:
    def test_returns_codes_when_api_succeeds(self, exporter):
        with (patch.object(exporter, "_call_countries_api", return_value={"US": "x", "CA": "y"}),):
            result = exporter._fetch_valid_country_codes_from_api()
        assert set(result) == {"US", "CA"}

    def test_returns_empty_when_no_codes(self, exporter):
        with patch.object(exporter, "_call_countries_api", return_value={}):
            assert exporter._fetch_valid_country_codes_from_api() == []


class TestGetCountryCodesList:
    def test_returns_api_codes_when_available(self, exporter):
        with patch.object(exporter, "_fetch_valid_country_codes_from_api", return_value=["US", "CA"]):
            assert exporter._get_country_codes_list() == ["US", "CA"]

    def test_falls_back_when_empty(self, exporter):
        with patch.object(exporter, "_fetch_valid_country_codes_from_api", return_value=[]):
            assert exporter._get_country_codes_list() == ConstDefinitionsExporter.FALLBACK_COUNTRIES


class TestResolveCountryCode:
    def test_prefers_code_field(self):
        assert ConstDefinitionsExporter._resolve_country_code({"code": "US"}) == "US"

    def test_falls_back_to_alpha2(self):
        assert ConstDefinitionsExporter._resolve_country_code({"alpha2": "CA"}) == "CA"

    def test_derives_from_name(self):
        assert ConstDefinitionsExporter._resolve_country_code({"name": "France"}) == "FR"


class TestCodesFromList:
    def test_extracts_codes_skipping_nondicts(self):
        items = [{"code": "US"}, "not-dict", {"alpha2": "CA"}, {}]
        assert ConstDefinitionsExporter._codes_from_list(items) == ["US", "CA"]


class TestExtractCountryCodes:
    def test_dict_returns_keys(self, exporter):
        assert exporter._extract_country_codes({"US": 1, "CA": 2}) == ["US", "CA"]

    def test_list_delegates(self, exporter):
        assert exporter._extract_country_codes([{"code": "US"}]) == ["US"]

    def test_unknown_shape_empty(self, exporter):
        assert exporter._extract_country_codes("weird") == []


class TestNormalizeStatesDict:
    def test_dict_state_data(self):
        result = ConstDefinitionsExporter._normalize_states_dict("US", {"CA": {"name": "California"}})
        assert result == [{"country_code": "US", "state_code": "CA", "name": "California"}]

    def test_scalar_state_data(self):
        result = ConstDefinitionsExporter._normalize_states_dict("US", {"CA": "California"})
        assert result == [{"country_code": "US", "state_code": "CA", "state_name": "California"}]


class TestNormalizeStatesList:
    def test_tags_dicts_only(self):
        data = [{"a": 1}, "not-dict"]
        result = ConstDefinitionsExporter._normalize_states_list("US", data)
        assert result[0]["country_code"] == "US"


class TestNormalizeStatesData:
    def test_dict_dispatch(self, exporter):
        result = exporter._normalize_states_data("US", {"CA": {"x": 1}})
        assert result[0]["country_code"] == "US"

    def test_list_dispatch(self, exporter):
        result = exporter._normalize_states_data("US", [{"a": 1}])
        assert result[0]["country_code"] == "US"

    def test_unknown_returns_empty(self, exporter):
        assert exporter._normalize_states_data("US", 42) == []


class TestFetchAllCountryChannels:
    def test_aggregates_channels(self, exporter):
        response = types.SimpleNamespace(data={"channel": 1})
        mod = types.SimpleNamespace(listChannels=lambda s, country_code: response)
        cfg = _endpoint_config(module=mod, function_name="listChannels")
        with patch.object(exporter, "_get_channel_country_codes", return_value=["US"]):
            result = exporter._fetch_all_country_channels(cfg)
        assert result[0]["country_code"] == "US"

    def test_handles_failure(self, exporter):
        def broken(s, country_code):
            raise RuntimeError("boom")

        mod = types.SimpleNamespace(listChannels=broken)
        cfg = _endpoint_config(module=mod, function_name="listChannels")
        with patch.object(exporter, "_get_channel_country_codes", return_value=["US"]):
            result = exporter._fetch_all_country_channels(cfg)
        assert result == []

    def test_skips_when_no_data(self, exporter):
        mod = types.SimpleNamespace(listChannels=lambda s, country_code: types.SimpleNamespace(data=None))
        cfg = _endpoint_config(module=mod, function_name="listChannels")
        with patch.object(exporter, "_get_channel_country_codes", return_value=["US"]):
            assert exporter._fetch_all_country_channels(cfg) == []


class TestFilterToIso2CountryCodes:
    def test_drops_invalid(self):
        result = ConstDefinitionsExporter._filter_to_iso2_country_codes(["US", "USA", "12"])
        assert result == ["US"]


class TestGetChannelCountryCodes:
    def test_returns_codes_from_api(self, exporter):
        response = types.SimpleNamespace(data={"US": "x", "CA": "y"})
        fake_mod = types.SimpleNamespace(listCountryCodes=lambda s: response)
        with patch("importlib.import_module", return_value=fake_mod):
            result = exporter._get_channel_country_codes()
        assert set(result) == {"US", "CA"}

    def test_falls_back_on_error(self, exporter):
        with patch("importlib.import_module", side_effect=RuntimeError("boom")):
            result = exporter._get_channel_country_codes()
        assert result == ConstDefinitionsExporter.FALLBACK_CHANNEL_COUNTRIES

    def test_falls_back_when_no_codes(self, exporter):
        response = types.SimpleNamespace(data={})
        fake_mod = types.SimpleNamespace(listCountryCodes=lambda s: response)
        with patch("importlib.import_module", return_value=fake_mod):
            result = exporter._get_channel_country_codes()
        assert result == ConstDefinitionsExporter.FALLBACK_CHANNEL_COUNTRIES


class TestExtractCountryCodeFromItem:
    def test_prefers_alpha2(self):
        assert ConstDefinitionsExporter._extract_country_code_from_item({"alpha2": "US"}) == "US"

    def test_falls_back_to_code(self):
        assert ConstDefinitionsExporter._extract_country_code_from_item({"code": "CA"}) == "CA"

    def test_none_for_missing(self):
        assert ConstDefinitionsExporter._extract_country_code_from_item({}) is None

    def test_none_for_non_dict(self):
        assert ConstDefinitionsExporter._extract_country_code_from_item("nope") is None


class TestCountryCodesFromList:
    def test_extracts_valid(self):
        items = [{"alpha2": "US"}, {"code": "CA"}, {}, "not-dict"]
        assert ConstDefinitionsExporter._country_codes_from_list(items) == ["US", "CA"]


class TestExtractChannelCountryCodes:
    def test_dict_returns_keys(self, exporter):
        assert exporter._extract_channel_country_codes({"US": 1}) == ["US"]

    def test_list_delegates(self, exporter):
        assert exporter._extract_channel_country_codes([{"alpha2": "US"}]) == ["US"]

    def test_unknown_empty(self, exporter):
        assert exporter._extract_channel_country_codes(42) == []


class TestNormalizeChannelsData:
    def test_dict_becomes_row(self, exporter):
        result = exporter._normalize_channels_data("US", {"chan": 1})
        assert result == [{"country_code": "US", "chan": 1}]

    def test_list_of_dicts_tagged(self, exporter):
        result = exporter._normalize_channels_data("US", [{"chan": 1}])
        assert result == [{"chan": 1, "country_code": "US"}]

    def test_unknown_returns_empty(self, exporter):
        assert exporter._normalize_channels_data("US", "weird") == []


class TestExportData:
    def test_empty_data_writes_empty(self, exporter, fake_mh):
        cfg = _endpoint_config()
        exporter._export_data(cfg, {})
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], cfg.filename)
        assert exporter.endpoints_updated == 1

    def test_writes_processed_data(self, exporter, fake_mh):
        cfg = _endpoint_config()
        fake_mh.DataProcessingUtils.escape_multiline = MagicMock(return_value=[{"a": 1}])
        # Patch the module-level DataProcessingUtils direct import
        with patch("src.export.const_definitions_exporter.DataProcessingUtils") as dpu:
            dpu.escape_multiline.return_value = [{"a": 1}]
            exporter._export_data(cfg, {"row": {"a": 1}})
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()
        assert exporter.endpoints_updated == 1


class TestConvertToList:
    def test_returns_list_unchanged(self, exporter):
        assert exporter._convert_to_list("foo", [{"a": 1}]) == [{"a": 1}]

    def test_wraps_non_dict_non_list(self, exporter):
        assert exporter._convert_to_list("foo", "raw") == ["raw"]

    def test_wraps_empty_non_dict(self, exporter):
        assert exporter._convert_to_list("foo", None) == []

    def test_insight_metrics_special(self, exporter):
        with patch.object(exporter, "_convert_insight_metrics", return_value=["metric_row"]):
            assert exporter._convert_to_list("insight_metrics", {"m": {}}) == ["metric_row"]

    def test_standard_dict_delegates(self, exporter):
        with patch.object(exporter, "_convert_standard_dict", return_value=["row"]):
            assert exporter._convert_to_list("foo", {"k": "v"}) == ["row"]


class TestConvertInsightMetrics:
    def test_builds_flat_rows(self, exporter):
        data = {
            "metric1": {
                "description": "d",
                "type": "t",
                "unit": "u",
                "scopes": ["a", "b"],
                "report_scopes": ["c"],
                "intervals": {},
                "report_intervals": {},
            }
        }
        result = exporter._convert_insight_metrics(data)
        assert result[0]["metric_name"] == "metric1"
        assert result[0]["scopes"] == "a, b"


class TestFormatIntervals:
    def test_empty_returns_empty_string(self, exporter):
        assert exporter._format_intervals({}) == ""

    def test_formats_intervals(self, exporter):
        result = exporter._format_intervals({"m1": {"interval": 60, "max_age": 3600}})
        assert "m1" in result
        assert "60s" in result


class TestFormatReportIntervals:
    def test_empty(self, exporter):
        assert exporter._format_report_intervals({}) == ""

    def test_formats(self, exporter):
        result = exporter._format_report_intervals({"r1": {"interval": 30}})
        assert "r1" in result
        assert "30s" in result


class TestConvertStandardDict:
    def test_dict_value_merged_with_name(self, exporter):
        result = exporter._convert_standard_dict({"k1": {"a": 1}})
        assert result == [{"name": "k1", "a": 1}]

    def test_scalar_value_becomes_value_row(self, exporter):
        result = exporter._convert_standard_dict({"k1": "raw"})
        assert result == [{"name": "k1", "value": "raw"}]


class TestPrintSummary:
    def test_emits_summary(self, exporter, capsys):
        exporter.endpoints_processed = 5
        exporter.endpoints_skipped_fresh = 2
        exporter.endpoints_updated = 3
        exporter.endpoints_failed = 0
        exporter._print_summary()
        out = capsys.readouterr().out
        assert "Total endpoints processed: 5" in out
