"""Prove installed analyzer selection, input safety, and working-tree reads offline."""

from __future__ import annotations  # Keep test annotations safe during collection.

import logging  # Record controlled history and content changes.
import os  # Assert fixture subprocess configuration without changing global settings.
import sys  # Require the active isolated interpreter in each real invocation.
from pathlib import Path  # Keep every fixture inside pytest temporary directories.

import pytest  # Name each required group and assert exact behavioral observations.

from .fixtures import (  # Use genuine isolated processes rather than substitute analyzer output.
    AnalyzerFixture,
    FixtureEnvironment,
    FixtureRepository,
    GuidanceFixture,
)  # Use real offline support.
from .guard import CiGateContract, GuideGuard, SectionCommands  # Pair semantic drift with direct guard failures.


class TestChangedPaths:  # Prove exact name, deletion, rename, and unrelated-path behavior.
    """Cover T01-T04 names, deletions, renames, and unrelated-only changes."""

    @pytest.mark.parametrize(
        "name_case",
        (
            ("tests/test_prefix.py", True),
            ("tests/suffix_test.py", True),
            ("tests/testlookalike.py", False),
            ("tests/sample_tests.py", False),
        ),
        ids=("T01-prefix", "T01-suffix", "T01-lookalike", "T01-plural"),
    )
    @pytest.mark.parametrize("form", ("added", "modified"))
    @pytest.mark.parametrize("weak", (False, True), ids=("strong", "weak"))
    def test_names(  # Use explicit filenames and real findings for inclusion and exclusion.
        self, tmp_path: Path, name_case: tuple[str, bool], form: str, weak: bool
    ) -> None:
        path, recognized = name_case  # Keep case facts grouped within five parameters.
        fixture = AnalyzerFixture(tmp_path)  # Read live controls and create genuine local history.
        repository = fixture.repository  # Keep all subsequent state changes fixture-local.
        if form == "modified":  # Make this path exist in the intended comparison base.
            repository.files.write(path, repository.Files.Sources.strong)  # Commit a strong initial version.
            base = repository.commit("named test base")  # Record the actual starting revision.
            repository.git("update-ref", "refs/remotes/origin/intended", base)  # Keep the intended reference local.
        source = repository.Files.Sources.weak if weak else repository.Files.Sources.strong + "\n"  # Change real bytes.
        repository.files.write(path, source)  # Add or modify this independently named fixture path.
        repository.commit("named test candidate")  # Put the intended path change in HEAD.
        observed = fixture.observe(f"T01-{form}-{path}-weak={weak}")  # Run the unchanged installed analyzer.
        expected = fixture.Expectation.empty()  # Lookalikes must not become selected test files.
        if recognized:  # Define inclusion by the explicit case table, not the installed resolver.
            findings = frozenset({path}) if weak else frozenset()  # Name the expected known witness.
            count = 1 if weak else 0  # Keep finding and new-finding expectations explicit.
            expected = fixture.Expectation.scan(  # Require independent path and finding expectations.
                count, frozenset({path}), findings, (1, count, 1, 1, count)
            )
        fixture.check(observed, expected)  # Assert exact exits, paths, identities, reports, and counts.
        assert (  # Make the explicit path expectation visible in this test.
            observed.evidence.analyzed == expected.analyzed
        )  # Make the explicit path expectation visible in this test.

    @pytest.mark.parametrize(
        "path", ("tests/test_removed.py", "tests/removed_test.py"), ids=("T02-prefix", "T02-suffix")
    )
    def test_deleted_test(self, tmp_path: Path, path: str) -> None:  # Never analyze a nonexistent recognized test.
        fixture = AnalyzerFixture(tmp_path)  # Keep the unchanged weak witness available but outside changed scope.
        repository = fixture.repository  # Mutate only the local repository.
        repository.files.write(path, repository.Files.Sources.weak)  # Give the deleted path a known finding.
        base = repository.commit("before deletion")  # Record the real comparison base.
        repository.git("update-ref", "refs/remotes/origin/intended", base)  # Use the explicit intended reference.
        repository.files.remove(path)  # Delete the actual fixture test.
        repository.commit("deleted test")  # Compare two committed endpoints.
        observed = fixture.observe(f"T02-delete-{path}")  # Run genuine changed-scope selection.
        fixture.check(observed, fixture.Expectation.empty())  # Require no stale report or nonexistent-file analysis.
        assert "No test file changed" in observed.process.stderr  # Require the installed empty-scope reason.

    @pytest.mark.parametrize(
        ("source", "destination", "recognized"),
        (
            ("tests/test_old.py", "tests/test_new.py", True),
            ("tests/test_old.py", "tests/new_test.py", True),
            ("tests/old_test.py", "tests/test_new.py", True),
            ("tests/test_old.py", "tests/ordinary.py", False),
            ("tests/ordinary.py", "tests/test_new.py", True),
            ("tests/ordinary.py", "tests/new_test.py", True),
        ),
        ids=(
            "T03-prefix",
            "T03-suffix",
            "T03-suffix-prefix",
            "T03-leaving",
            "T03-entering-prefix",
            "T03-entering-suffix",
        ),
    )
    def test_rename(  # Require existing recognized destinations and exclude old names.
        self, tmp_path: Path, source: str, destination: str, recognized: bool
    ) -> None:
        """Require the existing recognized destination and exclude old nonexistent names."""
        fixture = AnalyzerFixture(tmp_path)  # Use deterministic fixture-local rename settings.
        repository = fixture.repository  # Never rename a real test or production file.
        repository.files.write(source, repository.Files.Sources.weak)  # Keep exact bytes for rename detection.
        base = repository.commit("before rename")  # Record the source in the intended base.
        repository.git("update-ref", "refs/remotes/origin/intended", base)  # Represent the intended fetched reference.
        repository.files.rename(source, destination)  # Perform a genuine local filesystem rename.
        repository.commit("renamed test")  # Put the rename in the endpoint comparison.
        observed = fixture.observe(f"T03-{source}-to-{destination}")  # Use real Git selection and analyzer reads.
        expected = fixture.Expectation.empty()  # Non-test destinations must stay outside scope.
        if recognized:  # State the expected destination independently of the resolver.
            expected = fixture.Expectation.scan(  # Require the exact recognized rename destination.
                1, frozenset({destination}), frozenset({destination}), (1, 1, 1, 1, 1)
            )
        fixture.check(observed, expected)  # Require exact paths and the line-three weak identity.
        assert not (repository.root / source).exists()  # Confirm that old source names cannot be analyzed.

    def test_unrelated_change_and_missing_baseline(  # Empty scope still requires a usable baseline.
        self, tmp_path: Path
    ) -> None:  # Cover T04 and empty-scope T15 safety.
        fixture = AnalyzerFixture(tmp_path)  # Keep the known weak witness unchanged.
        repository = fixture.repository  # Mutate only an unrelated local document.
        repository.files.write("notes.md", "unrelated candidate\n")  # Do not change any recognized test path.
        repository.commit("unrelated change")  # Create a valid committed empty test scope.
        valid = fixture.observe("T04-valid-empty")  # Run the real baseline comparison at zero selected tests.
        fixture.check(valid, fixture.Expectation.empty())  # Require genuine zero scope counts without reports.
        repository.files.remove(".github/test-quality-baseline.json")  # Make only the current required input missing.
        invalid = fixture.observe("T04-T15-empty-missing-baseline")  # Keep the same committed endpoint difference.
        fixture.check(invalid, fixture.Expectation.error())  # A missing comparator is not a successful zero scan.
        assert "baseline error" in invalid.process.stderr  # Require the actual named installed input failure.

    @pytest.mark.parametrize("accepted", (False, True), ids=("T09-new-finding", "T09-accepted-finding"))
    def test_full_mode(  # Full-suite scope must include unchanged witnesses regardless of acceptance.
        self, tmp_path: Path, accepted: bool
    ) -> None:  # Prove push/manual mode includes unchanged tests.
        fixture = AnalyzerFixture(tmp_path)  # Keep the same two ordinary fixture tests.
        repository = fixture.repository  # Use a fixture-local accepted comparator only in its dedicated case.
        if accepted:  # Establish accepted identities before the comparison base.
            baseline = repository.Files.Sources.baseline("tests/test_witness.py")  # Define the known identity directly.
            repository.files.write(".github/test-quality-baseline.json", baseline)  # Never rewrite production findings.
            base = repository.commit("accepted fixture baseline")  # Keep later comparisons free of baseline triggers.
            repository.git("update-ref", "refs/remotes/origin/intended", base)  # Preserve an equal endpoint control.
        full = fixture.observe(f"T09-full-accepted={accepted}", revision=None)  # Omit all changed-scope controls.
        new_count = 0 if accepted else 1  # Baseline acceptance changes new findings, not selection.
        expected = fixture.Expectation.scan(  # Name both analyzed paths and the unchanged weak witness.
            new_count,
            frozenset({"tests/test_changed.py", "tests/test_witness.py"}),
            frozenset({"tests/test_witness.py"}),
            (2, 1, 2, 2, new_count),
        )
        fixture.check(full, expected)  # Require genuine discovered, parsed, and analyzed scope.
        fixture.check(  # Contrast scoped mode.
            fixture.observe("T09-incorrect-changed-mode"), fixture.Expectation.empty()
        )  # Contrast scoped mode.
        assert full.evidence.counts["scope_files"] == 2  # Full-suite mode must include both unchanged test paths.


