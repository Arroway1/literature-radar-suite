---
name: zotero-literature-visualizer
description: Build evidence-aware bilingual literature reviews and interactive dashboards from a local Zotero library or a new topic search. Use for Zotero PDF analysis, paper classification, bilingual research cards, journal-quality verification, citation networks, reading-state dashboards, or Zotero write-back.
---

# Zotero Literature Visualizer

## Purpose

Turn either a local Zotero library or a research topic into a reproducible literature workspace containing normalized metadata, evidence-aware paper notes, a bilingual synthesis, and an offline interactive dashboard.

Bundled scripts perform deterministic collection, Zotero snapshot reading, metadata normalization, dashboard rendering, citation-network enrichment, and optional Zotero API writes. The agent remains responsible for scholarly judgment: relevance screening, evidence verification, full-text interpretation, taxonomy design, and paper-specific bilingual summaries.

## Choose the workflow

| User intent | Workflow | Read first |
|---|---|---|
| Analyze an existing Zotero library | Local Zotero mode | `references/zotero-workflows.md` |
| Add papers, tags, notes, or reading state to Zotero | Zotero API/write-back mode | `references/zotero-workflows.md` |
| Search and review a new topic | Discovery mode | `references/discovery-workflow.md` |
| Verify Impact Factor or CAS partition claims | Quality evidence | `references/quality-and-evidence.md` |
| Build or refine the interactive dashboard | Dashboard mode | `references/dashboard-workflow.md` and `references/dashboard-spec.md` |

Do not combine modes automatically. In particular, do not apply the discovery workflow's journal or date defaults to a user's existing Zotero library unless requested.

## Non-negotiable rules

### Privacy and portability

- Never place names, email addresses, institutional accounts, API keys, cookies, browser profiles, Zotero databases, PDFs, or local absolute paths inside this skill or a shareable archive.
- Keep run data outside the skill directory. Treat `examples/demo-review` as synthetic demonstration data only.
- Read Zotero through a temporary SQLite snapshot. Never edit `zotero.sqlite` directly.
- Read API keys only from `ZOTERO_API_KEY` or a user-supplied file outside the skill directory. Never print or commit them.
- Do not copy or upload a user's Zotero PDFs unless the user explicitly requests an authorized import or upload workflow.

### Evidence integrity

- Never invent bibliographic fields, Impact Factors, CAS partitions, findings, methods, datasets, limitations, or citations.
- Distinguish `full_text`, `abstract_only`, and `metadata_only` evidence states.
- For a paper with a readable local PDF, derive the detailed card from the full text.
- Without a readable PDF, summarize only the abstract and label the evidence level clearly.
- If neither PDF text nor abstract is available, provide metadata only and state that no substantive summary was possible.
- Do not present search snippets, inferred labels, or generic templates as paper findings.

### Access and selection

- Relevance and quality determine selection; open-access status must not affect ranking.
- Analyze PDFs already available locally to the user. This skill does not claim to download subscription PDFs or control authenticated browser sessions.
- Verify journal metrics from an official journal, publisher, Clarivate, or CAS source before displaying them as official.

## Common output contract

Use a run directory outside the skill, normally `<workspace>/literature-reviews/<topic-slug>/`.

Expected core files:

- `metadata/papers.json` and `metadata/papers.csv`: normalized paper records.
- `texts/`: extracted PDF text when locally available.
- `review-bilingual.md`: Chinese-English synthesis grounded in the available evidence.
- `relationship-map.md`: theme-method relationships and research gaps.
- `dashboard-spec.json`: editable bilingual taxonomy and paper-card semantics.
- `<dashboard-name>.html`: offline interactive dashboard.

Optional files include `metadata/citation-network.json`, `metadata/journal-if-evidence.csv`, `metadata/papers-to-zotero.json`, `update-digest.md`, and Zotero write-back logs.

## Paper-card contract

Each card should be paper-specific and bilingual. Include only claims supported by the available evidence:

1. Research question or purpose / 研究问题或目的
2. Method and study design / 方法与研究设计
3. Data, sample, case, or setting / 数据、样本、案例或场景
4. Main findings / 主要发现
5. Limitations / 局限
6. Relevance to the review / 与综述主题的关系
7. Evidence level / 证据层级

Do not mechanically translate the English abstract into every field. With a PDF, inspect the abstract, methods, results, discussion, and conclusion; with abstract-only evidence, use cautious language such as “the abstract reports”.

## Minimal command patterns

Resolve `<python>` to a real Python 3.10+ interpreter and `<skill-dir>` to this skill directory.

### Local Zotero library

```powershell
& '<python>' '<skill-dir>\scripts\systematic_literature_review.py' zotero-import `
  --output-dir '<workspace>\literature-reviews\zotero-library' `
  --topic 'My Zotero Library' `
  --dashboard-name 'zotero-literature-dashboard'
