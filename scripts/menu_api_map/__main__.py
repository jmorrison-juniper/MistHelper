"""Write the menu API endpoint map: ``python -m scripts.menu_api_map``.

The command reads the source tree, walks each menu handler, and writes the map
pages. The ``--check`` flag writes nothing. It compares the pages on disk with
the pages that the source produces, and it fails when one page differs.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import argparse  # Reads the command line.
import logging  # Records each file action for the operator.
import sys  # Returns the exit code.
import time  # Measures the run time for the performance goal.
from pathlib import Path  # Builds the portable page paths.

from .analysis.reference_data import SDK_INDEX_PATH, CuratedRules, SdkIndex, SdkSourceReader  # The data files.
from .analysis.resolver import TypeResolver  # Finds the class of a receiver.
from .analysis.scanner import ScanCache, ScanTools  # Scans each function one time.
from .analysis.source_index import SourceIndex  # The source tree index.
from .analysis.walker import MenuRegistryReader, MenuWalker  # Walks each menu handler.
from .render.pages import DOCS_FOLDER, WIKI_FOLDER, PageInput, PageSet  # Builds the pages.

LOGGER = logging.getLogger("scripts.menu_api_map")  # The logger of the command.
REPO_ROOT = Path(__file__).resolve().parents[2]  # The folder that holds MistHelper.py.
WIKI_PAGE_PREFIX = (
    "Menu-API-Endpoints"  # The wiki folder holds other pages too, so only this prefix belongs to the map.
)
FIX_COMMAND = "python -m scripts.menu_api_map"  # The command that writes the pages again.


class MapBuilder:
    """Build the walk results of every menu option and every shared helper."""

    def __init__(self, repo_root: Path) -> None:
        """Store the repository folder to read."""
        self.repo_root = repo_root  # The folder that holds MistHelper.py.
        self.walker: MenuWalker | None = None  # The walker of the last build, for --explain.
        self.reader: MenuRegistryReader | None = None  # The menu table reader of the last build.

    def prepare(self) -> tuple[MenuWalker, MenuRegistryReader, SdkIndex, CuratedRules]:
        """Index the source tree and load the data files."""
        index = SourceIndex(self.repo_root).build()  # Parse every source file.
        sdk = SdkIndex.load()  # The vendored SDK index.
        curated = CuratedRules.load()  # The hand-written rules.
        tools = ScanTools(index, TypeResolver(index, curated.generic_names), sdk, curated)  # The shared tables.
        self.walker, self.reader = MenuWalker(tools, ScanCache(tools)), MenuRegistryReader(index)
        return self.walker, self.reader, sdk, curated

    def build(self) -> PageInput:
        """Return the page input: the menu results, the helper results, and the holder files."""
        walker, reader, sdk, curated = self.prepare()  # The walker and the tables.
        LOGGER.info("Walking every menu handler")  # Log before the walk.
        menus = [walker.walk_menu(option) for option in reader.read()]  # One result for each menu option.
        if not menus:  # A guard that reads no menu must fail, not pass.
            raise SystemExit("The menu table holds no menu option, so the map cannot be checked.")
        helpers = walker.walk_helpers()  # One result for each helper that a walk entered.
        LOGGER.debug("Walked %d menu options and %d helpers", len(menus), len(helpers))  # Log the counts.
        holders = {use.holder for result in [*menus, *helpers] for use in result.endpoints if use.holder}
        return PageInput(menus, helpers, self.holder_files(walker, holders), sdk.version)

    @staticmethod
    def holder_files(walker: MenuWalker, holders: set[str]) -> dict[str, str]:
        """Return the repository file of each holder key."""
        index = walker.tools.index  # The source tree index.
        files: dict[str, str] = {}  # Holder key to its file.
        for key in sorted(holders):  # A function or a constant.
            entry = index.functions.get(key) or index.constants.get(key)
            if entry is not None:
                files[key] = entry.module.relative
        return files


class PageFiles:
    """Compare, write, and remove the page files on disk."""

    def __init__(self, repo_root: Path, pages: dict[str, str]) -> None:
        """Store the repository folder and the expected pages."""
        self.repo_root = repo_root  # The folder that holds MistHelper.py.
        self.pages = pages  # Repository path to its expected text.

    def stale(self) -> list[str]:
        """Return each page that is missing or that differs from its expected text."""
        stale: list[str] = []  # The paths that need a write.
        for relative, text in self.pages.items():  # Compare each page.
            path = self.repo_root / relative  # The page file.
            if not path.is_file() or path.read_text(encoding="utf-8") != text:  # Missing or different.
                stale.append(relative)
        return stale

    def orphans(self) -> list[str]:
        """Return each map page on disk that the source no longer produces."""
        docs = sorted((self.repo_root / DOCS_FOLDER).glob("*.md"))  # Every page of the documentation set.
        wiki = sorted((self.repo_root / WIKI_FOLDER).glob(f"{WIKI_PAGE_PREFIX}*.md"))  # The map pages of the wiki.
        found = [path.relative_to(self.repo_root).as_posix() for path in [*docs, *wiki]]  # Repository paths.
        return [relative for relative in found if relative not in self.pages]

    def write(self, relatives: list[str]) -> None:
        """Write the named pages with Unix line ends."""
        for relative in relatives:  # Write each stale page.
            path = self.repo_root / relative  # The page file.
            LOGGER.info("Writing %s", relative)  # Log before the file write.
            path.parent.mkdir(parents=True, exist_ok=True)  # The documentation folder can be new.
            with path.open("w", encoding="utf-8", newline="\n") as handle:  # Unix line ends on every platform.
                handle.write(self.pages[relative])
            LOGGER.debug("Wrote %d characters to %s", len(self.pages[relative]), relative)  # Log the size.

    def remove(self, relatives: list[str]) -> None:
        """Remove the named orphan pages."""
        for relative in relatives:  # Remove each orphan page.
            LOGGER.info("Removing the orphan page %s", relative)  # Log before the file removal.
            (self.repo_root / relative).unlink()
            LOGGER.debug("Removed %s", relative)  # Log after the file removal.


class MenuApiMapCli:
    """Read the command line and run the selected action."""

    @staticmethod
    def parser() -> argparse.ArgumentParser:
        """Return the command line parser."""
        parser = argparse.ArgumentParser(prog="python -m scripts.menu_api_map", description=__doc__.splitlines()[0])
        parser.add_argument("--check", action="store_true", help="Compare the pages and write nothing.")
        parser.add_argument("--refresh-sdk-index", action="store_true", help="Read the installed mistapi again.")
        parser.add_argument("--explain", type=int, metavar="MENU", help="Print the call path of each endpoint.")
        parser.add_argument("--verbose", action="store_true", help="Print the debug log records.")
        return parser

    def run(self, argv: list[str] | None = None) -> int:
        """Run the selected action and return the exit code."""
        args = self.parser().parse_args(argv)  # The command line flags.
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s %(message)s"
        )
        started = time.perf_counter()  # The start of the run, for the performance goal.
        if args.refresh_sdk_index:  # Read the installed mistapi source again.
            return self.refresh_sdk_index()
        if args.explain is not None:  # Print the call paths of one menu option.
            return self.explain(args.explain)
        page_input = MapBuilder(REPO_ROOT).build()  # Walk every menu option.
        files = PageFiles(REPO_ROOT, PageSet(page_input).render())  # The expected pages.
        count = len(page_input.menus)  # The number of menu options that the run checked.
        return self.check(files, count, started) if args.check else self.write(files, count, started)

    @staticmethod
    def check(files: PageFiles, count: int, started: float) -> int:
        """Report each stale page and each orphan page, and return 1 when one exists."""
        stale, orphans = files.stale(), files.orphans()  # The pages that differ, and the pages to remove.
        seconds = time.perf_counter() - started  # The run time.
        if not stale and not orphans:  # Every page matches the source.
            print(f"OK: {len(files.pages)} map pages match the source for {count} menu options ({seconds:.1f} s).")
            return 0
        print(f"FAIL: {len(stale) + len(orphans)} of {len(files.pages)} map pages do not match the source.")
        for relative in stale:  # Name each stale page.
            print(f"  stale: {relative}")
        for relative in orphans:  # Name each orphan page.
            print(f"  orphan: {relative}")
        print(f"Run {FIX_COMMAND} from the repository root, and commit the pages.")
        return 1

    @staticmethod
    def write(files: PageFiles, count: int, started: float) -> int:
        """Write each stale page, remove each orphan page, and report the counts."""
        stale, orphans = files.stale(), files.orphans()  # The pages to write, and the pages to remove.
        files.write(stale)  # Write the pages that differ.
        files.remove(orphans)  # Remove the pages that the source no longer produces.
        seconds = time.perf_counter() - started  # The run time.
        unchanged = len(files.pages) - len(stale)  # The pages that already matched.
        print(f"Wrote {len(stale)} map pages and removed {len(orphans)} for {count} menu options ({seconds:.1f} s).")
        print(f"{unchanged} map pages did not change.")
        return 0

    @staticmethod
    def refresh_sdk_index() -> int:
        """Read the installed mistapi source again, and write the vendored SDK index."""
        rows = SdkSourceReader(SdkSourceReader.installed_dir()).read()  # One row for each SDK function.
        version = SdkSourceReader.installed_version()  # The installed mistapi version.
        LOGGER.info("Writing the SDK index %s", SDK_INDEX_PATH)  # Log before the file write.
        SDK_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)  # The data folder can be new.
        with SDK_INDEX_PATH.open("w", encoding="utf-8", newline="\n") as handle:  # Unix line ends.
            handle.write(SdkIndex(rows, version).render())
        print(f"Wrote the SDK index for mistapi {version} with {len(rows)} functions.")
        return 0

    @staticmethod
    def explain(menu_id: int) -> int:
        """Print the call path from the handler to each endpoint of one menu option."""
        builder = MapBuilder(REPO_ROOT)  # Build the tables once.
        walker, reader, _, _ = builder.prepare()  # The walker and the menu table reader.
        options = {option.menu_id: option for option in reader.read()}  # Menu number to its entry.
        if menu_id not in options:  # An unknown menu number.
            print(f"Menu {menu_id} does not exist in the menu table.")
            return 1
        for line in walker.explain(options[menu_id]):  # One line for each endpoint.
            print(line)
        return 0


if __name__ == "__main__":  # The module runs as a command.
    sys.exit(MenuApiMapCli().run())
