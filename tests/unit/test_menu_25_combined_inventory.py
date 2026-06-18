"""Unit tests for Menu 25 combined inventory weekly export refactor."""

import MistHelper


class TestCombinedInventoryHelpers:
    """Verify helper behavior for in-place combined inventory refactor."""

    def test_partition_combined_inventory_rows_identifies_empty_vc_shells(self):
        """Virtual VC placeholders split cleanly from physical devices."""
        all_devices = [
            {"mac": "020003aaaaaa", "vc_mac": "", "serial": ""},
            {"mac": "001122334455", "vc_mac": "020003bbbbbb", "serial": "SN1"},
            {"mac": "020003bbbbbb", "vc_mac": "", "serial": ""},
        ]

        site_configs, empty_vc_shells, duplicate_vc_entries = MistHelper.OrgInventoryExporter._partition_combined_inventory_rows(all_devices)

        assert len(site_configs) == 1
        assert len(empty_vc_shells) == 1
        assert empty_vc_shells[0]["mac"] == "020003aaaaaa"
        assert duplicate_vc_entries == 1

    def test_build_combined_inventory_weekly_data_groups_rows(self):
        """Devices are grouped into ISO week buckets and summary counts."""
        site_configs = [
            {
                "created_time": "1714521600",
                "site_name": "SiteA",
                "serial": "SN1",
                "mac": "001122334455",
                "model": "AP32",
                "street": "123 Main",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80202",
                "country": "US",
            }
        ]

        weekly_data, summary_data = MistHelper.OrgInventoryExporter._build_combined_inventory_weekly_data(site_configs, "Customer", "ACC-1")

        assert len(weekly_data) == 1
        only_rows = next(iter(weekly_data.values()))
        assert only_rows[0]["End Customer Name"] == "Customer"
        assert sum(summary_data.values()) == 1

    def test_build_safe_org_name_replaces_unsafe_characters(self):
        """Unsafe filename characters are normalized to underscores."""
        assert MistHelper.OrgInventoryExporter._build_safe_org_name("Org Name/West") == "Org_Name_West"


class TestCombinedInventoryOrchestration:
    """Verify top-level method orchestrates helper calls without wrapper extraction."""

    def test_combined_inventory_with_site_info_calls_helpers(self, monkeypatch):
        """Top-level method invokes refresh, grouping, and writers."""
        helper_calls = {"refresh": 0, "json": 0, "weekly": 0, "summary": 0, "master": 0}

        monkeypatch.setattr(MistHelper, "load_dotenv", lambda: None)
        monkeypatch.setattr(MistHelper.os, "getenv", lambda name: {"END_CUSTOMER_NAME": "Cust", "END_CUSTOMER_ACCOUNT_ID": "Acct"}.get(name))
        monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1")
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_resolve_combined_inventory_org_name", lambda current_org_id, fallback_org_name: "Org")
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_build_safe_org_name", lambda name: "Org")
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "devices_with_site_info", lambda: helper_calls.__setitem__("refresh", helper_calls["refresh"] + 1))
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_export_combined_inventory_raw_json", lambda output_folder, current_org_id: helper_calls.__setitem__("json", helper_calls["json"] + 1))
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_load_combined_inventory_rows", lambda: [{"created_time": "1714521600", "serial": "SN1", "mac": "001", "model": "AP", "street": "A", "city": "B", "state": "C", "zip_code": "1", "country": "US", "site_name": "Site"}])
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_partition_combined_inventory_rows", lambda rows: (rows, [], 0))
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_log_combined_inventory_vc_summary", lambda all_devices, site_configs, empty_vc_shells, duplicate_vc_entries: None)
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_build_combined_inventory_weekly_data", lambda site_configs, end_customer_name, end_customer_account_id: ({"2024_Week_18": [{"x": 1}]}, {(2024, 18): 1}))
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_write_combined_inventory_weekly_csvs", lambda output_folder, fieldnames, weekly_data: helper_calls.__setitem__("weekly", helper_calls["weekly"] + 1))
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_write_combined_inventory_summary", lambda output_folder, summary_data: helper_calls.__setitem__("summary", helper_calls["summary"] + 1))
        monkeypatch.setattr(MistHelper.OrgInventoryExporter, "_write_combined_inventory_master_csv", lambda output_folder, safe_org_name, site_configs: (helper_calls.__setitem__("master", helper_calls["master"] + 1) or ("Org_CombinedInventory_Master.csv", 1)))

        MistHelper.OrgInventoryExporter.combined_inventory_with_site_info()

        assert helper_calls == {"refresh": 1, "json": 1, "weekly": 1, "summary": 1, "master": 1}
