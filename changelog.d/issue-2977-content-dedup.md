### Corpus harvest

- Fixed: the Juniper corpus harvest compares the SHA256 digest of each fetched PDF with the stored files. It keeps one canonical file when the same bytes arrive under another name or category (issue #2977). The harvest does not change existing corpus data.
