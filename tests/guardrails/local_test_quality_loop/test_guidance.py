"""Prove input accounting and active local procedure decisions."""

from __future__ import annotations  # Keep fixture annotations independent of collection order.

import logging  # Record each controlled input mutation.
from pathlib import Path  # Keep fixture writes inside pytest temporary directories.

import pytest  # Run explicit positive and negative guard decisions.

from .fixtures import GuidanceFixture  # Keep all guide mutations inside temporary inputs.
from .guard import GuideGuard, InputLedger, SectionCommands  # Exercise direct guard decisions.


class TestInputLedger:  # Prove failures do not become claimed successful reads.
    """Prove all four independent read attempts and validation measurements."""

    paths = (  # Define expectations independently of the guard's manifest.
        ".github/copilot-instructions.md",  # Count the one required guide.
        ".github/workflows/ci.yml",  # Count the live contract input.
        ".github/test-quality-config.toml",  # Count the required settings input.
        ".github/test-quality-baseline.json",  # Count the required baseline input.
    )

    @classmethod
    def prepare(cls, root: Path) -> InputLedger:  # Build readable inputs without product dependencies.
        for path in cls.paths:  # Give every independent read a real file.
            logging.info("Preparing ledger input %s", path)  # Announce the fixture write.
            destination = root / path  # Confine the write to this temporary directory.
            destination.parent.mkdir(parents=True, exist_ok=True)  # Prepare only fixture directories.
            text = "[]\n" if path.endswith(".json") else ""  # Accept empty TOML and a usable empty baseline.
            destination.write_text(text, encoding="utf-8")  # Create real UTF-8 inputs for the ledger.
            logging.debug("Prepared ledger input %s with %s characters", path, len(text))  # Measure the write.
        return InputLedger(root)  # Return state with no claimed reads.

    def test_complete_reads(self, tmp_path: Path) -> None:  # Prove the successful accounting contract.
        ledger = self.prepare(tmp_path)  # Create all required inputs.
        ledger.read_all(self.paths)  # Exercise four real reads.
        assert ledger.progress.attempted == set(self.paths)  # Require every independent attempt.
        assert ledger.progress.reads == set(self.paths)  # Require every complete UTF-8 read.
        assert ledger.progress.guide_reads == set(self.paths[:1])  # Count only the one guide input.
        assert ledger.progress.guide_checks == set()  # Do not claim decisions from reads.
        assert ledger.progress.validations == set()  # Do not claim validations from reads.
        assert ledger.validate(self.paths[2], InputLedger.Validation.settings) is True  # Accept readable empty TOML.
        assert ledger.validate(self.paths[3], InputLedger.Validation.baseline) is True  # Accept empty identities.
        assert ledger.progress.validations == set(self.paths[2:])  # Measure only the two completed validations.
        assert ledger.errors == []  # Require named errors to remain empty only on success.

    @pytest.mark.parametrize("path", paths, ids=lambda path: f"T15-{path}")
    @pytest.mark.parametrize("form", ("missing", "directory", "invalid_utf8"))
    def test_failed_read(self, tmp_path: Path, path: str, form: str) -> None:  # Prove portable read failures.
        ledger = self.prepare(tmp_path)  # Keep the other three inputs readable.
        logging.info("Making ledger input %s %s", path, form)  # Identify the controlled failure.
        destination = tmp_path / path  # Keep the mutation inside the fixture.
        destination.unlink()  # Remove only this fixture's required file.
        if form == "directory":  # Use a genuine unreadable file input on every platform.
            destination.mkdir()  # Avoid permission tests that falsely pass as root.
        elif form == "invalid_utf8":  # Make the complete UTF-8 read fail.
            destination.write_bytes(b"\xff")  # Supply invalid bytes without changing permissions.
        logging.debug("Prepared ledger failure %s for %s", form, path)  # Confirm the controlled state.
        ledger.read_all(self.paths)  # Require later independent reads after the failure.
        assert ledger.progress.attempted == set(self.paths)  # Require all four attempted reads.
        assert ledger.progress.reads == set(self.paths) - {path}  # Do not count the failed read.
        assert ledger.progress.guide_reads == set(self.paths[:1]) - {path}  # Preserve a successful guide read.
        assert set(ledger.texts) == set(self.paths) - {path}  # Never retain unusable input as empty text.
        assert len(ledger.errors) == 1 and path in ledger.errors[0]  # Require the exact failed input.
        assert "read_failed" in ledger.errors[0]  # Distinguish read failure from validation failure.

    @pytest.mark.parametrize(
        ("path", "text"),
        (
            (paths[2], "[rules\n"),  # Reject malformed TOML without losing the completed read.
            (paths[3], "{"),  # Reject malformed JSON without losing the completed read.
            (paths[3], "{}"),  # Require a baseline list rather than an arbitrary JSON value.
            (paths[3], '[{"file_path": "tests/test_one.py"}]'),  # Require complete finding identities.
            (
                paths[3],
                '[{"category":"weak_assertion","file_path":"tests/test_one.py","line_number":true,"rule_id":"x"}]',
            ),  # Reject booleans as baseline line numbers.
        ),
        ids=("T15-toml", "T15-json", "T15-list", "T15-identity", "T15-line-type"),
    )
    def test_invalid_validation(self, tmp_path: Path, path: str, text: str) -> None:  # Keep failed validation visible.
        ledger = self.prepare(tmp_path)  # Preserve the three other required reads.
        logging.info("Writing invalid ledger content to %s", path)  # Announce the controlled parse failure.
        (tmp_path / path).write_text(text, encoding="utf-8")  # Mutate only the declared fixture input.
        logging.debug("Wrote %s invalid characters to %s", len(text), path)  # Measure the fixture write.
        ledger.read_all(self.paths)  # Count readable malformed text as a completed read.
        ledger.validate(self.paths[2], InputLedger.Validation.settings)  # Attempt settings independently.
        ledger.validate(self.paths[3], InputLedger.Validation.baseline)  # Attempt baseline independently.
        assert ledger.progress.reads == set(self.paths)  # Do not erase successful reads after parsing.
        assert ledger.progress.validations == set(self.paths[2:]) - {path}  # Count only usable inputs.
        assert len(ledger.errors) == 1 and path in ledger.errors[0]  # Name the failed validation.
        assert "validation_failed" in ledger.errors[0]  # Do not mislabel a parse failure as a read failure.


