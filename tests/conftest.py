"""Pytest configuration for MistHelper test suite.

Provides test isolation: temp directories, no network, no .env loading.
Unit tests must run offline with zero API credentials in under 30 seconds.
"""

import importlib.util
import sys
from pathlib import Path
import types

# Ensure project root is first on sys.path so `src` package imports succeed during tests
_project_root = Path(__file__).parents[1].resolve()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Provide a lightweight stub for `arango` package to avoid importing python-arango during unit tests
arango_mod = types.ModuleType("arango")

class _ArangoClientStub:
    def __init__(self, *args, **kwargs):
        pass

    def db(self, name, **kwargs):
        return None

arango_mod.ArangoClient = _ArangoClientStub
sys.modules["arango"] = arango_mod
# also provide arango.client module variant used by some import forms
arango_client_mod = types.ModuleType("arango.client")
arango_client_mod.ArangoClient = _ArangoClientStub
sys.modules["arango.client"] = arango_client_mod
import pytest
import re

# Provide a minimal, offline-friendly stub for `mistapi` when running unit tests
# This avoids importing heavy runtime dependencies (hvac, requests) during test
# collection; real mistapi will be used when installed and desired via env vars.
try:  # Attempt to import real mistapi if available in the environment
    import mistapi  # type: ignore  # Prefer real package when present for integration tests

    # If real mistapi is present but its version is older than the minimum
    # supported by test fixtures/modules (0.61.0), override it with our stub
    # so import-time version gates in code under test do not raise.
    def _parse_version_str(v: str) -> tuple[int, int, int]:
        nums = re.findall(r"\d+", str(v or ""))
        parts = [int(n) for n in nums[:3]]
        while len(parts) < 3:
            parts.append(0)
        return parts[0], parts[1], parts[2]

    try:
        installed_ver = _parse_version_str(getattr(mistapi, "__version__", None))
    except Exception:
        installed_ver = (0, 0, 0)

    if installed_ver < (0, 61, 0):
        # Replace real mistapi with a controlled stub that advertises a
        # compatible __version__ so import-time gates pass during tests.
        mistapi = None
        raise ImportError("force-stub")

except Exception:  # Fallback: create lightweight package-style stub modules to satisfy imports
    import types  # Build module/type placeholders for the stub

    # Create package module `mistapi` so `import mistapi.api.v1.orgs` works
    mistapi_mod = types.ModuleType("mistapi")  # Module object for mistapi package
    mistapi_mod.__path__ = ["<stub>"]  # Mark as package to the import system
    # Provide a compatible __version__ for modules that perform runtime
    # version checks during import (e.g., websocket adapter). Tests expect
    # the stub to satisfy minimum SDK version gates.
    mistapi_mod.__version__ = "0.61.0"

    # Build nested package modules: mistapi.api and mistapi.api.v1
    api_mod = types.ModuleType("mistapi.api")  # Subpackage module for api
    api_mod.__path__ = ["<stub>"]  # Mark as package
    v1_mod = types.ModuleType("mistapi.api.v1")  # Subpackage module for api.v1
    v1_mod.__path__ = ["<stub>"]  # Mark as package

    # Create concrete submodules expected by code: mistapi.api.v1.orgs, mistapi.api.v1.sites
    orgs_mod = types.ModuleType("mistapi.api.v1.orgs")
    orgs_mod.__path__ = ["<stub>"]  # Mark as package so submodules can be imported
    sites_mod = types.ModuleType("mistapi.api.v1.sites")
    sites_mod.__path__ = ["<stub>"]  # Mark as package so submodules can be imported

    # Provide small placeholders for common attributes to avoid attribute errors
    orgs_mod.devices = types.SimpleNamespace()  # Placeholder namespace for orgs.devices
    orgs_mod.gatewaytemplates = types.SimpleNamespace()  # Placeholder for gatewaytemplates API
    sites_mod.devices = types.SimpleNamespace()  # Placeholder namespace for sites.devices

    # Create common submodules used in tests so monkeypatch.setattr(..., raising=True) succeeds
    maps_mod = types.ModuleType("mistapi.api.v1.sites.maps")
    maps_mod.__path__ = ["<stub>"]
    # provide placeholder callable to allow attribute assignment via monkeypatch
    def _list_site_maps(*args, **kwargs):
        return types.SimpleNamespace(status_code=200)

    maps_mod.listSiteMaps = _list_site_maps

    wlans_mod = types.ModuleType("mistapi.api.v1.sites.wlans")
    wlans_mod.__path__ = ["<stub>"]

    def _list_site_wlans(*args, **kwargs):
        return types.SimpleNamespace(status_code=200)

    wlans_mod.listSiteWlans = _list_site_wlans

    stats_mod = types.ModuleType("mistapi.api.v1.sites.stats")
    stats_mod.__path__ = ["<stub>"]

    def _list_site_wireless_clients_stats(*args, **kwargs):
        return types.SimpleNamespace(data=[])

    stats_mod.listSiteWirelessClientsStats = _list_site_wireless_clients_stats

    insights_mod_sites = types.ModuleType("mistapi.api.v1.sites.insights")
    insights_mod_sites.__path__ = ["<stub>"]
    insights_mod_orgs = types.ModuleType("mistapi.api.v1.orgs.insights")
    insights_mod_orgs.__path__ = ["<stub>"]

    def _get_org_sites_sle(*args, **kwargs):
        return types.SimpleNamespace(data=[])

    insights_mod_orgs.getOrgSitesSle = _get_org_sites_sle

    # Attach to parent modules and sys.modules for direct import/attribute access
    sites_mod.maps = maps_mod
    sites_mod.wlans = wlans_mod
    sites_mod.stats = stats_mod
    sites_mod.insights = insights_mod_sites
    orgs_mod.insights = insights_mod_orgs
    sys.modules["mistapi.api.v1.sites.maps"] = maps_mod
    sys.modules["mistapi.api.v1.sites.wlans"] = wlans_mod
    sys.modules["mistapi.api.v1.sites.stats"] = stats_mod
    sys.modules["mistapi.api.v1.sites.insights"] = insights_mod_sites
    sys.modules["mistapi.api.v1.orgs.insights"] = insights_mod_orgs

    # Attach submodules to parent modules to mirror real package layout
    v1_mod.orgs = orgs_mod
    v1_mod.sites = sites_mod
    api_mod.v1 = v1_mod
    mistapi_mod.api = api_mod

    # Minimal helper and APISession class to allow fixtures and code to instantiate
    def _get_all(response, mist_session=None):
        """Return `.data` attribute if present, mirroring mistapi.get_all helper."""
        return getattr(response, "data", response)

    class APISession:  # Lightweight stand-in for mistapi.APISession used by tests
        def __init__(self, apitoken=None, host=None):
            self.apitoken = apitoken
            self.host = host

    # Attach helpers and classes to the top-level stub module
    mistapi_mod.get_all = _get_all
    mistapi_mod.APISession = APISession

    # Install all created modules into sys.modules so standard imports succeed
    sys.modules["mistapi"] = mistapi_mod
    sys.modules["mistapi.api"] = api_mod
    sys.modules["mistapi.api.v1"] = v1_mod
    sys.modules["mistapi.api.v1.orgs"] = orgs_mod
    sys.modules["mistapi.api.v1.sites"] = sites_mod

