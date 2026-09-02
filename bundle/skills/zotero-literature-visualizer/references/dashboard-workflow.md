# Dashboard workflow

## Build sequence

1. Normalize `metadata/papers.json`.
2. Read the papers and design a bilingual taxonomy.
3. Initialize `dashboard-spec.json`.
4. Replace starter labels and generic notes with evidence-based card content.
5. Optionally generate the citation network.
6. Build the dashboard and inspect it in a browser.

```powershell
& '<python>' '<skill-dir>\scripts\build_literature_dashboard.py' init-spec `
  --papers '<run-dir>\metadata\papers.json' `
  --output '<run-dir>\dashboard-spec.json' `
  --title '<Chinese title> / <English title>'

& '<python>' '<skill-dir>\scripts\build_literature_dashboard.py' build `
  --papers '<run-dir>\metadata\papers.json' `
  --spec '<run-dir>\dashboard-spec.json' `
  --output-dir '<run-dir>' --dashboard-name 'literature-dashboard'
```

Use `--inline` for one standalone HTML file. Read `dashboard-spec.md` before editing the spec.

## Required behavior

The dashboard should provide:

- bilingual Chinese/English/both display modes;
- search, theme, method, year, journal, and evidence filters;
- theme and method summaries plus theme-method relationships;
- paper cards and detailed paper views;
- local PDF and Zotero links when available;
- reading status, stars, and personal notes stored in browser localStorage;
- visible distinction between full-text, abstract-only, and metadata-only cards;
- export tools that do not silently expose local paths or personal notes.

For large libraries, use the scalable layout with grouped navigation and a two-level theme taxonomy. Do not render a dense one-node-per-paper network when aggregation communicates the structure more clearly.

## Citation network

```powershell
& '<python>' '<skill-dir>\scripts\citation_network.py' `
  --papers '<run-dir>\metadata\papers.json'
```

This uses public OpenAlex metadata to find citations within the selected collection. Treat missing edges as incomplete metadata, not proof that no citation exists.

## Incremental refresh

Rebuilding against an existing run may create NEW badges and `update-digest.md`. Preserve browser reading state by keeping stable paper identifiers. If identifiers change, explain that localStorage state may no longer map correctly.

## Browser verification

Open the final HTML and test:

- light/dark and language controls;
- search and every filter;
- paper-modal navigation and close behavior;
- read/reading/unread state, stars, notes, and quick filters;
- CSV/share-card/write-back exports;
- local PDF and Zotero links;
- responsive layout and text encoding.

Spot-check cards against their source evidence, especially those with PDFs.