class TestGuideNormalization:  # Accept only changes that preserve executable control meaning.
    """Accept only token-preserving changes with unchanged control meaning."""

    class Variants:  # Build harmless syntax changes independently of guard normalization.
        """Construct harmless variants independently of guard tokenization."""

        @classmethod
        def command(  # Preserve all semantic controls while changing harmless spelling.
            cls, controls: dict[str, tuple[str, ...]], form: str
        ) -> str:  # Preserve expected semantic controls.
            logging.info("Constructing equivalent command form %s", form)  # Announce controlled normalization input.
            ordered = dict(reversed(tuple(controls.items()))) if form == "order" else controls  # Alter order only.
            command = GuidanceFixture.Template.analyzer(ordered)  # Start with the complete fixture controls.
            command = cls.paths(command, controls, form)  # Keep static quoting separate from variable expansion.
            command = cls.syntax(command, controls, form)  # Change only supported option and variable spelling.
            command = cls.continuation(command, form)  # Use the actual selected shell's terminal marker.
            logging.debug(  # Confirm the complete controlled transformation.
                "Constructed equivalent command form %s", form
            )  # Confirm the complete controlled transformation.
            return command  # Supply parser input, never selection expectations.

        @staticmethod
        def paths(  # Keep static path quoting separate from variable expansion.
            command: str, controls: dict[str, tuple[str, ...]], form: str
        ) -> str:  # Preserve static path semantics.
            logging.info("Preparing static fixture path spelling %s", form)  # Announce the controlled text transform.
            paths = [  # Change static values without disabling base expansion.
                value for option, values in controls.items() if option != "--changed-from" for value in values
            ]
            for path in paths:  # Change only static values, never the expanding intended base.
                if path and form in {"single_quotes", "double_quotes", "leading_dot"}:  # Keep static semantics.
                    value = f"'{path}'" if form == "single_quotes" else f'"{path}"'  # Preserve static quoted paths.
                    command = command.replace(path, f"./{path}" if form == "leading_dot" else value)  # Alter spelling.
            logging.debug("Prepared static fixture path spelling %s", form)  # Record the completed transformation.
            return command  # Keep variable-bearing base controls unchanged.

        @staticmethod
        def syntax(  # Keep option syntax changes separate from shell continuation.
            command: str, controls: dict[str, tuple[str, ...]], form: str
        ) -> str:  # Keep option meaning unchanged.
            logging.info("Preparing equivalent option syntax %s", form)  # Announce controlled option transformation.
            if form == "equals":  # Support installed singleton and repeatable option assignment forms.
                command = command.replace(  # Preserve singleton semantics with equals spelling.
                    "--config ", "--config="
                ).replace("--baseline ", "--baseline=")
                command = command.replace("--changed-from ", "--changed-from=").replace(  # Preserve scope semantics.
                    "--full-gate-path ", "--full-gate-path="
                )
            if form == "identical_repeats":  # Identical singleton repeats do not change the intended command.
                command += (  # Repeat only identical singleton controls.
                    f" --gate --config {controls['--config'][0]} --baseline {controls['--baseline'][0]}"
                )
            if form == "braced_base":  # Both shells expand this supported variable form.
                command = command.replace("$BASE_REF", "${BASE_REF}")  # Do not replace it with a literal branch.
            logging.debug("Prepared equivalent option syntax %s", form)  # Record the completed transformation.
            return command  # Keep every original scope and gate control.

        @staticmethod
        def continuation(command: str, form: str) -> str:  # Preserve real Bash and PowerShell line continuation.
            logging.info("Preparing fixture continuation form %s", form)  # Announce the shell-profile transformation.
            if form in {"bash_continuation", "powershell_continuation"}:  # Join only supported terminal markers.
                marker = "\\\n" if form == "bash_continuation" else "`\n"  # Use the actual selected shell's syntax.
                command = command.replace(" --", f" {marker}  --")  # Preserve argument boundaries.
            if form == "comments":  # Dormant inline text must not change a correct active command.
                command += (  # A real inline comment cannot change active controls.
                    " # Do not use 'origin/$BASE_REF' as a literal."  # Prove quote handling ignores true comments.
                )
            if form == "html_comment_literal":
                command += " # <!-- Literal shell note --!>"
            logging.debug("Prepared fixture continuation form %s", form)  # Record the completed transformation.
            return command  # Unsupported constructs remain outside positive fixtures.

        @classmethod
        def guides(  # Apply supported syntax to both modes of every independent guide.
            cls, fixture: GuidanceFixture, form: str
        ) -> None:  # Keep each independent procedure variant valid.
            shell = "bash" if form == "bash_continuation" else "powershell"  # Preserve the selected shell's grammar.
            for path in TestInputLedger.paths[:1]:  # Prove the guide accepts harmless normalization.
                text = fixture.Template.guide(path, fixture.contract, shell)  # Construct a real active procedure.
                fixture.files.write(path, text)  # Keep writes and action logging fixture-local.
                fixture.texts[path] = text  # Do not reread or silently normalize fixture content.
                controls = (fixture.contract.scoped, fixture.contract.full)  # Keep both modes independent.
                for label, options in zip(SectionCommands.LABELS[2:], controls, strict=True):  # Require both fences.
                    original = fixture.Template.analyzer(options)  # Name the complete original active command.
                    fixture.change(path, label, original, cls.command(options, form))  # Change only its syntax.

    @pytest.mark.parametrize(
        "form",
        (
            "order",
            "single_quotes",
            "double_quotes",
            "leading_dot",
            "equals",
            "identical_repeats",
            "bash_continuation",
            "powershell_continuation",
            "braced_base",
            "comments",
            "html_comment_literal",
        ),
        ids=lambda form: f"T16-equivalent-{form}",
    )
    def test_equivalent_controls(self, tmp_path: Path, form: str) -> None:  # Prove semantic normalization is real.
        fixture = GuidanceFixture(tmp_path)  # Build four real readable fixture inputs.
        self.Variants.guides(fixture, form)  # Preserve all controls while changing harmless spelling or order.
        guard = GuideGuard(tmp_path)  # Read inputs through the direct guard.
        assert guard.run() is True, guard.summary()  # Equivalent syntax must preserve a successful decision.
        assert guard.counts() == {  # Require actual four-input and one-guide accounting.
            "inputs_attempted": 4,
            "input_reads": 4,
            "input_validations": 4,
            "guide_reads": 1,
            "guide_checks": 1,
            "explicit_paths": 2,
            "automatic_paths": 2,
            "effective_paths": 4,
        }
        assert guard.ledger.errors == []  # A positive variant must not hide an unsupported check.

    @pytest.mark.parametrize("shell", ("bash", "sh", "powershell"), ids=lambda shell: f"T16-plain-{shell}")
    @pytest.mark.parametrize(
        "comment_case",
        (
            pytest.param((None, False, None), id="bare"),
            pytest.param(("-->", False, None), id="standard-note"),
            pytest.param(("-->", True, None), id="standard-procedure"),
            pytest.param(("--!>", False, "unsupported HTML comment terminator"), id="alternate-note"),
            pytest.param(("--!>", True, "unsupported HTML comment terminator"), id="alternate-procedure"),
            pytest.param(("", True, "required section count=0"), id="unclosed-procedure"),
        ),
    )
    def test_plain_cli(self, tmp_path: Path, shell: str, comment_case: tuple[str | None, bool, str | None]) -> None:
        """Accept a standard Markdown comment without promoting malformed HTML."""
        fixture = GuidanceFixture(tmp_path)  # Keep all command input mutations local.
        close, hidden_commands, reason = comment_case
        for path in TestInputLedger.paths[:1]:  # Require a complete independent procedure in the guide.
            text = fixture.Template.guide(path, fixture.contract, shell).replace(  # Remove only a prefix.
                "rtk proxy ", ""
            )  # Remove only a prefix.
            if close is not None:
                hidden = text.replace("test-quality-analyzer", "other-analyzer") if hidden_commands else "Fixture note"
                text = f"<!--\n{hidden}\n{close}\n{text}"
            fixture.files.write(path, text)  # Keep active base, preflight, and analyzer fences executable.
        guard = GuideGuard(tmp_path)  # Read the plain active procedure directly.
        assert guard.run() is (reason is None), guard.summary()
        assert guard.counts()["input_validations"] == (4 if reason is None else 3)
        assert guard.counts()["input_reads"] == 4 and guard.counts()["guide_checks"] == 1
        if reason is not None:
            assert len(guard.ledger.errors) == 1 and all(reason in error for error in guard.ledger.errors)

    def test_readable_empty_settings_and_baseline(  # Preserve readable empty input semantics.
        self, tmp_path: Path
    ) -> None:  # Preserve installed default semantics.
        fixture = GuidanceFixture(tmp_path)  # Create all four readable fixture inputs.
        fixture.files.write(".github/test-quality-config.toml", "\n")  # Keep readable empty settings valid.
        fixture.files.write(".github/test-quality-baseline.json", "[ ]\n")  # Keep a valid empty comparator list.
        guard = GuideGuard(tmp_path)  # Require actual reads before interpreting analyzer evidence.
        assert guard.run() is True, guard.summary()  # Do not confuse missing files with usable empty files.
        assert (  # Measure complete success.
            guard.counts()["input_reads"] == 4 and guard.counts()["input_validations"] == 4
        )  # Measure complete success.

    @pytest.mark.parametrize(
        "mutation",
        (
            (
                '--changed-from "origin/$BASE_REF" '
                "--full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt",
                '--full-gate-path requirements-dev.txt --changed-from "origin/${BASE_REF}" '
                "--full-gate-path .github/workflows/ci.yml",
            ),  # Harmless live scope order must not change guide semantics.
            ("--config .github/test-quality-config.toml", "--config='./.github/test-quality-config.toml'"),
            (
                "test-quality-analyzer --gate",
                "rtk proxy test-quality-analyzer --gate",
            ),  # Verify only proxy prefix forms.
            (
                "test-quality-analyzer --gate --config",
                "test-quality-analyzer --gate \\\n            --config",
            ),  # Decode Bash continuation in actual named CI.
        ),
        ids=("T16-live-order", "T16-live-quotes", "T16-live-proxy", "T16-live-continuation"),
    )
    def test_equivalent_live_ci(  # Harmless actual script syntax must preserve authority.
        self, tmp_path: Path, mutation: tuple[str, str]
    ) -> None:  # Preserve live authority meaning.
        fixture = GuidanceFixture(tmp_path)  # Keep independent guide controls unchanged.
        fixture.replace(".github/workflows/ci.yml", *mutation)  # Normalize only supported actual named script syntax.
        guard = GuideGuard(tmp_path)  # Read current fixture CI rather than cached controls.
        assert guard.run() is True, guard.summary()  # Accept equivalent live executable controls.
        assert guard.counts()["input_validations"] == 4  # Require all complete independent decisions.


