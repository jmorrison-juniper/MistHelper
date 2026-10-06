"""Guard tracked Juniper corpus paths and their approved provenance references."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
NEW_CORPUS_ROOT = r"C:\Users\jmorrison\Downloads\juniper-library-md"
OLD_CORPUS_ROOT = r"C:\Users\jmorrison\Downloads\juniper-harvest-md"
OLD_CORPUS_MARKERS = (OLD_CORPUS_ROOT, OLD_CORPUS_ROOT.replace("\\", "\\\\"))
ALLOWLIST = frozenset(
    {
        ("specs/2925-juniper-skill-factory/contracts/domain-taxonomy.md", 13),
        (
            "specs/skills/juniper-evpn-vxlan-fabric/uncategorized-ex-configuration-evpn-vxlan-evpn-pdf/.spec-context.json",
            37,
        ),
        (
            "specs/skills/juniper-evpn-vxlan-fabric/uncategorized-ex-configuration-evpn-vxlan-evpn-pdf/quickstart.md",
            3,
        ),
        (
            "specs/skills/juniper-evpn-vxlan-fabric/uncategorized-ex-configuration-evpn-vxlan-evpn-pdf/spec.md",
            11,
        ),
        (
            "specs/skills/juniper-junos-fundamentals/guides-junos-beginners-guide-pdf/.spec-context.json",
            37,
        ),
        (
            "specs/skills/juniper-junos-fundamentals/guides-junos-beginners-guide-pdf/quickstart.md",
            3,
        ),
        (
            "specs/skills/juniper-junos-fundamentals/guides-junos-beginners-guide-pdf/spec.md",
            11,
        ),
        (
            "specs/skills/juniper-junos-fundamentals/junos-beginners-guide/.spec-context.json",
            91,
        ),
        (
            "specs/skills/juniper-junos-fundamentals/junos-beginners-guide/quickstart.md",
            3,
        ),
        (
            "specs/skills/juniper-junos-fundamentals/junos-beginners-guide/spec.md",
            9,
        ),
        (
            "specs/skills/juniper-security-analytics-compliance/additional-resources-juniper-networks-inc-trademark-usage-guidelines-pdf/.spec-context.json",
            37,
        ),
        (
            "specs/skills/juniper-security-analytics-compliance/additional-resources-juniper-networks-inc-trademark-usage-guidelines-pdf/quickstart.md",
            3,
        ),
        (
            "specs/skills/juniper-security-analytics-compliance/additional-resources-juniper-networks-inc-trademark-usage-guidelines-pdf/spec.md",
            11,
        ),
        (
            "specs/skills/junos/junos-beginners-guide/.spec-context.json",
            91,
        ),
        ("specs/skills/junos/junos-beginners-guide/quickstart.md", 3),
        ("specs/skills/junos/junos-beginners-guide/spec.md", 9),
    }
)


class JuniperCorpusPathScanner:
    """Scan tracked text files for corpus-root references."""

    @staticmethod
    def tracked_text_files(
        repository_root: Path = REPOSITORY_ROOT,
    ) -> tuple[Path, ...]:
        """Return tracked files that contain decodable text."""
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repository_root,
            check=True,
            capture_output=True,
        )
        paths = []
        for raw_path in result.stdout.split(b"\0"):
            if not raw_path:
                continue
            path = repository_root / raw_path.decode("utf-8")
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            paths.append(path)
        return tuple(paths)

    @classmethod
    def scan(
        cls,
        files: tuple[Path, ...],
        repository_root: Path = REPOSITORY_ROOT,
    ) -> tuple[int, tuple[tuple[str, int], ...], int]:
        """Return the file count, old-root references, and new-root references."""
        old_references: list[tuple[str, int]] = []
        new_reference_count = 0
        for path in files:
            relative_path = path.relative_to(repository_root).as_posix()
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if any(marker in line for marker in OLD_CORPUS_MARKERS):
                    old_references.append((relative_path, line_number))
                new_reference_count += line.count(NEW_CORPUS_ROOT)
        return len(files), tuple(old_references), new_reference_count

    @classmethod
    def report(
        cls,
        files: tuple[Path, ...],
        repository_root: Path = REPOSITORY_ROOT,
    ) -> str:
        """Return the stable guard report for a tracked-file scan."""
        scanned_count, old_references, new_reference_count = cls.scan(files, repository_root)
        compatibility_reference = cls.compatibility_reference(files, repository_root)
        unapproved = set(old_references) - ALLOWLIST - {compatibility_reference}
        return (
            f"scanned {scanned_count} tracked files; "
            f"found {len(old_references)} old-corpus references; "
            f"approved {len(ALLOWLIST)}; "
            f"unapproved {len(unapproved)}; "
            f"found {new_reference_count} new-corpus references"
        )

    @staticmethod
    def compatibility_reference(
        files: tuple[Path, ...],
        repository_root: Path = REPOSITORY_ROOT,
    ) -> tuple[str, int]:
        """Return the tracked compatibility-row reference."""
        for path in files:
            relative_path = path.relative_to(repository_root).as_posix()
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if (
                    relative_path == "specs/2925-juniper-skill-factory/contracts/interfaces.md"
                    and f"| `{OLD_CORPUS_ROOT}` | The compatibility corpus" in line
                ):
                    return relative_path, line_number
        raise AssertionError("old corpus compatibility row is absent")


def _assert_repository_paths(
    files: tuple[Path, ...],
    repository_root: Path = REPOSITORY_ROOT,
) -> str:
    """Validate the repository corpus contract and return its report."""
    scanned_count, old_references, new_reference_count = JuniperCorpusPathScanner.scan(files, repository_root)
    assert scanned_count > 0, "Juniper corpus guard scanned 0 tracked files"
    old_reference_set = set(old_references)
    missing_allowlist = ALLOWLIST - old_reference_set
    compatibility_reference = JuniperCorpusPathScanner.compatibility_reference(files, repository_root)
    unapproved = old_reference_set - ALLOWLIST - {compatibility_reference}
    interfaces_path = repository_root / "specs/2925-juniper-skill-factory/contracts/interfaces.md"
    interfaces_text = interfaces_path.read_text(encoding="utf-8")
    assert NEW_CORPUS_ROOT in interfaces_text, "new primary corpus root is absent"
    assert f"| `{NEW_CORPUS_ROOT}` | The primary converted corpus" in interfaces_text
    assert f"| `{OLD_CORPUS_ROOT}` | The compatibility corpus" in interfaces_text
    assert missing_allowlist == set(), f"allowlist entries disappeared: {sorted(missing_allowlist)}"
    assert not unapproved, f"unapproved old-corpus references: {sorted(unapproved)}"
    assert "The current converted corpus" not in interfaces_text
    return (
        f"scanned {scanned_count} tracked files; "
        f"found {len(old_references)} old-corpus references; "
        f"approved {len(ALLOWLIST)}; "
        f"unapproved {len(unapproved)}; "
        f"found {new_reference_count} new-corpus references"
    )


class TestJuniperCorpusPaths:
    """Verify the repository corpus path contract."""

    def test_tracked_corpus_paths_are_approved(self) -> None:
        """The tracked repository must contain only approved old-root references."""
        files = JuniperCorpusPathScanner.tracked_text_files()
        report = _assert_repository_paths(files)
        print(report)
        assert report == (
            "scanned " + str(len(files)) + " tracked files; found 17 old-corpus references; approved 16; "
            "unapproved 0; found 1 new-corpus references"
        )

    def test_scanner_rejects_an_unapproved_old_path(self, tmp_path: Path) -> None:
        """The scanner must identify an old path outside the allowlist."""
        synthetic_path = tmp_path / "synthetic.md"
        synthetic_path.write_text(f"{OLD_CORPUS_ROOT}\\unapproved.md\n", encoding="utf-8")
        _, old_references, _ = JuniperCorpusPathScanner.scan((synthetic_path,), tmp_path)
        assert set(old_references) - ALLOWLIST == {("synthetic.md", 1)}

    def test_zero_input_fails(self) -> None:
        """The guard must fail when the tracked input set is empty."""
        with pytest.raises(AssertionError, match="scanned 0 tracked files"):
            _assert_repository_paths(())