class TestRevisionAndContent:  # Distinguish endpoint selection from current file content.
    """Cover T10-T14 endpoint history and committed selection versus current content."""

    class Histories:  # Keep divergent revisions and expected witness identities explicit.
        """Build explicit divergent history and controlled local state changes."""

        @staticmethod
        def divergent(fixture: AnalyzerFixture) -> str:  # Distinguish endpoint comparison from merge-base selection.
            repository = fixture.repository  # Keep all history changes inside the fixture repository.
            repository.files.write(  # Common A contains the witness.
                "tests/test_shared.py", repository.Files.Sources.weak
            )  # Common A contains the witness.
            common = repository.commit("common A")  # Record the independent common ancestor.
            repository.git(  # Preserve the alternate valid base locally.
                "update-ref", "refs/remotes/origin/common", common
            )  # Preserve the alternate valid base locally.
            repository.files.write(  # Base B strengthens the test.
                "tests/test_shared.py", repository.Files.Sources.strong
            )  # Base B strengthens the test.
            intended = repository.commit("intended B")  # Record the intended comparison endpoint.
            repository.git("update-ref", "refs/remotes/origin/intended", intended)  # Use the intended branch reference.
            repository.git("switch", "--detach", common)  # Branch only this disposable fixture history.
            repository.files.write(  # H retains the common weak test.
                "notes.md", "candidate H changes only a document\n"
            )  # H retains the common weak test.
            repository.commit("candidate H")  # Commit the divergent candidate without a test edit.
            return intended  # Return the actual intended base revision for observation assertions.

        @staticmethod
        def weak(path: str) -> AnalyzerFixture.Expectation.Record:  # Define one known selected finding independently.
            return AnalyzerFixture.Expectation.scan(  # Require the known line-three witness identity and counts.
                1, frozenset({path}), frozenset({path}), (1, 1, 1, 1, 1)
            )

        @staticmethod
        def strong(  # Define independent zero-finding evidence for a selected path.
            path: str,
        ) -> AnalyzerFixture.Expectation.Record:  # Define one selected strong control independently.
            return AnalyzerFixture.Expectation.scan(  # Require the selected path with zero filtered findings.
                0, frozenset({path}), frozenset(), (1, 0, 1, 1, 0)
            )

    def test_endpoint_and_alternate_base(self, tmp_path: Path) -> None:  # Cover T10 correct and incorrect valid bases.
        fixture = AnalyzerFixture(tmp_path)  # Use the same installed comparison for both valid references.
        intended = self.Histories.divergent(fixture)  # Create A, B, and H without another worktree.
        endpoint = fixture.observe(  # B to H must include the shared test.
            "T10-intended-endpoint", revision="origin/intended"
        )  # B to H must include the shared test.
        fixture.check(  # Assert exact inclusion and finding identity.
            endpoint, self.Histories.weak("tests/test_shared.py")
        )  # Assert exact inclusion and finding identity.
        assert endpoint.process.revisions[1] == intended  # Prove that the intended endpoint actually resolved.
        common = fixture.observe("T10-incorrect-common-base", revision="origin/common")  # A to H changes no test.
        fixture.check(common, fixture.Expectation.empty())  # A valid substitute can conceal the intended finding.
        assert endpoint.process.revisions[1] != common.process.revisions[1]  # Keep the two actual bases distinct.

    @pytest.mark.parametrize(
        "revision", ("origin/unknown", "", "--option-like"), ids=("T11-unknown", "T11-empty", "T11-option")
    )
    def test_invalid_revision(  # Unknown references must fail rather than claim zero scope.
        self, tmp_path: Path, revision: str
    ) -> None:  # A missing base must not pass at zero scope.
        fixture = AnalyzerFixture(tmp_path)  # First prove a known resolving intended reference.
        valid = fixture.observe("T11-resolving-intended")  # Run the unchanged candidate against its known base.
        fixture.check(valid, fixture.Expectation.empty())  # Require valid baseline handling.
        assert valid.process.revisions[1] == fixture.base  # Record the actual resolved base.
        invalid = fixture.observe(f"T11-invalid-{revision}", revision=revision)  # Pass the actual invalid CLI value.
        fixture.check(invalid, fixture.Expectation.error())  # Require exit 2 and unavailable scan measurements.
        assert (  # Require the real unresolved-scope or usage error.
            "--changed-from" in invalid.process.stderr or "changed-file scope error" in invalid.process.stderr
        )

    @pytest.mark.parametrize(
        ("state", "path"),
        (
            ("staged_add", "tests/test_staged.py"),
            ("staged_modify", "tests/test_changed.py"),
            ("unstaged_modify", "tests/test_changed.py"),
            ("untracked", "tests/test_untracked.py"),
        ),
        ids=("T12-staged-added", "T12-staged-modified", "T13-unstaged", "T14-untracked"),
    )
    def test_before_and_after_commit(  # Prove uncommitted exclusion and selected current-content reads.
        self, tmp_path: Path, state: str, path: str
    ) -> None:
        """Prove committed path selection and dirty selected-content reads separately."""
        fixture = AnalyzerFixture(tmp_path)  # Keep both endpoint revisions equal before the controlled commit.
        repository = fixture.repository  # Mutate only this local fixture.
        repository.files.write(path, repository.Files.Sources.weak)  # Supply a known uncommitted weak finding.
        if state.startswith("staged"):  # Stage only the named case input.
            repository.git("add", "--", path)  # Do not change HEAD before the exclusion observation.
        before = fixture.observe(f"{state}-before-commit")  # Staged, unstaged, and untracked-only paths stay excluded.
        fixture.check(before, fixture.Expectation.empty())  # Do not confuse working-tree content with selected paths.
        repository.commit("committed state witness")  # Put the intended test path into the endpoint difference.
        after = fixture.observe(f"{state}-after-commit")  # The same weak source must now enter selection.
        fixture.check(after, self.Histories.weak(path))  # Require its exact line-three emitted identity.
        repository.files.write(path, repository.Files.Sources.strong)  # Change only selected current file content.
        if state.startswith("staged"):  # Cover staged strong content on an already selected path.
            repository.git("add", "--", path)  # Keep the same committed candidate and intended base.
        current = fixture.observe(f"{state}-selected-current-strong")  # The analyzer reads the current working tree.
        fixture.check(current, self.Histories.strong(path))  # Selection remains one path while findings change.
        assert after.process.revisions == current.process.revisions  # Prove that only analyzed content changed.

    def test_index_and_current_content_differ(self, tmp_path: Path) -> None:  # Cover the T13 index/content contrast.
        fixture = AnalyzerFixture(tmp_path)  # Start with a strong committed control.
        repository = fixture.repository  # Keep index and working-tree experiments fixture-local.
        path = "tests/test_changed.py"  # Name expected selection independently.
        repository.files.write(path, repository.Files.Sources.weak)  # Make a tracked unstaged-only weak edit.
        fixture.check(fixture.observe("T13-unselected-dirty"), fixture.Expectation.empty())  # Exclude dirty-only paths.
        repository.commit("selected weak candidate")  # Commit the path that must enter changed-test scope.
        repository.files.write(path, repository.Files.Sources.strong)  # Put strong source in the local index.
        repository.git("add", "--", path)  # Stage the strong version without changing HEAD.
        repository.files.write(path, repository.Files.Sources.weak)  # Keep weak source in the current working tree.
        assert (  # Prove actual index content.
            repository.git("show", ":" + path) == repository.Files.Sources.strong.strip()
        )  # Prove actual index content.
        weak = fixture.observe("T13-index-strong-current-weak")  # The installed analyzer must ignore the index source.
        fixture.check(weak, self.Histories.weak(path))  # Require the current weak finding.
        repository.files.write(path, repository.Files.Sources.strong)  # Change only the current file content.
        strong = fixture.observe("T13-same-head-current-strong")  # Keep both committed endpoints unchanged.
        fixture.check(strong, self.Histories.strong(path))  # Require the selected path with no weak finding.
        assert weak.process.revisions == strong.process.revisions  # Tie finding changes to content, not a new commit.


