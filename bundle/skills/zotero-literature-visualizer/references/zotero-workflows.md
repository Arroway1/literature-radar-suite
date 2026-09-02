# Zotero workflows

## Local direct-import mode

Use this mode when the user already has Zotero items and local PDFs. Prefer direct read over asking for a BibTeX, RIS, CSV, or RDF export.

The importer should:

- Auto-discover the default Zotero data directory or use `ZOTERO_DATA_DIR` / `--zotero-dir`.
- Copy `zotero.sqlite` to a temporary snapshot before reading it.
- Read item metadata, collections, tags, abstracts, and attachment paths without modifying Zotero.
- Include only items whose local PDF attachment resolves to an existing file when the user requests full-text analysis.
- Keep `local_pdf_path` pointed to the original PDF; do not copy or move it.
- Avoid OpenAlex, Crossref, Unpaywall, date limits, and IF filters unless the user asks for enrichment.
- Omit `--limit` for final full-library runs. Use it only for testing or an explicitly limited scope.

Command:

```powershell
& '<python>' '<skill-dir>\scripts\systematic_literature_review.py' zotero-import `
  --output-dir '<run-dir>' `
  --topic '<library title>' `
  --dashboard-name 'zotero-literature-dashboard'
```

Optional controls:

- `--zotero-dir '<path>'`: non-default Zotero data directory.
- `--max-text-chars 80000`: cap extracted text per item.
- `--no-extract-text`: metadata and links only.
- `--limit <n>`: testing or explicit subset only.

After import, compare the included and skipped counts, open sample PDFs, and inspect `metadata/zotero-import-summary.json` and `zotero-skipped.md`.

For more than 100 papers, use the large-library layout with two-level taxonomy, grouped browsing, search, filters, theme-method aggregation, and a separated missing-metadata bucket.

## Link existing dashboard rows to Zotero

If `papers.json` came from another source, use `zotero_link_items.py` to match DOI/title against a read-only Zotero snapshot and fill `zotero_item_key`. Never write the SQLite database.

## Zotero Web API import

Use Web API import only when the user wants new records or attachments written to Zotero. Prefer it over direct SQLite changes.

Credential rules:

- Read the key from `ZOTERO_API_KEY` or `--api-key-file` outside the repository.
- Never echo, log, archive, or commit the key.
- Verify permissions before writing.

```powershell
& '<python>' '<skill-dir>\scripts\zotero_api_import.py' `
  --api-key-file '<key-file>' verify-key
```

Import a manifest:

```powershell
& '<python>' '<skill-dir>\scripts\zotero_api_import.py' `
  --api-key-file '<key-file>' import-manifest `
  --manifest '<run-dir>\metadata\papers-to-zotero.json' `
  --collection '<collection>' --tag 'literature-visualizer' `
  --link-files `
  --output '<run-dir>\metadata\zotero-api-import-log.json'
```

Use `--link-files` for local-only PDFs. Use `--upload-files` only when the user explicitly wants Zotero File Storage uploads and has appropriate storage access. A manifest may contain title, authors, DOI, journal, date/year, abstract, URL, and local PDF path. Existing DOI matches should be skipped by default.

## Dashboard write-back

The dashboard can export `zotero-writeback.json`. Write-back synchronizes namespaced classification tags, reading status, stars, and child notes.

Always dry-run first:

```powershell
& '<python>' '<skill-dir>\scripts\zotero_api_import.py' `
  --api-key-file '<key-file>' write-back `
  --writeback '<writeback.json>' --dry-run
```

Then perform the write and retain the log:

```powershell
& '<python>' '<skill-dir>\scripts\zotero_api_import.py' `
  --api-key-file '<key-file>' write-back `
  --writeback '<writeback.json>' `
  --output '<run-dir>\metadata\zotero-writeback-log.json'
```

Do not claim that browser-local reading state has reached Zotero until the write-back command succeeds.
