### Fixed

- Fixed two glyph defects in `scripts/pdf_to_markdown.py` for issue #2911. An audit of 1,382
  converted documents found both.
- The reader writes the replacement mark when a glyph carries no mapping. The rule set did not
  remove that mark, so 7 documents carried it into the body text. One carried it 545 times. The
  rule now removes it.
- The front matter wrote each metadata value without the glyph rules, so 107 documents held a
  curly quotation mark in a title or a subject. The front matter now applies the same rules as
  the body.
