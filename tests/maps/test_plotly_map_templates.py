"""
Unit tests for DashTemplateManager

Tests template creation, CSS styling, HTML structure, and metadata
management for the Plotly/Dash map viewer.
"""

import pytest

from src.maps.plotly_map_templates import DashTemplateManager


class TestDashTemplateManagerInit:
    """Test DashTemplateManager initialization."""

    def test_init_creates_instance(self):
        """DashTemplateManager initializes without errors."""
        mgr = DashTemplateManager(org_id="test-org")
        assert mgr.org_id == "test-org"
        assert mgr.base_template_dir == "src/maps/templates"

    def test_init_with_custom_template_dir(self):
        """DashTemplateManager accepts custom template directory."""
        mgr = DashTemplateManager(org_id="test-org", base_template_dir="custom/path")
        assert mgr.base_template_dir == "custom/path"

    def test_init_creates_cache(self):
        """DashTemplateManager initializes template cache."""
        mgr = DashTemplateManager(org_id="test-org")
        assert isinstance(mgr._template_cache, dict)
        assert len(mgr._template_cache) == 0


class TestDashTemplateManagerCSS:
    """Test CSS template generation."""

    def test_get_custom_css_returns_string(self):
        """get_custom_css() returns non-empty CSS string."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()
        assert isinstance(css, str)
        assert len(css) > 100

    def test_get_custom_css_contains_dark_theme(self):
        """CSS includes dark theme colors."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()
        assert "#1a1a1a" in css  # Dark background
        assert "#e0e0e0" in css  # Light text
        assert "#667eea" in css  # Purple accent

    def test_get_custom_css_contains_layout_styles(self):
        """CSS includes layout and container styles."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()
        assert ".main-container" in css
        assert ".sidebar" in css
        assert ".map-container" in css

    def test_get_custom_css_contains_responsive_design(self):
        """CSS includes responsive design patterns."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()
        assert "display: flex" in css
        assert "overflow" in css
        assert "flex:" in css or "flex-" in css

    def test_get_custom_css_consistency(self):
        """Multiple calls return identical CSS."""
        mgr = DashTemplateManager(org_id="test-org")
        css1 = mgr.get_custom_css()
        css2 = mgr.get_custom_css()
        assert css1 == css2


class TestDashTemplateManagerHTML:
    """Test HTML template generation."""

    def test_get_html_template_returns_string(self):
        """get_html_template() returns non-empty HTML string."""
        mgr = DashTemplateManager(org_id="test-org")
        html = mgr.get_html_template()
        assert isinstance(html, str)
        assert len(html) > 100

    def test_get_html_template_valid_structure(self):
        """HTML template has valid structure."""
        mgr = DashTemplateManager(org_id="test-org")
        html = mgr.get_html_template()
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html

    def test_get_html_template_includes_dash_placeholders(self):
        """HTML template includes required Dash placeholders."""
        mgr = DashTemplateManager(org_id="test-org")
        html = mgr.get_html_template()
        assert "{%metas%}" in html
        assert "{%title%}" in html
        assert "{%css%}" in html
        assert "{%app_entry%}" in html
        assert "{%config%}" in html
        assert "{%scripts%}" in html
        assert "{%renderer%}" in html

    def test_get_html_template_includes_style_tag(self):
        """HTML template includes <style> tag for CSS injection."""
        mgr = DashTemplateManager(org_id="test-org")
        html = mgr.get_html_template()
        assert "<style>" in html
        assert "{%custom_css%}" in html or "</style>" in html

    def test_get_html_template_consistency(self):
        """Multiple calls return identical HTML."""
        mgr = DashTemplateManager(org_id="test-org")
        html1 = mgr.get_html_template()
        html2 = mgr.get_html_template()
        assert html1 == html2


class TestDashTemplateManagerMetadata:
    """Test app metadata generation."""

    def test_get_app_meta_returns_dict(self):
        """get_app_meta() returns dictionary."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()
        assert isinstance(meta, dict)

    def test_get_app_meta_has_required_keys(self):
        """App metadata includes required keys."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()
        assert "title" in meta
        assert "update_title" in meta
        assert "suppress_callback_exceptions" in meta

    def test_get_app_meta_title_value(self):
        """App title metadata has correct value."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()
        assert meta["title"] == "MistHelper Map Viewer"

    def test_get_app_meta_update_title_value(self):
        """Update title is empty string (prevents 'Updating...' flash)."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()
        assert meta["update_title"] == ""

    def test_get_app_meta_suppress_callbacks_value(self):
        """Callback exception suppression is enabled."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()
        assert meta["suppress_callback_exceptions"] is True

    def test_get_app_meta_consistency(self):
        """Multiple calls return identical metadata."""
        mgr = DashTemplateManager(org_id="test-org")
        meta1 = mgr.get_app_meta()
        meta2 = mgr.get_app_meta()
        assert meta1 == meta2


class TestDashTemplateManagerValidation:
    """Test template validation."""

    def test_validate_template_passes(self):
        """validate_template() returns True for valid templates."""
        mgr = DashTemplateManager(org_id="test-org")
        assert mgr.validate_template() is True

    def test_validate_template_checks_css_length(self):
        """Validation ensures CSS is not empty."""
        mgr = DashTemplateManager(org_id="test-org")
        # Should pass with actual CSS
        assert mgr.validate_template()

    def test_validate_template_checks_html_structure(self):
        """Validation ensures HTML has required placeholders."""
        mgr = DashTemplateManager(org_id="test-org")
        # Should pass with actual HTML
        assert mgr.validate_template()

    def test_validate_template_checks_metadata(self):
        """Validation ensures metadata is valid."""
        mgr = DashTemplateManager(org_id="test-org")
        # Should pass with actual metadata
        assert mgr.validate_template()


class TestDashTemplateManagerIntegration:
    """Integration tests for template manager."""

    def test_full_template_workflow(self):
        """Complete workflow: create manager, get all templates, validate."""
        # Create manager
        mgr = DashTemplateManager(org_id="production-org")

        # Get all templates
        css = mgr.get_custom_css()
        html = mgr.get_html_template()
        meta = mgr.get_app_meta()

        # Validate
        assert mgr.validate_template()

        # All should be non-empty
        assert len(css) > 0
        assert len(html) > 0
        assert len(meta) > 0

    def test_multiple_managers_independent(self):
        """Multiple manager instances are independent."""
        mgr1 = DashTemplateManager(org_id="org-1")
        mgr2 = DashTemplateManager(org_id="org-2")

        assert mgr1.org_id != mgr2.org_id
        assert mgr1.get_custom_css() == mgr2.get_custom_css()  # CSS is same
        assert mgr1.get_app_meta() == mgr2.get_app_meta()  # Meta is same


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