# Meta-path finder to dynamically create stub modules for any mistapi submodule
# This allows imports like `mistapi.api.v1.orgs.gatewaytemplates` to succeed
import importlib.abc
import importlib.machinery


class _CallableModule(types.ModuleType):
    """Module type that is also callable to support mistapi function modules."""

    def __call__(self, *args, **kwargs):
        # Heuristic: list/search/sites style calls return list-like `.data`, others return dict-like `.data`
        name = self.__name__.split('.')[-1]
        is_list = name.startswith("list") or "search" in name.lower() or name.startswith("search") or name in ("sites", "devices")
        data = [] if is_list else {}
        # Provide pagination-friendly attributes expected by caller code
        return types.SimpleNamespace(data=data, next=None, status_code=200)


class _MistApiLoader(importlib.abc.Loader):
    """Loader that materializes lightweight stub modules for mistapi on demand."""

    def create_module(self, spec):
        # Materialize all mistapi modules as _CallableModule so attribute-style
        # access and callable heuristics work consistently for the test stub
        # importer. Returning a callable-module for all depths preserves the
        # dynamic attribute chaining tests expect (mistapi.api.v1.orgs.*).
        return _CallableModule(spec.name)

    def exec_module(self, module):
        # Populate basic attributes so modules behave like packages
        module.__file__ = "<mistapi-stub>"
        module.__package__ = module.__name__
        module.__path__ = ["<mistapi-stub>"]

        # Provide top-level helpers only on the root mistapi module
        if module.__name__ == "mistapi":
            def _get_all(response, mist_session=None):
                return getattr(response, "data", response)

            module.get_all = _get_all

            class APISession:  # Lightweight stand-in class
                def __init__(self, apitoken=None, host=None):
                    self.apitoken = apitoken
                    self.host = host

            module.APISession = APISession
            # Satisfy version checks performed by modules importing mistapi
            # during test collection (avoid ImportError gates).
            module.__version__ = "0.61.0"

        # Ensure parent package exposes the child as an attribute for attribute-style access
        parent_name, _, child_name = module.__name__.rpartition('.')
        if parent_name:
            parent = sys.modules.get(parent_name)
            if parent is not None:
                try:
                    setattr(parent, child_name, module)
                except Exception:
                    pass

        # If this is the mistapi logger shim, provide a noop LogSanitizer compatible with
        # logging.addFilter() expectations (has filter() and is callable).
        if module.__name__ == "mistapi.__logger":
            class LogSanitizer:
                def __call__(self, record):
                    return True

                def filter(self, record):
                    return True

            module.LogSanitizer = LogSanitizer

        # Provide a module-level __getattr__ to lazily create common API call stubs
        def _make_stub_callable(attr_name: str):
            """Return a callable that mimics an SDK API call and returns a simple response object."""

            def _call(*args, **kwargs):
                # Heuristic: list/search style functions return list-like `.data`, others return dict-like `.data`
                is_list = attr_name.startswith("list") or "search" in attr_name.lower() or attr_name.startswith("search")
                data = [] if is_list else {}
                # Include pagination-friendly attributes (next/status_code) so callers
                # that inspect response.next or response.status_code do not error.
                return types.SimpleNamespace(data=data, next=None, status_code=200)

            return _call

        # Reentrancy guard to avoid recursive loops in __getattr__ during submodule imports
        _importing = False

        def __getattr__(name: str):
            nonlocal _importing
            # Create and cache stub callables on first access
            if name in module.__dict__:
                return module.__dict__[name]

            if not _importing:
                submodule_name = f"{module.__name__}.{name}"
                _importing = True
                try:
                    if submodule_name in sys.modules:
                        return sys.modules[submodule_name]
                    import importlib
                    return importlib.import_module(submodule_name)
                except ImportError:
                    pass
                finally:
                    _importing = False

            stub = _make_stub_callable(name)
            setattr(module, name, stub)
            return stub

        # Attach the attribute hook and a simple __dir__ implementation
        module.__getattr__ = __getattr__
        module.__dir__ = lambda: list(module.__dict__.keys())