```

Omit `--limit` for a final full-library run. Use `--zotero-dir` only when auto-discovery or `ZOTERO_DATA_DIR` does not locate the library.

### Topic discovery

```powershell
& '<python>' '<skill-dir>\scripts\systematic_literature_review.py' init-config `
  --topic '<topic>' --years 1 --min-if 5 `
  --output '<run-dir>\review-config.json'

& '<python>' '<skill-dir>\scripts\systematic_literature_review.py' collect `
  --config '<run-dir>\review-config.json' `
  --output-dir '<run-dir>' --max-results 120
```

Verify journal evidence before finalizing. See `references/discovery-workflow.md`.

### Dashboard

```powershell
& '<python>' '<skill-dir>\scripts\build_literature_dashboard.py' init-spec `
  --papers '<run-dir>\metadata\papers.json' `
  --output '<run-dir>\dashboard-spec.json'

& '<python>' '<skill-dir>\scripts\build_literature_dashboard.py' build `
  --papers '<run-dir>\metadata\papers.json' `
  --spec '<run-dir>\dashboard-spec.json' `
  --output-dir '<run-dir>' --dashboard-name 'literature-dashboard'
```

Use `--inline` for a single-file dashboard. Large libraries automatically use the scalable layout.

## Completion checks

Before reporting completion:

- Confirm the intended library or search scope and final paper count.
- Spot-check titles, DOI values, authors, years, and resolved PDF paths.
- Confirm each detailed card's evidence level matches its source.
- Confirm Chinese and English content is meaningful, not duplicated placeholder text.
- Open the dashboard and test search, filters, paper details, PDF/Zotero links, reading status, stars, and notes.
- Verify no mojibake, broken assets, personal paths, credentials, or user data entered the skill directory.
- For Zotero writes, run a dry-run first and retain the write log.

## Bundled resources

- `scripts/systematic_literature_review.py`: topic discovery, Zotero snapshot import, metadata normalization, queues, and exports.
- `scripts/build_literature_dashboard.py`: dashboard spec creation and rendering.
- `scripts/large_library_dashboard.py`: scalable layout for large libraries.
- `scripts/dashboard_common.py`: shared dashboard UI, bilingual controls, reading state, stars, notes, and exports.
- `scripts/citation_network.py`: OpenAlex-based in-collection citation enrichment.
- `scripts/zotero_api_import.py`: Zotero Web API import and dashboard write-back.
- `scripts/zotero_link_items.py`: local DOI/title matching to Zotero item keys.
- `scripts/quick_validate.py`: offline portability and smoke validation.
- `references/reporting-template.md`: final reporting structure.
- `examples/demo-review/`: synthetic sample data; never cite it as real research.

## Validate this skill

```powershell
& '<python>' '<skill-dir>\scripts\quick_validate.py' '<skill-dir>'
```

Run this before creating a release archive.

<!-- //============XJQ(本次修改：在上游 v2 工作流上保留 MRI 专题、中文翻译、每刊限额和授权浏览器扩展）====================// -->

## MRI 专题与本地兼容扩展

### MRI 期刊来源注册表

当主题属于 MRI、MR imaging 或 magnetic resonance 时，可在 discovery 配置中补充以下期刊来源。`magnetic medicine` 统一规范为 *Magnetic Resonance in Medicine*（MRM），不作为独立期刊：

- Magnetic Resonance in Medicine (MRM)：ISSN 1522-2594，Wiley
- NeuroImage：ISSN 1053-8119（linking ISSN 1095-9572），Elsevier
- IEEE Transactions on Medical Imaging (TMI)：ISSN 0278-0062，IEEE
- Medical Image Analysis (MIA)：ISSN 1361-8415，Elsevier
- Radiology：ISSN 0033-8419（online ISSN 1527-1315），RSNA
- Medical Physics：ISSN 0094-2405（online ISSN 2473-4209），Wiley
- npj Digital Medicine：ISSN 2398-6352，Nature Portfolio

这些是补充检索路线，不等同于 Impact Factor 通过。每条记录仍须通过日期、MRI 语境和证据层级筛选；只有官方期刊或出版社页面才能作为正式期刊指标证据。

### MRI 语境与证据边界

检索 MRI 相关主题时，标题、摘要或开放元数据至少要明确出现 MRI、MR imaging、magnetic resonance 或具体 MRI 序列/成像语境；仅有泛医学 AI、超声或 CT 语境的记录不得因关键词偶合纳入。只依据标题、摘要和开放元数据总结时，必须标记 `abstract_only` 或 `metadata_only`；没有摘要的记录要明确写“仅依据题目判断，未推断方法或结果”。预印本必须标记“未同行评审”。

### ZH 中文翻译闸门

每个双语 dashboard 的 `details[*]` 中，`zh` 必须是实际中文表述，不能把英文标题或英文摘要原样放在 ZH 标签下；原始证据保留在 `en`。完成语义卡片后运行：

```powershell
& '<python>' '<skill-dir>\scripts\translate_dashboard_zh.py' `
  --papers '<run-dir>\metadata\papers.json' `
  --spec '<run-dir>\dashboard-spec.json' `
  --cache '<run-dir>\metadata\zh-translation-cache.json'
