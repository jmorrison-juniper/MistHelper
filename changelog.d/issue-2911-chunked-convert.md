### Fixed

- Fixed the memory cost of converting a very large PDF for issue #2911.
  `scripts/pdf_to_markdown.py` read a whole document in one pass and held every page until the
  end. An 81 MB guide then reached 22 GB of memory and never finished.
- A PDF above 40 MB now writes one Markdown file for each page range, into a folder named for the
  document. A prototype of the same method converted the same file with 0.43 GB of memory, which
  is about 50 times less.
- The body font size still comes from every page. The first pass reads each page, keeps only a
  size counter, and releases the page. A test proves that a two page sample fails.

### Added

- Added `--pages-per-part` and `--split-above-mb` to `scripts/pdf_to_markdown.py` for issue #2911.
  The defaults are 250 pages for each part and 40 megabytes for the split threshold.