class TestTriggerPaths:  # Require unchanged witness inclusion for every effective trigger.
    """Cover every live explicit trigger and both automatic input triggers."""

    @staticmethod
    def explicit_cases() -> tuple[str, ...]:  # Derive parametrized controls from actual current CI.
        path = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"  # Stay in this worktree.
        logging.info("Reading live CI for explicit trigger case collection")  # Announce read-only authority.
        text = path.read_text(encoding="utf-8")  # Do not import another guard's cached constants.
        logging.debug("Read %s live CI characters for trigger case collection", len(text))  # Measure the read.
        return tuple(sorted(CiGateContract.from_text(text).explicit_paths))  # Cover every decoded live explicit value.

    class Mutation:  # Keep trigger histories and comparator acceptance independently controlled.
        """Build trigger histories with explicit comparator and rename controls."""

        @staticmethod
        def accepted(fixture: AnalyzerFixture, accepted: bool) -> str:  # Establish identities before comparison.
            if not accepted:  # Ordinary trigger cases accept no finding.
                return "[]\n"  # Keep an explicit independent comparator.
            repository = fixture.repository  # Write only this fixture's local accepted identity.
            text = repository.Files.Sources.baseline("tests/test_witness.py")  # Define the known identity directly.
            repository.files.write(".github/test-quality-baseline.json", text)  # Keep production findings unchanged.
            revision = repository.commit("accepted trigger comparator")  # Commit acceptance before the trigger base.
            repository.git("update-ref", "refs/remotes/origin/intended", revision)  # Keep the baseline out of the diff.
            return text  # Preserve the same comparator for controlled restored-input observations.

        @staticmethod
        def incoming(  # Make a real recognized rename name the exact live trigger.
            fixture: AnalyzerFixture, path: str, text: str, form: str
        ) -> None:
            """Make additions and recognized incoming renames name the exact trigger."""
            repository = fixture.repository  # Keep all rename and reference settings local.
            if form == "addition":  # Remove the required path from the comparison base.
                repository.files.remove(path)  # The candidate restores a genuine added trigger.
            else:  # Preserve exact bytes for a recognized incoming rename.
                repository.git("config", "--local", "diff.renameEmpty", "true")  # Detect empty settings locally.
                repository.files.rename(path, path + ".previous")  # Place the source under another committed name.
            base = repository.commit("before incoming trigger")  # Record the actual comparison base.
            repository.git("update-ref", "refs/remotes/origin/intended", base)  # Use the intended local reference.
            if form == "addition":  # Restore valid required content as an actual addition.
                repository.files.write(path, text)  # Keep settings and comparator syntax valid.
            else:  # Rename back into the exact live trigger path.
                repository.files.rename(path + ".previous", path)  # Let real rename detection name the destination.

        @classmethod
        def apply(cls, fixture: AnalyzerFixture, path: str, form: str) -> None:  # Put the trigger in the endpoint diff.
            repository = fixture.repository  # Restrict history operations to the fixture.
            logging.info("Reading trigger input %s for %s", path, form)  # Announce the source read.
            text = (repository.root / path).read_text(encoding="utf-8")  # Preserve usable required input content.
            logging.debug("Read %s trigger source characters", len(text))  # Measure the completed read.
            if form in {"addition", "rename_in"}:  # Both forms name a genuine candidate destination.
                cls.incoming(fixture, path, text, form)  # Preserve real incoming rename semantics.
            elif form == "modification":  # A whitespace-only change still names this path.
                repository.files.write(path, text + "\n")  # Keep required syntax valid.
            elif form == "deletion":  # The old endpoint must name the deleted trigger.
                repository.files.remove(path)  # Missing settings default, while missing baselines fail.
            else:  # Expose both paths for the controlled outgoing rename-removal case.
                assert form == "rename"  # Do not silently accept an unsupported history form.
                repository.git("config", "--local", "diff.renames", "false")  # Make old-path visibility explicit.
                repository.files.rename(path, path + ".moved")  # Keep the filesystem rename genuine.
            repository.commit("trigger " + form)  # Use the unchanged analyzer's committed endpoint comparison.

        @staticmethod
        def full(accepted: bool) -> AnalyzerFixture.Expectation.Record:  # Define independent full-scan expectations.
            new = 0 if accepted else 1  # Comparator acceptance changes new findings, not scope.
            return AnalyzerFixture.Expectation.scan(  # Require both named paths and the unchanged weak identity.
                new,
                frozenset({"tests/test_changed.py", "tests/test_witness.py"}),
                frozenset({"tests/test_witness.py"}),
                (2, 1, 2, 2, new),
            )

    @pytest.mark.parametrize(
        "path", explicit_cases(), ids=lambda path: f"T05-{path}" if path.endswith("ci.yml") else f"T06-{path}"
    )
    @pytest.mark.parametrize(
        ("form", "accepted"),
        (
            ("addition", False),
            ("modification", False),
            ("deletion", False),
            ("rename", False),
            ("rename_in", False),
            ("modification", True),
        ),
    )
    def test_explicit_trigger(  # Prove full scope and real omission pairs for every live control.
        self, tmp_path: Path, path: str, form: str, accepted: bool
    ) -> None:  # Cover all applicable explicit forms.
        fixture = AnalyzerFixture(tmp_path)  # Read live trigger controls again for the actual invocation.
        self.Mutation.accepted(fixture, accepted)  # Commit accepted identities before the comparison base.
        self.Mutation.apply(fixture, path, form)  # Put the exact trigger in the committed endpoint difference.
        observed = fixture.observe(f"T05-T06-{path}-{form}")  # Execute the unchanged installed scope resolver.
        expected = self.Mutation.full(accepted)  # Keep analyzed paths independent of comparator acceptance.
        fixture.check(observed, expected)  # Require the real two-path report and weak finding.
        assert (  # Require actual trigger reason.
            path + " changed, so the run scans every test root" in observed.process.stderr
        )  # Require actual trigger reason.
        remaining = tuple(  # Omit only this explicit control.
            value for value in fixture.explicit_paths if value != path
        )  # Omit only this explicit control.
        fixture.check(  # Prove actual exclusion when the live trigger is omitted.
            fixture.observe("T16-omitted-explicit-" + path, triggers=remaining), fixture.Expectation.empty()
        )
        incorrect = (*remaining, "wrong-trigger.txt")  # Replace only the actual trigger value under the same history.
        fixture.check(  # Prove actual exclusion when the live trigger is wrong.
            fixture.observe("T16-incorrect-explicit-" + path, triggers=incorrect), fixture.Expectation.empty()
        )

    @pytest.mark.parametrize(
        ("form", "accepted"),
        (
            ("addition", False),
            ("modification", False),
            ("deletion", False),
            ("rename", False),
            ("rename_in", False),
            ("modification", True),
        ),
        ids=("T07-add", "T07-modify", "T07-delete", "T07-rename-out", "T07-rename-in", "T07-accepted"),
    )
    def test_settings_trigger(  # Prove automatic scope and installed missing-settings defaults.
        self, tmp_path: Path, form: str, accepted: bool
    ) -> None:  # Cover default behavior after deletion or rename.
        fixture = AnalyzerFixture(tmp_path)  # Keep a valid local baseline throughout this group.
        path = ".github/test-quality-config.toml"  # Name the independently required automatic settings trigger.
        self.Mutation.accepted(fixture, accepted)  # Keep accepted comparator changes before the intended base.
        self.Mutation.apply(fixture, path, form)  # Put this automatic trigger in the committed endpoint difference.
        observed = fixture.observe("T07-settings-" + form)  # Run unchanged automatic trigger behavior.
        expected = self.Mutation.full(accepted)  # No explicit config trigger is needed.
        fixture.check(observed, expected)  # Require both tests and the unchanged weak identity.
        assert (  # Require installed reason.
            path + " changed, so the run scans every test root" in observed.process.stderr
        )  # Require installed reason.
        if form in {"deletion", "rename"}:  # Missing settings intentionally retain installed defaults.
            assert "missing; using built-in defaults" in observed.process.stderr  # Do not claim a config error.

    @pytest.mark.parametrize(
        ("form", "accepted"),
        (
            ("addition", False),
            ("modification", False),
            ("deletion", False),
            ("rename", False),
            ("rename_in", False),
            ("modification", True),
        ),
        ids=("T08-add", "T08-modify", "T08-delete", "T08-rename-out", "T08-rename-in", "T08-accepted"),
    )
    def test_baseline_trigger(self, tmp_path: Path, form: str, accepted: bool) -> None:  # Preserve real error evidence.
        fixture = AnalyzerFixture(tmp_path)  # Start with valid local inputs and an unchanged weak witness.
        path = ".github/test-quality-baseline.json"  # Name the independently required automatic comparator trigger.
        baseline = self.Mutation.accepted(  # Preserve the intended local comparator before comparison.
            fixture, accepted
        )  # Preserve the intended local comparator before comparison.
        self.Mutation.apply(fixture, path, form)  # Use genuine committed baseline path changes.
        observed = fixture.observe("T08-baseline-" + form)  # Keep the installed selection and baseline ordering.
        paths = frozenset({"tests/test_changed.py", "tests/test_witness.py"})  # Name both full-scope paths explicitly.
        if form in {"deletion", "rename"}:  # The baseline error occurs after real discovery and detection.
            expected_error = fixture.Expectation.error(  # Keep unavailable gate fields honest.
                (None, None, 2, 2, None), paths
            )  # Keep unavailable gate fields honest.
            fixture.check(observed, expected_error)  # Require completed detector traces and missing reports.
            assert "baseline error" in observed.process.stderr  # Require the actual input failure.
            fixture.repository.files.write(path, baseline)  # Restore only this fixture's current required comparator.
            observed = fixture.observe(  # Keep the same committed deletion history.
                "T08-dirty-restored-baseline-" + form
            )  # Keep the same committed deletion history.
        expected = self.Mutation.full(accepted)  # Keep findings and scope independent of new-finding acceptance.
        fixture.check(observed, expected)  # Controlled dirty evidence does not claim a clean pre-push candidate.
        assert (  # Require installed trigger.
            path + " changed, so the run scans every test root" in observed.process.stderr
        )  # Require installed trigger.


