"""Grade the STE writing guide of this repository with the shared linter.

The linter tests live in misthelper-devtools. This file keeps the one check
that reads a MistHelper file: the writing guide must follow its own rules
(issue #3487).
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

from pathlib import Path  # Builds the path to the guide.

from misthelper_devtools.ste_linter.analysis import GrammarAnalyzer, get_backend  # The analysis parts.
from misthelper_devtools.ste_linter.config import LinterConfig  # The configuration.
from misthelper_devtools.ste_linter.parsing import DocumentBuilder  # The document builder.
from misthelper_devtools.ste_linter.rules import RuleContext, load_rules  # The rule context and registry.
from misthelper_devtools.ste_linter.scoring import ScoringModel  # The scoring model.

# The guide sits two levels above the folder of this test file.
GUIDE = Path(__file__).resolve().parents[2] / "documentation" / "ASD-STE100_writing-guide.md"


def test_writing_guide_scores_high() -> None:
    """The STE writing guide scores at or above 90."""
    config = LinterConfig()  # The built-in defaults.
    document = DocumentBuilder().build(str(GUIDE), GUIDE.read_text(encoding="utf-8"))  # Parse the guide.
    context = RuleContext(  # The heuristic backend keeps the result free of spaCy.
        backend=get_backend(prefer_spacy=False),
        grammar=GrammarAnalyzer(),
        config=config,
        dictionary=None,
    )
    rules = load_rules(config)  # The active rules for the default configuration.
    violations = [item for rule in rules for item in rule.check(document, context)]  # Run each rule.
    result = ScoringModel().score(document, violations, rules, False, config)  # Score the guide.
    assert result.score >= 90, f"The writing guide scores {result.score}, below 90."  # The guide follows its rules.
