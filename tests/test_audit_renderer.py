"""Tests for src.audit.renderer module."""

import os
import tempfile

import pytest

from src.audit._renderer_delta import DiffKeyContext
from src.audit.analyzer import AdminTimeline, AuditAnalysisResult, ObjectChange, ObjectChangelog, RollbackDiff
from src.audit.renderer import AuditReportRenderer


@pytest.fixture
def renderer():
    return AuditReportRenderer()


@pytest.fixture
def sample_result():
    """Minimal analysis result for rendering tests."""
    timeline = AdminTimeline(
        admin_name="alice@corp.com",
        admin_id="uid-alice",
        entries=[
            {"timestamp": 1700000000, "message": 'Update Device "switch-1"'},
            {"timestamp": 1700000100, "message": 'Update Device "switch-2"'},
        ],
        first_action=1700000000,
        last_action=1700000100,
        action_count=2,
    )
    changelog = ObjectChangelog(
        object_name="switch-1",
        object_type="Device",
        changes=[
            ObjectChange(
                timestamp=1700000000,
                admin_name="alice@corp.com",
                message='Update Device "switch-1"',
                before={"vlan": 10},
                after={"vlan": 20},
            ),
        ],
    )
    rollback = RollbackDiff(
        object_name="switch-1",
        object_type="Device",
        original_state={"vlan": 10},
        final_state={"vlan": 20},
        fields_changed=["vlan"],
        net_changed=True,
    )
    return AuditAnalysisResult(
        admin_timelines=[timeline],
        object_changelogs=[changelog],
        rollback_diffs=[rollback],
        time_range_description="Last 3 days",
        total_entries=2,
        filtered_entries=2,
    )