class TestGuideMutations:  # Reject every controlled active-procedure change in each guide.
    """Reject each incorrect active control in each independent guide."""

    class Cases:  # Keep mutation targets independent of the guard's decoder.
        """Name mutations independently of the guard's option decoder."""

        scoped = (  # Each pair changes only the required scoped analyzer fence.
            ("--gate ", ""),  # Reject a report-only invocation.
            ("--gate", "--gate=false"),  # Reject an unsupported flag value.
            ("--config .github/test-quality-config.toml", ""),  # Reject missing required settings.
            (".github/test-quality-config.toml", ".github/wrong.toml"),  # Reject substituted settings.
            ("--baseline .github/test-quality-baseline.json", ""),  # Reject a missing comparator.
            (".github/test-quality-baseline.json", ".github/wrong.json"),  # Reject another comparator.
            ('--changed-from "origin/$BASE_REF"', ""),  # Reject an accidental full scan in the required fence.
            ('"origin/$BASE_REF"', '"origin/main"'),  # Reject a substituted base even if it can resolve.
            ('"origin/$BASE_REF"', "'origin/$BASE_REF'"),  # Reject literal single-quoted expansion.
            ('"origin/$BASE_REF"', '"origin/$OTHER_BASE"'),  # Reject an unrelated variable.
            ('"origin/$BASE_REF"', '"origin/\\$BASE_REF"'),  # Reject escaped expansion.
            ('"origin/$BASE_REF"', '"origin/$BASE_REF...HEAD"'),  # Reject different comparison meaning.
            ("--full-gate-path .github/workflows/ci.yml", ""),  # Reject the omitted workflow trigger.
            ("--full-gate-path requirements-dev.txt", ""),  # Reject the omitted requirements trigger.
            (".github/workflows/ci.yml", "wrong-workflow.yml"),  # Reject a similar but ineffective path.
            ("requirements-dev.txt", "wrong-requirements.txt"),  # Reject a similar but ineffective path.
            ("--gate", "--gate --full-gate-path requirements-dev.txt"),  # Reject duplicate explicit values.
            ("--config", "--config wrong.toml --config"),  # Reject an earlier conflicting singleton.
            ("--gate", "--gate --config wrong.toml"),  # Reject a later conflicting singleton.
            ("--baseline", "--baseline wrong.json --baseline"),  # Reject an earlier comparator conflict.
            ("--gate", "--gate --baseline wrong.json"),  # Reject a later comparator conflict.
            ("--changed-from", "--changed-from origin/wrong --changed-from"),  # Reject an earlier base conflict.
            ("--gate", "--gate --changed-from origin/wrong"),  # Reject a later base conflict.
            ("--gate", "--gate --roots tests"),  # Reject another scope source.
            ("--gate", "--gate --disable-rule weak_is_not_none"),  # Reject weakened findings.
            ("--gate", "--gate --include-mist-api"),  # Reject a changed exclusion policy.
            ("--gate", "--gate --write-baseline"),  # Reject comparator rewriting.
            ("--gate", "--gate --prune-baseline"),  # Reject comparator pruning.
            ("--gate", "--gate --unknown-control yes"),  # Reject unsupported controls explicitly.
            ("test-quality-analyzer", "python -m tools.test_quality_analyzer"),  # Reject the obsolete entry point.
            ("test-quality-analyzer", "other-analyzer"),  # Reject a different executable.
            ("rtk proxy", "rtk test"),  # Do not assume unverified RTK wrapper semantics.
            pytest.param(  # HTML text inside executable fences remains a literal command value.
                (
                    "--config .github/test-quality-config.toml",
                    "--config '<!--literal_marker-->.github/test-quality-config.toml'",
                ),
                id="T16-literal-marker",
            ),
            pytest.param(  # An unquoted midword hash is not a removable shell comment.
                (
                    "--config .github/test-quality-config.toml",
                    "--config .github/test-quality-config.toml#literal_hash",
                ),
                id="T16-literal-hash",
            ),
            pytest.param(  # Bash concatenation cannot stand in for unverified PowerShell escaping.
                (
                    "--config .github/test-quality-config.toml",
                    "--config '.github/test-''quality-config.toml'",
                ),
                id="T16-literal-quotes",
            ),
            pytest.param(  # A code-fence line must not disappear as a Markdown quote.
                ("rtk proxy test-quality-analyzer", "> dormant_line\nrtk proxy test-quality-analyzer"),
                id="T16-fenced-quote",
            ),
            ("--gate", "--gate | cat"),  # Reject a shell pipeline without executing it.
            ('"origin/$BASE_REF"', '"$(echo origin/main)"'),  # Reject command substitution without execution.
            ("rtk proxy test-quality-analyzer", "function dormant {\nrtk proxy test-quality-analyzer"),
        )  # A dormant function cannot supply the active procedure.
        full = (  # Each pair changes only the unscoped analyzer fence.
            ("--gate ", ""),  # Require a real full-suite gate.
            ("--config .github/test-quality-config.toml", ""),  # Require the same repository settings.
            (".github/test-quality-config.toml", "other.toml"),  # Reject substituted full-suite settings.
            ("--baseline .github/test-quality-baseline.json", ""),  # Require the same comparator.
            (".github/test-quality-baseline.json", "other.json"),  # Reject a different full-suite baseline.
            ("--gate", "--gate --changed-from origin/$BASE_REF"),  # Reject changed scope in full mode.
            ("--gate", "--gate --full-gate-path requirements-dev.txt"),  # Reject dormant scope controls.
            ("--gate", "--gate --roots tests"),  # Reject a narrowed full-suite command.
            ("--gate", "--gate --disable-rule weak_is_not_none"),  # Reject rule suppression.
            ("--gate", "--gate --write-baseline"),  # Reject baseline replacement.
            ("--config", "--config wrong.toml --config"),  # Reject earlier conflicts.
            ("--gate", "--gate --baseline wrong.json"),  # Reject later conflicts.
        )

        class Preparation:  # Reject mismatched base preparation and preflight substitutions.
            """Reject incorrect base relationships and direct preflight substitutions."""

            base = (  # Correct text elsewhere cannot replace matching active preparation.
                ('$BASE_REF = "main"', '$OTHER_BASE = "main"'),  # Require the intended variable.
                ('$BASE_REF = "main"', '$BASE_REF = ""'),  # Reject an empty intended branch.
                ("refs/remotes/origin/${BASE_REF}", "refs/remotes/origin/main"),  # Require matching destination.
                ("refs/heads/${BASE_REF}", "refs/heads/main"),  # Require matching source.
                ("origin/${BASE_REF}^{commit}", "origin/main^{commit}"),  # Require matching resolved reference.
                ("--verify", ""),  # Require commit verification.
                ('"origin/${BASE_REF}^{commit}"', "'origin/${BASE_REF}^{commit}'"),  # Preserve expansion.
                ("rtk proxy git fetch", "# rtk proxy git fetch"),  # Comments do not fetch the base.
            )
            preflight = (  # Require the actual direct measured guard class invocation.
                ("python", "other-python"),  # Reject another execution form.
                ("-B ", ""),  # Keep isolated no-bytecode execution.
                ("-m pytest", "-m unittest"),  # Require pytest collection.
                ("-p no:cacheprovider", "-p other-plugin"),  # Reject a changed invocation.
                ("-s ", ""),  # Keep measured output visible.
                ("-q ", ""),  # Require the documented direct command.
                ("::TestLiveGuides", "::UnusedExample"),  # Reject a dormant or unrelated test.
                ("rtk proxy", "rtk test"),  # Do not assume other wrapper semantics.
                ("rtk proxy python", "# rtk proxy python"),  # Correct comments cannot execute the guard.
            )
            profiles = (
                pytest.param(
                    (0, '$BASE_REF = "main"', "BASE_REF=main", "powershell"),
                    id="T16-powershell-bash-binding",
                ),
                pytest.param(
                    (0, '$BASE_REF = "main"', "$BASE_REF = main", "powershell"),
                    id="T16-powershell-command-value",
                ),
                pytest.param(
                    (0, '$BASE_REF = "main"', "$BASE_REF=main", "powershell"),
                    id="T16-powershell-unquoted-value",
                ),
                pytest.param(
                    (0, "BASE_REF=main", "BASE_REF = main", "bash"),
                    id="T16-bash-spaced-binding",
                ),
                pytest.param(
                    (0, "BASE_REF=main", '$BASE_REF = "main"', "bash"),
                    id="T16-bash-powershell-binding",
                ),
                pytest.param(
                    (0, "BASE_REF=main", "BASE_REF = main", "sh"),
                    id="T16-sh-spaced-binding",
                ),
                pytest.param(
                    (0, "BASE_REF=main", '$BASE_REF = "main"', "sh"),
                    id="T16-sh-powershell-binding",
                ),
            )

        class Inactive:  # Correct examples must not repair incorrect active commands.
            """Make structural and dormant-command mutations without executing text."""

            forms = (  # Cover all labels structurally and the scoped command behaviorally.
                "missing_label",
                "duplicate_label",
                "comment_label",
                "alternate_comment_label",
                "quoted_label",
                "fenced_label",
                "unsupported_language",
                "comment_command",
                "quoted_command",
                "echo_command",
                "empty_command",
                "wrong_with_comment",
                "wrong_with_example",
                "outside_section",
                "wrong_heading",
                "wrong_parent",
                "conditional_command",
            )

            @staticmethod
            def structure(  # Prove exact active label, heading, and fence boundaries.
                fixture: GuidanceFixture, path: str, label: str, form: str
            ) -> bool:
                """Mutate exact headings, visible labels, and executable fence profiles."""
                replacements = {  # Each entry changes one active structural property.
                    "missing_label": (label, "**Unused example:**"),  # Do not use a dormant label.
                    "duplicate_label": (label, label + "\n\n" + label),  # Reject ambiguous active labels.
                    "comment_label": (label, "<!-- " + label + " -->"),  # Ignore HTML comments.
                    "alternate_comment_label": (label, "<!-- " + label + " --!>"),
                    "quoted_label": (label, "> " + label),  # Ignore quoted procedures.
                    "fenced_label": (label, "```text\n" + label + "\n```"),  # Ignore fenced labels.
                    "outside_section": (label, "## Outside the required section\n" + label),  # Respect the boundary.
                    "wrong_heading": (SectionCommands.GUIDES[path][-1][1], "Unrelated section"),  # Require exact names.
                    "wrong_parent": (SectionCommands.GUIDES[path][0][1], "Unrelated parent"),  # Require the parent.
                }
                if form in replacements:  # These cases change only fixture Markdown structure.
                    fixture.replace(path, *replacements[form])  # Preserve unrelated independent inputs.
                    return True  # Do not make a second mutation for the same structural case.
                if form == "unsupported_language":  # A text fence cannot execute any required procedure part.
                    fixture.change(path, label, "powershell\n", "text\n")  # Change only the active fence profile.
                    return True  # Keep correct commands dormant within the unsupported profile.
                return False  # Remaining cases require active executable-text mutations.

            @staticmethod
            def execute(  # Keep dormant correct examples while the active check fails.
                fixture: GuidanceFixture, path: str, label: str, form: str
            ) -> None:
                """Keep valid dormant text while the required active command fails."""
                command = fixture.Template.analyzer(fixture.contract.scoped)  # Preserve a complete unused example.
                versions = {  # These strings remain input data and never execute.
                    "comment_command": "# " + command,  # A comment cannot supply an active command.
                    "quoted_command": "'" + command + "'",  # A quoted whole script is not an invocation.
                    "echo_command": "echo " + command,  # Printed command text does not execute it.
                    "empty_command": "",  # A fence without a command is incomplete.
                    "wrong_with_comment": "# " + command + "\nother-analyzer --gate",  # Ignore the correct comment.
                    "wrong_with_example": "other-analyzer --gate",  # Ignore the later correct dormant example.
                    "conditional_command": "if ($true) {\n" + command + "\n}",  # Reject unsupported controls.
                }
                fixture.change(path, label, command, versions[form])  # Change one active scoped command only.
                if form == "wrong_with_example":  # Correct unused examples cannot repair active drift.
                    fixture.replace(  # Leave a complete command outside the active labeled fence.
                        path,
                        "## End of fixture section",
                        f"```powershell\n{command}\n```\n\n## End of fixture section",
                    )

            @classmethod
            def apply(  # Make exactly one controlled active-procedure mutation.
                cls, fixture: GuidanceFixture, path: str, case: tuple[int, str]
            ) -> None:
                """Apply exactly one controlled mutation to its named active procedure part."""
                index, form = case  # Keep label choice and mutation form explicit.
                label = SectionCommands.LABELS[index]  # Mutate the correct active part.
                if not cls.structure(fixture, path, label, form):  # Do not interpret dormant shell constructs.
                    cls.execute(fixture, path, label, form)  # Supply actual incorrect active input text.

        @staticmethod
        def failure(guard: GuideGuard, path: str) -> None:  # Require a specific guide failure with complete progress.
            assert guard.run() is False, guard.summary()  # A mutation must return a failing guard decision.
            assert len(guard.ledger.errors) == 1 and path in guard.ledger.errors[0]  # Name this exact guide.
            assert guard.counts() == {  # Preserve the three independent valid inputs and all completed decisions.
                "inputs_attempted": 4,
                "input_reads": 4,
                "input_validations": 3,
                "guide_reads": 1,
                "guide_checks": 1,
                "explicit_paths": 2,
                "automatic_paths": 2,
                "effective_paths": 4,
            }

    @pytest.mark.parametrize("path", TestInputLedger.paths[:1])
    @pytest.mark.parametrize("mutation", Cases.scoped, ids=lambda mutation: f"T16-scoped-{mutation[0]}-{mutation[1]}")
    def test_scoped_control(  # Require a named failure for each scoped semantic mutation.
        self, tmp_path: Path, path: str, mutation: tuple[str, str]
    ) -> None:
        """Reject each scoped control mutation without accepting any exception."""
        fixture = GuidanceFixture(tmp_path)  # Give independent guides the valid live controls.
        fixture.change(path, SectionCommands.LABELS[2], *mutation)  # Change only one active scoped fence.
        guard = GuideGuard(tmp_path)  # Retain the direct measured decision.
        self.Cases.failure(guard, path)  # Require a named measured failure.
        assert guard.ledger.errors[0].startswith(path + ": validation_failed")  # Require this active guide failure.

    @pytest.mark.parametrize("path", TestInputLedger.paths[:1])
    @pytest.mark.parametrize("mutation", Cases.full, ids=lambda mutation: f"T16-full-{mutation[0]}-{mutation[1]}")
    def test_full_control(  # Reject controls that narrow or change the required full suite.
        self, tmp_path: Path, path: str, mutation: tuple[str, str]
    ) -> None:
        """Reject each full-suite control mutation with independent counts."""
        fixture = GuidanceFixture(tmp_path)  # Keep the scoped fence complete.
        fixture.change(path, SectionCommands.LABELS[3], *mutation)  # Change only the full-suite fence.
        guard = GuideGuard(tmp_path)  # Retain the direct measured decision.
        self.Cases.failure(guard, path)  # Require this guide to fail without hiding other progress.
        assert guard.ledger.errors[0].startswith(path + ": validation_failed")  # Require this full-suite guide failure.

    @pytest.mark.parametrize("path", TestInputLedger.paths[:1])
    @pytest.mark.parametrize(
        "case",
        tuple((0, *mutation, "powershell") for mutation in Cases.Preparation.base)
        + tuple((1, *mutation, "powershell") for mutation in Cases.Preparation.preflight)
        + Cases.Preparation.profiles,
        ids=lambda case: f"T16-preparation-{case[0]}-{case[2]}",
    )
    def test_base_control(  # Reject mismatched fetch, resolution, and preflight procedures.
        self, tmp_path: Path, path: str, case: tuple[int, str, str, str]
    ) -> None:
        """Reject a fetch or resolution that does not match the intended comparison."""
        fixture = GuidanceFixture(tmp_path)  # Keep analyzer text correct to isolate base preparation.
        index, old, new, shell = case
        if shell != "powershell":
            text = fixture.Template.guide(path, fixture.contract, shell)
            fixture.files.write(path, text)
            fixture.texts[path] = text
        fixture.change(path, SectionCommands.LABELS[index], old, new)  # Mutate only this active preparation fence.
        guard = GuideGuard(tmp_path)  # Retain the independent semantic decision.
        self.Cases.failure(guard, path)  # Require a semantic relationship failure.
        assert guard.ledger.errors[0].startswith(path + ": validation_failed")  # Require this preparation failure.

    @pytest.mark.parametrize("path", TestInputLedger.paths[:1])
    @pytest.mark.parametrize(
        "case",
        tuple((index, form) for form in Cases.Inactive.forms[:7] for index in range(4))
        + tuple((2, form) for form in Cases.Inactive.forms[7:]),
        ids=lambda case: f"T16-inactive-{case}",
    )
    def test_inactive_text(  # Correct inactive text must not pass an active procedure.
        self, tmp_path: Path, path: str, case: tuple[int, str]
    ) -> None:  # Reject dormant procedures.
        fixture = GuidanceFixture(tmp_path)  # Start with a complete procedure in each exact section.
        self.Cases.Inactive.apply(fixture, path, case)  # Correct dormant text must not repair the active procedure.
        guard = GuideGuard(tmp_path)  # Retain the completed active-procedure decision.
        self.Cases.failure(guard, path)  # Require a named failure, not an accepted exception.
        if case[1] == "alternate_comment_label":
            assert "unsupported HTML comment terminator" in guard.ledger.errors[0]
        assert guard.ledger.errors[0].startswith(  # Require this exact active guide failure.
            path + ": validation_failed"
        )  # Require this exact active input failure.


