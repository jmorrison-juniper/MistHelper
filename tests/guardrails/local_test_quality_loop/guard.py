"""Check the local test-quality procedure against the live CI contract."""

from __future__ import annotations  # Keep nested record annotations safe.

import json  # Validate required baseline identities without changing them.
import logging  # Expose completed reads and named failures.
import re  # Recognize a narrow documented Markdown and shell grammar.
import shlex  # Decode tokens without executing documents or workflow text.
import tomllib  # Accept valid settings, including readable empty TOML.
from collections.abc import Callable  # Preserve validator result types.
from dataclasses import dataclass, field  # Separate completed operations.
from pathlib import Path  # Restrict reads to the supplied repository.
from typing import cast  # Narrow checked YAML mappings without type suppression.

import yaml  # Decode the live workflow without executing its script.
from misthelper_devtools.test_quality_analyzer.config import (  # Use unchanged installed settings validators.
    ConfigError,  # Keep installed semantic failures distinct from malformed TOML.
    ConfigLoader,  # Reuse pure table validation without another file read.
)


class InputLedger:  # Keep required reads and usability decisions separately measurable.
    """Account for required reads and successful validations separately."""

    @dataclass
    class Progress:  # Prevent partial failures from erasing completed checks.
        """Keep five independent measurements for one invocation."""

        attempted: set[str] = field(default_factory=set)  # Count each started read once.
        reads: set[str] = field(default_factory=set)  # Count only complete UTF-8 reads.
        validations: set[str] = field(default_factory=set)  # Do not count a parse failure as valid.
        guide_reads: set[str] = field(default_factory=set)  # Separate documents from other inputs.
        guide_checks: set[str] = field(default_factory=set)  # Count completed guide decisions.

    class Validation:  # Reject unusable settings and comparator inputs before gate evidence.
        """Reject unusable settings and baseline text after successful reads."""

        class Identity:  # Require comparator records that the installed gate can read.
            """Validate comparator records without another input read."""

            fields = (  # Require the text fields that the installed comparator reads.
                "category",
                "rule_id",
                "file_path",
                "explanation",
                "severity",
                "remediation",
            )
            categories = {  # Preserve the installed finding taxonomy.
                "untested",
                "weak_assertion",
                "missing_failure_mode",
                "missing_edge_case",
                "tautological",
                "parse_error",
                "stale_baseline",
            }

            @classmethod
            def validate(cls, entry: object) -> None:  # Reject unusable finding identities.
                if not isinstance(entry, dict):  # A finding identity must be an object.
                    raise ValueError("A baseline identity must contain an object")  # Reject other JSON values.
                if any(not isinstance(entry.get(key), str) or not entry[key] for key in cls.fields):  # Require text.
                    raise ValueError("A baseline identity has invalid text fields")  # Do not print record contents.
                if type(entry.get("line_number")) is not int or entry["line_number"] < 1:  # Exclude bool and zero.
                    raise ValueError("A baseline identity requires positive line_number")  # Keep locations exact.
                if entry["severity"] not in {"critical", "high", "medium", "low"}:  # Require comparator taxonomy.
                    raise ValueError("A baseline identity has invalid severity")  # Reject an unusable comparator.
                if entry["category"] not in cls.categories:  # The comparator constructs this enumeration.
                    raise ValueError("A baseline identity has invalid category")  # Reject unknown categories.

        @staticmethod
        def settings(text: str) -> bool:  # Keep the settings decision explicit.
            logging.info("Parsing required settings")  # Announce the independent validation.
            tables = tomllib.loads(text)  # Reject malformed TOML without changing analyzer defaults.
            names = ("rules", "severity", "exclusions")  # Validate only installed analyzer tables.
            if any(not isinstance(tables.get(name, {}), dict) for name in names):  # Reject unusable table types.
                raise ValueError("Analyzer settings require table mappings")  # Fail before private parser calls.
            loader = ConfigLoader()  # Use the unchanged pinned package's pure validators.
            try:  # Do not reread settings through ConfigLoader.load.
                loader._parse_rules(tables.get("rules", {}))  # Preserve installed rule-name and boolean validation.
                loader._parse_severities(tables.get("severity", {}))  # Preserve installed taxonomy validation.
                loader._parse_predicate(tables.get("exclusions", {}))  # Preserve installed exclusion-field types.
                loader._parse_globs(tables.get("exclusions", {}))  # Reject unusable path-glob fields.
            except ConfigError as error:  # Catch only the installed semantic validation error.
                raise ValueError(  # Preserve installed settings validation without exposing input values.
                    "Invalid installed analyzer settings controls"
                ) from error  # Do not expose input values.
            logging.debug("Parsed %s settings tables", len(tables))  # Report actual parsed structure.
            return True  # A readable empty settings file remains valid.

        @staticmethod
        def baseline(text: str) -> bool:  # Keep the baseline decision explicit.
            logging.info("Validating required baseline identities")  # Announce the independent validation.
            entries: object = json.loads(text)  # Treat untrusted JSON as unknown until checked.
            if not isinstance(entries, list):  # Gate comparison requires a list of finding identities.
                raise ValueError("The baseline must contain a list")  # Reject arbitrary JSON envelopes.
            for entry in entries:  # Validate every supplied record, not only the first.
                InputLedger.Validation.Identity.validate(entry)  # Keep all supplied comparator identities usable.
            logging.debug("Validated %s baseline identities", len(entries))  # Report actual record coverage.
            return True  # Empty fixture-local baseline lists accept no findings.

    def __init__(self, root: Path) -> None:  # Keep all invocation state local.
        self.root = root  # Use only the caller's isolated input root.
        self.progress = self.Progress()  # Start with no claimed operations.
        self.texts: dict[str, str] = {}  # Retain only successfully read text.
        self.errors: list[str] = []  # Preserve named failures for the report.

    def read_all(self, paths: tuple[str, ...]) -> None:  # Preserve independent completed reads after failures.
        for path in paths:  # Attempt every independent input after an earlier failure.
            if path in self.progress.attempted:  # Prevent accidental rereads from inflating measurements.
                raise ValueError("A required input read was repeated")  # Expose an invalid invocation.
            logging.info("Reading required input %s", path)  # Name the read before it starts.
            self.progress.attempted.add(path)  # Count the attempt even if the file cannot be read.
            try:  # Handle only actual filesystem and text decoding failures.
                text = (self.root / path).read_text(encoding="utf-8")  # Require a complete genuine UTF-8 read.
            except (OSError, UnicodeError) as error:  # Missing, directory, permission, or encoding inputs fail.
                self.errors.append(f"{path}: read_failed ({type(error).__name__})")  # Preserve safe named context.
                logging.exception("Required input read failed for %s", path)  # Keep exception context for diagnosis.
                logging.debug("Required input %s read status=fail", path)  # Do not claim a completed read.
                continue  # Keep later independent input attempts visible.
            self.texts[path] = text  # Retain text only after the full read succeeds.
            self.progress.reads.add(path)  # Count completed reads separately from validations.
            if path.endswith(".md"):  # This manifest contains exactly the three required guide documents.
                self.progress.guide_reads.add(path)  # Measure guide reads without claiming guide decisions.
            logging.debug("Read input %s with %s characters", path, len(text))  # Report the actual read size.

    def validate[Value](self, path: str, validator: Callable[[str], Value]) -> Value | None:  # Keep results typed.
        if path not in self.texts:  # A failed read cannot provide valid empty input.
            return None  # Preserve the named read error and avoid an invented validation.
        logging.info("Validating required input %s", path)  # Announce the independent decision.
        try:  # Parse failures remain named input failures rather than passing defaults.
            result = validator(self.texts[path])  # Apply the required validation to the completed read.
        except (ValueError, yaml.YAMLError) as error:  # Catch only supported parser and contract failures.
            reason = str(error) if type(error) is ValueError else "input_parse_error"  # Do not print input excerpts.
            self.errors.append(  # Name the failed control.
                f"{path}: validation_failed ({type(error).__name__}: {reason})"
            )  # Name the failed control.
            logging.error(  # Retain traceback context without leaking parser excerpts or input values.
                "Required input validation failed for %s with %s",
                path,
                type(error).__name__,
                exc_info=(ValueError, ValueError(reason), error.__traceback__),
            )
            logging.debug("Required input %s validation status=fail", path)  # Record a completed failing decision.
            return None  # Allow other independent validations to continue.
        self.progress.validations.add(path)  # Count only a successful complete validation.
        logging.debug("Required input %s validation status=pass", path)  # Record the observed successful decision.
        return result  # Preserve the validator's concrete result type.


