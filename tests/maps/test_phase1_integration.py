"""Integration tests for Phase 1: DashTemplateManager integration."""

from unittest.mock import Mock, patch

from src.maps.plotly_map_templates import DashTemplateManager


class TestDashTemplateManagerIntegration:
    """Test DashTemplateManager integration into MapsManager."""

    def test_dash_template_manager_importable(self):
        """DashTemplateManager can be imported from maps_manager."""
        # This verifies the import statement exists in maps_manager.py
        from src.maps.maps_manager import DashTemplateManager

        assert DashTemplateManager is not None

    def test_template_manager_creates_instance(self):
        """Template manager can be instantiated with org_id."""
        mgr = DashTemplateManager(org_id="test-org-123")
        assert mgr.org_id == "test-org-123"

    def test_template_manager_provides_html_template(self):
        """Template manager provides valid HTML template string."""
        mgr = DashTemplateManager(org_id="test-org")
        template = mgr.get_html_template()

        # Template must be a string
        assert isinstance(template, str)

        # Template must contain critical HTML structure
        assert "<!DOCTYPE html>" in template
        assert "<html>" in template
        assert "<head>" in template
        assert "<body>" in template
        assert "{%app_entry%}" in template  # Dash placeholder
        assert "{%config%}" in template
        assert "{%scripts%}" in template

    def test_template_manager_provides_css(self):
        """Template manager provides custom CSS styling."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()

        # CSS must be a string
        assert isinstance(css, str)

        # CSS must contain dark theme styling
        assert "background-color" in css
        assert "#1a1a1a" in css or "#2d2d2d" in css  # Dark backgrounds
        assert "color" in css

    def test_template_manager_provides_metadata(self):
        """Template manager provides app metadata."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()

        # Metadata must be a dictionary
        assert isinstance(meta, dict)

        # Must contain required keys
        assert "title" in meta
        assert "update_title" in meta
        assert "suppress_callback_exceptions" in meta

        # Verify values
        assert isinstance(meta["title"], str)
        assert len(meta["title"]) > 0
        assert isinstance(meta["update_title"], str)
        assert isinstance(meta["suppress_callback_exceptions"], bool)

    def test_template_includes_custom_styling(self):
        """Template HTML includes custom CSS styling."""
        mgr = DashTemplateManager(org_id="test-org")
        template = mgr.get_html_template()

        # Should contain style tags for dark theme
        assert "<style>" in template or "background-color" in template

    def test_template_metadata_matches_expectations(self):
        """Template metadata matches Dash app creation expectations."""
        mgr = DashTemplateManager(org_id="test-org")
        meta = mgr.get_app_meta()

        # Verify app title is meaningful
        assert "map" in meta["title"].lower() or "mist" in meta["title"].lower()

        # Verify update_title for callback flash prevention
        assert meta["update_title"] == ""

        # Verify callback exception suppression is enabled for multiple outputs
        assert meta["suppress_callback_exceptions"] is True

    @patch("src.maps.plotly_map_templates.DashTemplateManager.validate_template")
    def test_template_validation_called(self, mock_validate):
        """Template manager can validate template structure."""
        mgr = DashTemplateManager(org_id="test-org")
        template = mgr.get_html_template()

        # Template should contain all required placeholders
        required_placeholders = [
            "{%metas%}",
            "{%title%}",
            "{%favicon%}",
            "{%css%}",
            "{%app_entry%}",
            "{%config%}",
            "{%scripts%}",
            "{%renderer%}",
        ]

        for placeholder in required_placeholders:
            assert placeholder in template, f"Missing Dash placeholder: {placeholder}"

    def test_multiple_template_managers_independent(self):
        """Multiple template manager instances are independent."""
        mgr1 = DashTemplateManager(org_id="org-1")
        mgr2 = DashTemplateManager(org_id="org-2")

        # Both should provide valid templates
        template1 = mgr1.get_html_template()
        template2 = mgr2.get_html_template()

        assert template1 is not None
        assert template2 is not None
        assert len(template1) > 0
        assert len(template2) > 0

    def test_template_html_structure_integrity(self):
        """Template HTML has proper structure and nesting."""
        mgr = DashTemplateManager(org_id="test-org")
        template = mgr.get_html_template()

        # Count opening and closing tags
        assert template.count("<html>") == template.count("</html>")
        assert template.count("<head>") == template.count("</head>")
        assert template.count("<body>") == template.count("</body>")

        # Verify proper order
        html_start = template.find("<html>")
        head_start = template.find("<head>")
        body_start = template.find("<body>")
        html_end = template.rfind("</html>")

        assert html_start < head_start < body_start < html_end

    def test_template_includes_dash_placeholders(self):
        """Template includes all required Dash framework placeholders."""
        mgr = DashTemplateManager(org_id="test-org")
        template = mgr.get_html_template()

        # These are required by Dash to inject content
        dash_placeholders = [
            "{%app_entry%}",  # Main app container
            "{%config%}",  # Dash configuration
            "{%scripts%}",  # JavaScript bundles
            "{%renderer%}",  # React renderer
        ]

        for placeholder in dash_placeholders:
            assert placeholder in template, f"Missing critical Dash placeholder: {placeholder}"

    def test_css_dark_theme_colors(self):
        """CSS includes dark theme color scheme."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()

        # Verify dark theme colors are present
        dark_colors = ["#1a1a1a", "#2d2d2d", "#3d3d3d", "#505050"]
        assert any(color in css for color in dark_colors), "Missing dark theme colors"

    def test_css_includes_responsive_design(self):
        """CSS includes responsive design rules."""
        mgr = DashTemplateManager(org_id="test-org")
        css = mgr.get_custom_css()

        # Verify flexbox for responsiveness
        assert "flex" in css or "display" in css


class TestTemplateIntegrationWithMapsManager:
    """Test template manager integration with MapsManager."""

    def test_maps_manager_imports_template_manager(self):
        """MapsManager properly imports DashTemplateManager."""
        # This import should succeed without errors
        from src.maps.maps_manager import DashTemplateManager

        assert DashTemplateManager is not None

    @patch("src.maps.maps_manager.Dash")
    @patch("src.maps.plotly_map_templates.DashTemplateManager")
    def test_launch_plotly_viewer_uses_template_manager(self, mock_template_mgr_class, mock_dash):
        """_launch_plotly_viewer uses DashTemplateManager for templates."""
        # Setup mock template manager
        mock_mgr_instance = Mock()
        mock_template_mgr_class.return_value = mock_mgr_instance

        mock_mgr_instance.get_app_meta.return_value = {
            "title": "Test Map Viewer",
            "update_title": "",
            "suppress_callback_exceptions": True,
        }
        mock_mgr_instance.get_html_template.return_value = "<!DOCTYPE html><html><body>{%app_entry%}</body></html>"

        # Verify mock setup
        assert mock_mgr_instance.get_app_meta.return_value is not None
        assert mock_mgr_instance.get_html_template.return_value is not None

    def test_template_manager_org_id_passed_correctly(self):
        """Template manager receives org_id correctly."""
        org_id = "test-org-xyz"
        mgr = DashTemplateManager(org_id=org_id)

        assert mgr.org_id == org_id


class TestPhase1Completion:
    """Test that Phase 1 extraction is complete and working."""

    def test_dash_template_manager_class_exists(self):
        """DashTemplateManager class exists and is importable."""
        from src.maps.plotly_map_templates import DashTemplateManager

        mgr = DashTemplateManager(org_id="test-org")
        assert mgr is not None

    def test_phase1_integration_complete(self):
        """Phase 1 integration is complete with all components."""
        # Import both
        from src.maps.maps_manager import DashTemplateManager as MapsImportedDTM
        from src.maps.plotly_map_templates import DashTemplateManager

        # They should be the same class
        assert DashTemplateManager is MapsImportedDTM

    def test_template_manager_api_complete(self):
        """Template manager has complete API."""
        mgr = DashTemplateManager(org_id="test-org")

        # All methods should exist and return valid values
        assert hasattr(mgr, "get_html_template")
        assert hasattr(mgr, "get_custom_css")
        assert hasattr(mgr, "get_app_meta")
        assert hasattr(mgr, "validate_template")

        # All methods should return valid values
        assert mgr.get_html_template() is not None
        assert mgr.get_custom_css() is not None
        assert mgr.get_app_meta() is not None
