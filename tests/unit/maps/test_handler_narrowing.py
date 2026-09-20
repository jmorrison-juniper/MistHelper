"""Tests for narrowed exception handlers in the maps subsystem."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import requests

from src.maps import _maps_backup, _maps_clone, _maps_coverage, _maps_wizard


class _DummyManager:
    """Provide the attributes that the wrapper classes delegate to."""

    apisession = object()  # Provide an opaque session for Mist API call sites.

    @staticmethod
    def _determine_image_extension(_: str) -> str:
        return ".png"  # Keep clone image tests away from MapsManager dependencies.

    @staticmethod
    def _cleanup_temp_file(_: str | None) -> None:
        return None  # Keep tests focused on exception behavior, not filesystem cleanup.


class TestMapsBackupHandlerNarrowing:
    """Verify backup helpers propagate exceptions outside the narrowed contract."""

    def test_http_get_bytes_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_backup.requests, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad"))
        )
        with pytest.raises(TypeError):
            _maps_backup._http_get_bytes("https://example.test/map.png")

    def test_call_api_propagates_unexpected_error(self) -> None:
        def broken_api(*_args: object, **_kwargs: object) -> object:
            raise TypeError("bad api")

        with pytest.raises(TypeError):
            _maps_backup._call_api(broken_api, object(), "site-1", "zones")

    def test_fetch_devices_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def broken_fetch(*_args: object, **_kwargs: object) -> object:
            raise TypeError("bad devices")

        monkeypatch.setattr(_maps_backup.mistapi.api.v1.sites.devices, "listSiteDevices", broken_fetch)
        request = _maps_backup.BackupRequest(object(), "site-1", "map-1", "Map")
        with pytest.raises(TypeError):
            _maps_backup._fetch_devices(request)

    def test_http_get_bytes_handles_request_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def broken_get(*_args: object, **_kwargs: object) -> object:
            raise requests.RequestException("network")

        monkeypatch.setattr(_maps_backup.requests, "get", broken_get)
        assert _maps_backup._http_get_bytes(
            "https://example.test/map.png"
        ) == (  # nosec B101  # WHY: pytest verifies the sentinel.
            None,
            0,
        )


class TestMapsCoverageHandlerNarrowing:
    """Verify coverage fetch helpers do not swallow programming errors."""

    def test_safe_call_propagates_unexpected_error(self) -> None:
        with pytest.raises(TypeError):
            _maps_coverage._safe_call("devices", lambda: (_ for _ in ()).throw(TypeError("bad layer")))

    def test_fetch_coverage_layer_propagates_unexpected_error(self) -> None:
        session = SimpleNamespace(mist_get=lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad coverage")))
        with pytest.raises(TypeError):
            _maps_coverage._MapsCoverage(_DummyManager())._fetch_coverage_layer(session, "site-1", "map-1", "wifi", 1.0)


class TestMapsCloneHandlerNarrowing:
    """Verify clone helpers expose errors that the narrowed handlers no longer catch."""

    def test_fetch_source_zone_count_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_clone.mistapi.api.v1.sites.zones,
            "listSiteZones",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad zones")),
        )
        with pytest.raises(TypeError):
            _maps_clone._MapsClone(_DummyManager())._fetch_source_zone_count("site-1", "map-1")

    def test_download_clone_image_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_clone._MapsClone,
            "_download_image_to_tempfile",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad image")),
        )
        with pytest.raises(TypeError):
            _maps_clone._MapsClone(_DummyManager())._download_clone_image({"url": "https://example.test/map.png"})

    def test_upload_clone_image_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_clone.mistapi.api.v1.sites.maps,
            "addSiteMapImageFile",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad upload")),
        )
        with pytest.raises(TypeError):
            _maps_clone._MapsClone(_DummyManager())._upload_clone_image("site-1", "map-1", "image.png")

    def test_clone_single_zone_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_clone.mistapi.api.v1.sites.zones,
            "createSiteZone",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad zone")),
        )
        with pytest.raises(TypeError):
            _maps_clone._MapsClone(_DummyManager())._clone_single_zone("site-1", "map-1", {"name": "zone"})

    def test_clone_zones_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_clone._MapsClone,
            "_fetch_source_zones",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad fetch")),
        )
        with pytest.raises(TypeError):
            _maps_clone._MapsClone(_DummyManager())._clone_zones("site-1", "source-map", "new-map")


class TestMapsWizardHandlerNarrowing:
    """Verify wizard helpers propagate errors outside their narrowed contracts."""

    def test_wizard_fetch_devices_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_wizard.mistapi.api.v1.sites.devices,
            "listSiteDevices",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad devices")),
        )
        with pytest.raises(TypeError):
            _maps_wizard._MapsWizard(_DummyManager())._wizard_fetch_devices("site-1", "map-1")

    def test_wizard_fetch_zones_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_wizard.mistapi.api.v1.sites.zones,
            "listSiteZones",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad zones")),
        )
        with pytest.raises(TypeError):
            _maps_wizard._MapsWizard(_DummyManager())._wizard_fetch_zones("site-1", "map-1")

    def test_wizard_fetch_beacons_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_wizard._MapsWizard,
            "_fetch_beacons_of_kind",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad beacon")),
        )
        with pytest.raises(TypeError):
            _maps_wizard._MapsWizard(_DummyManager())._wizard_fetch_beacons("site-1", "map-1")

    def test_read_image_dimensions_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from PIL import Image

        monkeypatch.setattr(Image, "open", lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad image")))
        with pytest.raises(TypeError):
            _maps_wizard._MapsWizard(_DummyManager())._read_image_dimensions("image.png")

    def test_apply_image_upload_propagates_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            _maps_wizard.mistapi.api.v1.sites.maps,
            "addSiteMapImageFile",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("bad upload")),
        )
        target = _maps_wizard._ImageUploadTarget("site-1", "map-1", "image.png")
        with pytest.raises(TypeError):
            _maps_wizard._MapsWizard(_DummyManager())._apply_image_upload(target, [])
