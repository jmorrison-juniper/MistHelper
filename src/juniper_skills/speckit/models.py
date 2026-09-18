"""Shared models for the SpecKit skill factory harness."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SpecKitPaths:
    """Repository paths that the harness reads and writes."""

    repo_root: Path
    output_root: Path | None = None

    @property
    def specify_dir(self) -> Path:
        """Return the installed SpecKit directory."""
        logging.info("Resolving the SpecKit directory")  # Record the path lookup before returning it.
        path = self.repo_root / ".specify"  # Build the repository-local SpecKit path with pathlib.
        logging.debug("Resolved the SpecKit directory at %s", path)  # Record the resolved path for diagnostics.
        return path

    @property
    def templates_dir(self) -> Path:
        """Return the installed SpecKit template directory."""
        logging.info("Resolving the SpecKit template directory")  # Record the template lookup before returning it.
        path = self.specify_dir / "templates"  # Use the real installed template directory.
        logging.debug(
            "Resolved the SpecKit template directory at %s", path
        )  # Record the resolved path for diagnostics.
        return path

    @property
    def skills_specs_dir(self) -> Path:
        """Return the generated skill specification root."""
        logging.info("Resolving the skill specification output directory")  # Record the output lookup.
        path = self.output_root or self.repo_root / "specs" / "skills"  # Default to the locked output root.
        logging.debug("Resolved the skill specification output directory at %s", path)  # Record the output path.
        return path


@dataclass(frozen=True)
class SkillDocument:
    """One source document that receives a SpecKit artifact set."""

    source_path: Path
    domain: str
    title: str
    pages: int
    slug: str
    source_file: str

    @classmethod
    def from_markdown(cls, source_path: Path, domain: str) -> SkillDocument:
        """Create a document model from source Markdown front matter."""
        logging.info("Reading source Markdown front matter")  # Record the source read before opening the file.
        text = source_path.read_text(encoding="utf-8")  # Read the converted source document for metadata only.
        logging.debug("Read %d characters from source Markdown", len(text))  # Record the safe source size.
        front_matter = cls._front_matter(text)  # Parse only the front matter block for metadata.
        logging.debug("Parsed %d front matter keys", len(front_matter))  # Record the metadata count.
        return cls(  # Build an immutable document value for repeatable artifact generation.
            source_path=source_path,
            domain=domain,
            title=front_matter.get("title", source_path.stem.replace("-", " ").title()),
            pages=int(front_matter.get("pages", "0") or 0),
            slug=cls._slug(source_path.stem),
            source_file=front_matter.get("source_file", source_path.name),
        )

    @property
    def content_hash(self) -> str:
        """Return a stable hash for living-spec drift checks."""
        logging.info("Hashing the source Markdown for living-spec tracking")  # Record the hash action.
        digest = hashlib.sha256(self.source_path.read_bytes()).hexdigest()  # Hash bytes so drift checks are exact.
        logging.debug("Computed source hash prefix %s", digest[:12])  # Record a safe hash prefix only.
        return digest

    @staticmethod
    def _front_matter(text: str) -> dict[str, str]:
        """Parse simple YAML front matter values from Markdown."""
        logging.info("Parsing source front matter values")  # Record the metadata parse action.
        if not text.startswith("---"):
            logging.debug("Source front matter is absent")  # Record the absence for fallback behavior.
            return {}
        block = text.split("---", 2)[1]  # Isolate the first front matter block from source Markdown.
        pairs = re.findall(r'^([^:\n]+):\s*"?([^"\n]+)"?$', block, re.MULTILINE)  # Read simple scalar keys.
        result = {key.strip(): value.strip() for key, value in pairs}  # Normalize whitespace for stable values.
        logging.debug("Parsed front matter keys: %s", sorted(result))  # Record key names without source prose.
        return result

    @staticmethod
    def _slug(value: str) -> str:
        """Return a filesystem-safe slug."""
        logging.info("Creating a document slug")  # Record slug creation for deterministic output.
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")  # Keep a stable lowercase slug.
        logging.debug("Created document slug %s", slug)  # Record the generated slug.
        return slug
