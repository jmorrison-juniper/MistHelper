"""Contract tests: the upgrade portal texts use American spelling.

Why:
    Issue #3384. The STE guide at ``documentation/ASD-STE100_writing-guide.md``
    requires American spelling in every text that the project ships. The
    options page and the confirm page showed the British word "neighbour". The
    guard below reads every template and the portal script, so a new British
    spelling fails the contract suite.
"""

from __future__ import annotations

import re
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[3] / "src" / "upgrade_portal" / "app" / "assets"  # The portal assets.
TEMPLATE_ROOT = ASSET_ROOT / "templates"  # Every page template and partial template of the portal.
SCRIPT_ROOT = ASSET_ROOT / "static" / "js"  # The portal script. The vendor folder stays out of scope.

# WHY: The guard must read the two pages of issue #3384 and the portal script.
# If a path changes and the guard reads fewer files, this set fails the test.
REQUIRED_FILES = frozenset(
    {
        "templates/upgrade/options.html",  # The page with three of the four visible hits.
        "templates/upgrade/confirm.html",  # The page with the fourth visible hit.
        "static/js/portal.js",  # The script that writes text into each page.
    }
)

# WHY: Each stem below is a British spelling with no identifier collision in the
# portal. Research Decision 2 of `specs/3384-american-spelling` names the words
# that the list omits: `labelled` (the ARIA name `aria-labelledby`), `cancelled`
# (a state identifier), and `analyses` (also the American plural of "analysis").
BRITISH_SPELLING = re.compile(
    r"\b(?:neighbour|colour|behaviour|favour|honour|centre|licence|catalogue|organis|authoris"
    r"|recognis|initialis|normalis|programme|artefact|judgement|whilst|amongst)\w*"
    r"|\banalys(?:e|ed|ing)\b",
    re.IGNORECASE,
)

BRITISH_SAMPLES = (
    "neighbour",  # The word of issue #3384.
    "Neighbourhood",  # The capital letter and the longer form must match too.
    "colour",  # A common British stem.
    "behaviour",  # A common British stem.
    "favourite",  # The stem inside a longer word.
    "centre",  # The British order of the last two letters.
    "licence",  # The British noun form.
    "catalogue",  # The British long form.
    "organisation",  # The British "s" form.
    "authorise",  # The British "s" form of a verb.
    "analyse",  # The British verb form.
    "whilst",  # A British conjunction.
)

ALLOWED_SAMPLES = (
    "aria-labelledby",  # The ARIA standard fixes this attribute name.
    "cancelled",  # The state model of the portal uses this identifier.
    "analyses",  # The American plural of "analysis".
    "neighbor",  # The American form of the word of issue #3384.
    "neighborhood",  # The American long form.
    "center",  # The American order of the last two letters.
    "catalog",  # The American short form.
    "organization",  # The American "z" form.
)


def portal_text_files() -> list[Path]:
    """Return every template and every portal script file, in a stable order."""
    templates = sorted(TEMPLATE_ROOT.rglob("*.html"))  # Every page template and partial template.
    scripts = sorted(SCRIPT_ROOT.glob("*.js"))  # The portal script only, not the vendor bundle.
    return templates + scripts  # One list keeps the order of the report stable.


def british_hits(path: Path) -> list[str]:
    """Return one ``<file>:<line>: <word>`` entry for each British spelling in the file."""
    relative = path.relative_to(ASSET_ROOT).as_posix()  # A short file name for the failure report.
    lines = path.read_text(encoding="utf-8").splitlines()  # Read the raw text, the Jinja comments included.
    return [
        f"{relative}:{number}: {match.group(0)}"  # Name the file, the line, and the word.
        for number, line in enumerate(lines, start=1)  # Count the lines from one, as an editor does.
        for match in BRITISH_SPELLING.finditer(line)  # Report each hit on the line.
    ]


def test_the_pattern_flags_each_british_sample() -> None:
    """Each British sample word matches the guard pattern."""
    missed = [word for word in BRITISH_SAMPLES if BRITISH_SPELLING.search(word) is None]  # Samples that pass unseen.
    assert missed == []  # The guard must catch every sample.


def test_the_pattern_keeps_each_allowed_word() -> None:
    """An identifier that a standard fixes, or an American word, does not match."""
    flagged = [word for word in ALLOWED_SAMPLES if BRITISH_SPELLING.search(word) is not None]  # Wrong hits.
    assert flagged == []  # The guard must not flag an allowed word.


def test_every_portal_text_uses_american_spelling() -> None:
    """No template and no portal script holds a British spelling from the guard list."""
    paths = portal_text_files()  # Read the full set of portal text files.
    names = {path.relative_to(ASSET_ROOT).as_posix() for path in paths}  # The short names of the files read.
    missing = sorted(REQUIRED_FILES - names)  # A required file that the guard did not read.
    assert missing == [], f"The guard read {len(paths)} files under {ASSET_ROOT} and missed {missing}."
    hits = [hit for path in paths for hit in british_hits(path)]  # Collect every hit across the files.
    assert hits == [], f"The guard read {len(paths)} files and found {len(hits)} British spellings: {hits}"
