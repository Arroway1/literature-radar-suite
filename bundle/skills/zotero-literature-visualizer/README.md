# Zotero 文献整理与可视化 Skill

## 中文说明

`zotero-literature-visualizer` 是面向 Codex 的学术文献工作流 skill。它可从研究主题或已有 Zotero 文献库出发，完成文献检索、期刊质量核查、已有本地 PDF 的全文整理、Zotero 条目整理、中英文研究摘要，以及交互式文献 dashboard 的生成。

Dashboard 采用「暖纸色学术编辑部」视觉风格，包含主题分类环图、方法热点、聚合式主题—方法关系流图（丝带宽度代表文献数）、发表时间线、期刊来源（含官方 IF 徽标）、文章卡片与本地 PDF 打开入口，并内置明暗双主题与中/英/双语切换。

### v2 新特性（2026-08）

- **全新视觉**：暖纸色编辑部风格、衬线标题、色盲友好配色（明暗两套色阶自动切换）、更清爽的聚合关系流图。
- **阅读进度追踪**：每篇文献可标记未读/在读/已读、加星标、写个人笔记（保存在本机浏览器 localStorage，重新生成 dashboard 不丢失）；首页显示阅读进度条，可按阅读状态筛选，CSV 导出包含笔记。
- **增量更新 + 周报**：重新构建时自动对比上一次结果，新文献打 NEW 徽标、可一键筛选，并生成可直接转发课题组群的 `update-digest.md` 双语更新摘要。
- **中科院分区徽标**：`papers.json` 填入 `cas_partition`（1-4 区）与 `cas_top` 后，卡片、期刊排行和详情页自动显示分区徽标。
- **引用关系网络**：`citation_network.py` 用 OpenAlex 公开元数据抓取集合内互引关系，dashboard 渲染弧线引用图 + 「核心必读 Top 5」，卡片带被引徽标并支持按被引排序。
- **小红书分享卡**：工具栏「分享卡」按钮一键导出 1080×1440 竖版统计海报（主题环图、高分期刊、阅读进度），适合直接发社交平台。
- **笔记回写 Zotero**：dashboard 导出回写包后，`zotero_api_import.py write-back` 把主题/方法分类、阅读状态、星标写成 Zotero 标签（`SLR:` 命名空间，重复同步不残留），个人笔记写成条目子笔记。
- **单文件分享**：构建时加 `--inline` 参数，生成一个可以直接发给导师/群聊的独立 HTML 文件。
- **快捷键**：`/` 聚焦搜索框；详情弹窗支持 ←/→ 翻页、Esc 关闭。

### 安装

压缩包里的 `zotero-literature-visualizer/` 文件夹就是 skill 本体（含 `SKILL.md`、`scripts/`、`references/`、`examples/`）。

- **Codex**：把 `.zip` 拖入 Codex，或附上文件说"请安装这个 zotero-literature-visualizer skill"；安装后重启 Codex 或刷新 skills 列表。
- **Claude Code**：把 `zotero-literature-visualizer/` 整个文件夹复制到 `$HOME/.claude/skills/`，新开会话即可被自动识别。
- **手动 / 其他 Agent**：任何能读 `SKILL.md` 并执行 Python 脚本的 Agent 都可以用；脚本只依赖 Python 3.10+ 标准库，**读取 PDF 全文时**需要 `pip install pypdf`。

环境要求：Python 3.10+（Windows 上如果 `python` 指向 Microsoft Store 占位符，请改用 `py -3` 或安装的真实 Python）。仪表盘是离线 HTML，不依赖任何前端框架或 CDN。

安装后自检 + 两分钟看到仪表盘效果：

```bash
python zotero-literature-visualizer/scripts/quick_validate.py zotero-literature-visualizer
python zotero-literature-visualizer/scripts/build_literature_dashboard.py build \
  --papers zotero-literature-visualizer/examples/demo-review/metadata/papers.json \
  --spec zotero-literature-visualizer/examples/demo-review/dashboard-spec.json \
  --output-dir zotero-literature-visualizer/examples/demo-review --dashboard-name demo-dashboard --inline --no-snapshot
```

双击打开生成的 `demo-dashboard.html`（合成演示数据），然后用下面的提示词生成你**自己**的仪表盘。

### 使用方式 1：直接整理已有 Zotero 文献库

适用于 Zotero 中已经有论文条目和本地 PDF 的情况。

```text
使用 zotero-literature-visualizer skill，读取我 Zotero 中所有带本地 PDF 的文献，
按主题和方法分类，生成中英文摘要与交互式 dashboard。
```

也可以限制到一个 collection：