class TestMermaidRendering:
    """Test Mermaid markdown report generation."""

    def test_creates_file(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.md")
            renderer.render_mermaid(sample_result, path)
            assert os.path.exists(path)

    def test_contains_header(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.md")
            renderer.render_mermaid(sample_result, path)
            content = open(path, encoding="utf-8").read()
            assert "Org Audit Log Analysis" in content
            assert "Last 3 days" in content

    def test_contains_mermaid_graph(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.md")
            renderer.render_mermaid(sample_result, path)
            content = open(path, encoding="utf-8").read()
            assert "```mermaid" in content
            assert "graph TD" in content

    def test_contains_rollback_table(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.md")
            renderer.render_mermaid(sample_result, path)
            content = open(path, encoding="utf-8").read()
            assert "Rollback Summary" in content
            assert "switch-1" in content
            assert "vlan" in content


class TestHtmlRendering:
    """Test HTML report generation."""

    def test_creates_file(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.html")
            renderer.render_html(sample_result, path)
            assert os.path.exists(path)

    def test_contains_plotly(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.html")
            renderer.render_html(sample_result, path)
            content = open(path, encoding="utf-8").read()
            assert "plotly-latest.min.js" in content
            assert "Plotly.newPlot" in content

    def test_contains_stats(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.html")
            renderer.render_html(sample_result, path)
            content = open(path, encoding="utf-8").read()
            assert "Events Analyzed" in content
            assert "Admins Active" in content

    def test_self_contained_html(self, renderer, sample_result):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.html")
            renderer.render_html(sample_result, path)
            content = open(path, encoding="utf-8").read()
            assert content.startswith("<!DOCTYPE html>")
            assert "</html>" in content

    def test_no_empty_result(self, renderer):
        empty = AuditAnalysisResult(time_range_description="Test")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.html")
            renderer.render_html(empty, path)
            content = open(path, encoding="utf-8").read()
            assert "No net changes detected" in content


class TestComputeDelta:
    """Test delta computation between before/after dicts."""

    def test_both_empty(self):
        delta_b, delta_a = AuditReportRenderer._compute_delta({}, {})
        assert delta_b == {}
        assert delta_a == {}

    def test_before_empty(self):
        delta_b, delta_a = AuditReportRenderer._compute_delta({}, {"a": 1})
        assert delta_b == {}
        assert delta_a == {"a": 1}

    def test_after_empty(self):
        delta_b, delta_a = AuditReportRenderer._compute_delta({"a": 1}, {})
        assert delta_b == {"a": 1}
        assert delta_a == {}

    def test_same_values_no_delta(self):
        delta_b, delta_a = AuditReportRenderer._compute_delta({"a": 1}, {"a": 1})
        assert delta_b == {}
        assert delta_a == {}

    def test_simple_diff(self):
        delta_b, delta_a = AuditReportRenderer._compute_delta({"a": 1}, {"a": 2})
        assert delta_b == {"a": 1}
        assert delta_a == {"a": 2}

    def test_nested_dict_diff(self):
        before = {"config": {"vlan": 10, "name": "test"}}
        after = {"config": {"vlan": 20, "name": "test"}}
        delta_b, delta_a = AuditReportRenderer._compute_delta(before, after)
        assert delta_b == {"config": {"vlan": 10}}
        assert delta_a == {"config": {"vlan": 20}}

    def test_added_key(self):
        delta_b, delta_a = AuditReportRenderer._compute_delta({"a": 1}, {"a": 1, "b": 2})
        assert "b" not in delta_b
        assert delta_a["b"] == 2

    def test_removed_key(self):
        delta_b, delta_a = AuditReportRenderer._compute_delta({"a": 1, "b": 2}, {"a": 1})
        assert delta_b["b"] == 2
        assert "b" not in delta_a

    def test_list_diff(self):
        before = {"ports": [1, 2, 3]}
        after = {"ports": [1, 2, 4]}
        delta_b, delta_a = AuditReportRenderer._compute_delta(before, after)
        assert delta_b["ports"] == [1, 2, 3]
        assert delta_a["ports"] == [1, 2, 4]


class TestComputeDeltaList:
    """Test list delta computation."""

    def test_equal_lists(self):
        result_b, result_a = AuditReportRenderer._compute_delta_list([1, 2], [1, 2])
        assert result_b is None
        assert result_a is None

    def test_non_dict_lists(self):
        result_b, result_a = AuditReportRenderer._compute_delta_list([1, 2], [3, 4])
        assert result_b == [1, 2]
        assert result_a == [3, 4]

    def test_dict_lists_by_identity(self):
        before = [{"name": "a", "val": 1}]
        after = [{"name": "a", "val": 2}]
        result_b, result_a = AuditReportRenderer._compute_delta_list(before, after)
        assert result_b is not None
        assert result_a is not None


class TestElementIdentity:
    """Test identity extraction from dict elements."""

    def test_name_key(self):
        assert AuditReportRenderer._element_identity({"name": "test"}) == "name=test"

    def test_id_key(self):
        assert AuditReportRenderer._element_identity({"id": "abc"}) == "id=abc"

    def test_ssid_key(self):
        assert AuditReportRenderer._element_identity({"ssid": "corp"}) == "ssid=corp"

    def test_no_identity(self):
        assert AuditReportRenderer._element_identity({"random": "val"}) is None

    def test_priority_name_over_id(self):
        result = AuditReportRenderer._element_identity({"name": "n", "id": "i"})
        assert result == "name=n"


class TestBuildIdentityMap:
    """Test identity map construction."""

    def test_all_identified(self):
        elements = [{"name": "a", "v": 1}, {"name": "b", "v": 2}]
        id_map, anon = AuditReportRenderer._build_identity_map(elements)
        assert len(id_map) == 2
        assert len(anon) == 0

    def test_duplicate_identity_goes_anon(self):
        elements = [{"name": "a", "v": 1}, {"name": "a", "v": 2}]
        id_map, anon = AuditReportRenderer._build_identity_map(elements)
        assert len(id_map) == 1
        assert len(anon) == 1

    def test_no_identity_all_anon(self):
        elements = [{"x": 1}, {"y": 2}]
        id_map, anon = AuditReportRenderer._build_identity_map(elements)
        assert len(id_map) == 0
        assert len(anon) == 2


class TestDiffIdentified:
    """Test identified element diffing."""

    def test_changed_element(self):
        before_map = {"name=a": {"name": "a", "val": 1}}
        after_map = {"name=a": {"name": "a", "val": 2}}
        delta_b: list[dict[str, object]] = []
        delta_a: list[dict[str, object]] = []
        AuditReportRenderer._diff_identified(before_map, after_map, delta_b, delta_a)
        assert len(delta_b) == 1
        assert len(delta_a) == 1

    def test_removed_element(self):
        before_map = {"name=a": {"name": "a", "val": 1}}
        after_map: dict[str, dict[str, object]] = {}
        delta_b: list[dict[str, object]] = []
        delta_a: list[dict[str, object]] = []
        AuditReportRenderer._diff_identified(before_map, after_map, delta_b, delta_a)
        assert delta_a[0] == {"_status": "(removed)"}

    def test_added_element(self):
        before_map: dict[str, dict[str, object]] = {}
        after_map = {"name=b": {"name": "b", "val": 2}}
        delta_b: list[dict[str, object]] = []
        delta_a: list[dict[str, object]] = []
        AuditReportRenderer._diff_identified(before_map, after_map, delta_b, delta_a)
        assert delta_b[0] == {"_status": "(added)"}


class TestDiffAnonymous:
    """Test anonymous element diffing."""

    def test_positional_diff(self):
        before = [{"x": 1}]
        after = [{"x": 2}]
        delta_b: list[dict[str, object]] = []
        delta_a: list[dict[str, object]] = []
        AuditReportRenderer._diff_anonymous(before, after, delta_b, delta_a)
        assert len(delta_b) == 1

    def test_extra_before_marked_removed(self):
        before = [{"x": 1}, {"x": 2}]
        after: list[dict[str, object]] = []
        delta_b: list[dict[str, object]] = []
        delta_a: list[dict[str, object]] = []
        AuditReportRenderer._diff_anonymous(before, after, delta_b, delta_a)
        assert any(d.get("_status") == "(removed)" for d in delta_a)

    def test_extra_after_marked_added(self):
        before: list[dict[str, object]] = []
        after = [{"x": 1}]
        delta_b: list[dict[str, object]] = []
        delta_a: list[dict[str, object]] = []
        AuditReportRenderer._diff_anonymous(before, after, delta_b, delta_a)
        assert any(d.get("_status") == "(added)" for d in delta_b)


class TestCheckReorder:
    """Test reorder detection."""

    def test_no_reorder_same_order(self):
        before_map = {"name=a": {"name": "a"}, "name=b": {"name": "b"}}
        after_map = {"name=a": {"name": "a"}, "name=b": {"name": "b"}}
        result = AuditReportRenderer._check_reorder(before_map, after_map)
        assert result == (None, None)

    def test_detects_reorder(self):
        before_map = {"name=a": {"name": "a"}, "name=b": {"name": "b"}}
        after_map = {"name=b": {"name": "b"}, "name=a": {"name": "a"}}
        result_b, result_a = AuditReportRenderer._check_reorder(before_map, after_map)
        assert result_b is not None
        assert result_a is not None
        assert "_reordered" in str(result_b)


class TestDeltaByIdentity:
    """Test full delta-by-identity flow."""

    def test_changed_named_element(self):
        before = [{"name": "x", "val": 1}]
        after = [{"name": "x", "val": 2}]
        result_b, result_a = AuditReportRenderer._delta_by_identity(before, after)
        assert result_b is not None
        assert result_a is not None

    def test_identical_returns_none(self):
        items = [{"name": "x", "val": 1}]
        result_b, result_a = AuditReportRenderer._delta_by_identity(items, items)
        assert result_b is None
        assert result_a is None


class TestFormatDeltaHtml:
    """Test HTML delta formatting."""

    def test_empty_dict(self):
        assert AuditReportRenderer._format_delta_html({}) == "{}"

    def test_empty_list(self):
        assert AuditReportRenderer._format_delta_html([]) == "[]"

    def test_scalar_bold(self):
        result = AuditReportRenderer._format_delta_html(42)
        assert "<b>" in result
        assert "42" in result

    def test_dict_with_keys(self):
        result = AuditReportRenderer._format_delta_html({"key": "val"})
        assert "key" in result
        assert "<b>" in result

    def test_list_with_items(self):
        result = AuditReportRenderer._format_delta_html([1, 2])
        assert "[" in result
        assert "<b>" in result

    def test_nested_structure(self):
        result = AuditReportRenderer._format_delta_html({"a": {"b": 1}})
        assert "<b>" in result


class TestHelpers:
    """Test small helper functions."""

    def test_reorder_label(self):
        label = AuditReportRenderer._reorder_label(["name=a", "name=b"])
        assert "_reordered" in label
        assert "name" in label

    def test_strip_id_prefix(self):
        assert AuditReportRenderer._strip_id_prefix("name=test") == "test"
        assert AuditReportRenderer._strip_id_prefix("noeq") == "noeq"

    def test_epoch_to_readable_zero(self):
        assert AuditReportRenderer._epoch_to_readable(0) == "N/A"

    def test_epoch_to_readable_valid(self):
        result = AuditReportRenderer._epoch_to_readable(1700000000)
        assert "2023" in result
        assert "UTC" in result

    def test_epoch_to_short_zero(self):
        assert AuditReportRenderer._epoch_to_short(0) == "?"

    def test_epoch_to_short_valid(self):
        result = AuditReportRenderer._epoch_to_short(1700000000)
        assert ":" in result


class TestDiffKey:
    """Test _diff_key dispatch."""

    def test_dict_values(self):
        delta_b: dict[str, object] = {}
        delta_a: dict[str, object] = {}
        ctx = DiffKeyContext(key="cfg", val_b={"a": 1}, val_a={"a": 2}, in_before=True, in_after=True)
        AuditReportRenderer._diff_key(ctx, delta_b, delta_a)
        assert "cfg" in delta_b

    def test_list_values(self):
        delta_b: dict[str, object] = {}
        delta_a: dict[str, object] = {}
        ctx = DiffKeyContext(key="ports", val_b=[1, 2], val_a=[3, 4], in_before=True, in_after=True)
        AuditReportRenderer._diff_key(ctx, delta_b, delta_a)
        assert "ports" in delta_b

    def test_scalar_values(self):
        delta_b: dict[str, object] = {}
        delta_a: dict[str, object] = {}
        ctx = DiffKeyContext(key="v", val_b=1, val_a=2, in_before=True, in_after=True)
        AuditReportRenderer._diff_key(ctx, delta_b, delta_a)
        assert delta_b["v"] == 1
        assert delta_a["v"] == 2
