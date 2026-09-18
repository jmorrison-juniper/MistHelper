"""Unit tests for the Juniper depth extraction engine."""

from __future__ import annotations  # Keep annotations cheap during test collection.

from pathlib import Path  # Build guard files with platform-safe paths.

from src.juniper_skills.extract import (  # Import the public depth extraction API.
    CachedSourceSimilarityGuard,
    CommandFactExtractor,
    ConfigurationFactExtractor,
    ConstraintFactExtractor,
    DefinitionFactExtractor,
    FactExtractionEngine,
    NumericFactExtractor,
    OutputFieldFactExtractor,
    PlatformReleaseFactExtractor,
    PrerequisiteFactExtractor,
    TableRowFactExtractor,
)
from src.juniper_skills.extract.parser import SourcePageParser  # Parse test source pages.
from src.juniper_skills.rewrite import CardClassMark, SimilarityCheckInput, VerbatimSimilarityGuard  # Verify contracts.


class TestDepthExtractors:
    """Verify that every fact class extractor emits cited cards."""

    def test_command_extractor_keeps_command_and_arguments(self) -> None:
        """A command extractor preserves the command and visible arguments."""
        facts = self._facts(CommandFactExtractor(), "<!-- page 7 -->\nshow route protocol bgp detail")  # Extract.
        assert facts[0].citation_key == "[TEST p.7]"  # Prove exact page citation.
        assert "`show route protocol bgp detail`" in facts[0].fact  # Prove verbatim command preservation.
        assert any("`bgp`" in fact.fact for fact in facts)  # Prove argument extraction.

    def test_configuration_extractor_keeps_hierarchy_path(self) -> None:
        """A configuration extractor preserves the configuration statement."""
        source = "<!-- page 8 -->\nset interfaces ge-0/0/0 unit 0 family inet address 192.0.2.1/24"  # Source.
        facts = self._facts(ConfigurationFactExtractor(), source)  # Extract the configuration line.
        assert "`set interfaces ge-0/0/0 unit 0 family inet address 192.0.2.1/24`" in facts[0].fact  # Preserve.
        assert facts[0].mark == CardClassMark.INFO  # Plain configuration syntax is informational.

    def test_numeric_extractor_classifies_required_limits(self) -> None:
        """A numeric extractor finds limits and marks required text as MUST."""
        source = "<!-- page 9 -->\nYou must configure a maximum 4096 VLANs on this platform."  # Source.
        facts = self._facts(NumericFactExtractor(), source)  # Extract the numeric limit.
        assert facts[0].mark == CardClassMark.MUST  # Prove mandatory language classification.
        assert "`maximum 4096 VLANs`" in facts[0].fact  # Prove numeric value preservation.

    def test_table_row_extractor_emits_one_fact_per_row(self) -> None:
        """A table row extractor emits each body row as one fact."""
        source = "<!-- page 10 -->\n| Field | Meaning |\n| --- | --- |\n| State | Up |\n| Admin | Enabled |"  # Source.
        facts = self._facts(TableRowFactExtractor(), source)  # Extract table body rows.
        assert len(facts) == 2  # Prove one fact exists for each table body row.
        assert "`Field` is `State`" in facts[0].fact  # Prove header-to-cell pairing.

    def test_output_field_extractor_finds_field_meaning(self) -> None:
        """An output field extractor finds output fields and meanings."""
        source = "<!-- page 11 -->\nSpeed - Shows the negotiated interface speed in Mbps."  # Source.
        facts = self._facts(OutputFieldFactExtractor(), source)  # Extract the field meaning.
        assert facts[0].fact.startswith("Output field `Speed` means")  # Prove field detection.
        assert facts[0].citation_key == "[TEST p.11]"  # Prove exact page citation.

    def test_constraint_extractor_maps_hard_rules_to_must(self) -> None:
        """A constraint extractor maps required text to MUST."""
        facts = self._facts(ConstraintFactExtractor(), "<!-- page 12 -->\nDo not remove the root password.")  # Extract.
        assert facts[0].mark == CardClassMark.MUST  # Prove hard-rule classification.
        assert "Constraint applies" in facts[0].fact  # Prove the extractor restates the source.

    def test_prerequisite_extractor_finds_ordering(self) -> None:
        """A prerequisite extractor finds ordering requirements."""
        facts = self._facts(
            PrerequisiteFactExtractor(), "<!-- page 13 -->\nBefore commit, verify the interface."
        )  # Extract.
        assert facts[0].citation_key == "[TEST p.13]"  # Prove exact page citation.
        assert "Ordering requirement applies" in facts[0].fact  # Prove ordering restatement.

    def test_definition_extractor_finds_terms(self) -> None:
        """A definition extractor finds term definitions."""
        facts = self._facts(
            DefinitionFactExtractor(), "<!-- page 14 -->\nRoute preference is a route rank."
        )  # Extract.
        assert "`Route preference`" in facts[0].fact  # Prove term preservation.
        assert facts[0].mark == CardClassMark.INFO  # Definitions are informational by default.

    def test_platform_release_extractor_finds_qualifiers(self) -> None:
        """A platform extractor finds release and platform qualifiers."""
        facts = self._facts(
            PlatformReleaseFactExtractor(), "<!-- page 15 -->\nThis option works on MX Series."
        )  # Extract.
        assert "`on MX Series`" in facts[0].fact  # Prove platform qualifier preservation.
        assert facts[0].citation_key == "[TEST p.15]"  # Prove exact page citation.

    def _facts(self, extractor, source: str):
        """Return facts from one extractor and source snippet."""
        lines = SourcePageParser().parse(source)  # Attach page numbers before extractor execution.
        return extractor.extract(lines, "TEST")  # Return facts with a stable test citation key.


