"""Check the initial failure-field contract and expose counted negative controls."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


class FailureFieldGuard(HTMLParser):
    """Read one actual field and require its strategy metadata and initial state."""

    def __init__(self, text: str) -> None:
        """Parse the supplied markup without a browser or a network."""
        super().__init__()
        self.groups: list[dict[str, str | None]] = []
        self.group: dict[str, str | None] = {}
        self.field: dict[str, str | None] = {}
        self.checked = 0
        self.feed(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Keep the enclosing group and the attributes of the failure field."""
        attributes = dict(attrs)
        if tag == "div":
            self.groups.append(attributes)
        if tag == "input" and attributes.get("name") == "max_failure_percentage":
            self.checked += 1
            self.group = self.groups[-1]
            self.field = attributes

    def handle_endtag(self, tag: str) -> None:
        """Leave each completed group before reading the next one."""
        if tag == "div":
            self.groups.pop()

    def require(self, strategy: str, percentage: int) -> None:
        """Require the saved initial state and all preserved field attributes."""
        print(f"Checked {self.checked} failure field(s) for {strategy}.")
        assert self.checked == 1, "The page must hold exactly one failure field."
        assert (
            self.group.get("data-org-requires-strategy") == "canary rrm serial"
        ), "The strategy rule is absent or wrong."
        applies = strategy in ("canary", "rrm", "serial")
        assert ("hidden" not in self.group) is applies, "The group has the wrong initial visibility."
        assert ("disabled" not in self.field) is applies, "The input has the wrong initial enabled state."
        assert "required" in self.field, "The input lost native required validation."
        assert (self.field["id"], self.field["data-testid"]) == ("max-failure-percentage", "org-upgrade-max-failures")
        assert (self.field["type"], self.field["min"], self.field["max"]) == ("number", "0", "100")
        assert self.field["value"] == str(percentage), "The page changed the saved percentage."

    @classmethod
    def from_file(cls, path: Path) -> FailureFieldGuard:
        """Require readable input rather than accepting an empty successful check."""
        print(f"Reading 1 template input: {path}.")
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            print("Checked 0 failure fields: the template input is unreadable.")
            raise
        return cls(text)
