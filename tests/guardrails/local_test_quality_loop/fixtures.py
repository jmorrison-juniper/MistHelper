"""Collect unchanged analyzer evidence in isolated offline repositories."""

from __future__ import annotations  # Keep nested evidence records safe to reference.

import json  # Read real analyzer reports and write fixture-local baselines.
import logging  # Record each fixture mutation and analyzer observation.
import os  # Copy the environment without changing process or global state.
import re  # Measure installed stdout and detector logging.
import shlex  # Quote static fixture paths without disabling base expansion.
import subprocess  # Run real Git and analyzer processes without a shell.
import sys  # Use the active isolated interpreter for analyzer execution.
from dataclasses import dataclass, field  # Keep related evidence in typed records.
from pathlib import Path  # Confine fixture inputs and reports to temporary roots.
from typing import cast  # Narrow validated JSON structures without type suppression.

from tests.support.git_environment import git_subprocess_environment  # Reuse the configuration-protocol repair.

from .guard import CiGateContract, SectionCommands  # Use the live contract rather than cached trigger constants.


class FixtureEnvironment:  # Prevent fixture processes from using production state.
    """Remove inherited Git overrides and credentials from fixture processes."""

    @staticmethod
    def create(source: dict[str, str] | None = None) -> dict[str, str]:  # Keep the caller's environment unchanged.
        logging.info("Preparing an isolated offline subprocess environment")  # Announce the safety boundary.
        inherited = git_subprocess_environment(source)  # Repair incomplete editor configuration first.
        secret_markers = ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "APITOKEN")  # Remove API credentials by name.
        python_overrides = {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"}  # Prevent external module shadowing.
        environment = {  # Remove the whole Git override protocol, including worktree and index locations.
            name: value  # Copy values rather than mutating the source mapping.
            for name, value in inherited.items()  # Inspect every inherited variable.
            if not name.upper().startswith("GIT_")  # Keep repository selection and configuration fixture-local.
            and name.upper() not in python_overrides  # Keep imports bound to the active interpreter.
            and not any(marker in name.upper() for marker in secret_markers)  # Do not pass credentials.
        }
        environment.update(  # Disable global configuration, prompts, and network protocols for fixture Git.
            GIT_CONFIG_NOSYSTEM="1",  # Do not read system Git settings.
            GIT_CONFIG_GLOBAL=os.devnull,  # Do not read or write the real global Git configuration.
            GIT_ATTR_NOSYSTEM="1",  # Do not import system attribute behavior.
            GIT_TERMINAL_PROMPT="0",  # Do not permit a credential prompt.
            GIT_ALLOW_PROTOCOL="file",  # Fixture commands must not use network transports.
            PYTHONNOUSERSITE="1",  # Do not load user-installed analyzer replacements.
            PYTHONDONTWRITEBYTECODE="1",  # Do not write bytecode into the installed package.
        )
        logging.debug("Prepared %s subprocess variables without inherited Git overrides", len(environment))  # Measure.
        return environment  # Supply an explicit environment for every subprocess.


class FixtureRepository:  # Keep all file, identity, and reference changes disposable.
    """Own local files, commits, references, and deterministic rename behavior."""

    class Files:  # Give each mutation one explicit temporary root.
        """Confine each controlled file mutation to one fixture root."""

        class Sources:  # Keep known assertions and comparator identities stable.
            """Keep assertion lines stable for independent finding identities."""

            boundaries = (  # Exercise real applicable detectors without adding findings or network work.
                "\nfrom fixture_subject import parse_payload  # Import only the local offline subject.\n"
                "import json  # Name the exact malformed-input exception.\n"
                "import pytest  # Require the subject to reject malformed JSON.\n"
                "\ndef test_input_boundaries() -> None:  # Provide genuine numeric and JSON coverage.\n"
                '    assert parse_payload(data="", limit=0) == []  # Cover empty input and zero limits.\n'
                '    assert parse_payload(data="[]", limit=-1) == []  # Cover negative limits.\n'
                "    with pytest.raises(json.JSONDecodeError):  # Require a specific parsing failure.\n"
                '        parse_payload(data="{", limit=1)  # Exercise malformed JSON without a network.\n'
            )
            subject = (  # Give applicability inference a real local signature and parsing body.
                "import json  # Parse fixture input without a remote service.\n"
                "import logging  # Keep fixture parsing observable if a developer executes it.\n"
                "\ndef parse_payload(data: str, limit: int) -> object:  # Define real JSON and numeric input domains.\n"
                '    logging.info("Parsing fixture input with limit %s", limit)  # Announce the local transform.\n'
                "    if not data:  # Keep empty input behavior explicit.\n"
                '        logging.debug("Parsed fixture input as an empty list")  # Record the empty result.\n'
                "        return []  # Define the independently asserted empty-input result.\n"
                "    result = json.loads(data)  # Perform real local parsing for applicability evidence.\n"
                '    logging.debug("Parsed fixture input type %s", type(result).__name__)  # Record the result.\n'
                "    return result  # Preserve the decoded value for exact assertions.\n"
            )
            strong = (  # Supply an exact-value control without product imports.
                "def test_observation() -> None:  # Keep this control independent of product code.\n"
                "    result = [1, 2]  # Use a stable local value without external actions.\n"
                "    assert result == [1, 2]  # Check the exact value for the strong control.\n"
            ) + boundaries  # Give full scans genuine applicable detector scope.
            weak = (  # Supply the intentional weak assertion that proves actual selection.
                "def test_observation() -> None:  # Keep this witness independent of product code.\n"
                "    result = [1, 2]  # Use a stable local value without external actions.\n"
                "    assert result is not None  # Create the known weak_is_not_none witness.\n"
            ) + boundaries  # Keep the weak assertion at the independent expected line.

            @staticmethod
            def baseline(path: str) -> str:  # Accept only the explicit fixture witness when requested.
                logging.info("Preparing an accepted fixture identity for %s", path)  # Announce baseline construction.
                entry = {  # Define the known identity independently of analyzer output.
                    "category": "weak_assertion",  # Match the installed detector category.
                    "rule_id": "weak_is_not_none",  # Do not confuse this identity with the settings switch.
                    "file_path": path,  # Accept only the named fixture witness.
                    "line_number": 3,  # Keep the assertion line stable.
                    "severity": "medium",  # Use the installed weak-assertion taxonomy.
                    "explanation": "assert x is not None only verifies non-None state.",  # Preserve identity text.
                    "remediation": "Assert on the actual value / type / structure you expect.",  # Keep usable records.
                    "heuristic": False,  # This witness uses a deterministic detector.
                }
                text = json.dumps([entry], ensure_ascii=True) + "\n"  # Serialize only the fixture-local comparator.
                logging.debug("Prepared one fixture identity with %s characters", len(text))  # Measure construction.
                return text  # Never rewrite the production baseline.

        def __init__(self, root: Path) -> None:  # Bind all later writes to this fixture.
            self.root = root  # Never infer the production working directory.

        def write(self, path: str, text: str) -> None:  # Create only caller-declared fixture inputs.
            logging.info("Writing fixture input %s", path)  # Name the mutation before it starts.
            destination = self.root / path  # Keep paths inside the temporary repository.
            destination.parent.mkdir(parents=True, exist_ok=True)  # Prepare only local fixture directories.
            destination.write_text(text, encoding="utf-8", newline="\n")  # Keep committed content portable.
            logging.debug("Wrote fixture input %s with %s characters", path, len(text))  # Measure the completed write.

        def remove(self, path: str) -> None:  # Remove only a controlled fixture file.
            logging.info("Removing fixture input %s", path)  # Name the deletion before it starts.
            (self.root / path).unlink()  # Do not change production files or permissions.
            logging.debug("Removed fixture input %s", path)  # Confirm the completed deletion.

        def rename(self, source: str, destination: str) -> None:  # Preserve source bytes for exact rename cases.
            logging.info("Renaming fixture input %s to %s", source, destination)  # Announce local rename evidence.
            target = self.root / destination  # Keep the destination inside the temporary repository.
            target.parent.mkdir(parents=True, exist_ok=True)  # Prepare the local destination directory.
            (self.root / source).rename(target)  # Use a genuine rename without touching real Git state.
            logging.debug("Renamed fixture input %s to %s", source, destination)  # Confirm the mutation.

    def __init__(self, root: Path) -> None:  # Create a repository only under the supplied temporary root.
        self.root = root  # Keep every subprocess bound to the fixture directory.
        logging.info("Preparing temporary repository directory")  # Announce the fixture-only directory write.
        root.mkdir(parents=True, exist_ok=True)  # Permit nested fixture roots without touching a real checkout.
        logging.debug("Prepared temporary repository directory")  # Confirm the local directory boundary.
        self.environment = FixtureEnvironment.create()  # Remove real worktree and credential overrides.
        self.files = self.Files(root)  # Give fixture writes the same explicit root.
        self.git("init", "--quiet", "--initial-branch=fixture")  # Initialize only this offline repository.
        settings = {  # Make identity, hooks, line endings, and rename behavior fixture-local.
            "user.name": "Offline fixture",  # Do not use the real author identity.
            "user.email": "fixture@example.invalid",  # Do not use a production address.
            "commit.gpgsign": "false",  # Do not access signing keys.
            "core.hooksPath": str(root / ".fixture-hooks"),  # Do not run real or installed hooks.
            "core.autocrlf": "false",  # Keep source line numbers stable across platforms.
            "core.fsmonitor": "false",  # Do not inherit an editor filesystem monitor.
            "diff.renames": "true",  # Keep exact rename detection deterministic.
        }
        for name, value in settings.items():  # Apply each setting only to this repository.
            self.git("config", "--local", name, value)  # Never change production or global Git settings.
        self.files.write(".git/info/exclude", ".fixture-reports/\n")  # Keep observation output out of later commits.

    def git(self, *arguments: str, check: bool = True) -> str:  # Use explicit local arguments without shell evaluation.
        logging.info("Running fixture Git action %s", arguments[0])  # Identify the action without unrelated data.
        completed = subprocess.run(  # Execute real Git against the isolated repository.
            ["git", "--no-pager", *arguments],  # Preserve boundaries and disable every possible pager.
            cwd=self.root,  # Never let Git discover the production worktree.
            env=self.environment,  # Remove inherited repository and index locations.
            capture_output=True,  # Retain failures without global terminal side effects.
            encoding="utf-8",  # Decode output consistently on Windows and macOS.
            timeout=30,  # Bound local Git work independently of analyzer time.
            check=False,  # Log the measured exit before deciding whether it is expected.
        )
        logging.debug("Fixture Git action %s exited %s", arguments[0], completed.returncode)  # Record real status.
        if check and completed.returncode != 0:  # Only explicit optional reference lookups may fail.
            raise subprocess.CalledProcessError(  # Fail fixture setup rather than inventing a successful history.
                completed.returncode, completed.args, completed.stdout, completed.stderr
            )
        return completed.stdout.strip()  # Keep revisions and path lists directly inspectable.

    def commit(self, label: str = "candidate") -> str:  # Record only fixture-local candidate revisions.
        self.git("add", "--all", ".")  # Include controlled file states, excluding observation reports.
        self.git("commit", "--quiet", "--message", label)  # Never invoke a production commit hook.
        return self.git("rev-parse", "HEAD")  # Return the actual local revision for evidence.

    def seed(self, paths: tuple[str, ...]) -> str:  # Commit valid inputs before the comparison base.
        self.files.write(".github/test-quality-config.toml", "")  # Preserve all installed default rules.
        self.files.write(".github/test-quality-baseline.json", "[]\n")  # Accept no finding in ordinary cases.
        self.files.write(  # Provide tested local parsing applicability.
            "fixture_subject.py", self.Files.Sources.subject
        )  # Provide tested local parsing applicability.
        self.files.write("tests/test_changed.py", self.Files.Sources.strong)  # Control the candidate path.
        self.files.write("tests/test_witness.py", self.Files.Sources.weak)  # Prove unchanged full-suite inclusion.
        for path in paths:  # Supply every additional live trigger without caching its values.
            self.files.write(path, "fixture tooling\n")  # Trigger content is not executed by the analyzer.
        return self.commit("base")  # Establish the independent committed baseline history.


class ScopeObservation:  # Separate raw process evidence from measured results.
    """Keep actual process, count, path, and finding evidence for one run."""

    @dataclass(frozen=True)
    class Process:  # Preserve exact subprocess output and revision context.
        """Retain exact invocation and revision context without fabricated output."""

        exit_code: int  # Record the real analyzer exit.
        stdout: str  # Preserve the real scope and gate lines.
        stderr: str  # Preserve selection reasons and completed detector traces.
        arguments: tuple[str, ...]  # Record exact argument boundaries.
        revisions: tuple[str | None, str | None, str]  # Keep requested base, resolved base, and actual HEAD.

    @dataclass
    class Evidence:  # Keep unavailable measurements distinct from zero.
        """Represent unavailable measurements explicitly."""

        counts: dict[str, int | None] = field(default_factory=dict)  # Never replace absent counts with zero.
        analyzed: frozenset[str] | None = None  # Use report paths or completed detector traces only.
        findings: frozenset[tuple[str, str, str, int]] | None = None  # Preserve actual finding identities.
        reports: tuple[bool, bool] = (False, False)  # Record JSON and summary existence independently.
        unavailable: tuple[str, ...] = ()  # Explain measurements that an early return cannot provide.

    class Decoder:  # Measure installed output without replacing selection logic.
        """Read installed output without reproducing analyzer selection."""

        @staticmethod
        def counts(process: ScopeObservation.Process) -> dict[str, int | None]:  # Measure emitted counts only.
            logging.info("Measuring analyzer stdout and diagnostic counts")  # Announce output parsing.
            patterns = {  # Use the installed output shapes rather than invented scope fields.
                "scope_files": r"^gate_scope: (\d+) files checked, \d+ findings checked$",  # Discovered gate count.
                "scope_findings": r"^gate_scope: \d+ files checked, (\d+) findings checked$",  # Filtered findings.
                "discovered": r"Discovery found (\d+) test files",  # Completed discovery measurement.
                "parsed": r"Parsed (\d+) file\(s\);",  # Completed parsing measurement.
                "new_findings": r"^gate: (\d+) new findings vs baseline$",  # Separate baseline comparison.
            }
            output = process.stdout + "\n" + process.stderr  # Preserve both genuine output channels.
            counts: dict[str, int | None] = {}  # Keep every absent measurement explicit.
            for name, pattern in patterns.items():  # Measure each independent emitted field.
                matches = re.findall(pattern, output, re.MULTILINE)  # Do not infer counts from paths.
                assert len(matches) <= 1, f"Repeated analyzer measurement: {name}"  # Reject ambiguous evidence.
                counts[name] = int(matches[0]) if matches else None  # An early error is not zero coverage.
            logging.debug("Measured analyzer counts %s", counts)  # Report actual available measurements.
            return counts  # Keep discovery, parsing, scope, and new findings distinct.

        @staticmethod
        def report(  # Require real analyzed paths and finding identities.
            path: Path,
        ) -> tuple[frozenset[str] | None, frozenset[tuple[str, str, str, int]] | None]:
            """Read exact paths and identities from a newly created report."""
            if not path.is_file():  # Valid empty scopes and early errors can omit this report.
                return None, None  # Do not claim an empty analyzed set from absent evidence.
            logging.info("Reading actual analyzer report %s", path.name)  # Announce the evidence read.
            payload: object = json.loads(path.read_text(encoding="utf-8"))  # Decode only this invocation's report.
            assert isinstance(payload, dict), "The analyzer report is not an object"  # Require the real shape.
            report = cast(dict[str, object], payload)  # Narrow validated JSON without suppression.
            paths = report["analyzed_files"]  # Read the installed report's actual analyzed set.
            entries = report["findings"]  # Read findings after installed rule filtering.
            assert isinstance(paths, list) and all(isinstance(path, str) for path in paths)  # Require real paths.
            assert isinstance(entries, list) and all(isinstance(entry, dict) for entry in entries)  # Require records.
            findings = cast(list[dict[str, object]], entries)  # Narrow the validated finding objects.
            identities = frozenset(  # Preserve category, emitted rule, path, and assertion line.
                (str(entry["category"]), str(entry["rule_id"]), str(entry["file_path"]), int(str(entry["line_number"])))
                for entry in findings  # Do not synthesize identities from fixture expectations.
            )
            analyzed = frozenset(cast(list[str], paths))  # Retain exact report paths independently of counts.
            logging.debug("Read %s analyzed paths and %s identities", len(analyzed), len(identities))  # Measure.
            return analyzed, identities  # Return actual report evidence only.

        @classmethod
        def decode(  # Preserve completed detector evidence after reporting errors.
            cls, process: ScopeObservation.Process, outputs: tuple[Path, Path]
        ) -> ScopeObservation.Evidence:
            """Preserve detector evidence when baseline errors prevent reports."""
            counts = cls.counts(process)  # Measure only completed installed output.
            analyzed, findings = cls.report(outputs[0])  # Read only this invocation's unique report.
            logging.info("Measuring completed weak-detector traces")  # Announce fallback evidence inspection.
            matches = re.findall(r"Weak-assertion finding count for ([^\n]+): \d+", process.stderr)  # Completed traces.
            traces = frozenset(matches) if matches else None  # Do not invent paths when no detector completed.
            if analyzed is None:  # An input error can stop reporting after the full scan.
                analyzed = traces  # Retain genuine completed detector paths when available.
            elif traces is not None:  # Successful scans must agree across independent evidence channels.
                assert analyzed == traces, "Report paths differ from completed detector paths"  # Reject false proof.
            reports = (outputs[0].is_file(), outputs[1].is_file())  # Measure both output files separately.
            missing = tuple(name for name, value in counts.items() if value is None)  # Name unavailable counts.
            if analyzed is None:  # No completed detector or report provides analyzed path evidence.
                missing += ("analyzed_paths",)  # State unavailable path evidence instead of inventing an empty set.
            if findings is None:  # A missing report cannot provide actual finding identities.
                missing += ("finding_identities",)  # State unavailable identity evidence explicitly.
            logging.debug("Measured %s completed detector paths and reports=%s", len(matches), reports)  # Measure.
            return ScopeObservation.Evidence(counts, analyzed, findings, reports, missing)  # Preserve unavailable data.

    def __init__(self, case: str, process: Process, outputs: tuple[Path, Path]) -> None:  # Bind one real observation.
        self.case = case  # Preserve the matrix group and variant name.
        self.process = process  # Keep unchanged raw subprocess evidence.
        self.outputs = outputs  # Prevent stale report reuse across observations.
        self.evidence = self.Decoder.decode(process, outputs)  # Measure installed behavior without replacement logic.

    def summary(self) -> str:  # Report available and unavailable measurements clearly.
        counts = self.evidence.counts  # Use only this invocation's measured values.
        analyzed = None if self.evidence.analyzed is None else len(self.evidence.analyzed)  # Preserve absence.
        return (  # Keep the report ASCII and tied to a named matrix case.
            f"scope_observation: case={self.case} exit={self.process.exit_code} counts={counts} "
            f"analyzed={analyzed} reports={self.evidence.reports} unavailable={self.evidence.unavailable}"
        )


class AnalyzerFixture:  # Use unchanged installed processes for every scope observation.
    """Run the active interpreter against fixture-local analyzer inputs."""

    class Expectation:  # Keep expected evidence independent of analyzer selection.
        """Supply independent expected sets, counts, identities, and exits."""

        @dataclass(frozen=True)
        class Record:  # Group independent expected counts, paths, and results.
            """Group expected fields without a long method signature."""

            exit_code: int  # State the expected success or failure explicitly.
            counts: tuple[  # Keep five measurements distinct.
                int | None, int | None, int | None, int | None, int | None
            ]  # Keep five measurements distinct.
            analyzed: frozenset[str] | None  # Name expected paths without resolver output.
            findings: frozenset[tuple[str, str, str, int]] | None  # Require actual finding identities.
            reports: tuple[bool, bool]  # Distinguish a genuine empty return from stale output.

        @staticmethod
        def scan(  # State expected behavior without copying a resolver.
            exit_code: int,  # Require the expected gate result.
            paths: frozenset[str],  # Name included paths independently.
            weak_paths: frozenset[str],  # Name each expected weak witness independently.
            counts: tuple[int, int, int, int, int],  # State scope files, findings, discovery, parsing, and new counts.
        ) -> AnalyzerFixture.Expectation.Record:
            """Define a scan expectation without copying analyzer selection."""
            identities = frozenset(  # Use the fixed intentional assertion line and emitted identity.
                ("weak_assertion", "weak_is_not_none", path, 3) for path in weak_paths  # Keep expectations independent.
            )
            return AnalyzerFixture.Expectation.Record(  # Require reports.
                exit_code, counts, paths, identities, (True, True)
            )  # Require reports.

        @staticmethod
        def empty() -> AnalyzerFixture.Expectation.Record:  # Describe the installed early return explicitly.
            return AnalyzerFixture.Expectation.Record(  # Parsing and discovery did not run on this path.
                0, (0, 0, None, None, 0), None, None, (False, False)
            )

        @staticmethod
        def error(  # Do not replace absent error measurements with zero.
            counts: tuple[int | None, int | None, int | None, int | None, int | None] = (None, None, None, None, None),
            paths: frozenset[str] | None = None,  # Retain completed detector paths when the case expects them.
            reports: tuple[bool, bool] = (False, False),  # Most early errors cannot write reports.
        ) -> AnalyzerFixture.Expectation.Record:
            """Require exit 2 without inventing absent measurements."""
            return AnalyzerFixture.Expectation.Record(  # Findings need a genuine report.
                2, counts, paths, None, reports
            )  # Findings need a genuine report.

    class Run:  # Give each bounded subprocess its own argument and report record.
        """Prepare one exact invocation and collect its real bounded subprocess result."""

        @dataclass(frozen=True)
        class Parameters:  # Preserve explicit modes and negative-case controls.
            """Keep the observation request inside the five-parameter limit."""

            case: str  # Name the required matrix group and variant.
            revision: str | None  # None selects actual unscoped full-suite mode.
            options: tuple[str, ...]  # Retain explicit negative-case controls.
            triggers: tuple[str, ...]  # Use live controls unless a negative case changes them.

        def __init__(self, fixture: AnalyzerFixture, parameters: Parameters) -> None:  # Allocate unique local outputs.
            logging.info("Allocating analyzer observation outputs for %s", parameters.case)  # Announce preparation.
            self.repository = fixture.repository  # Retain this fixture's explicit local environment and root.
            self.parameters = parameters  # Preserve exact observation request semantics.
            directory = self.repository.root / ".fixture-reports"  # Keep reports outside test roots and commits.
            stem = f"run-{fixture.observation_count}"  # Do not reuse a previous invocation's output.
            self.outputs = (directory / f"{stem}.json", directory / f"{stem}.md")  # Allocate both actual report paths.
            logging.debug("Allocated two output paths for %s", parameters.case)  # Measure allocated destinations.

        def arguments(self) -> tuple[str, ...]:  # Preserve genuine CLI selection while adding diagnostics.
            logging.info("Preparing analyzer arguments for %s", self.parameters.case)  # Announce transformation.
            module = "misthelper_devtools.test_quality_analyzer"  # Use the unchanged installed module.
            arguments = [sys.executable, "-B", "-m", module, "--gate"]  # Use the active isolated interpreter.
            values = {  # Keep inputs and outputs inside the fixture repository.
                "--config": ".github/test-quality-config.toml",  # Preserve installed default rule behavior.
                "--baseline": ".github/test-quality-baseline.json",  # Keep comparator changes local.
                "--log-level": "DEBUG",  # Retain completed detector and parsed-file evidence.
                "--report": str(self.outputs[0]),  # Prevent stale JSON report reuse.
                "--summary": str(self.outputs[1]),  # Keep summary existence independently observable.
            }
            for option, value in values.items():  # Preserve argument boundaries without shell evaluation.
                arguments.extend((option, value))  # Diagnostics do not change selection.
            if self.parameters.revision is not None:  # Do not add dormant controls to full-suite mode.
                arguments.extend(("--changed-from", self.parameters.revision))  # Preserve exact endpoint comparison.
                for path in self.parameters.triggers:  # Use dynamically decoded additional controls.
                    arguments.extend(("--full-gate-path", path))  # Do not copy the resolver or its selection.
            arguments.extend(self.parameters.options)  # Permit only caller-declared negative controls.
            logging.debug("Prepared %s analyzer argument tokens", len(arguments))  # Measure the actual vector.
            return tuple(arguments)  # Keep exact argument boundaries in the observation record.

        def revisions(self) -> tuple[str | None, str | None, str]:  # Keep unresolved references explicit.
            revision = self.parameters.revision  # Preserve the requested comparison even when invalid.
            resolved = (  # Keep unresolved references explicit.
                None if revision is None else self.repository.git("rev-parse", "--verify", revision, check=False)
            )
            head = self.repository.git("rev-parse", "HEAD")  # Record the actual fixture candidate revision.
            return revision, resolved or None, head  # Do not invent a base commit for an unresolved reference.

        def execute(self) -> ScopeObservation:  # Collect a fresh unchanged analyzer process with a strict bound.
            arguments = self.arguments()  # Construct the actual argument vector from the request.
            revisions = self.revisions()  # Preserve real base and candidate context before execution.
            logging.info("Running unchanged analyzer for %s", self.parameters.case)  # Announce the real offline action.
            completed = subprocess.run(  # No shell, network, API, or replacement analyzer participates.
                arguments,  # Retain empty and option-like values as real separate tokens.
                cwd=self.repository.root,  # Analyze only the isolated local repository.
                env=self.repository.environment,  # Pass no credentials or inherited Git locations.
                capture_output=True,  # Preserve genuine stdout and stderr for assertions.
                encoding="utf-8",  # Read the installed output consistently across platforms.
                timeout=30,  # Fail rather than skip when an observation exceeds its bound.
                check=False,  # Expected exits 1 and 2 remain actual evidence.
            )
            logging.debug(  # Record real status.
                "Analyzer case %s exited %s", self.parameters.case, completed.returncode
            )  # Record real status.
            process = ScopeObservation.Process(  # Preserve exact raw output instead of synthesizing expected text.
                completed.returncode, completed.stdout, completed.stderr, arguments, revisions
            )
            return ScopeObservation(self.parameters.case, process, self.outputs)  # Decode only this fresh invocation.

    def __init__(  # Derive default controls from the current named CI step.
        self, root: Path, explicit_paths: tuple[str, ...] | None = None
    ) -> None:  # Read live controls by default.
        if explicit_paths is None:  # Ordinary matrix cases must use the current named CI contract.
            live_path = (  # Stay in this worktree.
                Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"
            )  # Stay in this worktree.
            logging.info("Reading live CI for analyzer fixture controls")  # Announce the read-only authority lookup.
            text = live_path.read_text(encoding="utf-8")  # Do not use the old guard's cached trigger values.
            logging.debug("Read %s live CI characters for analyzer controls", len(text))  # Measure the real read.
            explicit_paths = tuple(sorted(CiGateContract.from_text(text).explicit_paths))  # Derive additional paths.
        self.repository = FixtureRepository(root)  # Create no production or global Git state.
        self.explicit_paths = explicit_paths  # Do not cache a second trigger list in this module.
        self.base = self.repository.seed(explicit_paths)  # Commit valid inputs before the intended base.
        self.repository.git(  # Represent a fetched base locally.
            "update-ref", "refs/remotes/origin/intended", self.base
        )  # Represent a fetched base locally.
        self.observation_count = 0  # Allocate unique outputs for each actual invocation.

    def observe(  # Allocate fresh process and output evidence for each case.
        self,  # Retain this fixture's local history and environment.
        case: str,  # Name the matrix group and controlled variant.
        revision: str | None = "origin/intended",  # None requests the real full-suite CLI mode.
        options: tuple[str, ...] = (),  # Use extra controls only for explicit negative cases.
        triggers: tuple[str, ...] | None = None,  # Permit omission pairs without replacing selection.
    ) -> ScopeObservation:
        logging.info("Preparing analyzer observation %s", case)  # Announce request and unique-output state.
        self.observation_count += 1  # Keep report names unique even for repeated case names.
        controls = self.explicit_paths if triggers is None else triggers  # Use decoded live controls by default.
        parameters = self.Run.Parameters(case, revision, options, controls)  # Keep request fields typed and grouped.
        logging.debug("Prepared observation %s number=%s", case, self.observation_count)  # Measure the allocated run.
        return self.Run(self, parameters).execute()  # Execute only after local preparation completes.

    @staticmethod
    def check(observed: ScopeObservation, expected: Expectation.Record) -> None:  # Assert independent behavioral proof.
        logging.info("Checking observed analyzer behavior for %s", observed.case)  # Announce evidence comparison.
        counts = observed.evidence.counts  # Compare actual measurements, not resolver predictions.
        measured = tuple(  # Keep absent fields explicit during expected-error checks.
            counts[name] for name in ("scope_files", "scope_findings", "discovered", "parsed", "new_findings")
        )
        print(observed.summary())  # Keep measured counts visible for every named case.
        assert observed.process.exit_code == expected.exit_code, observed.process.stderr  # Require the exact exit.
        assert measured == expected.counts, observed.process.stderr  # Require every independent count.
        assert observed.evidence.analyzed == expected.analyzed, observed.process.stderr  # Require exact analyzed paths.
        assert observed.evidence.findings == expected.findings, observed.process.stderr  # Require emitted identities.
        assert observed.evidence.reports == expected.reports  # Prevent stale reports from satisfying an empty result.
        logging.debug(  # Confirm the completed comparison.
            "Analyzer case %s matched counts=%s", observed.case, measured
        )  # Confirm the completed comparison.


class GuidanceFixture:  # Keep valid guide input and every mutation fixture-local.
    """Build valid local guide inputs and make one explicit mutation."""

    class Template:  # Construct complete active procedures without editing live guides.
        """Keep synthetic active procedures complete and separate from live documents."""

        @staticmethod
        def analyzer(controls: dict[str, tuple[str, ...]]) -> str:  # Preserve the decoded command's option semantics.
            logging.info("Constructing a fixture analyzer command")  # Announce the text transformation.
            words = ["rtk", "proxy", "test-quality-analyzer"]  # Use only a token-preserving supported prefix.
            for option, values in controls.items():  # Retain each live singleton or repeatable control.
                for value in values:  # Preserve explicit trigger multiplicity.
                    words.append(option)  # Keep the actual live option name.
                    if option != "--gate":  # Gate has no value in the installed CLI.
                        words.append(  # Preserve variable expansion.
                            f'"{value}"' if "$" in value else shlex.quote(value)
                        )  # Preserve variable expansion.
            command = " ".join(words)  # Make a copyable fixture command without executing it.
            logging.debug("Constructed a fixture command with %s words", len(words))  # Measure text construction.
            return command  # Use the command as fixture input, never as an expected behavioral resolver.

        @staticmethod
        def base(shell: str) -> str:  # Give each supported shell a real expanding assignment.
            assignment = '$BASE_REF = "main"' if shell == "powershell" else "BASE_REF=main"  # Bind the intended base.
            return "\n".join(  # Keep fetch destination, verification, and comparison related.
                (
                    assignment,  # The operator chooses the intended branch.
                    'rtk proxy git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"',
                    'rtk proxy git rev-parse --verify "origin/${BASE_REF}^{commit}"',
                )
            )

        @classmethod
        def guide(  # Keep each independent procedure under its owned heading chain.
            cls, path: str, contract: CiGateContract, shell: str = "powershell"
        ) -> str:
            """Generate one active procedure under its exact heading chain."""
            logging.info("Constructing fixture guide %s", path)  # Announce the scoped text transformation.
            headings = "\n".join(  # Enforce the exact owned heading chain.
                "#" * level + " " + title for level, title in SectionCommands.GUIDES[path]
            )
            preflight = (  # Invoke the direct class rather than a command or test-selection wrapper.
                "rtk proxy python -B -m pytest -p no:cacheprovider -s -q "
                "tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides"
            )
            commands = (  # Require all four active fences in every independent fixture guide.
                cls.base(shell),
                preflight,
                cls.analyzer(contract.scoped),
                cls.analyzer(contract.full),
            )
            fences = [  # Keep visible labels outside the executable fence.
                f"{label}\n\n```{shell}\n{command}\n```"  # Supply the next nonblank block after each label.
                for label, command in zip(SectionCommands.LABELS, commands, strict=True)  # Avoid omitted labels.
            ]
            text = headings + "\n\n" + "\n\n".join(fences) + "\n\n## End of fixture section\n"  # Bound the procedure.
            logging.debug("Constructed fixture guide %s with four active fences", path)  # Measure completed structure.
            return text  # Keep this independent from real-guide edits.

    def __init__(self, root: Path) -> None:  # Create required inputs only in the pytest fixture.
        self.root = root  # Keep all mutations away from production files.
        self.files = FixtureRepository.Files(root)  # Share the safe fixture-local file writer.
        live_path = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"  # Use current authority.
        logging.info("Reading live CI for guidance fixture inputs")  # Announce the read-only source access.
        workflow = live_path.read_text(encoding="utf-8")  # Copy current CI, not an obsolete command.
        logging.debug("Read %s live CI characters for fixture inputs", len(workflow))  # Measure the completed read.
        self.contract = CiGateContract.from_text(workflow)  # Derive explicit controls dynamically.
        self.texts = {  # Give all four required input reads real local files.
            path: self.Template.guide(path, self.contract) for path in SectionCommands.GUIDES  # Build each guide.
        }
        self.texts.update(  # Use usable local settings and an empty local comparator.
            {
                ".github/workflows/ci.yml": workflow,  # Preserve the actual named live script shape.
                ".github/test-quality-config.toml": "",  # Keep installed default behavior.
                ".github/test-quality-baseline.json": "[]\n",  # Accept no finding in the fixture.
            }
        )
        for path, text in self.texts.items():  # Write each declared fixture input once.
            self.files.write(path, text)  # Never change the real guides or analyzer inputs.

    def replace(self, path: str, old: str, new: str) -> None:  # Make an explicit whole-input mutation.
        logging.info("Changing fixture input %s", path)  # Announce the controlled text mutation.
        assert old in self.texts[path], f"Fixture mutation has no target in {path}"  # Prevent a vacuous negative case.
        text = self.texts[path].replace(old, new)  # Transform only the declared local input.
        logging.debug("Changed fixture input %s to %s characters", path, len(text))  # Measure the transformation.
        self.files.write(path, text)  # Keep the mutation fixture-local.
        self.texts[path] = text  # Retain current fixture text for subsequent controlled changes.

    def change(self, path: str, label: str, old: str, new: str) -> None:  # Mutate one named active fence only.
        logging.info("Changing active fixture fence in %s", path)  # Announce the specific procedure mutation.
        before, separator, after = self.texts[path].partition(label)  # Locate the known visible fixture label.
        opening, fence, body = after.partition("```")  # Keep unrelated procedure blocks unchanged.
        command, closing, remainder = body.partition("```")  # Bound the mutation to this executable fence.
        assert separator and fence and closing and old in command  # Require a real target in the active block.
        mutated = command.replace(old, new)  # Keep correct text elsewhere from satisfying this case.
        text = before + separator + opening + fence + mutated + closing + remainder  # Preserve other input content.
        logging.debug("Changed active fixture fence in %s", path)  # Record the completed transformation.
        self.files.write(path, text)  # Write only this controlled fixture input.
        self.texts[path] = text  # Keep subsequent mutations based on the current local input.
