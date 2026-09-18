"""Unit tests for the Juniper skill rewrite components."""

from __future__ import annotations  # Keep annotations cheap during test collection.

from pathlib import Path  # Build test file paths with portable path objects.

from src.juniper_skills.rewrite import (  # Import the public rewrite API used by orchestrator agents.
    CardClassMark,
    CardExtractor,
    KnowledgeCard,
    PromptTemplateBuilder,
    RewriteWorkPacket,
    RuleBasedBackend,
    SimilarityCheckInput,
    SteValidator,
    VerbatimSimilarityGuard,
)


class TestVerbatimSimilarityGuard:
    """Verify that the copyright similarity guard measures prose correctly."""

    def test_guard_catches_twenty_word_copied_passage(self, tmp_path: Path) -> None:
        """The guard fails when generated prose copies a long source passage."""
        words = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"  # Build the first ten copied words.
        copied = words + " kilo lima mike november oscar papa quebec romeo sierra tango"  # Add ten more words.
        generated = tmp_path / "topic.md"  # Put the generated topic in the pytest work directory.
        generated.write_text(copied, encoding="utf-8")  # Write the copied passage for the guard.
        check = SimilarityCheckInput(generated, (copied,))  # Compare the generated file to its source.
        report = VerbatimSimilarityGuard().check((check,))  # Run the guard against one file.
        assert report.files_checked == 1  # Prove the guard measured one file.
        assert report.results[0].longest_run == 20  # Prove the copied passage was measured.
        assert not report.passed  # Prove the guard rejects the copied passage.

    def test_guard_ignores_verbatim_cli_block(self, tmp_path: Path) -> None:
        """The guard passes a long CLI block because commands stay verbatim."""
        command_template = "set interfaces ge-0/0/%d unit 0 family inet address 192.0.2.%d/24"  # Set CLI shape.
        commands = [command_template % (index, index) for index in range(40)]  # Build config lines.
        cli = "\n".join(commands)  # Build a long config block.
        generated = tmp_path / "topic.md"  # Put the generated topic in the pytest work directory.
        generated.write_text(cli, encoding="utf-8")  # Write the verbatim CLI block.
        check = SimilarityCheckInput(generated, (cli,))  # Compare the generated file to the source CLI.
        report = VerbatimSimilarityGuard().check((check,))  # Run the similarity guard.
        assert report.files_checked == 1  # Prove the guard measured the file.
        assert report.results[0].longest_run == 0  # Prove the CLI block did not count as prose.
        assert report.passed  # Prove approved verbatim classes pass.

    def test_guard_fails_zero_files(self) -> None:
        """The guard fails when it checks no files."""
        report = VerbatimSimilarityGuard().check(tuple())  # Run the guard with no inputs.
        assert report.files_checked == 0  # Prove the report states zero checked files.
        assert not report.passed  # Prove the contract failure is enforced.
        assert report.errors  # Prove the report explains the failure.


class TestKnowledgeCards:
    """Verify the card model and extractor."""

    def test_card_round_trip(self) -> None:
        """A card keeps its mark, fact, and citation through Markdown."""
        fact = "Set the interface address before you commit."  # Use a short STE fact for the round trip.
        card = KnowledgeCard(CardClassMark.MUST, fact, "[JUNOS-BEG p.66]")  # Build a contract card.
        line = card.to_markdown()  # Render the card to the topic-file format.
        parsed = CardExtractor().from_markdown(line)  # Parse the card from Markdown.
        assert parsed == card  # Prove the card survives the round trip.


class TestRewriteHarness:
    """Verify the deterministic rewrite seam."""

    def test_prompt_template_contains_required_rules(self) -> None:
        """The prompt template carries the locked compliance rules."""
        commands = ("show interfaces terse",)  # Give the prompt one command that must stay verbatim.
        packet = RewriteWorkPacket(  # Build a packet with routing context.
            "A router supports BGP.",
            "p.66",
            commands,
            "routing",
            ("day2",),
            "JUNOS-BEG",
        )
        prompt = PromptTemplateBuilder().build(packet)  # Render the future agent backend prompt.
        assert "Do not copy Juniper source prose." in prompt  # Prove the copyright rule is present.
        assert "Simplified Technical English" in prompt  # Prove the STE rule is present.
        assert "Keep commands" in prompt  # Prove the verbatim-class rule is present.
        assert "Life cycle tags: day2." in prompt  # Prove life cycle tags route the output.

    def test_rule_based_backend_reports_limits(self) -> None:
        """The rule backend extracts structure and states its limitation."""
        source = "| Field | Value |\n| - | - |\n| Speed | 100 Gb/s |"  # Build structured source content.
        packet = RewriteWorkPacket(source, "p.10", tuple(), "switching", ("day0",), "QFX-GUIDE")  # Build a packet.
        result = RuleBasedBackend().rewrite(packet)  # Run deterministic extraction.
        assert result.cards  # Prove structured content creates cards.
        assert result.limitations  # Prove the backend states what it cannot do.


class TestSteValidator:
    """Verify STE validation through the existing linter."""

    def test_ste_validator_scores_file(self, tmp_path: Path) -> None:
        """The STE validator returns one score for one generated file."""
        topic = tmp_path / "topic.md"  # Put the test topic in the pytest work directory.
        prose = "- **INFO** The router stores the route. [JUNOS-BEG p.1]\n"  # Use simple STE prose.
        topic.write_text(prose, encoding="utf-8")  # Write simple STE prose.
        report = SteValidator(minimum_score=1).validate((topic,))  # Run the validator with a low test threshold.
        assert report.files_checked == 1  # Prove the validator measured one file.
        assert report.reports[0].score >= 1  # Prove the validator returned a usable score.
        assert report.passed  # Prove the report passed the configured threshold.