class SectionCommands:  # Correct dormant text must not satisfy an active local procedure.
    """Locate only the four active fences in each exact named section."""

    GUIDES = {  # Keep section ownership explicit without copying CI trigger controls.
        ".github/copilot-instructions.md": (  # The one repository guide. `AGENTS.md` holds no local command.
            (2, "Local gates"),  # Reject a lookalike section under another parent.
            (3, "Test quality ratchet"),  # Stop at the next peer section.
        ),
    }
    LABELS = (  # Only these visible labels identify active procedure commands.
        "**Intended base for the required check:**",  # Require base assignment, fetch, and resolution.
        "**Required input preflight:**",  # Require four-input validation before analyzer evidence.
        "**Required check after the local commit and before push:**",  # Identify committed changed scope.
        "**Full-suite check for push or manual CI:**",  # Identify the unscoped full-suite equivalent.
    )

    class Markdown:  # Enforce visible structure before interpreting any command text.
        """Ignore dormant examples while preserving exact section boundaries."""

        class Outline:  # Keep heading ownership and section boundaries explicit.
            """Locate headings only outside comments, quotes, and fences."""

            @staticmethod
            def headings(lines: list[str]) -> list[tuple[int, int, str]]:  # Preserve positions and hierarchy.
                logging.info("Reading active Markdown headings")  # Announce the structural transformation.
                headings = [  # Keep exact titles rather than matching arbitrary document substrings.
                    (index, len(match.group(1)), match.group(2).strip())  # Preserve heading level and line position.
                    for index, line in SectionCommands.Markdown.active(lines)  # Ignore inactive Markdown content.
                    if (match := re.fullmatch(r"(#{1,6})\s+(.+?)\s*#*", line.strip()))  # Require a real heading.
                ]
                logging.debug("Read %s active Markdown headings", len(headings))  # Measure actual structure.
                return headings  # Use these same boundaries for parent ownership and section end.

            @classmethod
            def section(  # Reject absent, ambiguous, or incorrectly owned procedure sections.
                cls, text: str, chain: tuple[tuple[int, str], ...]
            ) -> list[str]:
                """Require exactly one matching heading chain."""
                lines = SectionCommands.Markdown.Text.visible(text)  # Preserve literal fenced command content.
                headings = cls.headings(lines)  # Locate active headings outside every code fence.
                parents: list[tuple[int, str]] = []  # Keep the active heading hierarchy.
                matches: list[tuple[int, int]] = []  # Reject duplicate matching sections.
                for index, level, title in headings:  # Track exact parent ownership.
                    while parents and parents[-1][0] >= level:  # A peer or higher heading closes prior children.
                        parents.pop()  # Keep only the current active ancestors.
                    parents.append((level, title))  # Add this active heading to its hierarchy.
                    if tuple(parents[-len(chain) :]) == chain:  # Require the full named chain.
                        matches.append((index, level))  # Count every match instead of selecting a convenient one.
                if len(matches) != 1:  # Missing or duplicated sections cannot identify an active procedure.
                    raise ValueError(f"required section count={len(matches)}")  # Report the structural failure.
                start, level = matches[0]  # Use the unique matching section only.
                end = next(  # Stop at the next peer or parent heading.
                    (index for index, depth, _ in headings if index > start and depth <= level), len(lines)
                )
                logging.debug("Located required section from line %s to %s", start + 1, end)  # Measure its boundary.
                return lines[start + 1 : end]  # Correct text outside this boundary cannot satisfy the guard.

        class Text:  # Preserve executable literals while removing inactive Markdown structure.
            """Remove comments and quotes only outside fenced code."""

            def __init__(self) -> None:  # Keep rendering state within one document invocation.
                self.fence: str | None = None  # Preserve every literal line inside a code fence.
                self.comment = False  # Suppress only actual outside-fence HTML comments.

            def comments(self, line: str) -> str:  # Preserve multiline outside-fence comment boundaries.
                parts: list[str] = []  # Keep visible text on both sides of a real Markdown comment.
                for part in re.split(r"(<!--|--!?>)", line):  # Recognize both HTML terminators before validation.
                    if part == "<!--":  # Open a real outside-fence comment.
                        self.comment = True  # Hide subsequent Markdown structure until the close.
                    elif part == "--!>" and self.comment:
                        raise ValueError("unsupported HTML comment terminator")
                    elif part == "-->" and self.comment:  # Close only a currently open comment.
                        self.comment = False  # Restore active Markdown structure.
                    elif not self.comment:  # Retain visible text without inventing content.
                        parts.append(part)  # Preserve real heading and label spelling.
                return "".join(parts)  # Keep original line positions for section and next-block checks.

            def line(self, raw: str) -> str:  # Do not remove literal comments or quote operators from code.
                if self.fence is not None:  # Executable and dormant fenced text has literal Markdown characters.
                    if raw.strip() == self.fence:  # Close only the current exact delimiter.
                        self.fence = None  # Restore outside-fence rendering after the close.
                    return raw  # Keep command values and unsupported operators intact for semantic rejection.
                visible = self.comments(raw)  # Remove only actual outside-fence comments.
                if visible.lstrip().startswith(">"):  # A quoted procedure cannot define active structure.
                    return ""  # Preserve position without promoting quoted text.
                marker = re.match(r"^\s*(`{3,}|~{3,})", visible)  # Enter literal code state for every fence language.
                if marker:  # Code markers inside hidden comments never reach this branch.
                    self.fence = marker.group(1)  # Preserve delimiter type and length.
                return visible  # Keep exact visible structure outside the fence.

            @classmethod
            def visible(cls, text: str) -> list[str]:  # Produce active structure without changing command semantics.
                logging.info("Reading literal-aware Markdown structure")  # Announce the bounded text transformation.
                reader = cls()  # Keep comment and fence state local to this one input.
                lines = [reader.line(line) for line in text.splitlines()]  # Preserve literal fenced command text.
                logging.debug("Read %s literal-aware Markdown lines", len(lines))  # Measure actual input coverage.
                return lines  # Retain exact positions for owned sections and active labels.

        @staticmethod
        def active(lines: list[str]) -> list[tuple[int, str]]:  # Keep headings and labels outside all fences.
            logging.info("Selecting active Markdown lines")  # Announce the structural filter.
            outside: list[tuple[int, str]] = []  # Do not use text inside executable or dormant code blocks.
            marker: str | None = None  # Track the exact current fence delimiter.
            for index, line in enumerate(lines):  # Preserve line positions for the next-block requirement.
                if marker is not None:  # Content inside a fence cannot define an active heading or label.
                    if line.strip() == marker:  # Close only the matching supported fence.
                        marker = None  # Restore active Markdown parsing after the close.
                    continue  # Do not read fenced examples as procedure structure.
                match = re.match(r"^\s*(`{3,}|~{3,})", line)  # Recognize all code fences, including dormant languages.
                if match:  # A fence suppresses labels and headings until its closing delimiter.
                    marker = match.group(1)  # Keep delimiter length and character type.
                    continue  # The opening fence itself cannot be a label.
                outside.append((index, line))  # Retain only genuinely active Markdown lines.
            logging.debug("Selected %s active Markdown lines", len(outside))  # Measure the completed filter.
            return outside  # Let callers validate exact required structures.

        @staticmethod
        def block(lines: list[str], start: int) -> tuple[str, str]:  # Require the next block to be executable.
            if start >= len(lines):  # A label without a next block is not a complete procedure.
                raise ValueError("active label has no executable fence")  # Name the missing active command.
            opening = re.fullmatch(r"(`{3,}|~{3,})(powershell|bash|sh)", lines[start].strip())  # Narrow shell profiles.
            if opening is None:  # Prose, a quoted example, or a text fence cannot execute this procedure.
                raise ValueError("active label requires a supported executable fence")  # Reject unsupported grammar.
            end = next(  # Require a real closing fence before reading commands.
                (index for index in range(start + 1, len(lines)) if lines[index].strip() == opening.group(1)), None
            )
            if end is None:  # An unterminated fence cannot provide an unambiguous command.
                raise ValueError("active executable fence has no closing delimiter")  # Fail closed.
            return opening.group(2), "\n".join(lines[start + 1 : end])  # Preserve raw quotes and continuations.

        @classmethod
        def fences(cls, lines: list[str]) -> dict[str, tuple[str, str]]:  # Require all four visible active labels.
            logging.info("Reading active procedure fences")  # Announce the structural decision.
            active = cls.active(lines)  # Exclude labels inside comments, quotes, and code fences.
            fences: dict[str, tuple[str, str]] = {}  # Retain exactly one supported fence per required label.
            for label in SectionCommands.LABELS:  # Validate every required active procedure part.
                positions = [index for index, line in active if line.strip() == label]  # Count actual active labels.
                if len(positions) != 1:  # Duplicate labels fail instead of selecting a convenient example.
                    raise ValueError(  # Name the ambiguous or absent part.
                        f"active label {label} count={len(positions)}"
                    )  # Name the ambiguous or absent part.
                start = next(  # Require the immediate next nonblank block.
                    (index for index in range(positions[0] + 1, len(lines)) if lines[index].strip()), len(lines)
                )
                fences[label] = cls.block(lines, start)  # Require the next nonblank block to be executable.
            logging.debug("Read %s active procedure fences", len(fences))  # Measure actual completed structure.
            return fences  # Correct unused examples remain outside this decision surface.

    class Shell:  # Preserve variable expansion while rejecting unsupported execution forms.
        """Normalize only verified plain CLI and token-preserving proxy syntax."""

        class Text:  # Separate real shell comments from literal values and unsupported quoting.
            """Support whole-value quotes without guessing another shell's escape grammar."""

            @staticmethod
            def quotes(text: str) -> None:  # Reject unsupported concatenation and literal variable expansion.
                if "\\" in text or "`" in text:  # Supported terminal continuations were removed before this stage.
                    raise ValueError("unsupported shell escape grammar")  # Do not erase escaping semantics.
                for match in re.finditer(r"""(['"])(.*?)\1""", text):  # Check each actual whole quoted segment.
                    if match.group(1) == "'" and "$" in match.group(2):  # Single quotes disable intended expansion.
                        raise ValueError("literal single-quoted variable expansion")  # Preserve base semantics.
                    if (  # Support whole quoted values and option=value without concatenation.
                        match.start() and not text[match.start() - 1].isspace() and text[match.start() - 1] != "="
                    ):
                        raise ValueError("unsupported quote concatenation")  # Allow whole values and option=value only.
                    if (  # Do not reinterpret PowerShell doubled quotes as Bash concatenation.
                        match.end() < len(text) and not text[match.end()].isspace() and text[match.end()] != "#"
                    ):
                        raise ValueError(  # Reject unverified PowerShell quote concatenation.
                            "unsupported quote concatenation"
                        )  # Reject PowerShell doubled-quote ambiguity.

            @classmethod
            def active(cls, text: str) -> str:  # Remove only real unquoted comments at a token boundary.
                logging.info("Reading active shell text")  # Announce literal-preserving comment handling.
                quote: str | None = None  # Keep hashes inside quoted values literal.
                end = len(text)  # Retain all input when no genuine comment begins.
                for index, character in enumerate(text):  # Read characters without evaluating shell expressions.
                    if character in {"'", '"'} and quote in {None, character}:  # Change only matching quote state.
                        quote = None if quote else character  # Preserve the selected whole-value quote boundary.
                    elif (  # Remove only real unquoted token-boundary comments.
                        character == "#" and quote is None and (index == 0 or text[index - 1].isspace())
                    ):  # Real comment.
                        end = index  # Stop only at a genuine unquoted comment token.
                        break  # Do not inspect dormant comment text as executable syntax.
                active = text[:end]  # Preserve midword hashes and all literal quoted content.
                cls.quotes(active)  # Reject unsupported quoting before harmless quote normalization.
                logging.debug("Read %s active shell characters", len(active))  # Measure actual active input.
                return active  # Correct text inside comments cannot supply required controls.

            @classmethod
            def binding(cls, text: str, shell: str) -> str:
                """Check assignment syntax before tokenization removes the quotes."""
                active = cls.active(text)
                if re.match(r"^\$?BASE_REF\s*=", active) is None:
                    return active
                logging.info("Checking the intended base assignment for %s", shell)
                branch = r"[A-Za-z0-9][A-Za-z0-9._/-]*"
                quoted = rf"""(["']){branch}\1"""
                pattern = rf"\$BASE_REF\s*=\s*{quoted}" if shell == "powershell" else rf"BASE_REF=(?:{branch}|{quoted})"
                if re.fullmatch(pattern, active.strip()) is None:
                    raise ValueError(f"incorrect intended-base assignment for {shell}")
                logging.debug("Checked one intended base assignment for %s", shell)
                return active

        @staticmethod
        def logical_lines(text: str, shell: str) -> list[str]:  # Preserve supported continuation semantics.
            logging.info("Reading %s logical command lines", shell)  # Announce the shell-profile transformation.
            if shell not in {"powershell", "bash", "sh"}:  # Do not guess an unsupported shell grammar.
                raise ValueError("unsupported shell profile")  # Block unknown execution semantics.
            marker = "`\n" if shell == "powershell" else "\\\n"  # Only terminal continuations preserve tokens.
            joined = text.replace("\r\n", "\n").replace(marker, " ")  # Join supported physical continuations.
            lines = [  # Exclude dormant comments and empty physical lines.
                line.strip() for line in joined.splitlines() if line.strip() and not line.lstrip().startswith("#")
            ]
            logging.debug("Read %s logical command lines", len(lines))  # Measure active lines, not comments.
            return lines  # Keep unsupported control structures visible for rejection.

        @staticmethod
        def tokenize(text: str, shell: str | None = None) -> list[str]:
            """Preserve expansion and assignment syntax before removing quotes."""
            logging.info("Decoding active command tokens")  # Announce non-executing shell parsing.
            text = (
                SectionCommands.Shell.Text.binding(text, shell)
                if shell is not None
                else SectionCommands.Shell.Text.active(text)
            )
            lexer = shlex.shlex(text, posix=True)  # Tokenize without executing any shell text.
            lexer.whitespace_split = True  # Preserve complete option-value tokens.
            lexer.commenters = ""  # Active-text handling already preserves literal midword hashes.
            words = list(lexer)  # Decode quotes while retaining literal variable names.
            if any(re.search(r"[|;&<>`()\\]|\$\(", word) for word in words):  # Reject unsupported execution grammar.
                raise ValueError("unsupported shell construct")  # Never evaluate substitutions or pipelines.
            words = [word.replace("${BASE_REF}", "$BASE_REF") for word in words]  # Normalize expanding variable forms.
            logging.debug("Decoded %s active command tokens", len(words))  # Measure actual tokens.
            return words  # Static quoting is harmless only when expected semantic controls still match.

        @staticmethod
        def prefix(words: list[str]) -> list[str]:  # Accept only verified token-preserving prefix semantics.
            if words[:2] == ["rtk", "proxy"]:  # The proxy forwards exact command arguments and output.
                return words[2:]  # Remove only this known prefix.
            if words and words[0] == "rtk":  # Other wrappers can transform arguments or select another command.
                raise ValueError("unsupported RTK wrapper")  # Do not assume equivalence without verified semantics.
            return words  # A plain command retains the same contract.

        @classmethod
        def commands(cls, text: str, shell: str) -> list[list[str]]:  # Keep every active logical command visible.
            logging.info("Decoding active %s fence commands", shell)  # Announce command-list construction.
            commands = [  # Do not select hidden invocations.
                cls.tokenize(line, shell) for line in cls.logical_lines(text, shell)
            ]  # Do not select hidden invocations.
            commands = [words for words in commands if words]  # Exclude comment-only lines, not unsupported commands.
            logging.debug("Decoded %s active fence commands", len(commands))  # Measure actual active invocations.
            return commands  # Callers require exact command counts and supported execution forms.

    @classmethod
    def procedures(cls, text: str, path: str) -> dict[str, list[list[str]]]:  # Read only the owned named section.
        logging.info("Reading the required local procedure in %s", path)  # Announce the independent guide decision.
        section = cls.Markdown.Outline.section(  # Enforce exact heading ownership and boundaries.
            text, cls.GUIDES[path]
        )  # Enforce exact heading ownership and boundaries.
        fences = cls.Markdown.fences(section)  # Reject missing, duplicated, or inactive labels.
        commands = {  # Decode active fences.
            label: cls.Shell.commands(body, shell) for label, (shell, body) in fences.items()
        }  # Decode active fences.
        logging.debug("Read %s active procedure parts in %s", len(commands), path)  # Measure completed parsing.
        return commands  # Never execute document commands.


