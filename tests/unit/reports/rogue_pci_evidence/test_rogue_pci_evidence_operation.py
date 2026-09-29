"""Unit tests for the rogue PCI evidence operation."""

from types import SimpleNamespace  # Build small fake dependency objects.

from src.reports.rogue_pci_evidence.operation import RoguePciEvidencePack  # Import the operation under test.


class _FakeConfigUtils:
    """Return a fixed organization id without prompting."""

    @staticmethod
    def get_cached_or_prompted_org_id():
        """Return the test organization identifier."""
        return "org-1"  # Avoid prompts in the operation test.


class _FakeDataExporter:
    """Capture exporter writes in memory."""

    writes = []  # Store write calls for assertions.

    @classmethod
    def write_with_format_selection(cls, rows, filename, api_function_name, fieldnames=None):
        """Record the shared exporter call."""
        cls.writes.append((rows, filename, api_function_name, fieldnames))  # Save the write arguments.
        return True  # Simulate a successful exporter write.


class _FakeFilePathUtils:
    """Capture file path calls in memory."""

    summary_text = ""  # Store summary text through the fake path object.
    data_dir = None  # Store the pytest temporary path for summary writes.

    @staticmethod
    def get_csv_path(filename):
        """Return a fake path object for the summary file."""
        return str(_FakeFilePathUtils.data_dir / filename)  # Use a real temporary file path.

    @staticmethod
    def create_csv_template(filename, headers=None):
        """Record an empty template write."""
        _FakeDataExporter.writes.append(([], filename, None, headers))  # Record empty evidence files.
        return filename  # Return the fake path string.


class _FakeClient:
    """Return deterministic data for the operation."""

    def __init__(self, apisession, org_id, page_limit):
        """Store constructor inputs for parity with the real client."""
        self.apisession = apisession  # Keep the fake session.
        self.org_id = org_id  # Keep the fake organization id.
        self.page_limit = page_limit  # Keep the fake page limit.

    def list_org_wlans(self):
        """Return one organization WLAN."""
        return [{"ssid": "CorpWiFi"}]  # Provide the honeypot SSID.

    def list_org_sites(self):
        """Return one organization site."""
        return [{"id": "site-1", "name": "HQ"}]  # Provide one site.

    def list_site_rogue_aps(self, sites):
        """Return one rogue AP detection."""
        del sites  # The fake data does not need the site list.
        return [{"site_id": "site-1", "ssid": "CorpWiFi", "bssid": "11:22:33:44:55:66"}]  # Provide a honeypot.

    def list_org_rogue_events(self):
        """Return no extra rogue event detections."""
        return []  # Keep the operation test focused on the site rogue AP row.

    def list_site_settings(self, sites):
        """Return one site setting record."""
        del sites  # The fake data does not need the site list.
        return {"site-1": {"rogue": {"enabled": False, "honeypot_enabled": True}}}  # Provide detection-off evidence.


def test_operation_writes_three_outputs_without_prompt(monkeypatch, tmp_path):
    """The operation writes the three evidence files through fakes."""
    _FakeDataExporter.writes = []  # Reset exporter writes.
    _FakeFilePathUtils.data_dir = tmp_path  # Direct the summary to the pytest temp folder.
    fake_deps = SimpleNamespace(  # Build a fake SourceDependencyResolver shape.
        ConfigUtils=_FakeConfigUtils,
        DEFAULT_API_PAGE_LIMIT=1000,
        apisession=object(),
        DataExporter=_FakeDataExporter,
        FilePathUtils=_FakeFilePathUtils,
    )
    monkeypatch.setattr("src.reports.rogue_pci_evidence.operation.SourceDependencyResolver", fake_deps)  # Patch deps.
    monkeypatch.setattr("src.reports.rogue_pci_evidence.operation.RoguePciEvidenceClient", _FakeClient)  # Patch client.
    RoguePciEvidencePack.run()  # Run the operation with no prompt.
    filenames = [write[1] for write in _FakeDataExporter.writes]  # Read the exported file names.
    _FakeFilePathUtils.summary_text = (tmp_path / "RogueEvidenceSummary.md").read_text(
        encoding="utf-8"
    )  # Read summary.
    assert "RogueEvidence.csv" in filenames  # Verify classified evidence output.
    assert "RogueSiteSettings.csv" in filenames  # Verify settings output.
    assert "05-wlan-threat-client-and-pci-controls.md" in _FakeFilePathUtils.summary_text  # Verify summary source.
