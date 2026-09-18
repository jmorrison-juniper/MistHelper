"""Read real installed skill package measurements for SpecKit artifacts."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PackageMetrics:
    """Measurements read from the installed skill package."""

    package_path: Path | None = None
    topic_count: int | None = None
    life_cycle_spread: dict[str, int] = field(default_factory=dict)
    topic_titles: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    @property
    def is_measured(self) -> bool:
        """Return true when the installed package exists."""
        logging.info("Checking package measurement availability")  # Record the availability check.
        result = self.package_path is not None and self.topic_count is not None  # Require a package and count.
        logging.debug("Package measurement availability is %s", result)  # Record the Boolean result.
        return result


class InstalledPackageScanner:
    """Measure topics and life cycles from installed skill topic files."""

    LIFE_CYCLES = ("day0", "day1", "day2", "day2plus")

    def __init__(self, skills_root: Path) -> None:
        self.skills_root = skills_root  # Store the installed skills root from the path policy.

    def scan(self, domain: str, source_path: Path, source_file: str, title: str) -> PackageMetrics:
        """Return measurements for one installed document package."""
        logging.info("Scanning installed skill package for %s", title)  # Record package scan start.
        package_path = self._package_path(domain, source_path, source_file, title)  # Resolve the document folder.
        if package_path is None:  # Missing packages must stay honest as not measured.
            logging.debug("No installed package was found for %s", title)  # Record missing package state.
            return PackageMetrics(life_cycle_spread=self._empty_spread())
        topics = self._topic_files(package_path)  # Find real topic files, excluding indexes.
        spread = self._life_cycle_spread(topics)  # Parse lifecycle lists from each topic front matter.
        titles = tuple(self._topic_title(path) for path in topics)  # Read topic titles from each topic file.
        metrics = PackageMetrics(package_path, len(topics), spread, titles, self._keywords(titles))  # Build result.
        logging.debug("Measured %d topics from %s", len(topics), package_path)  # Record topic count and path.
        return metrics

    def _package_path(self, domain: str, source_path: Path, source_file: str, title: str) -> Path | None:
        """Return the installed document folder when it exists."""
        logging.info("Resolving installed document package path")  # Record path resolution start.
        root = self.skills_root / domain / "documents"  # Use the persisted domain from the database.
        candidates = [root / slug for slug in self._candidate_slugs(source_path, source_file, title)]  # Build paths.
        package_path = next((path for path in candidates if path.exists()), None)  # Select the first existing path.
        logging.debug("Resolved installed package path present=%s", package_path is not None)  # Record presence.
        return package_path

    def _candidate_slugs(self, source_path: Path, source_file: str, title: str) -> tuple[str, ...]:
        """Return likely installed document folder names."""
        logging.info("Building installed package slug candidates")  # Record candidate creation.
        values = (source_path.stem, Path(source_file).stem, title)  # Use source-derived values without guessing domain.
        slugs = tuple(dict.fromkeys(self._slug(value) for value in values if value))  # Deduplicate in order.
        logging.debug("Built %d installed package slug candidates", len(slugs))  # Record candidate count.
        return slugs

    def _topic_files(self, package_path: Path) -> list[Path]:
        """Return real topic files from an installed document package."""
        logging.info("Listing installed topic files")  # Record topic discovery start.
        files = sorted(path for path in package_path.glob("*.md") if path.name != "INDEX.md")  # Exclude the index.
        logging.debug("Listed %d installed topic files", len(files))  # Record topic file count.
        return files

    def _life_cycle_spread(self, topic_files: list[Path]) -> dict[str, int]:
        """Return life cycle counts from topic front matter."""
        logging.info("Parsing lifecycle lists from installed topics")  # Record lifecycle parsing start.
        spread = self._empty_spread()  # Start with all lifecycle buckets present.
        for path in topic_files:  # Read each installed topic file once.
            for name in self._life_cycles(path):  # Parse one or more lifecycle values per topic.
                spread[name] = spread.get(name, 0) + 1  # Count each declared lifecycle value.
        logging.debug("Parsed lifecycle spread %s", spread)  # Record the measured spread.
        return spread

    def _life_cycles(self, path: Path) -> tuple[str, ...]:
        """Return the lifecycle values from one topic file."""
        logging.info("Reading topic lifecycle front matter")  # Record topic lifecycle read.
        text = path.read_text(encoding="utf-8")  # Read the installed topic file.
        match = re.search(r"^lifecycle:\s*\[([^\]]*)\]", text, re.MULTILINE)  # Find the lifecycle list.
        values = tuple(value.strip().strip("'\"") for value in match.group(1).split(",")) if match else ()  # Parse.
        result = tuple(value for value in values if value in self.LIFE_CYCLES)  # Keep only approved lifecycle names.
        logging.debug("Read %d lifecycle values from %s", len(result), path.name)  # Record lifecycle value count.
        return result

    def _topic_title(self, path: Path) -> str:
        """Return one installed topic title."""
        logging.info("Reading installed topic title")  # Record title read.
        text = path.read_text(encoding="utf-8")  # Read the installed topic text.
        match = re.search(r"^topic:\s*(.+)$", text, re.MULTILINE)  # Prefer front matter topic titles.
        title = match.group(1).strip().strip('"') if match else path.stem.replace("-", " ").title()  # Fallback.
        logging.debug("Read installed topic title with %d characters", len(title))  # Record title length only.
        return title

    def _keywords(self, titles: tuple[str, ...]) -> tuple[str, ...]:
        """Return extracted keywords from topic titles."""
        logging.info("Extracting keywords from topic titles")  # Record keyword extraction start.
        words = [word.lower() for title in titles for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", title)]
        filtered = [word for word in words if word not in self._stop_words()]  # Remove common route words.
        keywords = tuple(dict.fromkeys(filtered))[:20]  # Keep stable unique keywords for compact specs.
        logging.debug("Extracted %d topic keywords", len(keywords))  # Record keyword count.
        return keywords

    def _empty_spread(self) -> dict[str, int]:
        """Return zero counts for all life cycle buckets."""
        logging.info("Building empty lifecycle spread")  # Record empty spread creation.
        spread = {name: 0 for name in self.LIFE_CYCLES}  # Keep all lifecycle buckets present.
        logging.debug("Built empty lifecycle spread with %d keys", len(spread))  # Record spread size.
        return spread

    def _slug(self, value: str) -> str:
        """Return a filesystem-safe package slug."""
        logging.info("Creating installed package slug")  # Record slug creation.
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")  # Match the installed skill convention.
        logging.debug("Created installed package slug %s", slug)  # Record generated slug.
        return slug

    def _stop_words(self) -> set[str]:
        """Return words that do not identify a subject."""
        logging.info("Building topic keyword stop words")  # Record stop word creation.
        words = {"overview", "series", "using", "guide", "configuration", "example", "examples"}  # Exclude noise.
        logging.debug("Built %d keyword stop words", len(words))  # Record stop word count.
        return words