```text
使用 zotero-literature-visualizer skill，只整理 Zotero 中“某个文件夹”内带本地 PDF 的文献，
生成交互式 dashboard。
```

Zotero 直读模式会以只读方式读取本地数据库，不移动 PDF，也不会修改原有条目。只有已解析到本地的 PDF 会被纳入全文可视化；没有本地 PDF 的条目会被明确标记为未纳入全文分析。

### 使用方式 2：检索一个新研究方向

```text
使用 zotero-literature-visualizer skill，整理“关键词***”相关的近年高质量论文。
请给出筛选逻辑、期刊质量核查、双语研究摘要和可视化 dashboard。
```

可补充限定条件，例如时间范围、目标数量、主题词、地区或方法：

```text
近 5 年；不限制篇数；重点关注关键词***、研究对象***与研究方法***。
```

默认流程优先关注相关性、研究质量与期刊证据，不会因为论文是否开放获取而改变纳入排序。

### 使用方式 3：把已有论文及 PDF 添加到 Zotero

如果希望把新文献写回 Zotero，可以说：

```text
将已下载的论文加入 Zotero 的“某个文件夹”，并把本地 PDF 作为对应条目的附件。
```

需要通过 Zotero Web API 写入时，请自行在 Zotero 创建仅限个人文库的 API key，并授予需要的 library/write 权限。不要把 API key 放入 README、代码仓库或公开聊天记录。

### 使用方式 4：生成或改进 dashboard

```text
为这个文献库生成 dashboard，并加入：主题分类、方法分布、发表时间线、主题—方法关系图、期刊来源与本地 PDF 链接。
```

如需针对某个文献库做更深入的解释，可继续要求：

```text
请根据 PDF 全文，逐篇补充中文的研究主题、方法、数据或案例、主要结果、局限与研究启示。
```

### 典型输出

运行目录通常包含：

- `metadata/papers.json`：规范化的论文元数据；
- `texts/`：从本地 PDF 提取的文本；
- `review-bilingual.md`：双语综述；
- `relationship-map.md`：主题与方法关系说明；
- `dashboard-spec.json`：可人工调整的分类与卡片语义；
- `literature-dashboard.html`：离线打开的交互式 dashboard。

### 隐私与数据边界

- 不要把姓名、邮箱、学校账号、API key、Cookie、浏览器配置或本地绝对路径写入 skill、README 或公开仓库。
- Zotero 直读模式默认只读取本机数据；不会复制或上传 PDF。
- 下载付费文献时只使用用户已经合法登录的可见浏览器流程。

公开发布前请运行 `scripts/quick_validate.py`，并阅读 [`PRIVACY.md`](PRIVACY.md)。仓库只应包含源码、说明和合成示例，不能包含 Zotero 数据库、PDF、全文提取、个人笔记、浏览器配置或运行输出。

### 许可证

本项目采用 [MIT License](LICENSE)。

---

## English Description

`zotero-literature-visualizer` is a Codex skill for academic literature workflows. Starting from either a research topic or an existing Zotero library, it supports literature discovery, journal-quality checks, analysis of locally available PDFs, Zotero organization, bilingual research summaries, and interactive literature dashboards.

The dashboard uses a warm-paper editorial visual style with theme donuts, method hotspots, an aggregated theme–method flow map (ribbon width = paper count per pair), a publication timeline, journal sources with official IF badges, paper cards, and local PDF launchers — plus built-in light/dark themes and a ZH/EN/bilingual toggle.

### What's new in v2 (2026-08)

- **New look**: warm-paper editorial design, serif display headings, a colorblind-validated palette with separate light/dark color steps, and a much cleaner aggregated flow map.
- **Reading tracker**: mark each paper unread/reading/read, star it, and write personal notes (stored in the local browser via localStorage, surviving dashboard rebuilds); a reading-progress bar in the hero, a reading-status filter, and notes columns in the CSV export.
- **Delta updates + digest**: every rebuild compares against the previous one — new papers get NEW badges and a one-click filter, and a bilingual `update-digest.md` is written, ready to paste into a group chat.
- **CAS partition badges**: fill `cas_partition` (tiers 1-4) and `cas_top` in `papers.json` and 中科院分区 badges appear on cards, journal rankings, and the detail modal.
- **Citation network**: `citation_network.py` pulls in-collection citation edges from public OpenAlex metadata; the dashboard renders an arc diagram plus a "core must-reads Top 5" list, with cited badges and a cited sort.
- **Share-card poster**: a toolbar button exports a 1080×1440 vertical stats poster (theme donut, top journals, reading progress) ready for social media.
- **Zotero write-back**: export a write-back package from the dashboard, then `zotero_api_import.py write-back` syncs themes/methods, reading status, and stars into namespaced Zotero tags (`SLR:` — replaced cleanly on re-sync) and personal notes into child notes.
- **Single-file sharing**: pass `--inline` at build time to produce one standalone HTML file you can send to a supervisor or group chat.
- **Shortcuts**: `/` focuses search; the detail modal supports ←/→ paging and Esc to close.