class TestDepthEngine:
    """Verify deduplication, splitting, and guard safety."""

    def test_engine_deduplicates_repeated_facts(self) -> None:
        """The engine merges repeated facts and reports the merge count."""
        source = "<!-- page 1 -->\nshow route terse\n<!-- page 2 -->\nshow route terse\n"  # Repeat one fact.
        result = FactExtractionEngine((CommandFactExtractor(),)).extract_text(source, "TEST")  # Extract.
        assert result.raw_count > len(result.cards)  # Prove a repeated candidate merged.
        assert result.merge_count == result.raw_count - len(result.cards)  # Prove the merge count is exact.

    def test_engine_splits_large_topics_without_dropping_cards(self) -> None:
        """The engine splits topics when the hard limit would overflow."""
        lines = ["<!-- page 1 -->"]  # Start the source with an exact page marker.
        lines.extend(f"show route protocol bgp detail {index}" for index in range(320))  # Add many commands.
        result = FactExtractionEngine((CommandFactExtractor(),)).extract_text("\n".join(lines), "TEST")  # Extract.
        assert len(result.topics) > 1  # Prove the hard-limit split ran.
        assert sum(topic.content.count("- **") for topic in result.topics) == len(result.cards)  # Prove no drop.
        assert all(topic.size_bytes <= FactExtractionEngine.HARD_LIMIT for topic in result.topics)  # Prove size.

    def test_engine_output_clears_similarity_guard(self, tmp_path: Path) -> None:
        """The generated cards clear the copyright similarity guard."""
        source = "<!-- page 1 -->\nYou must configure a maximum 4096 VLANs before commit."  # Source.
        result = FactExtractionEngine().extract_text(source, "TEST")  # Extract cards and topic content.
        topic = tmp_path / "topic.md"  # Put the generated topic under the pytest work directory.
        topic.write_text(result.topics[0].content, encoding="utf-8")  # Store the generated Markdown.
        check = SimilarityCheckInput(topic, (source,))  # Compare the topic to the source snippet.
        report = VerbatimSimilarityGuard().check((check,))  # Run the copyright guard.
        assert report.files_checked == 1  # Prove the guard measured one file.
        assert report.files_failed == 0  # Prove the guard found no hard failure.
        assert report.results[0].longest_run <= 7  # Prove copied prose stays in the clear band.

    def test_cached_guard_matches_base_guard(self, tmp_path: Path) -> None:
        """The cached guard returns the same longest run as the base guard."""
        source = "alpha bravo charlie delta echo foxtrot golf hotel india"  # Build a source phrase.
        generated = "alpha bravo charlie delta echo"  # Build a copied clear-band phrase.
        topic = tmp_path / "topic.md"  # Put the generated topic under the pytest work directory.
        topic.write_text(generated, encoding="utf-8")  # Store generated text for the base guard.
        base = VerbatimSimilarityGuard().check((SimilarityCheckInput(topic, (source,)),))  # Run the base guard.
        cached = CachedSourceSimilarityGuard().check_texts(((topic, generated),), source)  # Run cached guard.
        assert cached.files_checked == base.files_checked  # Prove the same file count.
        assert cached.results[0].longest_run == base.results[0].longest_run  # Prove the same longest run.

    def test_engine_reports_cards_per_page_and_retention(self) -> None:
        """The engine reports cards for each page and retained content."""
        source = "<!-- page 1 -->\nshow interfaces terse\n<!-- page 2 -->\ndefault 30 seconds"  # Source.
        result = FactExtractionEngine().extract_text(source, "TEST")  # Extract and measure the source.
        assert result.cards_per_page >= 1.0  # Prove the page density metric is populated.
        assert result.retention_percent > 0.0  # Prove the retention metric is populated.