class TestAnalyzerInputsAndDrift:  # Require real errors and real finding changes for semantic drift.
    """Cover T15 actual settings/baseline behavior and T16 semantic drift pairs."""

    @pytest.mark.parametrize("form", ("missing", "empty"), ids=lambda form: "T15-settings-" + form)
    def test_settings_defaults(  # Do not claim missing settings cause an analyzer error.
        self, tmp_path: Path, form: str
    ) -> None:  # Distinguish guard rejection from CLI defaults.
        fixture = AnalyzerFixture(tmp_path)  # Keep valid baseline inputs and an unchanged committed test set.
        path = ".github/test-quality-config.toml"  # Make this current input missing or empty without changing HEAD.
        if form == "missing":  # A missing settings file intentionally selects built-in defaults.
            fixture.repository.files.remove(path)  # Do not turn this dirty removal into a committed trigger.
        else:  # A readable empty file also selects the documented defaults.
            fixture.repository.files.write(path, "")  # Preserve the actual empty-settings input.
        observed = fixture.observe(  # Execute real default behavior at empty changed scope.
            "T15-default-settings-" + form
        )  # Execute real default behavior at empty changed scope.
        fixture.check(observed, fixture.Expectation.empty())  # Missing settings alone are not an analyzer error.
        assert form + "; using built-in defaults" in observed.process.stderr  # Require the installed explanatory log.

    @pytest.mark.parametrize(
        "form", ("directory", "malformed", "unknown_rule", "non_boolean"), ids=lambda form: "T15-settings-" + form
    )
    def test_invalid_settings(self, tmp_path: Path, form: str) -> None:  # Prove actual unreadable and config failures.
        fixture = AnalyzerFixture(tmp_path)  # Keep all other analyzer inputs valid.
        path = ".github/test-quality-config.toml"  # Target only the fixture-local current settings input.
        if form == "directory":  # A directory gives a genuine portable file-read error.
            fixture.repository.files.remove(path)  # Remove only the controlled temporary file.
            logging.info("Creating unreadable settings directory")  # Announce the fixture-only write.
            (tmp_path / path).mkdir()  # Do not rely on filesystem permissions or root-sensitive skips.
            logging.debug("Created unreadable settings directory")  # Confirm the actual read-failure input.
        else:  # Use installed semantic errors as well as malformed TOML.
            text = {  # Supply genuine installed settings failure cases.
                "malformed": "[rules\n",
                "unknown_rule": "[rules]\nwrong = true\n",
                "non_boolean": "[rules]\nweak_assert_not_none = 1\n",
            }[form]
            fixture.repository.files.write(path, text)  # Pass the actual bad content to unchanged ConfigLoader.
        observed = fixture.observe("T15-invalid-settings-" + form)  # Do not mock or replace analyzer reads.
        fixture.check(observed, fixture.Expectation.error())  # Require exit 2 with unavailable scan measurements.
        expected = "IO error" if form == "directory" else "config error"  # Name the independent expected error class.
        assert expected in observed.process.stderr  # Require the actual installed named failure.

    @pytest.mark.parametrize(
        "form",
        ("missing", "directory", "malformed", "not_list", "incomplete", "disabled"),
        ids=lambda form: "T15-baseline-" + form,
    )
    def test_invalid_baseline_at_empty_scope(  # Zero selected tests still require a comparator.
        self, tmp_path: Path, form: str
    ) -> None:  # Require a usable comparator at zero tests.
        fixture = AnalyzerFixture(tmp_path)  # Keep committed endpoints equal and settings readable.
        path = ".github/test-quality-baseline.json"  # Mutate only the fixture-local current comparator.
        options: tuple[str, ...] = ()  # Preserve the configured baseline unless the case explicitly disables it.
        if form in {"missing", "directory"}:  # Use real missing and portable unreadable inputs.
            fixture.repository.files.remove(path)  # Never edit the production baseline.
            if form == "directory":  # Ensure a genuine file-read failure on every supported platform.
                logging.info("Creating unreadable baseline directory")  # Announce the fixture write.
                (tmp_path / path).mkdir()  # Do not depend on chmod behavior or process privileges.
                logging.debug("Created unreadable baseline directory")  # Confirm the controlled input.
        elif form == "disabled":  # Gate mode must reject an explicitly empty comparator option.
            options = ("--baseline", "")  # Preserve the empty argument as a real subprocess token.
        else:  # Feed actual malformed or unusable JSON to the installed comparator.
            text = {"malformed": "{", "not_list": "{}", "incomplete": "[{}]"}[  # Define invalid inputs independently.
                form
            ]  # Define invalid inputs independently.
            fixture.repository.files.write(path, text)  # Keep failures genuine and fixture-local.
        observed = fixture.observe(  # No test needs to enter scope.
            "T15-empty-invalid-baseline-" + form, options=options
        )  # No test needs to enter scope.
        fixture.check(observed, fixture.Expectation.error())  # Require exit 2 rather than a fabricated zero result.
        reason = "--gate requires --baseline" if form == "disabled" else "baseline error"  # Name the expected failure.
        assert reason in observed.process.stderr  # Require actual installed error evidence.

    @pytest.mark.parametrize(
        "options",
        (
            ("--roots", "tests"),
            ("--write-baseline",),
            ("--prune-baseline",),
            ("--write-baseline", "--prune-baseline"),
            ("--unknown-control",),
        ),
        ids=("T15-roots-conflict", "T15-write-conflict", "T15-prune-conflict", "T15-modes", "T15-unknown"),
    )
    def test_invalid_controls(  # Invalid modes must fail before scanning or rewriting inputs.
        self, tmp_path: Path, options: tuple[str, ...]
    ) -> None:  # Prove actual CLI mode rejection.
        fixture = AnalyzerFixture(tmp_path)  # Use valid current inputs to isolate control behavior.
        observed = fixture.observe(  # Run the unchanged argument parser.
            "T15-invalid-controls-" + options[0], options=options
        )  # Run the unchanged argument parser.
        fixture.check(observed, fixture.Expectation.error())  # Require failure before discovery or report generation.
        assert (  # Require the actual installed mode or usage failure.
            "cannot be used" in observed.process.stderr
            or "mutually exclusive" in observed.process.stderr
            or "unrecognized arguments" in observed.process.stderr
        )
        assert (  # Keep the local baseline unchanged.
            fixture.repository.git("show", "HEAD:.github/test-quality-baseline.json") == "[]"
        )  # Keep the local baseline unchanged.

    def test_disabled_rule_behavior_and_guard_rejection(  # Pair direct rejection with genuine filtered findings.
        self, tmp_path: Path
    ) -> None:  # Pair T16 text drift with real behavior.
        guides = GuidanceFixture(tmp_path / "guides")  # Keep direct guard inputs separate from analyzer history.
        guide_path = "agents.md"  # Select one guide independently for the behavioral pair.
        guides.change(  # Weaken actual controls.
            guide_path, SectionCommands.LABELS[2], "--gate", "--gate --disable-rule weak_is_not_none"
        )  # Weaken actual controls.
        guard = GuideGuard(guides.root)  # Require a direct measured rejection, not an accepted exception.
        assert guard.run() is False and guide_path in guard.ledger.errors[0]  # Reject semantic suppression in guidance.
        fixture = AnalyzerFixture(tmp_path / "repository")  # Never alter the analyzer to obtain this pair.
        repository = fixture.repository  # Keep the real CLI experiment local.
        path = "tests/test_changed.py"  # Keep the expected selected identity explicit.
        repository.files.write(path, repository.Files.Sources.weak)  # Commit a known selected finding.
        repository.commit("selected weak control")  # Put this test in the two-endpoint comparison.
        normal = fixture.observe("T16-normal-weak-control")  # Preserve the configured detector behavior.
        expected = TestRevisionAndContent.Histories.weak(path)  # Require the known identity.
        fixture.check(normal, expected)  # Require the actual emitted weak_is_not_none identity.
        altered = fixture.observe(  # Negative case only.
            "T16-disabled-weak-control", options=("--disable-rule", "weak_is_not_none")
        )  # Negative case only.
        strong = TestRevisionAndContent.Histories.strong(path)  # Require no filtered finding.
        fixture.check(altered, strong)  # Prove unchanged selection with a suppressed actual finding.
        assert normal.process.revisions == altered.process.revisions  # Keep the same committed history for the pair.


