### Fixed

- The PDF converter now turns a control byte at the start of a line into a
  Markdown list item. A subset font can map its bullet glyph to a byte such as
  0x19. The byte then reached the Markdown file, and the list lost its mark. The
  converter removes the byte and writes the list item. Three tests prove that no
  control byte survives a line. See issue #2988.
