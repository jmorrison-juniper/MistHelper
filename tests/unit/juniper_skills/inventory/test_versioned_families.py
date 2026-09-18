"""Tests for Juniper inventory versioned family resolution."""

from pathlib import Path  # Use Path to create realistic source roots.

from src.juniper_skills.inventory.engine import VersionedFamilyResolver  # Test the production version resolver.
from src.juniper_skills.inventory.models import DocumentGroup, MarkdownPart, SourceRoot  # Build inventory records.


class TestVersionedFamilyResolver:
    """Verify current and superseded version handling."""

    def test_compares_versions_numerically(self, tmp_path: Path) -> None:
        old = self._group(tmp_path, "Juniper Routing Director 2.9.0 User Guide", 2095)  # Build version 2.9.0.
        current = self._group(tmp_path, "Juniper Routing Director 2.10.0 User Guide", 2191)  # Build version 2.10.0.
        families = VersionedFamilyResolver().resolve([old, current])  # Resolve the versioned family.
        assert families[0].current_version == "2.10.0"  # Numeric order must put 2.10.0 above 2.9.0.
        assert old.version_status == "superseded"  # Older versions must stay citable but skip topic builds.
        assert current.build_topics is True  # The newest version must remain eligible for topic generation.

    def test_uses_newest_version_in_multi_version_title(self, tmp_path: Path) -> None:
        group = self._group(tmp_path, "Juniper Apstra 4.2.2 / 4.2.1 / 4.2.0 User Guide", 1663)  # Build multi-title.
        VersionedFamilyResolver().resolve(
            [group, self._group(tmp_path, "Juniper Apstra 5.1 User Guide", 1935)]
        )  # Resolve.
        assert group.version_value == "4.2.2"  # The resolver must keep the newest version named in one title.

    def test_groups_hpe_apstra_rebrand_with_juniper_apstra(self, tmp_path: Path) -> None:
        hpe = self._group(
            tmp_path, "HPE Networking Apstra Data Center Director 6.2 User Guide", 2237
        )  # Build HPE title.
        juniper = self._group(tmp_path, "Juniper Apstra 6.1 User Guide", 2158)  # Build Juniper title.
        families = VersionedFamilyResolver().resolve([hpe, juniper])  # Resolve the rebranded family.
        assert families[0].family_key == "apstra-user-guide"  # The safe rebrand rule must join Apstra user guides.
        assert families[0].current_version == "6.2"  # The rebranded HPE document is the current version.

    def _group(self, tmp_path: Path, title: str, pages: int) -> DocumentGroup:
        root = SourceRoot("harvest", tmp_path, 3)  # Use one root because the resolver works after deduplication.
        part = self._part(root, title, pages)  # Create one physical part for the document.
        return DocumentGroup(title, title, "guides", f"{title}.pdf", root, [part], pages, "ok", "source_file")

    def _part(self, root: SourceRoot, title: str, pages: int) -> MarkdownPart:
        return MarkdownPart(title, root, root.path / "doc.md", "doc.md", "hash", 1, 1, {}, {"title": title}, "ok")
