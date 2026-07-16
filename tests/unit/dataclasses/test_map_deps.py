"""Tests for the frozen slotted map-related dataclasses in src/dataclasses/.

Wave 14 P2 coverage lift (issue #1018). These dataclasses are simple
frozen/slots containers used by the MapsManager tranche-3 refactor;
covering them is a cheap way to bump total line coverage while also
locking in the immutability contract call sites depend on.
"""  # WHY: module docstring explains the coverage-wave intent for future readers.

from __future__ import annotations  # WHY: PEP 604 unions in test annotations.

import dataclasses  # WHY: used to introspect the FrozenInstanceError contract.

import pytest  # WHY: parametrize + exception assertions.

from src.dataclasses.map_clone_deps import (  # WHY: 2 dataclasses under test.
    MapCloneSummary,
    ZoneCloneResult,
)
from src.dataclasses.map_marker_deps import (  # WHY: 2 dataclasses under test.
    DeviceMarkerStyle,
    MarkerPosition,
)
from src.dataclasses.map_scaling_deps import (  # WHY: 4 dataclasses under test.
    MapDimensions,
    MapScalingFactors,
    OriginalMapMetrics,
    ScaleChoiceContext,
)
from src.dataclasses.map_viewer_deps import (  # WHY: 4 dataclasses under test.
    HeatmapRenderCtx,
    MapViewerData,
    MapViewerOptional,
    MapViewerScope,
)
from src.dataclasses.map_wizard_deps import (  # WHY: 4 dataclasses under test.
    MapWizardApplyContext,
    MapWizardApplyTarget,
    MapWizardPreviewContext,
    MapWizardSummaryContext,
)


class TestMapMarkerDeps:
    """MarkerPosition + DeviceMarkerStyle: 2 simple frozen dataclasses."""

    def test_marker_position_stores_coordinates(self) -> None:
        """A MarkerPosition should keep x/y as passed at construction."""  # WHY: happy-path attribute round-trip.
        pos = MarkerPosition(x=10.5, y=20.25)  # WHY: build with float coords typical of Plotly canvas.
        assert pos.x == 10.5  # WHY: verify x round-trips exactly.
        assert pos.y == 20.25  # WHY: verify y round-trips exactly.

    def test_marker_position_is_frozen(self) -> None:
        """Frozen dataclass must reject attribute mutation."""  # WHY: locks in immutability contract.
        pos = MarkerPosition(x=1.0, y=2.0)  # WHY: any position instance suffices for the mutation attempt.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: expected error type from frozen=True.
            pos.x = 99.0  # type: ignore[misc]  # WHY: must raise, not silently assign.

    def test_device_marker_style_stores_fields(self) -> None:
        """DeviceMarkerStyle should keep angle/color/type_cfg intact."""  # WHY: three-field round-trip check.
        style = DeviceMarkerStyle(  # WHY: build a realistic style with a dict-shaped type_cfg.
            angle=45.0,
            device_color="#00FF00",
            type_cfg={"legend": "AP", "size": 12},
        )
        assert style.angle == 45.0  # WHY: numeric field round-trips.
        assert style.device_color == "#00FF00"  # WHY: string field round-trips.
        assert style.type_cfg == {"legend": "AP", "size": 12}  # WHY: dict field round-trips by value.

    def test_device_marker_style_is_frozen(self) -> None:
        """DeviceMarkerStyle enforces frozen semantics."""  # WHY: same frozen guard as MarkerPosition.
        style = DeviceMarkerStyle(angle=0.0, device_color="#000", type_cfg={})  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: assignment must raise.
            style.angle = 180.0  # type: ignore[misc]  # WHY: verify frozen guard trips.


