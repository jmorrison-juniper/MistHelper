### Juniper documentation corpus harvester

- **Added**: A new package `src/juniper_docs/` downloads the United States and
  English Juniper documentation set. The harvester reads the sitemap index and
  builds a document list. It keeps the newest release note in each train. It
  finds one companion PDF for each document root and downloads each PDF. It
  sorts each file into a category from the slug. Many documents match no slug
  keyword. For each such document, the harvester reads a small PDF text sample
  in memory. It makes a sub-category from the content signals. It then discards
  the text. The run stops and starts again with no loss. The run stays polite,
  and one bad document does not stop it. The harvester writes a folder tree, a
  manifest, and a summary. Issue #3081.
- **Changed**: The classes `JvdCatalogClient`, `JvdPdfResolver`, and
  `JvdDownloader` move from `scripts/crawl_jvd.py` into
  `src/juniper_docs/acquire/`. The class `ReleaseNoteSelector` moves from
  `scripts/jvd_doc_selector.py` into `src/juniper_docs/discovery/`. The script
  `scripts/crawl_jvd.py` imports the moved classes directly. It keeps no stub
  and no wrapper. Issue #3081.
- **Security**: The harvester prefers to verify the certificate through the
  Zscaler root CA in the repository. The unverified mode is a fallback that the
  operator selects. That mode carries one `# nosec B323` mark with a reason.
  The content classifier keeps the sample text in memory only. It writes no
  body text to the store, to the manifest, or to a file on disk. Issue #3081.