### Installation

The `zotero-literature-visualizer/` folder inside the zip is the skill itself (`SKILL.md`, `scripts/`, `references/`, `examples/`).

- **Codex**: drag the `.zip` into Codex, or attach it and say "Install this zotero-literature-visualizer skill"; restart Codex or refresh the skills list.
- **Claude Code**: copy the whole `zotero-literature-visualizer/` folder into `$HOME/.claude/skills/`; it is picked up in the next session.
- **Manual / other agents**: any agent that can read `SKILL.md` and run Python scripts can use it. Scripts need only the Python 3.10+ standard library; `pip install pypdf` is required only for full-text PDF reading.

Requirements: Python 3.10+ (on Windows, if `python` is the Microsoft Store placeholder, use `py -3` or a real install). The dashboard is offline HTML with no frameworks or CDNs.

Self-check plus a two-minute preview of the dashboard:

```bash
python zotero-literature-visualizer/scripts/quick_validate.py zotero-literature-visualizer
python zotero-literature-visualizer/scripts/build_literature_dashboard.py build \
  --papers zotero-literature-visualizer/examples/demo-review/metadata/papers.json \
  --spec zotero-literature-visualizer/examples/demo-review/dashboard-spec.json \
  --output-dir zotero-literature-visualizer/examples/demo-review --dashboard-name demo-dashboard --inline --no-snapshot
```

Open the generated `demo-dashboard.html` (synthetic data), then use the prompts below to build your **own** dashboard.

### Workflow 1: Read an existing Zotero library

Use this when Zotero already contains article records and local PDF files.

```text
Use the zotero-literature-visualizer skill to read all Zotero items with local PDFs,
classify them by theme and method, and generate bilingual summaries and an interactive dashboard.
```

To focus on one collection:

```text
Use the zotero-literature-visualizer skill to analyze only the local-PDF items in my Zotero collection named “Collection name” and generate an interactive dashboard.
```

Zotero direct-import mode reads a local database snapshot without moving PDFs or modifying existing Zotero records. Only records with resolved local PDFs are included in full-text visualization; records without local PDFs are kept out of full-text analysis.

### Workflow 2: Search a new research topic

```text
Use the zotero-literature-visualizer skill to review recent high-quality literature on
“keyword ***”.
Provide the screening logic, journal-quality checks, bilingual research notes, and a dashboard.
```

You can add constraints such as year range, target count, geographic scope, keywords, or methods:

```text
Last 5 years; no paper limit; focus on keyword ***, research context ***, and research method ***.
```

The workflow prioritizes relevance, research quality, and journal evidence. Open-access status is not used as a ranking criterion.

### Workflow 3: Add existing papers and PDFs to Zotero

```text
Add the downloaded papers to my Zotero collection named “Collection name” and attach each local PDF to its matching article record.
```

When Zotero Web API writing is needed, create a personal-library API key yourself and grant only the required library/write permissions. Never place an API key in a README, public repository, or public chat.

### Workflow 4: Generate or refine a dashboard

```text
Create a dashboard for this library with theme taxonomy, method distribution,
a publication timeline, a theme–method map, journal sources, and local PDF links.
```

For deeper literature notes, ask:

```text
Read the local PDFs and add paper-specific Chinese notes for research topic, method,
data or case, findings, limitations, and implications.
```

### Typical outputs

A run folder commonly contains:

- `metadata/papers.json`: normalized paper metadata;
- `texts/`: extracted text from local PDFs;
- `review-bilingual.md`: bilingual review;
- `relationship-map.md`: theme and method relationships;
- `dashboard-spec.json`: editable taxonomy and paper-card semantics;
- `literature-dashboard.html`: an offline interactive dashboard.

### Privacy and data boundaries

- Do not put names, email addresses, institutional accounts, API keys, cookies, browser profiles, or absolute local paths in the skill, README, or a public repository.
- Zotero direct-import mode reads local data by default and does not copy or upload PDFs.

Before a public release, run `scripts/quick_validate.py` and read [`PRIVACY.md`](PRIVACY.md). The repository should contain only source, instructions, and synthetic examples—not Zotero databases, PDFs, extracted text, personal notes, browser profiles, or run outputs.

### License

This project is licensed under the [MIT License](LICENSE).