class TestRequiredInputs:  # Make missing or unusable capabilities fail with measured progress.
    """Prove partial accounting, live CI drift, and required-input safety."""

    class Drift:  # Compare outdated and repaired commands with a newly decoded control.
        """Compare outdated and repaired guides against one new live control."""

        @staticmethod
        def outdated(fixture: GuidanceFixture) -> GuideGuard:  # Retain all independent failing decisions.
            fixture.replace(  # Add a third trigger only to the fixture's actual named CI script.
                ".github/workflows/ci.yml",
                "--full-gate-path requirements-dev.txt)",
                "--full-gate-path requirements-dev.txt --full-gate-path scripts/additional-trigger.txt)",
            )
            guard = GuideGuard(fixture.root)  # Read the new live authority rather than cached controls.
            assert guard.run() is False  # Every old guide command must now fail.
            assert guard.counts() == {  # Require measured reads, decisions, and newly decoded controls.
                "inputs_attempted": 4,
                "input_reads": 4,
                "input_validations": 3,
                "guide_reads": 1,
                "guide_checks": 1,
                "explicit_paths": 3,
                "automatic_paths": 2,
                "effective_paths": 5,
            }
            return guard  # Keep the actual named failures available to the independent test.

        @staticmethod
        def repaired(fixture: GuidanceFixture) -> GuideGuard:  # Repair every active scoped fixture fence.
            for path in TestInputLedger.paths[:1]:  # Repair the active scoped fence of the guide.
                fixture.change(  # Keep all production documents and workflows unchanged.
                    path,
                    SectionCommands.LABELS[2],
                    "--full-gate-path requirements-dev.txt",
                    "--full-gate-path requirements-dev.txt --full-gate-path scripts/additional-trigger.txt",
                )
            guard = GuideGuard(fixture.root)  # Reread all four inputs for the repaired invocation.
            assert guard.run() is True, guard.summary()  # Accept only the complete updated live contract.
            assert guard.counts()["input_validations"] == 4  # Require all complete successful validations.
            assert guard.counts()["explicit_paths"] == 3 and guard.counts()["effective_paths"] == 5  # Measure drift.
            return guard  # Retain the complete observed progress for the direct test.

    @pytest.mark.parametrize("path", TestInputLedger.paths)
    @pytest.mark.parametrize("form", ("missing", "directory", "invalid_utf8"), ids=lambda form: f"T15-{form}")
    def test_read_failure(self, tmp_path: Path, path: str, form: str) -> None:  # Prove four independent read attempts.
        fixture = GuidanceFixture(tmp_path)  # Keep every other input usable and independent.
        fixture.files.remove(path)  # Remove only the selected temporary input.
        logging.info("Preparing required-input failure %s for %s", form, path)  # Announce portable failure evidence.
        if form == "directory":  # A directory is genuinely unreadable as a required file.
            (tmp_path / path).mkdir()  # Avoid permission-sensitive tests and root-dependent skips.
        elif form == "invalid_utf8":  # Make the required complete UTF-8 read fail.
            (tmp_path / path).write_bytes(b"\xff")  # Supply an actual invalid input.
        logging.debug("Prepared required-input failure %s for %s", form, path)  # Confirm the fixture state.
        guard = GuideGuard(tmp_path)  # Read all four inputs even after this failure.
        assert guard.run() is False  # A missing capability must not become a successful empty scope.
        assert len(guard.ledger.errors) == 1 and path in guard.ledger.errors[0]  # Name the failed input.
        ci_failed = path == ".github/workflows/ci.yml"  # State the independent expected dependency boundary.
        guides = 0 if path in TestInputLedger.paths[:1] else 1  # Count available guide reads explicitly.
        assert guard.counts() == {  # Retain independent reads and validations when CI is unavailable.
            "inputs_attempted": 4,
            "input_reads": 3,
            "input_validations": 2 if ci_failed else 3,
            "guide_reads": guides,
            "guide_checks": 0 if ci_failed else guides,
            "explicit_paths": 0 if ci_failed else 2,
            "automatic_paths": 0 if ci_failed else 2,
            "effective_paths": 0 if ci_failed else 4,
        }

    @pytest.mark.parametrize(
        ("path", "text"),
        (
            (TestInputLedger.paths[0], ""),
            (TestInputLedger.paths[1], "jobs: [\n"),
            (TestInputLedger.paths[2], "[rules\n"),
            (TestInputLedger.paths[2], "[rules]\nunknown_rule = true\n"),  # Reject actual installed semantic errors.
            (TestInputLedger.paths[2], "[rules]\nweak_assert_not_none = 1\n"),  # Require boolean switch values.
            (TestInputLedger.paths[2], "rules = 1\n"),  # Reject unusable table shapes before installed parsing.
            (
                TestInputLedger.paths[2],
                '[severity]\nweak_assert_not_none = "invalid"\n',
            ),  # Preserve installed taxonomy.
            (TestInputLedger.paths[3], "{"),
            (TestInputLedger.paths[3], "{}"),
            (TestInputLedger.paths[3], "[{}]"),
        ),
        ids=lambda value: f"T15-invalid-{value}",
    )
    def test_invalid_text(self, tmp_path: Path, path: str, text: str) -> None:  # Separate reads from usability.
        fixture = GuidanceFixture(tmp_path)  # Keep independent valid input text.
        fixture.files.write(path, text)  # Supply malformed or incomplete required content.
        guard = GuideGuard(tmp_path)  # Parse available independent inputs.
        assert guard.run() is False  # Readability alone must not satisfy the procedure.
        assert len(guard.ledger.errors) == 1 and path in guard.ledger.errors[0]  # Identify this unusable input.
        ci_failed = path == ".github/workflows/ci.yml"  # Invalid CI blocks guide comparisons only.
        assert guard.counts() == {  # Preserve all four completed reads even for malformed text.
            "inputs_attempted": 4,
            "input_reads": 4,
            "input_validations": 2 if ci_failed else 3,
            "guide_reads": 1,
            "guide_checks": 0 if ci_failed else 1,
            "explicit_paths": 0 if ci_failed else 2,
            "automatic_paths": 0 if ci_failed else 2,
            "effective_paths": 0 if ci_failed else 4,
        }

    def test_live_ci_drift(self, tmp_path: Path) -> None:  # Prove live controls are not a cached two-path list.
        fixture = GuidanceFixture(tmp_path)  # Use the current named CI script as fixture authority.
        outdated = self.Drift.outdated(fixture)  # Require the old commands to fail against changed live authority.
        failed_paths = {error.split(": ", 1)[0] for error in outdated.ledger.errors}  # Keep every named failed guide.
        assert failed_paths == set(TestInputLedger.paths[:1])  # Require the one outdated guide decision.
        repaired = self.Drift.repaired(fixture)  # Verify complete fixture command repair against the third control.
        assert repaired.ledger.errors == []  # Complete updated commands must not hide an unsupported decision.

    @pytest.mark.parametrize(
        "mutation",
        (
            ("test_quality_gate:", "other_job:"),  # Do not read a different job's correct-looking command.
            ("name: Run test quality ratchet", "name: Unused ratchet example"),  # Require the exact live step.
            (
                "      - name: Run test quality ratchet\n",
                "      - name: Run test quality ratchet\n"
                "        run: echo duplicate\n"
                "      - name: Run test quality ratchet\n",
            ),  # Duplicate named steps must fail.
            (
                "EVENT_NAME: ${{ github.event_name }}",
                "EVENT_NAME: ${{ github.ref }}",
            ),  # Reject incorrect event binding.
            ("BASE_REF: ${{ github.base_ref }}", "BASE_REF: ${{ github.head_ref }}"),  # Reject incorrect intended base.
            (
                'if [ "$EVENT_NAME" = "pull_request" ]; then',
                'if [ "$EVENT_NAME" = "push" ]; then',
            ),  # Keep PR-only scope.
            (
                'if [ "$EVENT_NAME" = "pull_request" ]; then',
                "if [ '$EVENT_NAME' = 'pull_request' ]; then",
            ),  # Keep expansion.
            (
                "          scope=()",
                "          scope=()\n          echo unsupported",
            ),  # Reject unknown executable grammar.
            ('"${scope[@]}"', ""),  # Require actual scope-array insertion.
            ('"${scope[@]}"', '"${scope[@]}" "${scope[@]}"'),  # Reject duplicate expansion.
            ('"${scope[@]}"', "'${scope[@]}'"),  # Reject literal array insertion.
            ("--config .github/test-quality-config.toml", "--config other.toml"),  # Require repository settings.
            ("--baseline .github/test-quality-baseline.json", "--baseline other.json"),  # Require repository baseline.
            ("--gate --config", "--config"),  # Require gate mode in live authority.
            ('"origin/$BASE_REF"', '"origin/main"'),  # Reject an incorrect live comparison.
            (
                "--full-gate-path requirements-dev.txt)",
                "--full-gate-path requirements-dev.txt --full-gate-path requirements-dev.txt)",
            ),
            (
                "          fi",
                "          else\n            scope=()\n          fi",
            ),  # Reject unsupported event branches.
        ),
        ids=lambda mutation: f"T16-ci-{mutation[0]}-{mutation[1]}",
    )
    def test_ci_decode_failure(self, tmp_path: Path, mutation: tuple[str, str]) -> None:  # Fail closed on CI drift.
        fixture = GuidanceFixture(tmp_path)  # Keep all required input reads available.
        fixture.replace(".github/workflows/ci.yml", *mutation)  # Mutate only the fixture's named live contract.
        guard = GuideGuard(tmp_path)  # Do not execute the workflow script.
        assert guard.run() is False  # Unsupported CI must not invent a successful guide comparison.
        assert (  # Name the source.
            len(guard.ledger.errors) == 1 and ".github/workflows/ci.yml" in guard.ledger.errors[0]
        )  # Name the source.
        assert guard.counts() == {  # Independent settings and baseline validations remain visible.
            "inputs_attempted": 4,
            "input_reads": 4,
            "input_validations": 2,
            "guide_reads": 1,
            "guide_checks": 0,
            "explicit_paths": 0,
            "automatic_paths": 0,
            "effective_paths": 0,
        }


class TestLiveGuides:  # Check the actual worktree without executing any documented command.
    """Check the actual worktree without executing document or CI commands."""

    def test_required_local_procedures(self) -> None:  # Provide the direct measured preflight required by every guide.
        root = Path(__file__).resolve().parents[3]  # Read only this worktree, never another checkout.
        guard = GuideGuard(root)  # Bind all four independent reads to the current worktree.
        passed = guard.run()  # Print real completed reads, validations, decisions, and live controls.
        assert passed is True, guard.summary()  # Current omissions must fail before the guide edits.
        assert guard.counts() == {  # Require exact current successful measurements.
            "inputs_attempted": 4,
            "input_reads": 4,
            "input_validations": 4,
            "guide_reads": 1,
            "guide_checks": 1,
            "explicit_paths": 2,
            "automatic_paths": 2,
            "effective_paths": 4,
        }
