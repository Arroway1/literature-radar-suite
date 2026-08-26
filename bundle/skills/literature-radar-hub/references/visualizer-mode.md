# Visualizer mode / 可视化模式

## Routing

- Keyword/date/source request: use `nature-academic-search` multi-source
  discovery, then `zotero-literature-visualizer` for normalization, semantic
  details, review files, and dashboard rendering.
- Local Zotero request: use the Zotero-import route from
  `zotero-literature-visualizer`; include only local-PDF-backed items by
  default, and never edit `zotero.sqlite` directly.
- A source MCP failure is not a reason to stop the whole run. Record the
  provider, status/error, fallback source, and reused snapshot if any.

<!-- //============XJQ(本次修改：补充 Visualizer 模式的依赖预检与 ScienceDirect 可选降级)====================// -->

## Dependency check and full-text route

Run the hub dependency preflight before discovery. `nature-academic-search` and
`zotero-literature-visualizer` are required for this mode. `paper-vault` is
optional and is not needed to build the dashboard. The
`sciencedirect-live-session-fetcher` is also optional and is **not installed in
the current environment**; do not invoke it as if it were available.

If a user explicitly requests ScienceDirect/Elsevier full text and authorizes a
visible browser session, ask whether the missing helper may be installed. If
the user declines or installation is unavailable, use the bundled
`zotero-literature-visualizer/scripts/browser_pdf_downloader.py` workflow. The
fallback is limited to visible, user-authorized browser actions; never use
hidden sessions, stored cookies, unattended login, or paywall bypass.

<!-- //================XJQ(本次修改：补充 Visualizer 模式的依赖预检与 ScienceDirect 可选降级 END===============// -->

## MRI source registry

For MRI/magnetic-resonance scope, the requested Crossref journal routes are:

| Normalized journal | ISSN / publisher |
|---|---|
| Magnetic Resonance in Medicine (MRM) | 1522-2594 / Wiley |
| NeuroImage | 1053-8119 or linking 1095-9572 / Elsevier |
| IEEE Transactions on Medical Imaging (TMI) | 0278-0062 / IEEE |
| Medical Image Analysis (MIA) | 1361-8415 / Elsevier |
| Radiology | 0033-8419 or 1527-1315 / RSNA |
| Medical Physics | 0094-2405 or 2473-4209 / Wiley |
| npj Digital Medicine | 2398-6352 / Nature Portfolio |

Normalize the user phrase “magnetic medicine” to MRM; do not invent a separate
journal. These are discovery routes, not Impact Factor evidence. Keep official
journal links and source IDs in the metadata.

## Cap and Chinese evidence gate

Apply the cap only after date/MRI-context filtering and deduplication:

~~~powershell
& '<python>' '<zotero-literature-visualizer>/scripts/cap_journal_papers.py' `
  --input '<run>/metadata/all-candidates.json' `
  --output '<run>/metadata/papers.json' `
  --summary '<run>/metadata/journal-cap-summary.json' `
  --max-per-journal 10
~~~

The helper retains the existing rank order, writes per-journal before/after
counts, and renumbers the final set. If a dashboard already exists, remap
`details` and `paper_assignments` by DOI; without DOI use normalized title plus
first author. Never attach a translated note to a different paper because its
rank changed.

Translate after semantic details are present:

~~~powershell
& '<python>' '<zotero-literature-visualizer>/scripts/translate_dashboard_zh.py' `
  --papers '<run>/metadata/papers.json' `
  --spec '<run>/dashboard-spec.json' `
  --cache '<run>/metadata/zh-translation-cache.json'
~~~

Assert for every retained paper and each of `topic`, `method`, `data`,
`findings`, `limits`, and `relevance`:

- `zh` contains CJK text and is not the English title/abstract verbatim.
- `en` preserves the original evidence.
- No-abstract records explicitly say title-only and that methods/results were
  not inferred.

## Dashboard outputs

Render with the installed dashboard builder:

~~~powershell
& '<python>' '<zotero-literature-visualizer>/scripts/build_literature_dashboard.py' build `
  --papers '<run>/metadata/papers.json' `
  --spec '<run>/dashboard-spec.json' `
  --output-dir '<run>' `
  --dashboard-name mri-literature-dashboard
~~~

Expected files include `review-cn.md`, `review-bilingual.md`,
`relationship-map.md`, `metadata/papers.json`, `dashboard-spec.json`,
`mri-literature-dashboard.html`, and the data/details JavaScript files. Verify
that paper count, rank continuity, journal cap, CJK ZH fields, DOI links, and
local PDF paths match the retained metadata.
