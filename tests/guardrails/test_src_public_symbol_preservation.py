"""Compare public module symbols across the source package move."""  # State the moved-module compatibility contract.

from __future__ import annotations  # Use current annotation behavior in the guard.

import ast  # Read module-level symbols without importing runtime dependencies.
import io  # Give tarfile an in-memory archive stream.
import subprocess  # Read the base source tree through Git.
import tarfile  # Read all base modules from one Git archive command.
from pathlib import Path  # Resolve the current repository and moved modules.
from unittest.mock import Mock  # Simulate exact Git outcomes in direct guard tests.

import pytest  # Prove that the guard still refuses an unknown package name.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve the active worktree from this guard file.
SOURCE_ROOT = REPOSITORY_ROOT / "src"  # Read current modules from the refactored source tree.
MERGE_BASE_DEEPEN = "100"  # Fetch bounded history beyond the shallow checkout boundary.
MERGE_BASE_DEEPEN_ROUNDS = 3  # Repeat the bounded fetch, then read the complete history, before failing.
PACKAGE_GROUPS = {  # Map every old direct package to its new domain and group.
    "foundation/runtime": {"bootstrap", "config", "input", "time", "validation"},
    "foundation/models": {"data", "dataclasses"},
    "foundation/persistence": {"cache", "db"},
    "foundation/support": {"refactors", "utils"},
    "mist/access": {"api", "audit", "auth"},
    "mist/resources": {"device", "gateway", "inventory", "org", "site"},
    "mist/intelligence": {"analytics", "juniper_docs", "marvis", "reports", "troubleshooting"},
    "mist/realtime": {"websocket", "websocket_streams"},
    "mist/networking": {"network"},
    "operations/execution": {"capture", "firmware", "ssh", "ssid_consolidation"},
    "operations/exporting": {"export"},
    "operations/hardware": {"mib_generator"},
    "operations/protection": {"security"},
    "interfaces/portals": {"upgrade_portal"},
    "interfaces/visualization": {"maps", "ui"},
    "interfaces/monitoring": {"metrics_gateway"},
}  # Keep the test map identical to the approved package data model.
MODULE_PATHS = {  # Map each old direct module to its new canonical module.
    "constants.py": "foundation/constants.py",
    "foundation/persistence/db/arango_writer.py": "foundation/persistence/db/writers/arango_writer.py",
    "foundation/persistence/db/redis_writer.py": "foundation/persistence/db/writers/redis_writer.py",
    "mist/intelligence/juniper_docs/classify/manual_sorter.py": (
        "mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py"
    ),
    "mist/intelligence/juniper_docs/classify/reclassifier.py": (
        "mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py"
    ),
    "org_data_collector.py": "operations/wan/org_data_collector.py",
    "wan_hub_group_manager.py": "operations/wan/wan_hub_group_manager.py",
    "wan_vpn_builder.py": "operations/wan/wan_vpn_builder.py",
}  # Cover every moved direct source module.
CANONICAL_ROOTS = {group.split("/")[0] for group in PACKAGE_GROUPS} | {
    Path(path).parts[0] for path in MODULE_PATHS.values()
}  # Name every domain root that the move created, so a moved baseline maps to itself.
INTENTIONAL_SYMBOL_REMOVALS: dict[str, set[str]] = {
    # Issues #3334 and #3338 replace the invalid site fingerprint path with the
    # organization path. The site fallback import and its status constant are
    # removed on purpose, and the matching unit tests are removed in the same change.
    "src/mist/intelligence/reports/client_fingerprint_census/client.py": {"_HTTP_NOT_FOUND", "insights"},
}  # Record each reviewed module-level removal, so the guard reports only an unapproved loss.


def ensure_origin_main() -> None:
    """Ensure the baseline source ref exists before archive comparisons."""
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
        cwd=REPOSITORY_ROOT,
        check=False,
    )  # Check whether the workflow checkout fetched the required baseline ref.
    if result.returncode == 0:  # The baseline ref is already present.
        return  # Add no fetch, because the required input exists.
    depth_arguments = (
        ["--depth=1"] if repository_is_shallow() else []
    )  # Keep a complete clone complete, because a shallow fetch would hide its shared commit.
    subprocess.run(
        ["git", "fetch", "origin", "main", *depth_arguments],
        cwd=REPOSITORY_ROOT,
        check=True,
    )  # Fetch the baseline when a manual workflow checkout omitted it.


