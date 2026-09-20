"""Unit tests for the release-note selector (T019, FR-006, FR-007, FR-009)."""

from __future__ import annotations

from src.juniper_docs.discovery.release_note_selector import (
    CorpusReleaseNoteSelector,
    ReleaseNoteSelector,
)
from src.juniper_docs.models import DocumentType, InventoryRecord

_TRAIN = "software/junos/release-notes"
_RNE = "rne/us/en/release-notes"  # A PDF tree whose first path segment is not a locale.


def test_selector_keeps_only_the_newest_note_per_train() -> None:
    """The selector keeps the newest note in each major train."""
    roots = [
        f"{_TRAIN}/23.4/junos-release-notes-23.4r1",  # Older 23 note.
        f"{_TRAIN}/23.4/junos-release-notes-23.4r2",  # Newer 23 note.
        f"{_TRAIN}/22.2/junos-release-notes-22.2r1",  # A different train.
    ]
    kept, dropped = ReleaseNoteSelector().select(roots)  # Apply the filter.
    assert f"{_TRAIN}/23.4/junos-release-notes-23.4r2" in kept  # The newest 23 note stays.
    assert f"{_TRAIN}/22.2/junos-release-notes-22.2r1" in kept  # The other train stays.
    assert dropped == [f"{_TRAIN}/23.4/junos-release-notes-23.4r1"]  # The older 23 note goes.


def test_selector_keeps_a_non_release_note_and_an_unparseable_note() -> None:
    """Every non-release-note is kept, and a note with no version is kept."""
    roots = [
        "software/junos-configuration-guide",  # A normal document.
        "software/junos/release-notes/junos-release-notes-legacy",  # No version to parse.
    ]
    kept, dropped = ReleaseNoteSelector().select(roots)  # Apply the filter.
    assert set(kept) == set(roots)  # Both documents are kept.
    assert dropped == []  # Nothing is dropped without a newer sibling.


def test_corpus_selector_returns_records_and_drop_pairs() -> None:
    """The corpus selector partitions records and returns the drop reasons."""
    records = [
        _record(f"{_TRAIN}/23.4/junos-release-notes-23.4r1"),  # Older, dropped.
        _record(f"{_TRAIN}/23.4/junos-release-notes-23.4r2"),  # Newer, kept.
    ]
    kept, dropped = CorpusReleaseNoteSelector().filter_records(records)  # Filter records.
    kept_slugs = {record.root_slug for record in kept}  # The kept slugs.
    assert kept_slugs == {f"{_TRAIN}/23.4/junos-release-notes-23.4r2"}  # Only the newest.
    assert dropped[0][1] == "superseded-by-newer-train-member"  # The recorded reason.


def test_evolved_and_standard_junos_form_separate_trains() -> None:
    """Defect 1: Junos OS and Junos OS Evolved never collapse into one train."""
    roots = [
        f"{_TRAIN}/24.4/junos-release-notes-24.4r2",  # Standard Junos OS note.
        f"{_TRAIN}/24.4/junos-evo-release-notes-24.4r2",  # Junos OS Evolved note.
    ]
    kept, dropped = ReleaseNoteSelector().select(roots)  # Apply the filter.
    assert set(kept) == set(roots)  # Both products survive in the same major and minor.
    assert dropped == []  # Neither product evicts the other.


def test_x_build_does_not_evict_the_mainstream_note() -> None:
    """Defect 2: an X-build forms its own train and keeps the mainstream note."""
    roots = [
        f"{_TRAIN}/23.4/junos-evo-release-notes-23.4r1",  # Older mainstream note.
        f"{_TRAIN}/23.4/junos-evo-release-notes-23.4r2",  # Newer mainstream note.
        f"{_TRAIN}/23.4/junos-evo-release-notes-23.4x100-d40",  # Special X-build branch.
    ]
    kept, dropped = ReleaseNoteSelector().select(roots)  # Apply the filter.
    assert f"{_TRAIN}/23.4/junos-evo-release-notes-23.4r2" in kept  # Mainstream not evicted.
    assert f"{_TRAIN}/23.4/junos-evo-release-notes-23.4x100-d40" in kept  # X-build kept apart.
    assert dropped == [f"{_TRAIN}/23.4/junos-evo-release-notes-23.4r1"]  # Only the older R note.