class TestMapCloneDeps:
    """MapCloneSummary + ZoneCloneResult round-trip and immutability."""

    def test_map_clone_summary_round_trip(self) -> None:
        """All 5 fields should be preserved after construction."""  # WHY: five-field dataclass smoke test.
        source_map = {"id": "src-map-uuid", "walls": []}  # WHY: minimal Mist map payload shape.
        payload = {"name": "clone-1", "ppm": 20}  # WHY: minimal POST body shape.
        summary = MapCloneSummary(  # WHY: build with all 5 fields present.
            source_map=source_map,
            new_name="clone-1",
            cloned_map_id="new-map-uuid",
            clone_payload=payload,
            had_image=True,
        )
        assert summary.source_map is source_map  # WHY: identity preserved for the dict reference.
        assert summary.new_name == "clone-1"  # WHY: string round-trips.
        assert summary.cloned_map_id == "new-map-uuid"  # WHY: string round-trips.
        assert summary.clone_payload is payload  # WHY: dict identity preserved.
        assert summary.had_image is True  # WHY: bool round-trips.

    def test_map_clone_summary_is_frozen(self) -> None:
        """MapCloneSummary must reject mutation."""  # WHY: frozen guard.
        summary = MapCloneSummary(  # WHY: build minimal instance for the frozen check.
            source_map={},
            new_name="x",
            cloned_map_id="y",
            clone_payload={},
            had_image=False,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            summary.new_name = "changed"  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_zone_clone_result_stores_counts(self) -> None:
        """ZoneCloneResult stores cloned + failed integer counts."""  # WHY: two-int dataclass round-trip.
        result = ZoneCloneResult(cloned=3, failed=1)  # WHY: mix of non-zero values.
        assert result.cloned == 3  # WHY: cloned count round-trips.
        assert result.failed == 1  # WHY: failed count round-trips.

    def test_zone_clone_result_is_frozen(self) -> None:
        """ZoneCloneResult must reject mutation."""  # WHY: frozen guard.
        result = ZoneCloneResult(cloned=0, failed=0)  # WHY: zero-count instance for frozen check.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            result.cloned = 5  # type: ignore[misc]  # WHY: verify frozen contract.


class TestMapWizardDeps:
    """Wizard preview/apply/summary contexts + apply target."""

    def test_preview_context_round_trip(self) -> None:
        """MapWizardPreviewContext keeps current_map/name/assets."""  # WHY: three-field round-trip.
        ctx = MapWizardPreviewContext(  # WHY: build with populated fields.
            current_map={"ppm": 20.0},
            map_name="Floor 1",
            assets={"devices": [], "zones": []},
        )
        assert ctx.current_map == {"ppm": 20.0}  # WHY: dict field round-trips.
        assert ctx.map_name == "Floor 1"  # WHY: str field round-trips.
        assert ctx.assets == {"devices": [], "zones": []}  # WHY: dict field round-trips.

    def test_preview_context_is_frozen(self) -> None:
        """MapWizardPreviewContext must reject mutation."""  # WHY: frozen guard.
        ctx = MapWizardPreviewContext(current_map={}, map_name="", assets={})  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            ctx.map_name = "new"  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_apply_target_round_trip(self) -> None:
        """MapWizardApplyTarget stores site/map/file identifiers."""  # WHY: three-field round-trip.
        target = MapWizardApplyTarget(  # WHY: realistic site/map UUIDs + path.
            site_id="site-uuid",
            map_id="map-uuid",
            file_path="/tmp/new-image.png",
        )
        assert target.site_id == "site-uuid"  # WHY: str field round-trips.
        assert target.map_id == "map-uuid"  # WHY: str field round-trips.
        assert target.file_path == "/tmp/new-image.png"  # WHY: str field round-trips.

    def test_apply_target_is_frozen(self) -> None:
        """MapWizardApplyTarget must reject mutation."""  # WHY: frozen guard.
        target = MapWizardApplyTarget(site_id="s", map_id="m", file_path="/p")  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            target.site_id = "changed"  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_apply_context_round_trip(self) -> None:
        """MapWizardApplyContext keeps mutable assets + errors list references."""  # WHY: three-field round-trip.
        errors: list[str] = ["existing error"]  # WHY: pre-populated list to prove reference preservation.
        assets = {"devices": [{"id": "d1"}]}  # WHY: mutable inner dict.
        ctx = MapWizardApplyContext(  # WHY: build the apply-step state carrier.
            current_map={"ppm": 20.0},
            assets=assets,
            errors=errors,
        )
        assert ctx.current_map == {"ppm": 20.0}  # WHY: dict field round-trips.
        assert ctx.assets is assets  # WHY: reference identity preserved (mutability is intentional).
        assert ctx.errors is errors  # WHY: reference identity preserved for out-parameter semantics.
        ctx.errors.append("new error")  # WHY: proves errors list is mutable via the shared reference.
        assert errors == ["existing error", "new error"]  # WHY: shared reference reflects append.

    def test_apply_context_is_frozen(self) -> None:
        """MapWizardApplyContext rejects re-binding its fields."""  # WHY: fields frozen even if inner list mutable.
        ctx = MapWizardApplyContext(current_map={}, assets={}, errors=[])  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            ctx.errors = []  # type: ignore[misc]  # WHY: verify frozen contract at the field level.

    def test_summary_context_round_trip(self) -> None:
        """MapWizardSummaryContext keeps map/backup/errors intact."""  # WHY: three-field round-trip.
        errors: list[str] = []  # WHY: empty error list means clean run.
        ctx = MapWizardSummaryContext(  # WHY: build the summary printer input carrier.
            map_name="Floor 2",
            backup_file="/backups/floor2.json",
            errors=errors,
        )
        assert ctx.map_name == "Floor 2"  # WHY: str field round-trips.
        assert ctx.backup_file == "/backups/floor2.json"  # WHY: str field round-trips.
        assert ctx.errors is errors  # WHY: reference identity preserved.

    def test_summary_context_is_frozen(self) -> None:
        """MapWizardSummaryContext must reject mutation."""  # WHY: frozen guard.
        ctx = MapWizardSummaryContext(map_name="", backup_file="", errors=[])  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            ctx.map_name = "changed"  # type: ignore[misc]  # WHY: verify frozen contract.


class TestMapViewerDeps:
    """MapViewerScope/Data/Optional and HeatmapRenderCtx."""

    def test_viewer_scope_round_trip(self) -> None:
        """MapViewerScope stores site + map identifiers."""  # WHY: three-field round-trip.
        scope = MapViewerScope(site_id="s", site_name="HQ", map_id="m")  # WHY: minimal identity triple.
        assert scope.site_id == "s"  # WHY: str field round-trips.
        assert scope.site_name == "HQ"  # WHY: str field round-trips.
        assert scope.map_id == "m"  # WHY: str field round-trips.

    def test_viewer_scope_is_frozen(self) -> None:
        """MapViewerScope rejects mutation."""  # WHY: frozen guard.
        scope = MapViewerScope(site_id="s", site_name="HQ", map_id="m")  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            scope.site_name = "Other"  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_viewer_data_round_trip(self) -> None:
        """MapViewerData stores payload arrays intact."""  # WHY: four-field round-trip.
        data = MapViewerData(  # WHY: realistic empty-arrays payload.
            map_data={"ppm": 20.0},
            devices=[{"id": "d1"}],
            zones=[{"id": "z1"}],
            clients=[{"mac": "aa:bb"}],
        )
        assert data.map_data == {"ppm": 20.0}  # WHY: dict field round-trips.
        assert data.devices == [{"id": "d1"}]  # WHY: list field round-trips.
        assert data.zones == [{"id": "z1"}]  # WHY: list field round-trips.
        assert data.clients == [{"mac": "aa:bb"}]  # WHY: list field round-trips.

    def test_viewer_data_is_frozen(self) -> None:
        """MapViewerData rejects mutation."""  # WHY: frozen guard.
        data = MapViewerData(map_data={}, devices=[], zones=[], clients=[])  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            data.devices = []  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_viewer_optional_defaults_to_none(self) -> None:
        """MapViewerOptional carries three optional list/dict payloads."""  # WHY: covers the None branch semantics.
        opt = MapViewerOptional(coverage_data=None, all_maps=None, all_sites=None)  # WHY: all-None instance.
        assert opt.coverage_data is None  # WHY: verifies None default is accepted.
        assert opt.all_maps is None  # WHY: verifies None default is accepted.
        assert opt.all_sites is None  # WHY: verifies None default is accepted.

    def test_viewer_optional_stores_values(self) -> None:
        """MapViewerOptional round-trips populated values."""  # WHY: covers the populated branch semantics.
        opt = MapViewerOptional(  # WHY: build with realistic non-empty payloads.
            coverage_data={"grid": []},
            all_maps=[{"id": "m1"}, {"id": "m2"}],
            all_sites=[{"id": "s1"}],
        )
        assert opt.coverage_data == {"grid": []}  # WHY: dict round-trips.
        assert opt.all_maps == [{"id": "m1"}, {"id": "m2"}]  # WHY: list round-trips.
        assert opt.all_sites == [{"id": "s1"}]  # WHY: list round-trips.

    def test_viewer_optional_is_frozen(self) -> None:
        """MapViewerOptional rejects mutation."""  # WHY: frozen guard.
        opt = MapViewerOptional(coverage_data=None, all_maps=None, all_sites=None)  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            opt.coverage_data = {}  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_heatmap_render_ctx_round_trip(self) -> None:
        """HeatmapRenderCtx carries figure/renderer/coverage handles."""  # WHY: three-field round-trip.
        fig = object()  # WHY: opaque figure sentinel (not a real Plotly figure to keep test light).
        renderer = object()  # WHY: opaque renderer sentinel.
        coverage = {"grid": [[0.5]]}  # WHY: realistic coverage payload shape.
        ctx = HeatmapRenderCtx(fig=fig, heatmap_renderer=renderer, coverage_data=coverage)  # WHY: build instance.
        assert ctx.fig is fig  # WHY: identity preserved for the figure sentinel.
        assert ctx.heatmap_renderer is renderer  # WHY: identity preserved for the renderer sentinel.
        assert ctx.coverage_data == coverage  # WHY: dict field round-trips.

    def test_heatmap_render_ctx_none_coverage(self) -> None:
        """HeatmapRenderCtx accepts None coverage_data to signal skip."""  # WHY: covers the skip-heatmap branch.
        ctx = HeatmapRenderCtx(fig=object(), heatmap_renderer=object(), coverage_data=None)  # WHY: None means skip.
        assert ctx.coverage_data is None  # WHY: verifies the None branch is representable.

    def test_heatmap_render_ctx_is_frozen(self) -> None:
        """HeatmapRenderCtx rejects mutation."""  # WHY: frozen guard.
        ctx = HeatmapRenderCtx(fig=object(), heatmap_renderer=object(), coverage_data=None)  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            ctx.coverage_data = {}  # type: ignore[misc]  # WHY: verify frozen contract.


class TestMapScalingDeps:
    """MapDimensions/ScalingFactors/OriginalMapMetrics/ScaleChoiceContext."""

    def test_map_dimensions_round_trip(self) -> None:
        """MapDimensions carries pixel size + ppm."""  # WHY: three-field round-trip.
        dims = MapDimensions(width_px=1000, height_px=800, ppm=20.5)  # WHY: realistic map sizing values.
        assert dims.width_px == 1000  # WHY: int field round-trips.
        assert dims.height_px == 800  # WHY: int field round-trips.
        assert dims.ppm == 20.5  # WHY: float field round-trips.

    def test_map_dimensions_is_frozen(self) -> None:
        """MapDimensions rejects mutation."""  # WHY: frozen guard.
        dims = MapDimensions(width_px=0, height_px=0, ppm=0.0)  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            dims.ppm = 25.0  # type: ignore[misc]  # WHY: verify frozen contract.

    @pytest.mark.parametrize(  # WHY: cover all four scaling modes documented in the source docstring.
        "mode",
        ["none", "proportional", "preserve_physical", "manual_ppm"],
    )
    def test_map_scaling_factors_modes(self, mode: str) -> None:
        """MapScalingFactors accepts each documented mode + per-axis multiplier."""  # WHY: parametrized round-trip.
        factors = MapScalingFactors(mode=mode, x_factor=1.5, y_factor=1.25)  # WHY: build for the mode under test.
        assert factors.mode == mode  # WHY: mode field round-trips.
        assert factors.x_factor == 1.5  # WHY: x multiplier round-trips.
        assert factors.y_factor == 1.25  # WHY: y multiplier round-trips.

    def test_map_scaling_factors_is_frozen(self) -> None:
        """MapScalingFactors rejects mutation."""  # WHY: frozen guard.
        factors = MapScalingFactors(mode="none", x_factor=1.0, y_factor=1.0)  # WHY: identity-scale instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            factors.mode = "proportional"  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_original_map_metrics_round_trip(self) -> None:
        """OriginalMapMetrics stores pre-replacement pixel + physical size."""  # WHY: four-field round-trip.
        metrics = OriginalMapMetrics(
            width_px=500, height_px=400, ppm=10.0, width_m=50.0
        )  # WHY: realistic pre-map values.
        assert metrics.width_px == 500  # WHY: int field round-trips.
        assert metrics.height_px == 400  # WHY: int field round-trips.
        assert metrics.ppm == 10.0  # WHY: float field round-trips.
        assert metrics.width_m == 50.0  # WHY: float field round-trips.

    def test_original_map_metrics_is_frozen(self) -> None:
        """OriginalMapMetrics rejects mutation."""  # WHY: frozen guard.
        metrics = OriginalMapMetrics(width_px=0, height_px=0, ppm=0.0, width_m=0.0)  # WHY: minimal instance.
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            metrics.ppm = 15.0  # type: ignore[misc]  # WHY: verify frozen contract.

    def test_scale_choice_context_round_trip(self) -> None:
        """ScaleChoiceContext carries the 5 wizard-choice inputs."""  # WHY: five-field round-trip.
        ctx = ScaleChoiceContext(  # WHY: build with realistic ratio + PPM inputs.
            width_ratio=2.0,
            height_ratio=1.5,
            original_ppm=10.0,
            original_width_m=50.0,
            new_width_px=1000,
        )
        assert ctx.width_ratio == 2.0  # WHY: float field round-trips.
        assert ctx.height_ratio == 1.5  # WHY: float field round-trips.
        assert ctx.original_ppm == 10.0  # WHY: float field round-trips.
        assert ctx.original_width_m == 50.0  # WHY: float field round-trips.
        assert ctx.new_width_px == 1000  # WHY: int field round-trips.

    def test_scale_choice_context_is_frozen(self) -> None:
        """ScaleChoiceContext rejects mutation."""  # WHY: frozen guard.
        ctx = ScaleChoiceContext(  # WHY: minimal instance to trigger the frozen guard.
            width_ratio=1.0,
            height_ratio=1.0,
            original_ppm=10.0,
            original_width_m=10.0,
            new_width_px=100,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):  # WHY: mutation must raise.
            ctx.new_width_px = 200  # type: ignore[misc]  # WHY: verify frozen contract.