def repository_is_shallow() -> bool:
    """Return whether Git still holds a shallow boundary that can hide the shared commit."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )  # Read the boundary state without failing on an old Git build.
    return result.stdout.strip() == "true"  # Report a boundary only on an explicit positive answer.


def baseline_ref() -> str:
    """Return the merge base of this worktree and the baseline branch.

    Compare against the merge base, so a worktree that trails the baseline
    reports no phantom symbol loss.
    """
    ensure_origin_main()  # Make the baseline ref available before the merge-base read.
    result = merge_base_result()  # Read the common ancestor before changing the shallow checkout.
    if result.returncode == 0:  # An ordinary checkout already holds the shared commit.
        return result.stdout.strip()  # Supply the exact commit that both branches share.
    result, rounds_used, shallow = deepen_until_merge_base(result)  # Grow history until the base is readable.
    if result.returncode != 0:  # The guard cannot compare symbols without the shared commit.
        raise RuntimeError(merge_base_failure_message(rounds_used, shallow))  # Name the real condition.
    return result.stdout.strip()  # Supply the exact commit that both branches share.


def deepen_until_merge_base(
    result: subprocess.CompletedProcess[str],
) -> tuple[subprocess.CompletedProcess[str], int, bool]:
    """Deepen a shallow checkout repeatedly until the shared commit is readable.

    Repeat the fetch, because one fixed step cannot reach a merge base at an arbitrary distance.
    A rebased branch moves its merge base behind the shallow boundary, so a single step fails.
    """
    shallow = repository_is_shallow()  # Read whether more history can still arrive.
    rounds_used = 0  # Count the completed deepen rounds for the operator message.
    while shallow and rounds_used < MERGE_BASE_DEEPEN_ROUNDS:  # Continue while history can still grow.
        rounds_used += 1  # Record the round that is about to run.
        deepen_origin_history(rounds_used == MERGE_BASE_DEEPEN_ROUNDS)  # Read all history on the final round.
        result = merge_base_result()  # Retry after Git adds the missing history.
        if result.returncode == 0:  # The deepened history now holds the shared commit.
            break  # Stop fetching, because the required input has arrived.
        shallow = repository_is_shallow()  # Decide whether another round can add anything.
    return result, rounds_used, shallow  # Report the outcome, the work done, and the boundary state.


def merge_base_failure_message(rounds_used: int, shallow: bool) -> str:
    """Return a failure message that separates unreachable history from a lost symbol.

    Keep the two outcomes distinct, because an operator reads a lost module-level symbol as a
    stop-everything event, and a short checkout is only a missing input.
    """
    scope = (
        " The guard compared 0 modules and 0 package-data files, because it reads the merge base first."
        " This is a Git history condition, not a lost module-level symbol."
    )  # Report the measured scope and refuse the symbol-loss reading.
    if shallow:  # Git still holds a boundary, so the history is incomplete.
        return (
            "Cannot reach a merge base between HEAD and origin/main."
            f" The guard deepened the shallow checkout {rounds_used} time(s),"
            " and the shared commit stays outside the fetched history."
            f"{scope}"
            " Check out the complete history, for example with fetch-depth: 0, and run the guard again."
        )  # Name the checkout-depth condition and its remedy.
    return (
        "No merge base exists between HEAD and origin/main."
        f" The guard read the complete history after {rounds_used} deepening round(s),"
        " so these two refs hold no shared commit."
        f"{scope}"
        " Fetch origin/main from this same repository and run the guard again."
    )  # Name the unrelated-history condition and its remedy.


def merge_base_result() -> subprocess.CompletedProcess[str]:
    """Return Git's merge-base result without hiding the no-common-ancestor case."""
    return subprocess.run(
        ["git", "merge-base", "HEAD", "refs/remotes/origin/main"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )  # Preserve the return code so a shallow history can be deepened.


def deepen_origin_history(unshallow: bool = False) -> None:
    """Deepen the current commit and main ref so a shallow checkout can find its merge base.

    Read the complete history on the final round, because a bounded step cannot reach a merge
    base at an arbitrary distance.
    """
    head_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()  # Identify the checked-out commit without relying on a local branch name.
    depth_argument = (
        "--unshallow" if unshallow else f"--deepen={MERGE_BASE_DEEPEN}"
    )  # Escalate to the complete history only after the bounded steps fail.
    result = subprocess.run(
        [
            "git",
            "fetch",
            depth_argument,
            "origin",
            head_commit,
            "+refs/heads/main:refs/remotes/origin/main",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )  # Fetch only the checked-out commit and the required baseline branch.
    if result.returncode != 0:  # A failed fetch cannot support a safe symbol comparison.
        raise RuntimeError(
            f"Cannot deepen required Git history. Fetch exited with code {result.returncode}."
            " This is a Git history condition, not a lost module-level symbol."
        )  # Stop with an explicit required-input failure.


def read_archived_module(archive: tarfile.TarFile, member: tarfile.TarInfo) -> str:
    """Read one required module from the baseline archive or fail with its path."""
    extracted = archive.extractfile(member)  # Read the required archived module.
    if extracted is None:  # A missing member means the archive input is incomplete.
        raise AssertionError(f"Cannot read archived module {member.name}")  # Fail with the required path.
    return extracted.read().decode("utf-8")  # Return source text for the module symbol check.


def trailing_commit_count(baseline: str) -> int:
    """Return the count of baseline commits that this worktree does not hold."""
    result = subprocess.run(
        ["git", "rev-list", "--count", f"{baseline}..refs/remotes/origin/main"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )  # Measure the distance between the merge base and the baseline tip.
    return int(result.stdout.strip())  # Supply the measured commit count.


def trailing_notice(behind_count: int) -> str:
    """Return the operator message for a worktree that trails the baseline."""
    if behind_count <= 0:  # The worktree holds every baseline commit.
        return ""  # Add no message, because no action is needed.
    return (
        f" This worktree trails origin/main by {behind_count} commit(s)."
        " The guard compared against the merge base."
        " Rebase onto origin/main to compare against the current baseline."
    )  # Name the condition and the remedy, so the reader does not read a phantom loss.


def path_map() -> dict[str, str]:
    """Return every old and new source-relative path."""  # Build one canonical mapping for archived modules.
    mapping = dict(MODULE_PATHS)  # Start with direct module moves.
    for group, packages in PACKAGE_GROUPS.items():  # Expand each package group.
        for package in packages:  # Map each old direct package.
            mapping[package] = f"{group}/{package}"  # Keep the existing package name at the final level.
    return mapping  # Supply the complete move map.


def current_path(old_path: str) -> Path:
    """Return the current path for one archived source file.

    Resolve the moved module without a compatibility wrapper.
    """
    relative_path = Path(old_path).relative_to("src")  # Remove the common source root.
    mapped_path = path_map().get(relative_path.as_posix())  # Read an explicit nested or direct module move.
    if mapped_path is not None:  # An exact move must override the canonical-root shortcut.
        return SOURCE_ROOT / mapped_path  # Resolve the module at its approved canonical destination.
    first_part = relative_path.parts[0]  # Read the old direct package or module name.
    if first_part in CANONICAL_ROOTS:  # The baseline already holds the moved layout.
        return SOURCE_ROOT / relative_path  # Compare the module against itself at the same path.
    new_first_part = path_map()[first_part]  # Select its canonical domain path.
    remaining_parts = relative_path.parts[1:]  # Preserve the module path inside the moved package.
    return SOURCE_ROOT / new_first_part / Path(*remaining_parts)  # Build the canonical current module path.


def assigned_names(target: ast.expr) -> set[str]:
    """Return each name assigned by one module-level target.

    Include tuple assignments in the public symbol comparison.
    """
    if isinstance(target, ast.Name):  # Read a direct module-level assignment.
        return {target.id}  # Preserve the assigned symbol.
    if isinstance(target, (ast.Tuple, ast.List)):  # Read a destructuring assignment.
        return {name for item in target.elts for name in assigned_names(item)}  # Flatten each assigned child name.
    return set()  # Ignore attributes and subscripts that do not add module symbols.


def module_symbols(source: str, filename: str) -> set[str]:
    """Return module-level names from one Python source string.

    Compare definitions, assignments, and imported exports.
    """
    symbols: set[str] = set()  # Collect each module-level name once.
    for node in ast.parse(source, filename=filename).body:  # Inspect only direct module statements.
        if isinstance(
            node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):  # Read declared callables and classes.
            symbols.add(node.name)  # Preserve the declared public or private name.
        elif isinstance(node, ast.Assign):  # Read direct module assignments.
            symbols.update(
                name for target in node.targets for name in assigned_names(target)
            )  # Add every assigned name.
        elif isinstance(node, ast.AnnAssign):  # Read annotated module assignments.
            symbols.update(assigned_names(node.target))  # Add the annotated name.
        elif isinstance(node, (ast.Import, ast.ImportFrom)):  # Read names re-exported through imports.
            symbols.update(
                alias.asname or alias.name.split(".")[0] for alias in node.names if alias.name != "*"
            )  # Add imported names.
    return symbols  # Return the complete module-level symbol set.


def test_moved_modules_lose_no_module_level_symbol() -> None:
    """Require every moved module to preserve its module-level names.

    Replace the path-limited symbol-diff check for renamed files.
    """
    baseline = baseline_ref()  # Read the shared commit instead of the moving baseline tip.
    notice = trailing_notice(trailing_commit_count(baseline))  # Build the trailing-worktree message.
    command = [
        "git",
        "archive",
        "--format=tar",
        baseline,
        "src",
    ]  # Read all base modules with one bounded Git command.
    archive = subprocess.run(
        command, cwd=REPOSITORY_ROOT, check=True, capture_output=True
    ).stdout  # Fail if Git cannot read the base.
    checked_count = 0  # Count each compared Python module.
    checked_symbol_count = 0  # Count each baseline module-level name checked for loss.
    violations: dict[str, list[str]] = {}  # Collect lost names by old module path.
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source_archive:  # Read the in-memory base source tree.
        for member in source_archive.getmembers():  # Inspect each archived source entry.
            if (
                not member.isfile() or not member.name.endswith(".py") or member.name == "src/__init__.py"
            ):  # Select moved Python modules only.
                continue  # Ignore directories, non-Python files, and the unchanged source initializer.
            new_path = current_path(member.name)  # Resolve the canonical current module path.
            assert (
                new_path.is_file()
            ), f"Missing moved module for {member.name}: {new_path}"  # Reject an incomplete move.
            old_symbols = module_symbols(
                read_archived_module(source_archive, member), member.name
            )  # Read the base module symbol set.
            new_symbols = module_symbols(
                new_path.read_text(encoding="utf-8"), str(new_path)
            )  # Read the current module symbol set.
            checked_symbol_count += len(old_symbols)  # Count each baseline name tested for preservation.
            allowed = INTENTIONAL_SYMBOL_REMOVALS.get(member.name, set())  # Read the reviewed removal list.
            lost_symbols = sorted(old_symbols - new_symbols - allowed)  # Measure only an unapproved removal.
            if lost_symbols:  # Record each module that lost a name.
                violations[member.name] = lost_symbols  # Keep exact names for repair evidence.
            checked_count += 1  # Record one complete module comparison.
    # State the measured scope on every run, so a passing run still reports its coverage.
    print(
        f"Checked {checked_count} moved modules and {checked_symbol_count} baseline symbols "
        f"against {baseline}.{notice}"
    )
    # Report the measured scope, the failures, and the trailing remedy.
    message = (
        f"Checked {checked_count} moved modules and {checked_symbol_count} baseline symbols "
        f"against {baseline}. Lost symbols: {violations}.{notice}"
    )
    assert not violations, message  # Fail only on an unapproved module-level removal.


def test_moved_packages_preserve_tracked_data_files() -> None:
    """Require each tracked package-data file to keep its relative package path."""
    baseline = baseline_ref()  # Read the shared commit instead of the moving baseline tip.
    notice = trailing_notice(trailing_commit_count(baseline))  # Build the trailing-worktree message.
    command = [
        "git",
        "ls-tree",
        "-r",
        "--name-only",
        baseline,
        "src",
    ]  # Read the base tracked source file inventory.
    result = subprocess.run(
        command, cwd=REPOSITORY_ROOT, check=True, capture_output=True, text=True
    )  # Fail if Git cannot provide the required base input.
    old_paths = [
        path for path in result.stdout.splitlines() if not path.endswith(".py") and path != "src/__init__.py"
    ]  # Select each tracked non-Python package-data file.
    missing_paths = [
        f"{old_path} -> {current_path(old_path).relative_to(REPOSITORY_ROOT)}"
        for old_path in old_paths
        if not current_path(old_path).is_file()
    ]  # Record each package-data file that did not move with its package.
    checked_count = len(old_paths)  # Report the measured package-data scope.
    # State the measured scope on every run, so a passing run still reports its coverage.
    print(f"Checked {checked_count} package-data files against {baseline}.{notice}")
    # Build failure evidence that names the scope and the trailing remedy.
    message = f"Checked {checked_count} package-data files against {baseline}. Missing: {missing_paths}.{notice}"
    assert not missing_paths, message  # Fail if one tracked asset did not move with its package.


def test_canonical_roots_name_every_domain_root() -> None:
    """Require the canonical root set to name each domain root of the moved layout."""
    expected_roots = {
        "foundation",
        "interfaces",
        "mist",
        "operations",
    }  # Name the four domain roots that the move created.
    assert CANONICAL_ROOTS == expected_roots, f"Checked {len(CANONICAL_ROOTS)} roots: {sorted(CANONICAL_ROOTS)}"


def test_current_path_maps_a_moved_baseline_to_itself() -> None:
    """Require a baseline path that already holds the moved layout to map to the same path."""
    moved_path = current_path("src/foundation/runtime/config.py")  # Read a path in the new layout.
    expected_path = SOURCE_ROOT / "foundation" / "runtime" / "config.py"  # The same path must come back.
    assert moved_path == expected_path, f"Checked 1 moved path. Read {moved_path}."


def test_current_path_still_maps_an_old_flat_package() -> None:
    """Require an old flat package path to keep its canonical domain destination.

    The canonical path guard refuses a legacy source path literal in tracked text.
    Build the legacy path from a variable, so the file text holds no such literal.
    """
    legacy_package = "config"  # Name one package that moved out of the source root.
    old_path = current_path(f"src/{legacy_package}/settings.py")  # Read a path in the pre-move layout.
    expected_path = SOURCE_ROOT / "foundation/runtime/config" / "settings.py"  # The move map must apply.
    assert old_path == expected_path, f"Checked 1 old path. Read {old_path}."


def test_current_path_refuses_an_unknown_package() -> None:
    """Require an unknown package name to fail, so a real loss still breaks the guard."""
    with pytest.raises(KeyError):  # The guard must not accept a name it cannot place.
        current_path("src/unknown_package/file.py")  # Read a package that no map holds.


def test_module_symbols_reports_a_removed_name() -> None:
    """Require the symbol reader to detect one lost module-level name."""
    base_source = "VALUE = 1\n\n\ndef helper() -> None:\n    return None\n"  # Hold two module-level names.
    moved_source = "VALUE = 1\n"  # Drop the helper, so one name is lost.
    base_symbols = module_symbols(base_source, "base.py")  # Read the base names.
    moved_symbols = module_symbols(moved_source, "moved.py")  # Read the reduced names.
    lost_symbols = base_symbols - moved_symbols  # Measure the loss that the guard must report.
    assert lost_symbols == {"helper"}, f"Checked {len(base_symbols)} base symbols. Lost {sorted(lost_symbols)}."


def test_intentional_removals_waive_only_a_listed_name() -> None:
    """Prove the waiver list hides a reviewed removal and keeps an unlisted removal visible."""
    waived_module = "src/mist/intelligence/reports/client_fingerprint_census/client.py"
    allowed = INTENTIONAL_SYMBOL_REMOVALS[waived_module]  # Read the reviewed removal set for that module.
    old_symbols = allowed | {"unapproved"}  # Build a baseline that holds the waived names and one more name.
    new_symbols: set[str] = set()  # Model a module that lost every baseline name.
    lost_symbols = sorted(old_symbols - new_symbols - allowed)  # Apply the same subtraction as the guard.
    assert lost_symbols == ["unapproved"], f"Checked {len(old_symbols)} base symbols. Lost {lost_symbols}."


def test_intentional_removals_use_only_canonical_module_keys() -> None:
    """Require every waiver key to name a canonical domain root under the source tree."""
    bad_keys = [key for key in INTENTIONAL_SYMBOL_REMOVALS if Path(key).parts[1] not in CANONICAL_ROOTS]
    assert not bad_keys, f"Checked {len(INTENTIONAL_SYMBOL_REMOVALS)} waiver keys. Bad keys: {bad_keys}."


def test_trailing_notice_stays_silent_for_a_current_worktree() -> None:
    """Require no operator message when the worktree holds every baseline commit."""
    notice = trailing_notice(0)  # Model a worktree that trails the baseline by zero commits.
    assert notice == "", f"Checked 1 notice for a current worktree. Read {notice!r}."


def test_trailing_notice_names_the_count_and_the_remedy() -> None:
    """Require the operator message to name the trailing count and the rebase remedy."""
    notice = trailing_notice(7)  # Model a worktree that trails the baseline by seven commits.
    assert "7 commit(s)" in notice, f"Checked 1 notice. The count is absent from {notice!r}."
    assert "Rebase onto origin/main" in notice, f"Checked 1 notice. The remedy is absent from {notice!r}."


class FakeGit:
    """Answer the guard's Git calls, so a shallow checkout becomes a deterministic test input.

    Reveal the merge base only after a chosen number of deepen rounds, because the defect under
    test is a guard that gives up after one fixed round.
    """

    def __init__(self, rounds_to_reveal: int, stays_shallow: bool = True) -> None:
        """Record how many deepen rounds reveal the base and whether the checkout stays shallow."""
        self.rounds_to_reveal = rounds_to_reveal  # Hold the round that first exposes the shared commit.
        self.stays_shallow = stays_shallow  # Hold whether Git still reports a shallow boundary.
        self.fetch_commands: list[list[str]] = []  # Record each deepening fetch for assertion.
        self.rounds_done = 0  # Count the deepen rounds that the guard has already run.

    def __call__(self, command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        """Return the Git result that matches one guard command."""
        if command[1] == "show-ref":  # The guard checks for the baseline ref first.
            return subprocess.CompletedProcess(command, 0, "", "")  # Report that origin/main exists.
        if command[1] == "rev-parse" and "--is-shallow-repository" in command:  # The guard reads the boundary.
            shallow_text = "true\n" if self.stays_shallow else "false\n"  # Report the modeled boundary state.
            return subprocess.CompletedProcess(command, 0, shallow_text, "")  # Supply the boundary answer.
        if command[1] == "rev-parse":  # The guard reads the checked-out commit before fetching.
            return subprocess.CompletedProcess(command, 0, "head-sha\n", "")  # Supply a stable head commit.
        if command[1] == "fetch":  # The guard deepens the shallow history.
            self.fetch_commands.append(command)  # Keep the exact fetch argv for assertion.
            self.rounds_done += 1  # Record that one deepen round completed.
            return subprocess.CompletedProcess(command, 0, "", "")  # Report a successful fetch.
        if command[1] == "merge-base":  # The guard reads the shared commit.
            if self.rounds_done >= self.rounds_to_reveal:  # Enough history is now present.
                return subprocess.CompletedProcess(command, 0, "base-sha\n", "")  # Supply the shared commit.
            return subprocess.CompletedProcess(command, 1, "", "")  # Report that the base stays out of reach.
        raise AssertionError(f"Unexpected Git command {command}")  # Fail on an unmodeled guard call.


def test_baseline_ref_deepens_shallow_history(monkeypatch: pytest.MonkeyPatch) -> None:
    """Require a targeted history fetch when a shallow checkout hides the merge base."""
    fake_git = FakeGit(rounds_to_reveal=1)  # Model a base that the first deepen round reveals.
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=fake_git))  # Replace Git with the modeled checkout.

    baseline = baseline_ref()  # Exercise the same retry path used by the guard.

    assert baseline == "base-sha", f"Checked 1 merge base. Read {baseline!r}."
    assert fake_git.fetch_commands[0] == [  # Inspect the required targeted fetch.
        "git",
        "fetch",
        f"--deepen={MERGE_BASE_DEEPEN}",
        "origin",
        "head-sha",
        "+refs/heads/main:refs/remotes/origin/main",
    ], f"Checked 1 history fetch. Read {fake_git.fetch_commands[0]!r}."


def test_baseline_ref_rejects_histories_without_a_common_ancestor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require an explicit failure when a complete history holds no common ancestor."""
    mocked_run = Mock(  # Model the exact Git call order for unrelated repository histories.
        side_effect=[
            subprocess.CompletedProcess([], 0),  # The origin main ref exists.
            subprocess.CompletedProcess([], 1, "", ""),  # Git finds no merge base.
            subprocess.CompletedProcess([], 0, "false\n", ""),  # The checkout already holds all history.
        ]
    )
    monkeypatch.setattr(subprocess, "run", mocked_run)  # Isolate the fail-closed decision from Git state.

    with pytest.raises(RuntimeError, match="No merge base exists"):
        baseline_ref()  # Refuse to compare symbols when the required ancestor is absent.

    assert mocked_run.call_count == 3, f"Checked 3 Git calls. Read {mocked_run.call_count}."


def test_baseline_ref_returns_an_existing_merge_base_without_fetching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require normal histories to use their existing merge base without a fetch."""
    mocked_run = Mock(  # Model an ordinary checkout with visible shared history.
        side_effect=[
            subprocess.CompletedProcess([], 0),  # The origin main ref exists.
            subprocess.CompletedProcess([], 0, "base-sha\n", ""),  # Git finds the merge base.
        ]
    )
    monkeypatch.setattr(subprocess, "run", mocked_run)  # Keep the normal path independent of the host repository.

    baseline = baseline_ref()  # Read the existing common ancestor.

    assert baseline == "base-sha", f"Checked 1 merge base. Read {baseline!r}."
    assert mocked_run.call_count == 2, f"Checked 2 Git calls. Read {mocked_run.call_count}."


def test_baseline_ref_keeps_deepening_until_the_merge_base_is_readable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require more than one deepen round when the shared commit sits beyond the first step."""
    fake_git = FakeGit(rounds_to_reveal=2)  # Model a base that one fixed deepen round cannot reach.
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=fake_git))  # Replace Git with the modeled checkout.

    baseline = baseline_ref()  # Exercise the deepening path that must not stop after one round.

    assert baseline == "base-sha", f"Checked 1 merge base. Read {baseline!r}."
    assert len(fake_git.fetch_commands) == 2, f"Checked {len(fake_git.fetch_commands)} deepening fetches."


def test_baseline_ref_names_the_checkout_depth_when_history_stays_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require an unreachable base to read as a checkout-depth fault, not a lost symbol."""
    fake_git = FakeGit(rounds_to_reveal=99)  # Model history that no bounded deepening can reach.
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=fake_git))  # Replace Git with the modeled checkout.

    with pytest.raises(RuntimeError) as failure:
        baseline_ref()  # Refuse to compare symbols without the shared commit.

    message = str(failure.value)  # Read the operator message for the unreachable condition.
    assert "Cannot reach a merge base" in message, f"Checked 1 message. Read {message!r}."
    assert "not a lost module-level symbol" in message, f"Checked 1 message. Read {message!r}."
    assert "compared 0 modules" in message, f"Checked 1 message. Read {message!r}."
    assert (
        len(fake_git.fetch_commands) == MERGE_BASE_DEEPEN_ROUNDS
    ), f"Checked {len(fake_git.fetch_commands)} deepening fetches."
    assert (
        fake_git.fetch_commands[-1][2] == "--unshallow"
    ), f"Checked the final fetch. Read {fake_git.fetch_commands[-1]!r}."