class CommandControls:  # Reject commands that look similar but change gate behavior.
    """Compare supported commands without erasing expansion semantics."""

    PATHS = (  # These are required input locations, not a cached full-gate trigger list.
        ".github/test-quality-config.toml",  # Reject missing or substituted repository settings.
        ".github/test-quality-baseline.json",  # Reject missing or substituted repository baseline.
    )

    class Options:  # Retain observed conflicts before collapsing harmless singleton repeats.
        """Decode the small allowed analyzer surface and reject conflicting values."""

        supported = {  # Reject every control outside this small documented surface.
            "--gate",
            "--config",
            "--baseline",
            "--changed-from",
            "--full-gate-path",
        }  # Reject unknown controls.

        @staticmethod
        def consume(words: list[str], index: int) -> tuple[str, str, int]:  # Keep option parsing explicit.
            option, separator, value = words[index].partition("=")  # Support installed option=value forms.
            if (  # Reject roots, suppression, rewrite, and unknown controls.
                option not in CommandControls.Options.supported
            ):  # Roots, suppression, and rewrite controls are forbidden.
                name = (  # Do not expose values.
                    option if re.fullmatch(r"--[A-Za-z][A-Za-z0-9-]*", option) else "grammar"
                )  # Do not expose values.
                raise ValueError(f"unsupported analyzer control {name}")  # Name the unsupported control.
            if option == "--gate":  # Gate is a flag, not an option with a value.
                if separator:  # Even a similar-looking boolean assignment changes CLI grammar.
                    raise ValueError("--gate cannot take a value")  # Reject unsupported flag syntax.
                return option, "", index + 1  # Record the presence of the required flag.
            if not separator:  # Separate-value options must have a following value.
                index += 1  # Advance only for the installed separate-value form.
                value = words[index] if index < len(words) else ""  # Keep missing values explicit.
            if not value or value.startswith("--"):  # Another option cannot serve as this option's value.
                raise ValueError(f"{option} requires a value")  # Name the incomplete control.
            if option != "--changed-from":  # Static input and trigger paths must not contain shell expansion.
                value = CommandControls.Options.static_path(option, value)  # Normalize only supported local paths.
            return option, value, index + 1  # Preserve exact expansion semantics for the base control.

        @staticmethod
        def static_path(option: str, value: str) -> str:  # Keep fixture writes and comparisons repository-relative.
            logging.info("Checking static path control %s", option)  # Announce path semantics validation.
            if "$" in value or ":" in value or value.startswith(("/", "~")) or ".." in value.split("/"):  # Stay local.
                raise ValueError(f"{option} requires a static repository path")  # Reject expansion and external paths.
            normalized = value.removeprefix("./")  # Normalize harmless repository-relative spelling only.
            logging.debug("Checked one static path control %s", option)  # Record completed semantic validation.
            return normalized  # Keep the supplied live control's actual meaning.

        @staticmethod
        def record(  # A final correct value must not hide an earlier conflicting value.
            values: dict[str, list[str]], option: str, value: str
        ) -> None:  # Reject conflicts before collapsing repeats.
            prior = values.setdefault(option, [])  # Keep each observed control's values visible.
            if option == "--full-gate-path" and value in prior:  # Repeated explicit paths are ambiguous contract input.
                raise ValueError("duplicate --full-gate-path value")  # Do not normalize duplicate explicit controls.
            if (  # A final correct value cannot hide drift.
                option != "--full-gate-path" and prior and value not in prior
            ):  # A final correct value cannot hide drift.
                raise ValueError(f"conflicting {option} values")  # Reject earlier and later conflicts equally.
            if value not in prior:  # Identical singleton repeats preserve meaning.
                prior.append(value)  # Keep one semantic value per singleton.

        @classmethod
        def parse(  # Decode every actual token instead of searching for correct text.
            cls, command: list[str]
        ) -> dict[str, tuple[str, ...]]:  # Reject other executables and obsolete entry points.
            logging.info("Decoding analyzer option controls")  # Announce the semantic transformation.
            words = SectionCommands.Shell.prefix(command)  # Accept only the plain CLI or verified proxy prefix.
            if not words or words[0] != "test-quality-analyzer":  # Never search inside echoed or dormant commands.
                raise ValueError("required analyzer executable is absent")  # Reject obsolete module and wrapper forms.
            values: dict[str, list[str]] = {}  # Keep all values before checking conflicts.
            index = 1  # Start after the actual supported executable.
            while index < len(words):  # Decode every token instead of ignoring extra grammar.
                option, value, index = cls.consume(words, index)  # Require a supported complete control.
                cls.record(values, option, value)  # Reject duplicate paths and conflicting singleton values.
            controls = {option: tuple(entries) for option, entries in values.items()}  # Freeze semantic values.
            logging.debug("Decoded %s distinct analyzer controls", len(controls))  # Measure completed decoding.
            return controls  # Preserve live explicit values without a cached path list.

    @staticmethod
    def analyzer(  # Require one complete active command with the live semantic controls.
        commands: list[list[str]], expected: dict[str, tuple[str, ...]]
    ) -> dict[str, tuple[str, ...]]:
        """Require one active invocation with exactly the live semantic controls."""
        logging.info("Comparing active analyzer controls with live CI")  # Announce the semantic decision.
        if len(commands) != 1:  # Comments and extra commands cannot define one required active check.
            raise ValueError(f"analyzer invocation_count={len(commands)}")  # Name missing or ambiguous execution.
        observed = CommandControls.Options.parse(commands[0])  # Decode the actual active command.
        if observed.keys() != expected.keys():  # Extra controls can alter selection or gate behavior.
            missing = sorted(expected.keys() - observed.keys())  # Identify omitted required controls.
            extra = sorted(observed.keys() - expected.keys())  # Identify unsupported semantic additions.
            raise ValueError(f"analyzer controls differ missing={missing} extra={extra}")  # Report named drift.
        for option, values in expected.items():  # Check every singleton and live repeatable control.
            actual = (  # Ignore path order.
                frozenset(observed[option]) if option == "--full-gate-path" else observed[option]
            )  # Ignore path order.
            required = frozenset(values) if option == "--full-gate-path" else values  # Keep singleton meaning exact.
            if actual != required:  # Different values cannot pass through similar text.
                raise ValueError(f"incorrect {option} control")  # Name the failed contract without input values.
        logging.debug("Compared %s active analyzer controls", len(observed))  # Report actual comparison coverage.
        return observed  # Supply the successfully validated live or guide controls.

    class Base:  # Reject a resolved substitute when the intended fetched reference differs.
        """Validate each part of the intended fetched-base relationship."""

        @staticmethod
        def assignment(words: list[str]) -> None:  # Require the named operator choice.
            logging.info("Checking intended BASE_REF assignment")  # Announce the binding decision.
            assignment = " ".join(words)  # Normalize harmless spacing after quote validation.
            if re.fullmatch(r"\$?BASE_REF\s*=\s*[A-Za-z0-9][A-Za-z0-9._/-]*", assignment) is None:  # Require a branch.
                raise ValueError("incorrect intended BASE_REF assignment")  # Reject empty or substituted variables.
            logging.debug("Checked one intended BASE_REF assignment")  # Record the completed decision.

        @staticmethod
        def fetch(command: list[str]) -> None:  # Require matching source and remote-tracking destination.
            logging.info("Checking intended-base fetch controls")  # Announce non-executing fetch validation.
            words = SectionCommands.Shell.prefix(command)  # Accept only plain Git or verified proxy semantics.
            expected = [  # Match the base.
                "git",
                "fetch",
                "origin",
                "+refs/heads/$BASE_REF:refs/remotes/origin/$BASE_REF",
            ]  # Match the base.
            if (  # Require the same intended fetch source and destination.
                words.count("--no-tags") != 1 or [word for word in words if word != "--no-tags"] != expected
            ):
                raise ValueError("incorrect intended-base fetch destination")  # Reject either endpoint substitution.
            logging.debug("Checked one intended-base fetch destination")  # Record the completed relationship check.

        @staticmethod
        def resolution(command: list[str]) -> None:  # Require resolution of the same fetched commit.
            logging.info("Checking intended-base commit resolution")  # Announce the reference decision.
            words = SectionCommands.Shell.prefix(command)  # Reject unverified execution wrappers.
            expected = ["git", "rev-parse", "origin/$BASE_REF^{commit}"]  # Resolve the same intended base.
            if (  # Resolve the same intended fetched commit.
                words.count("--verify") != 1 or [word for word in words if word != "--verify"] != expected
            ):
                raise ValueError("incorrect intended-base commit resolution")  # Reject a different valid reference.
            logging.debug("Checked one intended-base commit resolution")  # Record the completed decision.

        @classmethod
        def validate(cls, commands: list[list[str]]) -> None:  # Preserve the full three-command relationship.
            if len(commands) != 3:  # Require active assignment, fetch, and resolution.
                raise ValueError("intended base requires three active commands")  # Reject dormant or missing commands.
            cls.assignment(commands[0])  # Validate the named intended variable.
            cls.fetch(commands[1])  # Validate matching remote source and destination.
            cls.resolution(commands[2])  # Validate actual commit-resolution syntax.

    @staticmethod
    def preflight(commands: list[list[str]]) -> None:  # Require direct measured input validation before either gate.
        logging.info("Checking the active required-input preflight")  # Announce the independent command check.
        expected = [  # Keep one direct class invocation rather than a text-only or skipped substitute.
            "python",
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-s",
            "-q",
            "tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides",
        ]
        if (  # Require exact direct invocation.
            len(commands) != 1 or SectionCommands.Shell.prefix(commands[0]) != expected
        ):  # Require exact direct invocation.
            raise ValueError("incorrect required-input preflight")  # Block a bypass of the four required reads.
        logging.debug("Checked one direct required-input preflight")  # Record completed validation coverage.


