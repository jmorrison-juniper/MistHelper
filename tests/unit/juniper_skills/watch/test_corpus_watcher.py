"""Tests for the live Juniper corpus watcher."""

from pathlib import Path  # Use Path to create isolated corpus roots for each test.

from src.juniper_skills.watch import CorpusWatcher, WatcherConfig  # Exercise the production watcher.


class TestCorpusWatcher:
    """Verify quiet-period, hash, part-set, and shutdown behavior."""

    def test_waits_for_partial_write_before_enqueue(self, tmp_path: Path) -> None:
        repo_root = self._repo_root(tmp_path)  # Create a local repository root for the shared database.
        download_root = self._download_root(tmp_path)  # Create local source roots instead of the real corpus.
        watcher = self._watcher(repo_root, download_root)  # Build the watcher with test roots.
        watcher.scan_once()  # Establish an empty baseline before the new file arrives.
        path = download_root / "juniper-harvest-md" / "guides" / "partial.md"  # Select one source Markdown path.
        path.parent.mkdir(parents=True, exist_ok=True)  # Create the document folder for the simulated converter.
        path.write_text("---\nsource_file: guides/partial.pdf\n", encoding="utf-8")  # Write an incomplete document.
        watcher.scan_once()  # Observe the partial file before it is stable.
        path.write_text(self._document("Partial", "guides/partial.pdf"), encoding="utf-8")  # Finish the conversion.
        watcher.scan_once()  # Observe the changed size and reset the quiet-period counter.
        watcher.scan_once()  # Accept the second unchanged sample and enqueue the document.
        assert watcher.stats.files_added == 1  # A new stable file must count as one added file.
        assert watcher.stats.items_enqueued == 1  # The watcher must enqueue the logical document once.

    def test_ignores_touch_without_content_change(self, tmp_path: Path) -> None:
        repo_root = self._repo_root(tmp_path)  # Create a local repository root for the shared database.
        download_root = self._download_root(tmp_path)  # Create local source roots instead of the real corpus.
        path = download_root / "juniper-harvest-md" / "guides" / "touch.md"  # Select one source Markdown path.
        path.parent.mkdir(parents=True, exist_ok=True)  # Create the document folder for the baseline file.
        path.write_text(self._document("Touch", "guides/touch.pdf"), encoding="utf-8")  # Write stable content.
        watcher = self._watcher(repo_root, download_root)  # Build the watcher after the file exists.
        watcher.scan_once()  # Take the first sample, which is not ready yet.
        watcher.scan_once()  # Take the baseline hash without queueing existing content.
        path.touch()  # Change only the timestamp to simulate OneDrive or converter churn.
        watcher.scan_once()  # Observe the timestamp change and reset stability.
        watcher.scan_once()  # Accept the stable touched file and compare the hash.
        assert watcher.stats.files_touched == 1  # The watcher must count the ignored touch.
        assert watcher.stats.items_enqueued == 0  # The queue must not rebuild when content is unchanged.

    def test_part_change_rebuilds_whole_part_set_after_peers_settle(self, tmp_path: Path) -> None:
        repo_root = self._repo_root(tmp_path)  # Create a local repository root for the shared database.
        download_root = self._download_root(tmp_path)  # Create local source roots instead of the real corpus.
        first = download_root / "juniper-harvest-md" / "cli-reference" / "cli-reference.md"  # Create part one.
        second = download_root / "juniper-harvest-md" / "cli-reference" / "cli-reference-2.md"  # Create part two.
        first.parent.mkdir(parents=True, exist_ok=True)  # Create the split document folder.
        first.write_text(self._document("CLI", "cli-reference/cli-reference.pdf"), encoding="utf-8")  # Write part one.
        second.write_text(self._document("CLI", "cli-reference/cli-reference.pdf"), encoding="utf-8")  # Write part two.
        watcher = self._watcher(repo_root, download_root)  # Build the watcher with the completed part set.
        watcher.scan_once()  # Take the first baseline sample for both parts.
        watcher.scan_once()  # Hash both parts without queueing the existing backlog.
        first.write_text(self._document("CLI", "cli-reference/cli-reference.pdf", "new"), encoding="utf-8")  # Change.
        second.write_text(
            "---\nsource_file: cli-reference/cli-reference.pdf\n", encoding="utf-8"
        )  # Start part two rewrite.
        watcher.scan_once()  # Observe both active writes and enqueue nothing.
        watcher.scan_once()  # Part one is stable, but part two now has a stable partial value.
        second.write_text(self._document("CLI", "cli-reference/cli-reference.pdf", "done"), encoding="utf-8")  # Finish.
        watcher.scan_once()  # Observe the completed part two rewrite and reset its quiet-period counter.
        watcher.scan_once()  # Accept the file quiet period and start the whole-set quiet check.
        watcher.scan_once()  # Accept the whole-set quiet period and enqueue the logical document.
        rows = self._work_rows(repo_root)  # Read the shared queue rows that inventory and watcher wrote.
        assert len(rows) == 1  # The whole split PDF must rebuild as one logical document.
        assert watcher.stats.files_changed == 2  # Both rewritten parts became part of the same refresh.
        assert rows[0][1] == "live content changed"  # The queue reason must identify the live change.

    def test_clean_shutdown_returns_without_scanning(self, tmp_path: Path) -> None:
        repo_root = self._repo_root(tmp_path)  # Create a local repository root for the shared database.
        download_root = self._download_root(tmp_path)  # Create local source roots instead of the real corpus.
        watcher = self._watcher(repo_root, download_root)  # Build the watcher service object.
        watcher.stop()  # Request shutdown before the service loop starts.
        stats = watcher.run(1.0)  # Run with a bound duration so the test cannot hang.
        assert stats.scans == 0  # The service must stop cleanly without another scan.

    def _repo_root(self, tmp_path: Path) -> Path:
        repo_root = tmp_path / "repo"  # Keep the test database away from the real repository.
        repo_root.mkdir(parents=True, exist_ok=True)  # Create the repository root for inventory output.
        return repo_root  # Return the root used by WatcherConfig.

    def _download_root(self, tmp_path: Path) -> Path:
        download_root = tmp_path / "downloads"  # Keep source roots away from the real corpus.
        (download_root / "juniper-doc-archives" / "markdown").mkdir(parents=True, exist_ok=True)  # Create root one.
        (download_root / "juniper-doc-archives" / "markdown2").mkdir(parents=True, exist_ok=True)  # Create root two.
        (download_root / "juniper-harvest-md").mkdir(parents=True, exist_ok=True)  # Create the live harvest root.
        return download_root  # Return the root used by InventoryBuilder.

    def _watcher(self, repo_root: Path, download_root: Path) -> CorpusWatcher:
        config = WatcherConfig(repo_root, download_root, 0.01, 100_000)  # Use fast polling for unit tests.
        return CorpusWatcher(config)  # Return a real watcher with isolated roots.

    def _document(self, title: str, source_file: str, marker: str = "base") -> str:
        return "\n".join(
            [
                "---",
                f"title: {title}",
                f"source_file: {source_file}",
                "pages: 2",
                "---",
                f"body {marker}",
                "",
            ]
        )  # Build a minimal converter-like Markdown document.

    def _work_rows(self, repo_root: Path) -> list[tuple[str, str]]:
        import sqlite3  # Import locally because only this assertion reads the database.

        db_path = repo_root / "data" / "juniper_skills" / "factory.db"  # Use the contract database path.
        with sqlite3.connect(db_path) as connection:  # Open a short read transaction for assertions.
            rows = connection.execute("SELECT document_key, reason FROM work_item").fetchall()  # Read queue state.
        return [(str(row[0]), str(row[1])) for row in rows]  # Normalize sqlite rows for simple assertions.