class TestFixtureSafety:  # Prove repository isolation and fresh-process observation safety.
    """Prove subprocess isolation and unique observation output without a network."""

    class Source:  # Build override mappings without changing the real environment.
        """Provide poisonous input mappings without changing process-global state."""

        @staticmethod
        def protocol(whole: bool) -> dict[str, str]:  # Exercise both prior-art configuration-protocol branches.
            logging.info("Constructing isolation-test input variables")  # Announce a controlled data transformation.
            source = {  # Do not install these variables into the real process environment.
                "PATH": os.environ["PATH"],  # Keep a real executable lookup path.
                "GIT_DIR": "/must-not-be-used",  # Expose a leaked repository override.
                "GIT_WORK_TREE": "/must-not-be-used",  # Expose a leaked worktree override.
                "GIT_INDEX_FILE": "/must-not-be-used",  # Expose a leaked index override.
                "GIT_COMMON_DIR": "/must-not-be-used",  # Expose a leaked shared-directory override.
                "GIT_CONFIG_COUNT": "1",  # Exercise the editor configuration protocol.
                "GIT_CONFIG_KEY_0": "core.fsmonitor",  # Exercise a real Git setting name.
                "MIST_APITOKEN": "fixture-only-secret",  # Do not pass a synthetic API credential.
                "MIST_API_TOKEN": "fixture-only-secret",  # Cover the other API credential spelling.
                "GH_TOKEN": "fixture-only-secret",  # Do not pass GitHub credentials.
                "PYTHONPATH": "/must-not-be-used",  # Do not load an external analyzer replacement.
            }
            if whole:  # Both complete and incomplete protocols must remain outside fixtures.
                source["GIT_CONFIG_VALUE_0"] = "true"  # Define the complete-protocol contrast.
            logging.debug("Constructed %s isolation-test variables", len(source))  # Measure construction safely.
            return source  # Keep the poisoned mapping fixture-local.

    @pytest.mark.parametrize("whole", (False, True), ids=("T15-incomplete-editor-config", "T15-whole-editor-config"))
    def test_environment_overrides_are_local(  # Keep whole and incomplete Git protocols outside fixtures.
        self, whole: bool
    ) -> None:  # Reuse prior art without retaining repository overrides.
        source = self.Source.protocol(whole)  # Inject overrides into a copied mapping, never the real environment.
        original = source.copy()  # Prove that sanitization does not mutate caller state.
        environment = FixtureEnvironment.create(source)  # Apply the reused protocol repair and fixture isolation.
        assert source == original  # Do not change global or caller configuration.
        assert (  # Block inherited repository and configuration locations.
            not {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_CONFIG_COUNT"}
            & environment.keys()
        )
        assert (  # Pass no API credentials.
            not {"MIST_APITOKEN", "MIST_API_TOKEN", "GH_TOKEN", "PYTHONPATH"} & environment.keys()
        )  # Pass no API credentials.
        assert environment["GIT_CONFIG_GLOBAL"] == os.devnull  # Disable production global configuration reads.
        assert (  # Block network prompts.
            environment["GIT_ALLOW_PROTOCOL"] == "file" and environment["GIT_TERMINAL_PROMPT"] == "0"
        )  # Block network prompts.

    def test_git_ignores_poisoned_locations(self, tmp_path: Path) -> None:  # Prove actual Git uses only fixture state.
        repository = FixtureRepository(tmp_path / "repository")  # Initialize only the explicit temporary root.
        source = dict(os.environ)  # Keep real process state untouched.
        source.update(  # Exercise foreign locations without changing process state.
            GIT_DIR=str(tmp_path / "foreign"),
            GIT_WORK_TREE=str(tmp_path / "foreign"),
            GIT_INDEX_FILE=str(tmp_path / "foreign-index"),
        )
        repository.environment = FixtureEnvironment.create(  # Remove poisoned locations before every subprocess.
            source
        )  # Remove poisoned locations before every later subprocess.
        repository.files.write("local.txt", "fixture-local content\n")  # Create a local commit witness.
        revision = repository.commit("isolated commit")  # Run genuine Git with the isolated environment.
        assert repository.git("rev-parse", "--show-toplevel") == str(  # Require the actual root.
            repository.root.resolve()
        )  # Require the actual root.
        assert (  # Verify actual committed bytes.
            repository.git("show", revision + ":local.txt") == "fixture-local content"
        )  # Verify actual committed bytes.
        assert (  # Do not mutate foreign state.
            not (tmp_path / "foreign").exists() and not (tmp_path / "foreign-index").exists()
        )  # Do not mutate foreign state.

    def test_active_interpreter_and_unique_outputs(  # Prevent stale reports or a different interpreter from passing.
        self, tmp_path: Path
    ) -> None:  # Prove fresh installed processes and reports.
        fixture = AnalyzerFixture(tmp_path)  # Keep one local committed selection history.
        repository = fixture.repository  # Write only the selected local test.
        path = "tests/test_changed.py"  # Define exact expected path identity.
        repository.files.write(path, repository.Files.Sources.weak)  # Supply the known finding.
        repository.commit("selected output witness")  # Make it a committed changed path.
        first = fixture.observe("T13-first-unique-output")  # Run a fresh installed analyzer process.
        fixture.check(first, TestRevisionAndContent.Histories.weak(path))  # Require real first report identities.
        repository.files.write(path, repository.Files.Sources.strong)  # Change only current selected content.
        second = fixture.observe("T13-second-unique-output")  # Run another fresh process with another report path.
        fixture.check(second, TestRevisionAndContent.Histories.strong(path))  # Do not reuse the first weak report.
        assert first.outputs != second.outputs  # Allocate unique outputs for every observation.
        assert first.process.arguments[:4] == (  # Require the active unchanged installed module entry point.
            sys.executable,
            "-B",
            "-m",
            "misthelper_devtools.test_quality_analyzer",
        )
        assert first.process.revisions == second.process.revisions  # Tie result changes to current content only.