class CiGateContract:  # Obtain scope controls only from the current named executable step.
    """Decode the named live ratchet step without running shell text."""

    class Workflow:  # Reject missing or ambiguous authority before decoding script text.
        """Require the actual named job, unique step, and expanding environment bindings."""

        @staticmethod
        def mapping(value: object, name: str) -> dict[str, object]:  # Narrow only checked YAML structures.
            if not isinstance(value, dict):  # Missing or wrong-shaped workflow sections cannot provide authority.
                raise ValueError(f"workflow requires {name} mapping")  # Name the unusable structure.
            return cast(dict[str, object], value)  # Access required string keys without suppressing types.

        @classmethod
        def step(cls, text: str) -> dict[str, object]:  # Locate actual authority without a whole-file command search.
            logging.info("Decoding the named live CI ratchet step")  # Announce safe YAML parsing.
            document = cls.mapping(yaml.safe_load(text), "document")  # Use safe loading, never executable YAML objects.
            jobs = cls.mapping(document.get("jobs"), "jobs")  # Require current workflow job structure.
            job = cls.mapping(jobs.get("test_quality_gate"), "test_quality_gate")  # Do not read another job.
            steps = job.get("steps")  # Read only this job's active steps.
            if not isinstance(steps, list):  # Missing steps cannot define a contract.
                raise ValueError("workflow requires test_quality_gate steps")  # Fail without a cached command.
            named = [  # Require exactly one named live ratchet step.
                cls.mapping(step, "step")
                for step in steps
                if isinstance(step, dict) and step.get("name") == "Run test quality ratchet"
            ]
            if len(named) != 1:  # Duplicate names fail instead of choosing a convenient step.
                raise ValueError(f"named ratchet step count={len(named)}")  # Report the authority failure.
            logging.debug("Located one named live CI ratchet step")  # Record the unique authority decision.
            return named[0]  # Return only the actual named live step.

        @classmethod
        def script(cls, step: dict[str, object]) -> str:  # Check metadata before decoding the active script.
            logging.info("Checking live CI environment and script bindings")  # Announce metadata validation.
            environment = cls.mapping(step.get("env"), "ratchet env")  # Preserve event and base expansion sources.
            if (  # Preserve actual event and intended-base bindings.
                environment.get("EVENT_NAME") != "${{ github.event_name }}"
                or environment.get("BASE_REF") != "${{ github.base_ref }}"
            ):
                raise ValueError(  # Reject a substituted live event or base source.
                    "incorrect live event or intended-base binding"
                )  # Reject a substituted runtime reference.
            script = step.get("run")  # Read the actual active script, not a comment or neighboring step.
            if (  # Reject unsupported or unusable active scripts.
                not isinstance(script, str) or not script.strip() or step.get("shell") not in {None, "bash"}
            ):
                raise ValueError(  # Fail closed on unsupported grammar.
                    "named ratchet step requires a supported Bash script"
                )  # Fail closed on unsupported grammar.
            logging.debug(  # Measure authority.
                "Decoded one live ratchet step with %s environment bindings", len(environment)
            )  # Measure authority.
            return script  # Never execute workflow text.

    class Script:  # Decode only the supported event-specific array grammar without execution.
        """Decode only the supported PR-only scope array and one analyzer invocation."""

        @staticmethod
        def scope(lines: list[str]) -> list[str]:  # Preserve empty push/manual scope and intended-base expansion.
            logging.info("Decoding the live pull-request scope array")  # Announce safe script interpretation.
            if len(lines) != 5 or lines[0] != "scope=()" or lines[3] != "fi":  # Support one bounded executable grammar.
                raise ValueError("unsupported live scope script grammar")  # Do not guess meaning from command text.
            if any("$" in value for value in re.findall(r"'[^']*'", lines[1])):  # Single quotes make the event literal.
                raise ValueError("literal live event expansion")  # Preserve actual condition semantics.
            condition = shlex.split(lines[1])  # Parse the known condition without evaluating it.
            if condition != ["if", "[", "$EVENT_NAME", "=", "pull_request", "];", "then"]:  # Populate only for PR.
                raise ValueError("incorrect live pull-request condition")  # Reject push/full-scope inversions.
            assignment = re.fullmatch(r"scope=\((.*)\)", lines[2])  # Require the active PR-only array assignment.
            if assignment is None:  # Missing arrays cannot define scoped controls.
                raise ValueError("incorrect live scope array assignment")  # Fail without a cached fallback.
            words = SectionCommands.Shell.tokenize(assignment.group(1))  # Preserve array values and expanding base.
            logging.debug("Decoded %s live PR scope tokens", len(words))  # Measure actual decoded controls.
            return words  # Push and manual runs retain the separate empty array.

        @classmethod
        def decode(cls, script: str) -> tuple[list[str], list[str]]:  # Expand supported arrays without shell execution.
            lines = SectionCommands.Shell.logical_lines(script, "bash")  # Normalize harmless terminal continuation.
            scope = cls.scope(lines)  # Require PR-only scope and the empty full-suite default.
            words = SectionCommands.Shell.tokenize(lines[4])  # Decode the one actual analyzer invocation.
            if (  # Require expanding quoted array insertion.
                words.count("${scope[@]}") != 1 or '"${scope[@]}"' not in lines[4]
            ):  # Require expanding quoted array insertion.
                raise ValueError("incorrect live scope-array insertion")  # Reject absent, duplicated, or literal scope.
            position = words.index("${scope[@]}")  # Preserve the array's actual argument position.
            full = words[:position] + words[position + 1 :]  # Push and manual events keep the empty array.
            scoped = words[:position] + scope + words[position + 1 :]  # PR events receive the live scope tokens.
            logging.debug("Decoded full=%s and scoped=%s live command tokens", len(full), len(scoped))  # Measure.
            return full, scoped  # Let semantic option checks reject hidden or extra executable controls.

    def __init__(  # Count distinct successfully decoded live controls once.
        self, full: dict[str, tuple[str, ...]], scoped: dict[str, tuple[str, ...]]
    ) -> None:
        """Count distinct successfully decoded live controls once per invocation."""
        logging.info("Measuring distinct live gate trigger controls")  # Announce dynamic control accounting.
        self.full = full  # Preserve the validated push/manual command controls.
        self.scoped = scoped  # Preserve the validated pull-request command controls.
        self.explicit_paths = frozenset(  # Derive live values, never cached constants.
            scoped.get("--full-gate-path", ())
        )  # Derive live values, never cached constants.
        self.automatic_paths = frozenset((*full["--config"], *full["--baseline"]))  # Derive automatic input triggers.
        self.effective_paths = self.explicit_paths | self.automatic_paths  # Count distinct effective path controls.
        logging.debug(  # Report actual distinct live-control measurements.
            "Measured explicit=%s automatic=%s effective=%s",
            len(self.explicit_paths),
            len(self.automatic_paths),
            len(self.effective_paths),
        )

    @classmethod
    def from_text(cls, text: str) -> CiGateContract:  # Derive every successfully decoded live control.
        step = cls.Workflow.step(text)  # Locate the unique named job and step from current YAML.
        script = cls.Workflow.script(step)  # Require the actual event and intended-base bindings.
        full_words, scoped_words = cls.Script.decode(script)  # Decode the supported actual script without execution.
        required: dict[str, tuple[str, ...]] = {  # Keep singleton and repeatable control types compatible.
            "--gate": ("",),
            "--config": (CommandControls.PATHS[0],),
            "--baseline": (CommandControls.PATHS[1],),
        }
        full = CommandControls.analyzer([full_words], required)  # Reject changed scope on push/manual events.
        scoped = CommandControls.Options.parse(scoped_words)  # Obtain the actual live additional path controls.
        expected = {  # Preserve the live intended-base relationship.
            **required,
            "--changed-from": ("origin/$BASE_REF",),
        }  # Preserve the live intended-base relationship.
        if "--full-gate-path" in scoped:  # Dynamic explicit controls remain live authority.
            expected["--full-gate-path"] = scoped[  # Do not replace them with a cached expected list.
                "--full-gate-path"
            ]  # Do not replace them with a cached expected list.
        CommandControls.analyzer([scoped_words], expected)  # Reject omitted base and unsupported extra controls.
        return cls(full, scoped)  # Count controls only after complete supported decoding succeeds.


