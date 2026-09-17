### Added

- Added the `hardening-junos` skill for issue #2754. It answers Junos hardening questions from a staged Juniper corpus and names its source. It has five files at 124 KB of a 400 KB limit. It includes 67 controls in eight sections, 181 DISA STIG rules, verification guidance, and corpus procedures.

### Changed

- Changed `scripts/pdf_to_markdown.py` for issue #2754. It uses `pdfplumber` to read PDF files. It detects headings from font size and writes front matter in YAML. It removes a running header. It changes each bullet glyph to a Markdown list item. It runs a worker pool.

### Fixed

- Fixed the heading rule for issue #2754. It now selects the tallest font size that holds at least one tenth of all characters. This reduces false headings in one measured guide from 46.4 percent to 1.7 percent.

