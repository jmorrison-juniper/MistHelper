"""Hold the complete-name contract for the shared diagram reference lint."""

from misthelper_devtools.diagram_refs import DiagramReferenceValidator  # Use the pinned shared implementation.


def test_pinned_lint_keeps_the_complete_suffix_bearing_name() -> None:
    """Keep characters that follow a recognized class-name suffix."""
    validator = DiagramReferenceValidator()  # Exercise the dependency that the repository pins.
    block = "flowchart TD\n    A[SiteAnalyticsConfigurator.configure]"  # Reproduce issue 3416.

    identifiers = validator.extract_identifiers(block)  # Read names through the production extraction path.
    checked_count = len(identifiers)  # Measure the references that the contract examined.
    print(f"Checked references: {checked_count}")  # Report the contract input count.

    assert checked_count > 0  # Fail when the contract input no longer exercises the parser.
    assert "SiteAnalyticsConfigurator" in identifiers  # Require the complete class name.
    assert "SiteAnalyticsConfig" not in identifiers  # Reject the former truncated prefix.


def test_pinned_lint_still_flags_an_absent_complete_name(tmp_path) -> None:
    """Keep a real failure for an absent complete class name."""
    diagram_path = tmp_path / "missing-class.md"  # Isolate the failing document from repository files.
    diagram_path.write_text(  # Create one controlled Mermaid reference.
        "```mermaid\nflowchart TD\n    A[FooConfig.run]\n```\n",
        encoding="utf-8",
    )
    validator = DiagramReferenceValidator()  # Exercise the dependency that the repository pins.
    validator.python_symbols = {"SiteAnalyticsConfigurator"}  # Exclude the controlled missing class.

    stale_count = validator.validate_file(diagram_path)  # Run the production validation path.

    assert stale_count == 1  # Prove that the corrected extraction still detects missing classes.
    assert validator.stale_references[0]["name"] == "FooConfig"  # Require the complete missing name.