class GuideGuard:  # Preserve independent input failures and completed guide decisions.
    """Compare every available guide and report completed operations."""

    class Decision:  # Compare each guide independently with the same current CI authority.
        """Validate one independent guide against the decoded live contract."""

        def __init__(self, path: str, contract: CiGateContract) -> None:  # Keep guide identity and authority together.
            self.path = path  # Preserve the exact input name for failure reports.
            self.contract = contract  # Never compare against copied fixture expectations.

        def validate(self, text: str) -> bool:  # Complete one pass or failure decision without executing commands.
            logging.info("Checking active local guide %s", self.path)  # Announce the independent guide comparison.
            commands = SectionCommands.procedures(text, self.path)  # Read only the named section's four active fences.
            CommandControls.Base.validate(  # Validate matching assignment, fetch, and resolution.
                commands[SectionCommands.LABELS[0]]
            )  # Validate matching assignment, fetch, and resolution.
            CommandControls.preflight(commands[SectionCommands.LABELS[1]])  # Require the direct four-input guard.
            CommandControls.analyzer(  # Match live PR controls.
                commands[SectionCommands.LABELS[2]], self.contract.scoped
            )  # Match live PR controls.
            CommandControls.analyzer(  # Match live full-suite controls.
                commands[SectionCommands.LABELS[3]], self.contract.full
            )  # Match live full-suite controls.
            logging.debug("Checked four active procedure parts in %s", self.path)  # Record completed coverage.
            return True  # Successful parsing alone does not bypass semantic comparisons.

        @staticmethod
        def inputs(ledger: InputLedger) -> CiGateContract | None:  # Complete independent required input operations.
            paths = (*SectionCommands.GUIDES, ".github/workflows/ci.yml", *CommandControls.PATHS)  # Four inputs.
            ledger.read_all(paths)  # Attempt every read once, including later inputs after failures.
            ledger.validate(CommandControls.PATHS[0], InputLedger.Validation.settings)  # Validate readable settings.
            ledger.validate(CommandControls.PATHS[1], InputLedger.Validation.baseline)  # Validate usable identities.
            return ledger.validate(".github/workflows/ci.yml", CiGateContract.from_text)  # Decode live authority.

        @classmethod
        def guides(cls, ledger: InputLedger, contract: CiGateContract) -> None:  # Preserve independent guide decisions.
            for path in SectionCommands.GUIDES:  # Complete every available guide decision.
                if path in ledger.texts:  # A failed read cannot provide a valid empty document.
                    decision = cls(path, contract)  # Bind this guide to successfully decoded live controls.
                    ledger.validate(path, decision.validate)  # Count only successful complete validations.
                    ledger.progress.guide_checks.add(path)  # Count completed pass and failure decisions separately.

    def __init__(self, root: Path) -> None:  # Bind required reads to one explicit repository.
        self.ledger = InputLedger(root)  # Keep actual progress and named errors in one invocation.
        self.contract: CiGateContract | None = None  # Do not claim decoded controls before parsing.

    def run(self) -> bool:  # Complete one measured preflight without executing document commands.
        logging.info("Checking required local test-quality inputs and procedures")  # Announce this measured invocation.
        self.contract = self.Decision.inputs(self.ledger)  # Attempt and validate every required independent input.
        if self.contract is not None:  # Unrecognized CI cannot supply a valid guide comparison.
            self.Decision.guides(self.ledger, self.contract)  # Complete every available independent guide decision.
        passed = (  # Require every attempted input to finish its complete validation.
            self.contract is not None
            and not self.ledger.errors
            and self.ledger.progress.validations == self.ledger.progress.attempted
        )
        print(self.summary())  # Always expose measured progress, including partial failures.
        for error in self.ledger.errors:  # Preserve every independent named failure in the direct output.
            path, reason = error.split(": ", 1)  # Separate safe input identity from the named failure reason.
            print(  # Never print input text or credentials.
                f"local_test_quality_guard: error input={path} reason={reason}"
            )  # Never print input text or credentials.
        logging.debug("Local test-quality guard status=%s counts=%s", passed, self.counts())  # Record actual outcome.
        return passed  # A skip, unsupported grammar, or unreadable input cannot pass.

    def counts(self) -> dict[str, int]:  # Derive measurements only from completed operations.
        progress = self.ledger.progress  # Read recorded operations rather than expected success constants.
        return {  # Decode path controls only when live CI validation completed.
            "inputs_attempted": len(progress.attempted),
            "input_reads": len(progress.reads),
            "input_validations": len(progress.validations),
            "guide_reads": len(progress.guide_reads),
            "guide_checks": len(progress.guide_checks),
            "explicit_paths": len(self.contract.explicit_paths) if self.contract else 0,
            "automatic_paths": len(self.contract.automatic_paths) if self.contract else 0,
            "effective_paths": len(self.contract.effective_paths) if self.contract else 0,
        }

    def summary(self) -> str:  # Report measured progress without expected success constants.
        status = (  # Require inputs.
            "pass"
            if self.contract is not None
            and not self.ledger.errors
            and self.ledger.progress.validations == self.ledger.progress.attempted
            else "fail"
        )  # Require inputs.
        counts = " ".join(  # Use actual completed measurements.
            f"{name}={count}" for name, count in self.counts().items()
        )  # Use actual completed measurements.
        return f"local_test_quality_guard: status={status} {counts}"  # Keep one stable ASCII summary shape.
