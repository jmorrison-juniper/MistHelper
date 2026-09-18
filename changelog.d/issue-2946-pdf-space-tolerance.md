### Fixed

- The PDF converter now keeps the space between two words. The pdfplumber
  default tolerance of 3 points joined adjacent words in a Juniper PDF, so
  `set class` became `setclass`. The converter now passes a tolerance of 1
  point. A joined command reads as correct, and an engineer cannot paste it.
  Two regression tests draw each word at its own position and prove that
  every space survives. See issue #2946.