```

该脚本只使用标题、摘要和开放元数据，不读取 PDF、账号、密码或 Cookie；翻译接口失败时写入中文-only fallback，同时保留 EN。交付前检查每个 ZH 字段包含中文字符，且未逐字复制英文证据；没有摘要的记录必须说明“仅依据题目判断，未推断方法或结果”。

### 每刊最多 10 篇

如果用户指定每个期刊的文献上限，在日期/MRI 语境筛选和 DOI/标题去重之后、综述和 dashboard 生成之前执行确定性限额。默认上限为 10，并写入运行配置或运行日志：

```powershell
& '<python>' '<skill-dir>\scripts\cap_journal_papers.py' `
  --input '<run-dir>\metadata\all-candidates.json' `
  --output '<run-dir>\metadata\papers.json' `
  --summary '<run-dir>\metadata\journal-cap-summary.json' `
  --max-per-journal 10
```

脚本按已有正 rank 保留顺序；无 rank 时以日期、相关性、被引数、标题和 DOI 做稳定排序，并输出每刊 before/after/removed。重建 dashboard 时按 DOI，或无 DOI 时按规范化标题+第一作者，重新映射详情和分类，不能因为 rank 变化把译文配到另一篇论文。

### 授权浏览器全文路线（可选）

对用户明确要求且已有合法学校/图书馆/出版社访问权限的论文，可使用套件保留的 `scripts/browser_pdf_downloader.py`：先打开官方文章页，再点击可见的 `View PDF`/`Download PDF`，只保存浏览器显示流程产生的 PDF。禁止构造隐藏 PDF URL、绕过付费墙、自动 CAPTCHA、读取或保存密码/Cookie；无法自动保存时请用户手动点击保存后再导入。不得在没有实际 PDF 或全文页面证据时声称 `full_text`。

### ScienceDirect 可选桥接

若另外安装了 `sciencedirect-live-session-fetcher`，仅对 Elsevier/ScienceDirect 记录在用户确认授权浏览器会话后使用；`scripts/sciencedirect_fetcher_bridge.py` 只负责准备输入 CSV 和导入结果，不替代本 Skill 的筛选、证据和 PDF 校验。导入前检查 `%PDF-` 文件头和 DOI/题目匹配，失败行记录在结果 CSV；没有该依赖时使用 `browser_pdf_downloader.py` 或可见手动保存 fallback。

### 官方期刊质量证据

用户要求 Impact Factor 或 CAS 分区时，只接受期刊官网、出版社页面，或由期刊/出版社明确链接的 Clarivate/CAS 页面；OpenAlex、SJR、CiteScore、ResearchGate、搜索摘要和第三方期刊榜单不能作为正式证据。若官方页面没有清晰数值，记录到 `if-verification-needed.md`，不要把未核实指标显示为正式值，并保存 `official_impact_factor`、`official_if_year`、`evidence_url`、`evidence_note`、`verified_date` 和 `verified_by`。

### Dashboard 质量闸门

每篇论文只能有一个主主题和一个主方法；大型 Zotero 库再增加一个 `subtheme`。保持 `review-bilingual.md`、`relationship-map.md` 和 `dashboard-spec.json` 的分类名称一致。卡片应包含研究问题、方法/设计、数据或样本、主要发现、局限、综述相关性和证据层级，并提供官方期刊主页、DOI 与存在时的本地 PDF 入口。未知期刊不要进入正常期刊排名，显示为 `Metadata missing / 元数据缺失` 并写 `metadata-repair.md`。生成 dashboard 后至少测试搜索、主题筛选、详情弹窗、阅读状态、星标、笔记、引用网络和链接。

### 可选辅助 Skill

若当前会话确实安装并暴露了 `literature-survey`、`deep-research` 或其他文献辅助工具，只能把它们作为检索/浏览器准备的辅助层；本 Skill 仍负责 MRI 语境筛选、官方质量证据、元数据规范化、证据层级、双语卡片、关系图和 dashboard。辅助工具不可用时，不得假装已调用；继续使用本 Skill 的公开元数据与授权浏览器流程。

### 本地附加资源

上游 v2 资源（引用网络、增量 NEW 摘要、阅读状态、分享卡和 Zotero 回写）与以下本地扩展并存：

- `scripts/translate_dashboard_zh.py`：逐篇中文翻译和离线安全 fallback；
- `scripts/cap_journal_papers.py`：每刊确定性数量上限；
- `scripts/browser_pdf_downloader.py`：授权 Chrome/Edge 可见 PDF 流程；
- `scripts/sciencedirect_fetcher_bridge.py`：ScienceDirect live-session 输入/结果桥接；
- `scripts/test_translate_dashboard_zh.py`、`scripts/test_cap_journal_papers.py`：本地扩展回归测试。

<!-- //================XJQ(本次修改：在上游 v2 工作流上保留 MRI 专题、中文翻译、每刊限额和授权浏览器扩展 END===============// -->