class _MistApiFinder(importlib.abc.MetaPathFinder):
    """MetaPathFinder that claims ownership of any import starting with 'mistapi'."""

    def find_spec(self, fullname, path, target=None):
        if "doesnotexist" in fullname:
            # Block dummy test submodules from being materialized to allow normal import-failure testing
            return None
        if fullname == "mistapi" or fullname.startswith("mistapi."):
            spec = importlib.machinery.ModuleSpec(fullname, _MistApiLoader(), is_package=True)
            spec.submodule_search_locations = ["<stub>"]
            return spec
        return None


# Install finder at front so it takes precedence during test collection
sys.meta_path.insert(0, _MistApiFinder())

# Provide a lightweight stub for `requests` if importing the real package fails
# This prevents requests from importing optional backends (simplejson) at import time
try:
    import requests  # type: ignore  # Prefer real requests when available
except Exception:  # pragma: no cover - fallback only used in constrained test envs
    import json as _json  # Use stdlib JSON for decode error type
    # Build minimal requests package stub
    _req_mod = types.ModuleType("requests")  # Minimal module to satisfy imports
    _req_mod.__path__ = ["<stub>"]  # Mark as package so submodules like requests.adapters can be imported

    # compatibility helpers expected by requests.compat
    _compat = types.ModuleType("requests.compat")  # compat submodule
    _compat.JSONDecodeError = _json.JSONDecodeError  # Alias stdlib JSONDecodeError

    # exceptions expected by callers
    _exceptions = types.ModuleType("requests.exceptions")  # exceptions submodule

    class RequestException(Exception):
        """Generic request exception used in tests when network calls are attempted."""

    class ConnectionError(RequestException):
        """Connection error placeholder for requests.ConnectionError import sites."""

    _exceptions.RequestException = RequestException
    _exceptions.RequestsDependencyWarning = Warning
    _exceptions.ConnectionError = ConnectionError

    # simple network-call stubs that fail loudly if used during tests
    def _network_disabled(*args, **kwargs):
        raise RuntimeError("Network calls disabled in unit test environment")

    _req_mod.get = _network_disabled
    _req_mod.post = _network_disabled
    _req_mod.compat = _compat
    _req_mod.exceptions = _exceptions
    # Top-level ConnectionError and Session expected by some third-party libs (python-arango)
    _req_mod.ConnectionError = ConnectionError

    class Session:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            return _network_disabled()

    _req_mod.Session = Session

    # Minimal adapters and sessions submodules expected by requests_toolbelt / arango
    adapters_mod = types.ModuleType("requests.adapters")

    class HTTPAdapter:
        def __init__(self, *args, **kwargs):
            pass

    adapters_mod.HTTPAdapter = HTTPAdapter

    sessions_mod = types.ModuleType("requests.sessions")
    sessions_mod.Session = Session

    # Attach submodules to the top-level stub and sys.modules so imports like
    # `from requests.adapters import HTTPAdapter` succeed during tests.
    _req_mod.adapters = adapters_mod
    _req_mod.sessions = sessions_mod
    sys.modules["requests.adapters"] = adapters_mod
    sys.modules["requests.sessions"] = sessions_mod

    # Install stubs into sys.modules so imports succeed without touching site-packages
    sys.modules["requests"] = _req_mod
    sys.modules["requests.compat"] = _compat
    sys.modules["requests.exceptions"] = _exceptions

# Do not preload `MistHelper` here; allow normal package import semantics to run
# so that `from MistHelper import ...` resolves through the package `__init__.py`.


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory for test file output."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def tmp_jsonl_file(tmp_data_dir):
    """Provide a temporary JSONL file path for telemetry tests."""
    return str(tmp_data_dir / "test_events.jsonl")


@pytest.fixture(autouse=True)
def isolate_working_directory(tmp_path, monkeypatch):
    """Ensure tests never write to the real data/ directory."""
    monkeypatch.chdir(tmp_path)