def test_baseline_ref_separates_unrelated_history_from_a_lost_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require a complete history with no shared commit to read differently from a lost symbol."""
    fake_git = FakeGit(rounds_to_reveal=99, stays_shallow=False)  # Model a complete, unrelated history.
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=fake_git))  # Replace Git with the modeled checkout.

    with pytest.raises(RuntimeError) as failure:
        baseline_ref()  # Refuse to compare symbols between unrelated histories.

    message = str(failure.value)  # Read the operator message for the unrelated-history condition.
    assert "No merge base exists" in message, f"Checked 1 message. Read {message!r}."
    assert "not a lost module-level symbol" in message, f"Checked 1 message. Read {message!r}."
    assert not fake_git.fetch_commands, f"Checked {len(fake_git.fetch_commands)} fetches on a complete history."


def test_ensure_origin_main_keeps_a_complete_clone_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    """Require a complete clone to fetch the baseline without a shallow boundary.

    A depth-limited fetch into a complete clone would hide the shared commit that the guard reads.
    """
    mocked_run = Mock(  # Model a complete clone whose baseline ref is absent.
        side_effect=[
            subprocess.CompletedProcess([], 1),  # The origin main ref is absent.
            subprocess.CompletedProcess([], 0, "false\n", ""),  # The clone holds all history.
            subprocess.CompletedProcess([], 0, "", ""),  # The baseline fetch succeeds.
        ]
    )
    monkeypatch.setattr(subprocess, "run", mocked_run)  # Replace Git so the fetch argv stays readable.

    ensure_origin_main()  # Exercise the baseline fetch on a complete clone.

    fetch_command = mocked_run.call_args_list[2].args[0]  # Read the exact baseline fetch argv.
    assert fetch_command == [
        "git",
        "fetch",
        "origin",
        "main",
    ], f"Checked 1 baseline fetch. Read {fetch_command!r}."


def test_ensure_origin_main_keeps_a_shallow_checkout_shallow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Require a shallow checkout to fetch the baseline cheaply, because deepening follows later."""
    mocked_run = Mock(  # Model a shallow checkout whose baseline ref is absent.
        side_effect=[
            subprocess.CompletedProcess([], 1),  # The origin main ref is absent.
            subprocess.CompletedProcess([], 0, "true\n", ""),  # The checkout holds a shallow boundary.
            subprocess.CompletedProcess([], 0, "", ""),  # The baseline fetch succeeds.
        ]
    )
    monkeypatch.setattr(subprocess, "run", mocked_run)  # Replace Git so the fetch argv stays readable.

    ensure_origin_main()  # Exercise the baseline fetch on a shallow checkout.

    fetch_command = mocked_run.call_args_list[2].args[0]  # Read the exact baseline fetch argv.
    assert "--depth=1" in fetch_command, f"Checked 1 baseline fetch. Read {fetch_command!r}."


def test_read_archived_module_rejects_unreadable_required_input() -> None:
    """Require an explicit failure when Git archive cannot read a tracked module."""
    archive = Mock(spec=tarfile.TarFile)  # Model the required archive input.
    member = Mock(spec=tarfile.TarInfo)  # Model one required Python module.
    member.name = "src/example.py"  # Name the unreadable required module.
    archive.extractfile.return_value = None  # Report that Git archive cannot read this module.

    with pytest.raises(AssertionError, match="Cannot read archived module src/example.py"):
        read_archived_module(archive, member)  # Refuse to treat missing source as a successful comparison.