def test_d_revision_winner_is_by_version_not_input_order() -> None:
    """Defect 3: the newest D revision wins, regardless of the input order."""
    base = f"{_TRAIN}/23.4/junos-evo-release-notes-23.4x100"  # One X-build train.
    forward = [f"{base}-d20", f"{base}-d30", f"{base}-d31", f"{base}-d40"]  # Ascending order.
    reverse = list(reversed(forward))  # Descending order proves the version decides.
    for order in (forward, reverse):  # The winner must not depend on the input order.
        kept, _ = ReleaseNoteSelector().select(order)  # Apply the filter for this order.
        assert kept == [f"{base}-d40"]  # The highest D revision wins every time.


def test_pdf_under_a_locale_path_keeps_both_products() -> None:
    """Defect 4: a PDF tree does not bucket two products under the locale."""
    roots = [
        f"{_RNE}/Junos%20OS/26.2R1/junos-os-release-notes-26.2r1.pdf",  # Junos OS PDF.
        f"{_RNE}/Junos%20OS%20Evolved/26.2R1/junos-os-evolved-release-notes-26.2r1.pdf",  # EVO PDF.
    ]
    kept, dropped = ReleaseNoteSelector().select(roots)  # Apply the filter.
    assert set(kept) == set(roots)  # The locale no longer merges the two products.
    assert dropped == []  # Both PDFs survive.


def test_default_keeps_the_newest_note_for_each_minor() -> None:
    """The default train covers a major and a minor, so each minor keeps a note."""
    roots = [
        f"{_TRAIN}/23.1/junos-release-notes-23.1r1",  # Major 23, minor 1.
        f"{_TRAIN}/23.4/junos-release-notes-23.4r2",  # Major 23, minor 4.
    ]
    kept, dropped = ReleaseNoteSelector().select(roots)  # Apply the default filter.
    assert set(kept) == set(roots)  # 23.1 and 23.4 are different trains by default.
    assert dropped == []  # The default keeps both minors.


def test_collapse_to_major_keeps_one_note_per_major() -> None:
    """The collapse option merges every minor, so one major keeps one note."""
    roots = [
        f"{_TRAIN}/23.1/junos-release-notes-23.1r1",  # Older minor within major 23.
        f"{_TRAIN}/23.4/junos-release-notes-23.4r2",  # Newer minor within major 23.
    ]
    selector = ReleaseNoteSelector(collapse_to_major=True)  # Collapse the train to the major.
    kept, dropped = selector.select(roots)  # Apply the collapse filter.
    assert kept == [f"{_TRAIN}/23.4/junos-release-notes-23.4r2"]  # Major 23 keeps one note.
    assert dropped == [f"{_TRAIN}/23.1/junos-release-notes-23.1r1"]  # The older minor drops.


def test_read_version_parses_the_d_revision() -> None:
    """The version parse reads the D revision and sorts by it."""
    selector = ReleaseNoteSelector()  # A default selector for the parse helpers.
    high = selector.read_version(f"{_TRAIN}/23.4/junos-evo-release-notes-23.4x100-d40")  # D40.
    low = selector.read_version(f"{_TRAIN}/23.4/junos-evo-release-notes-23.4x100-d20")  # D20.
    assert high is not None and low is not None  # Both names carry a version.
    assert high.d_rev == 40 and low.d_rev == 20  # The D revision is parsed, not dropped.
    assert high > low  # The newer D revision sorts above the older one.


def test_read_product_reads_the_family_from_the_name() -> None:
    """The product family comes from the document name, not the path segment."""
    selector = ReleaseNoteSelector()  # A default selector for the parse helpers.
    standard = selector.read_product(f"{_TRAIN}/24.4/junos-release-notes-24.4r2")  # Junos OS.
    evolved = selector.read_product(f"{_TRAIN}/24.4/junos-evo-release-notes-24.4r2")  # EVO.
    locale = selector.read_product(f"{_RNE}/Junos%20OS/26.2R1/junos-os-release-notes-26.2r1.pdf")
    assert standard == "junos"  # The standard family reads from the name.
    assert evolved == "junos-evo"  # The Evolved family stays distinct.
    assert locale == "junos-os"  # The locale path does not become the family.


def _record(slug: str) -> InventoryRecord:
    """Return an HTML-root inventory record whose slug drives the filter."""
    return InventoryRecord(f"https://x/{slug}/", slug, DocumentType.HTML_ROOT)  # Test record.
